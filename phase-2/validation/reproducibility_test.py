"""
Step 9: Reproducibility & Determinism Verification
Verifies that risk scores computed with identical inputs yield bitwise identical outputs across multiple runs.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

from trinetra_risk_scoring import RiskScoringService, Dispute


def test_reproducibility():
    print("=" * 70)
    print("      TRINETRA AI — DETERMINISTIC REPRODUCIBILITY TEST")
    print("=" * 70)

    service_a = RiskScoringService()
    service_b = RiskScoringService()

    disputes = [
        Dispute(f"d-{i}", f"b-{i}", f"s-{i}", "electronics" if i % 2 == 0 else "fashion", 500 * (i + 1),
                evidence_sources_present=(i % 5) + 1, buyer_return_count=i, buyer_total_orders=50)
        for i in range(100)
    ]

    mismatches = 0
    for d in disputes:
        res_a = service_a.compute_risk_score(d)
        res_b = service_b.compute_risk_score(d)

        if res_a.score != res_b.score or res_a.friction_level != res_b.friction_level:
            mismatches += 1

    print(f"\nTested 100 heterogeneous disputes across independent service instances.")
    print(f"  Mismatches detected: {mismatches}")
    assert mismatches == 0, f"RED FLAG: {mismatches} non-deterministic mismatches found!"
    print("  ✅ PASS: 100% deterministic reproducibility verified across all cases.")
    print("=" * 70)


if __name__ == "__main__":
    test_reproducibility()
