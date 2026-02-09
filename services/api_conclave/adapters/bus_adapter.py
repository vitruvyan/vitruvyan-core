"""
🕯 Synaptic Conclave — Bus Adapter (LIVELLO 2)

Bridges HTTP requests to Redis Streams (LIVELLO 1 transport).

The adapter does NOT contain business logic. It:
1. Initializes StreamBus connection
2. Delegates emit/health operations to StreamBus
3. Returns raw results as dicts

"Il Conclave non pensa; trasmette. L'intelligenza è nei consumer."
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

import logging
from typing import Any, Dict, Optional

from core.synaptic_conclave.transport.streams import StreamBus
from api_conclave.config import settings
from api_conclave.monitoring.metrics import redis_connection_status

logger = logging.getLogger("Conclave.BusAdapter")


class ConclaveBusAdapter:
    """
    Bridges HTTP layer to Redis Streams (StreamBus).

    Instantiate once at service startup. Thread-safe (StreamBus is thread-safe).

    Usage:
        adapter = ConclaveBusAdapter()
        event_id = adapter.emit("codex.discovery.mapped", {"ticker": "AAPL"})
    """

    def __init__(self):
        self.bus: Optional[StreamBus] = None
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
