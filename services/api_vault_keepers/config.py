"""
Vault Keepers — Service Configuration

All environment variables centralized in one place.
No scattered os.getenv() calls across modules.

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)
"""
import os


class Settings:
    """Vault Keepers service configuration"""
    
    # Service identity
    SERVICE_NAME = "api_vault_keepers"
    SERVICE_VERSION = "2.0.0"
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8007"))
    SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Redis / Cognitive Bus
    REDIS_HOST = os.getenv("REDIS_HOST", "omni_redis")
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
        "orthodoxy.audit.completed",
        "neural_engine.screening.completed",
    ]
    
    # PostgreSQL (host machine)
    PG_HOST = os.getenv("PG_HOST", "161.97.140.157")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "vitruvyan")
    PG_USER = os.getenv("PG_USER", "vitruvyan_user")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "")
    
    # Qdrant (vector database)
    QDRANT_HOST = os.getenv("QDRANT_HOST", "161.97.140.157")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "phrases")
    
    # Backup & Archive settings
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    ARCHIVE_ENABLED = os.getenv("ARCHIVE_ENABLED", "true").lower() == "true"
    SNAPSHOT_INTERVAL_HOURS = int(os.getenv("SNAPSHOT_INTERVAL_HOURS", "24"))
    
    # Integrity check thresholds
    INTEGRITY_WARNING_THRESHOLD = float(os.getenv("INTEGRITY_WARNING_THRESHOLD", "0.9"))
    INTEGRITY_CRITICAL_THRESHOLD = float(os.getenv("INTEGRITY_CRITICAL_THRESHOLD", "0.7"))
    
    # Google Drive (for archive, if configured)
    GDRIVE_ENABLED = os.getenv("GDRIVE_ENABLED", "false").lower() == "true"
    GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")
    
    # Event channels (emitting, not listening)
    CHANNEL_INTEGRITY_VALIDATED = "vault.integrity.validated"
    CHANNEL_BACKUP_COMPLETED = "vault.backup.completed"
    CHANNEL_RESTORE_COMPLETED = "vault.restore.completed"
    CHANNEL_ARCHIVE_STORED = "vault.archive.stored"
    CHANNEL_SNAPSHOT_CREATED = "vault.snapshot.created"


settings = Settings()
