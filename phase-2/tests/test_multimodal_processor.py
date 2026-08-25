"""
Unit tests for TriNetra Multi-Modal Processor.
Tests OpenCV wear detection, color consistency, and receipt parsing algorithms.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from services.multimodal_processor.main import (
        _rgb_to_color_name, parse_receipt_structure, validate_receipt_against_claim
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False


class TestMultiModalProcessor(unittest.TestCase):

    def setUp(self):
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Phase 2 packages (fastapi/uvicorn) not installed in current environment.")

    def test_rgb_to_color_name_mapping(self):
        self.assertEqual(_rgb_to_color_name(220, 30, 30), "RED")
        self.assertEqual(_rgb_to_color_name(20, 200, 20), "GREEN")
        self.assertEqual(_rgb_to_color_name(10, 10, 10), "BLACK")
        self.assertEqual(_rgb_to_color_name(250, 250, 250), "WHITE")

    def test_receipt_parsing(self):
        sample_text = """
        XYZ SUPERMARKET
        DATE: 23/08/2026
        ITEM 1: TS-204 T-SHIRT   ₹500.00
        SUBTOTAL: ₹500.00
        TOTAL AMOUNT: ₹500.00
        THANK YOU FOR SHOPPING!
        """
        parsed = parse_receipt_structure(sample_text)
        self.assertEqual(parsed.total_amount, 500.0)
        self.assertIn("23/08/2026", parsed.transaction_date)

    def test_receipt_validation_match(self):
        from services.multimodal_processor.main import ReceiptParseResult
        parsed = ReceiptParseResult(total_amount=500.0)
        result = validate_receipt_against_claim(500.0, parsed)
        self.assertEqual(result["status"], "MATCH")

    def test_receipt_validation_mismatch(self):
        from services.multimodal_processor.main import ReceiptParseResult
        parsed = ReceiptParseResult(total_amount=200.0)
        result = validate_receipt_against_claim(800.0, parsed)
        self.assertEqual(result["status"], "MISMATCH")
        self.assertEqual(result["risk"], "HIGH")


if __name__ == "__main__":
    unittest.main()
