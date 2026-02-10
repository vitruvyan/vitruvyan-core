"""
Bus Adapter for Codex Hunters
=============================

Orchestrates LIVELLO 1 pure consumers with StreamBus for event communication.
This adapter bridges pure domain logic with infrastructure.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import get_config
from .persistence import get_persistence

logger = logging.getLogger(__name__)


class BusAdapter:
    """
    Orchestrates LIVELLO 1 consumers and handles event emission.
    
    Responsibilities:
    - Import and orchestrate pure consumers
    - Emit events to StreamBus
    - Delegate persistence to PersistenceAdapter
    """
    
    def __init__(self):
        """Initialize bus adapter with lazy consumer loading."""
        self._bus = None
        self._tracker_consumer = None
        self._restorer_consumer = None
        self._binder_consumer = None
        self._config = get_config()
        self._persistence = get_persistence()
    
    @property
    def bus(self):
        """Lazy-load StreamBus."""
        if self._bus is None:
            try:
                from core.synaptic_conclave.transport.streams import StreamBus
                self._bus = StreamBus()
                logger.info("✅ StreamBus initialized")
            except ImportError as e:
                logger.warning(f"⚠️ StreamBus not available: {e}")
        return self._bus
    
    @property
    def tracker_consumer(self):
        """Lazy-load TrackerConsumer from LIVELLO 1."""
        if self._tracker_consumer is None:
            try:
                from core.governance.codex_hunters.consumers import TrackerConsumer
                self._tracker_consumer = TrackerConsumer()
                logger.info("✅ TrackerConsumer initialized")
            except ImportError as e:
                logger.warning(f"⚠️ TrackerConsumer not available: {e}")
        return self._tracker_consumer
    
    @property
    def restorer_consumer(self):
        """Lazy-load RestorerConsumer from LIVELLO 1."""
        if self._restorer_consumer is None:
            try:
                from core.governance.codex_hunters.consumers import RestorerConsumer
                self._restorer_consumer = RestorerConsumer()
                logger.info("✅ RestorerConsumer initialized")
            except ImportError as e:
                logger.warning(f"⚠️ RestorerConsumer not available: {e}")
        return self._restorer_consumer
    
    @property
    def binder_consumer(self):
        """Lazy-load BinderConsumer from LIVELLO 1."""
        if self._binder_consumer is None:
            try:
                from core.governance.codex_hunters.consumers import BinderConsumer
                self._binder_consumer = BinderConsumer()
                logger.info("✅ BinderConsumer initialized")
            except ImportError as e:
                logger.warning(f"⚠️ BinderConsumer not available: {e}")
        return self._binder_consumer
    
    # =========================================================================
    # Discovery Pipeline
    # =========================================================================
    
    def process_discovery(
        self,
        entity_id: str,
        source_type: str,
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process entity discovery through LIVELLO 1 consumer.
        
        Args:
            entity_id: Unique entity identifier
            source_type: Source type (configurable)
            raw_data: Raw data from source
            metadata: Additional metadata
            
        Returns:
            Processing result
        """
        if not self.tracker_consumer:
            return {"success": False, "error": "TrackerConsumer not available"}
        
        # Prepare event for pure consumer
        event = {
            "entity_id": entity_id,
            "source_type": source_type,
            "raw_data": raw_data,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Process through pure consumer (no I/O)
        result = self.tracker_consumer.process(event)
        
        # Emit event to bus if successful
        if result.success and self.bus:
            try:
                from core.governance.codex_hunters.events import Channels
                self.bus.emit(
                    Channels.DISCOVERED,
                    {
                        "entity_id": entity_id,
                        "source_type": source_type,
                        "discovered_at": datetime.utcnow().isoformat(),
                        "data": result.data,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to emit discovery event: {e}")
        
        return {
            "success": result.success,
            "entity_id": entity_id,
            "message": result.message,
            "data": result.data,
            "errors": result.errors,
        }
    
    def process_restore(
        self,
        entity_id: str,
        raw_data: Dict[str, Any],
        source_type: str
    ) -> Dict[str, Any]:
        """
        Process data restoration through LIVELLO 1 consumer.
        
        Args:
            entity_id: Entity identifier
            raw_data: Raw data to restore
            source_type: Source type
            
        Returns:
            Processing result with normalized data
        """
        if not self.restorer_consumer:
            return {"success": False, "error": "RestorerConsumer not available"}
        
        # Prepare event for pure consumer
        event = {
            "entity_id": entity_id,
            "raw_data": raw_data,
            "source_type": source_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Process through pure consumer (no I/O)
        result = self.restorer_consumer.process(event)
        
        # Emit event to bus if successful
        if result.success and self.bus:
            try:
                from core.governance.codex_hunters.events import Channels
                self.bus.emit(
                    Channels.RESTORED,
                    {
                        "entity_id": entity_id,
                        "quality_score": result.data.get("quality_score", 0.0),
                        "restored_at": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to emit restore event: {e}")
        
        return {
            "success": result.success,
            "entity_id": entity_id,
            "normalized_data": result.data.get("normalized_data", {}),
            "quality_score": result.data.get("quality_score", 0.0),
            "warnings": result.errors,
        }
    
    def process_bind(
        self,
        entity_id: str,
        normalized_data: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Process entity binding through LIVELLO 1 consumer.
        
        Args:
            entity_id: Entity identifier
            normalized_data: Normalized data to bind
            embedding: Vector embedding (optional)
            
        Returns:
            Processing result with storage status
        """
        if not self.binder_consumer:
            return {"success": False, "error": "BinderConsumer not available"}
        
        # Get config for table/collection names
        from core.governance.codex_hunters.domain import get_config as get_codex_config
        codex_config = get_codex_config()
        
        # Prepare event for pure consumer
        event = {
            "entity_id": entity_id,
            "normalized_data": normalized_data,
            "embedding": embedding,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Process through pure consumer (prepares payloads, no I/O)
        result = self.binder_consumer.process(event)
        
        # Now perform actual I/O through persistence adapter
        pg_success = False
        qdrant_success = False
        
        if result.success and result.data:
            # Store in PostgreSQL
            postgres_payload = result.data.get("postgres_payload", {})
            if postgres_payload:
                pg_success = self._persistence.store_entity(
                    table_name=codex_config.table.entities,
                    entity_id=entity_id,
                    data=postgres_payload
                )
            
            # Store in Qdrant (if embedding provided)
            qdrant_payload = result.data.get("qdrant_payload", {})
            if qdrant_payload and embedding:
                qdrant_success = self._persistence.store_embedding(
                    collection_name=codex_config.collection.embeddings,
                    entity_id=entity_id,
                    embedding=embedding,
                    payload=qdrant_payload
                )
        
        # Emit event to bus if any storage succeeded
        if (pg_success or qdrant_success) and self.bus:
            try:
                from core.governance.codex_hunters.events import Channels
                self.bus.emit(
                    Channels.BOUND,
                    {
                        "entity_id": entity_id,
                        "postgres_stored": pg_success,
                        "qdrant_stored": qdrant_success,
                        "bound_at": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to emit bind event: {e}")
        
        return {
            "success": pg_success or qdrant_success,
            "entity_id": entity_id,
            "postgres_stored": pg_success,
            "qdrant_stored": qdrant_success,
            "errors": result.errors,
        }
    
    # =========================================================================
    # Health Checks
    # =========================================================================
    
    def check_bus_health(self) -> bool:
        """Check StreamBus connection health."""
        if not self.bus:
            return False
        
        try:
            # Simple health check - ping Redis
            return self.bus.ping()
        except Exception:
            return False
    
    def get_consumers_status(self) -> Dict[str, str]:
        """Get status of all LIVELLO 1 consumers."""
        return {
            "tracker": "available" if self.tracker_consumer else "unavailable",
            "restorer": "available" if self.restorer_consumer else "unavailable",
            "binder": "available" if self.binder_consumer else "unavailable",
        }


# Singleton instance
_bus_adapter: Optional[BusAdapter] = None


def get_bus_adapter() -> BusAdapter:
    """Get or create the bus adapter singleton."""
    global _bus_adapter
    if _bus_adapter is None:
        _bus_adapter = BusAdapter()
    return _bus_adapter
