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

Deprecated (removed):
    - VMFL: Absorbed by VWRE + vertical AggregationProviders
    - VHSW: Trivial windowed statistics, not a proprietary algorithm
"""

__all__ = []

__version__ = "4.0.0"  # VARE+VWRE refactored, VMFL+VHSW deprecated
__author__ = "Vitruvyan AI Team"