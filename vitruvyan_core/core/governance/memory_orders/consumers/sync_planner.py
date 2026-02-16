"""
Memory Orders — Sync Planner

Pure synchronization planning between Archivarium and Mnemosyne.
Pure planning logic, NO I/O.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — consumers)
"""

from collections import Counter
from typing import Any

from .base import MemoryRole
from ..domain import (
    SyncInput,
    SyncOperation,
    SyncPlan,
    DriftType,
    ConflictType,
    ReconciliationPlan,
)


class SyncPlanner(MemoryRole):
    """
    Pure sync operation planning: determine what operations to execute.
    
    Algorithm:
    1. Compare pg_data and qdrant_data
    2. Identify missing records (pg → qdrant)
    3. Identify orphaned records (qdrant → pg)
    4. Generate insert/update/delete operations
    5. Estimate execution duration
    6. Return frozen SyncPlan
    
    NO I/O. NO database writes. NO HTTP calls.
    """
    
    OPERATION_TIME_S = 0.1  # Estimated time per operation (for duration calculation)
    CRITICAL_DRIFT_TYPES = frozenset(
        [
            DriftType.ORPHAN_IN_PG,
            DriftType.ORPHAN_IN_QDRANT,
            DriftType.VERSION_MISMATCH,
            DriftType.DUPLICATE_ENTRY,
        ]
    )
    
    def process(self, payload: SyncInput) -> SyncPlan:
        """
        Plan synchronization operations.
        
        Args:
            payload: SyncInput with pg_data, qdrant_data, and mode
        
        Returns:
            SyncPlan with operations to execute
        
        Raises:
            ValueError: If payload is not a SyncInput
        """
        if not isinstance(payload, SyncInput):
            raise ValueError(f"Expected SyncInput, got {type(payload)}")
        
        operations = []
        
        # Mode: full sync (rebuild entire Qdrant from PostgreSQL)
        if payload.mode == "full":
            operations = self._plan_full_sync(payload)
        
        # Mode: incremental sync (only missing/modified records)
        elif payload.mode == "incremental":
            operations = self._plan_incremental_sync(payload)
        
        else:
            raise ValueError(f"Unknown sync mode: {payload.mode}")
        
        # Estimate duration
        estimated_duration = len(operations) * self.OPERATION_TIME_S
        
        # Return frozen plan
        return SyncPlan(
            operations=tuple(operations),
            estimated_duration_s=estimated_duration,
            mode=payload.mode,
        )

    def process_reconciliation(
        self,
        payload: SyncInput,
        extra_drift_types: tuple[DriftType, ...] = (),
    ) -> ReconciliationPlan:
        """
        Build deterministic reconciliation plan from sync input + optional external drift hints.

        Args:
            payload: Sync input snapshot.
            extra_drift_types: Additional drift categories discovered by service-level detectors.

        Returns:
            ReconciliationPlan for execution layer.
        """
        sync_plan = self.process(payload)
        drift_types = self.classify_drift(payload) + tuple(extra_drift_types)
        return self.build_reconciliation_plan(sync_plan, drift_types)

    def classify_drift(self, payload: SyncInput) -> tuple[DriftType, ...]:
        """Classify drift categories deterministically from pure snapshots."""
        if not isinstance(payload, SyncInput):
            raise ValueError(f"Expected SyncInput, got {type(payload)}")

        drift_types: list[DriftType] = []

        pg_ids_list = [self._extract_id(record) for record in payload.pg_data]
        qdrant_ids_list = [self._extract_id(record) for record in payload.qdrant_data]
        pg_ids = set(pg_ids_list)
        qdrant_ids = set(qdrant_ids_list)

        if len(payload.pg_data) != len(payload.qdrant_data):
            drift_types.append(DriftType.COUNT_MISMATCH)

        if pg_ids - qdrant_ids:
            drift_types.append(DriftType.ORPHAN_IN_PG)

        if qdrant_ids - pg_ids:
            drift_types.append(DriftType.ORPHAN_IN_QDRANT)

        if self._has_version_mismatch(payload):
            drift_types.append(DriftType.VERSION_MISMATCH)

        if self._has_duplicate_ids(pg_ids_list) or self._has_duplicate_ids(qdrant_ids_list):
            drift_types.append(DriftType.DUPLICATE_ENTRY)

        return tuple(drift_types)

    def map_drift_to_conflicts(
        self,
        drift_types: tuple[DriftType, ...],
    ) -> tuple[ConflictType, ...]:
        """Map drift categories to storage-level conflict categories."""
        conflicts: list[ConflictType] = []

        if DriftType.ORPHAN_IN_PG in drift_types:
            conflicts.append(ConflictType.MISSING_VECTOR)

        if DriftType.ORPHAN_IN_QDRANT in drift_types:
            conflicts.append(ConflictType.ORPHAN_VECTOR)

        if DriftType.VERSION_MISMATCH in drift_types:
            conflicts.append(ConflictType.STALE_VECTOR)

        if DriftType.DUPLICATE_ENTRY in drift_types:
            conflicts.append(ConflictType.DUPLICATE_VECTOR)

        return tuple(conflicts)

    def build_reconciliation_plan(
        self,
        sync_plan: SyncPlan,
        drift_types: tuple[DriftType, ...],
    ) -> ReconciliationPlan:
        """Build reconciliation plan from existing sync plan to avoid operation duplication."""
        unique_drifts = tuple(dict.fromkeys(drift_types))
        severity = self._severity_for_drifts(unique_drifts, sync_plan.total_operations)
        requires_execution = sync_plan.total_operations > 0

        return ReconciliationPlan(
            drift_types=unique_drifts,
            operations=sync_plan.operations,
            severity=severity,
            requires_execution=requires_execution,
        )
    
    def _plan_full_sync(self, payload: SyncInput) -> list[SyncOperation]:
        """
        Plan full synchronization: rebuild Qdrant from PostgreSQL.
        
        Algorithm:
        1. DELETE all points from Qdrant (target: mnemosyne)
        2. INSERT all records from PostgreSQL (target: mnemosyne)
        
        Args:
            payload: SyncInput
        
        Returns:
            List of SyncOperation objects
        """
        operations = []
        
        # Step 1: Clear Qdrant collection
        operations.append(
            SyncOperation(
                operation_type="delete",
                target="mnemosyne",
                payload=(("action", "clear_collection"), ("collection", payload.target_collection)),
                entity_id=None,
            )
        )
        
        # Step 2: Insert all PostgreSQL records
        for record in payload.pg_data:
            # Assume record is dict-like with 'id' and 'embedding'
            if isinstance(record, dict):
                entity_id = record.get("id", str(hash(record)))
                operations.append(
                    SyncOperation(
                        operation_type="insert",
                        target="mnemosyne",
                        payload=tuple(record.items()),
                        entity_id=entity_id,
                    )
                )
        
        return operations
    
    def _plan_incremental_sync(self, payload: SyncInput) -> list[SyncOperation]:
        """
        Plan incremental synchronization: only missing/modified records.
        
        Algorithm:
        1. Find records in PostgreSQL not in Qdrant → INSERT
        2. Find records in Qdrant not in PostgreSQL → DELETE
        3. Find modified records → UPDATE
        
        Args:
            payload: SyncInput
        
        Returns:
            List of SyncOperation objects
        """
        operations = []
        
        # Convert data to sets for comparison (assume records have 'id' field)
        pg_ids = {self._extract_id(r) for r in payload.pg_data}
        qdrant_ids = {self._extract_id(r) for r in payload.qdrant_data}
        
        # Missing in Qdrant → INSERT
        missing_in_qdrant = pg_ids - qdrant_ids
        for entity_id in missing_in_qdrant:
            record = next((r for r in payload.pg_data if self._extract_id(r) == entity_id), None)
            if record:
                operations.append(
                    SyncOperation(
                        operation_type="insert",
                        target="mnemosyne",
                        payload=tuple(record.items()) if isinstance(record, dict) else (("id", entity_id),),
                        entity_id=entity_id,
                    )
                )
        
        # Orphaned in Qdrant → DELETE
        orphaned_in_qdrant = qdrant_ids - pg_ids
        for entity_id in orphaned_in_qdrant:
            operations.append(
                SyncOperation(
                    operation_type="delete",
                    target="mnemosyne",
                    payload=(("id", entity_id),),
                    entity_id=entity_id,
                )
            )
        
        return operations
    
    def _extract_id(self, record: Any) -> str:
        """Extract ID from record (dict or tuple)."""
        if isinstance(record, dict):
            record_id = record.get("id")
            if record_id is None:
                return str(id(record))
            return str(record_id)
        elif isinstance(record, tuple):
            # Assume first element is ID
            return str(record[0]) if record else ""
        else:
            return str(hash(record))

    def _has_duplicate_ids(self, ids: list[str]) -> bool:
        """Return True when same entity ID appears more than once."""
        counts = Counter(ids)
        return any(count > 1 for count in counts.values())

    def _has_version_mismatch(self, payload: SyncInput) -> bool:
        """Detect version mismatch for entities present in both stores."""
        pg_records = {
            self._extract_id(record): record for record in payload.pg_data if isinstance(record, dict)
        }
        qdrant_records = {
            self._extract_id(record): record for record in payload.qdrant_data if isinstance(record, dict)
        }

        shared_ids = set(pg_records.keys()) & set(qdrant_records.keys())
        for entity_id in shared_ids:
            pg_meta = self._extract_version_metadata(pg_records[entity_id])
            qdrant_meta = self._extract_version_metadata(qdrant_records[entity_id])
            if pg_meta is None and qdrant_meta is None:
                continue
            if pg_meta != qdrant_meta:
                return True
        return False

    def _extract_version_metadata(self, record: dict[str, Any]) -> tuple[str, str] | None:
        """Extract comparable version metadata tuple (version, updated_at)."""
        version = record.get("version")
        updated_at = record.get("updated_at")

        if version is None and updated_at is None:
            return None

        return (
            "" if version is None else str(version),
            "" if updated_at is None else str(updated_at),
        )

    def _severity_for_drifts(
        self,
        drift_types: tuple[DriftType, ...],
        operations_count: int,
    ) -> str:
        """Compute deterministic severity from drift categories and required operations."""
        if not drift_types and operations_count == 0:
            return "healthy"

        if any(drift in self.CRITICAL_DRIFT_TYPES for drift in drift_types):
            return "critical"

        if DriftType.COUNT_MISMATCH in drift_types or operations_count > 0:
            return "warning"

        return "healthy"
    
    def can_handle(self, payload: SyncInput) -> bool:
        """Check if payload is valid SyncInput."""
        return isinstance(payload, SyncInput)
