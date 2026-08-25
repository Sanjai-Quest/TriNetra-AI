# TriNetra AI: Cross-Organizational Evidence Reconciliation & Multi-Modal Fraud Prevention

[![Java 21](https://img.shields.io/badge/Java-21-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot 3.2](https://img.shields.io/badge/Spring%20Boot-3.2-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue.svg)](https://www.typescriptlang.org/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-yellow.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-orange.svg)](https://www.rabbitmq.com/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)

TriNetra AI ("Three Eyes") is an enterprise fraud prevention platform that reconciles multi-source physical and digital telemetry across the e-commerce supply chain to eliminate return fraud and reduce false negatives.

---

## 🚀 Key Highlights

- **Statistically Validated (Phase 1):** Achieved **100% false-negative reduction** over single-source baselines on 1,000 synthetic lifecycles ($\chi^2 = 53.02, p < 0.0001$).
- **Spring Boot 3.2 Microservices (Phase 2):** Modular services for Claim Ingestion, Evidence Management, Fraud Detection, Verdict Generation, and Third-Party Webhooks.
- **Multi-Modal Vision Engine:** Lightweight OpenCV computer vision pipeline for wear detection, EXIF extraction, and receipt OCR without heavy ML model dependencies.
- **React 18 Dashboard:** Modern dark-mode UI with live claim triage queues, risk meters, and human-in-the-loop override audit logging.

---

## 🏗️ System Architecture

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

## 📁 Repository Structure

- [`phase-1/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-1/): Research baseline, entity resolution, canonical normalization, and 1,000-case evaluation suite.
- [`phase-2/spring-services/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/spring-services/): Native Spring Boot 3.2 microservices (`claim-service`, `evidence-service`, `fraud-detection-engine`, `verdict-generator`, `integration-service`).
- [`phase-2/services/multimodal_processor/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/services/multimodal_processor/): Python FastAPI OpenCV / OCR vision worker.
- [`phase-2/frontend-react/`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/phase-2/frontend-react/): React 18 + TypeScript + Vite Investigator Dashboard.
- [`PROJECT_DOCUMENTATION.md`](file:///c:/Users/mitsu/Downloads/TriNetra%20AI/PROJECT_DOCUMENTATION.md): Detailed architectural & algorithmic specifications.

---

## ⚡ Quick Start

### 1. Start Backend (Claim Service on Port 8080)
```powershell
cd phase-2/spring-services/claim-service
mvn spring-boot:run "-Dspring-boot.run.profiles=local"
```

### 2. Start Frontend (React Dashboard on Port 3000)
```powershell
cd phase-2/frontend-react
npm run dev
```

### 3. Ingest a Test Claim
```powershell
cd phase-2
powershell -ExecutionPolicy Bypass -File test_claim.ps1
```

Visit **`http://localhost:3000`** to view and triage the claim.
