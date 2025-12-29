# core/algorithms/__init__.py
"""
🧠 Vitruvyan Core Algorithms - Linea Proprietaria

Moduli componibili per analisi finanziaria explainable, safe e composable:

- VEE: Vitruvyan Explainability Engine (già esistente in core/logic/vee_engine.py)
- VHSW: Vitruvyan Historical Strength Window
- VARE: Vitruvyan Adaptive Risk Engine  
- VMFL: Vitruvyan Multi-Factor Learning

Tutti orchestrati tramite LangGraph nodes per massima flessibilità.
"""

from .vhsw_engine import VHSWEngine
from .vare_engine import VAREEngine
from .vmfl_engine import VMFLEngine

__all__ = [
    'VHSWEngine',
    'VAREEngine', 
    'VMFLEngine'
]

__version__ = "1.0.0"
__author__ = "Vitruvyan AI Team"