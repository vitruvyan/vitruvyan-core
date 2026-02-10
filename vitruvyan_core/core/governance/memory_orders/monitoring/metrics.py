"""
Memory Orders — Metric Name Constants

Prometheus metric names for dual-memory coherence system.
NO prometheus_client imports. Names only.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — monitoring)
"""

# ========================================
#  Coherence Metrics
# ========================================

COHERENCE_DRIFT_PCT = "memory_coherence_drift_percentage"
COHERENCE_DRIFT_ABS = "memory_coherence_drift_absolute"
COHERENCE_STATUS = "memory_coherence_status"
COHERENCE_CHECK_DURATION_S = "memory_coherence_check_duration_seconds"


# ========================================
#  Health Metrics
# ========================================

HEALTH_STATUS = "memory_health_status"
HEALTH_SCORE = "memory_health_score"
HEALTH_CHECK_DURATION_S = "memory_health_check_duration_seconds"


# ========================================
#  Component Health Metrics
# ========================================

ARCHIVARIUM_CONNECTED = "memory_archivarium_connected"
MNEMOSYNE_CONNECTED = "memory_mnemosyne_connected"
REDIS_CONNECTED = "memory_redis_connected"
EMBEDDING_API_CONNECTED = "memory_embedding_api_connected"
BABEL_GARDENS_CONNECTED = "memory_babel_gardens_connected"


# ========================================
#  Sync Metrics
# ========================================

SYNC_OPERATIONS_TOTAL = "memory_sync_operations_total"
SYNC_DURATION_S = "memory_sync_duration_seconds"
SYNC_FAILURES_TOTAL = "memory_sync_failures_total"
SYNC_LAST_TIMESTAMP = "memory_sync_last_timestamp"


# ========================================
#  Data Metrics
# ========================================

ARCHIVARIUM_RECORD_COUNT = "memory_archivarium_record_count"
MNEMOSYNE_POINT_COUNT = "memory_mnemosyne_point_count"
DUAL_MEMORY_QUERIES_TOTAL = "memory_dual_memory_queries_total"


# ========================================
#  Audit Metrics
# ========================================

AUDIT_RECORDS_TOTAL = "memory_audit_records_total"
AUDIT_WRITE_DURATION_S = "memory_audit_write_duration_seconds"
