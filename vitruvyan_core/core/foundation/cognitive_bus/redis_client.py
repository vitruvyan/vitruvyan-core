#!/usr/bin/env python3
"""
Redis Client - Compatibility Shim (TEMPORARY - Jan 25, 2026)

This is a TEMPORARY compatibility layer that wraps StreamBus to provide
the legacy Herald API. This allows the codebase to continue using Herald-style
calls while we migrate to Streams.

Status: TEMPORARY SHIM (remove after full migration)
Migration Target: Q1 2026
Legacy Dependencies: orthodoxy_node.py, autopilot_node.py

Architecture Decision (Jan 25, 2026):
    LangGraph codebase still has Herald dependencies in orthodoxy_node.py.
    Rather than blocking all development, we create this shim to provide
    backward compatibility. This allows:
    1. Listeners to migrate to Streams (DONE: LangGraph listener)
    2. Main codebase to continue functioning (via shim)
    3. Gradual migration without breaking production
    
    Once all Herald usage is removed, delete this file.

TODO (Phase 8 - Full Migration):
    - Migrate orthodoxy_node.py from get_redis_bus() to StreamBus
    - Migrate autopilot_node.py from Herald.publish() to StreamBus.emit()
    - Delete this file
    - Update all imports to use StreamBus directly
"""

import os
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .streams import StreamBus, TransportEvent

logger = logging.getLogger(__name__)


# ============================================================================
# LEGACY DATA STRUCTURES (Herald compatibility)
# ============================================================================

@dataclass
class CognitiveEvent:
    """
    Legacy event structure for Herald compatibility.
    
    This mimics the old Herald event format. New code should use
    TransportEvent from streams.py instead.
    """
    event_id: str
    stream: str
    payload: Dict[str, Any]
    emitter: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    correlation_id: Optional[str] = None
    
    @classmethod
    def from_transport_event(cls, event: TransportEvent) -> 'CognitiveEvent':
        """Convert new TransportEvent to legacy CognitiveEvent"""
        return cls(
            event_id=event.event_id,
            stream=event.stream,
            payload=event.payload,
            emitter=event.emitter,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id
        )


# ============================================================================
# LEGACY API SHIM (Herald compatibility)
# ============================================================================

class RedisClientShim:
    """
    Shim that provides Herald-like API using StreamBus underneath.
    
    This is a TEMPORARY compatibility layer. DO NOT EXTEND.
    """
    
    def __init__(self):
        self.bus = StreamBus(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            password=os.getenv('REDIS_PASSWORD')
        )
        logger.warning("⚠️ Using RedisClientShim (Herald compatibility). Migrate to StreamBus!")
        
        # Herald compatibility attributes (mock)
        self.is_beating = True  # Always "beating" since StreamBus is always connected
        self._pulse_status = {"active": True, "interval": 30}
    
    def connect(self) -> bool:
        """Herald compatibility: check connection (StreamBus always connected)"""
        try:
            # StreamBus connection is lazy, test with PING
            self.bus.client.ping()
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Herald compatibility: check if Redis is connected"""
        try:
            self.bus.client.ping()
            return True
        except Exception:
            return False
    
    async def stop_beating(self):
        """Herald compatibility: no-op"""
        self.is_beating = False
    
    async def start_beating(self, interval: int = 30):
        """Herald compatibility: no-op"""
        self.is_beating = True
        self._pulse_status["interval"] = interval
    
    async def get_pulse_status(self):
        """Herald compatibility: return mock status"""
        return {
            "is_beating": self.is_beating,
            "active": True,
            "interval": self._pulse_status.get("interval", 30)
        }
    
    async def get_vitals(self):
        """Herald compatibility: return mock vitals"""
        return {
            "status": "healthy",
            "is_beating": self.is_beating,
            "redis_connected": True,  # StreamBus is always connected
            "pulse_interval": self._pulse_status.get("interval", 30),
            "connections": 1,
            "uptime_seconds": 0,
            "message": "RedisClientShim compatibility layer (migrate to StreamBus)"
        }
    
    def publish(self, channel: str, payload: Dict[str, Any], emitter: str = "unknown") -> str:
        """
        Legacy publish() method (Herald-style).
        
        Wraps StreamBus.emit() for backward compatibility.
        """
        event_id = self.bus.emit(
            channel=channel,
            payload=payload,
            emitter=emitter
        )
        logger.debug(f"📤 [SHIM] Published to {channel}: {event_id}")
        return event_id
    
    def subscribe(self, channel: str, group: str, consumer: str):
        """
        Legacy subscribe() method (Herald-style).
        
        Wraps StreamBus.consume() generator.
        """
        logger.warning(f"⚠️ [SHIM] subscribe() called - this is blocking! Use listeners instead.")
        for transport_event in self.bus.consume(channel, group, consumer):
            yield CognitiveEvent.from_transport_event(transport_event)
    
    def ack(self, event: CognitiveEvent, group: str) -> bool:
        """Legacy ACK method"""
        # Convert back to TransportEvent for ACK
        transport_event = TransportEvent(
            event_id=event.event_id,
            stream=event.stream,
            payload=event.payload,
            emitter=event.emitter,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id
        )
        return self.bus.ack(transport_event, group=group)
    
    def health(self) -> Dict[str, Any]:
        """Health check pass-through"""
        return self.bus.health()


# ============================================================================
# GLOBAL INSTANCE (Herald pattern compatibility)
# ============================================================================

_global_bus_shim: Optional[RedisClientShim] = None


def get_redis_bus() -> RedisClientShim:
    """
    Get global RedisClientShim instance (singleton pattern).
    
    This mimics the old get_redis_bus() function from Herald.
    
    DEPRECATED: Use StreamBus() directly in new code.
    """
    global _global_bus_shim
    if _global_bus_shim is None:
        _global_bus_shim = RedisClientShim()
        logger.info("✅ RedisClientShim initialized (Herald compatibility mode)")
    return _global_bus_shim


# Alias for compatibility with different import patterns
RedisBusClient = RedisClientShim


# ============================================================================
# MIGRATION HELPERS
# ============================================================================

def is_using_shim() -> bool:
    """Check if codebase is still using compatibility shim"""
    return _global_bus_shim is not None


def log_migration_status():
    """Log migration status for monitoring"""
    if is_using_shim():
        logger.warning(
            "⚠️ MIGRATION STATUS: Still using Herald compatibility shim. "
            "Migrate to StreamBus to remove this warning."
        )
    else:
        logger.info("✅ MIGRATION STATUS: Not using Herald shim (good!)")
