# domains/enterprise/pattern_weavers/__init__.py
"""
Enterprise Pattern Weavers Domain Pack

Ontology mapping for ERP/business domain: customers, invoices, CRM,
procurement, HR, inventory. Loaded via PATTERN_DOMAIN=enterprise.
"""

from .weave_config import (
    EnterpriseWeaveConfig,
    get_enterprise_threshold,
    get_category_boost,
)
from .enterprise_context import EnterpriseContextDetector

__all__ = [
    "EnterpriseWeaveConfig",
    "get_enterprise_threshold",
    "get_category_boost",
    "EnterpriseContextDetector",
]
