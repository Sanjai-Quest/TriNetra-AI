"""
Synthetic Lifecycle Data Generator for TriNetra AI Phase 1.
Generates 1,000 product dispute lifecycles (900 normal, 100 injected conflicts)
with exact ground truth labels and fixed deterministic seed (seed=42).
"""

import random
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple


class SyntheticDataGenerator:
    """Generates synthetic multi-stakeholder e-commerce product dispute lifecycles."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(self.seed)
        np.random.seed(self.seed)
        self.skus = ["TS-204", "TS-205", "TS-206", "KB-100", "SW-880", "HD-500"]
        self.sizes = ["S", "M", "L", "XL", "XXL"]
        self.colors = ["RED", "BLUE", "BLACK", "WHITE", "NAVY"]

    def generate_dataset(self, total_cases: int = 1000) -> Tuple[List[Dict[str, Any]], pd.DataFrame, pd.DataFrame]:
        """
        Generates total_cases cases:
        - 900 NORMAL cases (ground_truth: CONSISTENT)
        - 100 CONFLICT cases:
            - 30 IDENTITY_CONFLICT
            - 40 WEIGHT_ANOMALY
            - 15 TEMPORAL_CONFLICT
            - 10 VARIANT_CONFLICT
            - 5 MISSING_EVIDENCE
        """
        random.seed(self.seed)
        np.random.seed(self.seed)

        cases = []
        evidence_rows = []
        ground_truth_rows = []

        # Target distribution
        normal_count = 900
        identity_count = 30
        weight_count = 40
        temporal_count = 15
        variant_count = 10
        missing_count = 5

        case_idx = 1

        # 1. Generate Normal Cases (900)
        for _ in range(normal_count):
            case_id = f"CASE-{case_idx:06d}"
            case = self._generate_normal_case(case_id)
            cases.append(case)
            self._flatten_case(case, evidence_rows, ground_truth_rows)
            case_idx += 1

        # 2. Generate Identity Conflict Cases (30)
        for _ in range(identity_count):
            case_id = f"CASE-{case_idx:06d}"
            case = self._generate_identity_conflict(case_id)
            cases.append(case)
            self._flatten_case(case, evidence_rows, ground_truth_rows)
            case_idx += 1

        # 3. Generate Weight Anomaly Cases (40)
        for _ in range(weight_count):
            case_id = f"CASE-{case_idx:06d}"
            case = self._generate_weight_anomaly(case_id)
            cases.append(case)
            self._flatten_case(case, evidence_rows, ground_truth_rows)
            case_idx += 1

        # 4. Generate Temporal Conflict Cases (15)
        for _ in range(temporal_count):
            case_id = f"CASE-{case_idx:06d}"
            case = self._generate_temporal_conflict(case_id)
            cases.append(case)
            self._flatten_case(case, evidence_rows, ground_truth_rows)
            case_idx += 1

        # 5. Generate Variant Conflict Cases (10)
        for _ in range(variant_count):
            case_id = f"CASE-{case_idx:06d}"
            case = self._generate_variant_conflict(case_id)
            cases.append(case)
            self._flatten_case(case, evidence_rows, ground_truth_rows)
            case_idx += 1

        # 6. Generate Missing Evidence Cases (5)
        for _ in range(missing_count):
            case_id = f"CASE-{case_idx:06d}"
            case = self._generate_missing_evidence(case_id)
            cases.append(case)
            self._flatten_case(case, evidence_rows, ground_truth_rows)
            case_idx += 1

        df_evidence = pd.DataFrame(evidence_rows)
        df_ground_truth = pd.DataFrame(ground_truth_rows)

        return cases, df_evidence, df_ground_truth

    def _generate_normal_case(self, case_id: str) -> Dict[str, Any]:
        sku = random.choice(self.skus)
        size = random.choice(self.sizes)
        color = random.choice(self.colors)
        base_weight = random.randint(450, 550)
        base_time = datetime(2026, 8, 23, 10, 0, 0) + timedelta(minutes=random.randint(0, 10000))

        # Variances within normal calibration bounds
        seller_weight = base_weight + random.randint(-5, 5)
        warehouse_weight = base_weight + random.randint(-5, 5)
        carrier_weight = base_weight + random.randint(-8, 8)
        return_weight = base_weight + random.randint(-5, 5)

        evidence = [
            {
                "source": "ORDER",
                "order_id": f"ORD-{case_id[5:]}",
                "sku": sku,
                "size": size,
                "color": color,
                "quantity": 1,
                "timestamp": base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "SELLER",
                "seller_id": "SELLER-001",
                "sku": sku,
                "size": size,
                "color": color,
                "weight": f"{seller_weight}g",
                "timestamp": (base_time + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "WAREHOUSE",
                "warehouse_id": "WH-001",
                "sku": sku,
                "size": size,
                "color": color,
                "weight": f"{warehouse_weight}g",
                "seal_status": "intact",
                "timestamp": (base_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "CARRIER",
                "carrier_id": "CARRIER-001",
                "tracking_id": f"TRK-{case_id[5:]}",
                "weight": f"{carrier_weight}g",
                "timestamp": (base_time + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "DELIVERY",
                "delivery_id": f"DEL-{case_id[5:]}",
                "delivered_status": "delivered",
                "timestamp": (base_time + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "RETURN",
                "return_id": f"RET-{case_id[5:]}",
                "sku": sku,
                "size": size,
                "color": color,
                "weight": f"{return_weight}g",
                "condition": "good",
                "timestamp": (base_time + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]

        return {
            "case_id": case_id,
            "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case_id}_{sku}")),
            "expected_status": "CONSISTENT",
            "conflict_types": [],
            "severity": "NONE",
            "root_cause": "Normal dispute lifecycle; all physical telemetry and identity records match.",
            "evidence": evidence
        }

    def _generate_identity_conflict(self, case_id: str) -> Dict[str, Any]:
        ordered_sku = "TS-204"
        dispatched_sku = "TS-203"
        size = "XL"
        color = "RED"
        base_weight = 500
        base_time = datetime(2026, 8, 23, 10, 0, 0) + timedelta(minutes=random.randint(0, 10000))

        evidence = [
            {
                "source": "ORDER",
                "sku": ordered_sku,
                "size": size,
                "color": color,
                "timestamp": base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "SELLER",
                "sku": dispatched_sku,  # Conflict: Seller dispatched wrong product
                "size": size,
                "color": color,
                "weight": "505g",
                "timestamp": (base_time + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "WAREHOUSE",
                "sku": dispatched_sku,
                "size": size,
                "color": color,
                "weight": "502g",
                "timestamp": (base_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "CARRIER",
                "weight": "505g",
                "timestamp": (base_time + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "RETURN",
                "sku": dispatched_sku,
                "size": size,
                "color": color,
                "weight": "505g",
                "timestamp": (base_time + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]

        return {
            "case_id": case_id,
            "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case_id}_{ordered_sku}")),
            "expected_status": "CONFLICT",
            "conflict_types": ["IDENTITY_CONFLICT"],
            "severity": "HIGH",
            "root_cause": "Seller dispatched wrong product SKU (TS-203 instead of ordered TS-204).",
            "evidence": evidence
        }

    def _generate_weight_anomaly(self, case_id: str) -> Dict[str, Any]:
        sku = "TS-204"
        size = "XL"
        color = "RED"
        base_time = datetime(2026, 8, 23, 10, 0, 0) + timedelta(minutes=random.randint(0, 10000))

        evidence = [
            {
                "source": "ORDER",
                "sku": sku,
                "size": size,
                "color": color,
                "timestamp": base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "SELLER",
                "sku": sku,
                "weight": "500g",
                "timestamp": (base_time + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "WAREHOUSE",
                "sku": sku,
                "weight": "505g",
                "timestamp": (base_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "CARRIER",
                "weight": "510g",
                "timestamp": (base_time + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "RETURN",
                "sku": sku,
                "weight": "210g",  # Conflict: 58% weight loss, product missing from return package
                "condition": "empty_box",
                "timestamp": (base_time + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]

        return {
            "case_id": case_id,
            "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case_id}_{sku}")),
            "expected_status": "CONFLICT",
            "conflict_types": ["WEIGHT_ANOMALY"],
            "severity": "HIGH",
            "root_cause": "Product missing from return package (weight dropped from 505g outbound to 210g return).",
            "evidence": evidence
        }

    def _generate_temporal_conflict(self, case_id: str) -> Dict[str, Any]:
        sku = "TS-204"
        size = "XL"
        color = "RED"
        base_time = datetime(2026, 8, 23, 10, 0, 0) + timedelta(minutes=random.randint(0, 10000))

        evidence = [
            {
                "source": "ORDER",
                "sku": sku,
                "size": size,
                "color": color,
                "timestamp": base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "WAREHOUSE",
                "sku": sku,
                "weight": "500g",
                "timestamp": (base_time - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")  # Conflict: Precedes order!
            },
            {
                "source": "CARRIER",
                "weight": "505g",
                "timestamp": (base_time + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "RETURN",
                "sku": sku,
                "weight": "500g",
                "timestamp": (base_time + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]

        return {
            "case_id": case_id,
            "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case_id}_{sku}")),
            "expected_status": "CONFLICT",
            "conflict_types": ["TEMPORAL_CONFLICT"],
            "severity": "MEDIUM",
            "root_cause": "Warehouse receiving timestamp occurs before order placement timestamp.",
            "evidence": evidence
        }

    def _generate_variant_conflict(self, case_id: str) -> Dict[str, Any]:
        sku = "TS-204"
        ordered_size = "XL"
        dispatched_size = "M"
        color = "RED"
        base_time = datetime(2026, 8, 23, 10, 0, 0) + timedelta(minutes=random.randint(0, 10000))

        evidence = [
            {
                "source": "ORDER",
                "sku": sku,
                "size": ordered_size,
                "color": color,
                "timestamp": base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "WAREHOUSE",
                "sku": sku,
                "size": dispatched_size,  # Conflict: Wrong size variant shipped
                "color": color,
                "weight": "490g",
                "timestamp": (base_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "RETURN",
                "sku": sku,
                "size": dispatched_size,
                "color": color,
                "weight": "490g",
                "timestamp": (base_time + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]

        return {
            "case_id": case_id,
            "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case_id}_{sku}")),
            "expected_status": "CONFLICT",
            "conflict_types": ["VARIANT_CONFLICT"],
            "severity": "HIGH",
            "root_cause": "Variant mismatch: Customer ordered XL, Warehouse fulfilled size M.",
            "evidence": evidence
        }

    def _generate_missing_evidence(self, case_id: str) -> Dict[str, Any]:
        sku = "TS-204"
        size = "XL"
        color = "RED"
        base_time = datetime(2026, 8, 23, 10, 0, 0) + timedelta(minutes=random.randint(0, 10000))

        # Missing CARRIER and WAREHOUSE evidence
        evidence = [
            {
                "source": "ORDER",
                "sku": sku,
                "size": size,
                "color": color,
                "timestamp": base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "SELLER",
                "sku": sku,
                "weight": "500g",
                "timestamp": (base_time + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            {
                "source": "RETURN",
                "sku": sku,
                "weight": "500g",
                "timestamp": (base_time + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]

        return {
            "case_id": case_id,
            "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case_id}_{sku}")),
            "expected_status": "INCONCLUSIVE",
            "conflict_types": ["MISSING_EVIDENCE"],
            "severity": "LOW-MEDIUM",
            "root_cause": "Incomplete chain of custody; Carrier and Warehouse checkpoints missing.",
            "evidence": evidence
        }

    def _flatten_case(
        self,
        case: Dict[str, Any],
        evidence_rows: List[Dict[str, Any]],
        ground_truth_rows: List[Dict[str, Any]]
    ) -> None:
        case_id = case["case_id"]
        ground_truth_rows.append({
            "case_id": case_id,
            "expected_status": case["expected_status"],
            "conflict_types": ";".join(case["conflict_types"]),
            "severity": case["severity"],
            "root_cause": case["root_cause"]
        })

        for idx, ev in enumerate(case["evidence"], start=1):
            source = ev.get("source")
            for attr, val in ev.items():
                if attr != "source":
                    evidence_rows.append({
                        "case_id": case_id,
                        "evidence_index": idx,
                        "source": source,
                        "attribute": attr,
                        "value": str(val),
                        "timestamp": ev.get("timestamp", "")
                    })
