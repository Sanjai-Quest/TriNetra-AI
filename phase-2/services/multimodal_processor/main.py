"""
TriNetra Phase 2 — Service 3: Multi-Modal Processor (Port 8082)

Responsibilities:
  - Consumes evidence.uploaded events from RabbitMQ
  - Runs OCR on receipts using pytesseract
  - Runs wear analysis on product images using OpenCV (no ML model download required)
  - Extracts EXIF metadata from photos
  - Checks color consistency for authenticity
  - Saves all results as evidence_artifacts in PostgreSQL
  - Publishes evidence.processed event
"""

import asyncio
import io
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.database import get_db_session, check_db_connection
from shared.message_bus import get_message_bus, publish_event
from shared.minio_client import get_minio_client
from shared.models import EvidenceStatus, WearAnalysisResult, ReceiptParseResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multimodal_processor")

app = FastAPI(
    title="TriNetra Multi-Modal Processor",
    description="OCR, wear detection, EXIF extraction, and color analysis for evidence files",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# OpenCV Wear Analysis (no CLIP model — deterministic computer vision)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_wear_opencv(image_bytes: bytes) -> WearAnalysisResult:
    """
    Estimate garment wear using deterministic OpenCV computer vision:
      - Color saturation loss (worn fabric has lower HSV saturation)
      - Edge density via Canny (creases and folds = higher edge density)
      - Texture variance via Laplacian (worn fabric = lower texture variance)
    Returns WearAnalysisResult with 0.0 (new) to 1.0 (heavily worn) wear_score.
    """
    try:
        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return WearAnalysisResult(wear_score=0.0, confidence=0.0, recommendation="UNKNOWN")

        # 1. Color saturation (HSV S channel): worn fabric loses vibrancy
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        saturation = float(img_hsv[:, :, 1].mean()) / 255.0   # 0.0-1.0

        # 2. Edge density (Canny): more edges = more creases = more wear
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(img_gray, threshold1=50, threshold2=150)
        edge_density = float(edges.mean()) / 255.0              # 0.0-1.0

        # 3. Texture variance (Laplacian): worn = smoother/more worn surface
        laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
        texture_score = min(1.0, laplacian_var / 5000.0)        # Normalize

        # Composite wear score:
        # High edge density → more creases (wear signal +)
        # Low saturation → color fading (wear signal +)
        # Low texture → pilling or smoothing (wear signal +)
        wear_score = (
            (1.0 - saturation) * 0.35 +   # Low saturation = worn
            edge_density * 0.40 +          # High edge density = creases
            (1.0 - texture_score) * 0.25   # Low texture = worn surface
        )
        wear_score = min(1.0, max(0.0, wear_score))

        fold_detected   = edge_density > 0.12
        texture_anomaly = texture_score < 0.15

        if wear_score > 0.70:
            estimated_hours = ">20"
            recommendation  = "HIGH_RISK"
        elif wear_score > 0.45:
            estimated_hours = "5-20"
            recommendation  = "MEDIUM_RISK"
        else:
            estimated_hours = "<5"
            recommendation  = "LOW_RISK"

        return WearAnalysisResult(
            wear_score=round(wear_score, 4),
            confidence=0.78,
            fold_detected=fold_detected,
            texture_anomaly=texture_anomaly,
            saturation_score=round(saturation, 4),
            edge_density=round(edge_density, 4),
            estimated_wear_hours=estimated_hours,
            recommendation=recommendation,
        )

    except ImportError:
        logger.warning("OpenCV not available; returning neutral wear score.")
        return WearAnalysisResult(wear_score=0.0, confidence=0.0, recommendation="OPENCV_UNAVAILABLE")
    except Exception as exc:
        logger.error("Wear analysis failed: %s", exc)
        return WearAnalysisResult(wear_score=0.0, confidence=0.0, recommendation="ERROR")


# ─────────────────────────────────────────────────────────────────────────────
# EXIF Metadata Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_exif_metadata(image_bytes: bytes) -> Dict[str, Any]:
    """Extract EXIF metadata from a JPEG/PNG image using Pillow."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif() or {}

        readable = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, str(tag_id))
            if isinstance(value, bytes):
                continue  # Skip binary blobs
            readable[tag] = str(value)

        return {
            "format":    img.format,
            "mode":      img.mode,
            "size":      f"{img.width}x{img.height}",
            "exif_tags": readable,
            "has_gps":   "GPSInfo" in readable,
            "capture_datetime": readable.get("DateTimeOriginal") or readable.get("DateTime"),
        }
    except Exception as exc:
        logger.warning("EXIF extraction failed: %s", exc)
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Color Consistency Analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_color_consistency(image_bytes: bytes) -> Dict[str, Any]:
    """
    Detect dominant colors in the image.
    Used to verify that a returned product matches the expected color.
    """
    try:
        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"error": "Could not decode image"}

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Resize for speed
        small = cv2.resize(img_rgb, (64, 64))
        pixels = small.reshape(-1, 3)

        # Calculate mean color
        mean_color = pixels.mean(axis=0)
        dominant = _rgb_to_color_name(int(mean_color[0]), int(mean_color[1]), int(mean_color[2]))

        return {
            "dominant_color_name": dominant,
            "mean_rgb": {"r": int(mean_color[0]), "g": int(mean_color[1]), "b": int(mean_color[2])},
            "brightness": round(float(mean_color.mean()) / 255.0, 3),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _rgb_to_color_name(r: int, g: int, b: int) -> str:
    """Simple heuristic: map RGB to nearest basic color name."""
    colors = {
        "RED":    (220, 50, 50),
        "GREEN":  (50, 200, 50),
        "BLUE":   (50, 50, 220),
        "BLACK":  (20, 20, 20),
        "WHITE":  (240, 240, 240),
        "GREY":   (128, 128, 128),
        "YELLOW": (230, 220, 40),
        "ORANGE": (230, 140, 40),
        "PINK":   (230, 130, 180),
        "PURPLE": (140, 50, 180),
        "BROWN":  (139, 90, 43),
    }
    import math
    min_dist = float("inf")
    best = "UNKNOWN"
    for name, (cr, cg, cb) in colors.items():
        dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if dist < min_dist:
            min_dist = dist
            best = name
    return best


# ─────────────────────────────────────────────────────────────────────────────
# OCR Receipt Processing
# ─────────────────────────────────────────────────────────────────────────────

def run_ocr(image_bytes: bytes) -> str:
    """Extract text from an image using pytesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img)
    except ImportError:
        logger.warning("pytesseract not installed; returning empty OCR text.")
        return ""
    except Exception as exc:
        logger.error("OCR failed: %s", exc)
        return ""


