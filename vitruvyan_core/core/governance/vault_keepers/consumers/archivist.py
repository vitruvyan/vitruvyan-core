"""
Vault Keepers — Archivist Consumer

The Archivist plans and validates backup/archive operations.
Pure logic: given system state, creates backup plans and validates archives.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (consumers)
"""

from typing import Any, Dict
from datetime import datetime, timedelta

from ..consumers.base import VaultRole
from ..domain.vault_objects import VaultSnapshot, ArchiveMetadata


class Archivist(VaultRole):
    """
    The Archivist: Backup Planner & Archive Validator
    
    Plans backup operations and validates archive integrity.
    Does NOT perform actual backups — creates plans for service layer to execute.
    
    Input (dict):
        For backup:
        {
            "operation": "backup",
            "mode": "full|incremental",
            "include_vectors": bool,
            "correlation_id": str
        }
        
        For archive:
        {
            "operation": "archive",
            "content_type": str,
            "source_order": str,
            "payload": dict,
            "correlation_id": str
        }
    
    Output:
        VaultSnapshot or ArchiveMetadata with plan details
    """
    
    @property
    def role_name(self) -> str:
        return "archivist"
    
    @property
    def description(self) -> str:
        return "Plans backup operations and validates archives"
    
    def can_handle(self, event: Any) -> bool:
        """Handles backup and archive events"""
        if isinstance(event, dict):
            operation = event.get("operation", "")
            return operation in ["backup", "archive"]
        return False
    
    def process(self, event: Dict[str, Any]) -> Any:
        """
        Pure backup/archive planning logic.
        
        Args:
            event: Backup or archive request
            
        Returns:
            VaultSnapshot or ArchiveMetadata with plan
        """
        operation = event.get("operation")
        
        if operation == "backup":
            return self._plan_backup(event)
        elif operation == "archive":
            return self._plan_archive(event)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _plan_backup(self, event: Dict[str, Any]) -> VaultSnapshot:
        """
        Create a backup plan.
        
        Returns:
            VaultSnapshot with backup specifications
        """
        mode = event.get("mode", "full")
        include_vectors = event.get("include_vectors", True)
        correlation_id = event.get("correlation_id", "unknown")
        
        # Generate snapshot ID
        snapshot_id = f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine scope
        if mode == "full" and include_vectors:
            scope = "full"
        elif mode == "full":
            scope = "postgresql"
        elif include_vectors:
            scope = "qdrant"
        else:
            scope = "partial"
        
        # Create plan (sizes are estimates, actual paths set by service layer)
        return VaultSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.utcnow().isoformat(),
            scope=scope,
            postgresql_backup_path=f"/var/vitruvyan/vaults/pg_{snapshot_id}.sql" if mode == "full" else None,
            qdrant_backup_path=f"/var/vitruvyan/vaults/qdrant_{snapshot_id}.tar" if include_vectors else None,
            size_bytes=0,  # Will be set after actual backup
            status="in_progress",
            metadata=(
                ("mode", mode),
                ("include_vectors", str(include_vectors)),
                ("correlation_id", correlation_id),
                ("planned_at", datetime.utcnow().isoformat()),
            )
        )
    
    def _plan_archive(self, event: Dict[str, Any]) -> ArchiveMetadata:
        """
        Create an archive plan.
        
        Returns:
            ArchiveMetadata with archive specifications
        """
        content_type = event.get("content_type", "generic")
        source_order = event.get("source_order", "unknown")
        correlation_id = event.get("correlation_id", "unknown")
        
        # Generate archive ID
        archive_id = f"archive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate retention (30 days default)
        retention_until = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        # Create archive plan
        return ArchiveMetadata(
            archive_id=archive_id,
            timestamp=datetime.utcnow().isoformat(),
            content_type=content_type,
            source_order=source_order,
            correlation_id=correlation_id,
            storage_path=f"/var/vitruvyan/vaults/archives/{archive_id}.json",
            size_bytes=0,  # Will be set after actual archival
            retention_until=retention_until
        )
