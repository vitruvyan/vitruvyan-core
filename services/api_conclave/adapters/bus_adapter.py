"""
Synaptic Conclave — Bus Adapter (LIVELLO 2)

Bridges HTTP requests to Redis Streams (LIVELLO 1 transport).

The adapter does NOT contain business logic. It:
1. Initializes StreamBus connection
2. Delegates emit/health/replay/info operations to StreamBus
3. Returns raw results as dicts

Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_schema import EVENT_ROUTING_MAP
from api_conclave.config import settings
from api_conclave.monitoring.metrics import redis_connection_status

logger = logging.getLogger("Conclave.BusAdapter")


class ConclaveBusAdapter:
    """
    Bridges HTTP layer to Redis Streams (StreamBus).

    Instantiate once at service startup. Thread-safe (StreamBus is thread-safe).

    Usage:
        adapter = ConclaveBusAdapter()
        event_id = adapter.emit("codex.discovery.mapped", {"entity": "X"})
    """

    def __init__(self):
        self.bus: Optional[StreamBus] = None
        self._started_at: str = datetime.utcnow().isoformat() + "Z"
        self._heartbeat_count: int = 0
        self._connect()

    def _connect(self):
        """Establish StreamBus connection."""
        try:
            self.bus = StreamBus(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
            )
            redis_connection_status.set(1)
            logger.info(
                "StreamBus initialized: %s:%s",
                settings.REDIS_HOST,
                settings.REDIS_PORT,
            )
        except Exception as exc:
            self.bus = None
            redis_connection_status.set(0)
            logger.error("StreamBus initialization failed: %s", exc)

    @property
    def is_connected(self) -> bool:
        return self.bus is not None

    # ── Emit ─────────────────────────────────────────────────

    def emit(self, channel: str, data: Dict[str, Any], emitter: str = "conclave.api") -> str:
        """
        Emit event to Redis Streams.

        Args:
            channel: dot-notation stream name (e.g. 'codex.discovery.mapped')
            data: arbitrary JSON-serializable payload
            emitter: source identifier

        Returns:
            Redis event ID (e.g. '1770569658797-0')
        """
        if not self.bus:
            raise RuntimeError("StreamBus not initialized")
        return self.bus.emit(channel=channel, payload=data, emitter=emitter)

    # ── Health / Ping ────────────────────────────────────────

    def ping(self) -> bool:
        """Test Redis connectivity via PING."""
        import redis as _redis
        try:
            r = _redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
            r.ping()
            redis_connection_status.set(1)
            return True
        except Exception:
            redis_connection_status.set(0)
            return False

    def health(self) -> Dict[str, Any]:
        """Full StreamBus health (memory, host, status)."""
        if not self.bus:
            return {"status": "unhealthy", "connected": False, "error": "bus not initialized"}
        return self.bus.health()

    # ── Recent Events (XRANGE / replay) ─────────────────────

    def recent_events(
        self,
        channel: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Return recent events from a single channel via StreamBus.replay().

        Uses XRANGE under the hood — no consumer group needed.
        """
        if not self.bus:
            return []
        try:
            events = self.bus.replay(channel=channel, count=limit)
            return [
                {
                    "event_id": str(e.event_id),
                    "stream": str(e.stream),
                    "payload": e.payload if isinstance(e.payload, dict) else str(e.payload),
                }
                for e in events
            ]
        except Exception as exc:
            logger.warning("replay(%s) failed: %s", channel, exc)
            return []

    def recent_events_all(
        self,
        limit: int = 100,
        domain_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate recent events across all sacred channels.

        If *domain_filter* is given, only channels whose name starts with
        that string are queried.
        """
        channels = list(settings.SACRED_CHANNELS)
        if domain_filter:
            channels = [c for c in channels if c.startswith(domain_filter)]

        all_events: List[Dict[str, Any]] = []
        per_channel = max(1, limit // max(len(channels), 1))
        for ch in channels:
            all_events.extend(self.recent_events(ch, limit=per_channel))

        # Sort by event_id (Redis timestamp-sequence) descending → newest first
        all_events.sort(key=lambda e: e.get("event_id", ""), reverse=True)
        return all_events[:limit]

    # ── Stream Statistics ────────────────────────────────────

    def stream_statistics(self) -> Dict[str, Any]:
        """
        Aggregate XINFO STREAM for every sacred channel.

        Returns per-channel length + total summary.
        """
        if not self.bus:
            return {"error": "bus not initialized"}

        stats: Dict[str, Any] = {}
        total_length = 0
        for ch in settings.SACRED_CHANNELS:
            info = self.bus.stream_info(ch)
            length = info.get("length", 0)
            total_length += length
            stats[ch] = {
                "length": length,
                "exists": info.get("exists", True) if length == 0 else True,
                "groups": len(info.get("groups", [])),
            }
        return {
            "channels": stats,
            "total_events": total_length,
            "total_channels": len(settings.SACRED_CHANNELS),
        }

    # ── Orders Health ────────────────────────────────────────

    def orders_health(self) -> Dict[str, Any]:
        """
        Probe each sacred channel for active consumer groups.

        An order is "alive" if it has ≥ 1 consumer group with ≥ 1 consumer.
        """
        if not self.bus:
            return {}
        result: Dict[str, Any] = {}
        for ch in settings.SACRED_CHANNELS:
            info = self.bus.stream_info(ch)
            groups = info.get("groups", [])
            active = False
            for g in groups:
                # redis-py returns dicts or byte-keyed dicts
                consumers = g.get("consumers", g.get(b"consumers", 0))
                if isinstance(consumers, int) and consumers > 0:
                    active = True
                    break
            result[ch] = {
                "status": "alive" if active else "idle",
                "consumer_groups": len(groups),
                "stream_length": info.get("length", 0),
            }
        return result

    # ── Routing Map ──────────────────────────────────────────

    @staticmethod
    def routing_map() -> Dict[str, List[str]]:
        """Return the canonical EVENT_ROUTING_MAP from LAYER 1."""
        return dict(EVENT_ROUTING_MAP)

    # ── Pulse / Heartbeat ────────────────────────────────────

    def pulse_status(self) -> Dict[str, Any]:
        """Return liveness metadata about this Conclave instance."""
        return {
            "is_active": self.is_connected,
            "started_at": self._started_at,
            "heartbeat_count": self._heartbeat_count,
            "redis": self.health(),
        }

    def force_heartbeat(self) -> bool:
        """Emit a heartbeat event on conclave.pulse channel."""
        try:
            self.emit(
                channel="conclave.pulse",
                data={
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "heartbeat_seq": self._heartbeat_count,
                },
                emitter="conclave.heartbeat",
            )
            self._heartbeat_count += 1
            return True
        except Exception as exc:
            logger.error("force_heartbeat failed: %s", exc)
            return False
