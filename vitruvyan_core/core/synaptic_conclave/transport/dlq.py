"""
Vitruvyan Core — Dead Letter Queue (DLQ) for Synaptic Conclave
================================================================

Provides structured DLQ handling for events that fail processing
after a configurable number of retries.

Architecture:
    Stream → Consumer Group → Consumer → FAIL N times → DLQ Stream
    
    DLQ stream name = "{prefix}:dlq" (e.g., "vitruvyan:dlq")
    Each DLQ entry contains:
    - Original event ID and stream
    - Failure reason
    - Retry count
    - Correlation ID
    - Idempotency key (prevents duplicate DLQ entries)
    - Timestamp

Configuration:
    DLQ_MAX_RETRIES: Max retries before DLQ routing (env var, default: 3)
    DLQ_STREAM_MAX_LEN: Max DLQ stream length (env var, default: 50000)

Author: Vitruvyan Core Team
Created: February 15, 2026
Status: LEVEL 1 transport extension — no business logic
"""

import os
import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DLQ_MAX_RETRIES = int(os.getenv("DLQ_MAX_RETRIES", "3"))
DLQ_STREAM_MAX_LEN = int(os.getenv("DLQ_STREAM_MAX_LEN", "50000"))
DLQ_STREAM_SUFFIX = "dlq"


