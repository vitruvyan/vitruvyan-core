"""
Persistence Adapter for Codex Hunters
=====================================

ONLY I/O point for database operations.
All PostgresAgent and QdrantAgent access must go through this adapter.
"""

import hashlib
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from ..config import get_config

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.]*$")


class PersistenceAdapter:
    """
    Centralizes all database I/O operations.
    
    LIVELLO 2 responsibility: This adapter owns all database connections.
    LIVELLO 1 consumers never touch databases directly.
    """
    
    def __init__(self):
        """Initialize persistence adapter with lazy agent loading."""
        self._pg_agent = None
        self._qdrant_agent = None
        self._config = get_config()

    def _safe_identifier(self, name: str) -> str:
        """Validate SQL identifier-like names coming from config/env."""
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"Invalid SQL identifier: {name}")
        return name
    
    @property
    def pg_agent(self):
        """Lazy-load PostgresAgent."""
        if self._pg_agent is None:
            try:
                from core.agents.postgres_agent import PostgresAgent
                self._pg_agent = PostgresAgent()
                logger.info("✅ PostgresAgent initialized")
            except ImportError as e:
                logger.warning(f"⚠️ PostgresAgent not available: {e}")
        return self._pg_agent
    
    @property
    def qdrant_agent(self):
        """Lazy-load QdrantAgent."""
        if self._qdrant_agent is None:
            try:
                from core.agents.qdrant_agent import QdrantAgent
                self._qdrant_agent = QdrantAgent()
                logger.info("✅ QdrantAgent initialized")
            except ImportError as e:
                logger.warning(f"⚠️ QdrantAgent not available: {e}")
        return self._qdrant_agent
    
    # =========================================================================
    # PostgreSQL Operations
    # =========================================================================
    
    def store_entity(
        self,
        table_name: str,
        entity_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store entity data in PostgreSQL.
        
        Args:
            table_name: Target table name (from config)
            entity_id: Unique entity identifier
            data: Entity data to store
            
        Returns:
            bool: True if successful
        """
        if not self.pg_agent:
            logger.error("PostgresAgent not available")
            return False
        
        try:
            # Use UPSERT pattern for idempotency
            import json
            self.pg_agent.execute(
                f"""
                INSERT INTO {table_name} (entity_id, data, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                ON CONFLICT (entity_id) 
                DO UPDATE SET data = %s, updated_at = NOW()
                """,
                (entity_id, json.dumps(data), json.dumps(data))
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store entity {entity_id}: {e}")
            return False
    
    def fetch_entity(
        self,
        table_name: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch entity data from PostgreSQL.
        
        Args:
            table_name: Source table name
            entity_id: Entity identifier
            
        Returns:
            Entity data or None if not found
        """
        if not self.pg_agent:
            return None
        
        try:
            rows = self.pg_agent.fetch(
                f"SELECT data FROM {table_name} WHERE entity_id = %s",
                (entity_id,)
            )
            if rows:
                return rows[0]["data"]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch entity {entity_id}: {e}")
            return None
    
    def check_database_health(self) -> bool:
        """Check PostgreSQL connection health."""
        if not self.pg_agent:
            return False
        
        try:
            rows = self.pg_agent.fetch("SELECT 1 AS ok")
            return rows and rows[0].get("ok") == 1
        except Exception:
            return False

    def list_source_registry(self) -> List[Dict[str, Any]]:
        """
        Load enabled source registry records from PostgreSQL.

        Returns:
            List of source rows ordered by DB default flag first.
        """
        if not self.pg_agent:
            return []

        try:
            table = self._safe_identifier(self._config.source_registry.registry_table)
            sql = f"""
                SELECT
                    source_key,
                    display_name,
                    source_type,
                    description,
                    rate_limit_per_minute,
                    timeout_seconds,
                    retry_attempts,
                    enabled,
                    config_json,
                    CASE
                        WHEN LOWER(COALESCE(config_json->>'default', 'false')) IN ('1', 'true', 'yes', 'on')
                        THEN TRUE
                        ELSE FALSE
                    END AS is_default
                FROM {table}
                WHERE enabled = TRUE
                ORDER BY
                    CASE
                        WHEN LOWER(COALESCE(config_json->>'default', 'false')) IN ('1', 'true', 'yes', 'on')
                        THEN 0
                        ELSE 1
                    END,
                    source_key ASC
            """
            return self.pg_agent.fetch(sql)
        except Exception as e:
            logger.warning("Failed to load source registry: %s", e)
            return []

    def list_source_topics(self, source_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load enabled source topics (e.g. subreddits) from PostgreSQL.

        Args:
            source_key: Optional source filter.
        """
        if not self.pg_agent:
            return []

        try:
            table = self._safe_identifier(self._config.source_registry.topics_table)
            base_sql = f"""
                SELECT
                    source_key,
                    topic_kind,
                    topic_value,
                    locale,
                    priority,
                    enabled,
                    metadata
                FROM {table}
                WHERE enabled = TRUE
            """
            params = None
            if source_key:
                base_sql += " AND source_key = %s"
                params = (source_key,)
            base_sql += " ORDER BY source_key ASC, priority ASC, topic_value ASC"
            return self.pg_agent.fetch(base_sql, params)
        except Exception as e:
            logger.warning("Failed to load source topics: %s", e)
            return []

    def get_default_source_key(self, preferred: Optional[str] = None) -> Optional[str]:
        """
        Resolve the default source key from DB configuration.

        Resolution order:
        1) explicit `preferred` if enabled
        2) env/config default source key if enabled
        3) source marked `config_json.default=true`
        4) first enabled source alphabetically
        """
        sources = self.list_source_registry()
        if not sources:
            return None

        by_key = {str(row["source_key"]): row for row in sources if row.get("source_key")}

        if preferred and preferred in by_key:
            return preferred

        configured_default = self._config.source_registry.default_source_key
        if configured_default and configured_default in by_key:
            return configured_default

        for row in sources:
            if row.get("is_default"):
                key = str(row.get("source_key") or "").strip()
                if key:
                    return key

        return str(sources[0].get("source_key") or "").strip() or None

    def get_source_registry_snapshot(self) -> Dict[str, Any]:
        """
        Return runtime view of source registry and topics for debugging/API.
        """
        sources = self.list_source_registry()
        topics = self.list_source_topics()
        topics_by_source: Dict[str, List[Dict[str, Any]]] = {}
        for topic in topics:
            key = str(topic.get("source_key") or "")
            if not key:
                continue
            topics_by_source.setdefault(key, []).append(topic)

        return {
            "sources": sources,
            "topics_by_source": topics_by_source,
            "default_source": self.get_default_source_key(),
        }
    
    # =========================================================================
    # Qdrant Operations
    # =========================================================================
    
    def store_embedding(
        self,
        collection_name: str,
        entity_id: str,
        embedding: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """
        Store embedding in Qdrant.
        
        Args:
            collection_name: Target collection (from config)
            entity_id: Unique entity identifier
            embedding: Vector embedding
            payload: Metadata payload
            
        Returns:
            bool: True if successful
        """
        if not self.qdrant_agent:
            logger.error("QdrantAgent not available")
            return False
        
        try:
            # Qdrant requires UUID or integer point IDs.
            # Derive a deterministic UUID-5 from the entity_id string.
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, entity_id))
            
            self.qdrant_agent.upsert(
                collection=collection_name,
                points=[{
                    "id": point_id,
                    "vector": embedding,
                    "payload": payload
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding for {entity_id}: {e}")
            return False
    
    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in Qdrant.
        
        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Maximum results
            
        Returns:
            List of similar entities with scores
        """
        if not self.qdrant_agent:
            return []
        
        try:
            results = self.qdrant_agent.search(
                collection=collection_name,
                query_vector=query_vector,
                top_k=limit
            )
            return results
        except Exception as e:
            logger.error(f"Failed to search similar: {e}")
            return []
    
    def check_qdrant_health(self) -> bool:
        """Check Qdrant connection health."""
        if not self.qdrant_agent:
            return False
        
        try:
            status = self.qdrant_agent.health()
            return status.get("status") == "ok"
        except Exception:
            return False


# Singleton instance
_persistence: Optional[PersistenceAdapter] = None


def get_persistence() -> PersistenceAdapter:
    """Get or create the persistence adapter singleton."""
    global _persistence
    if _persistence is None:
        _persistence = PersistenceAdapter()
    return _persistence
