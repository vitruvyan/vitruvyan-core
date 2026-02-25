"""
Finance Memory Orders Configuration
===================================

Minimal finance-specific settings for Memory Orders.
This package keeps LIVELLO 1 agnostic and only provides source-selection hints
used by LIVELLO 2 adapters.
"""

from dataclasses import dataclass
from typing import Iterable, Optional


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    """Deduplicate string values while preserving insertion order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_value in values:
        value = (raw_value or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


@dataclass(frozen=True)
class FinanceMemoryConfig:
    """
    Finance vertical memory configuration.

    `primary_*` are Mercator-native defaults.
    `legacy_*` provide migration compatibility with Vitruvyan imports.
    """

    primary_table: str = "entities"
    primary_collection: str = "entities_embeddings"
    legacy_table: str = "phrases"
    legacy_collection: str = "phrases_embeddings"

    healthy_drift_threshold: float = 5.0
    warning_drift_threshold: float = 15.0

    default_sync_mode: str = "incremental"
    default_limit: int = 1000


def get_finance_thresholds() -> tuple[float, float]:
    """Return (healthy, warning) drift thresholds for finance operations."""
    cfg = FinanceMemoryConfig()
    return cfg.healthy_drift_threshold, cfg.warning_drift_threshold


def get_finance_default_sources() -> dict[str, str]:
    """Return canonical finance source pair for Memory Orders."""
    cfg = FinanceMemoryConfig()
    return {
        "table": cfg.primary_table,
        "collection": cfg.primary_collection,
    }


def get_finance_source_candidates(
    table_override: Optional[str] = None,
    collection_override: Optional[str] = None,
) -> dict[str, tuple[str, ...]]:
    """
    Return ordered candidates for source resolution.

    Priority:
    1) optional explicit override
    2) Mercator primary source
    3) Vitruvyan legacy fallback
    """
    cfg = FinanceMemoryConfig()
    return {
        "tables": _ordered_unique(
            (
                table_override or "",
                cfg.primary_table,
                cfg.legacy_table,
            )
        ),
        "collections": _ordered_unique(
            (
                collection_override or "",
                cfg.primary_collection,
                cfg.legacy_collection,
            )
        ),
    }
