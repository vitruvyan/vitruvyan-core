-- =============================================================================
-- Causal Event Log — F3.2 (Phase 3)
-- =============================================================================
-- Purpose:
--   Persist CognitiveEvent causal chain (trace_id, causation_id) to enable
--   post-hoc causal queries: "show me all events caused by event X" or
--   "reconstruct the causal tree for trace Y".
--
-- Notes:
--   - Idempotent (safe to run multiple times)
--   - Append-only (events are immutable once emitted)
--   - Indexed on trace_id for fast tree reconstruction
--   - Indexed on causation_id for parent→child traversal
-- =============================================================================

CREATE TABLE IF NOT EXISTS causal_event_log (
    id            BIGSERIAL PRIMARY KEY,
    event_id      VARCHAR(64)  NOT NULL UNIQUE,
    trace_id      VARCHAR(64)  NOT NULL,
    causation_id  VARCHAR(64),                    -- NULL for root events
    correlation_id VARCHAR(128),
    event_type    VARCHAR(128) NOT NULL,
    source        VARCHAR(128) NOT NULL,
    channel       VARCHAR(128),                   -- Redis Streams channel
    payload_hash  VARCHAR(64),                    -- SHA-256 of payload (audit, not content)
    created_at    TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Fast causal tree reconstruction by trace
CREATE INDEX IF NOT EXISTS idx_causal_event_log_trace_id
    ON causal_event_log (trace_id);

-- Parent→child traversal
CREATE INDEX IF NOT EXISTS idx_causal_event_log_causation_id
    ON causal_event_log (causation_id);

-- Timeline queries per source
CREATE INDEX IF NOT EXISTS idx_causal_event_log_source
    ON causal_event_log (source, created_at DESC);

-- Event type filtering
CREATE INDEX IF NOT EXISTS idx_causal_event_log_event_type
    ON causal_event_log (event_type);
