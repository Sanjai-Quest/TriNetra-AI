"""
Shared Pydantic models for all TriNetra Phase 2 services.
All services import from this module to maintain consistent data contracts.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class ClaimStatus(str, Enum):
    CREATED                = "CREATED"
    EVIDENCE_PENDING       = "EVIDENCE_PENDING"
    PROCESSING             = "PROCESSING"
    DECISION_PENDING_REVIEW = "DECISION_PENDING_REVIEW"
    APPROVED               = "APPROVED"
    REJECTED               = "REJECTED"
    INVESTIGATING          = "INVESTIGATING"
    CLOSED                 = "CLOSED"


class VerdictEnum(str, Enum):
    REFUND      = "REFUND"
    REJECT      = "REJECT"
    INVESTIGATE = "INVESTIGATE"


class EvidenceType(str, Enum):
    PRODUCT_IMAGE = "product_image"
    RECEIPT       = "receipt"
    SHIPPING      = "shipping"
    BEHAVIORAL    = "behavioral"


class EvidenceStatus(str, Enum):
    PENDING   = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED    = "FAILED"


class FraudSeverity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    OVERRIDE       = "OVERRIDE"
    APPROVE        = "APPROVE"
    REJECT         = "REJECT"
    ASSIGN         = "ASSIGN"
    COMMENT        = "COMMENT"
    MARK_FOR_REVIEW = "MARK_FOR_REVIEW"


class IntegrationProvider(str, Enum):
    SHIPPING_CARRIER   = "shipping_carrier"
    PAYMENT_PROCESSOR  = "payment_processor"
    IMAGE_API          = "image_api"
    KYC_SERVICE        = "kyc_service"


# ─────────────────────────────────────────────────────────────────────────────
# Claim Models
# ─────────────────────────────────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    customer_id:      UUID
    order_id:         Optional[str]   = None
    product_id:       Optional[str]   = None
    product_category: Optional[str]   = None
    product_value:    Optional[float] = None
    claim_amount:     Optional[float] = None
    claim_reason:     Optional[str]   = None
    delivery_date:    Optional[datetime] = None
    return_date:      Optional[datetime] = None
    tracking_number:  Optional[str]   = None
    payment_txn_id:   Optional[str]   = None


class ClaimResponse(BaseModel):
    claim_id:          UUID
    customer_id:       UUID
    order_id:          Optional[str]
    product_category:  Optional[str]
    product_value:     Optional[float]
    claim_amount:      Optional[float]
    claim_reason:      Optional[str]
    delivery_date:     Optional[datetime]
    return_date:       Optional[datetime]
    status:            ClaimStatus
    automated_verdict: Optional[str]
    confidence_score:  Optional[float]
    created_at:        datetime

    model_config = {"from_attributes": True}


class ClaimOverride(BaseModel):
    verdict:          VerdictEnum
    reasoning:        str = Field(min_length=10)
    investigator_id:  UUID


class ClaimSearchParams(BaseModel):
    status:     Optional[ClaimStatus] = None
    risk_level: Optional[FraudSeverity] = None
    limit:      int = Field(default=50, le=200)
    offset:     int = Field(default=0, ge=0)


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Models
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceResponse(BaseModel):
    evidence_id:  UUID
    claim_id:     UUID
    evidence_type: EvidenceType
    file_url:     Optional[str]
    status:       EvidenceStatus
    uploaded_at:  datetime

    model_config = {"from_attributes": True}


class EvidenceArtifactResponse(BaseModel):
    artifact_id:       UUID
    evidence_id:       UUID
    artifact_type:     str
    data:              Dict[str, Any]
    confidence_score:  Optional[float]
    processor_service: Optional[str]
    created_at:        datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Fraud Signal Models
# ─────────────────────────────────────────────────────────────────────────────

class FraudSignalResponse(BaseModel):
    signal_id:              UUID
    claim_id:               UUID
    signal_type:            str
    severity:               FraudSeverity
    confidence_score:       float
    reasoning:              Optional[str]
    cross_claim_indicators: Optional[Dict[str, Any]]
    created_at:             datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Verdict Models
# ─────────────────────────────────────────────────────────────────────────────

class VerdictReasoningResponse(BaseModel):
    reasoning_id:           UUID
    claim_id:               UUID
    verdict:                VerdictEnum
    evidence_summary:       Optional[Dict[str, Any]]
    fraud_signals_detected: Optional[List[Dict[str, Any]]]
    factor_weights:         Optional[Dict[str, Any]]
    final_confidence_score: float
    reasoning_text:         Optional[str]
    generated_at:           datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Message Bus Events
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceUploadedEvent(BaseModel):
    event_type:   str = "evidence.uploaded"
    evidence_id:  UUID
    claim_id:     UUID
    evidence_type: EvidenceType
    file_url:     str
    timestamp:    datetime = Field(default_factory=datetime.utcnow)


class EvidenceProcessedEvent(BaseModel):
    event_type:   str = "evidence.processed"
    evidence_id:  UUID
    claim_id:     UUID
    artifact_types: List[str] = []
    timestamp:    datetime = Field(default_factory=datetime.utcnow)


class FraudAnalysisCompleteEvent(BaseModel):
    event_type:    str = "fraud.analysis.complete"
    claim_id:      UUID
    signal_count:  int = 0
    max_severity:  Optional[str] = None
    timestamp:     datetime = Field(default_factory=datetime.utcnow)


class VerdictGeneratedEvent(BaseModel):
    event_type:       str = "verdict.generated"
    claim_id:         UUID
    verdict:          VerdictEnum
    confidence_score: float
    timestamp:        datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Wear Analysis Result
# ─────────────────────────────────────────────────────────────────────────────

class WearAnalysisResult(BaseModel):
    wear_score:           float  # 0.0 = new, 1.0 = heavily worn
    confidence:           float
    fold_detected:        bool   = False
    texture_anomaly:      bool   = False
    saturation_score:     float  = 1.0
    edge_density:         float  = 0.0
    estimated_wear_hours: str    = "<5"
    recommendation:       str    = "LOW_RISK"


class ReceiptParseResult(BaseModel):
    merchant_name:  Optional[str]   = None
    transaction_date: Optional[str] = None
    total_amount:   Optional[float] = None
    items:          List[Dict[str, Any]] = []
    raw_text:       Optional[str]   = None
    parse_confidence: float         = 0.0


class IntegrationWebhookRequest(BaseModel):
    provider:   IntegrationProvider
    event_type: str
    payload:    Dict[str, Any]
    claim_id:   Optional[UUID] = None
