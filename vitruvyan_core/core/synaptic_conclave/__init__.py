"""
    Vitruvyan Cognitive Bus
=======================

Redis Streams-based event transport system for inter-service communication.
Provides durable, replayable event streaming with consumer groups.

ARCHITECTURAL DECISION (Jan 24, 2026):
- Redis Streams is the ONLY canonical bus
- All Pub/Sub systems removed
- Bus is "humble" - no payload inspection, no semantic routing

Author: Vitruvyan Development Team
Created: 2025-01-14
Hardened: 2026-01-24
"""
    
# ============================================================================
# CANONICAL BUS - Redis Streams Only
# ============================================================================
from .transport.streams import StreamBus, StreamEvent
from .utils.lexicon import get_lexicon

# ============================================================================
# DEPRECATED — Legacy modules removed
# ============================================================================
# redis_client_shim.py, redis_client_compat.py: DELETED (Mar 06, 2026)
# heart, herald, scribe: removed (Jan 24, 2026)
# Use StreamBus for all event transport.

__all__ = [
    # Canonical bus (Redis Streams)
    'StreamBus',
    'StreamEvent',
    'get_lexicon',
]

__version__ = '2.0.0'  # Major version bump - architectural consolidation
__author__ = 'Vitruvyan Team'
__description__ = 'Cognitive Bus - Redis Streams Event Transport'


__all__.extend([
    'StreamBus',
    'StreamEvent', 
    'get_stream_bus',
    'emit',
    'consume',
])
