"""
Step 7: Audit Trail Logging Verification
Verifies that every risk computation creates an immutable audit record containing:
  - event_type: "RISK_COMPUTED"
  - dispute_id
  - event_data: { risk_score, friction_level, factors, factor_weights }
  - actor: "system"
  - created_at: timestamp
"""

import os
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

from trinetra_risk_scoring import RiskScoringService, Dispute


class TestAuditLogging(unittest.TestCase):

    def setUp(self):
        self.service = RiskScoringService()

    def test_audit_log_entry_created_on_computation(self):
        dispute = Dispute(
            id="disp-audit-101",
            buyer_id="buyer-audit-1",
            seller_id="seller-audit-1",
            category="electronics",
            price=4500,
            evidence_sources_present=5,
            evidence_sources_expected=5,
        )

        res = self.service.compute_risk_score(dispute)

        self.assertEqual(len(self.service.audit_log), 1)
        entry = self.service.audit_log[0]

        # Verify required audit fields
        self.assertEqual(entry["event_type"], "RISK_COMPUTED")
        self.assertEqual(entry["dispute_id"], "disp-audit-101")
        self.assertEqual(entry["actor"], "system")
        self.assertIsNotNone(entry["created_at"])
        self.assertIn("event_id", entry)

        # Verify event_data payload
        payload = entry["event_data"]
        self.assertEqual(payload["risk_score"], res.score)
        self.assertEqual(payload["friction_level"], res.friction_level.value)
        self.assertIn("factors", payload)
        self.assertIn("factor_weights", payload)

        factors = payload["factors"]
        self.assertIn("buyer_trust", factors)
        self.assertIn("category_baseline", factors)
        self.assertIn("evidence_complete", factors)
        self.assertIn("seller_reliability", factors)
        self.assertIn("price_risk", factors)

    def test_audit_log_records_multiple_disputes(self):
        for i in range(5):
            d = Dispute(f"disp-seq-{i}", f"buyer-{i}", f"seller-{i}", "fashion", 1200)
            self.service.compute_risk_score(d)

        self.assertEqual(len(self.service.audit_log), 5)
        for i, entry in enumerate(self.service.audit_log):
            self.assertEqual(entry["dispute_id"], f"disp-seq-{i}")
            self.assertEqual(entry["event_type"], "RISK_COMPUTED")


if __name__ == "__main__":
    unittest.main()
