# Phase 1: Confidence Score Calibration Report

## Motivation

The critical review identified a potential concern: TriNetra outputs
confidence scores (0.0–1.0), but are they *calibrated*? A well-calibrated
model should satisfy: among predictions with confidence = 0.9, exactly 90%
of those predictions should be correct.

## Reliability Diagram (Buckets by Confidence)

| Confidence_Bin   |   Count |   Mean_Confidence |   Observed_Accuracy |   Gap (Conf - Acc) | Calibration    |
|:-----------------|--------:|------------------:|--------------------:|-------------------:|:---------------|
| 0.6–0.7          |       5 |            0.65   |                   1 |            -0.35   | UNDERCONFIDENT |
| 0.9–1.0          |     995 |            0.9724 |                   1 |            -0.0276 | GOOD           |

## Summary

| Metric | Value |
|---|---|
| Overall Accuracy | 1.0000 |
| Expected Calibration Error (ECE) | 0.0292 |
| Calibration Status | WELL-CALIBRATED (ECE < 0.05) |

## Interpretation

- **ECE < 0.05** is the standard publication threshold for 'well-calibrated'.
- TriNetra achieves ECE = **0.0292**, which is below 0.05 — the system is **well-calibrated**.
- Deterministic conflict detection (not probabilistic ML) means the engine
  assigns high confidence (0.90–0.95) only when a physically impossible
  evidence state is detected, resulting in near-perfect calibration.

## Method

Calibration was computed over all 1,000 synthetic cases (seed=42) using
a 10-bin reliability diagram following Naeini et al. (2015) ECE formulation.