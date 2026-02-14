"""Orphan detection helpers for reconciliation snapshots."""

from __future__ import annotations

from typing import Any, TypedDict


class OrphanDetectionResult(TypedDict):
    """Identifier-level orphan summary between canonical and derived snapshots."""

    pg_only_ids: tuple[str, ...]
    qdrant_only_ids: tuple[str, ...]


class OrphanDetector:
    """Detect entity identifiers present in one store but missing in the other."""

    def detect(
        self,
        pg_records: tuple[dict[str, Any], ...],
        qdrant_records: tuple[dict[str, Any], ...],
    ) -> OrphanDetectionResult:
        pg_ids = self._extract_ids(pg_records)
        qdrant_ids = self._extract_ids(qdrant_records)

        return {
            "pg_only_ids": tuple(sorted(pg_ids - qdrant_ids)),
            "qdrant_only_ids": tuple(sorted(qdrant_ids - pg_ids)),
        }

    @staticmethod
    def _extract_ids(records: tuple[dict[str, Any], ...]) -> set[str]:
        return {
            str(record.get("id"))
            for record in records
            if isinstance(record, dict) and record.get("id") is not None
        }
