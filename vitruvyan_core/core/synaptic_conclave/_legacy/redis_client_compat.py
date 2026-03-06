"""
Vitruvyan Core — Redis Client (Compatibility Shim)
===================================================

Re-exports redis_client from transport layer for backward compatibility.

Canonical location: core.synaptic_conclave.transport.redis_client

Some legacy nodes import directly from:
    from core.synaptic_conclave.redis_client import get_redis_bus, CognitiveEvent

This file provides that compatibility path.

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: COMPATIBILITY LAYER
"""

from core.synaptic_conclave.transport.redis_client import (
    get_redis_bus,
    CognitiveEvent,
    RedisBusClient,
)

__all__ = ["get_redis_bus", "CognitiveEvent", "RedisBusClient"]
