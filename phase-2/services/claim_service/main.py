"""
TriNetra Phase 2 — Service 1: Claim Service (Port 8080)

Responsibilities:
  - Claim ingestion (single + bulk CSV/JSON)
  - Claim lifecycle management
  - Investigator assignment and override
  - Filtered search for investigation queue
"""

import csv
import io
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.database import get_db, check_db_connection
from shared.message_bus import publish_event
from shared.models import (
    ClaimCreate, ClaimResponse, ClaimOverride, ClaimSearchParams,
    ClaimStatus, ActionType, VerdictEnum
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("claim_service")

app = FastAPI(
    title="TriNetra Claim Service",
    description="Claim ingestion, lifecycle management, and investigator workflow",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    return {
        "service": "claim_service",
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v2/claims — Single claim ingestion
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v2/claims", response_model=dict, status_code=201, tags=["Claims"])
async def create_claim(
    claim: ClaimCreate,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single claim from a seller, marketplace, or customer portal."""
    claim_id = uuid4()
    now = datetime.utcnow()

    await db.execute(
        """
        INSERT INTO claims (
            claim_id, customer_id, order_id, product_id, product_category,
            product_value, claim_amount, claim_reason, delivery_date, return_date,
            tracking_number, payment_txn_id, status, created_at, updated_at
        ) VALUES (
            :claim_id, :customer_id, :order_id, :product_id, :product_category,
            :product_value, :claim_amount, :claim_reason, :delivery_date, :return_date,
            :tracking_number, :payment_txn_id, :status, :created_at, :updated_at
        )
        """,
        {
            "claim_id":        str(claim_id),
            "customer_id":     str(claim.customer_id),
            "order_id":        claim.order_id,
            "product_id":      claim.product_id,
            "product_category": claim.product_category,
            "product_value":   claim.product_value,
            "claim_amount":    claim.claim_amount,
            "claim_reason":    claim.claim_reason,
            "delivery_date":   claim.delivery_date,
            "return_date":     claim.return_date,
            "tracking_number": claim.tracking_number,
            "payment_txn_id":  claim.payment_txn_id,
            "status":          ClaimStatus.CREATED.value,
            "created_at":      now,
            "updated_at":      now,
        }
    )

    # Publish claim.created event for downstream services
    await publish_event("evidence.uploaded", {
        "event_type": "claim.created",
        "claim_id": str(claim_id),
        "customer_id": str(claim.customer_id),
        "product_category": claim.product_category,
        "timestamp": now.isoformat(),
    })

    logger.info("Claim created: %s for customer: %s", claim_id, claim.customer_id)

    return {
        "claim_id": str(claim_id),
        "status": ClaimStatus.CREATED.value,
        "created_at": now.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v2/claims/bulk-import — CSV/JSON batch import
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v2/claims/bulk-import", tags=["Claims"])
async def bulk_import_claims(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Import multiple claims from a CSV file.
    Expected CSV columns: customer_id, order_id, product_category, product_value,
                          claim_amount, claim_reason, delivery_date, return_date
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted for bulk import.")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    created_ids = []
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            claim_id = uuid4()
            now = datetime.utcnow()
            await db.execute(
                """
                INSERT INTO claims (
                    claim_id, customer_id, order_id, product_category,
                    product_value, claim_amount, claim_reason,
                    delivery_date, return_date, status, created_at, updated_at
                ) VALUES (
                    :claim_id, :customer_id, :order_id, :product_category,
                    :product_value, :claim_amount, :claim_reason,
                    :delivery_date, :return_date, :status, :created_at, :updated_at
                )
                """,
                {
                    "claim_id":        str(claim_id),
                    "customer_id":     row.get("customer_id"),
                    "order_id":        row.get("order_id"),
                    "product_category": row.get("product_category"),
                    "product_value":   float(row.get("product_value", 0)),
                    "claim_amount":    float(row.get("claim_amount", 0)),
                    "claim_reason":    row.get("claim_reason"),
                    "delivery_date":   row.get("delivery_date") or None,
                    "return_date":     row.get("return_date") or None,
                    "status":          ClaimStatus.CREATED.value,
                    "created_at":      now,
                    "updated_at":      now,
                }
            )
            created_ids.append(str(claim_id))
        except Exception as exc:
            errors.append({"row": row_num, "error": str(exc)})

    logger.info("Bulk import: %d created, %d errors", len(created_ids), len(errors))

    return {
        "claims_created": len(created_ids),
        "errors": errors,
        "claim_ids": created_ids[:20],  # Return first 20 IDs
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v2/claims/search — Filtered investigator queue
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v2/claims/search", tags=["Claims"])
async def search_claims(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Filtered search for the investigator queue — sorted by confidence_score ASC (most uncertain first)."""
    query = "SELECT * FROM claims WHERE 1=1"
    params: dict = {}

    if status:
        query += " AND status = :status"
        params["status"] = status

    query += " ORDER BY confidence_score ASC NULLS FIRST, created_at DESC"
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    result = await db.execute(query, params)
    rows = result.mappings().all()

    return {
        "claims": [dict(r) for r in rows],
        "total": len(rows),
        "limit": limit,
        "offset": offset,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v2/claims/{id} — Claim detail with fraud signals + verdict
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v2/claims/{claim_id}", tags=["Claims"])
async def get_claim_detail(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Full claim detail including fraud signals, verdict reasoning, and investigator actions."""
    claim = await db.execute(
        "SELECT * FROM claims WHERE claim_id = :claim_id",
        {"claim_id": str(claim_id)}
    )
    claim_row = claim.mappings().first()
    if not claim_row:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")

    # Fetch fraud signals
    signals_result = await db.execute(
        "SELECT * FROM fraud_signals WHERE claim_id = :claim_id ORDER BY created_at DESC",
        {"claim_id": str(claim_id)}
    )
    signals = [dict(r) for r in signals_result.mappings().all()]

    # Fetch verdict reasoning
    verdict_result = await db.execute(
        "SELECT * FROM verdict_reasoning WHERE claim_id = :claim_id ORDER BY generated_at DESC LIMIT 1",
        {"claim_id": str(claim_id)}
    )
    verdict = verdict_result.mappings().first()

    # Fetch investigator actions
    actions_result = await db.execute(
        "SELECT * FROM investigator_actions WHERE claim_id = :claim_id ORDER BY created_at DESC",
        {"claim_id": str(claim_id)}
    )
    actions = [dict(r) for r in actions_result.mappings().all()]

    return {
        **dict(claim_row),
        "fraud_signals": signals,
        "verdict_reasoning": dict(verdict) if verdict else None,
        "investigator_actions": actions,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v2/claims/{id}/assign — Assign to investigator
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v2/claims/{claim_id}/assign", tags=["Investigator"])
async def assign_claim(
    claim_id: UUID,
    investigator_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Assign a claim to a specific investigator."""
    await db.execute(
        """
        UPDATE claims SET assigned_to = :investigator_id, updated_at = :now
        WHERE claim_id = :claim_id
        """,
        {"investigator_id": str(investigator_id), "claim_id": str(claim_id), "now": datetime.utcnow()}
    )
    await db.execute(
        """
        INSERT INTO investigator_actions (action_id, claim_id, investigator_id, action_type, created_at)
        VALUES (:action_id, :claim_id, :investigator_id, 'ASSIGN', :now)
        """,
        {
            "action_id": str(uuid4()),
            "claim_id": str(claim_id),
            "investigator_id": str(investigator_id),
            "now": datetime.utcnow(),
        }
    )
    return {"claim_id": str(claim_id), "assigned_to": str(investigator_id)}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v2/claims/{id}/override — Human verdict override
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v2/claims/{claim_id}/override", tags=["Investigator"])
async def override_verdict(
    claim_id: UUID,
    override: ClaimOverride,
    db: AsyncSession = Depends(get_db),
):
    """
    Allow an investigator to override the automated verdict.
    Creates an audit record in investigator_actions.
    """
    new_status = {
        VerdictEnum.REFUND: ClaimStatus.APPROVED,
        VerdictEnum.REJECT: ClaimStatus.REJECTED,
        VerdictEnum.INVESTIGATE: ClaimStatus.INVESTIGATING,
    }[override.verdict]

    await db.execute(
        """
        UPDATE claims
        SET status = :status, automated_verdict = :verdict, updated_at = :now
        WHERE claim_id = :claim_id
        """,
        {
            "status": new_status.value,
            "verdict": override.verdict.value,
            "claim_id": str(claim_id),
            "now": datetime.utcnow(),
        }
    )

    await db.execute(
        """
        INSERT INTO investigator_actions
            (action_id, claim_id, investigator_id, action_type, override_verdict, override_reasoning, created_at)
        VALUES
            (:action_id, :claim_id, :investigator_id, 'OVERRIDE', :verdict, :reasoning, :now)
        """,
        {
            "action_id":        str(uuid4()),
            "claim_id":         str(claim_id),
            "investigator_id":  str(override.investigator_id),
            "verdict":          override.verdict.value,
            "reasoning":        override.reasoning,
            "now":              datetime.utcnow(),
        }
    )

    await publish_event("verdict.generated", {
        "event_type": "verdict.finalized",
        "claim_id": str(claim_id),
        "verdict": override.verdict.value,
        "source": "INVESTIGATOR_OVERRIDE",
        "investigator_id": str(override.investigator_id),
        "timestamp": datetime.utcnow().isoformat(),
    })

    logger.info("Claim %s overridden to %s by investigator %s", claim_id, override.verdict.value, override.investigator_id)

    return {
        "claim_id": str(claim_id),
        "new_verdict": override.verdict.value,
        "new_status": new_status.value,
        "overridden_by": str(override.investigator_id),
        "overridden_at": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    port = int(os.getenv("CLAIM_SERVICE_PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
