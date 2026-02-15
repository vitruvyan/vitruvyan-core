"""
Vault Keepers — Metric Name Constants

Prometheus metric names for archival and persistence operations.
NO prometheus_client imports. Names only.

Sacred Order: Memory (Archival)
Layer: Foundational (LIVELLO 1 — monitoring)
"""

# ========================================
#  Archival Metrics
# ========================================

ARCHIVE_OPERATIONS_TOTAL = "vault_archive_operations_total"
ARCHIVE_DURATION_S = "vault_archive_duration_seconds"
ARCHIVE_FAILURES_TOTAL = "vault_archive_failures_total"
ARCHIVE_LAST_TIMESTAMP = "vault_archive_last_timestamp"


# ========================================
#  Snapshot Metrics
# ========================================

SNAPSHOT_CREATED_TOTAL = "vault_snapshot_created_total"
SNAPSHOT_RESTORED_TOTAL = "vault_snapshot_restored_total"
SNAPSHOT_DURATION_S = "vault_snapshot_duration_seconds"
SNAPSHOT_SIZE_BYTES = "vault_snapshot_size_bytes"


# ========================================
#  Audit Metrics
# ========================================

AUDIT_RECORDS_TOTAL = "vault_audit_records_total"
AUDIT_WRITE_DURATION_S = "vault_audit_write_duration_seconds"
AUDIT_IDEMPOTENT_SKIPS_TOTAL = "vault_audit_idempotent_skips_total"


# ========================================
#  Health Metrics
# ========================================

HEALTH_STATUS = "vault_health_status"
HEALTH_CHECK_DURATION_S = "vault_health_check_duration_seconds"
POSTGRES_CONNECTED = "vault_postgres_connected"
QDRANT_CONNECTED = "vault_qdrant_connected"


# ========================================
#  Storage Metrics
# ========================================

STORAGE_RECORDS_TOTAL = "vault_storage_records_total"
STORAGE_QUERIES_TOTAL = "vault_storage_queries_total"
STORAGE_QUERY_DURATION_S = "vault_storage_query_duration_seconds"
