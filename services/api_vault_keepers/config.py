"""
Vault Keepers — Service Configuration

All environment variables centralized in one place.
No scattered os.getenv() calls across modules.

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)
"""
import os


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_postgres_host() -> str:
    explicit = os.getenv("POSTGRES_HOST") or os.getenv("PG_HOST")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "mercator_postgres"
    return "localhost"


def _default_postgres_port() -> int:
    explicit = os.getenv("POSTGRES_PORT") or os.getenv("PG_PORT")
    if explicit:
        return int(explicit)
    if os.path.exists("/.dockerenv"):
        return 5432
    return 2432


def _default_qdrant_host() -> str:
    explicit = os.getenv("QDRANT_HOST")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "mercator_qdrant"
    return "localhost"


def _default_redis_host() -> str:
    explicit = os.getenv("REDIS_HOST")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "mercator_redis"
    return "localhost"


class Settings:
    """Vault Keepers service configuration"""
    
    # Service identity
    SERVICE_NAME = "api_vault_keepers"
    SERVICE_VERSION = "2.0.0"
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", os.getenv("VAULT_API_PORT", "8007")))
    SERVICE_HOST = os.getenv("SERVICE_HOST", os.getenv("VAULT_API_HOST", "0.0.0.0"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", os.getenv("VAULT_LOG_LEVEL", "INFO"))
    VAULT_DOMAIN = os.getenv("VAULT_DOMAIN", "generic").lower()
    
    # Redis / Cognitive Bus
    REDIS_HOST = _default_redis_host()
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # Consumer groups (Redis Streams)
    CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "vault_keepers_group")
    CONSUMER_NAME = os.getenv("CONSUMER_NAME", "vault_keeper_worker_1")
    
    # Sacred Channels (events this order listens to)
    SACRED_CHANNELS = [
        "vault.archive.requested",
        "vault.restore.requested",
        "vault.snapshot.requested",
        "audit.vault.requested",
        "orthodoxy.audit.completed",
        "engine.eval.completed",
    ]
    
    # PostgreSQL (aligned with docker-compose and PostgresAgent)
    POSTGRES_HOST = _default_postgres_host()
    POSTGRES_PORT = _default_postgres_port()
    POSTGRES_DB = os.getenv("POSTGRES_DB", "mercator")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "mercator_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    # Qdrant (vector database, aligned with docker-compose)
    QDRANT_HOST = _default_qdrant_host()
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "entities_embeddings")
    
    # Backup & Archive settings
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    ARCHIVE_ENABLED = _as_bool(os.getenv("ARCHIVE_ENABLED"), default=True)
    SNAPSHOT_INTERVAL_HOURS = int(os.getenv("SNAPSHOT_INTERVAL_HOURS", "24"))
    
    # Integrity check thresholds
    INTEGRITY_WARNING_THRESHOLD = float(os.getenv("INTEGRITY_WARNING_THRESHOLD", "0.9"))
    INTEGRITY_CRITICAL_THRESHOLD = float(os.getenv("INTEGRITY_CRITICAL_THRESHOLD", "0.7"))
    
    # Google Drive (for archive, if configured)
    GDRIVE_ENABLED = _as_bool(os.getenv("GDRIVE_ENABLED"), default=False)
    GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")

    # Finance vertical
    VAULT_FINANCE_SIGNAL_RETENTION_DAYS = int(
        os.getenv("VAULT_FINANCE_SIGNAL_RETENTION_DAYS", "1825")
    )
    VAULT_FINANCE_ARCHIVE_RETENTION_DAYS = int(
        os.getenv("VAULT_FINANCE_ARCHIVE_RETENTION_DAYS", "1825")
    )
    VAULT_FINANCE_DEFAULT_BACKUP_MODE = os.getenv(
        "VAULT_FINANCE_DEFAULT_BACKUP_MODE",
        "full",
    )
    VAULT_FINANCE_INCLUDE_VECTORS = _as_bool(
        os.getenv("VAULT_FINANCE_INCLUDE_VECTORS"),
        default=True,
    )
    
    # Event channels (emitting, not listening)
    CHANNEL_INTEGRITY_VALIDATED = "vault.integrity.validated"
    CHANNEL_BACKUP_COMPLETED = "vault.backup.completed"
    CHANNEL_RESTORE_COMPLETED = "vault.restore.completed"
    CHANNEL_ARCHIVE_STORED = "vault.archive.stored"
    CHANNEL_SNAPSHOT_CREATED = "vault.snapshot.created"


settings = Settings()

if settings.VAULT_DOMAIN not in {"generic", "finance"}:
    settings.VAULT_DOMAIN = "generic"

if settings.VAULT_DOMAIN == "finance":
    extra_channels = ("babel.sentiment.completed",)
    for channel in extra_channels:
        if channel not in settings.SACRED_CHANNELS:
            settings.SACRED_CHANNELS.append(channel)
