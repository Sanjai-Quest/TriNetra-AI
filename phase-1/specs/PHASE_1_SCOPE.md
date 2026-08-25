# Phase 1 Scope: Research MVP (FINAL & FROZEN)

## PHASE 1 WILL INCLUDE (8 Components)

### 1. PostgreSQL Schema
- `entity_resolution` table (maps org-specific IDs to canonical products)
- `evidence_record` table (stores evidence from different sources)
- `evidence_attribute` table (normalizes individual evidence attributes)
- `ground_truth` table (for evaluation)
- `predictions` table (to store baseline + TriNetra predictions)

### 2. Canonical Normalization Engine
- Normalize SKU: "TS-204", "TS204", "ts204" → "TS-204"
- Normalize Weight: "500g", "0.5kg", "500 grams" → 500 (grams)
- Normalize Size: "XL", "extra large", "x-large" → "XL"
- Normalize Color: "red", "RED", "bright red" → "RED"
- Normalize Timestamp: Multiple formats → ISO 8601

### 3. Entity Resolution
- Map organization-specific IDs to canonical product IDs
- Example: Seller's "PROD-001" + Warehouse's "SKU-2845" + Carrier's "PKG-9999" → UUID "PRODUCT-XYZ"
- Track resolution confidence (deterministic = 100%)

### 4. Synthetic Data Generator
- Create 1000+ product lifecycles (normal + conflict cases)
- Evidence flow: ORDER → SELLER → WAREHOUSE → CARRIER → DELIVERY → RETURN
- Inject 5 conflict types: Identity, SKU, Weight anomaly, Temporal, Missing evidence
- Every case MUST have ground truth label
- 90% normal cases, 10% conflict cases

### 5. Deterministic Reconciliation Engine
- Check identity consistency (do all sources agree on product ID?)
- Check attribute matching (do SKUs match? Do sizes match?)
- Check timestamp ordering (are events in logical order?)
- Produce output: CONSISTENT or CONFLICT + list of detected conflicts

### 6. Statistical Anomaly Detection
- Weight analysis: mean ± 3×stddev (production variance tolerance)
- Detect weight anomalies in return center evidence (weight drop = missing product)
- Output: WEIGHT_ANOMALY if weight differs significantly

### 7. Three Baselines (for comparison)
- Baseline 1: Identity-only verification (check SKU match only)
- Baseline 2: Weight-only anomaly detection (check weight variance only)
- Baseline 3: Timeline-only verification (check timestamp ordering only)
- Baselines represent "single-source" approaches

### 8. Evaluation Module
- Calculate: Precision, Recall, F1, FPR, FNR, False Negative Reduction
- Generate confusion matrices
- Ablation study (test component importance: Identity → Identity+Weight → Identity+Timeline → Full)
- Output: CSV with all metrics

## PHASE 1 WILL NOT INCLUDE (Forbidden)

❌ React dashboard / frontend UI  
❌ REST APIs / HTTP endpoints  
❌ Authentication / authorization  
❌ LLM / language model usage  
❌ Computer vision / image processing  
❌ Redis caching  
❌ Kafka streaming  
❌ Microservices architecture  
❌ Docker / Kubernetes  
❌ Production deployment scripts  
❌ Real e-commerce integrations  
❌ Customer portal  

**These belong in Phases 2-14. DO NOT BUILD THEM IN PHASE 1.**
