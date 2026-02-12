"""
VPAR — Vitruvyan Proprietary Algorithms Repository

Domain-agnostic epistemic engines. Each sub-package is a self-contained
algorithm with its own engine, analyzer, and memory adapter.

Location: vitruvyan_core/core/vpar/ (same level as agents/, governance/, orchestration/)

Active modules:
    - VEE:  Vitruvyan Explainability Engine (narrative generation)
    - VSGS: Vitruvyan Semantic Grounding System (semantic context enrichment)

Pending migration (from mercator VPS):
    - VWRE: Vitruvyan Weighted Reverse Engineering
    - VARE: Vitruvyan Adaptive Risk Engine
    - VMFL: Vitruvyan Memory Feedback Loop
    - VHSW: Vitruvyan Human Sentiment Weighting

Archived:
    - _legacy/orchestrator.py: Pre-refactoring composite scorer (broken imports)
    - _legacy/algorithm_memory_adapter.py: Orphaned persistence adapter
"""

__all__ = []

__version__ = "3.0.0"  # Restructured: moved to core/vpar/, VSGS added, VWRE/VARE/VMFL/VHSW migrated
__author__ = "Vitruvyan AI Team"