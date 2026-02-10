"""
Persistence Adapter for Codex Hunters
=====================================

ONLY I/O point for database operations.
All PostgresAgent and QdrantAgent access must go through this adapter.
"""

import logging
from typing import Any, Dict, List, Optional

from ..config import get_config

logger = logging.getLogger(__name__)


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
            self.qdrant_agent.upsert(
                collection_name=collection_name,
                points=[{
                    "id": entity_id,
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
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
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
            # Simple health check - list collections
            self.qdrant_agent.list_collections()
            return True
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
