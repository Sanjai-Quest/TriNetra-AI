"""
TriNetra Phase 2 — Service 4: Fraud Detection Engine (Port 8083)

Responsibilities:
  - Consumes evidence.processed events from RabbitMQ
  - Runs 4 fraud detection patterns:
      1. Serial Fraudster (7+ returns in 90 days)
      2. Behavioral Anomalies (impossibly fast return, inflated claim)
      3. Cross-Org Pattern Detection (returns across 3+ organizations)
      4. Wardrobing Detection (cross-references wear_analysis artifacts)
  - Saves FraudSignal records to PostgreSQL
  - Uses Redis to cache customer patterns for fast lookup
  - Publishes fraud.analysis.complete event
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.database import get_db_session, check_db_connection
from shared.message_bus import get_message_bus, publish_event
from shared.redis_client import get_redis_cache
from shared.models import FraudSeverity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fraud_engine")

app = FastAPI(
    title="TriNetra Fraud Detection Engine",
    description="Serial fraudster, behavioral anomaly, wardrobing, and cross-org fraud ring detection",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# Signal persistence helper
# ─────────────────────────────────────────────────────────────────────────────

async def save_fraud_signal(
    db_session,
    claim_id: str,
    signal_type: str,
    severity: FraudSeverity,
    confidence: float,
    reasoning: str,
    cross_claim_indicators: Optional[Dict[str, Any]] = None,
    source_evidence_id: Optional[str] = None,
) -> None:
    await db_session.execute(
        """
        INSERT INTO fraud_signals (
            signal_id, claim_id, signal_type, severity, confidence_score,
            source_evidence_id, reasoning, cross_claim_indicators, created_at
        ) VALUES (
            :signal_id, :claim_id, :signal_type, :severity, :confidence,
            :source_evidence_id, :reasoning, :cross_claim_indicators, :now
        )
        """,
        {
            "signal_id":               str(uuid4()),
            "claim_id":                claim_id,
            "signal_type":             signal_type,
            "severity":                severity.value,
            "confidence":              confidence,
            "source_evidence_id":      source_evidence_id,
            "reasoning":               reasoning,
            "cross_claim_indicators":  json.dumps(cross_claim_indicators or {}, default=str),
            "now":                     datetime.utcnow(),
        }
    )
    logger.info("FraudSignal saved: %s | severity=%s | confidence=%.2f", signal_type, severity.value, confidence)


# ─────────────────────────────────────────────────────────────────────────────
# Detection 1: Serial Fraudster
# ─────────────────────────────────────────────────────────────────────────────

async def detect_serial_fraudster(db_session, claim: Dict[str, Any]) -> int:
    """
    Flag if customer filed 7+ claims in the past 90 days.
    Uses Redis cache to avoid repeated DB queries.
    """
    customer_id  = claim["customer_id"]
    claim_id     = str(claim["claim_id"])
    cutoff_date  = datetime.utcnow() - timedelta(days=90)

    # Try cache first
    cache = await get_redis_cache()
    cached = await cache.get_customer_pattern(customer_id)
    if cached:
        return_count = cached.get("return_count_90d", 0)
    else:
        # DB query
        result = await db_session.execute(
            "SELECT COUNT(*) as cnt FROM claims WHERE customer_id = :cid AND created_at > :cutoff",
            {"cid": str(customer_id), "cutoff": cutoff_date}
        )
        row = result.mappings().first()
        return_count = row["cnt"] if row else 0
        await cache.set_customer_pattern(customer_id, {"return_count_90d": return_count})

    THRESHOLD = 7
    if return_count >= THRESHOLD:
        await save_fraud_signal(
            db_session, claim_id,
            signal_type="serial_fraudster",
            severity=FraudSeverity.HIGH,
            confidence=min(0.95, 0.60 + (return_count - THRESHOLD) * 0.05),
            reasoning=(
                f"Customer has filed {return_count} claims in 90 days "
                f"(threshold: {THRESHOLD}). Pattern consistent with serial return abuse."
            ),
            cross_claim_indicators={
                "total_returns_90d": return_count,
                "avg_per_month": round(return_count / 3.0, 1),
                "threshold": THRESHOLD,
            },
        )
    return return_count


# ─────────────────────────────────────────────────────────────────────────────
# Detection 2: Behavioral Anomalies
# ─────────────────────────────────────────────────────────────────────────────

async def detect_behavioral_anomalies(db_session, claim: Dict[str, Any]) -> List[str]:
    """
    Detect:
      a) Impossibly fast return (< 60 minutes after delivery)
      b) Inflated claim amount (> 150% of product value)
      c) High-risk category abuse (3+ returns in electronics)
    """
    signals_detected = []
    claim_id = str(claim["claim_id"])

    # (a) Fast return
    delivery_date = claim.get("delivery_date")
    return_date   = claim.get("return_date")
    if delivery_date and return_date:
        if isinstance(delivery_date, str):
            delivery_date = datetime.fromisoformat(delivery_date.replace("Z", "+00:00")).replace(tzinfo=None)
        if isinstance(return_date, str):
            return_date = datetime.fromisoformat(return_date.replace("Z", "+00:00")).replace(tzinfo=None)

        possession_mins = int((return_date - delivery_date).total_seconds() / 60)
        if possession_mins < 60:
            await save_fraud_signal(
                db_session, claim_id,
                signal_type="impossibly_fast_return",
                severity=FraudSeverity.CRITICAL,
                confidence=0.95,
                reasoning=(
                    f"Item returned within {possession_mins} minutes of delivery. "
                    f"Insufficient time to evaluate product condition legitimately."
                ),
                cross_claim_indicators={"possession_minutes": possession_mins},
            )
            signals_detected.append("impossibly_fast_return")

    # (b) Inflated claim
    product_value = claim.get("product_value") or 0
    claim_amount  = claim.get("claim_amount") or 0
    if product_value > 0 and claim_amount > product_value * 1.5:
        inflation_pct = ((claim_amount / product_value) - 1) * 100
        await save_fraud_signal(
            db_session, claim_id,
            signal_type="inflated_claim_amount",
            severity=FraudSeverity.MEDIUM,
            confidence=0.72,
            reasoning=(
                f"Claimed amount (₹{claim_amount:.2f}) exceeds product value "
                f"(₹{product_value:.2f}) by {inflation_pct:.0f}%."
            ),
            cross_claim_indicators={
                "claimed": claim_amount,
                "product_value": product_value,
                "inflation_pct": round(inflation_pct, 1),
            },
        )
        signals_detected.append("inflated_claim_amount")

    # (c) Category abuse
    HIGH_RISK_CATEGORIES = {"electronics", "mobile", "laptop", "smartphone", "camera"}
    category = (claim.get("product_category") or "").lower()
    if any(h in category for h in HIGH_RISK_CATEGORIES):
        customer_id = str(claim["customer_id"])
        result = await db_session.execute(
            """
            SELECT COUNT(*) as cnt FROM claims
            WHERE customer_id = :cid AND LOWER(product_category) LIKE :cat
            """,
            {"cid": customer_id, "cat": f"%{category}%"}
        )
        row = result.mappings().first()
        cat_return_count = row["cnt"] if row else 0

        if cat_return_count >= 3:
            await save_fraud_signal(
                db_session, claim_id,
                signal_type="high_risk_category_abuse",
                severity=FraudSeverity.MEDIUM,
                confidence=0.68,
                reasoning=(
                    f"Customer has {cat_return_count} returns in high-risk category '{category}'. "
                    f"This pattern is consistent with electronics wardrobing or scam behavior."
                ),
                cross_claim_indicators={"category": category, "return_count": cat_return_count},
            )
            signals_detected.append("high_risk_category_abuse")

    return signals_detected


# ─────────────────────────────────────────────────────────────────────────────
# Detection 3: Cross-Org Fraud Ring
# ─────────────────────────────────────────────────────────────────────────────

async def detect_cross_org_patterns(db_session, claim: Dict[str, Any]) -> bool:
    """
    Flag if the same customer has filed claims across 3+ different seller organizations.
    Requires the `claims` table to store a seller/org identifier.
    """
    customer_id = str(claim["customer_id"])
    claim_id    = str(claim["claim_id"])

    # Count distinct order_ids (as a proxy for org diversity in Phase 2)
    result = await db_session.execute(
        "SELECT COUNT(DISTINCT order_id) as org_count FROM claims WHERE customer_id = :cid AND order_id IS NOT NULL",
        {"cid": customer_id}
    )
    row = result.mappings().first()
    org_count = row["org_count"] if row else 0

    if org_count >= 3:
        await save_fraud_signal(
            db_session, claim_id,
            signal_type="cross_org_fraud_ring",
            severity=FraudSeverity.HIGH,
            confidence=0.80,
            reasoning=(
                f"Customer has returns across {org_count} distinct organizations "
                f"— potential cross-platform fraud ring behavior."
            ),
            cross_claim_indicators={"org_count": org_count},
        )
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Detection 4: Wardrobing (via wear_analysis artifact)
# ─────────────────────────────────────────────────────────────────────────────

async def detect_wardrobing(db_session, claim: Dict[str, Any]) -> bool:
    """
    Cross-reference the wear_analysis artifact from Multi-Modal Processor.
    If wear_score > 0.70, flag as wardrobing.
    """
    claim_id = str(claim["claim_id"])

    # Fetch wear_analysis artifacts associated with this claim
    result = await db_session.execute(
        """
        SELECT ea.artifact_id, ea.evidence_id, ea.data, ea.confidence_score
        FROM evidence_artifacts ea
        JOIN evidence e ON ea.evidence_id = e.evidence_id
        WHERE e.claim_id = :claim_id AND ea.artifact_type = 'wear_analysis'
        ORDER BY ea.created_at DESC
        LIMIT 1
        """,
        {"claim_id": claim_id}
    )
    artifact = result.mappings().first()

    if not artifact:
        return False

    # Parse wear data
    data = artifact["data"] if isinstance(artifact["data"], dict) else json.loads(artifact["data"])
    wear_score = float(data.get("wear_score", 0.0))
    evidence_id = str(artifact["evidence_id"])

    WARDROBING_THRESHOLD = 0.70
    if wear_score >= WARDROBING_THRESHOLD:
        await save_fraud_signal(
            db_session, claim_id,
            signal_type="wardrobing",
            severity=FraudSeverity.HIGH,
            confidence=round(wear_score, 3),
            reasoning=(
                f"Product image shows heavy wear (wear_score={wear_score:.2f}). "
                f"Fabric condition indicates the item was used before returning. "
                f"Estimated usage: {data.get('estimated_wear_hours', 'unknown')} hours."
            ),
            cross_claim_indicators={
                "wear_score":            wear_score,
                "fold_detected":         data.get("fold_detected", False),
                "saturation_score":      data.get("saturation_score"),
                "edge_density":          data.get("edge_density"),
                "estimated_wear_hours":  data.get("estimated_wear_hours"),
            },
            source_evidence_id=evidence_id,
        )
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main Event Handler
# ─────────────────────────────────────────────────────────────────────────────

async def run_fraud_detection(payload: Dict[str, Any]) -> None:
    """
    Consumes evidence.processed event and runs all 4 fraud detection checks.
    Publishes fraud.analysis.complete event when done.
    """
    claim_id = payload.get("claim_id")
    if not claim_id:
        return

    logger.info("Running fraud detection for claim: %s", claim_id)
    start = datetime.utcnow()

    try:
        async with get_db_session() as db:
            # Load claim data
            result = await db.execute(
                "SELECT * FROM claims WHERE claim_id = :cid", {"cid": str(claim_id)}
            )
            claim = result.mappings().first()
            if not claim:
                logger.warning("Claim not found: %s", claim_id)
                return

            claim = dict(claim)

            # Run all detectors
            await detect_serial_fraudster(db, claim)
            await detect_behavioral_anomalies(db, claim)
            await detect_cross_org_patterns(db, claim)
            await detect_wardrobing(db, claim)

            # Count signals generated
            sig_result = await db.execute(
                "SELECT COUNT(*) as cnt, MAX(severity) as max_sev FROM fraud_signals WHERE claim_id = :cid",
                {"cid": str(claim_id)}
            )
            sig_row = sig_result.mappings().first()
            signal_count = sig_row["cnt"] if sig_row else 0
            max_severity = sig_row["max_sev"] if sig_row else None

            # Update claim status to PROCESSING → DECISION_PENDING_REVIEW
            await db.execute(
                "UPDATE claims SET status = 'DECISION_PENDING_REVIEW', updated_at = :now WHERE claim_id = :cid",
                {"cid": str(claim_id), "now": datetime.utcnow()}
            )

        elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        logger.info("Fraud detection completed for %s in %dms: %d signals", claim_id, elapsed_ms, signal_count)

        # Publish fraud.analysis.complete
        await publish_event("fraud.analysis.complete", {
            "event_type":   "fraud.analysis.complete",
            "claim_id":     str(claim_id),
            "signal_count": signal_count,
            "max_severity": max_severity,
            "elapsed_ms":   elapsed_ms,
            "timestamp":    datetime.utcnow().isoformat(),
        })

    except Exception as exc:
        logger.error("Fraud detection failed for claim %s: %s", claim_id, exc)


@app.on_event("startup")
async def startup():
    try:
        bus = await get_message_bus()
        await bus.subscribe("evidence.processed", run_fraud_detection)
        logger.info("Fraud Detection Engine subscribed to evidence.processed queue.")
    except Exception as exc:
        logger.warning("Could not connect to RabbitMQ on startup: %s", exc)


@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    return {"service": "fraud_engine", "status": "healthy" if db_ok else "degraded"}


@app.post("/api/v2/fraud/analyze/{claim_id}", tags=["Fraud Detection"])
async def analyze_claim_direct(claim_id: UUID):
    """Direct HTTP endpoint to trigger fraud analysis (for testing without RabbitMQ)."""
    await run_fraud_detection({"claim_id": str(claim_id)})
    return {"claim_id": str(claim_id), "status": "analysis_triggered"}


if __name__ == "__main__":
    port = int(os.getenv("FRAUD_ENGINE_PORT", "8083"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
