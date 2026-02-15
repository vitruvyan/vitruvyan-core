"""
Vault Keepers — Event Definitions

Sacred channel names and event envelope constants.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (LIVELLO 1)
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════════════════
# Sacred Channels (Redis Streams)
# ═══════════════════════════════════════════════════════════════════════════

# Inbound channels (events Vault Keepers listens to)
CHANNEL_ARCHIVE_REQUESTED = "vault.archive.requested"
CHANNEL_RESTORE_REQUESTED = "vault.restore.requested"
CHANNEL_SNAPSHOT_REQUESTED = "vault.snapshot.requested"
CHANNEL_INTEGRITY_CHECK_REQUESTED = "integrity.check.requested"
CHANNEL_BACKUP_CREATE_REQUESTED = "backup.create.requested"
CHANNEL_RECOVERY_EXECUTE_REQUESTED = "recovery.execute.requested"
CHANNEL_AUDIT_VAULT_REQUESTED = "audit.vault.requested"

# Inbound from other orders
CHANNEL_ORTHODOXY_AUDIT_COMPLETED = "orthodoxy.audit.completed"
CHANNEL_ENGINE_EVAL_COMPLETED = "engine.eval.completed"  # Was: neural_engine.screening.completed

# Outbound channels (events Vault Keepers emits)
CHANNEL_ARCHIVE_COMPLETED = "vault.archive.completed"
CHANNEL_RESTORE_COMPLETED = "vault.restore.completed"
CHANNEL_SNAPSHOT_CREATED = "vault.snapshot.created"
CHANNEL_INTEGRITY_VALIDATED = "vault.integrity.validated"
CHANNEL_BACKUP_COMPLETED = "vault.backup.completed"
CHANNEL_RECOVERY_COMPLETED = "vault.recovery.completed"


# ═══════════════════════════════════════════════════════════════════════════
# Event Envelope (if needed beyond CognitiveEvent)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class VaultEvent:
    """
    Immutable event envelope for Vault Keepers operations.
    
    Wraps CognitiveEvent with vault-specific context.
    """
    event_type: str
    correlation_id: str
    timestamp: str
    emitter: str
    payload: tuple  # Frozen: tuple of (key, value) pairs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "emitter": self.emitter,
            "payload": dict(self.payload),
        }
