"""
VPAR — Vitruvyan Proprietary Algorithms Repository

Domain-agnostic epistemic engines. Each sub-package is a self-contained
algorithm with its own engine, analyzer, and memory adapter.

Location: vitruvyan_core/core/vpar/ (same level as agents/, governance/, orchestration/)

Active modules:
    - VEE:  Vitruvyan Explainability Engine v3.0 (narrative generation)
    - VSGS: Vitruvyan Semantic Grounding System v2.0 (semantic context enrichment)
    - VARE: Vitruvyan Adaptive Risk Engine v2.0 (multi-dimensional risk profiling)
    - VWRE: Vitruvyan Weighted Reverse Engineering v2.0 (attribution analysis)

Deprecated (archived to _legacy/):
    - VMFL: Absorbed by VWRE + vertical AggregationProviders
    - VHSW: Trivial windowed statistics, not a proprietary algorithm

Archived:
    - _legacy/orchestrator.py: Pre-refactoring composite scorer
    - _legacy/algorithm_memory_adapter.py: Orphaned persistence adapter
    - _legacy/vmfl/: Finance-specific multi-factor scoring (deprecated)
    - _legacy/vhsw/: Historical sliding window (deprecated)
"""

__all__ = []

__version__ = "4.0.0"  # VARE+VWRE refactored, VMFL+VHSW deprecated
__author__ = "Vitruvyan AI Team"