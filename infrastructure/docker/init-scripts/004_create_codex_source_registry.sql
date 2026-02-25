-- =============================================================================
-- Codex Hunters Source Registry (DB-backed source/topic configuration)
-- =============================================================================
-- Purpose:
--   Remove hardcoded source/subreddit lists from code paths by storing source
--   configuration in PostgreSQL.
--
-- Notes:
--   - Safe to run multiple times (idempotent).
--   - Seed includes legacy aliases (primary/secondary) plus finance sources.
-- =============================================================================

CREATE TABLE IF NOT EXISTS codex_source_registry (
    source_key VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(128) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    description TEXT,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 60 CHECK (rate_limit_per_minute > 0),
    timeout_seconds INTEGER NOT NULL DEFAULT 30 CHECK (timeout_seconds > 0),
    retry_attempts INTEGER NOT NULL DEFAULT 3 CHECK (retry_attempts >= 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS codex_source_topics (
    id BIGSERIAL PRIMARY KEY,
    source_key VARCHAR(64) NOT NULL REFERENCES codex_source_registry(source_key) ON DELETE CASCADE,
    topic_kind VARCHAR(32) NOT NULL,
    topic_value VARCHAR(255) NOT NULL,
    locale VARCHAR(16),
    priority SMALLINT NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_key, topic_kind, topic_value)
);

CREATE INDEX IF NOT EXISTS idx_codex_source_registry_enabled
    ON codex_source_registry (enabled);

CREATE INDEX IF NOT EXISTS idx_codex_source_registry_type
    ON codex_source_registry (source_type);

CREATE INDEX IF NOT EXISTS idx_codex_source_topics_source
    ON codex_source_topics (source_key);

CREATE INDEX IF NOT EXISTS idx_codex_source_topics_kind_enabled
    ON codex_source_topics (topic_kind, enabled);

INSERT INTO codex_source_registry (
    source_key, display_name, source_type, description,
    rate_limit_per_minute, timeout_seconds, retry_attempts, enabled, config_json
) VALUES
    (
        'primary',
        'Primary Source',
        'generic',
        'Legacy default source alias for compatibility',
        120, 30, 3, TRUE,
        '{"legacy_alias": true, "default": true}'::jsonb
    ),
    (
        'secondary',
        'Secondary Source',
        'generic',
        'Legacy secondary source alias for compatibility',
        60, 30, 3, TRUE,
        '{"legacy_alias": true}'::jsonb
    ),
    (
        'yfinance',
        'Yahoo Finance',
        'market_data',
        'Price/fundamentals source',
        30, 30, 3, TRUE,
        '{"provider": "yfinance"}'::jsonb
    ),
    (
        'reddit',
        'Reddit',
        'sentiment',
        'Community sentiment source (finance subreddits in codex_source_topics)',
        30, 30, 3, TRUE,
        '{"provider": "praw"}'::jsonb
    ),
    (
        'google_news',
        'Google News',
        'news',
        'RSS financial news source',
        60, 30, 3, TRUE,
        '{"provider": "rss"}'::jsonb
    ),
    (
        'fred',
        'FRED',
        'macro',
        'Federal Reserve Economic Data source',
        50, 30, 3, TRUE,
        '{"provider": "fred"}'::jsonb
    )
ON CONFLICT (source_key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    source_type = EXCLUDED.source_type,
    description = EXCLUDED.description,
    rate_limit_per_minute = EXCLUDED.rate_limit_per_minute,
    timeout_seconds = EXCLUDED.timeout_seconds,
    retry_attempts = EXCLUDED.retry_attempts,
    enabled = EXCLUDED.enabled,
    config_json = EXCLUDED.config_json,
    updated_at = NOW();

INSERT INTO codex_source_topics (source_key, topic_kind, topic_value, locale, priority, enabled, metadata) VALUES
    ('reddit', 'subreddit', 'investing', 'en', 10, TRUE, '{}'::jsonb),
    ('reddit', 'subreddit', 'stocks', 'en', 20, TRUE, '{}'::jsonb),
    ('reddit', 'subreddit', 'wallstreetbets', 'en', 30, TRUE, '{}'::jsonb),
    ('reddit', 'subreddit', 'ValueInvesting', 'en', 40, TRUE, '{}'::jsonb),
    ('reddit', 'subreddit', 'stockmarket', 'en', 50, TRUE, '{}'::jsonb)
ON CONFLICT (source_key, topic_kind, topic_value) DO UPDATE SET
    locale = EXCLUDED.locale,
    priority = EXCLUDED.priority,
    enabled = EXCLUDED.enabled,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

GRANT SELECT, INSERT, UPDATE, DELETE ON codex_source_registry TO mercator_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON codex_source_topics TO mercator_user;
GRANT USAGE, SELECT ON SEQUENCE codex_source_topics_id_seq TO mercator_user;

COMMENT ON TABLE codex_source_registry IS 'Codex source definitions loaded by api_codex_hunters (no hardcoded source lists).';
COMMENT ON TABLE codex_source_topics IS 'Codex source topics (e.g. subreddit list) loaded at runtime from DB.';
