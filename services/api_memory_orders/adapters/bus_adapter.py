"""
Memory Orders — Bus Adapter

Orchestrates LIVELLO 1 consumers + LIVELLO 2 persistence + event emission.
Bridge between pure domain logic and infrastructure.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — adapters)
"""

import logging
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from core.synaptic_conclave.transport.streams import StreamBus
from core.governance.memory_orders.domain import (
    CoherenceInput,
    CoherenceReport,
    SystemHealth,
    SyncInput,
    SyncPlan,
)
from core.governance.memory_orders.consumers import (
    CoherenceAnalyzer,
    HealthAggregator,
    SyncPlanner,
)
from core.governance.memory_orders.governance import (
    CoherenceThresholds,
)
from core.governance.memory_orders.events import (
    MEMORY_COHERENCE_CHECKED,
    MEMORY_HEALTH_CHECKED,
    MEMORY_SYNC_COMPLETED,
    MemoryEvent,
)

from api_memory_orders.config import settings
from api_memory_orders.adapters.persistence import MemoryPersistence
from api_memory_orders.reconciliation.orphan_detector import OrphanDetector
from api_memory_orders.reconciliation.version_reconciler import VersionReconciler
from api_memory_orders.reconciliation.duplicate_detector import DuplicateDetector
from api_memory_orders.reconciliation.conflict_resolver import ConflictResolver


logger = logging.getLogger(__name__)


