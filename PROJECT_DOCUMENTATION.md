# TriNetra AI: Complete System Architecture & Implementation Documentation
**Version:** 2.0.0  
**Repository:** [https://github.com/Sanjai-Quest/TriNetra-AI.git](https://github.com/Sanjai-Quest/TriNetra-AI.git)

---

## Executive Summary

**TriNetra AI** ("Three Eyes") is an automated, cross-organizational fraud detection and evidence reconciliation platform for modern e-commerce and logistics ecosystems.

TriNetra eliminates fraudulent return claims and reduces false negatives by cross-verifying telemetry and physical evidence from multiple independent stakeholders (Warehouse CCTV/scales, Outbound Carriers, Return Centers, Merchants, and Consumer complaints).

---

## Table of Contents
1. [Core Hypothesis & Phase 1 Validation](#1-core-hypothesis--phase-1-validation)
2. [Statistical Experimental Results](#2-statistical-experimental-results)
3. [Phase 1: Evidence Reconciliation MVP](#3-phase-1-evidence-reconciliation-mvp)
4. [Phase 2: Enterprise Multi-Service Architecture](#4-phase-2-enterprise-multi-service-architecture)
5. [Multi-Modal Computer Vision Pipeline](#5-multi-modal-computer-vision-pipeline)
6. [4-Signal Fraud Detection Matrix](#6-4-signal-fraud-detection-matrix)
7. [Spring Boot 3.2 Services & Port Mapping](#7-spring-boot-32-services--port-mapping)
8. [React 18 + TypeScript Investigator Dashboard](#8-react-18--typescript-investigator-dashboard)
9. [Database Schema Extensions](#9-database-schema-extensions)
10. [End-to-End Setup & Run Guide](#10-end-to-end-setup--run-guide)

---

## 1. Core Hypothesis & Phase 1 Validation

### The Problem
Traditional fraud detection relies on **single-source inspection** (e.g. only checking package weight at the return center, or only matching barcodes). Fraudsters exploit these silos by:
- Swapping contents inside original boxes (identity matches, but weight drops).
- Returning worn clothes with counterfeit tags (wardrobing).
- Serial return abuse across different marketplace sellers.

### The Hypothesis
> *"Can multi-source, cross-organizational evidence reconciliation reduce false negatives compared with single-source verification?"*

### The Verdict: Validated ✅
By unifying 5 independent evidence sources (Order, Warehouse, Carrier Outbound, Carrier Return, Return Inspection Center), TriNetra caught 100% of synthetic fraud cases without introducing false positives.

---

## 2. Statistical Experimental Results

Evaluated across **1,000 synthetic lifecycle cases**:

| Metric | Baseline 1 (Identity Only) | Baseline 2 (Weight Only) | Baseline 3 (Timeline Only) | **TriNetra AI (Multi-Source)** | Target Threshold |
|---|---|---|---|---|---|
| **True Positives (TP)** | 30 | 40 | 15 | **95** | — |
| **False Positives (FP)** | 0 | 0 | 0 | **0** | — |
| **True Negatives (TN)** | 905 | 905 | 905 | **905** | — |
| **False Negatives (FN)** | 65 | 55 | 80 | **0** | — |
| **Precision** | 1.0000 | 1.0000 | 1.0000 | **1.0000** | $\ge 0.80$ ✅ |
| **Recall** | 0.3158 | 0.4211 | 0.1579 | **1.0000** | $\ge 0.75$ ✅ |
| **F1 Score** | 0.4800 | 0.5926 | 0.2727 | **1.0000** | $\ge 0.77$ ✅ |
| **False Positive Rate (FPR)** | 0.0000 | 0.0000 | 0.0000 | **0.0000** | $\le 0.15$ ✅ |
| **False Negative Rate (FNR)** | 0.6842 | 0.5789 | 0.8421 | **0.0000** | — |
| **FN Reduction vs Best Baseline** | 0.0% | 0.0% | 0.0% | **100.0%** | $> 15.0\%$ ✅ |

### Statistical Significance:
- **McNemar’s Chi-Square Test:** $\chi^2 = 53.02$
- **p-value:** $p = 3.3048 \times 10^{-13}$ ($p < 0.0001 \ll 0.05$)
- **Conclusion:** The reduction in false negatives achieved by multi-source reconciliation is statistically significant.

---

## 3. Phase 1: Evidence Reconciliation MVP

Located in [`phase-1/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-1/):
- **Canonical Normalizer:** Standardizes SKU formats, weights (grams/kg/lbs $\rightarrow$ grams), dimensions, and timestamps.
- **Entity Resolution Engine:** Resolves vendor-specific barcodes/SKUs to canonical product UUIDs.
- **Reconciliation Engine:** Deterministic rule engine cross-comparing attribute values across 5 lifecycle touchpoints.
- **Baselines Suite:** Implements single-source comparator baselines for benchmark testing.
- **Synthetic Data Generator:** Generates 1,000 realistic e-commerce lifecycles with parameterized fraud injections.

---

## 4. Phase 2: Enterprise Multi-Service Architecture

Phase 2 scales the research MVP into an asynchronous, event-driven enterprise architecture:

```
                                  ┌────────────────────────────────┐
                                  │   React Investigator Frontend  │
                                  │   (React 18 + TS + Vite / 3000)│
                                  └───────────────┬────────────────┘
                                                  │
┌───────────────────────────┐       ┌─────────────▼──────────────────┐
│   Third-Party Webhooks    ├──────►│      Claim Service             │ (Port 8080)
│  (Shipping, Payment, KYC) │       │ (Spring Boot 3.2 + JPA + REST) │
└─────────────┬─────────────┘       └─────────────┬──────────────────┘
              │                                   │
              │                     ┌─────────────▼──────────────────┐
              │                     │     Evidence Service           │ (Port 8081)
              │                     │ (Spring Boot 3.2 + MinIO SDK)  │
              │                     └─────────────┬──────────────────┘
              │                                   │
              │                            RabbitMQ Broker           │
              └───────────────────────────────────┼──────────────────┘
                                                  │
                    ┌─────────────────────────────┼──────────────────────────────┐
                    │                             │                              │
         ┌──────────▼───────────┐      ┌──────────▼───────────┐       ┌──────────▼───────────┐
         │ Multi-Modal Processor│      │  Fraud Detection     │       │  Integration Service │
         │ (FastAPI + OpenCV)   │      │ (Spring Boot + Redis)│       │ (Spring Boot + DLQ)  │
         │     (Port 8082)      │      │     (Port 8083)      │       │     (Port 8085)      │
         └──────────┬───────────┘      └──────────┬───────────┘       └──────────────────────┘
                    │                             │
                    └─────────────────────────────┼──────────────────────────────┐
                                                  │                              │
                                       ┌──────────▼───────────┐                  │
                                       │   Verdict Generator  │ (Port 8084)      │
                                       │ (Spring Boot Engine) │                  │
                                       └──────────────────────┘                  │
```

---

## 5. Multi-Modal Computer Vision Pipeline

Located in [`phase-2/services/multimodal_processor/main.py`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/services/multimodal_processor/main.py):
- **Wear Detection:** Analyzes fabric wear and creases via OpenCV Canny edge density + HSV saturation loss + Laplacian texture variance. Zero large ML model download requirements.
- **EXIF Extraction:** Reads camera make, timestamp, and GPS tags via Pillow.
- **Color Consistency:** Analyzes RGB color distribution to verify that the returned product matches the expected catalog color.
- **Receipt OCR:** Parses receipt text via `pytesseract` to extract dates and total amounts for claim validation.

---

## 6. 4-Signal Fraud Detection Matrix

Located in [`phase-2/spring-services/fraud-detection-engine/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/spring-services/fraud-detection-engine/):

1. **Serial Fraudster (`HIGH`):** Flags customers with $\ge 7$ claims in the past 90 days. Cached in Redis with a 24-hour TTL.
2. **Impossibly Fast Return (`CRITICAL`):** Flags returns initiated within $< 60$ minutes of delivery.
3. **Inflated Claim (`MEDIUM`):** Flags claimed refund amounts exceeding $150\%$ of original product value.
4. **Wardrobing (`HIGH`):** Flags clothing items with OpenCV wear score $> 0.70$.

---

## 7. Spring Boot 3.2 Services & Port Mapping

| Service | Port | Technology | Purpose |
|---|---|---|---|
| **Claim Service** | `8080` | Spring Boot 3.2, Data JPA, REST | Ingestion, claim lifecycle, investigator assignments & overrides |
| **Evidence Service** | `8081` | Spring Boot 3.2, MinIO SDK | Multi-modal file storage & artifact tracking |
| **Multi-Modal Processor** | `8082` | Python 3.12, FastAPI, OpenCV | Computer vision & OCR worker |
| **Fraud Detection Engine** | `8083` | Spring Boot 3.2, Data Redis | 4-signal fraud detection algorithms |
| **Verdict Generator** | `8084` | Spring Boot 3.2, AMQP | Cross-stakeholder reconciliation & decision engine |
| **Integration Service** | `8085` | Spring Boot 3.2, Webhooks | Shipping & payment webhooks, Dead Letter Queue |
| **Investigator Dashboard** | `3000` | React 18, Vite, TypeScript | Modern UI for queue triage & overrides |

---

## 8. React 18 + TypeScript Investigator Dashboard

Located in [`phase-2/frontend-react/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/frontend-react/):
- **Live Queue:** Search claims by ID, order, or category; filter by status (`Pending Review`, `Approved`, `Rejected`, `Investigating`).
- **Claim Inspector:** Real-time metrics, color-coded severity badges, automated reasoning viewer, and audit log.
- **Investigator Override:** Modal form allowing manual verdict overrides with mandatory audit justifications.

---

## 9. Database Schema Extensions

Located in [`phase-2/schema/schema_extensions.sql`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/schema/schema_extensions.sql):
- `claims`
- `evidence`
- `evidence_artifacts`
- `fraud_signals`
- `verdict_reasoning`
- `investigator_actions`
- `integration_events`

---

## 10. End-to-End Setup & Run Guide

### Step 1: Start Stateful Containers (Docker)
```powershell
docker compose -f phase-2/docker-compose.yml up -d postgres redis rabbitmq minio
```

### Step 2: Start Spring Boot Claim Service
```powershell
cd phase-2/spring-services/claim-service
mvn spring-boot:run "-Dspring-boot.run.profiles=local"
```

### Step 3: Start React Investigator Dashboard
```powershell
cd phase-2/frontend-react
npm run dev
```
Open **`http://localhost:3000`** in your browser.

### Step 4: Test Sample Ingestion
```powershell
cd phase-2
powershell -ExecutionPolicy Bypass -File test_claim.ps1
```
