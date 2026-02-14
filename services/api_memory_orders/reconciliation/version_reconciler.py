"""Version metadata reconciliation helpers (PG authoritative)."""

from __future__ import annotations

from typing import Any, TypedDict

from core.governance.memory_orders.domain import ConflictType


class VersionMismatch(TypedDict):
    """Metadata mismatch between canonical and derived representations."""

    entity_id: str
    pg_version: str | None
    qdrant_version: str | None
    pg_updated_at: str | None
    qdrant_updated_at: str | None
    authoritative_source: str
    conflict_type: ConflictType


class VersionReconciler:
    """Classify stale derived vectors based on version/updated_at metadata drift."""

    def classify(
        self,
        pg_records: tuple[dict[str, Any], ...],
        qdrant_records: tuple[dict[str, Any], ...],
    ) -> tuple[VersionMismatch, ...]:
        pg_index = self._index_by_id(pg_records)
        qdrant_index = self._index_by_id(qdrant_records)
        shared_ids = sorted(set(pg_index.keys()) & set(qdrant_index.keys()))

        mismatches: list[VersionMismatch] = []
        for entity_id in shared_ids:
            pg_meta = self._meta_tuple(pg_index[entity_id])
            qdrant_meta = self._meta_tuple(qdrant_index[entity_id])

            if pg_meta == qdrant_meta:
                continue

            mismatches.append(
                {
                    "entity_id": entity_id,
                    "pg_version": pg_meta[0],
                    "qdrant_version": qdrant_meta[0],
                    "pg_updated_at": pg_meta[1],
                    "qdrant_updated_at": qdrant_meta[1],
                    "authoritative_source": "pg",
                    "conflict_type": ConflictType.STALE_VECTOR,
                }
            )

        return tuple(mismatches)

    @staticmethod
    def _index_by_id(records: tuple[dict[str, Any], ...]) -> dict[str, dict[str, Any]]:
        return {
            str(record.get("id")): record
            for record in records
            if isinstance(record, dict) and record.get("id") is not None
        }

    @staticmethod
    def _meta_tuple(record: dict[str, Any]) -> tuple[str | None, str | None]:
        version = record.get("version")
        updated_at = record.get("updated_at")
        version_str = None if version is None else str(version)
        updated_at_str = None if updated_at is None else str(updated_at)
        return version_str, updated_at_str
