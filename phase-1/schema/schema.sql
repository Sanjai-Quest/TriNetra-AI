-- PostgreSQL Schema for TriNetra AI Phase 1: Research MVP
-- Stores canonical entity resolution, multi-source evidence, normalized attributes, ground truth, and predictions.

-- Drop existing tables if re-running
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS ground_truth CASCADE;
DROP TABLE IF EXISTS evidence_attribute CASCADE;
DROP TABLE IF EXISTS evidence_record CASCADE;
DROP TABLE IF EXISTS entity_resolution CASCADE;

-- 1. Entity Resolution Table
CREATE TABLE entity_resolution (
    id SERIAL PRIMARY KEY,
    canonical_product_id UUID NOT NULL,
    source_organization VARCHAR(50) NOT NULL,
    source_system_id VARCHAR(100) NOT NULL,
    mapping_confidence FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_canonical ON entity_resolution(canonical_product_id);
CREATE INDEX idx_entity_source ON entity_resolution(source_organization, source_system_id);

-- 2. Evidence Record Table
CREATE TABLE evidence_record (
    id SERIAL PRIMARY KEY,
    evidence_id UUID NOT NULL,
    canonical_product_id UUID NOT NULL,
    case_id VARCHAR(50) NOT NULL,
    source_organization VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evidence_case ON evidence_record(case_id);
CREATE INDEX idx_evidence_canonical ON evidence_record(canonical_product_id);
CREATE INDEX idx_evidence_source ON evidence_record(source_organization);

-- 3. Evidence Attribute Table (Normalized attributes)
CREATE TABLE evidence_attribute (
    id SERIAL PRIMARY KEY,
    evidence_id UUID NOT NULL,
    attribute_name VARCHAR(100) NOT NULL,
    original_value VARCHAR(255),
    normalized_value VARCHAR(255) NOT NULL,
    unit VARCHAR(50),
    data_type VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0
);

CREATE INDEX idx_attribute_evidence ON evidence_attribute(evidence_id);
CREATE INDEX idx_attribute_name ON evidence_attribute(attribute_name);

-- 4. Ground Truth Table (For experimental evaluation)
CREATE TABLE ground_truth (
    case_id VARCHAR(50) PRIMARY KEY,
    expected_status VARCHAR(50) NOT NULL, -- 'CONSISTENT', 'CONFLICT', 'INCONCLUSIVE'
    conflict_types VARCHAR(255),
    severity VARCHAR(50),
    root_cause TEXT
);

-- 5. Predictions Table
CREATE TABLE predictions (
    case_id VARCHAR(50) PRIMARY KEY,
    baseline_1_prediction VARCHAR(50),
    baseline_2_prediction VARCHAR(50),
    baseline_3_prediction VARCHAR(50),
    trinetra_prediction VARCHAR(50),
    trinetra_confidence FLOAT,
    trinetra_status VARCHAR(50),
    conflicts_detected TEXT
);
