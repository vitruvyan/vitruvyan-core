"""
Finance Vertical - Babel Gardens Integration
============================================

Domain-specific signal extraction, sector resolution, and fusion configuration
for the finance vertical.

Loaded when BABEL_DOMAIN=finance.
"""

from .financial_context import FinancialContextDetector
from .sector_resolver import SectorResolver
from .sentiment_config import (
    FinanceSentimentConfig,
    get_finance_fusion_weights,
    get_finance_model_boost,
)

__all__ = [
    "FinanceSentimentConfig",
    "get_finance_fusion_weights",
    "get_finance_model_boost",
    "FinancialContextDetector",
    "SectorResolver",
]
