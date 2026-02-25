"""
Finance Vertical - Orthodoxy Wardens Integration
===============================================

Domain-specific configuration for finance governance in Orthodoxy Wardens.
Loaded when ORTHODOXY_DOMAIN=finance.
"""

from .compliance_config import (
    FinanceOrthodoxyConfig,
    get_finance_event_defaults,
    get_finance_ruleset_version,
)

__all__ = [
    "FinanceOrthodoxyConfig",
    "get_finance_ruleset_version",
    "get_finance_event_defaults",
]
