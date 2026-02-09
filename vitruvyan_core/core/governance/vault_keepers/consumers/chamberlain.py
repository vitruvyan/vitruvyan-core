"""
Vault Keepers — Chamberlain Consumer

The Chamberlain tracks audit trails and maintains records.
Pure logic: given an operation, creates audit records for compliance.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (consumers)
"""

from typing import Any, Dict
from datetime import datetime

from ..consumers.base import VaultRole
from ..domain.vault_objects import AuditRecord


class Chamberlain(VaultRole):
    """
    The Chamberlain: Audit Trail & Record Keeper
    
    Creates immutable audit records for vault operations.
    Does NOT write to databases — generates records for service layer to persist.
    
    Input (dict):
        {
            "operation": str,
            "performed_by": str,
            "resource_type": str,
            "resource_id": str,
            "action": str,
            "status": "initiated|completed|failed",
            "correlation_id": str,
            "metadata": dict (optional)
        }
    
    Output:
        AuditRecord with operation details
    """
    
    @property
    def role_name(self) -> str:
        return "chamberlain"
    
    @property
    def description(self) -> str:
        return "Tracks audit trails and maintains records"
    
    def can_handle(self, event: Any) -> bool:
        """Handles all events that need audit trail"""
        if isinstance(event, dict):
            # Audit any event with operation or action
            return "operation" in event or "action" in event
        return False
    
    def process(self, event: Dict[str, Any]) -> AuditRecord:
        """
        Pure audit record creation logic.
        
        Args:
            event: Operation to audit
            
        Returns:
            AuditRecord with immutable trail
        """
        operation = event.get("operation", event.get("action", "unknown"))
        performed_by = event.get("performed_by", "system")
        resource_type = event.get("resource_type", "vault")
        resource_id = event.get("resource_id", "unknown")
        action = event.get("action", operation)
        status = event.get("status", "completed")
        correlation_id = event.get("correlation_id", "unknown")
        
        # Generate record ID
        record_id = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Collect metadata
        metadata_dict = event.get("metadata", {})
        metadata_tuples = tuple((k, str(v)) for k, v in metadata_dict.items())
        
        # Add standard metadata
        standard_metadata = (
            ("warden", "vault_keepers"),
            ("priority", event.get("priority", "normal")),
            ("scope", event.get("scope", "system")),
        )
        
        all_metadata = standard_metadata + metadata_tuples
        
        # Create audit record
        return AuditRecord(
            record_id=record_id,
            timestamp=datetime.utcnow().isoformat(),
            operation=operation,
            performed_by=performed_by,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            correlation_id=correlation_id,
            metadata=all_metadata
        )
