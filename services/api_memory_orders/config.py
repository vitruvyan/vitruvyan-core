"""
Memory Orders — Service Configuration

Centralized environment variable management.
ALL os.getenv() calls MUST be here.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2)
"""

import os


class Settings:
    """Memory Orders service configuration."""
    
    # Service identity
    SERVICE_NAME = "api_memory_orders"
    SERVICE_PORT = int(os.getenv("MEMORY_API_PORT", "8016"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # PostgreSQL (Archivarium)
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "core_postgres")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "vitruvyan_core")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "vitruvyan_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    # Qdrant (Mnemosyne)
    QDRANT_HOST = os.getenv("QDRANT_HOST", "core_qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "entities_embeddings")
    
    # Redis (Cognitive Bus)
    REDIS_HOST = os.getenv("REDIS_HOST", "core_redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    
    # External services (for health checks)
    EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://vitruvyan_api_embedding:8010")
    BABEL_GARDENS_URL = os.getenv("BABEL_GARDENS_URL", "http://vitruvyan_babel_gardens:8009")
    
    # Coherence thresholds
    COHERENCE_THRESHOLD_HEALTHY = float(os.getenv("COHERENCE_THRESHOLD_HEALTHY", "5.0"))
    COHERENCE_THRESHOLD_WARNING = float(os.getenv("COHERENCE_THRESHOLD_WARNING", "15.0"))
    
    # Interoperability channels
    VAULT_AUDIT_REQUEST_CHANNEL = os.getenv("VAULT_AUDIT_REQUEST_CHANNEL", "audit.vault.requested")

    # Reconciliation execution mode
    MEMORY_RECONCILIATION_MODE = os.getenv("MEMORY_RECONCILIATION_MODE", "dry_run").lower()
    MEMORY_RECONCILIATION_LOCK_TTL_S = int(os.getenv("MEMORY_RECONCILIATION_LOCK_TTL_S", "300"))
    MEMORY_RECONCILIATION_IDEMPOTENCY_TTL_S = int(os.getenv("MEMORY_RECONCILIATION_IDEMPOTENCY_TTL_S", "900"))
    MEMORY_RECONCILIATION_MAX_DELETE_RATIO = float(os.getenv("MEMORY_RECONCILIATION_MAX_DELETE_RATIO", "0.20"))
    MEMORY_RECONCILIATION_RETRY_MAX = int(os.getenv("MEMORY_RECONCILIATION_RETRY_MAX", "2"))
    MEMORY_RECONCILIATION_RETRY_BACKOFF_MS = int(os.getenv("MEMORY_RECONCILIATION_RETRY_BACKOFF_MS", "250"))
    MEMORY_RECONCILIATION_DEAD_LETTER_CHANNEL = os.getenv(
        "MEMORY_RECONCILIATION_DEAD_LETTER_CHANNEL",
        "memory.reconciliation.dead_letter",
    )
    
    # Feature flags
    ENABLE_AUTO_SYNC = os.getenv("ENABLE_AUTO_SYNC", "false").lower() == "true"
    ENABLE_PROMETHEUS = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"


settings = Settings()

if settings.MEMORY_RECONCILIATION_MODE not in {"dry_run", "assisted", "autonomous"}:
    settings.MEMORY_RECONCILIATION_MODE = "dry_run"

if settings.MEMORY_RECONCILIATION_MAX_DELETE_RATIO < 0:
    settings.MEMORY_RECONCILIATION_MAX_DELETE_RATIO = 0.0
if settings.MEMORY_RECONCILIATION_MAX_DELETE_RATIO > 1:
    settings.MEMORY_RECONCILIATION_MAX_DELETE_RATIO = 1.0
