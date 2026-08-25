"""
Direct JSON Evidence Packet Reconciler for TriNetra AI Phase 1.
Ingests structured JSON dispute packets from files or stdin and produces structured JSON verdicts.
"""

import sys
import json
import os

# Add phase-1 root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalization.canonical_normalizer import CanonicalNormalizer
from resolution.entity_resolver import EntityResolver
from engine.reconciliation_engine import ReconciliationEngine


def reconcile_packet(packet: dict) -> dict:
    """
    Ingests a standardized JSON evidence packet:
    {
      "order": { ... },
      "evidence": [ { "source": "...", "attributes": { ... }, "timestamp": "..." }, ... ]
    }
    """
    normalizer = CanonicalNormalizer()
    resolver = EntityResolver()
    engine = ReconciliationEngine()

    order_info = packet.get("order", {})
    raw_evidence_list = packet.get("evidence", [])

    # Synthesize flattened evidence records for the engine
    flattened_evidence = []

    # 1. Order Evidence
    if order_info:
        flattened_evidence.append({
            "source": "ORDER",
            "order_id": order_info.get("order_id"),
            "product_id": order_info.get("product_id"),
            "sku": order_info.get("sku"),
            "size": order_info.get("size"),
            "color": order_info.get("color"),
            "timestamp": order_info.get("order_timestamp") or order_info.get("timestamp")
        })

    # 2. Stakeholder Evidence
    for item in raw_evidence_list:
        src = item.get("source", "UNKNOWN").upper()
        attrs = item.get("attributes", {})
        ts = item.get("timestamp")

        rec = {
            "source": src,
            "organization_id": item.get("organization_id"),
            "event_type": item.get("event_type"),
            "timestamp": ts
        }

        # Merge attributes (weight, sku, size, color, condition, etc.)
        for k, v in attrs.items():
            if k in ["weight_grams", "weight", "weight_g"]:
                rec["weight"] = v
            else:
                rec[k] = v

        flattened_evidence.append(rec)

    # 3. Canonical Normalization
    normalized_evidence = [normalizer.normalize_evidence_record(e) for e in flattened_evidence]

    # 4. Entity Resolution
    cid, conf, is_consistent = resolver.resolve_case_evidence(normalized_evidence)

    # 5. Multi-Source Reconciliation
    result = engine.reconcile(normalized_evidence)

    # Map status to recommendation & format
    conflicts_detected = result.get("conflicts", [])
    if any(c["conflict_type"] != "MISSING_EVIDENCE" for c in conflicts_detected):
        status = "INCONSISTENT"
        recommendation = "VERIFY"
    elif any(c["conflict_type"] == "MISSING_EVIDENCE" for c in conflicts_detected):
        status = "INCONCLUSIVE"
        recommendation = "REQUEST_MORE_EVIDENCE"
    else:
        status = "CONSISTENT"
        recommendation = "AUTO_REFUND_APPROVED"

    output_packet = {
        "order_id": order_info.get("order_id", "UNKNOWN"),
        "canonical_product_id": cid or order_info.get("product_id", "UNKNOWN"),
        "status": status,
        "recommendation": recommendation,
        "confidence_score": result.get("confidence_score", 0.0),
        "conflicts_count": len(conflicts_detected),
        "conflicts": conflicts_detected,
        "evidence_sources_present": result.get("evidence_sources_provided", []),
        "evidence_sources_missing": result.get("evidence_sources_missing", []),
        "provenance": {
            "evidence_count": len(normalized_evidence),
            "normalization_applied": True,
            "entity_resolution_confidence": conf
        }
    }
    return output_packet


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file path
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Read from stdin
        data = json.load(sys.stdin)

    result = reconcile_packet(data)
    print(json.dumps(result, indent=2))
