"""
TriNetra Phase 2 — Service 2: Evidence Service (Port 8081)

Responsibilities:
  - Multi-modal file upload (images, receipts, shipping docs) to MinIO
  - Evidence record creation in PostgreSQL
  - Publishing evidence.uploaded event to trigger multi-modal processing
  - Artifact retrieval for dashboard
"""

import logging
import os
import sys
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.database import get_db, check_db_connection
from shared.message_bus import publish_event
from shared.minio_client import get_minio_client
from shared.models import EvidenceType, EvidenceStatus, EvidenceUploadedEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evidence_service")

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf", "text/plain",
}
MAX_FILE_SIZE_MB = 20

app = FastAPI(
    title="TriNetra Evidence Service",
    description="Multi-modal evidence ingestion, storage, and artifact retrieval",
    version="2.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    return {
        "service": "evidence_service",
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v2/evidence/upload
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v2/evidence/upload", status_code=202, tags=["Evidence"])
async def upload_evidence(
    claim_id: UUID = Form(...),
    evidence_type: EvidenceType = Form(...),
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a multi-modal evidence file (product image, receipt, shipping document).
    Stores the file in MinIO and publishes an event for async processing.
    """
    # ── Validation ────────────────────────────────────────────────────────────
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {ALLOWED_MIME_TYPES}"
        )

    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size_mb:.1f} MB. Maximum allowed: {MAX_FILE_SIZE_MB} MB"
        )

    # ── Store in MinIO ─────────────────────────────────────────────────────────
    evidence_id = uuid4()
    minio = get_minio_client()
    object_key = minio.object_key_for_evidence(claim_id, evidence_id, file.filename)
    file_url = minio.upload_bytes(object_key, file_bytes, file.content_type)

    # ── Create evidence record ────────────────────────────────────────────────
    now = datetime.utcnow()
    await db.execute(
        """
        INSERT INTO evidence (
            evidence_id, claim_id, evidence_type, file_url,
            file_size_bytes, mime_type, metadata, status, uploaded_at
        ) VALUES (
            :evidence_id, :claim_id, :evidence_type, :file_url,
            :file_size_bytes, :mime_type, :metadata, :status, :uploaded_at
        )
        """,
        {
            "evidence_id":    str(evidence_id),
            "claim_id":       str(claim_id),
            "evidence_type":  evidence_type.value,
            "file_url":       file_url,
            "file_size_bytes": len(file_bytes),
            "mime_type":      file.content_type,
            "metadata":       metadata,
            "status":         EvidenceStatus.PENDING.value,
            "uploaded_at":    now,
        }
    )

    # Update claim status to EVIDENCE_PENDING
    await db.execute(
        "UPDATE claims SET status = 'EVIDENCE_PENDING', updated_at = :now WHERE claim_id = :claim_id",
        {"claim_id": str(claim_id), "now": now}
    )

    # ── Publish event ─────────────────────────────────────────────────────────
    event = EvidenceUploadedEvent(
        evidence_id=evidence_id,
        claim_id=claim_id,
        evidence_type=evidence_type,
        file_url=file_url,
    )
    await publish_event("evidence.uploaded", event.model_dump(mode="json"))

    logger.info("Evidence uploaded: %s (type: %s) for claim: %s", evidence_id, evidence_type.value, claim_id)

    return {
        "evidence_id":  str(evidence_id),
        "claim_id":     str(claim_id),
        "evidence_type": evidence_type.value,
        "status":       EvidenceStatus.PENDING.value,
        "file_url":     file_url,
        "uploaded_at":  now.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v2/evidence/{id}/artifacts
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v2/evidence/{evidence_id}/artifacts", tags=["Evidence"])
async def get_evidence_artifacts(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all processed artifacts for an evidence record (OCR, wear scores, etc)."""
    result = await db.execute(
        """
        SELECT * FROM evidence_artifacts
        WHERE evidence_id = :evidence_id
        ORDER BY created_at ASC
        """,
        {"evidence_id": str(evidence_id)}
    )
    artifacts = [dict(r) for r in result.mappings().all()]

    return {
        "evidence_id": str(evidence_id),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v2/evidence/claim/{claim_id}
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v2/evidence/claim/{claim_id}", tags=["Evidence"])
async def get_claim_evidence(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all evidence records for a specific claim."""
    result = await db.execute(
        "SELECT * FROM evidence WHERE claim_id = :claim_id ORDER BY uploaded_at ASC",
        {"claim_id": str(claim_id)}
    )
    rows = [dict(r) for r in result.mappings().all()]
    return {"claim_id": str(claim_id), "evidence": rows}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v2/evidence/{id}/process — Manual re-trigger for processing
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v2/evidence/{evidence_id}/process", status_code=202, tags=["Evidence"])
async def reprocess_evidence(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger re-processing for a specific evidence record."""
    result = await db.execute(
        "SELECT evidence_id, claim_id, evidence_type, file_url FROM evidence WHERE evidence_id = :evidence_id",
        {"evidence_id": str(evidence_id)}
    )
    ev = result.mappings().first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found.")

    await publish_event("evidence.uploaded", {
        "event_type": "evidence.uploaded",
        "evidence_id": str(evidence_id),
        "claim_id": str(ev["claim_id"]),
        "evidence_type": ev["evidence_type"],
        "file_url": ev["file_url"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"evidence_id": str(evidence_id), "status": "reprocessing_triggered"}


if __name__ == "__main__":
    port = int(os.getenv("EVIDENCE_SERVICE_PORT", "8081"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
