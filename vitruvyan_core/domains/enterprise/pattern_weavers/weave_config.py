# domains/enterprise/pattern_weavers/weave_config.py
"""
Enterprise Weave Configuration — Pattern Weavers Domain Pack

Thresholds and category boosts for enterprise ontology resolution.
Mirrors finance FinanceWeaveConfig pattern.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class EnterpriseWeaveConfig:
    """Frozen configuration for enterprise ontology weaving."""

    base_similarity_threshold: float = 0.4
    enterprise_similarity_threshold: float = 0.42
    max_categories_per_query: int = 3
    category_boosts: Dict[str, float] = field(default_factory=lambda: {
        "CRM Pipeline": 1.15,
        "Sales": 1.12,
        "Invoicing": 1.12,
        "Accounting": 1.10,
        "Purchasing": 1.10,
        "Inventory": 1.08,
        "Human Resources": 1.08,
        "Product Catalog": 1.05,
        "Projects": 1.05,
        "Operations": 1.05,
        "Compliance": 1.15,
    })


_DEFAULT = EnterpriseWeaveConfig()


def get_enterprise_threshold() -> float:
    """Return the enterprise-specific similarity threshold."""
    return _DEFAULT.enterprise_similarity_threshold


def get_category_boost(category: str) -> float:
    """Return category-specific relevance boost."""
    return _DEFAULT.category_boosts.get(category, 1.0)
