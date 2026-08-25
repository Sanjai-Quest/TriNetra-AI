# Synthetic Data Generation Specification

## Distribution (1000 Cases Total)
- **NORMAL Cases:** 900 (90%)
  - Weights within normal $\pm 5\text{g}$ tolerance, chronological timestamps, matching SKUs.
  - Ground Truth: `CONSISTENT`
- **CONFLICT Cases:** 100 (10%)
  - `IDENTITY_CONFLICT`: 30 cases (Seller dispatches wrong product SKU)
  - `WEIGHT_ANOMALY`: 40 cases (Product missing from return package; >15% drop)
  - `TEMPORAL_CONFLICT`: 15 cases (Timestamp inversion / causality violation)
  - `VARIANT_CONFLICT`: 10 cases (Wrong size/color variant shipped)
  - `MISSING_EVIDENCE`: 5 cases (Incomplete chain of custody)
  - Ground Truth: `CONFLICT` / `INCONCLUSIVE`

## Reproducibility
- Random seed locked to `seed=42`.
- Outputs generated: `synthetic_evidence.csv` and `ground_truth.csv`.
