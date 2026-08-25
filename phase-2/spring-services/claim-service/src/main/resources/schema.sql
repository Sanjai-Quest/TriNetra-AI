CREATE TABLE IF NOT EXISTS claims (
    claim_id            UUID PRIMARY KEY,
    customer_id         UUID NOT NULL,
    order_id            VARCHAR(100),
    product_id          VARCHAR(100),
    product_category    VARCHAR(100),
    product_value       NUMERIC(12,2),
    claim_amount        NUMERIC(12,2),
    claim_reason        TEXT,
    delivery_date       TIMESTAMP WITH TIME ZONE,
    return_date         TIMESTAMP WITH TIME ZONE,
    tracking_number     VARCHAR(100),
    payment_txn_id      VARCHAR(100),
    delivery_proof      BOOLEAN DEFAULT FALSE,
    status              VARCHAR(50) DEFAULT 'CREATED',
    automated_verdict   VARCHAR(50),
    confidence_score    DOUBLE PRECISION,
    assigned_to         UUID,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fraud_signals (
    signal_id               UUID PRIMARY KEY,
    claim_id                UUID NOT NULL,
    signal_type             VARCHAR(100) NOT NULL,
    severity                VARCHAR(20) NOT NULL,
    confidence_score        DOUBLE PRECISION NOT NULL,
    source_evidence_id      UUID,
    reasoning               TEXT,
    cross_claim_indicators  JSON,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at            TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS verdict_reasoning (
    reasoning_id            UUID PRIMARY KEY,
    claim_id                UUID NOT NULL,
    verdict                 VARCHAR(50) NOT NULL,
    evidence_summary        JSON,
    fraud_signals_detected  JSON,
    factor_weights          JSON,
    final_confidence_score  DOUBLE PRECISION NOT NULL,
    reasoning_text          TEXT,
    generated_at            TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS investigator_actions (
    action_id           UUID PRIMARY KEY,
    claim_id            UUID NOT NULL,
    investigator_id     UUID NOT NULL,
    action_type         VARCHAR(50) NOT NULL,
    override_verdict    VARCHAR(50),
    override_reasoning  TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
