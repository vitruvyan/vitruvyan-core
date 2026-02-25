"""
Finance Vertical - MCP Server integration helpers.

This package contains finance-only configuration and argument normalization
used by `services/api_mcp` when `MCP_DOMAIN=finance`.
"""

from .finance_config import (
    FinanceMCPConfig,
    build_finance_phrase_samples,
    get_finance_signal_source_candidates,
    normalize_finance_args,
    resolve_finance_tool_name,
)

__all__ = [
    "FinanceMCPConfig",
    "build_finance_phrase_samples",
    "get_finance_signal_source_candidates",
    "normalize_finance_args",
    "resolve_finance_tool_name",
]