@dataclass
class DLQEntry:
    """Structured Dead Letter Queue entry for audit trail."""
    original_stream: str
    original_event_id: str
    consumer_group: str
    consumer_name: str
    failure_reason: str
    retry_count: int
    correlation_id: str
    idempotency_key: str
    timestamp: str
    payload: Dict[str, Any]

    def to_redis_fields(self) -> Dict[str, str]:
        """Convert to Redis Streams field-value pairs."""
        return {
            "original_stream": self.original_stream,
            "original_event_id": self.original_event_id,
            "consumer_group": self.consumer_group,
            "consumer_name": self.consumer_name,
            "failure_reason": self.failure_reason,
            "retry_count": str(self.retry_count),
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp,
            "payload": json.dumps(self.payload),
        }

    @classmethod
    def from_redis(cls, data: Dict[bytes, bytes]) -> "DLQEntry":
        """Reconstruct from Redis XRANGE response."""
        decoded = {
            k.decode() if isinstance(k, bytes) else k:
            v.decode() if isinstance(v, bytes) else v
            for k, v in data.items()
        }
        return cls(
            original_stream=decoded.get("original_stream", ""),
            original_event_id=decoded.get("original_event_id", ""),
            consumer_group=decoded.get("consumer_group", ""),
            consumer_name=decoded.get("consumer_name", ""),
            failure_reason=decoded.get("failure_reason", ""),
            retry_count=int(decoded.get("retry_count", "0")),
            correlation_id=decoded.get("correlation_id", ""),
            idempotency_key=decoded.get("idempotency_key", ""),
            timestamp=decoded.get("timestamp", ""),
            payload=json.loads(decoded.get("payload", "{}")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_idempotency_key(
    stream: str, event_id: str, group: str
) -> str:
    """
    Generate a deterministic idempotency key for DLQ deduplication.

    Same (stream, event_id, group) always produces the same key.
    This prevents duplicate DLQ entries if move_to_dlq is called
    multiple times for the same event failure.
    """
    raw = f"{stream}:{event_id}:{group}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class DeadLetterQueue:
    """
    Dead Letter Queue manager for StreamBus.

    Tracks per-event retry counts and moves events to the DLQ stream
    after exceeding the retry threshold.

    The DLQ is a standard Redis Stream ({prefix}:dlq) that can be:
    - Queried for audit/inspection
    - Replayed for manual reprocessing
    - Trimmed for retention management

    Thread safety: Uses Redis atomic operations. No local mutable state
    beyond the Redis client reference.
    """

    def __init__(self, redis_client, prefix: str = "vitruvyan"):
        self._client = redis_client
        self._prefix = prefix
        self._dlq_stream = f"{prefix}:{DLQ_STREAM_SUFFIX}"
        self._max_retries = DLQ_MAX_RETRIES
        self._max_len = DLQ_STREAM_MAX_LEN

    @property
    def stream_name(self) -> str:
        """Return the DLQ stream name."""
        return self._dlq_stream

    def record_failure(
        self,
        stream: str,
        event_id: str,
        group: str,
        consumer: str,
        reason: str,
        correlation_id: str = "",
        payload: Dict[str, Any] = None,
    ) -> bool:
        """
        Record a processing failure for an event.

        Increments the retry counter in Redis. If the counter exceeds
        DLQ_MAX_RETRIES, the event is moved to the DLQ stream and
        acknowledged from the original stream.

        Args:
            stream: Original stream name
            event_id: Original event ID
            group: Consumer group name
            consumer: Consumer identifier
            reason: Human-readable failure description
            correlation_id: Optional correlation ID for tracing
            payload: Original event payload (for DLQ entry)

        Returns:
            True if event was moved to DLQ (max retries exceeded)
            False if event can still be retried
        """
        retry_key = f"{self._prefix}:retry:{stream}:{event_id}:{group}"

        try:
            # Atomic increment
            retry_count = self._client.incr(retry_key)
            # Set TTL on retry counter (24h) to prevent accumulation
            self._client.expire(retry_key, 86400)

            if retry_count >= self._max_retries:
                # Move to DLQ
                self._move_to_dlq(
                    stream=stream,
                    event_id=event_id,
                    group=group,
                    consumer=consumer,
                    reason=reason,
                    retry_count=retry_count,
                    correlation_id=correlation_id,
                    payload=payload or {},
                )
                # Clean up retry counter
                self._client.delete(retry_key)
                # ACK from original stream to prevent redelivery
                try:
                    self._client.xack(stream, group, event_id)
                except Exception:
                    pass  # Best-effort ACK
                return True

            logger.warning(
                "Event %s on %s failed (attempt %d/%d): %s",
                event_id, stream, retry_count, self._max_retries, reason
            )
            return False

        except Exception as e:
            logger.error("DLQ record_failure error: %s", e)
            return False

    def _move_to_dlq(
        self,
        stream: str,
        event_id: str,
        group: str,
        consumer: str,
        reason: str,
        retry_count: int,
        correlation_id: str,
        payload: Dict[str, Any],
    ) -> Optional[str]:
        """Write event to the DLQ stream with deduplication."""
        idempotency_key = generate_idempotency_key(stream, event_id, group)

        # Check for duplicate (idempotency)
        dup_check_key = f"{self._prefix}:dlq_idem:{idempotency_key}"
        if self._client.exists(dup_check_key):
            logger.debug("DLQ duplicate suppressed: %s", idempotency_key)
            return None

        entry = DLQEntry(
            original_stream=stream,
            original_event_id=event_id,
            consumer_group=group,
            consumer_name=consumer,
            failure_reason=reason,
            retry_count=retry_count,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            payload=payload,
        )

        try:
            dlq_id = self._client.xadd(
                self._dlq_stream,
                entry.to_redis_fields(),
                maxlen=self._max_len,
                approximate=True,
            )

            # Mark idempotency key (TTL 7 days)
            self._client.setex(dup_check_key, 604800, "1")

            dlq_id_str = dlq_id.decode() if isinstance(dlq_id, bytes) else dlq_id
            logger.error(
                "DLQ: Event %s moved from %s (group=%s, retries=%d, reason=%s) → %s:%s",
                event_id, stream, group, retry_count, reason,
                self._dlq_stream, dlq_id_str,
            )
            return dlq_id_str

        except Exception as e:
            logger.error("DLQ write failed: %s", e)
            return None

    def list_entries(
        self,
        start_id: str = "0",
        end_id: str = "+",
        count: int = 100,
    ) -> List[DLQEntry]:
        """
        List DLQ entries for audit/inspection.

        Returns:
            List of DLQEntry dataclasses
        """
        try:
            response = self._client.xrange(
                self._dlq_stream, min=start_id, max=end_id, count=count
            )
            entries = []
            for _event_id, data in response:
                entries.append(DLQEntry.from_redis(data))
            return entries
        except Exception as e:
            logger.error("DLQ list_entries error: %s", e)
            return []

    def count(self) -> int:
        """Return number of events in DLQ."""
        try:
            return self._client.xlen(self._dlq_stream)
        except Exception:
            return 0

    def reprocess(
        self,
        dlq_event_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Read a single DLQ entry for manual reprocessing.

        The caller is responsible for re-emitting to the original stream.

        Returns:
            DLQEntry as dict, or None
        """
        try:
            response = self._client.xrange(
                self._dlq_stream,
                min=dlq_event_id,
                max=dlq_event_id,
                count=1,
            )
            if response:
                _eid, data = response[0]
                return DLQEntry.from_redis(data).to_dict()
            return None
        except Exception as e:
            logger.error("DLQ reprocess error: %s", e)
            return None

    def purge(self) -> int:
        """
        Delete all entries in the DLQ stream.

        Returns:
            Number of entries deleted (stream length before purge)
        """
        try:
            length = self._client.xlen(self._dlq_stream)
            self._client.delete(self._dlq_stream)
            logger.info("DLQ purged: %d entries removed", length)
            return length
        except Exception as e:
            logger.error("DLQ purge error: %s", e)
            return 0

    def health(self) -> Dict[str, Any]:
        """DLQ health check."""
        try:
            return {
                "status": "healthy",
                "stream": self._dlq_stream,
                "entries": self.count(),
                "max_retries": self._max_retries,
                "max_len": self._max_len,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