def parse_receipt_structure(raw_text: str) -> ReceiptParseResult:
    """Parse OCR text to extract receipt fields: merchant, date, amount, items."""
    amount_pattern = re.compile(r"(?:total|amount|rs\.?|₹)\s*[:\-]?\s*(\d+[\.,]?\d*)", re.IGNORECASE)
    date_pattern   = re.compile(r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b")

    amounts_found = amount_pattern.findall(raw_text)
    dates_found   = date_pattern.findall(raw_text)

    total_amount = None
    if amounts_found:
        try:
            total_amount = float(amounts_found[-1].replace(",", ""))
        except ValueError:
            pass

    return ReceiptParseResult(
        transaction_date=dates_found[0] if dates_found else None,
        total_amount=total_amount,
        raw_text=raw_text[:2000],
        parse_confidence=0.65 if total_amount else 0.30,
    )


def validate_receipt_against_claim(claim_amount: Optional[float], receipt: ReceiptParseResult) -> Dict[str, Any]:
    """Compare parsed receipt amount to claimed amount."""
    if claim_amount is None or receipt.total_amount is None:
        return {"status": "CANNOT_VALIDATE", "reason": "Missing amount data"}

    diff_pct = abs(claim_amount - receipt.total_amount) / max(claim_amount, 0.01) * 100
    if diff_pct <= 5:
        return {"status": "MATCH", "diff_pct": round(diff_pct, 2)}
    elif diff_pct <= 20:
        return {"status": "PARTIAL_MATCH", "diff_pct": round(diff_pct, 2)}
    else:
        return {"status": "MISMATCH", "diff_pct": round(diff_pct, 2), "risk": "HIGH"}


# ─────────────────────────────────────────────────────────────────────────────
# Core Processing Pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def save_artifact(
    db_session,
    evidence_id: str,
    artifact_type: str,
    data: Dict[str, Any],
    confidence: float,
    duration_ms: int,
) -> None:
    await db_session.execute(
        """
        INSERT INTO evidence_artifacts
            (artifact_id, evidence_id, artifact_type, content_type, data,
             confidence_score, processor_service, processing_duration_ms, created_at)
        VALUES
            (:artifact_id, :evidence_id, :artifact_type, 'json', :data,
             :confidence, 'multimodal_processor', :duration_ms, :now)
        """,
        {
            "artifact_id":  str(uuid4()),
            "evidence_id":  evidence_id,
            "artifact_type": artifact_type,
            "data":         json.dumps(data, default=str),
            "confidence":   confidence,
            "duration_ms":  duration_ms,
            "now":          datetime.utcnow(),
        }
    )


