"""Duplicate vector identifier detection helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, TypedDict

from core.governance.memory_orders.domain import ConflictType


class DuplicateVectorFinding(TypedDict):
    """Duplicate vector identifier classification entry."""

    entity_id: str
    occurrences: int
    conflict_type: ConflictType


class DuplicateDetector:
    """
    Detect duplicate vector identifiers in Qdrant snapshots.

    Detection only: this component does not mutate storage state.
    """

    def classify(
        self,
        qdrant_records: tuple[dict[str, Any], ...],
    ) -> tuple[DuplicateVectorFinding, ...]:
        ids = [
            str(record.get("id"))
            for record in qdrant_records
            if isinstance(record, dict) and record.get("id") is not None
        ]
        counts = Counter(ids)

        duplicates: list[DuplicateVectorFinding] = []
        for entity_id, occurrences in counts.items():
            if occurrences <= 1:
                continue
            duplicates.append(
                {
                    "entity_id": entity_id,
                    "occurrences": occurrences,
                    "conflict_type": ConflictType.DUPLICATE_VECTOR,
                }
            )

        duplicates.sort(key=lambda item: item["entity_id"])
        return tuple(duplicates)
