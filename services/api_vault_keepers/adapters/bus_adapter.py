"""
Vault Keepers — Bus Adapter (LIVELLO 2)

Bridges HTTP/Streams to vault operations.
This is the ONLY file that touches the StreamBus.

Architecture:
  - Receives events from bus or HTTP
  - Delegates to pure domain consumers (LIVELLO 1)
  - Calls PersistenceAdapter for I/O
  - Emits result events back to bus

"Il Conclave non pensa; trasmette. L'intelligenza è nei consumer."

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.synaptic_conclave.transport.streams import StreamBus
from core.governance.vault_keepers.consumers import Guardian, Sentinel, Archivist, Chamberlain
from api_vault_keepers.config import settings
from api_vault_keepers.adapters.persistence import PersistenceAdapter

logger = logging.getLogger("VaultKeepers.BusAdapter")


class VaultBusAdapter:
    """
    Bridges HTTP/Streams to vault operations.
    
    Instantiate once at service startup. Thread-safe (StreamBus is thread-safe).
    
    Usage:
        adapter = VaultBusAdapter()
        result = adapter.handle_integrity_check(scope="full")
    """
    
    def __init__(self):
        """Initialize bus connection, persistence adapter, and LIVELLO 1 consumers."""
        self.bus = StreamBus(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        self.persistence = PersistenceAdapter()
        
        # LIVELLO 1 consumers (pure logic, no I/O)
        self.guardian = Guardian()
        self.sentinel = Sentinel()
        self.archivist = Archivist()
        self.chamberlain = Chamberlain()
        
        logger.info("Vault Bus Adapter initialized with all consumers")
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTEGRITY VALIDATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def handle_integrity_check(self, scope: str = "full", correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle integrity validation request.
        
        Workflow:
          1. Gather health data from persistence (I/O boundary)
          2. Delegate judgment to Sentinel consumer (pure logic)
          3. Create audit record via Chamberlain
          4. Emit result event
        
        Args:
            scope: Validation scope ("full", "postgresql", "qdrant")
            correlation_id: Optional correlation ID
            
        Returns:
            Integrity report dict
        """
        correlation_id = correlation_id or f"integrity_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[{correlation_id}] Processing integrity check: scope={scope}")
        
        # Step 1: Gather health data from persistence layer (I/O boundary)
        pg_status = self.persistence.validate_postgresql_integrity()
        qdrant_status = self.persistence.validate_qdrant_integrity()
        coherence = self.persistence.validate_coherence()
        
        # Step 2: Delegate to LIVELLO 1 Sentinel (pure logic)
        sentinel_input = {
            "postgresql": pg_status,
            "qdrant": qdrant_status,
            "coherence": coherence,
            "correlation_id": correlation_id
        }
        
        integrity_report = self.sentinel.process(sentinel_input)
        
        # Step 3: Create audit record via Chamberlain
        audit_input = {
            "operation": "integrity_check",
            "performed_by": "system",
            "resource_type": "vault",
            "resource_id": "global",
            "action": "integrity_validated",
            "status": "completed",
            "correlation_id": correlation_id,
            "metadata": {
                "overall_status": integrity_report.overall_status,
                "scope": scope
            }
        }
        audit_record = self.chamberlain.process(audit_input)
        
        # Step 4: Persist audit record
        self.persistence.store_audit_record(audit_record)
        
        # Step 5: Convert to dict for API response
        report = {
            "correlation_id": correlation_id,
            "timestamp": integrity_report.timestamp,
            "postgresql": integrity_report.postgresql_status,
            "qdrant": integrity_report.qdrant_status,
            "coherence": integrity_report.coherence_status,
            "overall_status": integrity_report.overall_status,
            "findings": list(integrity_report.findings),
            "warden_blessing": integrity_report.warden_blessing
        }
        
        # Step 6: Emit result event
        self._emit_event(
            channel=settings.CHANNEL_INTEGRITY_VALIDATED,
            data=report,
            correlation_id=correlation_id
        )
        
        logger.info(f"[{correlation_id}] Integrity check completed: status={integrity_report.overall_status}")
        return report
    
    # ═══════════════════════════════════════════════════════════════════════
    # BACKUP OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def handle_backup(self, mode: str = "full", include_vectors: bool = True, 
                     correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle backup request.
        
        Workflow:
          1. Get orchestration plan from Guardian
          2. Optionally check integrity first (if Guardian requires)
          3. Create backup plan via Archivist
          4. Execute backup via persistence
          5. Create audit record
          6. Emit result event
        
        Args:
            mode: Backup mode ("full" or "incremental")
            include_vectors: Whether to include Qdrant vectors
            correlation_id: Optional correlation ID
            
        Returns:
            Backup result dict
        """
        correlation_id = correlation_id or f"backup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[{correlation_id}] Processing backup: mode={mode}, vectors={include_vectors}")
        
        # Step 1: Get orchestration plan from Guardian
        guardian_input = {
            "operation": "backup",
            "mode": mode,
            "include_vectors": include_vectors,
            "priority": "normal",
            "correlation_id": correlation_id
        }
        orchestration = self.guardian.process(guardian_input)
        
        # Step 2: Check if integrity validation needed first
        if "sentinel" in orchestration["roles_to_invoke"]:
            logger.info(f"[{correlation_id}] Guardian requires integrity check before backup")
            pg_status = self.persistence.validate_postgresql_integrity()
            qdrant_status = self.persistence.validate_qdrant_integrity()
            
            sentinel_input = {
                "postgresql": pg_status,
                "qdrant": qdrant_status,
                "coherence": {"status": "coherent"},
                "correlation_id": correlation_id
            }
            integrity = self.sentinel.process(sentinel_input)
            
            if integrity.overall_status == "corruption_detected":
                logger.warning(f"[{correlation_id}] Backup aborted: corruption detected")
                return {
                    "correlation_id": correlation_id,
                    "status": "aborted",
                    "reason": "integrity_check_failed",
                    "findings": list(integrity.findings)
                }
        
        # Step 3: Create backup plan via Archivist
        archivist_input = {
            "operation": "backup",
            "mode": mode,
            "include_vectors": include_vectors,
            "correlation_id": correlation_id
        }
        snapshot_plan = self.archivist.process(archivist_input)
        
        # Step 4: Execute backup via persistence layer
        backup_result = self.persistence.execute_backup(
            mode=mode,
            include_vectors=include_vectors,
            snapshot_id=snapshot_plan.snapshot_id
        )
        
        # Step 5: Create audit record
        audit_input = {
            "operation": "backup",
            "performed_by": "system",
            "resource_type": "vault",
            "resource_id": snapshot_plan.snapshot_id,
            "action": "backup_completed",
            "status": backup_result["status"],
            "correlation_id": correlation_id,
            "metadata": {
                "mode": mode,
                "scope": snapshot_plan.scope,
                "size_bytes": backup_result.get("size_bytes", 0)
            }
        }
        audit_record = self.chamberlain.process(audit_input)
        self.persistence.store_audit_record(audit_record)
        
        # Step 6: Build response
        result = {
            "correlation_id": correlation_id,
            "timestamp": snapshot_plan.timestamp,
            "snapshot_id": snapshot_plan.snapshot_id,
            "mode": mode,
            "scope": snapshot_plan.scope,
            "status": backup_result["status"],
            "postgresql_path": backup_result.get("postgresql_path"),
            "qdrant_path": backup_result.get("qdrant_path"),
            "size_bytes": backup_result.get("size_bytes", 0)
        }
        
        # Step 7: Emit event
        self._emit_event(
            channel=settings.CHANNEL_BACKUP_COMPLETED,
            data=result,
            correlation_id=correlation_id
        )
        
        logger.info(f"[{correlation_id}] Backup completed: snapshot_id={snapshot_plan.snapshot_id}")
        return result
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESTORE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def handle_restore(self, snapshot_id: str, dry_run: bool = True,
                      correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle restore request.
        
        Workflow:
          1. Get orchestration plan from Guardian
          2. Validate current integrity via Sentinel
          3. Validate snapshot exists
          4. Execute restore (or test if dry_run)
          5. Create audit record
          6. Emit result event
        
        Args:
            snapshot_id: ID of snapshot to restore
            dry_run: If True, validate only without executing
            correlation_id: Optional correlation ID
            
        Returns:
            Restore result dict
        """
        correlation_id = correlation_id or f"restore_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[{correlation_id}] Processing restore: snapshot_id={snapshot_id}, dry_run={dry_run}")
        
        # Step 1: Get orchestration plan from Guardian
        guardian_input = {
            "operation": "restore",
            "snapshot_id": snapshot_id,
            "dry_run": dry_run,
            "priority": "critical" if not dry_run else "normal",
            "correlation_id": correlation_id
        }
        orchestration = self.guardian.process(guardian_input)
        
        # Step 2: Always validate current integrity first
        pg_status = self.persistence.validate_postgresql_integrity()
        qdrant_status = self.persistence.validate_qdrant_integrity()
        
        sentinel_input = {
            "postgresql": pg_status,
            "qdrant": qdrant_status,
            "coherence": {"status": "coherent"},
            "correlation_id": correlation_id
        }
        pre_restore_integrity = self.sentinel.process(sentinel_input)
        
        # Step 3: Validate snapshot exists
        snapshot_valid = self.persistence.validate_snapshot_exists(snapshot_id)
        if not snapshot_valid:
            logger.error(f"[{correlation_id}] Snapshot not found: {snapshot_id}")
            return {
                "correlation_id": correlation_id,
                "status": "failed",
                "reason": "snapshot_not_found",
                "snapshot_id": snapshot_id
            }
        
        # Step 4: Execute restore (or test if dry_run)
        if dry_run:
            restore_result = self.persistence.test_restore(snapshot_id)
            status = "validated"
        else:
            if orchestration.get("requires_approval"):
                logger.warning(f"[{correlation_id}] Real restore requires explicit approval")
                return {
                    "correlation_id": correlation_id,
                    "status": "requires_approval",
                    "snapshot_id": snapshot_id,
                    "message": "Critical restore operation requires manual approval"
                }
            restore_result = self.persistence.execute_restore(snapshot_id)
            status = restore_result.get("status", "completed")
        
        # Step 5: Create audit record
        audit_input = {
            "operation": "restore",
            "performed_by": "system",
            "resource_type": "vault",
            "resource_id": snapshot_id,
            "action": "restore_tested" if dry_run else "restore_executed",
            "status": status,
            "correlation_id": correlation_id,
            "metadata": {
                "dry_run": str(dry_run),
                "pre_restore_integrity": pre_restore_integrity.overall_status
            }
        }
        audit_record = self.chamberlain.process(audit_input)
        self.persistence.store_audit_record(audit_record)
        
        # Step 6: Build response
        result = {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "snapshot_id": snapshot_id,
            "dry_run": dry_run,
            "status": status,
            "pre_restore_integrity": pre_restore_integrity.overall_status,
            "details": restore_result
        }
        
        # Step 7: Emit event
        self._emit_event(
            channel=settings.CHANNEL_RESTORE_COMPLETED,
            data=result,
            correlation_id=correlation_id
        )
        
        logger.info(f"[{correlation_id}] Restore {'tested' if dry_run else 'executed'}: status={status}")
        return result
    
    # ═══════════════════════════════════════════════════════════════════════
    # ARCHIVE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def handle_archive(self, content: Dict[str, Any], content_type: str = "generic",
                      source_order: str = "unknown", correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle archive storage request.
        
        Workflow:
          1. Create archive plan via Archivist
          2. Store archive via persistence
          3. Create audit record
          4. Emit result event
        
        Args:
            content: Content to archive
            content_type: Type of content
            source_order: Which Sacred Order generated this
            correlation_id: Optional correlation ID
            
        Returns:
            Archive result dict
        """
        correlation_id = correlation_id or f"archive_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[{correlation_id}] Processing archive: type={content_type}, source={source_order}")
        
        # Step 1: Create archive plan via Archivist
        archivist_input = {
            "operation": "archive",
            "content_type": content_type,
            "source_order": source_order,
            "payload": content,
            "correlation_id": correlation_id
        }
        archive_metadata = self.archivist.process(archivist_input)
        
        # Step 2: Store archive via persistence layer
        storage_result = self.persistence.store_archive(
            archive_id=archive_metadata.archive_id,
            content=content,
            metadata=archive_metadata
        )
        
        # Step 3: Create audit record
        audit_input = {
            "operation": "archive",
            "performed_by": source_order,
            "resource_type": "archive",
            "resource_id": archive_metadata.archive_id,
            "action": "content_archived",
            "status": storage_result["status"],
            "correlation_id": correlation_id,
            "metadata": {
                "content_type": content_type,
                "retention_until": archive_metadata.retention_until
            }
        }
        audit_record = self.chamberlain.process(audit_input)
        self.persistence.store_audit_record(audit_record)
        
        # Step 4: Build response
        result = {
            "correlation_id": correlation_id,
            "timestamp": archive_metadata.timestamp,
            "archive_id": archive_metadata.archive_id,
            "content_type": content_type,
            "source_order": source_order,
            "storage_path": archive_metadata.storage_path,
            "retention_until": archive_metadata.retention_until,
            "status": storage_result["status"],
            "size_bytes": storage_result.get("size_bytes", 0)
        }
        
        # Step 5: Emit event
        self._emit_event(
            channel=settings.CHANNEL_ARCHIVE_STORED,
            data=result,
            correlation_id=correlation_id
        )
        
        logger.info(f"[{correlation_id}] Archive stored: archive_id={archive_metadata.archive_id}")
        return result
    
    # ═══════════════════════════════════════════════════════════════════════
    # EVENT EMISSION
    # ═══════════════════════════════════════════════════════════════════════
    
    def _emit_event(self, channel: str, data: Dict[str, Any], correlation_id: str):
        """
        Emit event to StreamBus.
        
        Args:
            channel: Channel name (without vitruvyan: prefix)
            data: Event payload
            correlation_id: Correlation identifier
        """
        try:
            event_id = self.bus.emit(
                channel=channel,
                payload=data,
                emitter="vault_keepers.api",
                correlation_id=correlation_id
            )
            logger.debug(f"[{correlation_id}] Event emitted: {channel} -> {event_id}")
        except Exception as e:
            logger.error(f"[{correlation_id}] Failed to emit event to {channel}: {e}")
