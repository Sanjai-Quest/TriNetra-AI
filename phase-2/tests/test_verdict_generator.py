"""
Unit tests for TriNetra Verdict Generator reasoning and output formatting.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from services.verdict_generator.main import build_reasoning_text, VerdictEnum
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


class TestVerdictGenerator(unittest.TestCase):

    def setUp(self):
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Phase 2 packages not installed in current environment.")

    def test_reasoning_text_formatting(self):
        signals = [
            {"signal_type": "serial_fraudster", "severity": "high", "reasoning": "7 returns in 90 days"},
            {"signal_type": "wardrobing", "severity": "high", "reasoning": "heavy fabric wear detected"},
        ]
        text = build_reasoning_text(VerdictEnum.REJECT, 0.85, signals, phase1_conflict=True)

        self.assertIn("REJECT", text)
        self.assertIn("serial_fraudster", text)
        self.assertIn("wardrobing", text)
        self.assertIn("Phase 1 Reconciliation: CONFLICT", text)


if __name__ == "__main__":
    unittest.main()
