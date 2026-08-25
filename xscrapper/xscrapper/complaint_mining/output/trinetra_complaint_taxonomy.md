# TriNetra AI — Complaint & Evidence Conflict Taxonomy

**Version:** 2.0  
**Purpose:** Formal classification rules mapping raw consumer claims to TriNetra dispute reconciliation dimensions.

---

## 1. Conflict Taxonomy Definitions

### 1. `IDENTITY_CONFLICT`
* **Definition:** A verifiable discrepancy between the promised product SKU/specification and the actual physical item delivered or returned.
* **Trigger Conditions:** Wrong product received, counterfeit duplicate, used item shipped as new, incorrect apparel/shoe size, incorrect color variant.
* **Required Evidence for Reconciliation:** Manufacturer Barcode Scan, Product Serial/IMEI, High-Resolution Photo of Tag/Label.

### 2. `CONDITION_CONFLICT`
* **Definition:** A dispute regarding the physical integrity, operational state, or damage of the item.
* **Trigger Conditions:** Dead on arrival (DOA), broken/cracked housing, torn stitching, chemical leakage, opened security seal.
* **Required Evidence for Reconciliation:** Continuous Unboxing Video, Outbound Pack-Station CCTV, Carrier Transit Exception Log.

### 3. `QUANTITY_CONFLICT`
* **Definition:** A mismatch between the number of items or bundle accessories ordered and what was physically unboxed.
* **Trigger Conditions:** Missing charger, missing combo piece, partial shipment without notice.
* **Required Evidence for Reconciliation:** Outbound Itemized Picking Manifest, Inbound Return Inspection Checklist.

### 4. `WEIGHT_CONFLICT`
* **Definition:** An anomaly where the package weight deviates significantly (>15% or 3-sigma) from the manufacturer baseline or outbound checkpoint.
* **Trigger Conditions:** Empty box delivery, soap bar scam, returned package hollowed out.
* **Required Evidence for Reconciliation:** Calibrated Scale Weight Checkpoint at Outbound, Carrier Hub Scan, and Inbound Return Dock.

### 5. `TEMPORAL_CONFLICT`
* **Definition:** A chronological impossibility or causality violation in the chain of custody.
* **Trigger Conditions:** Return pickup marked completed before delivery; carrier marked "delivered" while package was at sorting hub; refund SLA expired.
* **Required Evidence for Reconciliation:** Cryptographically Signed Timestamp Logs, Carrier GPS Telemetry, OTP Verification Timestamp.

### 6. `REFUND_CONFLICT`
* **Definition:** A financial disagreement where return was completed or cancelled, but monetary restitution was withheld or delayed.
* **Trigger Conditions:** Return delivered to seller warehouse >14 days ago without payout; gateway debit without order generation.
* **Required Evidence for Reconciliation:** Bank UTR Reference, Gateway Refund API Response, Return Inward Receipt.

### 7. `POLICY_CONFLICT`
* **Definition:** A disagreement stemming from restrictive or ambiguous marketplace return window policies.
* **Trigger Conditions:** Non-returnable tag applied post-purchase, 7-day replacement-only restriction on defective electronics.
* **Required Evidence for Reconciliation:** Snapshot of Category Return Policy at Checkout Timestamp.

### 8. `EVIDENCE_GAP`
* **Definition:** A dispute state where neither party's claim can be mathematically verified due to missing intermediate custody telemetry.
* **Action:** Directs TriNetra to classify case as `INCONCLUSIVE` and recommend proportional adaptive friction (e.g., OTP pickup, unboxing video request).

---
