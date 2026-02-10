"""
Persistence Adapter for Babel Gardens
======================================

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
            except Exception as e:
                logger.warning(f"⚠️ PostgresAgent connection failed: {e}")
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
            except Exception as e:
                logger.warning(f"⚠️ QdrantAgent connection failed: {e}")
        return self._qdrant_agent
    
    # =========================================================================
    # Qdrant Operations
    # =========================================================================
    
    def store_embedding(
        self,
        collection: str,
        embedding_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> bool:
        """Store embedding in Qdrant."""
        if not self.qdrant_agent:
            return False
        
        try:
            self.qdrant_agent.upsert(
                collection_name=collection,
                points=[{
                    "id": embedding_id,
                    "vector": vector,
                    "payload": payload,
                }],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            return False
    
    def search_similar(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings."""
        if not self.qdrant_agent:
            return []
        
        try:
            return self.qdrant_agent.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []
    
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
    
    def log_request(
        self,
        request_type: str,
        text: str,
        result: Dict[str, Any],
    ) -> bool:
        """Log request to PostgreSQL."""
        if not self.pg_agent:
            return False
        
        try:
            import json
            self.pg_agent.execute(
                """
                INSERT INTO babel_requests (request_type, text_hash, result, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (request_type, hash(text) % (10 ** 10), json.dumps(result)),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
            return False
    
    def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Get cached embedding from database."""
        if not self.pg_agent:
            return None
        
        try:
            rows = self.pg_agent.fetch(
                """
                SELECT embedding FROM babel_cache 
                WHERE text_hash = %s AND created_at > NOW() - INTERVAL '7 days'
                LIMIT 1
                """,
                (text_hash,),
            )
            if rows:
                return rows[0].get("embedding")
            return None
        except Exception:
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


# Singleton
_persistence: Optional[PersistenceAdapter] = None


def get_persistence() -> PersistenceAdapter:
    """Get or create persistence adapter singleton."""
    global _persistence
    if _persistence is None:
        _persistence = PersistenceAdapter()
    return _persistence
