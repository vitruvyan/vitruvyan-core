# core/algorithms/__init__.py
"""
🧠 Vitruvyan Core Algorithms - Linea Proprietaria

Moduli componibili per analisi explainable, safe e composable:

- VEE: Vitruvyan Explainability Engine (domain-agnostic narrative generation)

NOTE (Feb 2026): Domain-specific engines (VHSW, VARE, VMFL) have been 
moved to vitruvyan (finance vertical). Only domain-agnostic VEE remains.
"""

# Domain-agnostic imports only
# VHSWEngine, VAREEngine, VMFLEngine are finance-specific and live in vitruvyan

__all__ = []

__version__ = "2.0.0"  # Breaking change: removed finance-specific engines
__author__ = "Vitruvyan AI Team"