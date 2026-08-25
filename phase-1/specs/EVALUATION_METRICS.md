# Phase 1 Evaluation Metrics

## Primary Success Metric: False Negative Reduction
```
FN_Reduction = (FN_Baseline - FN_TriNetra) / FN_Baseline * 100%

SUCCESS THRESHOLD: FN_Reduction > 15% with p-value < 0.05
```

## Secondary Metrics
- **Precision:** $\text{TP} / (\text{TP} + \text{FP}) \ge 0.80$
- **Recall:** $\text{TP} / (\text{TP} + \text{FN}) \ge 0.75$
- **F1 Score:** $2 \cdot (\text{Precision} \cdot \text{Recall}) / (\text{Precision} + \text{Recall}) \ge 0.77$
- **False Positive Rate (FPR):** $\text{FP} / (\text{FP} + \text{TN}) \le 0.15$
- **Statistical Significance Test:** McNemar's paired test with continuity correction ($p < 0.05$).
