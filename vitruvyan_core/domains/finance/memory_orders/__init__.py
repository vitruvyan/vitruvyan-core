"""
Finance Vertical - Memory Orders Integration
===========================================

Minimal finance-specific configuration for dual-memory governance.
Loaded when MEMORY_DOMAIN=finance.
"""

from .finance_config import (
    FinanceMemoryConfig,
    get_finance_default_sources,
    get_finance_source_candidates,
    get_finance_thresholds,
)

__all__ = [
    "FinanceMemoryConfig",
    "get_finance_default_sources",
    "get_finance_source_candidates",
    "get_finance_thresholds",
]
