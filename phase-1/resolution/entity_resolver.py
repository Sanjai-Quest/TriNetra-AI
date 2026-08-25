"""
Entity Resolution Module for TriNetra AI Phase 1.
Maps organization-specific identifiers to canonical product UUIDs and manages resolution graph.
"""

import uuid
from typing import Dict, List, Optional, Tuple, Any


class EntityResolver:
    """Resolves multi-organization system identifiers to a canonical product entity."""

    def __init__(self):
        # Map (source_org, source_system_id) -> (canonical_product_id, confidence)
        self.registry: Dict[Tuple[str, str], Tuple[str, float]] = {}
        # Map canonical_product_id -> list of (source_org, source_system_id)
        self.reverse_registry: Dict[str, List[Tuple[str, str]]] = {}

    def register_mapping(
        self,
        canonical_product_id: str,
        source_organization: str,
        source_system_id: str,
        confidence: float = 1.0
    ) -> None:
        """Explicitly registers an entity mapping."""
        key = (source_organization.upper(), str(source_system_id).strip())
        self.registry[key] = (canonical_product_id, confidence)
        if canonical_product_id not in self.reverse_registry:
            self.reverse_registry[canonical_product_id] = []
        self.reverse_registry[canonical_product_id].append(key)

    def resolve(
        self,
        source_organization: str,
        source_system_id: str
    ) -> Tuple[Optional[str], float]:
        """Looks up canonical product ID for a given organization ID."""
        key = (source_organization.upper(), str(source_system_id).strip())
        if key in self.registry:
            return self.registry[key]
        return None, 0.0

    def resolve_case_evidence(
        self,
        evidence_records: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], float, bool]:
        """
        Resolves canonical entity across a full evidence chain.
        Returns (canonical_id, overall_confidence, is_consistent).
        """
        if not evidence_records:
            return None, 0.0, False

        resolved_ids = set()
        for rec in evidence_records:
            source = rec.get("source", "UNKNOWN")
            system_id = rec.get("sku") or rec.get("product_id") or rec.get("order_id")
            if system_id:
                cid, conf = self.resolve(source, system_id)
                if cid:
                    resolved_ids.add(cid)

        if len(resolved_ids) == 1:
            return list(resolved_ids)[0], 1.0, True
        elif len(resolved_ids) > 1:
            # Conflict detected at entity resolution level
            return None, 0.0, False
        else:
            # Generate deterministic canonical ID based on anchor (first record)
            anchor = evidence_records[0]
            anchor_val = anchor.get("sku") or anchor.get("product_id") or "UNKNOWN"
            generated_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{anchor_val}"))
            return generated_id, 1.0, True
