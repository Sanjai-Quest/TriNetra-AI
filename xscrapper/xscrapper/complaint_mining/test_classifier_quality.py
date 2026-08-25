"""
Regression test suite for TriNetra AI Complaint Classifier & Quality Inspector.
Ensures that known noisy/non-ecommerce titles are strictly rejected and genuine complaints are accepted.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from complaint_mining.processing.classifier import ComplaintClassifier


class TestClassifierQuality(unittest.TestCase):

    def setUp(self):
        self.classifier = ComplaintClassifier()

    def test_known_bad_titles_must_be_rejected(self):
        """Hardcoded audit failure examples that MUST fail inspect_quality."""
        bad_cases = [
            ("Missing (2023 film)", "Full movie review and details of the 2023 mystery thriller film Missing."),
            ("Kidnappings & Missing Persons — FBI", "FBI official warning and report on kidnappings and missing persons statistics."),
            ("Supported AI models in GitHub Copilot", "GitHub Copilot documentation listing supported AI models for Visual Studio Code."),
            ("Check Income Tax Refund Status", "Track your income tax return refund status online on NSDL e-Filing portal."),
            ("6504 Used Cars in Bangalore", "Buy used cars in Bangalore at best prices. Second hand cars for sale."),
            ("Viking Cruises Reviews and Complaints", "Read customer reviews and cruise line ratings for Viking Cruises trips."),
            ("COUNTERFEIT Definition & Meaning", "Merriam-Webster dictionary definition and meaning of the word counterfeit in English."),
            ("Prezzo dei titoli... Microsoft", "Prezzo dei titoli di Microsoft Corporation stock price and financial market quotes."),
        ]

        for title, text in bad_cases:
            is_valid, reason = self.classifier.inspect_quality(text, title)
            self.assertFalse(
                is_valid,
                f"Expected REJECT for bad title '{title}', but passed! Reason: {reason}"
            )

    def test_genuine_complaints_must_be_accepted(self):
        """Real e-commerce complaint examples that MUST pass inspect_quality."""
        good_cases = [
            (
                "Myntra return request rejected for wrong dress delivered",
                "I ordered an XL size kurta from Myntra, but received a damaged small size dress. When I applied for return, Myntra rejected my return request stating quality check failed."
            ),
            (
                "Flipkart delivered empty box instead of smartphone",
                "Ordered a mobile phone on Flipkart during sale. Delivery agent handed over the parcel, but inside the box was completely empty. Customer support refused refund."
            ),
            (
                "Amazon seller sent counterfeit shoes and refund delayed",
                "Bought Nike sneakers from an Amazon seller. Received fake counterfeit shoes with poor stitching. Returned the item 10 days ago but refund is still delayed."
            ),
            (
                "Ajio wrong size received and pickup failed twice",
                "Received wrong shoe size from Ajio. Raised return request but pickup agent failed to arrive twice and return window is expiring."
            ),
            (
                "Meesho seller delivered used clothes instead of new garment",
                "Ordered a new dress on Meesho but received used stained clothes with torn fabric. Customer care is unresponsive."
            )
        ]

        for title, text in good_cases:
            is_valid, reason = self.classifier.inspect_quality(text, title)
            self.assertTrue(
                is_valid,
                f"Expected ACCEPT for good title '{title}', but rejected! Reason: {reason}"
            )

    def test_product_category_classification(self):
        """Test Product_Category tag assignment logic."""
        self.assertEqual(
            self.classifier.classify_product_category("Damaged shirt and wrong size dress delivered", "Myntra return"),
            "Apparel/Clothing"
        )
        self.assertEqual(
            self.classifier.classify_product_category("Received fake Nike sneakers instead of running shoes", "Amazon order"),
            "Footwear"
        )
        self.assertEqual(
            self.classifier.classify_product_category("Empty box received for mobile phone", "Flipkart order"),
            "Electronics"
        )


if __name__ == "__main__":
    unittest.main()
