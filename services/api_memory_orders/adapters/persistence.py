"""
Memory Orders — Persistence Adapter

ONLY I/O point. All PostgresAgent, QdrantAgent, httpx calls here.
NO business logic. Delegate to LIVELLO 1 consumers.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — adapters)
"""

import httpx
from typing import Any

from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from core.governance.memory_orders.domain import ComponentHealth
from api_memory_orders.config import settings


class MemoryPersistence:
    """
    Persistence layer for Memory Orders.
    
    ALL database/HTTP I/O happens here.
    Pure domain logic lives in LIVELLO 1 consumers.
    """
    
    def __init__(self):
        self.pg = PostgresAgent()
        self.qdrant = QdrantAgent()

    @staticmethod
    def _scalar_from_row(row: dict[str, Any] | None) -> Any:
        """
        Extract first scalar value from PostgresAgent.fetch_one() dict row.

        PostgresAgent returns RealDict rows (dict), not tuple indexes.
        """
        if not row:
            return None
        return next(iter(row.values()))
    
    # ========================================
    #  Coherence I/O
    # ========================================
    
    def get_postgres_count(self, table: str, embedded_column: str = "embedded") -> int:
        """
        Count records in PostgreSQL with embedded=true.
        
        Args:
            table: Table name (e.g., 'entities')
            embedded_column: Column indicating embedded status
        
        Returns:
            Count of embedded records
        """
        query = f"SELECT COUNT(*) FROM {table} WHERE {embedded_column} = true;"
        result = self.pg.fetch_one(query)
        count = self._scalar_from_row(result)
        return int(count) if count is not None else 0
    
    def get_qdrant_count(self, collection: str) -> int:
        """
        Count points in Qdrant collection.
        
        Args:
            collection: Collection name (e.g., 'entities_embeddings')
        
        Returns:
            Count of points
        """
        try:
            # Use httpx to query Qdrant HTTP API
            response = httpx.get(
                f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections/{collection}",
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            return data["result"]["points_count"]
        except Exception as e:
            # Graceful degradation: return 0 on error
            return 0
    
    # ========================================
    #  Health Check I/O
    # ========================================
    
    def check_postgres_health(self) -> ComponentHealth:
        """Check PostgreSQL connection and metrics."""
        try:
            # Test query
            result = self.pg.fetch_one("SELECT 1;")
            ping = self._scalar_from_row(result)
            if ping != 1:
                return ComponentHealth(
                    component="archivarium",
                    status="unhealthy",
                    metrics=(),
                    error="Query returned unexpected result"
                )

            # Get entity counts
            entities_total = self._scalar_from_row(
                self.pg.fetch_one("SELECT COUNT(*) FROM entities;")
            )
            entities_embedded = self._scalar_from_row(
                self.pg.fetch_one("SELECT COUNT(*) FROM entities WHERE embedded = true;")
            )

            return ComponentHealth(
                component="archivarium",
                status="healthy",
                metrics=(
                    ("entities_total", int(entities_total or 0)),
                    ("entities_embedded", int(entities_embedded or 0)),
                ),
                error=None,
                response_time_ms=10.0  # Approximate
            )
        except Exception as e:
            return ComponentHealth(
                component="archivarium",
                status="unhealthy",
                metrics=(),
                error=str(e)
            )
    
    def check_qdrant_health(self) -> ComponentHealth:
        """Check Qdrant connection and metrics."""
        try:
            # Health endpoint
            response = httpx.get(
                f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/",
                timeout=5.0
            )
            response.raise_for_status()
            
            # Get collection count
            collection = settings.QDRANT_COLLECTION
            col_response = httpx.get(
                f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections/{collection}",
                timeout=5.0
            )
            col_response.raise_for_status()
            count = col_response.json()["result"]["points_count"]
            
            return ComponentHealth(
                component="mnemosyne",
                status="healthy",
                metrics=(
                    ("collection", collection),
                    ("points_count", count),
                ),
                error=None,
                response_time_ms=50.0  # Approximate
            )
        except Exception as e:
            return ComponentHealth(
                component="mnemosyne",
                status="unhealthy",
                metrics=(),
                error=str(e)
            )
    
    def check_embedding_api_health(self) -> ComponentHealth:
        """Check Embedding API health."""
        try:
            response = httpx.get(
                f"{settings.EMBEDDING_API_URL}/health",
                timeout=5.0
            )
            response.raise_for_status()
            
            return ComponentHealth(
                component="embedding_api",
                status="healthy",
                metrics=(("url", settings.EMBEDDING_API_URL),),
                error=None
            )
        except Exception as e:
            return ComponentHealth(
                component="embedding_api",
                status="unhealthy",
                metrics=(),
                error=str(e)
            )
    
    def check_babel_gardens_health(self) -> ComponentHealth:
        """Check Babel Gardens health."""
        try:
            response = httpx.get(
                f"{settings.BABEL_GARDENS_URL}/sacred-health",
                timeout=5.0
            )
            response.raise_for_status()
            
            return ComponentHealth(
                component="babel_gardens",
                status="healthy",
                metrics=(("url", settings.BABEL_GARDENS_URL),),
                error=None
            )
        except Exception as e:
            return ComponentHealth(
                component="babel_gardens",
                status="unhealthy",
                metrics=(),
                error=str(e)
            )
    
    def check_redis_health(self) -> ComponentHealth:
        """Check Redis connection."""
        try:
            import redis
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            client.close()
            
            return ComponentHealth(
                component="redis",
                status="healthy",
                metrics=(("url", settings.REDIS_URL),),
                error=None
            )
        except Exception as e:
            return ComponentHealth(
                component="redis",
                status="unhealthy",
                metrics=(),
                error=str(e)
            )
    
    # ========================================
    #  Sync I/O
    # ========================================
    
    def fetch_postgres_sync_data(self, table: str, limit: int = 1000) -> tuple[dict, ...]:
        """
        Fetch records from PostgreSQL for sync planning.
        
        Args:
            table: Table name
            limit: Max records to fetch
        
        Returns:
            Tuple of record dicts
        """
        query = f"SELECT id, embedded FROM {table} WHERE embedded = true LIMIT {limit};"
        rows = self.pg.fetch(query)
        return tuple(
            {
                "id": row.get("id"),
                "embedded": row.get("embedded", True),
            }
            for row in rows
        )
    
    def fetch_qdrant_sync_data(self, collection: str, limit: int = 1000) -> tuple[dict, ...]:
        """
        Fetch points from Qdrant for sync planning.
        
        Args:
            collection: Collection name
            limit: Max points to fetch
        
        Returns:
            Tuple of point dicts
        """
        # Simplified: return point IDs only
        # In real implementation, use qdrant_client.scroll()
        try:
            response = httpx.post(
                f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections/{collection}/points/scroll",
                json={"limit": limit},
                timeout=10.0
            )
            response.raise_for_status()
            points = response.json()["result"]["points"]
            return tuple({"id": p["id"]} for p in points)
        except Exception:
            return ()
    
