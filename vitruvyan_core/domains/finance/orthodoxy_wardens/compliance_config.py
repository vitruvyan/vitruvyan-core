"""
Finance Orthodoxy Configuration
==============================

Minimal finance-specific runtime defaults for Orthodoxy Wardens.
This package remains pure configuration (no I/O).
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class FinanceOrthodoxyConfig:
    """Finance vertical defaults for governance audits."""

    domain_name: str = "finance"
    ruleset_version: str = "v1.1-finance"
    default_scope: str = "single_output"
    default_trigger_type: str = "output_validation"
    default_source: str = "orthodoxy.finance"
    strict_mode: bool = True
    confidence_floor: float = 0.75


def get_finance_ruleset_version() -> str:
    """Return finance ruleset version tag."""
    return FinanceOrthodoxyConfig().ruleset_version


def get_finance_event_defaults() -> Dict[str, str]:
    """Return default event fields used for finance validation payloads."""
    cfg = FinanceOrthodoxyConfig()
    return {
        "trigger_type": cfg.default_trigger_type,
        "scope": cfg.default_scope,
        "source": cfg.default_source,
    }
