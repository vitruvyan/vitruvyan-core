"""
Vault Keepers — Bus Adapter

Bridges infrastructure events (StreamBus, HTTP) to vault operations.

This adapter orchestrates vault operations (backup, restore, integrity checks)
by delegating to the persistence adapter and emitting result events.

"Il Conclave non pensa; trasmette. L'intelligenza è nei consumer."

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_envelope import CognitiveEvent

from api_vault_keepers.config import settings
from api_vault_keepers.adapters.persistence import PersistenceAdapter
from core.governance.vault_keepers.events.vault_events import (
    CHANNEL_ARCHIVE_COMPLETED,
    CHANNEL_RESTORE_COMPLETED,
    CHANNEL_SNAPSHOT_CREATED,
    CHANNEL_INTEGRITY_VALIDATED,
    CHANNEL_BACKUP_COMPLETED,
)

logger = logging.getLogger("VaultKeepers.BusAdapter")


class VaultBusAdapter:
    """
    Bridges HTTP/Streams to vault operations.
    
    Instantiate once at service startup. Thread-safe (StreamBus is thread-safe).
    
    Usage:
        adapter = VaultBusAdapter()
        result = adapter.handle_integrity_check(event_dict)
    """
    
    def __init__(self):
        self.bus = StreamBus(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        self.persistence = PersistenceAdapter()
        logger.info("Vault Bus Adapter initialized")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Event Handlers (called by routes or streams_listener)
    # ═══════════════════════════════════════════════════════════════════════
    
    def handle_integrity_check(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle integrity check request.
        
        Args:
            event: Event dict with correlation_id, priority, etc.
            
        Returns:
            Dict with integrity validation results
        """
        correlation_id = event.get('correlation_id', f"integrity_{int(datetime.utcnow().timestamp())}")
        logger.info(f"Integrity check requested", extra={"correlation_id": correlation_id})
        
        # Validate PostgreSQL
        pg_result = self.persistence.validate_postgresql_integrity()
        
        # Validate Qdrant
        qdrant_result = self.persistence.validate_qdrant_integrity()
        
        # Validate coherence
        coherence_result = self.persistence.validate_coherence()
        
        # Determine overall status
        overall_status = self._determine_integrity_status(pg_result, qdrant_result, coherence_result)
        
        result = {
            "integrity_status": overall_status,
            "postgresql": pg_result,
            "qdrant": qdrant_result,
            "coherence": coherence_result,
            "warden_blessing": "integrity_verified" if overall_status == "sacred" else "integrity_concern",
            "sacred_timestamp": datetime.utcnow().isoformat(),
        }
        
        # Emit result event
        self._emit_event(CHANNEL_INTEGRITY_VALIDATED, result, correlation_id)
        
        logger.info(f"Integrity check completed", extra={
            "correlation_id": correlation_id,
            "status": overall_status
        })
        
        return result
    
    def handle_backup(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle backup creation request.
        
        Args:
            event: Event dict with mode, priority, include_vectors, etc.
            
        Returns:
            Dict with backup operation results
        """
        correlation_id = event.get('correlation_id', f"backup_{int(datetime.utcnow().timestamp())}")
        include_vectors = event.get('include_vectors', True)
        
        logger.info(f"Backup requested", extra={
            "correlation_id": correlation_id,
            "include_vectors": include_vectors
        })
        
        # Backup PostgreSQL
        pg_backup_result = self.persistence.backup_postgresql()
        
        # Backup Qdrant (if requested)
        qdrant_backup_result = None
        if include_vectors:
            qdrant_backup_result = self.persistence.backup_qdrant()
        
        snapshot_id = f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        result = {
            "success": pg_backup_result.get("status") == "success",
            "snapshot_id": snapshot_id,
            "postgresql_backup": pg_backup_result,
            "qdrant_backup": qdrant_backup_result,
            "sacred_timestamp": datetime.utcnow().isoformat(),
        }
        
        # Emit result event
        self._emit_event(CHANNEL_BACKUP_COMPLETED, result, correlation_id)
        
        logger.info(f"Backup completed", extra={
            "correlation_id": correlation_id,
            "snapshot_id": snapshot_id,
            "success": result["success"]
        })
        
        return result
    
    def handle_restore(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle data restoration request.
        
        Args:
            event: Event dict with snapshot_id, target, dry_run, etc.
            
        Returns:
            Dict with restoration operation results
        """
        correlation_id = event.get('correlation_id', f"restore_{int(datetime.utcnow().timestamp())}")
        snapshot_id = event.get('snapshot_id', 'unknown')
        dry_run = event.get('dry_run', True)
        
        logger.info(f"Restore requested", extra={
            "correlation_id": correlation_id,
            "snapshot_id": snapshot_id,
            "dry_run": dry_run
        })
        
        # Placeholder: Real restore logic would be implemented here
        # This would integrate with existing keeper.py or sentinel.py if available
        
        result = {
            "success": False,
            "message": "Restore operation not yet implemented (placeholder)",
            "snapshot_id": snapshot_id,
            "dry_run": dry_run,
            "sacred_timestamp": datetime.utcnow().isoformat(),
        }
        
        # Emit result event
        self._emit_event(CHANNEL_RESTORE_COMPLETED, result, correlation_id)
        
        logger.warning(f"Restore placeholder executed", extra={
            "correlation_id": correlation_id,
            "snapshot_id": snapshot_id
        })
        
        return result
    
    def handle_archive(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle archival request (from other orders).
        
        Args:
            event: Event dict with content_type, source_order, payload, etc.
            
        Returns:
            Dict with archive operation results
        """
        correlation_id = event.get('correlation_id', f"archive_{int(datetime.utcnow().timestamp())}")
        content_type = event.get('content_type', 'generic')
        source_order = event.get('source_order', 'unknown')
        
        logger.info(f"Archive requested", extra={
            "correlation_id": correlation_id,
            "content_type": content_type,
            "source_order": source_order
        })
        
        # Placeholder: Real archive logic would be implemented here
        # This would integrate with existing archivist.py or chamberlain.py
        
        archive_id = f"archive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        result = {
            "success": True,
            "archive_id": archive_id,
            "content_type": content_type,
            "source_order": source_order,
            "message": "Archive placeholder (integrate with archivist.py)",
            "sacred_timestamp": datetime.utcnow().isoformat(),
        }
        
        # Emit result event
        self._emit_event(CHANNEL_ARCHIVE_COMPLETED, result, correlation_id)
        
        logger.info(f"Archive placeholder executed", extra={
            "correlation_id": correlation_id,
            "archive_id": archive_id
        })
        
        return result
    
    def get_vault_status(self) -> Dict[str, Any]:
        """
        Get comprehensive vault status.
        
        Returns:
            Dict with overall vault health and component statuses
        """
        # Quick health check
        health = self.persistence.health_check()
        
        # Get integrity snapshot
        integrity_result = self.handle_integrity_check({"correlation_id": "status_check"})
        
        return {
            "vault_status": "blessed" if all(health.values()) else "requires_attention",
            "integrity_status": integrity_result,
            "sacred_roles": {
                "vault_guardian": "divine_oversight_active",
                "integrity_warden": "validation_ready",
                "archive_keeper": "backup_ready",
                "recovery_specialist": "recovery_ready",
                "audit_tracker": "chronicles_maintained",
            },
            "synaptic_conclave": "connected" if self.bus else "disconnected",
            "sacred_timestamp": datetime.utcnow().isoformat(),
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    def _determine_integrity_status(
        self, pg_result: Dict, qdrant_result: Dict, coherence_result: Dict
    ) -> str:
        """Determine overall integrity status from component results"""
        pg_status = pg_result.get("status")
        qdrant_status = qdrant_result.get("status")
        coherence_status = coherence_result.get("status")
        
        if all(s in ["healthy", "coherent"] for s in [pg_status, qdrant_status, coherence_status]):
            return "sacred"
        elif any(s == "error" for s in [pg_status, qdrant_status, coherence_status]):
            return "corruption_detected"
        else:
            return "blessed_with_concerns"
    
    def _emit_event(self, channel: str, payload: Dict[str, Any], correlation_id: str) -> None:
        """Emit event to Synaptic Conclave"""
        try:
            event_id = self.bus.emit(
                channel=channel,
                payload=payload,
                emitter="vault_keepers.api"
            )
            logger.debug(f"Event emitted", extra={
                "channel": channel,
                "event_id": event_id,
                "correlation_id": correlation_id
            })
        except Exception as e:
            logger.error(f"Failed to emit event", extra={
                "channel": channel,
                "correlation_id": correlation_id,
                "error": str(e)
            })
