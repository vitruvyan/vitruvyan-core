-- Vault Keepers migration: enforce audit idempotency by correlation_id
-- Safe to run multiple times.
-- Strategy:
--   1) Ensure vault_audit_log table exists.
--   2) Remove pre-existing duplicates deterministically (keep latest).
--   3) Add UNIQUE constraint on correlation_id if missing.

BEGIN;

CREATE TABLE IF NOT EXISTS vault_audit_log (
    record_id VARCHAR PRIMARY KEY,
    timestamp TIMESTAMP,
    operation VARCHAR,
    performed_by VARCHAR,
    resource_type VARCHAR,
    resource_id VARCHAR,
    action VARCHAR,
    status VARCHAR,
    correlation_id VARCHAR,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Keep only the most recent row per correlation_id.
WITH ranked AS (
    SELECT
        ctid,
        correlation_id,
        ROW_NUMBER() OVER (
            PARTITION BY correlation_id
            ORDER BY created_at DESC NULLS LAST, timestamp DESC NULLS LAST, record_id DESC
        ) AS rn
    FROM vault_audit_log
    WHERE correlation_id IS NOT NULL
)
DELETE FROM vault_audit_log target
USING ranked src
WHERE target.ctid = src.ctid
  AND src.rn > 1;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'vault_audit_log_correlation_unique'
          AND conrelid = 'vault_audit_log'::regclass
    ) THEN
        ALTER TABLE vault_audit_log
        ADD CONSTRAINT vault_audit_log_correlation_unique
        UNIQUE (correlation_id);
    END IF;
END $$;

COMMIT;
