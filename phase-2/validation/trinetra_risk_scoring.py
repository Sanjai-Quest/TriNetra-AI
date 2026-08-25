"""
TriNetra AI — Phase 2: Risk Scoring Service
Computes dispute-level fraud risk from 5 independent factors:
  1. Buyer Trust Score (35% weight)
  2. Category Fraud Baseline (25% weight)
  3. Evidence Completeness (20% weight)
  4. Seller Reliability (10% weight)
  5. Price Risk (10% weight)

Formula: risk_score = Σ(factor_score × weight)
Friction Mapping:
  [0.00, 0.25) -> AUTOMATED (2-hour automated processing)
  [0.25, 0.50) -> LOW (24-hour verification)
  [0.50, 0.75) -> MEDIUM (72-hour manual review)
  [0.75, 1.00] -> HIGH (7-day deep fraud investigation)
"""

import enum
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger("RiskScoringService")


class FrictionLevel(str, enum.Enum):
    AUTOMATED = "AUTOMATED"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ─── WEIGHTS (Sum = 1.00) ───────────────────────────────────────────────────
WEIGHT_BUYER_TRUST = 0.35
WEIGHT_CATEGORY_BASELINE = 0.25
WEIGHT_EVIDENCE_COMPLETENESS = 0.20
WEIGHT_SELLER_RELIABILITY = 0.10
WEIGHT_PRICE_RISK = 0.10

# ─── CATEGORY BASELINES ──────────────────────────────────────────────────────
CATEGORY_FRAUD_BASELINES = {
    "electronics": 0.08,
    "mobile": 0.08,
    "laptop": 0.08,
    "fashion": 0.05,
    "apparel": 0.05,
    "clothing": 0.05,
    "apparel/clothing": 0.05,
    "footwear": 0.05,
    "beauty": 0.04,
    "cosmetics": 0.04,
    "home": 0.03,
    "kitchen": 0.03,
    "books": 0.02,
    "general": 0.04,
}

# ─── PRICE BRACKETS (INR) ───────────────────────────────────────────────────
# <500: 0.05 | 500-2000: 0.10 | 2000-5000: 0.15 | >5000: 0.20
PRICE_RISK_BRACKETS = [
    (500, 0.05),
    (2000, 0.10),
    (5000, 0.15),
    (float("inf"), 0.20),
]


@dataclass
class FactorScore:
    value: float
    source: str = "computed"
    cached: bool = False

    def __post_init__(self):
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"Factor score must be between 0.0 and 1.0, got: {self.value}")


@dataclass
class RiskScoreResult:
    score: float
    friction_level: FrictionLevel
    factors: Dict[str, float]
    factor_weights: Dict[str, float]
    dispute_id: Optional[str] = None
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Risk score must be between 0.0 and 1.0, got: {self.score}")


@dataclass
class Dispute:
    id: str
    buyer_id: str
    seller_id: str
    category: str
    price: float
    evidence_sources_present: int = 5
    evidence_sources_expected: int = 5
    buyer_return_count: Optional[int] = None
    buyer_total_orders: Optional[int] = None
    seller_dispute_count: Optional[int] = None
    seller_total_sales: Optional[int] = None
    severity: Optional[str] = None


