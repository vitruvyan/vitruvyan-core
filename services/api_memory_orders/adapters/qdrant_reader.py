"""Qdrant read adapter for reconciliation snapshots."""

from __future__ import annotations

from typing import Any, TypedDict

from core.agents.qdrant_agent import QdrantAgent


class QdrantVectorRecord(TypedDict):
    """Minimal derived-vector record used by reconciliation flow."""

    id: str
    version: Any | None
    updated_at: str | None
    has_vector: bool
    metadata: dict[str, Any]


class QdrantReader:
    """
    Read-only Qdrant adapter for derived vector snapshots.

    This adapter intentionally contains no reconciliation logic.
    """

    def __init__(self, qdrant_agent: QdrantAgent | None = None):
        self.qdrant = qdrant_agent or QdrantAgent()

    def read_vectors(
        self,
        collection: str,
        limit: int = 1000,
    ) -> tuple[QdrantVectorRecord, ...]:
        """Read vector entries from a collection with payload metadata."""
        try:
            points, _ = self.qdrant.client.scroll(
                collection_name=collection,
                limit=limit,
                with_payload=True,
                with_vectors=True,
            )
        except Exception:
            return ()

        records: list[QdrantVectorRecord] = []
        for point in points:
            payload = point.payload if isinstance(point.payload, dict) else {}
            metadata = dict(payload)
            records.append(
                {
                    "id": str(getattr(point, "id", "")),
                    "version": payload.get("version"),
                    "updated_at": self._to_str_or_none(payload.get("updated_at")),
                    "has_vector": getattr(point, "vector", None) is not None,
                    "metadata": metadata,
                }
            )

        return tuple(records)

    @staticmethod
    def _to_str_or_none(value: Any) -> str | None:
        return None if value is None else str(value)
