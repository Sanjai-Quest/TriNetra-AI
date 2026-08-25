"""
TriNetra Phase 2 — Service 6: Integration Service (Port 8085)

Responsibilities:
  - Webhook receiver for shipping carriers, payment processors, KYC services
  - Object detection endpoint (OpenCV-based, no large model downloads)
  - Dead-letter queue retry handler for failed integration events
  - Persists all integration events in PostgreSQL for auditability
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.database import get_db_session, check_db_connection
from shared.message_bus import get_message_bus, publish_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("integration_service")

MAX_RETRIES = 3

app = FastAPI(
    title="TriNetra Integration Service",
    description="Third-party webhooks: shipping carriers, payment processors, KYC services",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────────────────────

class ShippingWebhook(BaseModel):
    tracking_number: str
    status: str
    delivery_date: Optional[str] = None
    carrier: Optional[str] = None
    timestamp: str


class PaymentWebhook(BaseModel):
    transaction_id: str
    refund_status: str
    amount: float
    currency: str = "INR"


class KYCVerificationRequest(BaseModel):
    customer_id: UUID
    claim_id: Optional[UUID] = None


class ObjectDetectionRequest(BaseModel):
    image_url: str
    claim_id: Optional[UUID] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def save_integration_event(
    claim_id: Optional[str],
    provider: str,
    event_type: str,
    payload: Dict[str, Any],
    status: str = "success",
    retry_count: int = 0,
) -> str:
    event_id = str(uuid4())
    async with get_db_session() as db:
        await db.execute(
            """
            INSERT INTO integration_events
                (event_id, claim_id, provider, event_type, payload, status, retry_count, created_at)
            VALUES
                (:event_id, :claim_id, :provider, :event_type, :payload, :status, :retry_count, :now)
            """,
            {
                "event_id":    event_id,
                "claim_id":    claim_id,
                "provider":    provider,
                "event_type":  event_type,
                "payload":     json.dumps(payload, default=str),
                "status":      status,
                "retry_count": retry_count,
                "now":         datetime.utcnow(),
            }
        )
    return event_id


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    return {"service": "integration_service", "status": "healthy" if db_ok else "degraded"}


# ─────────────────────────────────────────────────────────────────────────────
# Webhook 1: Shipping Carrier Delivery Confirmation
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/webhooks/shipping/delivered", status_code=202, tags=["Webhooks"])
async def handle_shipping_delivery(
    webhook: ShippingWebhook,
    background_tasks: BackgroundTasks,
):
    """
    Receive delivery confirmation from shipping carriers (FedEx, Delhivery, Bluedart, etc).
    Updates claim with proof of delivery and stores integration event.
    """
    background_tasks.add_task(_process_delivery, webhook)
    return {"status": "received", "tracking_number": webhook.tracking_number}


async def _process_delivery(webhook: ShippingWebhook) -> None:
    try:
        # Find claim by tracking number
        async with get_db_session() as db:
            result = await db.execute(
                "SELECT claim_id FROM claims WHERE tracking_number = :tn",
                {"tn": webhook.tracking_number}
            )
            claim = result.mappings().first()
            claim_id = str(claim["claim_id"]) if claim else None

            if claim_id and webhook.status.lower() in ("delivered", "delivery_confirmed"):
                await db.execute(
                    """
                    UPDATE claims SET delivery_proof = TRUE, delivery_date = :date, updated_at = :now
                    WHERE claim_id = :cid
                    """,
                    {
                        "date": datetime.fromisoformat(webhook.delivery_date) if webhook.delivery_date else datetime.utcnow(),
                        "now":  datetime.utcnow(),
                        "cid":  claim_id,
                    }
                )
                logger.info("Delivery confirmed for claim %s (tracking: %s)", claim_id, webhook.tracking_number)

        await save_integration_event(
            claim_id, "shipping_carrier", "delivery_confirmed",
            {"tracking": webhook.tracking_number, "status": webhook.status, "carrier": webhook.carrier}
        )

        # Notify fraud engine to re-evaluate
        if claim_id:
            await publish_event("fraud.analysis.complete", {
                "event_type": "delivery.confirmed",
                "claim_id": claim_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

    except Exception as exc:
        logger.error("Error processing delivery webhook: %s", exc)
        await save_integration_event(None, "shipping_carrier", "delivery_confirmed", {}, "failed")


# ─────────────────────────────────────────────────────────────────────────────
# Webhook 2: Payment Processor Refund Status
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/webhooks/payment/refund-status", status_code=202, tags=["Webhooks"])
async def handle_payment_webhook(
    webhook: PaymentWebhook,
    background_tasks: BackgroundTasks,
):
    """Receive payment processor refund status (Razorpay, Stripe, PayU, etc)."""
    background_tasks.add_task(_process_payment, webhook)
    return {"status": "received", "transaction_id": webhook.transaction_id}


async def _process_payment(webhook: PaymentWebhook) -> None:
    try:
        async with get_db_session() as db:
            result = await db.execute(
                "SELECT claim_id FROM claims WHERE payment_txn_id = :txn",
                {"txn": webhook.transaction_id}
            )
            claim = result.mappings().first()
            claim_id = str(claim["claim_id"]) if claim else None

        event_type = "refund_processed" if webhook.refund_status.lower() == "completed" else "refund_failed"
        await save_integration_event(
            claim_id, "payment_processor", event_type,
            {"txn_id": webhook.transaction_id, "refund_status": webhook.refund_status, "amount": webhook.amount}
        )

        if webhook.refund_status.lower() == "completed" and claim_id:
            async with get_db_session() as db:
                await db.execute(
                    "UPDATE claims SET status = 'CLOSED', updated_at = :now WHERE claim_id = :cid",
                    {"cid": claim_id, "now": datetime.utcnow()}
                )
            logger.info("Refund confirmed and claim closed: %s", claim_id)

    except Exception as exc:
        logger.error("Error processing payment webhook: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint: Object Detection (OpenCV-based, no YOLO model download)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/image-analysis/detect-objects", tags=["Image Analysis"])
async def detect_objects(request: ObjectDetectionRequest):
    """
    Perform basic object detection using OpenCV contour analysis.
    Detects presence and rough count of distinct objects in the image.
    No ML model download required.
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            img_response = await client.get(request.image_url, timeout=10.0)
            image_bytes = img_response.content

        detections = _detect_objects_opencv(image_bytes)

        if request.claim_id:
            await save_integration_event(
                str(request.claim_id), "image_api", "object_detected",
                {"image_url": request.image_url, "detections": detections}
            )

        return {"detections": detections, "image_url": request.image_url}

    except Exception as exc:
        logger.error("Object detection failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


def _detect_objects_opencv(image_bytes: bytes) -> list:
    """
    OpenCV contour-based object detection:
    - Converts to greyscale, applies GaussianBlur + Canny edge
    - Finds contours → counts likely distinct objects
    """
    try:
        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return [{"class": "unknown", "confidence": 0.0, "reason": "Could not decode image"}]

        gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter by area to remove noise
        h, w = img.shape[:2]
        min_area = (h * w) * 0.01
        significant = [c for c in contours if cv2.contourArea(c) > min_area]

        detections = []
        for i, cnt in enumerate(significant[:10]):
            x, y, cw, ch = cv2.boundingRect(cnt)
            area_ratio = (cw * ch) / (h * w)
            detections.append({
                "object_index": i + 1,
                "class": "object",
                "confidence": round(min(0.95, area_ratio * 10), 2),
                "bbox": {"x": int(x), "y": int(y), "w": int(cw), "h": int(ch)},
                "area_ratio": round(area_ratio, 4),
            })
        return detections

    except ImportError:
        return [{"class": "unavailable", "confidence": 0.0, "reason": "OpenCV not installed"}]
    except Exception as exc:
        return [{"class": "error", "confidence": 0.0, "reason": str(exc)}]


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint: KYC / Identity Verification (mock external call)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/kyc-verification", tags=["KYC"])
async def verify_kyc(request: KYCVerificationRequest):
    """
    Placeholder KYC/AML identity verification endpoint.
    Calls external provider (IDfy, Signzy, etc.) when API key is configured.
    Currently returns a simulated response.
    """
    KYC_API_KEY = os.getenv("KYC_API_KEY")

    if KYC_API_KEY:
        # Real integration (stub: connect to actual provider)
        logger.info("KYC API key detected — would call external provider for customer %s", request.customer_id)
        result = {"status": "VERIFIED", "customer_id": str(request.customer_id), "provider": "external"}
    else:
        logger.info("KYC API key not set — returning simulated KYC result.")
        result = {"status": "SIMULATED_VERIFIED", "customer_id": str(request.customer_id), "provider": "simulation"}

    await save_integration_event(
        str(request.claim_id) if request.claim_id else None,
        "kyc_service", "identity_verified", result
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Dead Letter Queue Retry Handler
# ─────────────────────────────────────────────────────────────────────────────

async def handle_dlq_event(payload: Dict[str, Any]) -> None:
    """
    Consumes failed integration events from the dead letter queue.
    Applies exponential backoff retry (up to MAX_RETRIES attempts).
    """
    event_id    = payload.get("event_id")
    retry_count = int(payload.get("retry_count", 0))

    if retry_count >= MAX_RETRIES:
        logger.error("Integration event %s exhausted %d retries — giving up.", event_id, MAX_RETRIES)
        async with get_db_session() as db:
            await db.execute(
                "UPDATE integration_events SET status = 'failed', updated_at = :now WHERE event_id = :eid",
                {"eid": event_id, "now": datetime.utcnow()}
            )
        return

    backoff_seconds = 2 ** retry_count  # 1s, 2s, 4s
    logger.warning("Retrying integration event %s (attempt %d) in %ds", event_id, retry_count + 1, backoff_seconds)
    await asyncio.sleep(backoff_seconds)

    # Re-publish with incremented retry count
    payload["retry_count"] = retry_count + 1
    await publish_event("integration.events", payload)

    async with get_db_session() as db:
        await db.execute(
            """
            UPDATE integration_events SET status = 'pending_retry', retry_count = :rc, updated_at = :now
            WHERE event_id = :eid
            """,
            {"rc": retry_count + 1, "eid": event_id, "now": datetime.utcnow()}
        )


@app.on_event("startup")
async def startup():
    try:
        bus = await get_message_bus()
        await bus.subscribe("integration.events.dlq", handle_dlq_event)
        logger.info("Integration Service subscribed to DLQ.")
    except Exception as exc:
        logger.warning("Could not connect to RabbitMQ on startup: %s", exc)


if __name__ == "__main__":
    port = int(os.getenv("INTEGRATION_SERVICE_PORT", "8085"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