class InMemoryCache:
    """Fast in-memory cache simulating Redis with TTL enforcement."""

    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            val, expiry = self._store[key]
            if time.time() < expiry:
                self.hits += 1
                return val
            else:
                del self._store[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        self._store[key] = (value, time.time() + ttl_seconds)

    def clear(self):
        self._store.clear()
        self.hits = 0
        self.misses = 0


class RiskScoringService:
    """
    Computes dispute-level fraud risk scores following the 5-factor weighted formula.
    Integrates with Redis (or mock cache) and maintains an immutable audit log.
    """

    def __init__(self, redis_client: Optional[Any] = None):
        self.redis = redis_client or InMemoryCache()
        self.audit_log: List[Dict[str, Any]] = []

    # ── Factor 1: Buyer Trust Score (35% weight) ──────────────────────────────
    def get_buyer_trust_score(
        self,
        buyer_id: str,
        return_count: Optional[int] = None,
        total_orders: Optional[int] = None,
    ) -> FactorScore:
        """
        Buyer's return rate: return_count / total_orders.
        0 returns / 100 orders = 0.0 (perfect)
        5 returns / 100 orders = 0.05 (good)
        50 returns / 100 orders = 0.50 (high risk)
        Cached with 1 hour (3600s) TTL.
        """
        cache_key = f"buyer_trust:{buyer_id}"
        cached = self.redis.get(cache_key)
        if cached is not None:
            return FactorScore(value=float(cached), source="cache", cached=True)

        if total_orders is None or total_orders <= 0:
            val = 0.10  # Default neutral for new buyers
        elif return_count is None or return_count <= 0:
            val = 0.00
        else:
            val = min(1.0, max(0.0, float(return_count) / float(total_orders)))

        val = round(val, 4)
        self.redis.set(cache_key, val, ttl_seconds=3600)
        return FactorScore(value=val, source="computed", cached=False)

    # ── Factor 2: Category Fraud Baseline (25% weight) ────────────────────────
    def get_category_fraud_baseline(self, category: str) -> FactorScore:
        """
        Industry baseline fraud rate by category.
        Electronics: 0.08 | Fashion: 0.05 | Books: 0.02 | General: 0.04
        Cached with 24 hours (86400s) TTL.
        """
        norm_cat = (category or "general").strip().lower()
        cache_key = f"category_fraud_rate:{norm_cat}"
        cached = self.redis.get(cache_key)
        if cached is not None:
            return FactorScore(value=float(cached), source="cache", cached=True)

        val = CATEGORY_FRAUD_BASELINES.get(norm_cat, 0.04)
        val = round(val, 4)
        self.redis.set(cache_key, val, ttl_seconds=86400)
        return FactorScore(value=val, source="computed", cached=False)

    # ── Factor 3: Evidence Completeness (20% weight) ──────────────────────────
    def get_evidence_completeness(self, dispute: Dispute) -> FactorScore:
        """
        Completeness of physical & telemetry evidence across all expected sources.
        evidence_sources_present / evidence_sources_expected.
        All 5 sources present = 1.0 (5/5)
        4 sources = 0.8 (4/5)
        3 sources = 0.6 (3/5)
        Computed per dispute (NOT cached).
        """
        expected = max(1, dispute.evidence_sources_expected)
        present = min(expected, max(0, dispute.evidence_sources_present))
        val = round(float(present) / float(expected), 4)
        return FactorScore(value=val, source="computed", cached=False)

    # ── Factor 4: Seller Reliability (10% weight) ─────────────────────────────
    def get_seller_reliability(
        self,
        seller_id: str,
        refund_disputes: Optional[int] = None,
        total_sales: Optional[int] = None,
    ) -> FactorScore:
        """
        Seller's dispute / refund rate: refund_disputes / total_sales.
        1 dispute / 100 sales = 0.01
        Cached with 1 hour (3600s) TTL.
        """
        cache_key = f"seller_reliability:{seller_id}"
        cached = self.redis.get(cache_key)
        if cached is not None:
            return FactorScore(value=float(cached), source="cache", cached=True)

        if total_sales is None or total_sales <= 0:
            val = 0.05  # Default neutral for new sellers
        elif refund_disputes is None or refund_disputes <= 0:
            val = 0.00
        else:
            val = min(1.0, max(0.0, float(refund_disputes) / float(total_sales)))

        val = round(val, 4)
        self.redis.set(cache_key, val, ttl_seconds=3600)
        return FactorScore(value=val, source="computed", cached=False)

    # ── Factor 5: Price Risk (10% weight) ─────────────────────────────────────
    def get_price_risk(self, price: float, category: Optional[str] = None) -> FactorScore:
        """
        Price tier risk multiplier:
        <₹500: 0.05 | ₹500-2000: 0.10 | ₹2000-5000: 0.15 | >₹5000: 0.20
        Cached with 24 hours (86400s) TTL.
        """
        p = max(0.0, float(price))
        bracket_key = "tier1" if p < 500 else ("tier2" if p <= 2000 else ("tier3" if p <= 5000 else "tier4"))
        cache_key = f"price_risk_multiplier:{bracket_key}"

        cached = self.redis.get(cache_key)
        if cached is not None:
            return FactorScore(value=float(cached), source="cache", cached=True)

        for limit, score in PRICE_RISK_BRACKETS:
            if p <= limit:
                val = score
                break
        else:
            val = 0.20

        val = round(val, 4)
        self.redis.set(cache_key, val, ttl_seconds=86400)
        return FactorScore(value=val, source="computed", cached=False)

    # ── Adaptive Friction Mapping ─────────────────────────────────────────────
    @staticmethod
    def map_risk_to_friction(risk_score: float) -> FrictionLevel:
        """
        Maps risk score to adaptive friction review level:
        [0.00, 0.25) -> AUTOMATED
        [0.25, 0.50) -> LOW
        [0.50, 0.75) -> MEDIUM
        [0.75, 1.00] -> HIGH
        """
        if risk_score < 0.25:
            return FrictionLevel.AUTOMATED
        elif risk_score < 0.50:
            return FrictionLevel.LOW
        elif risk_score < 0.75:
            return FrictionLevel.MEDIUM
        else:
            return FrictionLevel.HIGH

    # ── Core Risk Computation ─────────────────────────────────────────────────
    def compute_risk_score(
        self,
        dispute: Optional[Dispute] = None,
        buyer_trust: Optional[float] = None,
        category_baseline: Optional[float] = None,
        evidence_complete: Optional[float] = None,
        seller_reliability: Optional[float] = None,
        price_risk: Optional[float] = None,
    ) -> RiskScoreResult:
        """
        Computes composite risk score:
        risk = (0.35 × buyer_trust) + (0.25 × category_baseline) +
               (0.20 × evidence_complete) + (0.10 × seller_reliability) +
               (0.10 × price_risk)
        """
        if dispute is not None:
            f_buyer = self.get_buyer_trust_score(
                dispute.buyer_id, dispute.buyer_return_count, dispute.buyer_total_orders
            ).value if buyer_trust is None else buyer_trust

            f_cat = self.get_category_fraud_baseline(dispute.category).value if category_baseline is None else category_baseline

            f_ev = self.get_evidence_completeness(dispute).value if evidence_complete is None else evidence_complete

            f_seller = self.get_seller_reliability(
                dispute.seller_id, dispute.seller_dispute_count, dispute.seller_total_sales
            ).value if seller_reliability is None else seller_reliability

            f_price = self.get_price_risk(dispute.price, dispute.category).value if price_risk is None else price_risk

            dispute_id = dispute.id
        else:
            f_buyer = float(buyer_trust if buyer_trust is not None else 0.0)
            f_cat = float(category_baseline if category_baseline is not None else 0.04)
            f_ev = float(evidence_complete if evidence_complete is not None else 1.0)
            f_seller = float(seller_reliability if seller_reliability is not None else 0.0)
            f_price = float(price_risk if price_risk is not None else 0.05)
            dispute_id = None

        # Weighted calculation
        raw_score = (
            (WEIGHT_BUYER_TRUST * f_buyer) +
            (WEIGHT_CATEGORY_BASELINE * f_cat) +
            (WEIGHT_EVIDENCE_COMPLETENESS * f_ev) +
            (WEIGHT_SELLER_RELIABILITY * f_seller) +
            (WEIGHT_PRICE_RISK * f_price)
        )

        final_score = round(min(1.0, max(0.0, raw_score)), 4)
        friction = self.map_risk_to_friction(final_score)

        factors = {
            "buyer_trust": round(f_buyer, 4),
            "category_baseline": round(f_cat, 4),
            "evidence_complete": round(f_ev, 4),
            "seller_reliability": round(f_seller, 4),
            "price_risk": round(f_price, 4),
        }

        weights = {
            "buyer_trust": WEIGHT_BUYER_TRUST,
            "category_baseline": WEIGHT_CATEGORY_BASELINE,
            "evidence_complete": WEIGHT_EVIDENCE_COMPLETENESS,
            "seller_reliability": WEIGHT_SELLER_RELIABILITY,
            "price_risk": WEIGHT_PRICE_RISK,
        }

        result = RiskScoreResult(
            score=final_score,
            friction_level=friction,
            factors=factors,
            factor_weights=weights,
            dispute_id=dispute_id,
        )

        # Log immutable audit event
        self._log_audit_event(result)

        return result

    def _log_audit_event(self, result: RiskScoreResult):
        """Append immutable audit log entry for this risk computation."""
        log_entry = {
            "event_id": str(uuid4()),
            "event_type": "RISK_COMPUTED",
            "dispute_id": result.dispute_id,
            "event_data": {
                "risk_score": result.score,
                "friction_level": result.friction_level.value,
                "factors": result.factors,
                "factor_weights": result.factor_weights,
            },
            "actor": "system",
            "created_at": result.computed_at,
        }
        self.audit_log.append(log_entry)


def compute_risk_score(**kwargs) -> float:
    """Convenience helper matching formula validation signature."""
    service = RiskScoringService()
    res = service.compute_risk_score(**kwargs)
    return res.score
