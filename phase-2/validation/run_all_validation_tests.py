"""
TriNetra AI — Phase 2 Master Validation Test Suite Runner
Executes the complete 10-step validation workflow and generates official sign-off summary.
"""

import os
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

import test_formula
import test_redis_caching
import test_audit_logging
import validate_against_real_data
import performance_test
import reproducibility_test


def run_master_suite():
    print("#" * 75)
    print("      TRINETRA AI — PHASE 2 RISK SCORING MASTER VALIDATION SUITE")
    print("#" * 75)

    checklist_results = {}

    # STEP 1 & 4: Formula & Unit Tests (30 tests)
    print("\n>>> [STEP 1 & 4] Running 30+ Unit Tests (Formula, Weights, Factors, Boundaries)...")
    suite1 = unittest.TestLoader().loadTestsFromModule(test_formula)
    res1 = unittest.TextTestRunner(verbosity=1).run(suite1)
    checklist_results["Formula Implementation (30 tests)"] = res1.wasSuccessful()

    # STEP 3: Redis Caching & Hit Rate (>80%)
    print("\n>>> [STEP 3] Running Redis Caching & Hit Rate Tests...")
    suite2 = unittest.TestLoader().loadTestsFromModule(test_redis_caching)
    res2 = unittest.TextTestRunner(verbosity=1).run(suite2)
    checklist_results["Redis Caching Layer (>80% Hit Rate)"] = res2.wasSuccessful()

    # STEP 7: Audit Trail Logging
    print("\n>>> [STEP 7] Running Audit Trail Logging Tests...")
    suite3 = unittest.TestLoader().loadTestsFromModule(test_audit_logging)
    res3 = unittest.TextTestRunner(verbosity=1).run(suite3)
    checklist_results["Audit Trail Logging"] = res3.wasSuccessful()

    # STEP 6: Real Data Validation (271 Complaints)
    print("\n>>> [STEP 6] Running Validation Against 271 Real Consumer Complaints...")
    try:
        validate_against_real_data.run_real_data_validation()
        checklist_results["Validation Against 271 Real Complaints"] = True
    except Exception as e:
        print(f"❌ Real Data Validation Error: {e}")
        checklist_results["Validation Against 271 Real Complaints"] = False

    # STEP 8: Performance Benchmark
    print("\n>>> [STEP 8] Running Latency Performance Benchmark (<100ms p95)...")
    try:
        performance_test.test_performance()
        checklist_results["Performance SLA (<100ms p95)"] = True
    except Exception as e:
        print(f"❌ Performance Test Error: {e}")
        checklist_results["Performance SLA (<100ms p95)"] = False

    # STEP 9: Reproducibility Test
    print("\n>>> [STEP 9] Running Deterministic Reproducibility Test...")
    try:
        reproducibility_test.test_reproducibility()
        checklist_results["Deterministic Reproducibility"] = True
    except Exception as e:
        print(f"❌ Reproducibility Test Error: {e}")
        checklist_results["Deterministic Reproducibility"] = False

    # STEP 10: Official Approval Summary
    print("\n" + "=" * 75)
    print("                    PHASE 2 VALIDATION SUMMARY")
    print("=" * 75)

    all_passed = True
    for item, passed in checklist_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {item}")

    print("-" * 75)
    if all_passed:
        print("  Status: ✅ APPROVED — ALL CRITERIA MET (0 RED FLAGS)")
        print("  Ready to proceed to Phase 3 Architecture & Summary Diagrams.")
    else:
        print("  Status: ❌ NOT APPROVED — Fix failing items above.")
    print("=" * 75)


if __name__ == "__main__":
    run_master_suite()
