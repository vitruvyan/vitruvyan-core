"""
VARE — Vitruvyan Adaptive Risk Engine v2.0

Domain-agnostic multi-dimensional risk profiling.
Delegates domain-specific logic to RiskProvider contract.

Components:
    - types.py:        RiskConfig, RiskDimensionScore, RiskResult (frozen dataclasses)
    - vare_engine.py:  VAREEngine — provider-driven risk assessment
    - _legacy_vare_engine.py: Pre-refactoring finance-coupled version (archived)

Contract: vitruvyan_core/domains/risk_contract.py (RiskProvider)

Architecture:
    LIVELLO 1 (Pure domain): This module — zero I/O, zero yfinance
    LIVELLO 2 (Adapter):     LangGraph node or service-level integration
"""

from .types import RiskConfig, RiskDimensionScore, RiskResult
from .vare_engine import VAREEngine

__all__ = ["VAREEngine", "RiskConfig", "RiskDimensionScore", "RiskResult"]

__version__ = "2.0.0"
__author__ = "Vitruvyan AI Team"

