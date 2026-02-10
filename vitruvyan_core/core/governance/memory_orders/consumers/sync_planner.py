"""
Memory Orders — Sync Planner

Pure synchronization planning between Archivarium and Mnemosyne.
Extracted from _legacy/phrase_sync.py (ONLY planning logic, NO I/O).

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — consumers)
"""

from .base import MemoryRole
from ..domain import (
    SyncInput,
    SyncOperation,
    SyncPlan,
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
    
    def _extract_id(self, record: any) -> str:
        """Extract ID from record (dict or tuple)."""
        if isinstance(record, dict):
            return str(record.get("id", hash(record)))
        elif isinstance(record, tuple):
            # Assume first element is ID
            return str(record[0]) if record else ""
        else:
            return str(hash(record))
    
    def can_handle(self, payload: SyncInput) -> bool:
        """Check if payload is valid SyncInput."""
        return isinstance(payload, SyncInput)
