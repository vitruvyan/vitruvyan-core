"""
Memory Orders — Persistence Adapter

ONLY I/O point. All PostgresAgent, QdrantAgent, httpx calls here.
NO business logic. Delegate to LIVELLO 1 consumers.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — adapters)
"""

import json
import logging
import time
import httpx
from typing import Any

from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from core.governance.memory_orders.domain import ComponentHealth
from api_memory_orders.config import settings
from api_memory_orders.adapters.pg_reader import PgReader
from api_memory_orders.adapters.qdrant_reader import QdrantReader

logger = logging.getLogger(__name__)


class MemoryPersistence:
    """
    Persistence layer for Memory Orders.
    
    ALL database/HTTP I/O happens here.
    Pure domain logic lives in LIVELLO 1 consumers.
    """
    
    def __init__(self):
        self.pg = PostgresAgent()
        self.qdrant = QdrantAgent()
        self.pg_reader = PgReader(self.pg)
        self.qdrant_reader = QdrantReader(self.qdrant)
        self._redis = None
        self._local_lock_store: dict[str, tuple[str, float]] = {}
        self._local_idempotency_store: dict[str, tuple[str, float]] = {}

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

    # ========================================
    #  Reconciliation I/O + Execution
    # ========================================

    def fetch_pg_reconciliation_snapshot(self, table: str, limit: int = 1000) -> tuple[dict[str, Any], ...]:
        """Canonical snapshot for reconciliation (PG is authoritative)."""
        return self.pg_reader.read_entities(
            table=table,
            limit=limit,
            metadata_columns=("embedded", "text", "content", "language"),
        )

    def fetch_qdrant_reconciliation_snapshot(self, collection: str, limit: int = 1000) -> tuple[dict[str, Any], ...]:
        """Derived snapshot for reconciliation."""
        return self.qdrant_reader.read_vectors(collection=collection, limit=limit)

    def _embedding_from_text(self, text: str) -> list[float] | None:
        """Generate vector via central embedding API."""
        try:
            response = httpx.post(
                f"{settings.EMBEDDING_API_URL}/v1/embeddings/create",
                json={"text": text},
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()
            vector = payload.get("embedding")
            if isinstance(vector, list) and vector:
                return vector
        except Exception:
            return None
        return None

    def execute_reconciliation_operations(
        self,
        operations: tuple[Any, ...],
        collection: str,
        mode: str,
    ) -> dict[str, int | str]:
        """Execute reconciliation operations on Qdrant."""
        attempted = len(operations)
        applied = 0
        skipped = 0
        failed = 0
        dead_lettered = 0
        retry_max = max(0, settings.MEMORY_RECONCILIATION_RETRY_MAX)
        retry_backoff_s = max(0, settings.MEMORY_RECONCILIATION_RETRY_BACKOFF_MS) / 1000.0

        for operation in operations:
            payload = dict(getattr(operation, "payload", ()))
            entity_id = str(payload.get("id") or getattr(operation, "entity_id", ""))
            operation_type = getattr(operation, "operation_type", "")

            try:
                success, was_skipped = self._execute_single_reconciliation_operation(
                    operation=operation,
                    collection=collection,
                )
                if was_skipped:
                    skipped += 1
                    continue
                if success:
                    applied += 1
                    continue

                retry_success = False
                for retry_index in range(retry_max):
                    if retry_backoff_s:
                        time.sleep(retry_backoff_s * (retry_index + 1))
                    retry_success, retry_skipped = self._execute_single_reconciliation_operation(
                        operation=operation,
                        collection=collection,
                    )
                    if retry_skipped:
                        skipped += 1
                        retry_success = True
                        break
                    if retry_success:
                        applied += 1
                        break

                if not retry_success:
                    failed += 1
                    if self.emit_dead_letter(
                        channel=settings.MEMORY_RECONCILIATION_DEAD_LETTER_CHANNEL,
                        payload={
                            "event": "memory.reconciliation.operation_failed",
                            "entity_id": entity_id,
                            "operation_type": operation_type,
                            "collection": collection,
                        },
                    ):
                        dead_lettered += 1
            except Exception as exc:
                failed += 1
                logger.error("Reconciliation operation failed unexpectedly: %s", exc)

        return {
            "attempted": attempted,
            "applied": applied,
            "skipped": skipped,
            "failed": failed,
            "mode": mode,
            "dead_lettered": dead_lettered,
        }

    def _execute_single_reconciliation_operation(self, operation: Any, collection: str) -> tuple[bool, bool]:
        """
        Execute one operation.
        Returns (success, skipped).
        """
        payload = dict(getattr(operation, "payload", ()))
        entity_id = str(payload.get("id") or getattr(operation, "entity_id", ""))
        operation_type = getattr(operation, "operation_type", "")

        if operation_type == "delete":
            if not entity_id:
                return False, True
            result = self.qdrant.delete_by_ids(collection, [entity_id])
            return bool(result.get("status") == "ok"), False

        if operation_type in {"insert", "update"}:
            metadata = payload.get("metadata", {})
            text = metadata.get("text") if isinstance(metadata, dict) else None
            if not text and isinstance(metadata, dict):
                text = metadata.get("content")
            if not text:
                return False, True

            vector = self._embedding_from_text(str(text))
            if not vector:
                return False, False

            qdrant_payload = {
                "id": entity_id,
                "version": payload.get("version"),
                "updated_at": payload.get("updated_at"),
                "language": metadata.get("language", "unknown") if isinstance(metadata, dict) else "unknown",
                "source": "memory_orders.reconciliation",
            }
            result = self.qdrant.upsert(
                collection=collection,
                points=[{"id": entity_id, "vector": vector, "payload": qdrant_payload}],
            )
            return bool(result.get("status") == "ok"), False

        return False, True

    def acquire_reconciliation_lock(self, lock_key: str, ttl_s: int) -> tuple[bool, str]:
        """Acquire distributed lock for reconciliation run."""
        token = str(time.time_ns())
        redis_client = self._redis_client()

        if redis_client:
            try:
                acquired = bool(redis_client.set(lock_key, token, nx=True, ex=max(1, ttl_s)))
                return acquired, token
            except Exception as exc:
                logger.warning("Redis lock unavailable, using local lock fallback: %s", exc)

        now = time.time()
        expires_at = now + max(1, ttl_s)
        existing = self._local_lock_store.get(lock_key)
        if existing and existing[1] > now:
            return False, token
        self._local_lock_store[lock_key] = (token, expires_at)
        return True, token

    def release_reconciliation_lock(self, lock_key: str, token: str) -> None:
        """Release distributed lock if owner token matches."""
        redis_client = self._redis_client()
        if redis_client:
            try:
                value = redis_client.get(lock_key)
                if value and str(value) == token:
                    redis_client.delete(lock_key)
            except Exception:
                pass

        existing = self._local_lock_store.get(lock_key)
        if existing and existing[0] == token:
            self._local_lock_store.pop(lock_key, None)

    def get_cached_idempotency_result(self, idempotency_key: str) -> dict[str, Any] | None:
        """Return cached result if idempotency key already completed."""
        if not idempotency_key:
            return None
        redis_client = self._redis_client()
        redis_key = f"memory:reconcile:idempotency:{idempotency_key}"

        if redis_client:
            try:
                payload = redis_client.get(redis_key)
                if payload:
                    return json.loads(payload)
            except Exception:
                pass

        now = time.time()
        local = self._local_idempotency_store.get(idempotency_key)
        if not local:
            return None
        payload, expires_at = local
        if expires_at < now:
            self._local_idempotency_store.pop(idempotency_key, None)
            return None
        try:
            return json.loads(payload)
        except Exception:
            return None

    def cache_idempotency_result(self, idempotency_key: str, result: dict[str, Any], ttl_s: int) -> None:
        """Cache final result for safe retries."""
        if not idempotency_key:
            return
        redis_client = self._redis_client()
        redis_key = f"memory:reconcile:idempotency:{idempotency_key}"
        payload = json.dumps(result)

        if redis_client:
            try:
                redis_client.set(redis_key, payload, ex=max(1, ttl_s))
                return
            except Exception:
                pass

        self._local_idempotency_store[idempotency_key] = (payload, time.time() + max(1, ttl_s))

    def emit_dead_letter(self, channel: str, payload: dict[str, Any]) -> bool:
        """Persist failed operation payload for manual replay."""
        redis_client = self._redis_client()
        data = json.dumps(payload, default=str)

        if redis_client:
            try:
                redis_client.xadd(channel, {"payload": data}, maxlen=10000, approximate=True)
                return True
            except Exception:
                return False

        logger.error("Dead-letter fallback (no redis): %s", data)
        return True

    def increment_metric(self, metric_name: str, value: float = 1.0) -> None:
        """Best-effort counter storage for reconciliation metrics."""
        redis_client = self._redis_client()
        if not redis_client:
            return
        try:
            redis_client.hincrbyfloat("memory:reconciliation:metrics", metric_name, value)
        except Exception:
            pass

    def _redis_client(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            return self._redis
        except Exception:
            self._redis = None
            return None
    
