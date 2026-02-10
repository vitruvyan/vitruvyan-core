"""
Persistence Adapter for Pattern Weavers
=======================================

ONLY I/O point for database operations.
All PostgresAgent and QdrantAgent access goes through this adapter.
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
        """Initialize with lazy agent loading."""
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
    # Qdrant Operations
    # =========================================================================
    
    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.4,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Qdrant.
        
        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Maximum results
            score_threshold: Minimum similarity score
            
        Returns:
            List of results with score and payload
        """
        if not self.qdrant_agent:
            logger.error("QdrantAgent not available")
            return []
        
        try:
            results = self.qdrant_agent.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            return results
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []
    
    def upsert_taxonomy(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
    ) -> bool:
        """
        Upsert taxonomy entries to Qdrant.
        
        Args:
            collection_name: Target collection
            points: List of {id, vector, payload}
            
        Returns:
            bool: Success status
        """
        if not self.qdrant_agent:
            return False
        
        try:
            self.qdrant_agent.upsert(
                collection_name=collection_name,
                points=points,
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            return False
    
    def check_qdrant_health(self) -> bool:
        """Check Qdrant connection health."""
        if not self.qdrant_agent:
            return False
        try:
            self.qdrant_agent.list_collections()
            return True
        except Exception:
            return False
    
    # =========================================================================
    # PostgreSQL Operations
    # =========================================================================
    
    def log_weave(
        self,
        user_id: str,
        query_text: str,
        result: Dict[str, Any],
    ) -> bool:
        """
        Log weave operation to PostgreSQL.
        
        Args:
            user_id: User identifier
            query_text: Original query
            result: Weave result
            
        Returns:
            bool: Success status
        """
        if not self.pg_agent:
            return False
        
        try:
            import json
            self.pg_agent.execute(
                """
                INSERT INTO weave_logs (user_id, query_text, result, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (user_id, query_text, json.dumps(result)),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log weave: {e}")
            return False
    
    def check_database_health(self) -> bool:
        """Check PostgreSQL connection health."""
        if not self.pg_agent:
            return False
        try:
            rows = self.pg_agent.fetch("SELECT 1 AS ok")
            return rows and rows[0].get("ok") == 1
        except Exception:
            return False


# Singleton
_persistence: Optional[PersistenceAdapter] = None


def get_persistence() -> PersistenceAdapter:
    """Get or create persistence adapter singleton."""
    global _persistence
    if _persistence is None:
        _persistence = PersistenceAdapter()
    return _persistence
