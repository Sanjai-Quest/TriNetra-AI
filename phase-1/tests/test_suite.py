"""
Unit Tests for TriNetra AI Phase 1 Normalization, Entity Resolution, Baselines & Reconciliation.
"""

import unittest
import os
import sys

# Ensure phase-1 root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from normalization.canonical_normalizer import CanonicalNormalizer
from resolution.entity_resolver import EntityResolver
from baselines.baseline_1_identity import Baseline1IdentityOnly
from baselines.baseline_2_weight import Baseline2WeightOnly
from baselines.baseline_3_timeline import Baseline3TimelineOnly
from engine.reconciliation_engine import ReconciliationEngine


class TestTriNetraPhase1(unittest.TestCase):

    def setUp(self):
        self.normalizer = CanonicalNormalizer()
        self.resolver = EntityResolver()
        self.b1 = Baseline1IdentityOnly()
        self.b2 = Baseline2WeightOnly()
        self.b3 = Baseline3TimelineOnly()
        self.engine = ReconciliationEngine()

    def test_sku_normalization(self):
        self.assertEqual(self.normalizer.normalize_sku("ts-204"), "TS-204")
        self.assertEqual(self.normalizer.normalize_sku("TS204"), "TS-204")
        self.assertEqual(self.normalizer.normalize_sku("TS 204"), "TS-204")
        self.assertEqual(self.normalizer.normalize_sku("KB100"), "KB-100")

    def test_weight_normalization(self):
        self.assertEqual(self.normalizer.normalize_weight("500g"), 500)
        self.assertEqual(self.normalizer.normalize_weight("0.5kg"), 500)
        self.assertEqual(self.normalizer.normalize_weight("500 grams"), 500)
        self.assertEqual(self.normalizer.normalize_weight(505), 505)

    def test_size_and_color_normalization(self):
        self.assertEqual(self.normalizer.normalize_size("Extra Large"), "XL")
        self.assertEqual(self.normalizer.normalize_size("x-large"), "XL")
        self.assertEqual(self.normalizer.normalize_color("bright red"), "RED")
        self.assertEqual(self.normalizer.normalize_color("dark blue"), "BLUE")

    def test_timestamp_normalization(self):
        ts = self.normalizer.normalize_timestamp("08/23/2026 10:00 AM")
        self.assertEqual(ts, "2026-08-23T10:00:00Z")

    def test_entity_resolver(self):
        self.resolver.register_mapping("CANONICAL-UUID-1", "SELLER", "PROD-001")
        cid, conf = self.resolver.resolve("SELLER", "PROD-001")
        self.assertEqual(cid, "CANONICAL-UUID-1")
        self.assertEqual(conf, 1.0)

    def test_reconciliation_weight_anomaly(self):
        evidence = [
            {"source": "ORDER", "sku": "TS-204"},
            {"source": "WAREHOUSE", "sku": "TS-204", "weight": 500},
            {"source": "CARRIER", "weight": 505},
            {"source": "RETURN", "sku": "TS-204", "weight": 210}
        ]
        result = self.engine.reconcile(evidence)
        self.assertEqual(result["status"], "CONFLICT")
        self.assertTrue(any(c["conflict_type"] == "WEIGHT_ANOMALY" for c in result["conflicts"]))

    def test_reconciliation_identity_conflict(self):
        evidence = [
            {"source": "ORDER", "sku": "TS-204"},
            {"source": "SELLER", "sku": "TS-203"},
            {"source": "WAREHOUSE", "sku": "TS-203"},
            {"source": "RETURN", "sku": "TS-203"}
        ]
        result = self.engine.reconcile(evidence)
        self.assertEqual(result["status"], "CONFLICT")
        self.assertTrue(any(c["conflict_type"] == "IDENTITY_CONFLICT" for c in result["conflicts"]))

    def test_reconciliation_temporal_conflict(self):
        evidence = [
            {"source": "ORDER", "sku": "TS-204", "timestamp": "2026-08-23T10:00:00Z"},
            {"source": "WAREHOUSE", "sku": "TS-204", "timestamp": "2026-08-23T09:30:00Z"}
        ]
        result = self.engine.reconcile(evidence)
        self.assertEqual(result["status"], "CONFLICT")
        self.assertTrue(any(c["conflict_type"] == "TEMPORAL_CONFLICT" for c in result["conflicts"]))


if __name__ == "__main__":
    unittest.main()
