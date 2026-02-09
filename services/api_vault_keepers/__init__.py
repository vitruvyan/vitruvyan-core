"""
vitruvyan_os.services.governance.api_vault_keepers
===================================================

FastAPI service for Vault Keepers sacred memory operations.

Port: 8007
Sacred Order: Truth/Governance (Order V)

Endpoints:
----------
- POST /vault/backup: Trigger manual backup
- POST /vault/restore: Restore from backup
- GET /vault/status: Vault health and statistics
- POST /vault/verify: Verify backup integrity
- GET /vault/history: Backup history
- GET /health: Health check
- GET /metrics: Prometheus metrics

The Vault Keepers respond to Cognitive Bus events with divine vigilance,
ensuring preservation and restoration of sacred knowledge.

Metrics:
--------
- vault_backups_total (Counter)
- vault_restore_operations (Counter)
- vault_integrity_checks (Counter)
- vault_backup_duration_seconds (Histogram)
- vault_backup_size_bytes (Histogram)

Dependencies:
-------------
- vitruvyan_os.core.governance.vault_keepers: Core guardian logic
- vitruvyan_os.core.foundation.persistence: PostgresAgent, QdrantAgent
- vitruvyan_os.core.foundation.cognitive_bus: Event handling

Version: 4.4.0
"""

__version__ = '4.4.0'
__port__ = 8007
__sacred_order__ = 'Truth/Governance (Order V)'
