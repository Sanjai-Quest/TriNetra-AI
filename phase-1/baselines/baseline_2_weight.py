"""
Baseline 2: Weight-Only Anomaly Detection (Single-Source Sensor Model)
Evaluates dispute validity solely based on physical weight sensor readings across checkpoints.
"""

import numpy as np
from typing import List, Dict, Any


class Baseline2WeightOnly:
    """Baseline 2 checking only weight anomaly detection."""

    def predict(self, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts weights across checkpoints.
        Flags CONFLICT if weight drops > 15% from outbound baseline or exceeds 3 standard deviations.
        """
        weights = []
        for ev in evidence_list:
            w = ev.get("weight")
            if w is not None:
                try:
                    weights.append(float(w))
                except (ValueError, TypeError):
                    continue

        if len(weights) < 2:
            return {
                "baseline": "WEIGHT_ONLY",
                "prediction": "CONSISTENT",
                "reasoning": "Insufficient weight readings to calculate variance."
            }

        outbound_weight = weights[0]  # Initial seller/warehouse weight
        for w in weights[1:]:
            # Check relative drop
            if outbound_weight > 0:
                drop_pct = (outbound_weight - w) / outbound_weight
                if drop_pct > 0.15:  # > 15% drop indicates weight anomaly
                    return {
                        "baseline": "WEIGHT_ONLY",
                        "prediction": "CONFLICT",
                        "reasoning": f"Significant weight drop detected: {outbound_weight}g -> {w}g ({drop_pct:.1%} loss)."
                    }

        # Statistical 3-sigma check across readings
        if len(weights) >= 3:
            mean_w = np.mean(weights)
            std_w = np.std(weights)
            if std_w > 0:
                for w in weights:
                    if abs(w - mean_w) > 3 * std_w:
                        return {
                            "baseline": "WEIGHT_ONLY",
                            "prediction": "CONFLICT",
                            "reasoning": f"Statistical weight outlier detected: {w}g (mean={mean_w:.1f}g, std={std_w:.1f}g)."
                        }

        return {
            "baseline": "WEIGHT_ONLY",
            "prediction": "CONSISTENT",
            "reasoning": "All recorded weights within normal tolerance bounds."
        }
