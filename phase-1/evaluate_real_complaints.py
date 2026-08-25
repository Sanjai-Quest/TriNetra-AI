"""
TriNetra AI — Real Complaint Evaluation Runner
===============================================
Runs the full reconciliation benchmark on real consumer complaint evidence
packets and compares TriNetra vs. 3 baselines.

Validates that the system trained on synthetic data generalises to real disputes.
"""

import os
import sys
import json
import csv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from normalization.canonical_normalizer import CanonicalNormalizer
from resolution.entity_resolver import EntityResolver
from baselines.baseline_1_identity import Baseline1IdentityOnly
from baselines.baseline_2_weight import Baseline2WeightOnly
from baselines.baseline_3_timeline import Baseline3TimelineOnly
from engine.reconciliation_engine import ReconciliationEngine
from evaluation.evaluator import Evaluator
from data.build_real_dataset import build_real_complaint_dataset


def evaluate_on_real_data():
    print("=" * 70)
    print("  TRINETRA AI — REAL COMPLAINT EVALUATION")
    print("  Source: 271 real consumer complaints (Ajio, Amazon, Meesho, etc.)")
    print("=" * 70)

    # 1. Build real complaint evidence packets
    cases, complaints = build_real_complaint_dataset()
    if not cases:
        print("[ERROR] Could not load real complaints. Aborting.")
        return

    # 2. Initialise engines
    normalizer = CanonicalNormalizer()
    b1 = Baseline1IdentityOnly()
    b2 = Baseline2WeightOnly()
    b3 = Baseline3TimelineOnly()
    trinetra = ReconciliationEngine()

    # 3. Run inference on all real cases
    print(f"\n[Step 2] Running inference on {len(cases)} real complaint evidence packets...")
    predictions = []
    for case in cases:
        ev = [normalizer.normalize_evidence_record(r) for r in case["evidence"]]
        pred_b1 = b1.predict(ev)
        pred_b2 = b2.predict(ev)
        pred_b3 = b3.predict(ev)
        pred_t  = trinetra.reconcile(ev)

        predictions.append({
            "case_id":                case["case_id"],
            "expected_status":        case["expected_status"],
            "conflict_types":         case.get("conflict_type", "") or "",
            "baseline_1_prediction":  pred_b1["prediction"],
            "baseline_2_prediction":  pred_b2["prediction"],
            "baseline_3_prediction":  pred_b3["prediction"],
            "trinetra_prediction":    pred_t["status"],
            "trinetra_confidence":    pred_t["confidence_score"],
            "trinetra_conflicts_count": len(pred_t["conflicts"]),
            "trinetra_conflicts":     json.dumps(pred_t["conflicts"]),
        })

    # 4. Evaluate
    print("[Step 3] Computing metrics vs. 3 baselines...")
    evaluator = Evaluator(ground_truth=cases, predictions=predictions)
    results = evaluator.evaluate_all()
    m = results["metrics"]

    print("\n" + "=" * 70)
    print("  RESULTS ON REAL CONSUMER COMPLAINTS (271 cases)")
    print("=" * 70)
    header = f"{'Metric':<30} {'B1-Identity':>12} {'B2-Weight':>12} {'B3-Timeline':>12} {'TriNetra':>12}"
    print(header)
    print("-" * 70)

    rows = [
        ("True Positives (TP)",   "tp"),
        ("False Positives (FP)",  "fp"),
        ("True Negatives (TN)",   "tn"),
        ("False Negatives (FN)",  "fn"),
        ("Precision",             "precision"),
        ("Recall",                "recall"),
        ("F1 Score",              "f1"),
        ("FPR",                   "fpr"),
        ("FNR",                   "fnr"),
    ]

    for label, key in rows:
        vals = [m[model][key] for model in ["baseline_1", "baseline_2", "baseline_3", "trinetra"]]
        if isinstance(vals[0], float):
            row = f"  {label:<28}" + "".join(f"{v:>12.4f}" for v in vals)
        else:
            row = f"  {label:<28}" + "".join(f"{v:>12}" for v in vals)
        print(row)

    print("-" * 70)
    print(f"\n  FN Reduction vs. best baseline : {results['fn_reduction']:.1%}")
    print(f"  McNemar chi2                   : {results['mcnemar_chi2']:.4f}")
    print(f"  p-value                        : {results['p_value']:.4e}")
    print(f"  Statistically significant      : {results['statistically_significant']}")

    # 5. Save results
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    results_path = os.path.join(results_dir, "real_complaint_results.json")
    os.makedirs(results_dir, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Saved full results -> {results_path}")

    # 6. Save predictions CSV
    preds_path = os.path.join(base_dir, "data", "real_complaint_predictions.csv")
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    with open(preds_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)
    print(f"  Saved predictions  -> {preds_path}")

    print("\n" + "=" * 70)
    if results["statistically_significant"] and results["fn_reduction"] > 0.15:
        print("  STATUS: PASSED — Real-world FN reduction > 15% (p < 0.05)")
    else:
        print(f"  STATUS: NOTE — FN reduction = {results['fn_reduction']:.1%}, p = {results['p_value']:.4e}")
        print("  (Check conflict label quality if FN reduction is unexpectedly low)")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_on_real_data()
