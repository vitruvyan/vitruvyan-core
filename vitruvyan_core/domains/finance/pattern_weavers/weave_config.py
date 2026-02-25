"""
Finance Weaving Configuration
=============================

Finance-specific thresholding and category boosts for Pattern Weavers.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class FinanceWeaveConfig:
    """Finance-specific weaving configuration."""

    base_similarity_threshold: float = 0.4
    finance_similarity_threshold: float = 0.45
    top_k: int = 10
    category_boosts: Dict[str, float] = field(
        default_factory=lambda: {
            "sectors": 1.15,
            "instruments": 1.1,
            "macro": 1.05,
            "risk_terms": 1.08,
            "regions": 1.02,
        }
    )
    max_adjusted_score: float = 1.0


def get_finance_threshold(is_financial: bool) -> float:
    """Return finance-aware semantic threshold."""
    cfg = FinanceWeaveConfig()
    if is_financial:
        return cfg.finance_similarity_threshold
    return cfg.base_similarity_threshold


def get_category_boost(category: str, is_financial: bool) -> float:
    """Return multiplier for category score adjustment."""
    if not is_financial:
        return 1.0
    return FinanceWeaveConfig().category_boosts.get((category or "").lower(), 1.0)
