"""
Finance Vertical Adapter
========================

Loads finance-specific source selection when MEMORY_DOMAIN=finance.
Keeps Memory Orders core agnostic by applying logic at LIVELLO 2 only.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

from ..config import settings

logger = logging.getLogger(__name__)


def _get_finance_helpers():
    """Import finance vertical helpers with local and package fallback."""
    try:
        from domains.finance.memory_orders.finance_config import (
            FinanceMemoryConfig,
            get_finance_source_candidates,
            get_finance_thresholds,
        )
    except ModuleNotFoundError:
        from core.domains.finance.memory_orders.finance_config import (
            FinanceMemoryConfig,
            get_finance_source_candidates,
            get_finance_thresholds,
        )

    return FinanceMemoryConfig, get_finance_source_candidates, get_finance_thresholds


class FinanceAdapter:
    """Finance adapter for Memory Orders source resolution."""

    def __init__(self):
        self._config = None

    @property
    def finance_config(self):
        if self._config is None:
            finance_config_cls, _, _ = _get_finance_helpers()
            self._config = finance_config_cls()
        return self._config

    def get_thresholds(self) -> dict[str, float]:
        """Expose finance threshold hints for diagnostics."""
        _, _, get_finance_thresholds = _get_finance_helpers()
        healthy, warning = get_finance_thresholds()
        return {
            "healthy": float(healthy),
            "warning": float(warning),
        }

    def resolve_sources(
        self,
        persistence: Any,
        table: str | None = None,
        collection: str | None = None,
        probe_backends: bool = True,
    ) -> dict[str, Any]:
        """
        Resolve best table/collection pair for finance vertical operations.

        Priority:
        1) explicit request overrides
        2) env overrides (MEMORY_FINANCE_TABLE / MEMORY_FINANCE_COLLECTION)
        3) finance primary sources (Mercator)
        4) finance legacy fallback sources (Vitruvyan)
        """
        _, get_finance_source_candidates, _ = _get_finance_helpers()

        table_override = table or settings.MEMORY_FINANCE_TABLE or None
        collection_override = collection or settings.MEMORY_FINANCE_COLLECTION or None
        candidates = get_finance_source_candidates(
            table_override=table_override,
            collection_override=collection_override,
        )

        table_candidates = tuple(candidates.get("tables", ()))
        collection_candidates = tuple(candidates.get("collections", ()))

        resolved_table = None
        resolved_collection = None
        if probe_backends:
            resolved_table = self._resolve_existing_table(
                persistence=persistence,
                table_candidates=table_candidates,
            )
            resolved_collection = self._resolve_existing_collection(
                persistence=persistence,
                collection_candidates=collection_candidates,
            )

        return {
            "table": resolved_table or (table_candidates[0] if table_candidates else "entities"),
            "collection": resolved_collection
            or (collection_candidates[0] if collection_candidates else settings.QDRANT_COLLECTION),
            "table_candidates": list(table_candidates),
            "collection_candidates": list(collection_candidates),
            "resolved_table_from_db": bool(resolved_table),
            "resolved_collection_from_qdrant": bool(resolved_collection),
        }

    @staticmethod
    def _resolve_existing_table(
        persistence: Any,
        table_candidates: Sequence[str],
    ) -> str | None:
        """Return first table candidate found in PostgreSQL public schema."""
        pg = getattr(persistence, "pg", None)
        if pg is None or not hasattr(pg, "fetch_one"):
            return None

        query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            ) AS exists;
        """

        for table_name in table_candidates:
            try:
                row = pg.fetch_one(query, (table_name,))
                exists = bool(next(iter((row or {}).values()), False))
                if exists:
                    return table_name
            except Exception as exc:
                logger.debug("Table probe failed for %s: %s", table_name, exc)
        return None

    @staticmethod
    def _resolve_existing_collection(
        persistence: Any,
        collection_candidates: Sequence[str],
    ) -> str | None:
        """Return first collection candidate present in Qdrant."""
        qdrant = getattr(persistence, "qdrant", None)
        client = getattr(qdrant, "client", None)
        if client is None or not hasattr(client, "get_collections"):
            return None

        try:
            collections_response = client.get_collections()
            raw_collections = getattr(collections_response, "collections", ())
            available = {
                getattr(item, "name", "")
                for item in raw_collections
                if getattr(item, "name", "")
            }
        except Exception as exc:
            logger.debug("Qdrant collection probe failed: %s", exc)
            return None

        for collection_name in collection_candidates:
            if collection_name in available:
                return collection_name
        return None


_finance_adapter: Optional[FinanceAdapter] = None


def is_finance_enabled() -> bool:
    """Check whether finance vertical is active for memory orders."""
    return settings.MEMORY_DOMAIN == "finance"


def get_finance_adapter() -> Optional[FinanceAdapter]:
    """Get finance adapter singleton when MEMORY_DOMAIN=finance."""
    global _finance_adapter
    if not is_finance_enabled():
        return None

    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("Finance vertical adapter loaded (MEMORY_DOMAIN=finance)")

    return _finance_adapter
