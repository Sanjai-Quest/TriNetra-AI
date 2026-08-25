"""
TriNetra Multi-Source Cross-Organizational Evidence Reconciliation Engine.
Executes deterministic identity matching, variant checking, statistical weight anomaly detection,
temporal ordering validation, and evidence chain completeness checking.
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


class ReconciliationEngine:
    """Multi-source evidence reconciliation engine for e-commerce return disputes."""

    EVENT_HIERARCHY = {
        "ORDER": 1,
        "SELLER": 2,
        "WAREHOUSE": 3,
        "CARRIER": 4,
        "DELIVERY": 5,
        "RETURN": 6
    }

    def reconcile(self, normalized_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reconciles multi-source normalized evidence records.
        Returns full structured verdict, detected conflicts, provenance, and confidence score.
        """
        conflicts = []
        sources_present = set(ev.get("source", "").upper() for ev in normalized_evidence)
        expected_sources = {"ORDER", "SELLER", "WAREHOUSE", "CARRIER", "RETURN"}
        missing_sources = list(expected_sources - sources_present)

        # 1. Check Identity & SKU Consistency
        identity_conflicts = self._check_identity_consistency(normalized_evidence)
        conflicts.extend(identity_conflicts)

        # 2. Check Variant Consistency (Size / Color)
        variant_conflicts = self._check_variant_consistency(normalized_evidence)
        conflicts.extend(variant_conflicts)

        # 3. Check Statistical Weight Anomaly
        weight_conflicts = self._check_weight_anomaly(normalized_evidence)
        conflicts.extend(weight_conflicts)

        # 4. Check Temporal Chronology
        temporal_conflicts = self._check_temporal_ordering(normalized_evidence)
        conflicts.extend(temporal_conflicts)

        # 5. Check Missing Evidence / Chain Completeness
        if missing_sources and not conflicts:
            # If critical checkpoints (e.g. CARRIER or WAREHOUSE) are missing and no explicit conflict found
            if "CARRIER" in missing_sources or "WAREHOUSE" in missing_sources:
                conflicts.append({
                    "conflict_type": "MISSING_EVIDENCE",
                    "severity": "LOW-MEDIUM",
                    "evidence_sources": list(sources_present),
                    "interpretation": f"Missing critical custody records: {', '.join(missing_sources)}."
                })

        # Decision & Confidence Logic
        if any(c["conflict_type"] != "MISSING_EVIDENCE" for c in conflicts):
            status = "CONFLICT"
            recommendation = "VERIFY"
            # High confidence when concrete physical or attribute conflicts are proven
            confidence_score = 0.95 if len(conflicts) > 1 else 0.90
        elif any(c["conflict_type"] == "MISSING_EVIDENCE" for c in conflicts):
            status = "INCONCLUSIVE"
            recommendation = "INCONCLUSIVE"
            confidence_score = 0.65
        else:
            status = "CONSISTENT"
            recommendation = "CONSISTENT"
            confidence_score = 0.98

        return {
            "status": status,
            "recommendation": recommendation,
            "confidence_score": confidence_score,
            "conflicts": conflicts,
            "evidence_sources_provided": list(sources_present),
            "evidence_sources_missing": missing_sources,
            "provenance": {
                "evidence_count": len(normalized_evidence),
                "attributes_checked": ["sku", "size", "color", "weight", "timestamp"],
                "normalization_applied": True,
                "entity_resolution_successful": len(identity_conflicts) == 0
            }
        }

    def _check_identity_consistency(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verifies SKU consistency across all participating entities."""
        conflicts = []
        skus_by_source = {}
        for ev in evidence_list:
            src = ev.get("source", "UNKNOWN")
            sku = ev.get("sku")
            if sku:
                skus_by_source[src] = str(sku).strip().upper()

        if len(skus_by_source) > 1:
            unique_skus = set(skus_by_source.values())
            if len(unique_skus) > 1:
                conflicts.append({
                    "conflict_type": "IDENTITY_CONFLICT",
                    "severity": "HIGH",
                    "evidence_sources": list(skus_by_source.keys()),
                    "interpretation": f"Multi-source SKU mismatch: {skus_by_source}"
                })
        return conflicts

    def _check_variant_consistency(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verifies Size and Color variant consistency."""
        conflicts = []
        sizes = {}
        colors = {}
        for ev in evidence_list:
            src = ev.get("source", "UNKNOWN")
            if ev.get("size"):
                sizes[src] = str(ev.get("size")).strip().upper()
            if ev.get("color"):
                colors[src] = str(ev.get("color")).strip().upper()

        if len(set(sizes.values())) > 1:
            conflicts.append({
                "conflict_type": "VARIANT_CONFLICT",
                "severity": "HIGH",
                "evidence_sources": list(sizes.keys()),
                "interpretation": f"Size variant mismatch across sources: {sizes}"
            })
        if len(set(colors.values())) > 1:
            conflicts.append({
                "conflict_type": "VARIANT_CONFLICT",
                "severity": "HIGH",
                "evidence_sources": list(colors.keys()),
                "interpretation": f"Color variant mismatch across sources: {colors}"
            })
        return conflicts

    def _check_weight_anomaly(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Checks for statistical weight drops and anomalies."""
        conflicts = []
        weights_by_source = {}
        for ev in evidence_list:
            src = ev.get("source", "UNKNOWN")
            w = ev.get("weight")
            if w is not None:
                try:
                    weights_by_source[src] = float(w)
                except (ValueError, TypeError):
                    continue

        if len(weights_by_source) >= 2:
            outbound_weight = weights_by_source.get("SELLER") or weights_by_source.get("WAREHOUSE")
            return_weight = weights_by_source.get("RETURN")

            if outbound_weight and return_weight:
                drop_pct = (outbound_weight - return_weight) / outbound_weight
                if drop_pct > 0.15:  # > 15% drop indicates weight anomaly
                    conflicts.append({
                        "conflict_type": "WEIGHT_ANOMALY",
                        "severity": "HIGH",
                        "evidence_sources": ["WAREHOUSE", "RETURN"] if "WAREHOUSE" in weights_by_source else ["SELLER", "RETURN"],
                        "measurement_outbound": outbound_weight,
                        "measurement_return": return_weight,
                        "variance": f"{drop_pct:.1%} drop",
                        "interpretation": f"Product weight loss of {drop_pct:.1%} between outbound ({outbound_weight}g) and return ({return_weight}g)."
                    })

            # Check 3-sigma variance across all readings
            w_vals = list(weights_by_source.values())
            if len(w_vals) >= 3 and not conflicts:
                mean_w = np.mean(w_vals)
                std_w = np.std(w_vals)
                if std_w > 0:
                    for src, val in weights_by_source.items():
                        if abs(val - mean_w) > 3 * std_w:
                            conflicts.append({
                                "conflict_type": "WEIGHT_ANOMALY",
                                "severity": "MEDIUM-HIGH",
                                "evidence_sources": [src],
                                "measurement": val,
                                "interpretation": f"Weight reading at {src} ({val}g) violates 3-sigma tolerance (mean={mean_w:.1f}g, std={std_w:.1f}g)."
                            })
        return conflicts

    def _check_temporal_ordering(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verifies chronological order of lifecycle stages."""
        conflicts = []
        parsed = []
        for ev in evidence_list:
            src = ev.get("source", "").upper()
            ts_str = ev.get("timestamp")
            if src in self.EVENT_HIERARCHY and ts_str:
                try:
                    dt = datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
                    parsed.append((self.EVENT_HIERARCHY[src], src, dt))
                except Exception:
                    continue

        for i in range(len(parsed)):
            for j in range(i + 1, len(parsed)):
                rank_i, src_i, dt_i = parsed[i]
                rank_j, src_j, dt_j = parsed[j]

                if rank_i < rank_j and dt_i > dt_j:
                    conflicts.append({
                        "conflict_type": "TEMPORAL_CONFLICT",
                        "severity": "MEDIUM",
                        "evidence_sources": [src_i, src_j],
                        "interpretation": f"Timeline inversion: {src_i} ({dt_i.isoformat()}) occurred after {src_j} ({dt_j.isoformat()})."
                    })
                elif rank_i > rank_j and dt_i < dt_j:
                    conflicts.append({
                        "conflict_type": "TEMPORAL_CONFLICT",
                        "severity": "MEDIUM",
                        "evidence_sources": [src_i, src_j],
                        "interpretation": f"Timeline inversion: {src_i} ({dt_i.isoformat()}) occurred before {src_j} ({dt_j.isoformat()})."
                    })
        return conflicts
