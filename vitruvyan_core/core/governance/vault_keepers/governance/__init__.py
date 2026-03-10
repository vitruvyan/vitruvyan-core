"""
Vault Keepers — Governance Package

Business rules and workflow coordination for vault operations.
All logic is pure: no I/O, no infrastructure.

Available modules:
  - rules:     Retention policies, integrity thresholds, backup priorities
  - workflows: Consumer orchestration patterns

Usage:
    from core.governance.vault_keepers.governance import (
        VaultRules, VaultWorkflows
    )
    
    priority = VaultRules.calculate_backup_priority(24.5, 0.7)
    steps = VaultWorkflows.backup_workflow(priority)
"""

from .rules import VaultRules
from .workflows import VaultWorkflows, WorkflowStep

__all__ = [
    "VaultRules",
    "VaultWorkflows",
    "WorkflowStep",
]
