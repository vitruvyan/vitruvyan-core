"""
Vault Keepers — Consumers Package

Pure decision engines for vault operations.
All consumers follow the VaultRole pattern: no I/O, no side effects.

Available consumers:
  - Guardian:    Orchestrates vault workflows
  - Sentinel:    Validates data integrity
  - Archivist:   Plans backup/archive operations
  - Chamberlain: Creates audit records

Usage:
    from vitruvyan_core.core.governance.vault_keepers.consumers import (
        Guardian, Sentinel, Archivist, Chamberlain
    )
    
    sentinel = Sentinel()
    if sentinel.can_handle(event):
        report = sentinel.process(event)
"""

from .base import VaultRole
from .guardian import Guardian
from .sentinel import Sentinel
from .archivist import Archivist
from .chamberlain import Chamberlain

__all__ = [
    "VaultRole",
    "Guardian",
    "Sentinel",
    "Archivist",
    "Chamberlain",
]
