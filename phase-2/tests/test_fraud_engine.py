"""
Unit & Integration Tests for TriNetra Phase 2 Fraud Detection Engine.
Tests serial fraudster detection, behavioral anomalies, and wardrobing logic.
"""

import unittest
from datetime import datetime, timedelta
from uuid import uuid4

# Import detection logic directly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from shared.models import FraudSeverity
    from services.verdict_generator.main import (
        SEVERITY_WEIGHTS, calculate_fraud_risk_score, determine_verdict, VerdictEnum
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Note: Phase 2 dependencies not installed yet ({e}). Skipping live import tests.")


class TestFraudDetectionEngine(unittest.TestCase):

    def setUp(self):
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Phase 2 packages (pydantic/uvicorn) not installed in current environment.")

    def test_severity_weights(self):
        self.assertEqual(SEVERITY_WEIGHTS[FraudSeverity.CRITICAL.value], 0.40)
        self.assertEqual(SEVERITY_WEIGHTS[FraudSeverity.HIGH.value], 0.25)
        self.assertEqual(SEVERITY_WEIGHTS[FraudSeverity.MEDIUM.value], 0.12)
        self.assertEqual(SEVERITY_WEIGHTS[FraudSeverity.LOW.value], 0.05)

    def test_fraud_risk_score_calculation(self):
        from services.verdict_generator.main import calculate_fraud_risk_score

        signals = [
            {"signal_type": "serial_fraudster", "severity": "high", "confidence_score": 0.85},
            {"signal_type": "wardrobing", "severity": "high", "confidence_score": 0.80},
        ]
        score, weights = calculate_fraud_risk_score(signals)

        # Expected: 0.25 * 0.85 + 0.25 * 0.80 = 0.2125 + 0.2000 = 0.4125
        self.assertAlmostEqual(score, 0.4125, places=3)
        self.assertIn("serial_fraudster", weights)
        self.assertIn("wardrobing", weights)

    def test_critical_signal_forces_reject(self):
        from services.verdict_generator.main import determine_verdict, VerdictEnum

        verdict, conf = determine_verdict(
            fraud_risk_score=0.85,
            phase1_conflict=False,
            signal_count=2,
            max_severity="critical"
        )
        self.assertEqual(verdict, VerdictEnum.REJECT)

    def test_clean_claim_yields_refund(self):
        from services.verdict_generator.main import determine_verdict, VerdictEnum

        verdict, conf = determine_verdict(
            fraud_risk_score=0.05,
            phase1_conflict=False,
            signal_count=0,
            max_severity=None
        )
        self.assertEqual(verdict, VerdictEnum.REFUND)
        self.assertGreaterEqual(conf, 0.90)

    def test_phase1_conflict_yields_investigate(self):
        from services.verdict_generator.main import determine_verdict, VerdictEnum

        verdict, conf = determine_verdict(
            fraud_risk_score=0.20,
            phase1_conflict=True,
            signal_count=1,
            max_severity="medium"
        )
        self.assertEqual(verdict, VerdictEnum.INVESTIGATE)


if __name__ == "__main__":
    unittest.main()
