# TriNetra AI — Real-World Consumer Complaint Dataset: Data Dictionary

**Dataset Version:** 2.0 (Expanded Research Corpus)  
**Total Records:** 1050  
**File:** `trinetra_real_complaints_expanded.csv`  
**License / Scope:** Academic Research / Empirical Evidence Orchestration Study  

---

## 1. Schema Overview

The expanded dataset separates **Raw Consumer Narrative Data** from **Derived TriNetra Research Labels** to prevent semantic leakage and preserve empirical rigor.

| Column Name | Data Type | Description | Source / Provenance | Example |
|---|---|---|---|---|
| `case_id` | String | Unique sequential identifier (`CMP_XXXXX`) | System Generated | `CMP_00001` |
| `source` | String | Primary platform or subreddit archive origin | Data Collection | `Reddit (r/LegalAdviceIndia)` |
| `source_url` | String | Direct permanent URL to the public discussion | Data Collection | `https://reddit.com/r/...` |
| `collection_date` | Date (YYYY-MM-DD) | Date the complaint record was harvested | Metadata | `2026-08-25` |
| `date` | String / Date | Date the original consumer post was published | Source Metadata | `2025-11-12` |
| `platform` | String | E-commerce marketplace or retail brand involved | Classification Rule | `Flipkart`, `Amazon`, `Meesho` |
| `product_category` | String | Standardized retail category | Classification Rule | `Apparel/Clothing`, `Electronics` |
| `complaint_type` | String | Primary surface-level dispute taxonomy | Classification Rule | `Wrong Product`, `Empty Box Delivery` |
| `return_requested` | Boolean | Whether consumer explicitly sought return/pickup | Raw Narrative Extraction | `True` / `False` |
| `return_reason` | String | Stated grounds for dispute or return | Raw Narrative Extraction | `Damaged / Defective Product` |
| `refund_requested` | Boolean | Whether monetary refund was explicitly sought | Raw Narrative Extraction | `True` / `False` |
| `replacement_requested`| Boolean | Whether product replacement was sought | Raw Narrative Extraction | `True` / `False` |
| `delivery_issue` | Boolean | Whether logistics, courier, or pickup failed | Raw Narrative Extraction | `True` / `False` |
| `product_condition_issue`| Boolean| Whether physical state/integrity was disputed | Raw Narrative Extraction | `True` / `False` |
| `consumer_claim` | String | Full verbatim text of customer grievance | Raw Unmodified Post | `"Ordered shoes size 9, received size 7..."` |
| `company_claim` | String | Explicit or inferred claim by company/seller | Raw Narrative Extraction | `"Seller claimed package was intact..."` |
| `company_response` | String | Response or automated decision received | Raw Narrative Extraction | `"Customer care rejected return claiming QC..."` |
| `resolution` | String | Final known status at time of publication | Raw Narrative Extraction | `"Unresolved at time of posting"` |
| `outcome` | String | Dispute state outcome category | Research Category | `"Publicly Disputed"`, `"Escalated Dispute"` |
| `evidence_mentioned` | String | Specific evidence explicitly cited in post | Raw Evidence Extraction | `"Photographic Evidence; Invoice"` |
| `evidence_missing` | String | Critical evidence required to prove dispute | Derived Gap Rule | `"In-transit Checkpoint Weight Log"` |
| `customer_evidence` | String | Typology of buyer-side evidence available | Evidence Model | `"First-hand post narrative + photos"` |
| `seller_evidence` | String | Typology of seller-side evidence available | Evidence Model | `"Marketplace seller claim / refusal"` |
| `logistics_evidence` | String | Typology of carrier-side evidence available | Evidence Model | `"Carrier scan / delivery attempt record"` |
| `warehouse_evidence` | String | Typology of warehouse evidence available | Evidence Model | `"Return QC inspection checkpoint"` |
| `identity_conflict` | Boolean | Derived Label: SKU / variant / product mismatch | TriNetra Taxonomy | `True` / `False` |
| `condition_conflict`| Boolean | Derived Label: Damage, defect, or used item | TriNetra Taxonomy | `True` / `False` |
| `quantity_conflict` | Boolean | Derived Label: Missing item or component count | TriNetra Taxonomy | `True` / `False` |
| `weight_conflict` | Boolean | Derived Label: Physical weight discrepancy | TriNetra Taxonomy | `True` / `False` |
| `temporal_conflict` | Boolean | Derived Label: Timeline or causality inversion | TriNetra Taxonomy | `True` / `False` |
| `refund_conflict` | Boolean | Derived Label: Monetary refund withheld or delayed| TriNetra Taxonomy | `True` / `False` |
| `policy_conflict` | Boolean | Derived Label: Dispute over return policy terms | TriNetra Taxonomy | `True` / `False` |
| `evidence_gap` | Boolean | Derived Label: Inconclusive without new evidence | TriNetra Taxonomy | `True` / `False` |
| `data_completeness` | Float (0.0–1.0)| Measure of structural completeness of post | Metric | `0.85` |
| `source_reliability` | String | Qualitative reliability assessment of source | Metric | `High (Direct Public Consumer Experience)` |
| `classification_confidence`| Float | Confidence score of taxonomy extraction | Metric | `0.90` |
| `likes` | Integer | Upvotes / likes on original post | Social Telemetry | `42` |
| `replies` | Integer | Number of community comments / replies | Social Telemetry | `11` |

---
