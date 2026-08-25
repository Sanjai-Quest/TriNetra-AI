# TriNetra AI: Phase 2 — Multi-Modal Processing & Advanced Detection

Phase 2 expands Phase 1's evidence reconciliation foundation into a production-grade multi-service architecture with multi-modal processing (images, receipts, EXIF), advanced fraud pattern detection (serial fraud, wardrobing, behavioral anomalies), third-party webhooks, and an investigator review dashboard.

---

## Architecture Overview

```
                                  ┌───────────────────────────┐
                                  │   Investigator Dashboard  │
                                  │    (HTML / Port 3000)     │
                                  └─────────────┬─────────────┘
                                                │
┌─────────────────────────┐        ┌────────────▼──────────────┐
│  Third-Party Webhooks   ├───────►│       Claim Service       │ (Port 8080)
│ (Shipping, Payment, KYC)│        │   (FastAPI + PostgreSQL)  │
└────────────┬────────────┘        └────────────┬──────────────┘
             │                                  │
             │                     ┌────────────▼──────────────┐
             │                     │     Evidence Service      │ (Port 8081)
             │                     │     (FastAPI + MinIO)     │
             │                     └────────────┬──────────────┘
             │                                  │
             └──────────────────────────────────┼───────────────────────────────┐
                                                │                               │
                                       RabbitMQ Message Bus                     │
                                                │                               │
                      ┌─────────────────────────┼────────────────────────┐      │
                      │                         │                        │      │
           ┌──────────▼──────────┐   ┌──────────▼──────────┐  ┌──────────▼──────▼─────┐
           │ Multi-Modal Processor│   │ Fraud Detection Eng.│  │ Integration Service │
           │   (OpenCV + OCR)    │   │ (4-Signal Detector) │  │  (Webhooks + DLQ)   │
           │     (Port 8082)     │   │  (Port 8083 + Redis)│  │     (Port 8085)     │
           └──────────┬──────────┘   └──────────┬──────────┘  └─────────────────────┘
                      │                         │
                      └─────────────────────────┼────────────────────────┐
                                                │                        │
                                   ┌────────────▼─────────────┐          │
                                   │    Verdict Generator     │ (Port 8084)
                                   │ (Decision Engine + Ph1)  │
                                   └──────────────────────────┘
```

---

## Port Allocation

| Service | Port | Description |
|---|---|---|
| **Claim Service** | 8080 | Claim ingestion, lifecycle management, investigator assignment & override |
| **Evidence Service** | 8081 | Multi-modal file upload (MinIO), artifact retrieval |
| **Multi-Modal Processor** | 8082 | OpenCV wear detection, EXIF extraction, color consistency, OCR |
| **Fraud Detection Engine** | 8083 | Serial fraudster, behavioral anomaly, wardrobing, cross-org ring detector |
| **Verdict Generator** | 8084 | Signal aggregation + Phase 1 engine $\rightarrow$ REFUND/REJECT/INVESTIGATE |
| **Integration Service** | 8085 | Carrier delivery webhooks, payment status webhooks, OpenCV object detection |
| **Investigator Dashboard** | 3000 | Responsive UI for review queue and verdict overrides |
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | Customer fraud pattern cache |
| **RabbitMQ** | 5672 / 15672 | Message broker (15672: Management UI) |
| **MinIO** | 9000 / 9001 | Object storage (9001: MinIO Console) |
| **Elasticsearch** | 9200 | Audit logs and analytics |

---

## Quick Start (Local Development)

### 1. Start Stateful Infrastructure (Docker)
```bash
docker compose -f phase-2/docker-compose.yml up -d postgres redis rabbitmq minio
```

### 2. Apply Schema Extensions
```bash
psql -h localhost -U trinetra_user -d trinetra -f phase-2/schema/schema_extensions.sql
```

### 3. Run Unit Tests
```bash
python -m unittest discover -s phase-2/tests -p "*.py"
```

### 4. Start Services Locally (Python)
In separate terminals:
```bash
# Claim Service
python phase-2/services/claim_service/main.py

# Evidence Service
python phase-2/services/evidence_service/main.py

# Multi-Modal Processor
python phase-2/services/multimodal_processor/main.py

# Fraud Detection Engine
python phase-2/services/fraud_engine/main.py

# Verdict Generator
python phase-2/services/verdict_generator/main.py

# Integration Service
python phase-2/services/integration_service/main.py
```

### 5. Access Investigator Dashboard
Open [`phase-2/dashboard/index.html`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/dashboard/index.html) in any web browser, or serve via Nginx on port 3000.
