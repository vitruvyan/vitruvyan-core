"""
code_analyzer.py — LIVELLO 1 STUB (re-exports from _legacy/)

CodeAnalyzer performs filesystem I/O (os.walk, subprocess) and therefore
violates LIVELLO 1 purity constraints.  The full implementation lives in
_legacy/code_analyzer.py and is re-exported here for backwards compatibility.

When a LIVELLO 2 adapter is created (services/api_orthodoxy_wardens/adapters/),
this stub should be removed and imports updated to point at the adapter.

Archived: February 2026
"""

from core.governance.orthodoxy_wardens._legacy.code_analyzer import CodeAnalyzer

__all__ = ["CodeAnalyzer"]
