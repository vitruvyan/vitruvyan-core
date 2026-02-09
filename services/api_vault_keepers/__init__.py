"""
Vault Keepers — Service Package

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)

FastAPI service for Vault Keepers sacred memory operations.

Port: 8007
Sacred Order: Truth/Governance (Order V)

Endpoints:
----------
- POST /vault/backup: Trigger manual backup
- POST /vault/restore: Restore from backup
- GET /vault/status: Vault health and statistics
- POST /vault/integrity_check: Verify integrity
- GET /health: Health check
- GET /metrics: Prometheus metrics

Dependencies:
-------------
- vitruvyan_core.core.governance.vault_keepers: Core domain logic (LIVELLO 1)
- core.agents: PostgresAgent, QdrantAgent
- core.synaptic_conclave: StreamBus

Refactored: Feb 9, 2026 — SERVICE_PATTERN alignment
Version: 2.0.0
"""

__version__ = '2.0.0'
__port__ = 8007
__sacred_order__ = 'Truth/Governance (Order V)'
