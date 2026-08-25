"""
Evaluation Engine & Statistical Validation Suite for TriNetra AI Phase 1.
Computes Precision, Recall, F1, FPR, FNR, FN Reduction, Confusion Matrices,
McNemar's Test / Binomial Test p-values, and Full Ablation Suite.
"""

import json
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple


class Evaluator:
    """Evaluates multi-source reconciliation vs single-source baselines against ground truth."""

    def __init__(self, ground_truth: List[Dict[str, Any]], predictions: List[Dict[str, Any]]):
        self.ground_truth = {gt["case_id"]: gt for gt in ground_truth}
        self.predictions = predictions

    def evaluate_all(self) -> Dict[str, Any]:
        """Runs full benchmark across Baseline 1, Baseline 2, Baseline 3, and TriNetra."""
        results = {}
        models = ["baseline_1", "baseline_2", "baseline_3", "trinetra"]

        for model in models:
            tp, fp, tn, fn = 0, 0, 0, 0
            for pred in self.predictions:
                case_id = pred["case_id"]
                actual = self.ground_truth[case_id]["expected_status"]
                predicted = pred[f"{model}_prediction"]

                # In binary conflict detection:
                # Actual positive = CONFLICT
                # Actual negative = CONSISTENT or INCONCLUSIVE (for conflict detection)
                is_actual_conflict = (actual == "CONFLICT")
                is_pred_conflict = (predicted == "CONFLICT")

                if is_actual_conflict and is_pred_conflict:
                    tp += 1
                elif not is_actual_conflict and is_pred_conflict:
                    fp += 1
                elif not is_actual_conflict and not is_pred_conflict:
                    tn += 1
                elif is_actual_conflict and not is_pred_conflict:
                    fn += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

            results[model] = {
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "fpr": fpr,
                "fnr": fnr
            }

        # Calculate False Negative Reductions vs best baseline
        best_baseline_fnr = min(results["baseline_1"]["fnr"], results["baseline_2"]["fnr"], results["baseline_3"]["fnr"])
        best_baseline_name = min(
            ["baseline_1", "baseline_2", "baseline_3"],
            key=lambda k: results[k]["fnr"]
        )

        trinetra_fnr = results["trinetra"]["fnr"]
        fn_reduction = (best_baseline_fnr - trinetra_fnr) / best_baseline_fnr if best_baseline_fnr > 0 else 0.0

        # Statistical Significance: McNemar's Test between TriNetra and best baseline
        b_pred = [p[f"{best_baseline_name}_prediction"] == "CONFLICT" for p in self.predictions]
        t_pred = [p["trinetra_prediction"] == "CONFLICT" for p in self.predictions]
        actual_labels = [self.ground_truth[p["case_id"]]["expected_status"] == "CONFLICT" for p in self.predictions]

        # Contingency table for paired binary classification correctness
        # b_correct = (b_pred == actual), t_correct = (t_pred == actual)
        n00, n01, n10, n11 = 0, 0, 0, 0
        for b_p, t_p, act in zip(b_pred, t_pred, actual_labels):
            b_corr = (b_p == act)
            t_corr = (t_p == act)
            if not b_corr and not t_corr:
                n00 += 1
            elif not b_corr and t_corr:
                n01 += 1  # Baseline incorrect, TriNetra correct
            elif b_corr and not t_corr:
                n10 += 1  # Baseline correct, TriNetra incorrect
            else:
                n11 += 1

        # McNemar test statistic with Edwards continuity correction
        if (n01 + n10) > 0:
            chi2 = ((abs(n01 - n10) - 1.0) ** 2) / (n01 + n10)
            # For 1 degree of freedom, p = erfc(sqrt(chi2 / 2))
            p_value = math.erfc(math.sqrt(chi2 / 2.0))
        else:
            chi2 = 0.0
            p_value = 1.0

        summary = {
            "metrics": results,
            "best_baseline": best_baseline_name,
            "best_baseline_fnr": best_baseline_fnr,
            "trinetra_fnr": trinetra_fnr,
            "fn_reduction": fn_reduction,
            "mcnemar_contingency": {"n00": n00, "n01_tri_better": n01, "n10_base_better": n10, "n11": n11},
            "mcnemar_chi2": float(chi2),
            "p_value": float(p_value),
            "statistically_significant": p_value < 0.05
        }
        return summary

    def run_ablation_study(self, cases: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Runs cumulative ablation study across 4 configuration levels:
        Level 1: Identity Only
        Level 2: Identity + Weight Anomaly
        Level 3: Identity + Timeline
        Level 4: Full Multi-Source (Identity + Weight + Timeline + Completeness)
        """
        ablation_configs = [
            ("L1_Identity_Only", {"identity": True, "weight": False, "timeline": False}),
            ("L2_Identity_Weight", {"identity": True, "weight": True, "timeline": False}),
            ("L3_Identity_Timeline", {"identity": True, "weight": False, "timeline": True}),
            ("L4_Full_Reconciliation", {"identity": True, "weight": True, "timeline": True})
        ]

        rows = []
        for name, cfg in ablation_configs:
            tp, fp, tn, fn = 0, 0, 0, 0
            for case in cases:
                actual = case["expected_status"]
                pred_conflict = False

                # Simulate config checks
                ev = case["evidence"]
                if cfg["identity"]:
                    skus = set(e.get("sku") for e in ev if e.get("sku"))
                    sizes = set(e.get("size") for e in ev if e.get("size"))
                    if len(skus) > 1 or len(sizes) > 1:
                        pred_conflict = True

                if cfg["weight"] and not pred_conflict:
                    weights = []
                    for e in ev:
                        w_raw = e.get("weight")
                        if w_raw is not None:
                            if isinstance(w_raw, (int, float)):
                                weights.append(float(w_raw))
                            else:
                                import re
                                match = re.search(r'[\d.]+', str(w_raw))
                                if match:
                                    weights.append(float(match.group(0)))
                    if len(weights) >= 2:
                        if (weights[0] - weights[-1]) / weights[0] > 0.15:
                            pred_conflict = True

                if cfg["timeline"] and not pred_conflict:
                    # Check temporal
                    for i in range(len(ev) - 1):
                        t1 = ev[i].get("timestamp", "")
                        t2 = ev[i + 1].get("timestamp", "")
                        if t1 and t2 and t1 > t2:
                            pred_conflict = True
                            break

                is_actual = (actual == "CONFLICT")
                if is_actual and pred_conflict:
                    tp += 1
                elif not is_actual and pred_conflict:
                    fp += 1
                elif not is_actual and not pred_conflict:
                    tn += 1
                elif is_actual and not pred_conflict:
                    fn += 1

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

            rows.append({
                "Configuration": name,
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "Precision": round(prec, 4),
                "Recall": round(rec, 4),
                "F1_Score": round(f1, 4),
                "FPR": round(fpr, 4),
                "FNR": round(fnr, 4)
            })

        df_ablation = pd.DataFrame(rows)
        return df_ablation

    def evaluate_per_conflict_type(self, cases: List[Dict[str, Any]], predictions: List[Dict[str, Any]]) -> pd.DataFrame:
        """Evaluates detection rates across specific injected conflict sub-types."""
        pred_map = {p["case_id"]: p for p in predictions}
        type_cases = {}
        for c in cases:
            ctype = ";".join(c.get("conflict_types", [])) or "NONE"
            if ctype not in type_cases:
                type_cases[ctype] = []
            type_cases[ctype].append(c)

        rows = []
        for ctype, clist in type_cases.items():
            total = len(clist)
            b1_caught = sum(1 for c in clist if pred_map[c["case_id"]]["baseline_1_prediction"] == "CONFLICT")
            b2_caught = sum(1 for c in clist if pred_map[c["case_id"]]["baseline_2_prediction"] == "CONFLICT")
            b3_caught = sum(1 for c in clist if pred_map[c["case_id"]]["baseline_3_prediction"] == "CONFLICT")
            tri_caught = sum(1 for c in clist if pred_map[c["case_id"]]["trinetra_prediction"] == "CONFLICT")

            rows.append({
                "Conflict_Type": ctype,
                "Count": total,
                "Baseline_1_Recall": f"{b1_caught/total:.1%}",
                "Baseline_2_Recall": f"{b2_caught/total:.1%}",
                "Baseline_3_Recall": f"{b3_caught/total:.1%}",
                "TriNetra_Recall": f"{tri_caught/total:.1%}"
            })

        return pd.DataFrame(rows)
