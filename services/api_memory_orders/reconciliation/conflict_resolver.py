"""Conflict resolution helpers that map classifications to SyncOperation DTOs."""

from __future__ import annotations

from typing import Any

from core.governance.memory_orders.domain import (
    ConflictType,
    SyncOperation,
)


class ConflictResolver:
    """
    Convert reconciliation findings into storage operations.

    This helper performs no I/O and does not execute operations.
    """

    def build_operations(
        self,
        pg_records: tuple[dict[str, Any], ...],
        pg_only_ids: tuple[str, ...],
        qdrant_only_ids: tuple[str, ...],
        version_mismatches: tuple[dict[str, Any], ...],
        duplicate_vectors: tuple[dict[str, Any], ...],
    ) -> tuple[SyncOperation, ...]:
        pg_index = self._index_by_id(pg_records)
        operations: list[SyncOperation] = []

        for entity_id in pg_only_ids:
            operations.append(
                SyncOperation(
                    operation_type="insert",
                    target="mnemosyne",
                    payload=self._canonical_payload(
                        entity_id=entity_id,
                        record=pg_index.get(entity_id),
                        reason=ConflictType.MISSING_VECTOR,
                    ),
                    entity_id=entity_id,
                )
            )

        for entity_id in qdrant_only_ids:
            operations.append(
                SyncOperation(
                    operation_type="delete",
                    target="mnemosyne",
                    payload=(("id", entity_id), ("reason", ConflictType.ORPHAN_VECTOR.value)),
                    entity_id=entity_id,
                )
            )

        for mismatch in version_mismatches:
            entity_id = str(mismatch.get("entity_id"))
            operations.append(
                SyncOperation(
                    operation_type="update",
                    target="mnemosyne",
                    payload=self._canonical_payload(
                        entity_id=entity_id,
                        record=pg_index.get(entity_id),
                        reason=ConflictType.STALE_VECTOR,
                    ),
                    entity_id=entity_id,
                )
            )

        for duplicate in duplicate_vectors:
            entity_id = str(duplicate.get("entity_id"))
            operations.append(
                SyncOperation(
                    operation_type="update",
                    target="mnemosyne",
                    payload=self._canonical_payload(
                        entity_id=entity_id,
                        record=pg_index.get(entity_id),
                        reason=ConflictType.DUPLICATE_VECTOR,
                    ),
                    entity_id=entity_id,
                )
            )

        return tuple(operations)

    @staticmethod
    def _index_by_id(records: tuple[dict[str, Any], ...]) -> dict[str, dict[str, Any]]:
        return {
            str(record.get("id")): record
            for record in records
            if isinstance(record, dict) and record.get("id") is not None
        }

    @staticmethod
    def _canonical_payload(
        entity_id: str,
        record: dict[str, Any] | None,
        reason: ConflictType,
    ) -> tuple[tuple[str, Any], ...]:
        canonical = record or {}
        metadata = canonical.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        return (
            ("id", entity_id),
            ("version", canonical.get("version")),
            ("updated_at", canonical.get("updated_at")),
            ("metadata", metadata),
            ("reason", reason.value),
            ("authoritative_source", "pg"),
        )
