"""
Memory Orders — Bus Adapter

Orchestrates LIVELLO 1 consumers + LIVELLO 2 persistence + event emission.
Bridge between pure domain logic and infrastructure.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — adapters)
"""

import logging
from typing import Any

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
    MEMORY_AUDIT_RECORDED,
)

from api_memory_orders.config import settings
from api_memory_orders.adapters.persistence import MemoryPersistence


logger = logging.getLogger(__name__)


class MemoryBusAdapter:
    """
    Orchestrator: LIVELLO 1 consumers + LIVELLO 2 persistence + events.
    
    Pattern:
    1. Fetch data (persistence I/O)
    2. Process data (LIVELLO 1 consumer — pure logic)
    3. Store audit (persistence I/O)
    4. Emit event (bus)
    5. Return result
    """
    
    def __init__(self):
        self.bus = StreamBus()
        self.persistence = MemoryPersistence()
        
        # LIVELLO 1 consumers (pure, no I/O)
        self.coherence_analyzer = CoherenceAnalyzer()
        self.health_aggregator = HealthAggregator()
        self.sync_planner = SyncPlanner()
        
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
        embedded_column: str = "embedded"
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
        
        # Step 3: Audit (I/O)
        try:
            self.persistence.store_audit_record("coherence_check", report.to_dict())
        except Exception as e:
            logger.error(f"Failed to store audit record: {e}")
        
        # Step 4: Emit event
        try:
            self.bus.emit(MEMORY_COHERENCE_CHECKED, report.to_dict())
            logger.info(f"Emitted event: {MEMORY_COHERENCE_CHECKED}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
        
        # Step 5: Return report
        return report
    
    # ========================================
    #  Health Check Pipeline
    # ========================================
    
    async def handle_health_check(self) -> SystemHealth:
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
        coherence_report = await self.handle_coherence_check()
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
        
        # Step 3: Audit (I/O)
        try:
            self.persistence.store_audit_record("health_check", health.to_dict())
        except Exception as e:
            logger.error(f"Failed to store audit record: {e}")
        
        # Step 4: Emit event
        try:
            self.bus.emit(MEMORY_HEALTH_CHECKED, health.to_dict())
            logger.info(f"Emitted event: {MEMORY_HEALTH_CHECKED}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
        
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
        limit: int = 1000
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
        
        # Step 3: Audit (I/O)
        try:
            self.persistence.store_audit_record("sync_planning", plan.to_dict())
        except Exception as e:
            logger.error(f"Failed to store audit record: {e}")
        
        # Step 4: Emit event (plan created, execution happens separately)
        try:
            self.bus.emit(MEMORY_SYNC_COMPLETED, plan.to_dict())
            logger.info(f"Emitted event: {MEMORY_SYNC_COMPLETED}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
        
        # Step 5: Return plan
        return plan
