# TriNetra AI — Phase 1: Research MVP & Evidence Reconciliation Engine

## Overview
Phase 1 implements and experimentally validates the core research hypothesis:
> *"Can multi-source, cross-organizational evidence reconciliation reduce false negatives compared with single-source verification?"*

All execution is 100% deterministic, seed-locked (`seed=42`), and grounded in PostgreSQL schemas and Python statistical logic without unverified LLM dependencies.

---

## Directory Structure
```
phase-1/
├── schema/
│   └── schema.sql                  # PostgreSQL DDL schema & indexes
├── generator/
│   └── synthetic_generator.py      # Lifecycle generator with 5 conflict modes (seed=42)
├── normalization/
│   └── canonical_normalizer.py     # SKU, weight, size, color, timestamp normalizer
├── resolution/
│   └── entity_resolver.py          # Organization ID to canonical UUID resolution graph
├── baselines/
│   ├── baseline_1_identity.py      # Single-source SKU identity model
│   ├── baseline_2_weight.py        # Single-source sensor weight anomaly model
│   └── baseline_3_timeline.py      # Single-source temporal chronology model
├── engine/
│   └── reconciliation_engine.py    # TriNetra multi-source deterministic + statistical engine
├── evaluation/
│   └── evaluator.py                # Precision/Recall/F1, McNemar test, and Ablation suite
├── tests/
│   └── test_suite.py               # Unit tests covering all pipeline modules
├── data/
│   ├── synthetic_evidence.csv      # Generated 1,000 cases normalized records
│   ├── ground_truth.csv            # Ground truth dispute classifications
│   └── predictions.csv             # Baseline and TriNetra inferences
├── results/
│   ├── metrics.csv                 # Core performance metrics table
│   ├── ablation_results.csv        # Multi-level ablation study
│   ├── confusion_matrices.json     # Detailed confusion matrices and p-values
│   ├── conflict_type_recall.csv    # Detection breakdown by conflict sub-type
│   └── PHASE_1_RESULTS.md          # Authoritative Research Results Report
├── generate_and_evaluate.py        # Master execution pipeline
└── README.md                       # Reproducibility instructions
```

---

## Reproducibility Instructions

### 1. Run Unit Tests
```bash
python -m unittest phase-1/tests/test_suite.py
```

### 2. Run Full 1,000-Case Experiment Pipeline
```bash
python phase-1/generate_and_evaluate.py
```

All metrics, confusion matrices, ablation tables, and `PHASE_1_RESULTS.md` will be generated directly in `phase-1/results/`.
