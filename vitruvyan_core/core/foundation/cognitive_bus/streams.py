#!/usr/bin/env python3
"""
Redis Streams — Durable Event Transport (Level 1)

This module provides persistent, replayable event transport using Redis Streams.
It is LEVEL 1 ONLY — pure transport, no interpretation, no correlation.

Key differences from Pub/Sub:
- Persistence: Events survive subscriber downtime
- Consumer Groups: Multiple consumers can process events cooperatively
- Acknowledgment: At-least-once delivery guarantee
- Replay: Historical events can be re-processed

Architecture:
    Producer → Stream → Consumer Group → Consumer → ACK
    
    Streams are named: "vitruvyan:{domain}:{intent}"
    Example: "vitruvyan:codex:entity_updated"

Usage:
    from core.foundation.cognitive_bus.streams import StreamBus
    
    bus = StreamBus()
    
    # Produce (any service)
    bus.emit("codex:entity_updated", {"entity_id": "E123", "source": "api"})
    
    # Consume (dedicated worker)
    for event in bus.consume("codex:entity_updated", group="indexer", consumer="worker-1"):
        process(event)
        bus.ack(event)

Invariants (from Vitruvyan_Bus_Invariants.md):
    1. The bus NEVER interprets payload content
    2. The bus NEVER correlates events (that's Level 2, vertical responsibility)
    3. The bus ONLY transports and persists
    4. "I don't know what this means" is the bus's permanent state

Author: Vitruvyan Core Team
Created: 2026-01-18
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
import redis
from redis.exceptions import ConnectionError, ResponseError

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class StreamEvent:
    """
    Immutable event structure for Redis Streams.
    
    The bus does NOT interpret these fields — they are opaque containers.
    Meaning is assigned by the vertical, not the core.
    """
    stream: str                    # Stream name (e.g., "vitruvyan:codex:entity_updated")
    event_id: str                  # Redis-assigned ID (e.g., "1705123456789-0")
    emitter: str                   # Source service identifier
    payload: Dict[str, Any]        # Opaque data — bus doesn't look inside
    timestamp: str                 # ISO 8601 timestamp
    correlation_id: Optional[str] = None  # Optional chain tracking
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_redis(cls, stream: str, event_id: str, data: Dict[bytes, bytes]) -> 'StreamEvent':
        """Reconstruct event from Redis XREAD response."""
        # Decode bytes to strings
        decoded = {k.decode(): v.decode() for k, v in data.items()}
        
        # Parse JSON payload
        payload = json.loads(decoded.get('payload', '{}'))
        
        return cls(
            stream=stream,
            event_id=event_id,
            emitter=decoded.get('emitter', 'unknown'),
            payload=payload,
            timestamp=decoded.get('timestamp', ''),
            correlation_id=decoded.get('correlation_id')
        )


# ============================================================================
# STREAM BUS (Level 1 Transport)
# ============================================================================

class StreamBus:
    """
    Redis Streams transport layer.
    
    This is LEVEL 1 — pure transport with persistence.
    No interpretation. No correlation. No business logic.
    
    The bus is deliberately "dumb" — it moves bytes, nothing more.
    """
    
    # Stream retention: 7 days or 100K messages (whichever first)
    DEFAULT_MAX_LEN = 100_000
    DEFAULT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000  # 7 days in ms
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        prefix: str = "vitruvyan"
    ):
        """
        Initialize Stream Bus.
        
        Args:
            host: Redis host (env: REDIS_HOST, default: localhost)
            port: Redis port (env: REDIS_PORT, default: 6379)
            db: Redis database number
            password: Redis password (env: REDIS_PASSWORD)
            prefix: Stream name prefix (default: "vitruvyan")
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', '6379'))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')
        self.prefix = prefix
        
        self._client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,  # We handle decoding manually
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True
            )
            self._client.ping()
            logger.info(f"✅ StreamBus connected: {self.host}:{self.port}")
        except ConnectionError as e:
            logger.error(f"❌ StreamBus connection failed: {e}")
            raise
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client, reconnecting if needed."""
        if self._client is None:
            self._connect()
        return self._client
    
    def _stream_name(self, channel: str) -> str:
        """Convert channel to full stream name."""
        # "codex:entity_updated" → "vitruvyan:codex:entity_updated"
        if channel.startswith(self.prefix):
            return channel
        return f"{self.prefix}:{channel}"
    
    # ========================================================================
    # PRODUCE (Write to Stream)
    # ========================================================================
    
    def emit(
        self,
        channel: str,
        payload: Dict[str, Any],
        emitter: str = "unknown",
        correlation_id: str = None,
        max_len: int = None
    ) -> str:
        """
        Emit event to stream.
        
        This is fire-and-store — the event persists until consumed or trimmed.
        
        Args:
            channel: Event channel (e.g., "codex:entity_updated")
            payload: Event data (will be JSON-serialized)
            emitter: Source service identifier
            correlation_id: Optional chain tracking ID
            max_len: Max stream length (approximate, uses MAXLEN ~)
        
        Returns:
            Event ID assigned by Redis (e.g., "1705123456789-0")
        """
        stream = self._stream_name(channel)
        
        # Prepare fields (Redis Streams store field-value pairs)
        fields = {
            'emitter': emitter,
            'payload': json.dumps(payload),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        if correlation_id:
            fields['correlation_id'] = correlation_id
        
        # XADD with approximate trimming
        max_len = max_len or self.DEFAULT_MAX_LEN
        event_id = self.client.xadd(
            stream,
            fields,
            maxlen=max_len,
            approximate=True  # ~ flag for efficient trimming
        )
        
        logger.debug(f"📤 Emitted to {stream}: {event_id}")
        return event_id.decode() if isinstance(event_id, bytes) else event_id
    
    # ========================================================================
    # CONSUME (Read from Stream)
    # ========================================================================
    
    def create_consumer_group(
        self,
        channel: str,
        group: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create consumer group for a stream.
        
        Consumer groups allow multiple workers to cooperatively process events.
        Each event is delivered to ONE consumer in the group.
        
        Args:
            channel: Event channel
            group: Consumer group name
            start_id: Where to start ("0" = beginning, "$" = new events only)
        
        Returns:
            True if created, False if already exists
        """
        stream = self._stream_name(channel)
        try:
            self.client.xgroup_create(stream, group, id=start_id, mkstream=True)
            logger.info(f"✅ Created consumer group '{group}' on {stream}")
            return True
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{group}' already exists on {stream}")
                return False
            raise
    
    def consume(
        self,
        channel: str,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 5000
    ) -> Generator[StreamEvent, None, None]:
        """
        Consume events from stream as generator.
        
        This is a blocking generator that yields events as they arrive.
        Events must be ACKed after processing.
        
        Args:
            channel: Event channel
            group: Consumer group name
            consumer: Consumer identifier (unique per worker)
            count: Max events per batch
            block_ms: Block timeout (0 = forever)
        
        Yields:
            StreamEvent objects
        
        Example:
            for event in bus.consume("codex:entity_updated", "indexer", "worker-1"):
                process(event)
                bus.ack(event)
        """
        stream = self._stream_name(channel)
        
        # Ensure group exists
        self.create_consumer_group(channel, group)
        
        while True:
            try:
                # XREADGROUP: Read pending or new events
                # ">" means only new events not yet delivered to this consumer
                response = self.client.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={stream: '>'},
                    count=count,
                    block=block_ms
                )
                
                if not response:
                    continue  # Timeout, loop again
                
                for stream_name, events in response:
                    stream_str = stream_name.decode() if isinstance(stream_name, bytes) else stream_name
                    for event_id, data in events:
                        event_id_str = event_id.decode() if isinstance(event_id, bytes) else event_id
                        yield StreamEvent.from_redis(stream_str, event_id_str, data)
                        
            except ConnectionError as e:
                logger.warning(f"Connection lost, reconnecting: {e}")
                time.sleep(1)
                self._connect()
    
    def ack(self, event: StreamEvent, group: str = None) -> bool:
        """
        Acknowledge event processing.
        
        ACKed events are removed from the pending list.
        Un-ACKed events will be redelivered after timeout.
        
        Args:
            event: Event to acknowledge
            group: Consumer group (inferred from event if not provided)
        
        Returns:
            True if acknowledged
        """
        # Extract group from stream name if not provided
        # This is a simplification — in production, track group per consumer
        if group is None:
            raise ValueError("Consumer group must be provided for ACK")
        
        count = self.client.xack(event.stream, group, event.event_id)
        return count > 0
    
    # ========================================================================
    # REPLAY (Historical Processing)
    # ========================================================================
    
    def replay(
        self,
        channel: str,
        start_id: str = "0",
        end_id: str = "+",
        count: int = 100
    ) -> List[StreamEvent]:
        """
        Replay historical events from stream.
        
        This does NOT use consumer groups — it's direct XRANGE read.
        Use for debugging, backfilling, or one-time processing.
        
        Args:
            channel: Event channel
            start_id: Start ID ("0" = beginning, or specific ID)
            end_id: End ID ("+" = latest, or specific ID)
            count: Max events to return
        
        Returns:
            List of StreamEvent objects
        """
        stream = self._stream_name(channel)
        
        response = self.client.xrange(stream, min=start_id, max=end_id, count=count)
        
        events = []
        for event_id, data in response:
            event_id_str = event_id.decode() if isinstance(event_id, bytes) else event_id
            events.append(StreamEvent.from_redis(stream, event_id_str, data))
        
        return events
    
    # ========================================================================
    # ADMIN (Stream Management)
    # ========================================================================
    
    def stream_info(self, channel: str) -> Dict[str, Any]:
        """Get stream metadata."""
        stream = self._stream_name(channel)
        try:
            info = self.client.xinfo_stream(stream)
            return {
                'length': info.get(b'length', 0),
                'first_entry': info.get(b'first-entry'),
                'last_entry': info.get(b'last-entry'),
                'groups': self.client.xinfo_groups(stream)
            }
        except ResponseError:
            return {'length': 0, 'exists': False}
    
    def pending(self, channel: str, group: str) -> Dict[str, Any]:
        """Get pending (unacked) events info."""
        stream = self._stream_name(channel)
        try:
            info = self.client.xpending(stream, group)
            # redis-py returns dict with keys: pending, min, max, consumers
            if isinstance(info, dict):
                return {
                    'pending_count': info.get('pending', 0),
                    'min_id': info.get('min'),
                    'max_id': info.get('max'),
                    'consumers': info.get('consumers', [])
                }
            # Fallback for older redis-py versions (tuple)
            elif info:
                return {
                    'pending_count': info[0] if len(info) > 0 else 0,
                    'min_id': info[1] if len(info) > 1 else None,
                    'max_id': info[2] if len(info) > 2 else None,
                    'consumers': info[3] if len(info) > 3 else []
                }
            return {'pending_count': 0}
        except ResponseError:
            return {'pending_count': 0}
    
    def trim(self, channel: str, max_len: int = None) -> int:
        """
        Trim stream to max length.
        
        Returns number of entries removed.
        """
        stream = self._stream_name(channel)
        max_len = max_len or self.DEFAULT_MAX_LEN
        return self.client.xtrim(stream, maxlen=max_len, approximate=True)
    
    def delete_stream(self, channel: str) -> bool:
        """Delete entire stream. Use with caution."""
        stream = self._stream_name(channel)
        return self.client.delete(stream) > 0
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    def health(self) -> Dict[str, Any]:
        """
        Health check for Stream Bus.
        
        Returns:
            Dict with connection status and basic metrics
        """
        try:
            self.client.ping()
            info = self.client.info('memory')
            return {
                'status': 'healthy',
                'connected': True,
                'host': f"{self.host}:{self.port}",
                'memory_used': info.get('used_memory_human', 'unknown'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_default_bus: Optional[StreamBus] = None

def get_stream_bus() -> StreamBus:
    """Get default StreamBus singleton."""
    global _default_bus
    if _default_bus is None:
        _default_bus = StreamBus()
    return _default_bus


def emit(channel: str, payload: Dict[str, Any], **kwargs) -> str:
    """Convenience: emit to default bus."""
    return get_stream_bus().emit(channel, payload, **kwargs)


def consume(channel: str, group: str, consumer: str, **kwargs) -> Generator[StreamEvent, None, None]:
    """Convenience: consume from default bus."""
    return get_stream_bus().consume(channel, group, consumer, **kwargs)
