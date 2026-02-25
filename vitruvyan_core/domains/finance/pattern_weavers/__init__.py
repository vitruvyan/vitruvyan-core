"""
Finance Vertical - Pattern Weavers Integration
==============================================

Domain-specific configuration and helpers for finance ontology weaving.
Loaded when PATTERN_DOMAIN=finance.
"""

from .financial_context import FinancialContextDetector
from .sector_resolver import SectorResolver
from .weave_config import (
    FinanceWeaveConfig,
    get_category_boost,
    get_finance_threshold,
)

__all__ = [
    "FinancialContextDetector",
    "SectorResolver",
    "FinanceWeaveConfig",
    "get_category_boost",
    "get_finance_threshold",
]
