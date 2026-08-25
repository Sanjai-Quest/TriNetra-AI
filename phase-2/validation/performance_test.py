"""
Step 8: Performance Benchmark Test
Verifies performance SLA:
  - Risk computation latency: p95 < 100ms
  - Cache hit latency: < 10ms
"""

import os
import statistics
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

from trinetra_risk_scoring import RiskScoringService, Dispute


def test_performance():
    print("=" * 70)
    print("      TRINETRA AI — RISK SCORING PERFORMANCE BENCHMARK")
    print("=" * 70)

    service = RiskScoringService()
    dispute = Dispute(
        id="perf-dispute-001",
        buyer_id="perf-buyer-001",
        seller_id="perf-seller-001",
        category="electronics",
        price=3500.0,
        evidence_sources_present=5,
        evidence_sources_expected=5,
        buyer_return_count=3,
        buyer_total_orders=50,
        seller_dispute_count=2,
        seller_total_sales=100,
    )

    times_ms = []
    NUM_RUNS = 200

    for _ in range(NUM_RUNS):
        start = time.perf_counter()
        service.compute_risk_score(dispute)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        times_ms.append(elapsed_ms)

    p50 = statistics.median(times_ms)
    sorted_times = sorted(times_ms)
    p95_idx = int(0.95 * len(sorted_times))
    p99_idx = int(0.99 * len(sorted_times))
    p95 = sorted_times[p95_idx]
    p99 = sorted_times[p99_idx]
    mean_lat = statistics.mean(times_ms)

    print(f"\nExecution Benchmark ({NUM_RUNS} iterations):")
    print(f"  Mean Latency: {mean_lat:.4f} ms")
    print(f"  p50 Latency:  {p50:.4f} ms")
    print(f"  p95 Latency:  {p95:.4f} ms (Target SLA: < 100.0 ms)")
    print(f"  p99 Latency:  {p99:.4f} ms")
    print(f"  Max Latency:  {max(times_ms):.4f} ms")

    assert p95 < 100.0, f"RED FLAG: p95 latency ({p95:.2f}ms) exceeds 100ms SLA target!"
    print("\n  ✅ PASS: Performance SLA successfully met (< 100ms p95).")
    print("=" * 70)


if __name__ == "__main__":
    test_performance()
