"""
Baseline 1: Identity-Only Verification (Single-Source Attribute Model)
Evaluates dispute validity solely based on SKU / product identity matches between Order, Seller, and Return.
"""

from typing import List, Dict, Any


class Baseline1IdentityOnly:
    """Baseline 1 checking only product identity (SKU) consistency."""

    def predict(self, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts all SKUs from evidence records.
        If all present SKUs match, predicts CONSISTENT.
        If any SKU mismatch is observed, predicts CONFLICT.
        """
        skus = []
        for ev in evidence_list:
            sku = ev.get("sku")
            if sku:
                skus.append(str(sku).strip().upper())

        if len(skus) <= 1:
            return {
                "baseline": "IDENTITY_ONLY",
                "prediction": "CONSISTENT",
                "reasoning": "Single or no SKU record found; no identity conflict detected."
            }

        first_sku = skus[0]
        for s in skus[1:]:
            if s != first_sku:
                return {
                    "baseline": "IDENTITY_ONLY",
                    "prediction": "CONFLICT",
                    "reasoning": f"SKU mismatch detected: {first_sku} vs {s}"
                }

        return {
            "baseline": "IDENTITY_ONLY",
            "prediction": "CONSISTENT",
            "reasoning": "All evidence sources agree on SKU identity."
        }
