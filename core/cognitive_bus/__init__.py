"""
    Vitruvyan Cognitive Bus
=======================

Redis Streams-based event transport system for inter-service communication.
Provides durable, replayable event streaming with consumer groups.

ARCHITECTURAL DECISION (Jan 24, 2026):
- Redis Streams is the ONLY canonical bus
- All Pub/Sub systems archived (see /archive/pub_sub_legacy/)
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
# DEPRECATED - Archived to /archive/pub_sub_legacy/ (Jan 24, 2026)
# ============================================================================
# The following imports are NO LONGER AVAILABLE:
# - redis_client (RedisBusClient, CognitiveEvent) → Use StreamBus
# - heart (get_heart, publish_event) → Use StreamBus.emit()
# - herald (get_herald) → Semantic routing moved to consumers
# - scribe (get_scribe) → Event persistence via Redis Streams
#
# Migration guide: /archive/pub_sub_legacy/README.md

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
