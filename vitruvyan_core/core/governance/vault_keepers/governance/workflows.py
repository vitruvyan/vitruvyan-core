"""
Vault Keepers — Governance Workflows

Pure workflow coordination logic.
Defines how consumers are orchestrated for different vault operations.

No I/O, no infrastructure, fully testable.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

from ..consumers import Guardian, Sentinel, Archivist, Chamberlain
from ..governance.rules import VaultRules


@dataclass(frozen=True)
class WorkflowStep:
    """A single step in a vault workflow"""
    consumer_name: str
    input_mapping: Dict[str, Any]
    required: bool = True


class VaultWorkflows:
    """
    Sacred workflows for vault operations.
    Defines consumer orchestration patterns.
    """
    
    @staticmethod
    def integrity_check_workflow() -> List[WorkflowStep]:
        """
        Workflow for integrity validation.
        
        Returns:
            List of workflow steps
        """
        return [
            WorkflowStep(
                consumer_name="sentinel",
                input_mapping={"operation": "integrity_check"},
                required=True
            ),
            WorkflowStep(
                consumer_name="chamberlain",
                input_mapping={"action": "integrity_check_audited"},
                required=True
            )
        ]
    
    @staticmethod
    def backup_workflow(priority: str = "normal") -> List[WorkflowStep]:
        """
        Workflow for backup operations.
        
        Args:
            priority: Backup priority level
            
        Returns:
            List of workflow steps
        """
        steps = []
        
        # High priority backups check integrity first
        if VaultRules.requires_integrity_check_before_backup(priority):
            steps.append(WorkflowStep(
                consumer_name="sentinel",
                input_mapping={"operation": "integrity_check"},
                required=True
            ))
        
        # Plan the backup
        steps.append(WorkflowStep(
            consumer_name="archivist",
            input_mapping={"operation": "backup"},
            required=True
        ))
        
        # Audit the backup
        steps.append(WorkflowStep(
            consumer_name="chamberlain",
            input_mapping={"action": "backup_executed"},
            required=True
        ))
        
        return steps
    
    @staticmethod
    def restore_workflow(dry_run: bool = True) -> List[WorkflowStep]:
        """
        Workflow for restore operations.
        
        Args:
            dry_run: If True, only validate without executing
            
        Returns:
            List of workflow steps
        """
        steps = [
            # Always validate current integrity first
            WorkflowStep(
                consumer_name="sentinel",
                input_mapping={"operation": "integrity_check"},
                required=True
            ),
        ]
        
        # Real restores require Guardian approval
        if not dry_run:
            steps.append(WorkflowStep(
                consumer_name="guardian",
                input_mapping={"operation": "restore", "approve": True},
                required=True
            ))
        
        # Audit the restore
        steps.append(WorkflowStep(
            consumer_name="chamberlain",
            input_mapping={"action": "restore_executed" if not dry_run else "restore_tested"},
            required=True
        ))
        
        return steps
    
    @staticmethod
    def archive_workflow() -> List[WorkflowStep]:
        """
        Workflow for archival operations.
        
        Returns:
            List of workflow steps
        """
        return [
            WorkflowStep(
                consumer_name="archivist",
                input_mapping={"operation": "archive"},
                required=True
            ),
            WorkflowStep(
                consumer_name="chamberlain",
                input_mapping={"action": "archive_stored"},
                required=True
            )
        ]
    
    @staticmethod
    def emergency_recovery_workflow() -> List[WorkflowStep]:
        """
        Workflow for emergency recovery (high priority).
        
        Returns:
            List of workflow steps
        """
        return [
            # Guardian orchestrates emergency response
            WorkflowStep(
                consumer_name="guardian",
                input_mapping={"operation": "emergency_recovery", "priority": "critical"},
                required=True
            ),
            # Validate current state
            WorkflowStep(
                consumer_name="sentinel",
                input_mapping={"operation": "integrity_check"},
                required=True
            ),
            # Plan recovery
            WorkflowStep(
                consumer_name="archivist",
                input_mapping={"operation": "restore", "mode": "full"},
                required=True
            ),
            # Audit emergency action
            WorkflowStep(
                consumer_name="chamberlain",
                input_mapping={"action": "emergency_recovery_executed", "priority": "critical"},
                required=True
            )
        ]
