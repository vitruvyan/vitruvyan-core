"""
Finance Domain — VPAR Providers
================================

Domain-specific provider implementations for:
- VEE (Explainability) → FinanceExplainabilityProvider
- VARE (Risk) → FinanceRiskProvider
- VWRE (Attribution) → FinanceAggregationProvider

These inject finance semantics into the domain-agnostic VPAR engines.
"""

from .explainability_provider import FinanceExplainabilityProvider
from .risk_provider import FinanceRiskProvider
from .aggregation_provider import FinanceAggregationProvider

__all__ = [
    "FinanceExplainabilityProvider",
    "FinanceRiskProvider",
    "FinanceAggregationProvider",
]
