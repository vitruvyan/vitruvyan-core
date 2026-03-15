"""
Enterprise Vertical - MCP Server integration helpers.

This package contains enterprise-only configuration and argument normalization
used by MCP server when MCP_DOMAIN=enterprise.
"""

from .enterprise_config import (
    EnterpriseMCPConfig,
    build_enterprise_phrase_samples,
    get_enterprise_signal_source_candidates,
    get_enterprise_tool_schemas,
    normalize_enterprise_args,
    resolve_enterprise_tool_name,
)

__all__ = [
    "EnterpriseMCPConfig",
    "build_enterprise_phrase_samples",
    "get_enterprise_signal_source_candidates",
    "get_enterprise_tool_schemas",
    "normalize_enterprise_args",
    "resolve_enterprise_tool_name",
]