class MemoryBusAdapter:
    """
    Orchestrator: LIVELLO 1 consumers + LIVELLO 2 persistence + events.
    
    Pattern:
    1. Fetch data (persistence I/O)
    2. Process data (LIVELLO 1 consumer — pure logic)
    3. Emit operational events (bus)
    4. Emit audit request event for Vault Keepers persistence
    5. Return result
    """
    
    def __init__(self):
        self.bus = StreamBus()
        self.persistence = MemoryPersistence()
        
        # LIVELLO 1 consumers (pure, no I/O)
        self.coherence_analyzer = CoherenceAnalyzer()
        self.health_aggregator = HealthAggregator()
        self.sync_planner = SyncPlanner()
        self.orphan_detector = OrphanDetector()
        self.version_reconciler = VersionReconciler()
        self.duplicate_detector = DuplicateDetector()
        self.conflict_resolver = ConflictResolver()
        
        # Thresholds (configurable)
        self.thresholds = CoherenceThresholds(
            healthy=settings.COHERENCE_THRESHOLD_HEALTHY,
            warning=settings.COHERENCE_THRESHOLD_WARNING,
        )
        
        logger.info("MemoryBusAdapter initialized")
    
    # ========================================
    #  Coherence Check Pipeline
    # ========================================
    
    async def handle_coherence_check(
        self,
        table: str = "entities",
        collection: str = None,
        embedded_column: str = "embedded",
        correlation_id: str | None = None,
        emit_audit_event: bool = True,
    ) -> CoherenceReport:
        """
        Complete coherence check pipeline.
        
        1. Fetch counts from PostgreSQL and Qdrant
        2. Analyze coherence (LIVELLO 1 — pure logic)
        3. Store audit record
        4. Emit event
        5. Return report
        
        Args:
            table: PostgreSQL table name
            collection: Qdrant collection name (default: from settings)
            embedded_column: Column indicating embedded status
        
        Returns:
            CoherenceReport with drift analysis
        """
        if collection is None:
            collection = settings.QDRANT_COLLECTION

        correlation_id = correlation_id or self._new_correlation_id("coherence")
        
        logger.info(f"Starting coherence check: {table} ↔ {collection}")
        
        # Step 1: Fetch counts (I/O)
        pg_count = self.persistence.get_postgres_count(table, embedded_column)
        qdrant_count = self.persistence.get_qdrant_count(collection)
        
        logger.info(f"Counts: PostgreSQL={pg_count}, Qdrant={qdrant_count}")
        
        # Step 2: Pure analysis (LIVELLO 1)
        input_data = CoherenceInput(
            pg_count=pg_count,
            qdrant_count=qdrant_count,
            thresholds=self.thresholds.as_tuple(),
            table=table,
            collection=collection,
        )
        report = self.coherence_analyzer.process(input_data)
        
        logger.info(f"Coherence status: {report.status}, drift: {report.drift_percentage:.2f}%")
        
        # Step 3: Emit domain event
        try:
            self.bus.emit(MEMORY_COHERENCE_CHECKED, report.to_dict())
            logger.info(f"Emitted event: {MEMORY_COHERENCE_CHECKED}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")

        # Step 4: Emit Vault audit request (event-only; no local DB audit writes)
        if emit_audit_event:
            self._emit_vault_audit_request(
                action="coherence",
                correlation_id=correlation_id,
                summary={
                    "status": report.status,
                    "table": table,
                    "collection": collection,
                    "pg_count": report.pg_count,
                    "qdrant_count": report.qdrant_count,
                },
                drift_metrics={
                    "drift_percentage": report.drift_percentage,
                    "drift_absolute": report.drift_absolute,
                },
            )

        # Step 5: Return report
        return report
    
    # ========================================
    #  Health Check Pipeline
    # ========================================
    
    async def handle_health_check(self, correlation_id: str | None = None) -> SystemHealth:
        """
        Complete health check pipeline.
        
        1. Check all component health (PostgreSQL, Qdrant, Redis, APIs)
        2. Aggregate health (LIVELLO 1 — pure logic)
        3. Store audit record
        4. Emit event
        5. Return health report
        
        Returns:
            SystemHealth with overall status and component details
        """
        logger.info("Starting health check")
        correlation_id = correlation_id or self._new_correlation_id("health")
        
        # Step 1: Check all components (I/O)
        components = (
            self.persistence.check_postgres_health(),
            self.persistence.check_qdrant_health(),
            self.persistence.check_redis_health(),
            self.persistence.check_embedding_api_health(),
            self.persistence.check_babel_gardens_health(),
        )
        
        logger.info(f"Component statuses: {[c.status for c in components]}")
        
        # Calculate summary metrics
        coherence_report = await self.handle_coherence_check(
            correlation_id=correlation_id,
            emit_audit_event=False,
        )
        summary = {
            "drift_percentage": coherence_report.drift_percentage,
            "coherence_status": coherence_report.status,
        }
        
        # Step 2: Aggregate health (LIVELLO 1)
        payload = {
            "components": components,
            "summary": summary,
        }
        health = self.health_aggregator.process(payload)
        
        logger.info(f"Overall health: {health.overall_status}")
        
        # Step 3: Emit domain event
        try:
            self.bus.emit(MEMORY_HEALTH_CHECKED, health.to_dict())
            logger.info(f"Emitted event: {MEMORY_HEALTH_CHECKED}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")

        # Step 4: Emit Vault audit request (event-only; no local DB audit writes)
        self._emit_vault_audit_request(
            action="health",
            correlation_id=correlation_id,
            summary={
                "status": health.overall_status,
                "components": [component.component for component in health.components],
            },
            drift_metrics={
                "drift_percentage": coherence_report.drift_percentage,
                "coherence_status": coherence_report.status,
            },
        )

        # Step 5: Return health
        return health
    
    # ========================================
    #  Sync Planning Pipeline
    # ========================================
    
    async def handle_sync_request(
        self,
        mode: str = "incremental",
        table: str = "entities",
        collection: str = None,
        limit: int = 1000,
        correlation_id: str | None = None,
    ) -> SyncPlan:
        """
        Complete sync planning pipeline.
        
        1. Fetch data from PostgreSQL and Qdrant
        2. Generate sync plan (LIVELLO 1 — pure logic)
        3. Store audit record
        4. Emit event
        5. Return plan (execution delegated to separate service)
        
        Args:
            mode: 'incremental' or 'full'
            table: PostgreSQL table
            collection: Qdrant collection
            limit: Max records to fetch for planning
        
        Returns:
            SyncPlan with operations to execute
        """
        if collection is None:
            collection = settings.QDRANT_COLLECTION

        correlation_id = correlation_id or self._new_correlation_id("sync")
        
        logger.info(f"Starting sync planning: mode={mode}, {table} ↔ {collection}")
        
        # Step 1: Fetch sync data (I/O)
        pg_data = self.persistence.fetch_postgres_sync_data(table, limit)
        qdrant_data = self.persistence.fetch_qdrant_sync_data(collection, limit)
        
        logger.info(f"Fetched: PostgreSQL={len(pg_data)}, Qdrant={len(qdrant_data)} records")
        
        # Step 2: Plan sync operations (LIVELLO 1)
        input_data = SyncInput(
            pg_data=pg_data,
            qdrant_data=qdrant_data,
            mode=mode,
            source_table=table,
            target_collection=collection,
        )
        plan = self.sync_planner.process(input_data)
        
        logger.info(f"Sync plan: {plan.total_operations} operations, estimated {plan.estimated_duration_s:.2f}s")
        
        # Step 3: Emit event (plan created, execution happens separately)
        try:
            self.bus.emit(MEMORY_SYNC_COMPLETED, plan.to_dict())
            logger.info(f"Emitted event: {MEMORY_SYNC_COMPLETED}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")

        # Step 4: Emit Vault audit request (event-only; no local DB audit writes)
        self._emit_vault_audit_request(
            action="sync",
            correlation_id=correlation_id,
            summary={
                "mode": mode,
                "source_table": table,
                "target_collection": collection,
                "operations": plan.total_operations,
            },
            drift_metrics={
                "operations_count": plan.total_operations,
                "estimated_duration_s": plan.estimated_duration_s,
            },
        )

        # Step 5: Return plan
        return plan

    # ========================================
    #  Reconciliation + Enforcement Pipeline
    # ========================================

    async def handle_reconciliation(
        self,
        table: str = "entities",
        collection: str | None = None,
        limit: int = 1000,
        execute: bool = False,
        idempotency_key: str | None = None,
        allow_mass_delete: bool = False,
        correlation_id: str | None = None,
    ) -> dict:
        """
        Build and optionally execute deterministic reconciliation plan.
        PG is authoritative; Qdrant is repaired according to policy mode.
        """
        if collection is None:
            collection = settings.QDRANT_COLLECTION

        correlation_id = correlation_id or self._new_correlation_id("reconcile")
        idempotency_key = idempotency_key or self._build_reconciliation_idempotency_key(
            table=table,
            collection=collection,
            limit=limit,
            execute=execute,
        )

        cached = self.persistence.get_cached_idempotency_result(idempotency_key)
        if cached:
            cached["idempotent_replay"] = True
            return cached

        lock_key = f"memory:reconcile:lock:{table}:{collection}"
        lock_acquired, lock_token = self.persistence.acquire_reconciliation_lock(
            lock_key=lock_key,
            ttl_s=settings.MEMORY_RECONCILIATION_LOCK_TTL_S,
        )
        if not lock_acquired:
            raise RuntimeError("Reconciliation already running for this source/collection")

        try:
            pg_records = self.persistence.fetch_pg_reconciliation_snapshot(table=table, limit=limit)
            qdrant_records = self.persistence.fetch_qdrant_reconciliation_snapshot(collection=collection, limit=limit)

            orphan_result = self.orphan_detector.detect(pg_records=pg_records, qdrant_records=qdrant_records)
            version_mismatches = self.version_reconciler.classify(pg_records=pg_records, qdrant_records=qdrant_records)
            duplicate_vectors = self.duplicate_detector.classify(qdrant_records=qdrant_records)

            operations = self.conflict_resolver.build_operations(
                pg_records=pg_records,
                pg_only_ids=orphan_result["pg_only_ids"],
                qdrant_only_ids=orphan_result["qdrant_only_ids"],
                version_mismatches=version_mismatches,
                duplicate_vectors=duplicate_vectors,
            )

            sync_plan = SyncPlan(
                operations=operations,
                estimated_duration_s=len(operations) * self.sync_planner.OPERATION_TIME_S,
                mode="incremental",
            )
            extra_drifts = self.sync_planner.classify_drift(
                SyncInput(
                    pg_data=pg_records,
                    qdrant_data=qdrant_records,
                    mode="incremental",
                    source_table=table,
                    target_collection=collection,
                )
            )
            reconciliation_plan = self.sync_planner.build_reconciliation_plan(
                sync_plan=sync_plan,
                drift_types=extra_drifts,
            )

            execution_summary = None
            delete_operations = tuple(
                op for op in reconciliation_plan.operations if op.operation_type == "delete"
            )
            qdrant_total = max(1, len(qdrant_records))
            delete_ratio = len(delete_operations) / qdrant_total
            mass_delete_blocked = (
                delete_ratio > settings.MEMORY_RECONCILIATION_MAX_DELETE_RATIO and not allow_mass_delete
            )

            if reconciliation_plan.requires_execution and execute and mass_delete_blocked:
                execution_summary = {
                    "attempted": reconciliation_plan.operations_count,
                    "applied": 0,
                    "skipped": reconciliation_plan.operations_count,
                    "failed": 0,
                    "mode": settings.MEMORY_RECONCILIATION_MODE,
                    "dead_lettered": 0,
                }
            elif reconciliation_plan.requires_execution and execute:
                if settings.MEMORY_RECONCILIATION_MODE == "dry_run":
                    execution_summary = {
                        "attempted": 0,
                        "applied": 0,
                        "skipped": 0,
                        "failed": 0,
                        "mode": "dry_run",
                        "dead_lettered": 0,
                    }
                else:
                    execution_summary = self.persistence.execute_reconciliation_operations(
                        operations=reconciliation_plan.operations,
                        collection=collection,
                        mode=settings.MEMORY_RECONCILIATION_MODE,
                    )

            response = {
                "status": "blocked" if mass_delete_blocked else "ok",
                "severity": reconciliation_plan.severity,
                "drift_types": [d.value for d in reconciliation_plan.drift_types],
                "operations_count": reconciliation_plan.operations_count,
                "requires_execution": reconciliation_plan.requires_execution,
                "execution": execution_summary,
                "recommendation": self._reconciliation_recommendation(
                    severity=reconciliation_plan.severity,
                    mode=settings.MEMORY_RECONCILIATION_MODE,
                    mass_delete_blocked=mass_delete_blocked,
                ),
                "correlation_id": correlation_id,
                "idempotent_replay": False,
            }

            self.persistence.cache_idempotency_result(
                idempotency_key=idempotency_key,
                result=response,
                ttl_s=settings.MEMORY_RECONCILIATION_IDEMPOTENCY_TTL_S,
            )

            self.persistence.increment_metric("runs_total", 1.0)
            if execution_summary:
                self.persistence.increment_metric("operations_attempted_total", float(execution_summary.get("attempted", 0)))
                self.persistence.increment_metric("operations_applied_total", float(execution_summary.get("applied", 0)))
                self.persistence.increment_metric("operations_failed_total", float(execution_summary.get("failed", 0)))
                self.persistence.increment_metric("dead_letter_total", float(execution_summary.get("dead_lettered", 0)))
            if mass_delete_blocked:
                self.persistence.increment_metric("policy_block_total", 1.0)

            try:
                self.bus.emit("memory.reconciliation.planned", response)
            except Exception:
                pass

            self._emit_vault_audit_request(
                action="reconciliation",
                correlation_id=correlation_id,
                summary={
                    "table": table,
                    "collection": collection,
                    "severity": reconciliation_plan.severity,
                    "operations_count": reconciliation_plan.operations_count,
                    "idempotency_key": idempotency_key,
                },
                drift_metrics={
                    "drift_types": [d.value for d in reconciliation_plan.drift_types],
                    "pg_snapshot": len(pg_records),
                    "qdrant_snapshot": len(qdrant_records),
                    "mass_delete_ratio": delete_ratio,
                },
                mode=settings.MEMORY_RECONCILIATION_MODE,
            )
            return response
        finally:
            self.persistence.release_reconciliation_lock(lock_key=lock_key, token=lock_token)

    @staticmethod
    def _reconciliation_recommendation(severity: str, mode: str, mass_delete_blocked: bool = False) -> str:
        if mass_delete_blocked:
            return "Execution blocked by delete-ratio policy. Set allow_mass_delete=true only after manual review."
        if severity == "healthy":
            return "No reconciliation actions required."
        if mode == "dry_run":
            return "Drift detected. Review operations and rerun with execute=true in assisted/autonomous mode."
        return "Drift detected. Execute reconciliation and monitor Vault audit trail."

    @staticmethod
    def _build_reconciliation_idempotency_key(
        table: str,
        collection: str,
        limit: int,
        execute: bool,
    ) -> str:
        seed = f"{table}|{collection}|{limit}|{execute}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]

    def _new_correlation_id(self, action: str) -> str:
        """Create a deterministic-looking correlation id for traceability."""
        return f"memory_{action}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

    def _emit_memory_event(
        self,
        stream: str,
        payload: dict,
        correlation_id: str,
        source: str = "memory_orders.api",
    ) -> None:
        """Emit a MemoryEvent envelope through StreamBus."""
        event = MemoryEvent(
            stream=stream,
            payload=tuple(payload.items()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id,
            source=source,
        )
        self.bus.emit(
            channel=event.stream,
            payload=event.to_dict(),
            emitter=event.source,
            correlation_id=event.correlation_id,
        )

    def _emit_vault_audit_request(
        self,
        action: str,
        correlation_id: str,
        summary: dict,
        drift_metrics: dict | None = None,
        mode: str | None = None,
    ) -> None:
        """Emit structured audit request for Vault Keepers ingestion."""
        payload = {
            "order": "memory_orders",
            "action": action,
            "summary": summary,
            "drift_metrics": drift_metrics or {},
            "mode": mode or settings.MEMORY_RECONCILIATION_MODE,
            "status": "completed",
            "correlation_id": correlation_id,
        }
        try:
            self._emit_memory_event(
                stream=settings.VAULT_AUDIT_REQUEST_CHANNEL,
                payload=payload,
                correlation_id=correlation_id,
            )
            logger.info("Emitted vault audit request: %s", settings.VAULT_AUDIT_REQUEST_CHANNEL)
        except Exception as exc:
            logger.error("Failed to emit vault audit request: %s", exc)
