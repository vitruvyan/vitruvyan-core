"""
Bus Adapter for Codex Hunters
=============================

Orchestrates LIVELLO 1 pure consumers with StreamBus for event communication.
This adapter bridges pure domain logic with infrastructure.
"""

import logging
import time
from dataclasses import replace
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
        self._known_sources: Dict[str, Dict[str, Any]] = {}
        self._topics_by_source: Dict[str, List[Dict[str, Any]]] = {}
        self._default_source: Optional[str] = None
        self._next_source_refresh_at: float = 0.0
        self._refresh_sources_from_registry(force=True)

    def _invalidate_consumers(self) -> None:
        """Force consumer re-creation after runtime config updates."""
        self._tracker_consumer = None
        self._restorer_consumer = None
        self._binder_consumer = None

    def _refresh_sources_from_registry(self, force: bool = False) -> None:
        """
        Sync Codex source configuration from DB source registry.

        This keeps LIVELLO 1 agnostic while moving source choices to DB.
        """
        now = time.monotonic()
        interval = max(5, int(self._config.source_registry.refresh_interval_seconds))
        if not force and now < self._next_source_refresh_at:
            return
        self._next_source_refresh_at = now + interval

        registry_rows = self._persistence.list_source_registry()
        if not registry_rows:
            if force:
                logger.warning("No enabled sources found in source registry; keeping current CodexConfig")
            return

        try:
            from core.governance.codex_hunters.domain import (
                SourceConfig,
                get_config as get_codex_config,
                set_config as set_codex_config,
            )

            source_map = {}
            source_snapshot: Dict[str, Dict[str, Any]] = {}
            for row in registry_rows:
                source_key = str(row.get("source_key") or "").strip()
                if not source_key:
                    continue

                config = SourceConfig(
                    name=source_key,
                    rate_limit_per_minute=int(row.get("rate_limit_per_minute") or 60),
                    timeout_seconds=int(row.get("timeout_seconds") or 30),
                    retry_attempts=int(row.get("retry_attempts") or 3),
                    description=str(row.get("description") or row.get("display_name") or ""),
                    enabled=bool(row.get("enabled", True)),
                )
                source_map[source_key] = config
                source_snapshot[source_key] = {
                    "source_key": source_key,
                    "display_name": row.get("display_name"),
                    "source_type": row.get("source_type"),
                    "description": row.get("description"),
                    "rate_limit_per_minute": config.rate_limit_per_minute,
                    "timeout_seconds": config.timeout_seconds,
                    "retry_attempts": config.retry_attempts,
                    "enabled": config.enabled,
                    "is_default": bool(row.get("is_default", False)),
                    "config_json": row.get("config_json") or {},
                }

            if not source_map:
                logger.warning("Source registry query returned rows but no usable source_key entries")
                return

            current_config = get_codex_config()
            current_signature = {
                key: (
                    cfg.rate_limit_per_minute,
                    cfg.timeout_seconds,
                    cfg.retry_attempts,
                    cfg.description,
                    cfg.enabled,
                )
                for key, cfg in current_config.sources.items()
            }
            new_signature = {
                key: (
                    cfg.rate_limit_per_minute,
                    cfg.timeout_seconds,
                    cfg.retry_attempts,
                    cfg.description,
                    cfg.enabled,
                )
                for key, cfg in source_map.items()
            }

            if new_signature != current_signature:
                updated_config = replace(current_config, sources=source_map)
                set_codex_config(updated_config)
                self._invalidate_consumers()
                logger.info(
                    "Source registry applied: %d enabled sources (%s)",
                    len(source_map),
                    ", ".join(sorted(source_map.keys())),
                )

            topics = self._persistence.list_source_topics()
            topics_by_source: Dict[str, List[Dict[str, Any]]] = {}
            for topic in topics:
                source_key = str(topic.get("source_key") or "")
                if not source_key:
                    continue
                topics_by_source.setdefault(source_key, []).append(topic)

            self._known_sources = source_snapshot
            self._topics_by_source = topics_by_source
            self._default_source = self._persistence.get_default_source_key()
        except Exception as e:
            logger.warning("Failed to apply DB source registry to CodexConfig: %s", e)

    def resolve_source(self, source: Optional[str]) -> str:
        """
        Resolve and validate a source key using DB-backed source registry.
        """
        self._refresh_sources_from_registry(force=False)
        candidate = str(source or "").strip()

        if candidate:
            if candidate in self._known_sources:
                return candidate

            # Allow one forced refresh in case registry changed recently.
            self._refresh_sources_from_registry(force=True)
            if candidate in self._known_sources:
                return candidate

            known = sorted(self._known_sources.keys())
            raise ValueError(f"Unknown source '{candidate}'. Enabled sources: {known}")

        if self._default_source and self._default_source in self._known_sources:
            return self._default_source

        fallback = self._persistence.get_default_source_key()
        if fallback and fallback in self._known_sources:
            self._default_source = fallback
            return fallback

        if self._known_sources:
            first = sorted(self._known_sources.keys())[0]
            self._default_source = first
            return first

        raise ValueError("No enabled source configured in codex_source_registry")

    def get_source_registry_snapshot(self) -> Dict[str, Any]:
        """Expose current DB-backed source registry state for debugging."""
        self._refresh_sources_from_registry(force=False)
        return {
            "default_source": self._default_source,
            "sources": [self._known_sources[key] for key in sorted(self._known_sources.keys())],
            "topics_by_source": self._topics_by_source,
        }
    
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
        self._refresh_sources_from_registry(force=False)
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
        self._refresh_sources_from_registry(force=False)
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
        self._refresh_sources_from_registry(force=False)
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
        source: Optional[str],
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process entity discovery through LIVELLO 1 consumer.
        
        Args:
            entity_id: Unique entity identifier
            source: Optional source identifier (resolved from DB if omitted)
            raw_data: Raw data from source
            metadata: Additional metadata
            
        Returns:
            Processing result
        """
        if not self.tracker_consumer:
            return {"success": False, "error": "TrackerConsumer not available"}

        resolved_source = self.resolve_source(source)
        
        # Prepare event for pure consumer
        event = {
            "entity_id": entity_id,
            "source": resolved_source,
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
                    Channels.entity_discovered(),
                    {
                        "entity_id": entity_id,
                        "source": resolved_source,
                        "discovered_at": datetime.utcnow().isoformat(),
                        "data": result.data,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to emit discovery event: {e}")
        
        return {
            "success": result.success,
            "entity_id": entity_id,
            "data": result.data,
            "errors": result.errors,
        }
    
    def process_restore(
        self,
        entity_id: str,
        raw_data: Dict[str, Any],
        source: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process data restoration through LIVELLO 1 consumer.
        
        Args:
            entity_id: Entity identifier
            raw_data: Raw data to restore
            source: Optional source identifier
            
        Returns:
            Processing result with normalized data
        """
        if not self.restorer_consumer:
            return {"success": False, "error": "RestorerConsumer not available"}

        resolved_source = self.resolve_source(source)
        
        # Prepare event for pure consumer (RestorerConsumer expects 'entity' key)
        from core.governance.codex_hunters.domain.entities import DiscoveredEntity
        from datetime import datetime as dt
        
        discovered_entity = DiscoveredEntity(
            entity_id=entity_id,
            source=resolved_source,
            discovered_at=dt.utcnow(),
            raw_data=raw_data,
            metadata={},
        )
        
        event = {
            "entity": discovered_entity,
        }
        
        # Process through pure consumer (no I/O)
        result = self.restorer_consumer.process(event)
        
        # Emit event to bus if successful
        if result.success and self.bus:
            try:
                from core.governance.codex_hunters.events import Channels
                self.bus.emit(
                    Channels.with_prefix(Channels.ENTITY_RESTORED),
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
        # Binder expects {"entity": {...}, "embedding": [...]}
        event = {
            "entity": {
                "entity_id": entity_id,
                "source": normalized_data.get("source", "api"),
                "normalized_data": normalized_data,
                "quality_score": normalized_data.get("quality_score", 1.0),
            },
            "embedding": embedding,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Process through pure consumer (domain-agnostic, no I/O)
        result = self.binder_consumer.process(event)
        
        if not result.success:
            logger.warning(f"Binder consumer failed for {entity_id}: {result.errors}")
        
        # Now perform actual I/O through persistence adapter
        pg_success = False
        qdrant_success = False
        dedupe_key = None
        
        if result.success and result.data:
            # Get domain-agnostic data from Binder
            normalized_data_out = result.data.get("normalized_data", normalized_data)
            embedding_out = result.data.get("embedding", embedding)
            quality_score = result.data.get("quality_score", 1.0)
            dedupe_key = result.data.get("dedupe_key")
            
            # ── AUTO-EMBED ──────────────────────────────────────────────
            # If no embedding was provided, generate one via the embedding
            # service.  We build a searchable text string from the
            # normalized_data and delegate to persistence.generate_embedding.
            if not embedding_out:
                embed_text = self._build_embed_text(entity_id, normalized_data_out)
                if embed_text:
                    embedding_out = self._persistence.generate_embedding(embed_text)
                    if embedding_out:
                        logger.info(
                            "Auto-embedding generated for %s (dim=%d)",
                            entity_id, len(embedding_out),
                        )
            
            # LIVELLO 2 responsibility: Construct provider-specific payloads
            # PostgreSQL payload (JSONB storage)
            postgres_payload = {
                "entity_id": entity_id,
                "data": normalized_data_out,
                "quality_score": quality_score,
                "dedupe_key": dedupe_key,
                "bound_at": datetime.utcnow().isoformat(),
            }
            
            # Store in PostgreSQL
            pg_success = self._persistence.store_entity(
                table_name=codex_config.entity_table.name,
                entity_id=entity_id,
                data=postgres_payload
            )
            
            # Store in Qdrant (if embedding provided)
            if embedding_out:
                # LIVELLO 2 responsibility: Construct Qdrant point payload
                qdrant_payload = {
                    "entity_id": entity_id,
                    "bound_at": datetime.utcnow().isoformat(),
                    **self._extract_searchable_fields(normalized_data_out)
                }
                
                qdrant_success = self._persistence.store_embedding(
                    collection_name=codex_config.embedding_collection.name,
                    entity_id=entity_id,
                    embedding=embedding_out,
                    payload=qdrant_payload
                )
        
        # Emit event to bus if any storage succeeded
        if (pg_success or qdrant_success) and self.bus:
            try:
                from core.governance.codex_hunters.events import Channels
                self.bus.emit(
                    Channels.entity_bound(),
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
            "dedupe_key": dedupe_key,
        }
    
    def _build_embed_text(self, entity_id: str, data: Dict[str, Any], max_len: int = 2000) -> str:
        """
        Build a single text string from normalized_data suitable for embedding.

        Heuristic: join all string-valued fields (title, text, description,
        normalized_text, etc.) up to *max_len* characters.
        """
        parts: List[str] = []

        # Prefer specific keys first (order matters for truncation)
        priority_keys = [
            "title", "normalized_text", "text", "description",
            "selftext", "content", "notes", "summary",
        ]
        seen = set()
        for key in priority_keys:
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val.strip())
                seen.add(key)

        # Then any remaining string fields
        for key, val in data.items():
            if key in seen:
                continue
            if isinstance(val, str) and len(val) > 10:
                parts.append(val.strip())

        joined = " ".join(parts)[:max_len]
        return joined if joined.strip() else entity_id

    def _extract_searchable_fields(self, data: Dict[str, Any], max_fields: int = 10) -> Dict[str, Any]:
        """
        Extract searchable fields from normalized data for Qdrant payload.
        LIVELLO 2 responsibility (provider-specific extraction).
        """
        searchable = {}
        for k, v in list(data.items())[:max_fields]:
            if isinstance(v, (str, int, float, bool)):
                searchable[k] = v
        return searchable
    
    # =========================================================================
    # Health Checks
    # =========================================================================
    
    def check_bus_health(self) -> bool:
        """Check StreamBus connection health."""
        if not self.bus:
            return False
        
        try:
            # StreamBus exposes raw redis client for transport-level checks.
            return bool(self.bus.client.ping())
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
