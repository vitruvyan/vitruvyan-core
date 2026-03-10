"""
Vault Keepers — Consumers Package

Pure decision engines for vault operations.
All consumers follow the VaultRole pattern: no I/O, no side effects.

Available consumers:
  - Guardian:    Orchestrates vault workflows
  - Sentinel:    Validates data integrity
  - Archivist:   Plans backup/archive operations
  - Chamberlain: Creates audit records
  - SignalArchivist: Plans signal timeseries archival (Babel Gardens v2.1)

Usage:
    from core.governance.vault_keepers.consumers import (
        Guardian, Sentinel, Archivist, Chamberlain, SignalArchivist
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
from .signal_archivist import SignalArchivist, archive_signal_timeseries

__all__ = [
    "VaultRole",
    "Guardian",
    "Sentinel",
    "Archivist",
    "Chamberlain",
    
    # Signal archival (Babel Gardens v2.1 integration)
    "SignalArchivist",
    "archive_signal_timeseries",
]
