# Evidence Taxonomy for Phase 1

## Evidence Sources (8 types)

### 1. ORDER
- What: Initial customer order data
- Fields: `order_id`, `product_id`, `sku`, `size`, `color`, `quantity`, `timestamp`
- Example: `{"order_id": "ORD-001", "sku": "TS-204", "size": "XL"}`

### 2. SELLER
- What: Seller's dispatch/fulfillment record
- Fields: `seller_id`, `order_id`, `product_id`, `sku`, `size`, `color`, `quantity`, `weight`, `timestamp`
- Example: `{"seller_id": "SELLER-123", "sku": "TS-204", "weight": 500, "timestamp": "2026-08-23T10:00:00Z"}`

### 3. WAREHOUSE
- What: Warehouse receiving and inspection
- Fields: `warehouse_id`, `order_id`, `product_id`, `sku`, `size`, `color`, `quantity`, `weight`, `seal_status`, `timestamp`
- Example: `{"warehouse_id": "WH-001", "sku": "TS-204", "weight": 505, "seal_status": "intact"}`

### 4. PACKAGING
- What: Packaging operation (optional in Phase 1)
- Fields: `packaging_id`, `order_id`, `product_id`, `sku`, `weight_packaged`, `timestamp`
- Example: `{"packaging_id": "PKG-001", "weight_packaged": 510}`

### 5. CARRIER
- What: Logistics provider (pickup, in-transit, delivery)
- Fields: `carrier_id`, `order_id`, `tracking_id`, `weight`, `timestamp`
- Example: `{"carrier_id": "CARRIER-001", "weight": 505, "timestamp": "2026-08-23T12:00:00Z"}`

### 6. DELIVERY
- What: Delivery confirmation
- Fields: `delivery_id`, `order_id`, `delivered_status`, `timestamp`
- Example: `{"delivery_id": "DEL-001", "delivered_status": "delivered", "timestamp": "2026-08-23T14:00:00Z"}`

### 7. RETURN
- What: Return center receipt and inspection
- Fields: `return_id`, `order_id`, `product_id`, `sku`, `weight`, `condition`, `timestamp`
- Example: `{"return_id": "RET-001", "sku": "TS-204", "weight": 210, "condition": "damaged"}`

### 8. MARKETPLACE
- What: Dispute/complaint data
- Fields: `case_id`, `order_id`, `customer_claim`, `timestamp`
- Example: `{"case_id": "CASE-001", "customer_claim": "item missing from package"}`

## Normalization Rules (MUST implement)

### SKU Normalization
Input: `"TS-204"`, `"TS204"`, `"ts-204"`, `"TS 204"`  
Output: `"TS-204"` (canonical)  
Rule: Convert to uppercase, insert hyphen between letters and numbers  

### Weight Normalization
Input: `"500g"`, `"0.5kg"`, `"500 grams"`, `"0.5 kilograms"`  
Output: `500` (integer, in grams)  
Rule: Convert all to grams, return as integer  

### Size Normalization
Input: `"XL"`, `"x-large"`, `"extra large"`, `"extra-large"`, `"xl"`  
Output: `"XL"` (canonical)  
Rule: Map all variations to canonical size format  

### Color Normalization
Input: `"red"`, `"RED"`, `"dark red"`, `"bright red"`  
Output: `"RED"` (canonical)  
Rule: Convert to uppercase, remove modifiers for basic color  

### Timestamp Normalization
Input: `"2026-08-23T10:00:00Z"`, `"08/23/2026 10:00 AM"`, `"23-Aug-2026 10:00:00"`  
Output: `"2026-08-23T10:00:00Z"` (ISO 8601)  
Rule: Convert all to ISO 8601 UTC format  

## Conflict Types (5 types to test)
1. `IDENTITY_CONFLICT`: Different sources claim different product IDs for same order
2. `SKU_CONFLICT`: Normalized SKUs don't match across sources
3. `WEIGHT_ANOMALY`: Weight drop > 3 standard deviations / relative loss
4. `TEMPORAL_CONFLICT`: Events out of chronological order
5. `MISSING_EVIDENCE`: Expected evidence source is absent
