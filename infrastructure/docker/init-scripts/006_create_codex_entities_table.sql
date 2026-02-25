-- =============================================================================
-- Codex Hunters — Entity Storage Table
-- =============================================================================
-- Purpose:
--   Primary entity storage for the Codex Hunters bind pipeline.
--   Entities flow: discover → restore → bind (this table)
--
-- Notes:
--   - Idempotent (safe to run multiple times)
--   - UPSERT pattern via ON CONFLICT (entity_id) DO UPDATE
--   - GIN index on data JSONB for flexible querying
-- =============================================================================

CREATE TABLE IF NOT EXISTS entities (
    entity_id   VARCHAR(255)   PRIMARY KEY,
    data        JSONB          NOT NULL,
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- Fast lookup by creation time (for recent entities listing)
CREATE INDEX IF NOT EXISTS idx_entities_created_at
    ON entities(created_at);

-- GIN index for JSONB containment queries (@>, ?)
CREATE INDEX IF NOT EXISTS idx_entities_data_gin
    ON entities USING gin (data);
