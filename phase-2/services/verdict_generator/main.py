"""
TriNetra Phase 2 — Service 5: Verdict Generator (Port 8084)

Responsibilities:
  - Consumes fraud.analysis.complete events from RabbitMQ
  - Aggregates all fraud signals for a claim
  - Imports and runs Phase 1 reconciliation logic
  - Applies weighted decision logic: REFUND / REJECT / INVESTIGATE
  - Saves VerdictReasoning to PostgreSQL
  - Updates claim status and confidence_score
  - Publishes verdict.generated event
  - Caches verdict in Redis
"""

import asyncio
import json
import logging
import os
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
from shared.redis_client import get_redis_cache
from shared.models import FraudSeverity, VerdictEnum, ClaimStatus

# ── Import Phase 1 reconciliation engine ────────────────────────────────────
PHASE1_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "phase-1")
if PHASE1_PATH not in sys.path:
    sys.path.insert(0, PHASE1_PATH)
try:
    from engine.reconciliation_engine import ReconciliationEngine
    from normalization.canonical_normalizer import CanonicalNormalizer
    PHASE1_ENGINE_AVAILABLE = True
except ImportError:
    PHASE1_ENGINE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verdict_generator")

app = FastAPI(
    title="TriNetra Verdict Generator",
    description="Aggregates fraud signals and Phase 1 reconciliation to generate REFUND/REJECT/INVESTIGATE verdicts",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# Fraud risk scorer
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_WEIGHTS = {
    FraudSeverity.CRITICAL.value: 0.40,
    FraudSeverity.HIGH.value:     0.25,
    FraudSeverity.MEDIUM.value:   0.12,
    FraudSeverity.LOW.value:      0.05,
}


def calculate_fraud_risk_score(signals: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
    """
    Compute composite fraud risk score from all fraud signals.
    Returns (score 0.0-1.0, factor_weights dict).
    """
    if not signals:
        return 0.0, {}

    raw_score = 0.0
    factor_weights: Dict[str, Any] = {}

    for signal in signals:
        severity   = signal.get("severity", "low")
        confidence = float(signal.get("confidence_score", 0.5))
        weight     = SEVERITY_WEIGHTS.get(severity, 0.05)
        contribution = weight * confidence
        raw_score   += contribution
        factor_weights[signal["signal_type"]] = {
            "severity":     severity,
            "confidence":   confidence,
            "contribution": round(contribution, 4),
        }

    # Normalize: cap at 1.0, avoid 1.0 for single low signal
    score = min(1.0, raw_score)
    return round(score, 4), factor_weights


def determine_verdict(
    fraud_risk_score: float,
    phase1_conflict: bool,
    signal_count: int,
    max_severity: Optional[str],
) -> Tuple[VerdictEnum, float]:
    """
    Decision logic combining fraud risk + Phase 1 reconciliation result.
    Returns (verdict, confidence_score).
    """
    # Critical signals → always REJECT
    if max_severity == "critical" or fraud_risk_score > 0.75:
        return VerdictEnum.REJECT, round(fraud_risk_score, 3)

    # Phase 1 conflict + fraud signals → INVESTIGATE
    if phase1_conflict or (fraud_risk_score > 0.40 and signal_count >= 1):
        combined = min(1.0, fraud_risk_score + (0.20 if phase1_conflict else 0.0))
        return VerdictEnum.INVESTIGATE, round(combined, 3)

    # Low fraud risk, no Phase 1 conflict → REFUND
    clean_confidence = 1.0 - fraud_risk_score
    return VerdictEnum.REFUND, round(clean_confidence, 3)


def build_reasoning_text(
    verdict: VerdictEnum,
    fraud_risk_score: float,
    signals: List[Dict[str, Any]],
    phase1_conflict: bool,
) -> str:
    lines = [
        f"Automated Verdict: {verdict.value} (fraud_risk_score={fraud_risk_score:.2f})",
        "",
    ]
    if signals:
        lines.append("Fraud Signals Detected:")
        for s in signals[:5]:
            lines.append(f"  • [{s['severity'].upper()}] {s['signal_type']}: {s.get('reasoning','')[:120]}")
    else:
        lines.append("No fraud signals detected.")

    if phase1_conflict:
        lines.append("\nPhase 1 Reconciliation: CONFLICT detected across stakeholder evidence.")

    lines.append(
        "\nInvestigator review recommended."
        if verdict == VerdictEnum.INVESTIGATE
        else "\nConfidence threshold met for automated decision."
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 Reconciliation Integration
# ─────────────────────────────────────────────────────────────────────────────

async def run_phase1_reconciliation(db_session, claim_id: str) -> bool:
    """
    Pull evidence attributes from Phase 2 DB and run Phase 1 engine.
    Returns True if any conflict is detected.
    """
    if not PHASE1_ENGINE_AVAILABLE:
        return False

    try:
        engine = ReconciliationEngine()
        normalizer = CanonicalNormalizer()

        # Fetch evidence records for this claim
        result = await db_session.execute(
            "SELECT evidence_type, metadata FROM evidence WHERE claim_id = :cid",
            {"cid": claim_id}
        )
        rows = result.mappings().all()
        if not rows:
            return False

        evidence_list = []
        for row in rows:
            meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {})
            evidence_list.append({
                "source": row["evidence_type"].upper(),
                **meta,
            })

        normalized = [normalizer.normalize_evidence_record(e) for e in evidence_list]
        verdict = engine.reconcile(normalized)
        return len(verdict.get("conflicts", [])) > 0

    except Exception as exc:
        logger.warning("Phase 1 reconciliation skipped: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Main Event Handler
# ─────────────────────────────────────────────────────────────────────────────

async def generate_verdict_for_claim(payload: Dict[str, Any]) -> None:
    """
    Consumes fraud.analysis.complete event and generates the final verdict.
    """
    claim_id = payload.get("claim_id")
    if not claim_id:
        return

    logger.info("Generating verdict for claim: %s", claim_id)

    try:
        async with get_db_session() as db:
            # 1. Load claim
            claim_result = await db.execute(
                "SELECT * FROM claims WHERE claim_id = :cid", {"cid": str(claim_id)}
            )
            claim = claim_result.mappings().first()
            if not claim:
                return
            claim = dict(claim)

            # 2. Load all fraud signals
            sig_result = await db.execute(
                "SELECT * FROM fraud_signals WHERE claim_id = :cid ORDER BY confidence_score DESC",
                {"cid": str(claim_id)}
            )
            signals = [dict(r) for r in sig_result.mappings().all()]

            # 3. Phase 1 reconciliation
            phase1_conflict = await run_phase1_reconciliation(db, str(claim_id))

            # 4. Score + decide
            fraud_risk_score, factor_weights = calculate_fraud_risk_score(signals)
            max_severity = signals[0]["severity"] if signals else None
            verdict, confidence = determine_verdict(
                fraud_risk_score, phase1_conflict, len(signals), max_severity
            )

            # 5. Build reasoning
            reasoning_text = build_reasoning_text(verdict, fraud_risk_score, signals, phase1_conflict)

            # 6. Determine final claim status
            new_status_map = {
                VerdictEnum.REFUND:      ClaimStatus.APPROVED.value,
                VerdictEnum.REJECT:      ClaimStatus.REJECTED.value,
                VerdictEnum.INVESTIGATE: ClaimStatus.DECISION_PENDING_REVIEW.value,
            }
            new_status = new_status_map[verdict]

            # 7. Save VerdictReasoning record
            evidence_summary = {
                "fraud_risk_score": fraud_risk_score,
                "signal_count":     len(signals),
                "max_severity":     max_severity,
                "phase1_conflict":  phase1_conflict,
            }
            fraud_signal_list = [
                {"type": s["signal_type"], "severity": s["severity"], "confidence": s["confidence_score"]}
                for s in signals
            ]

            await db.execute(
                """
                INSERT INTO verdict_reasoning (
                    reasoning_id, claim_id, verdict, evidence_summary,
                    fraud_signals_detected, factor_weights,
                    final_confidence_score, reasoning_text, generated_at
                ) VALUES (
                    :reasoning_id, :claim_id, :verdict, :evidence_summary,
                    :fraud_signals, :factor_weights,
                    :confidence, :reasoning_text, :now
                )
                """,
                {
                    "reasoning_id":     str(uuid4()),
                    "claim_id":         str(claim_id),
                    "verdict":          verdict.value,
                    "evidence_summary": json.dumps(evidence_summary, default=str),
                    "fraud_signals":    json.dumps(fraud_signal_list, default=str),
                    "factor_weights":   json.dumps(factor_weights, default=str),
                    "confidence":       confidence,
                    "reasoning_text":   reasoning_text,
                    "now":              datetime.utcnow(),
                }
            )

            # 8. Update claim
            await db.execute(
                """
                UPDATE claims SET
                    status = :status, automated_verdict = :verdict,
                    confidence_score = :confidence, updated_at = :now
                WHERE claim_id = :cid
                """,
                {
                    "status":     new_status,
                    "verdict":    verdict.value,
                    "confidence": confidence,
                    "cid":        str(claim_id),
                    "now":        datetime.utcnow(),
                }
            )

        # 9. Cache verdict in Redis
        cache = await get_redis_cache()
        await cache.cache_verdict(UUID(str(claim_id)), {
            "verdict": verdict.value,
            "confidence_score": confidence,
            "fraud_risk_score": fraud_risk_score,
            "signal_count": len(signals),
        })

        # 10. Publish verdict.generated
        await publish_event("verdict.generated", {
            "event_type":       "verdict.generated",
            "claim_id":         str(claim_id),
            "verdict":          verdict.value,
            "confidence_score": confidence,
            "fraud_risk_score": fraud_risk_score,
            "signal_count":     len(signals),
            "timestamp":        datetime.utcnow().isoformat(),
        })

        logger.info(
            "Verdict generated for %s: %s (confidence=%.2f, fraud_risk=%.2f, signals=%d)",
            claim_id, verdict.value, confidence, fraud_risk_score, len(signals)
        )

    except Exception as exc:
        logger.error("Verdict generation failed for claim %s: %s", claim_id, exc)


@app.on_event("startup")
async def startup():
    try:
        bus = await get_message_bus()
        await bus.subscribe("fraud.analysis.complete", generate_verdict_for_claim)
        logger.info("Verdict Generator subscribed to fraud.analysis.complete queue.")
    except Exception as exc:
        logger.warning("Could not connect to RabbitMQ on startup: %s", exc)


@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    return {
        "service": "verdict_generator",
        "status": "healthy" if db_ok else "degraded",
        "phase1_engine_available": PHASE1_ENGINE_AVAILABLE,
    }


@app.post("/api/v2/verdict/generate/{claim_id}", tags=["Verdict"])
async def generate_verdict_direct(claim_id: UUID):
    """Direct HTTP endpoint to trigger verdict generation (testing without RabbitMQ)."""
    await generate_verdict_for_claim({"claim_id": str(claim_id)})
    return {"claim_id": str(claim_id), "status": "verdict_generation_triggered"}


if __name__ == "__main__":
    port = int(os.getenv("VERDICT_GENERATOR_PORT", "8084"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
