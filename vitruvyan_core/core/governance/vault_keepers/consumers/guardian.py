"""
Vault Keepers — Guardian Consumer

The Guardian orchestrates vault operations and coordinates responses.
Pure logic: given an event, determines which vault roles to invoke and in what order.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (consumers)
"""

from typing import Any, Dict, List
from datetime import datetime

from ..consumers.base import VaultRole


class Guardian(VaultRole):
    """
    The Guardian: Vault Operations Orchestrator
    
    Coordinates vault operations by determining which roles to invoke.
    Does NOT execute operations — provides orchestration plan for service layer.
    
    Input (dict):
        {
            "event_type": str,  # e.g., "integrity.check.requested"
            "priority": "low|normal|high|critical",
            "scope": str,
            "correlation_id": str
        }
    
    Output:
        Dict with orchestration plan:
        {
            "roles_to_invoke": ["sentinel", "archivist", ...],
            "sequence": "parallel|sequential",
            "priority_level": str,
            "requires_approval": bool
        }
    """
    
    @property
    def role_name(self) -> str:
        return "guardian"
    
    @property
    def description(self) -> str:
        return "Orchestrates vault operations and coordinates responses"
    
    def can_handle(self, event: Any) -> bool:
        """Handles all vault coordination events"""
        if isinstance(event, dict):
            return "event_type" in event or "operation" in event
        return False
    
    def process(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure orchestration logic.
        
        Args:
            event: Vault operation request
            
        Returns:
            Orchestration plan with roles to invoke
        """
        event_type = event.get("event_type", "")
        operation = event.get("operation", "")
        priority = event.get("priority", "normal")
        correlation_id = event.get("correlation_id", "unknown")
        
        # Determine operation from event type or explicit operation
        if "integrity" in event_type or operation == "integrity_check":
            return self._plan_integrity_check(event, priority, correlation_id)
        elif "backup" in event_type or operation == "backup":
            return self._plan_backup(event, priority, correlation_id)
        elif "restore" in event_type or operation == "restore":
            return self._plan_restore(event, priority, correlation_id)
        elif "archive" in event_type or operation == "archive":
            return self._plan_archive(event, priority, correlation_id)
        else:
            return self._plan_generic(event, priority, correlation_id)
    
    def _plan_integrity_check(self, event: Dict, priority: str, correlation_id: str) -> Dict:
        """Plan integrity validation workflow"""
        return {
            "operation": "integrity_check",
            "roles_to_invoke": ["sentinel"],
            "sequence": "single",
            "priority_level": priority,
            "requires_approval": False,
            "estimated_duration_seconds": 10,
            "correlation_id": correlation_id,
            "guardian_decision": "integrity_check_approved",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _plan_backup(self, event: Dict, priority: str, correlation_id: str) -> Dict:
        """Plan backup workflow"""
        mode = event.get("mode", "full")
        
        # Determine if integrity check needed first
        check_first = priority in ["high", "critical"]
        
        roles = []
        if check_first:
            roles.append("sentinel")
        roles.append("archivist")
        roles.append("chamberlain")  # For audit trail
        
        return {
            "operation": "backup",
            "roles_to_invoke": roles,
            "sequence": "sequential" if check_first else "parallel",
            "priority_level": priority,
            "requires_approval": priority == "critical",
            "estimated_duration_seconds": 60 if mode == "full" else 30,
            "correlation_id": correlation_id,
            "guardian_decision": "backup_approved" if priority != "critical" else "backup_requires_approval",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _plan_restore(self, event: Dict, priority: str, correlation_id: str) -> Dict:
        """Plan restore workflow"""
        dry_run = event.get("dry_run", True)
        
        return {
            "operation": "restore",
            "roles_to_invoke": ["sentinel", "chamberlain"],  # Validate before restore
            "sequence": "sequential",
            "priority_level": priority,
            "requires_approval": not dry_run,  # Always require approval for real restore
            "estimated_duration_seconds": 120 if not dry_run else 30,
            "correlation_id": correlation_id,
            "guardian_decision": "restore_test_approved" if dry_run else "restore_requires_approval",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _plan_archive(self, event: Dict, priority: str, correlation_id: str) -> Dict:
        """Plan archival workflow"""
        return {
            "operation": "archive",
            "roles_to_invoke": ["archivist", "chamberlain"],
            "sequence": "sequential",
            "priority_level": priority,
            "requires_approval": False,
            "estimated_duration_seconds": 5,
            "correlation_id": correlation_id,
            "guardian_decision": "archive_approved",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _plan_generic(self, event: Dict, priority: str, correlation_id: str) -> Dict:
        """Plan generic vault operation"""
        return {
            "operation": "generic",
            "roles_to_invoke": ["sentinel"],  # Default: check integrity
            "sequence": "single",
            "priority_level": priority,
            "requires_approval": False,
            "estimated_duration_seconds": 10,
            "correlation_id": correlation_id,
            "guardian_decision": "generic_operation_approved",
            "timestamp": datetime.utcnow().isoformat()
        }
