-- =============================================================================
-- Finance Learning Loop (MVP) — Feedback Event Store + User Learning Profile
-- =============================================================================
-- Purpose:
--   1) Persist user activity/feedback events (append-only)
--   2) Maintain per-user learning profile state (upsert-friendly)
--
-- Notes:
--   - Idempotent (safe to run multiple times)
--   - Domain-specific for finance vertical
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_feedback_events (
    id BIGSERIAL PRIMARY KEY,
    event_uuid VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(255) NOT NULL,
    source_service VARCHAR(64) NOT NULL,
    event_name VARCHAR(128) NOT NULL,
    event_version VARCHAR(16) NOT NULL DEFAULT 'v1',
    actor_type VARCHAR(32) NOT NULL DEFAULT 'user',
    feedback_signal VARCHAR(64) NOT NULL,
    feedback_value NUMERIC(8,4),
    correlation_id VARCHAR(128),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_feedback_events_user_created
    ON user_feedback_events (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_feedback_events_event_name
    ON user_feedback_events (event_name);

CREATE INDEX IF NOT EXISTS idx_user_feedback_events_source
    ON user_feedback_events (source_service);

CREATE INDEX IF NOT EXISTS idx_user_feedback_events_signal
    ON user_feedback_events (feedback_signal);

CREATE INDEX IF NOT EXISTS idx_user_feedback_events_correlation
    ON user_feedback_events (correlation_id)
    WHERE correlation_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS user_learning_profile (
    user_id VARCHAR(255) PRIMARY KEY,
    profile_version INTEGER NOT NULL DEFAULT 1,
    inferred_risk_tolerance VARCHAR(32),
    preference_vector JSONB NOT NULL DEFAULT '{}'::jsonb,
    behavior_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_overrides JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_processed_event_id BIGINT NOT NULL DEFAULT 0,
    last_feedback_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS user_learning_profile
    ADD COLUMN IF NOT EXISTS last_processed_event_id BIGINT NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_user_learning_profile_updated
    ON user_learning_profile (updated_at DESC);

GRANT SELECT, INSERT, UPDATE, DELETE ON user_feedback_events TO mercator_user;
GRANT USAGE, SELECT ON SEQUENCE user_feedback_events_id_seq TO mercator_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_learning_profile TO mercator_user;

COMMENT ON TABLE user_feedback_events IS
    'Append-only learning loop events from user activity (orders, portfolio actions, feedback).';

COMMENT ON TABLE user_learning_profile IS
    'Per-user learned profile used by finance ranking/recommendation pipelines.';
