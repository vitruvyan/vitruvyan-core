# domains/enterprise/memory_orders/__init__.py
"""
Enterprise Memory Orders Domain Pack

Coherence monitoring configuration for enterprise ERP data.
Loaded when MEMORY_DOMAIN=enterprise.
"""

from .enterprise_config import (
    EnterpriseMemoryConfig,
    get_enterprise_thresholds,
    get_enterprise_default_sources,
)

__all__ = [
    "EnterpriseMemoryConfig",
    "get_enterprise_thresholds",
    "get_enterprise_default_sources",
]