async def process_evidence_event(payload: Dict[str, Any]) -> None:
    """Main consumer handler: downloads file from MinIO and runs all relevant processors."""
    evidence_id   = payload.get("evidence_id")
    claim_id      = payload.get("claim_id")
    evidence_type = payload.get("evidence_type", "product_image")
    file_url      = payload.get("file_url", "")

    if not evidence_id or not file_url:
        logger.warning("Skipping invalid evidence.uploaded event: %s", payload)
        return

    start = datetime.utcnow()
    artifacts_created = []

    try:
        # Download file bytes from MinIO
        minio = get_minio_client()
        object_key = "/".join(file_url.split("/")[3:])  # Strip host prefix
        file_bytes = minio.download_bytes(object_key)

        async with get_db_session() as db:
            if evidence_type in ("product_image", "behavioral"):
                # 1. EXIF metadata
                t0 = datetime.utcnow()
                exif = extract_exif_metadata(file_bytes)
                await save_artifact(db, evidence_id, "exif_metadata", exif, 0.95,
                                    int((datetime.utcnow() - t0).total_seconds() * 1000))
                artifacts_created.append("exif_metadata")

                # 2. Wear analysis
                t0 = datetime.utcnow()
                wear = analyze_wear_opencv(file_bytes)
                await save_artifact(db, evidence_id, "wear_analysis", wear.model_dump(), wear.confidence,
                                    int((datetime.utcnow() - t0).total_seconds() * 1000))
                artifacts_created.append("wear_analysis")

                # 3. Color consistency
                t0 = datetime.utcnow()
                color = analyze_color_consistency(file_bytes)
                await save_artifact(db, evidence_id, "color_analysis", color, 0.85,
                                    int((datetime.utcnow() - t0).total_seconds() * 1000))
                artifacts_created.append("color_analysis")

            elif evidence_type == "receipt":
                # 1. OCR
                t0 = datetime.utcnow()
                raw_text = run_ocr(file_bytes)
                await save_artifact(db, evidence_id, "ocr_text", {"text": raw_text}, 0.80,
                                    int((datetime.utcnow() - t0).total_seconds() * 1000))
                artifacts_created.append("ocr_text")

                # 2. Parse receipt
                parsed = parse_receipt_structure(raw_text)
                await save_artifact(db, evidence_id, "receipt_parsed", parsed.model_dump(), parsed.parse_confidence,
                                    0)
                artifacts_created.append("receipt_parsed")

            # Update evidence status to PROCESSED
            await db.execute(
                "UPDATE evidence SET status = 'PROCESSED', processed_at = :now WHERE evidence_id = :eid",
                {"eid": evidence_id, "now": datetime.utcnow()}
            )

        # Publish evidence.processed event
        total_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        await publish_event("evidence.processed", {
            "event_type":    "evidence.processed",
            "evidence_id":   evidence_id,
            "claim_id":      claim_id,
            "artifact_types": artifacts_created,
            "processing_ms":  total_ms,
            "timestamp":      datetime.utcnow().isoformat(),
        })

        logger.info("Evidence %s processed in %dms. Artifacts: %s", evidence_id, total_ms, artifacts_created)

    except Exception as exc:
        logger.error("Failed to process evidence %s: %s", evidence_id, exc)
        async with get_db_session() as db:
            await db.execute(
                "UPDATE evidence SET status = 'FAILED', processed_at = :now WHERE evidence_id = :eid",
                {"eid": evidence_id, "now": datetime.utcnow()}
            )


# ─────────────────────────────────────────────────────────────────────────────
# Startup: connect to message bus and start consuming
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    try:
        bus = await get_message_bus()
        await bus.subscribe("evidence.uploaded", process_evidence_event)
        logger.info("Multi-Modal Processor subscribed to evidence.uploaded queue.")
    except Exception as exc:
        logger.warning("Could not connect to RabbitMQ on startup (will retry): %s", exc)


@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    return {"service": "multimodal_processor", "status": "healthy" if db_ok else "degraded"}


@app.post("/api/v2/process/image", tags=["Direct Processing"])
async def process_image_direct(image_url: str):
    """Direct HTTP endpoint for triggering image analysis (for testing without RabbitMQ)."""
    minio = get_minio_client()
    object_key = "/".join(image_url.split("/")[3:])
    file_bytes = minio.download_bytes(object_key)
    wear = analyze_wear_opencv(file_bytes)
    color = analyze_color_consistency(file_bytes)
    exif = extract_exif_metadata(file_bytes)
    return {"wear_analysis": wear.model_dump(), "color_analysis": color, "exif_metadata": exif}


if __name__ == "__main__":
    port = int(os.getenv("MULTIMODAL_PROCESSOR_PORT", "8082"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
