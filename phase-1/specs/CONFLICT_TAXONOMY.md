# Conflict Taxonomy: Detection Rules & Output Format

## Conflict Detection Rules

### 1. IDENTITY_CONFLICT & SKU_CONFLICT Detection
```
IF (SELLER.sku ≠ ORDER.sku) OR (WAREHOUSE.sku ≠ ORDER.sku) OR (RETURN.sku ≠ ORDER.sku)
THEN
  OUTPUT: IDENTITY_CONFLICT
  SEVERITY: HIGH
  RECOMMENDATION: Verification required before dispatch / refund
END
```

### 2. WEIGHT_ANOMALY Detection
```
CALCULATE:
  mean_weight = average of all recorded weights
  stddev_weight = standard deviation
  threshold = mean_weight ± 3 * stddev_weight

FOR EACH evidence.weight:
  IF weight < (mean - 3*stddev) OR weight > (mean + 3*stddev) OR drop > 15%
  THEN
    OUTPUT: WEIGHT_ANOMALY
    SEVERITY: MEDIUM-HIGH / HIGH
    ANOMALY_MAGNITUDE: (recorded_weight - expected_weight) / expected_weight
  END
END
```

### 3. TEMPORAL_CONFLICT Detection
```
SORT all evidence by timestamp
FOR EACH adjacent pair (event1, event2):
  IF event1.timestamp > event2.timestamp AND event1.type should_precede event2.type
  THEN
    OUTPUT: TEMPORAL_CONFLICT
    SEVERITY: MEDIUM
    RECOMMENDATION: Check data quality
  END
END

Expected order:
1. ORDER
2. SELLER dispatch
3. WAREHOUSE receive
4. CARRIER pickup
5. DELIVERY
6. RETURN
```

### 4. MISSING_EVIDENCE Detection
```
expected_sources = [ORDER, SELLER, WAREHOUSE, CARRIER, RETURN]
provided_sources = sources in this case
missing = expected_sources - provided_sources

IF len(missing) > 0
THEN
  OUTPUT: MISSING_EVIDENCE
  SEVERITY: LOW-MEDIUM
  MISSING: [list of sources]
  IMPACT: "Cannot fully reconcile without [missing sources]"
END
```
