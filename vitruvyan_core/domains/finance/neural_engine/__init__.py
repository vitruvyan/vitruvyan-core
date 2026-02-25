"""
Finance Vertical - Neural Engine Integration
===========================================

Domain-specific implementations for Neural Engine contracts:
- TickerDataProvider (IDataProvider)
- FinancialScoringStrategy (IScoringStrategy)

Loaded when DOMAIN=finance in api_neural_engine.
"""

from .data_provider import TickerDataProvider
from .scoring_strategy import FinancialScoringStrategy
from .filter_strategy import FinancialFilterStrategy

__all__ = [
    "TickerDataProvider",
    "FinancialScoringStrategy",
    "FinancialFilterStrategy",
]
