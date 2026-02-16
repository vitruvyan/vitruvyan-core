"""
Vault Keepers — LIVELLO 1 Package

Sacred Order: Truth (Memory & Archival)
Layer: Foundational

Pure domain logic for vault operations: backup, restore, integrity validation.

Refactored: Feb 9, 2026 — SACRED_ORDER_PATTERN alignment

Modules:
  - domain/      Immutable domain objects (@dataclass(frozen=True))
  - consumers/   Pure process() roles (SacredRole ABC) [TO BE IMPLEMENTED]
  - governance/  Rules, retention policies [TO BE IMPLEMENTED]
  - events/      Sacred channel names and event envelopes
  - monitoring/  Metric name constants [TO BE IMPLEMENTED]
"""
__version__ = "2.0.0"
__sacred_order__ = "Truth/Governance (Order V)"

# Export new LIVELLO 1 modules when ready
# from .domain import VaultSnapshot, IntegrityReport, ArchiveMetadata, RecoveryPlan, AuditRecord
# from .events import CHANNEL_ARCHIVE_COMPLETED, CHANNEL_BACKUP_COMPLETED, etc.
