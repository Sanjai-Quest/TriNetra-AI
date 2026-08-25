-- TriNetra AI: Phase 2 Database Schema Extensions
-- Run AFTER Phase 1 schema has been applied (phase-1/schema/schema.sql)
-- These tables extend the base schema with Phase 2 capabilities.

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. CLAIMS (Phase 2 extended version)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS claims (
    claim_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL,
    order_id            VARCHAR(100),
    product_id          VARCHAR(100),
    product_category    VARCHAR(100),
    product_value       NUMERIC(12,2),
    claim_amount        NUMERIC(12,2),
    claim_reason        TEXT,
    delivery_date       TIMESTAMPTZ,
    return_date         TIMESTAMPTZ,
    tracking_number     VARCHAR(100),
    payment_txn_id      VARCHAR(100),
    delivery_proof      BOOLEAN DEFAULT FALSE,
    status              VARCHAR(50) DEFAULT 'CREATED',
    automated_verdict   VARCHAR(50),
    confidence_score    FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    assigned_to         UUID,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claims_customer       ON claims(customer_id);
CREATE INDEX IF NOT EXISTS idx_claims_status         ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_order_id       ON claims(order_id);
CREATE INDEX IF NOT EXISTS idx_claims_created_at     ON claims(created_at);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. EVIDENCE (Phase 2: multi-modal file storage records)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    evidence_type       VARCHAR(50) NOT NULL,   -- product_image, receipt, shipping, behavioral
    file_url            TEXT,
    file_size_bytes     BIGINT,
    mime_type           VARCHAR(100),
    metadata            JSONB,
    status              VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, PROCESSED, FAILED
    uploaded_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_evidence_claim_id     ON evidence(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type         ON evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_status       ON evidence(status);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. EVIDENCE_ARTIFACTS (Phase 2: processed multi-modal outputs)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_artifacts (
    artifact_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id             UUID NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    artifact_type           VARCHAR(50) NOT NULL,
    -- Types: ocr_text | receipt_parsed | receipt_validation |
    --        wear_analysis | color_analysis | exif_metadata | object_detection
    content_type            VARCHAR(50) DEFAULT 'json',
    data                    JSONB NOT NULL,
    confidence_score        FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    processor_service       VARCHAR(100),
    processing_duration_ms  INT,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_artifact_type CHECK (artifact_type IN (
        'ocr_text', 'receipt_parsed', 'receipt_validation',
        'wear_analysis', 'color_analysis', 'exif_metadata', 'object_detection'
    ))
);

CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_evidence_id ON evidence_artifacts(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_type        ON evidence_artifacts(artifact_type);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. FRAUD_SIGNALS (Phase 2: detected fraud patterns)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fraud_signals (
    signal_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id                UUID NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    signal_type             VARCHAR(100) NOT NULL,
    -- Types: serial_fraudster | wardrobing | impossibly_fast_return |
    --        inflated_claim_amount | high_risk_category_abuse |
    --        cross_org_fraud_ring | color_inconsistency
    severity                VARCHAR(20) NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    confidence_score        FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    source_evidence_id      UUID REFERENCES evidence(evidence_id),
    reasoning               TEXT,
    cross_claim_indicators  JSONB,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at            TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_fraud_signals_claim_id  ON fraud_signals(claim_id);
CREATE INDEX IF NOT EXISTS idx_fraud_signals_type      ON fraud_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_fraud_signals_severity  ON fraud_signals(severity);

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. VERDICT_REASONING (Phase 2: full decision audit trail)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS verdict_reasoning (
    reasoning_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id                UUID NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    verdict                 VARCHAR(50) NOT NULL CHECK (verdict IN ('REFUND','REJECT','INVESTIGATE')),
    evidence_summary        JSONB,
    fraud_signals_detected  JSONB,
    factor_weights          JSONB,
    final_confidence_score  FLOAT NOT NULL CHECK (final_confidence_score >= 0.0 AND final_confidence_score <= 1.0),
    reasoning_text          TEXT,
    generated_at            TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_verdict_reasoning_claim_id ON verdict_reasoning(claim_id);
CREATE INDEX IF NOT EXISTS idx_verdict_reasoning_verdict  ON verdict_reasoning(verdict);

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. INVESTIGATOR_ACTIONS (Phase 2: human override audit log)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS investigator_actions (
    action_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    investigator_id     UUID NOT NULL,
    action_type         VARCHAR(50) NOT NULL CHECK (action_type IN (
                            'OVERRIDE','APPROVE','REJECT','ASSIGN','COMMENT','MARK_FOR_REVIEW'
                        )),
    override_verdict    VARCHAR(50),
    override_reasoning  TEXT,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_investigator_actions_investigator ON investigator_actions(investigator_id);
CREATE INDEX IF NOT EXISTS idx_investigator_actions_claim        ON investigator_actions(claim_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. INTEGRATION_EVENTS (Phase 2: third-party webhook log)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS integration_events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id        UUID REFERENCES claims(claim_id),
    provider        VARCHAR(100) NOT NULL,
    -- Values: shipping_carrier | payment_processor | image_api | kyc_service
    event_type      VARCHAR(100) NOT NULL,
    payload         JSONB NOT NULL,
    status          VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('success','failed','pending','pending_retry')),
    retry_count     INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_integration_events_claim    ON integration_events(claim_id);
CREATE INDEX IF NOT EXISTS idx_integration_events_provider ON integration_events(provider);
CREATE INDEX IF NOT EXISTS idx_integration_events_status   ON integration_events(status);

-- ─────────────────────────────────────────────────────────────────────────────
-- Utility: auto-update updated_at columns
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_claims_updated_at') THEN
        CREATE TRIGGER trg_claims_updated_at
            BEFORE UPDATE ON claims
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_evidence_artifacts_updated_at') THEN
        CREATE TRIGGER trg_evidence_artifacts_updated_at
            BEFORE UPDATE ON evidence_artifacts
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_integration_events_updated_at') THEN
        CREATE TRIGGER trg_integration_events_updated_at
            BEFORE UPDATE ON integration_events
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;
