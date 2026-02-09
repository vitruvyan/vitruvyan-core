-- Orthodoxy Wardens Database Schema
-- Sacred Orders Refactoring - vitruvyan-core
-- Created: 2026-02-09

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Table: confessions (audit requests/events)
-- =====================================================
CREATE TABLE IF NOT EXISTS confessions (
    id SERIAL PRIMARY KEY,
    confession_id VARCHAR(255) UNIQUE NOT NULL,
    service VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    sacred_status VARCHAR(50) DEFAULT 'pending',  -- pending, blessed, heretical, failed
    orthodoxy_score FLOAT DEFAULT NULL,
    penance_progress FLOAT DEFAULT 0.0,
    divine_results JSONB,
    assigned_warden VARCHAR(100) DEFAULT 'confessor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NULL
);

-- Indexes for confessions
CREATE INDEX IF NOT EXISTS idx_confessions_confession_id ON confessions(confession_id);
CREATE INDEX IF NOT EXISTS idx_confessions_service ON confessions(service);
CREATE INDEX IF NOT EXISTS idx_confessions_status ON confessions(sacred_status);
CREATE INDEX IF NOT EXISTS idx_confessions_created_at ON confessions(created_at DESC);

-- =====================================================
-- Table: audit_findings (validation results)
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_findings (
    id SERIAL PRIMARY KEY,
    confession_id VARCHAR(255) NOT NULL,
    finding_type VARCHAR(100) NOT NULL,  -- violation, warning, blessing
    severity VARCHAR(50),  -- critical, high, medium, low
    message TEXT,
    context JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (confession_id) REFERENCES confessions(confession_id) ON DELETE CASCADE
);

-- Indexes for audit_findings
CREATE INDEX IF NOT EXISTS idx_audit_findings_confession_id ON audit_findings(confession_id);
CREATE INDEX IF NOT EXISTS idx_audit_findings_type ON audit_findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_audit_findings_timestamp ON audit_findings(timestamp DESC);

-- =====================================================
-- Table: sacred_records (event log for recent queries)
-- =====================================================
CREATE TABLE IF NOT EXISTS sacred_records (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    service VARCHAR(100),
    status VARCHAR(50),
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sacred_records
CREATE INDEX IF NOT EXISTS idx_sacred_records_event_type ON sacred_records(event_type);
CREATE INDEX IF NOT EXISTS idx_sacred_records_service ON sacred_records(service);
CREATE INDEX IF NOT EXISTS idx_sacred_records_timestamp ON sacred_records(timestamp DESC);

-- =====================================================
-- Table: orthodoxy_metrics (performance tracking)
-- =====================================================
CREATE TABLE IF NOT EXISTS orthodoxy_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for metrics
CREATE INDEX IF NOT EXISTS idx_orthodoxy_metrics_name ON orthodoxy_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_orthodoxy_metrics_timestamp ON orthodoxy_metrics(timestamp DESC);

-- =====================================================
-- Function: Update updated_at timestamp
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at on confessions
CREATE TRIGGER update_confessions_updated_at
BEFORE UPDATE ON confessions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Initial Data / Seed (Optional)
-- =====================================================

-- Insert test confession for validation
INSERT INTO confessions (
    confession_id, 
    service, 
    event_type, 
    payload, 
    sacred_status
) VALUES (
    'test_confession_init',
    'orthodoxy_wardens',
    'system_init',
    '{"description": "Initial schema creation", "version": "2.0.0"}'::jsonb,
    'blessed'
) ON CONFLICT (confession_id) DO NOTHING;

-- Insert test sacred record
INSERT INTO sacred_records (
    event_type,
    service,
    status,
    details
) VALUES (
    'schema_initialization',
    'orthodoxy_wardens',
    'completed',
    '{"tables_created": ["confessions", "audit_findings", "sacred_records", "orthodoxy_metrics"]}'::jsonb
);

-- =====================================================
-- Views (Optional - for convenience)
-- =====================================================

-- View: Recent blessed confessions
CREATE OR REPLACE VIEW recent_blessed_confessions AS
SELECT 
    confession_id,
    service,
    event_type,
    sacred_status,
    orthodoxy_score,
    created_at,
    completed_at
FROM confessions
WHERE sacred_status = 'blessed'
ORDER BY completed_at DESC
LIMIT 100;

-- View: Pending confessions (for monitoring)
CREATE OR REPLACE VIEW pending_confessions AS
SELECT 
    confession_id,
    service,
    event_type,
    created_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) as age_seconds
FROM confessions
WHERE sacred_status = 'pending'
ORDER BY created_at ASC;

-- =====================================================
-- Grants (adjust as needed)
-- =====================================================

-- Grant permissions to vitruvyan_omni_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vitruvyan_omni_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vitruvyan_omni_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO vitruvyan_omni_user;

-- =====================================================
-- Schema Information
-- =====================================================

COMMENT ON TABLE confessions IS 'Audit confessions - requests for Orthodoxy Wardens validation';
COMMENT ON TABLE audit_findings IS 'Validation results from Orthodoxy audits';
COMMENT ON TABLE sacred_records IS 'Event log for all Orthodoxy Wardens activities';
COMMENT ON TABLE orthodoxy_metrics IS 'Performance and operational metrics';
