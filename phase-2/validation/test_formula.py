"""
Step 1: Formula Implementation Verification & Unit Tests (30+ assertions)
Verifies exact 5-factor weighted calculation:
  risk = (0.35 * buyer_trust) + (0.25 * category_baseline) +
         (0.20 * evidence_complete) + (0.10 * seller_reliability) +
         (0.10 * price_risk)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from trinetra_risk_scoring import (
    RiskScoringService, Dispute, FrictionLevel, FactorScore,
    WEIGHT_BUYER_TRUST, WEIGHT_CATEGORY_BASELINE, WEIGHT_EVIDENCE_COMPLETENESS,
    WEIGHT_SELLER_RELIABILITY, WEIGHT_PRICE_RISK, compute_risk_score
)


class TestRiskFormula(unittest.TestCase):

    def setUp(self):
        self.service = RiskScoringService()

    # ── Category 1: Weights & Basic Formula (5 tests) ─────────────────────────
    def test_weights_sum_to_one(self):
        total_weight = (
            WEIGHT_BUYER_TRUST + WEIGHT_CATEGORY_BASELINE +
            WEIGHT_EVIDENCE_COMPLETENESS + WEIGHT_SELLER_RELIABILITY + WEIGHT_PRICE_RISK
        )
        self.assertAlmostEqual(total_weight, 1.00, places=4)

    def test_formula_low_risk_dispute(self):
        factors = {
            'buyer_trust': 0.0,
            'category_baseline': 0.05,
            'evidence_complete': 1.0,
            'seller_reliability': 0.0,
            'price_risk': 0.05,
        }
        # expected = (0.35*0.0) + (0.25*0.05) + (0.20*1.0) + (0.10*0.0) + (0.10*0.05)
        # expected = 0.0 + 0.0125 + 0.20 + 0.0 + 0.005 = 0.2175
        expected = 0.2175
        res = compute_risk_score(**factors)
        self.assertAlmostEqual(res, expected, places=4)

    def test_formula_high_risk_dispute(self):
        factors = {
            'buyer_trust': 0.40,
            'category_baseline': 0.15,
            'evidence_complete': 0.40,
            'seller_reliability': 0.30,
            'price_risk': 0.20,
        }
        # expected = (0.35*0.40) + (0.25*0.15) + (0.20*0.40) + (0.10*0.30) + (0.10*0.20)
        # expected = 0.14 + 0.0375 + 0.08 + 0.03 + 0.02 = 0.3075
        expected = 0.3075
        res = compute_risk_score(**factors)
        self.assertAlmostEqual(res, expected, places=4)

    def test_formula_all_zeros(self):
        res = self.service.compute_risk_score(
            buyer_trust=0.0, category_baseline=0.0, evidence_complete=0.0,
            seller_reliability=0.0, price_risk=0.0
        )
        self.assertEqual(res.score, 0.0)
        self.assertEqual(res.friction_level, FrictionLevel.AUTOMATED)

    def test_formula_all_ones(self):
        res = self.service.compute_risk_score(
            buyer_trust=1.0, category_baseline=1.0, evidence_complete=1.0,
            seller_reliability=1.0, price_risk=1.0
        )
        self.assertEqual(res.score, 1.0)
        self.assertEqual(res.friction_level, FrictionLevel.HIGH)

    # ── Category 2: Buyer Trust Score (4 tests) ───────────────────────────────
    def test_buyer_trust_perfect_buyer(self):
        score = self.service.get_buyer_trust_score("buyer-1", return_count=0, total_orders=100)
        self.assertEqual(score.value, 0.0)

    def test_buyer_trust_good_buyer(self):
        score = self.service.get_buyer_trust_score("buyer-2", return_count=5, total_orders=100)
        self.assertEqual(score.value, 0.05)

    def test_buyer_trust_medium_risk(self):
        score = self.service.get_buyer_trust_score("buyer-3", return_count=20, total_orders=100)
        self.assertEqual(score.value, 0.20)

    def test_buyer_trust_high_risk(self):
        score = self.service.get_buyer_trust_score("buyer-4", return_count=50, total_orders=100)
        self.assertEqual(score.value, 0.50)

    # ── Category 3: Seller Reliability (3 tests) ──────────────────────────────
    def test_seller_reliability_trusted(self):
        score = self.service.get_seller_reliability("seller-1", refund_disputes=1, total_sales=100)
        self.assertEqual(score.value, 0.01)

    def test_seller_reliability_perfect(self):
        score = self.service.get_seller_reliability("seller-2", refund_disputes=0, total_sales=500)
        self.assertEqual(score.value, 0.0)

    def test_seller_reliability_risky(self):
        score = self.service.get_seller_reliability("seller-3", refund_disputes=25, total_sales=100)
        self.assertEqual(score.value, 0.25)

    # ── Category 4: Category Fraud Baseline (4 tests) ─────────────────────────
    def test_category_baseline_electronics(self):
        score = self.service.get_category_fraud_baseline("electronics")
        self.assertEqual(score.value, 0.08)

    def test_category_baseline_fashion(self):
        score = self.service.get_category_fraud_baseline("fashion")
        self.assertEqual(score.value, 0.05)

    def test_category_baseline_books(self):
        score = self.service.get_category_fraud_baseline("books")
        self.assertEqual(score.value, 0.02)

    def test_category_baseline_unknown_general(self):
        score = self.service.get_category_fraud_baseline("stationery")
        self.assertEqual(score.value, 0.04)

    # ── Category 5: Evidence Completeness (4 tests) ───────────────────────────
    def test_evidence_completeness_all_sources(self):
        d = Dispute("d1", "b1", "s1", "electronics", 1000, evidence_sources_present=5, evidence_sources_expected=5)
        score = self.service.get_evidence_completeness(d)
        self.assertEqual(score.value, 1.0)

    def test_evidence_completeness_four_sources(self):
        d = Dispute("d2", "b1", "s1", "electronics", 1000, evidence_sources_present=4, evidence_sources_expected=5)
        score = self.service.get_evidence_completeness(d)
        self.assertEqual(score.value, 0.8)

    def test_evidence_completeness_three_sources(self):
        d = Dispute("d3", "b1", "s1", "electronics", 1000, evidence_sources_present=3, evidence_sources_expected=5)
        score = self.service.get_evidence_completeness(d)
        self.assertEqual(score.value, 0.6)

    def test_evidence_completeness_no_sources(self):
        d = Dispute("d4", "b1", "s1", "electronics", 1000, evidence_sources_present=0, evidence_sources_expected=5)
        score = self.service.get_evidence_completeness(d)
        self.assertEqual(score.value, 0.0)

    # ── Category 6: Price Risk (4 tests) ──────────────────────────────────────
    def test_price_risk_tier1_low(self):
        score = self.service.get_price_risk(300)
        self.assertEqual(score.value, 0.05)

    def test_price_risk_tier2_medium(self):
        score = self.service.get_price_risk(1500)
        self.assertEqual(score.value, 0.10)

    def test_price_risk_tier3_medium_high(self):
        score = self.service.get_price_risk(3500)
        self.assertEqual(score.value, 0.15)

    def test_price_risk_tier4_high(self):
        score = self.service.get_price_risk(12000)
        self.assertEqual(score.value, 0.20)

    # ── Category 7: Adaptive Friction Mapping & Boundaries (6 tests) ──────────
    def test_friction_automated(self):
        self.assertEqual(self.service.map_risk_to_friction(0.10), FrictionLevel.AUTOMATED)
        self.assertEqual(self.service.map_risk_to_friction(0.249), FrictionLevel.AUTOMATED)

    def test_friction_low(self):
        self.assertEqual(self.service.map_risk_to_friction(0.25), FrictionLevel.LOW)
        self.assertEqual(self.service.map_risk_to_friction(0.499), FrictionLevel.LOW)

    def test_friction_medium(self):
        self.assertEqual(self.service.map_risk_to_friction(0.50), FrictionLevel.MEDIUM)
        self.assertEqual(self.service.map_risk_to_friction(0.749), FrictionLevel.MEDIUM)

    def test_friction_high(self):
        self.assertEqual(self.service.map_risk_to_friction(0.75), FrictionLevel.HIGH)
        self.assertEqual(self.service.map_risk_to_friction(1.00), FrictionLevel.HIGH)

    def test_boundary_zero_twenty_five(self):
        # 0.25 must be mapped to LOW, NOT AUTOMATED
        self.assertEqual(self.service.map_risk_to_friction(0.25), FrictionLevel.LOW)

    def test_boundary_zero_seventy_five(self):
        # 0.75 must be mapped to HIGH, NOT MEDIUM
        self.assertEqual(self.service.map_risk_to_friction(0.75), FrictionLevel.HIGH)


if __name__ == "__main__":
    unittest.main()
