"""
VWRE — Vitruvyan Weighted Reverse Engineering v2.0

Domain-agnostic attribution analysis.
Decomposes composite scores into weighted factor contributions.

Components:
    - types.py:        AttributionConfig, FactorAttribution, AttributionResult, ComparisonResult
    - vwre_engine.py:  VWREEngine — provider-driven attribution analysis
    - _legacy_vwre_engine.py: Pre-refactoring finance-coupled version (archived)

Contract: vitruvyan_core/domains/aggregation_contract.py (AggregationProvider)

Architecture:
    LIVELLO 1 (Pure domain): This module — zero I/O, zero Neural Engine imports
    LIVELLO 2 (Adapter):     LangGraph node or service-level integration
"""

from .types import AttributionConfig, AttributionResult, ComparisonResult, FactorAttribution
from .vwre_engine import VWREEngine

__all__ = [
    "VWREEngine",
    "AttributionConfig", "AttributionResult",
    "ComparisonResult", "FactorAttribution",
]

__version__ = "2.0.0"
__author__ = "Vitruvyan AI Team"
