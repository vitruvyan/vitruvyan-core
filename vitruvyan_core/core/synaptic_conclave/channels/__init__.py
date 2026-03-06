"""
Synaptic Conclave — Channel Registry

Centralized source of truth for all Redis Streams channel names
and their producer/consumer contracts.

LIVELLO 1: Pure Python, no I/O, no Redis dependency.
"""

from .channel_registry import (
    EventContract,
    CHANNEL_REGISTRY,
    get_channels_for_consumer,
    get_channels_for_producer,
    validate_channel,
)

__all__ = [
    "EventContract",
    "CHANNEL_REGISTRY",
    "get_channels_for_consumer",
    "get_channels_for_producer",
    "validate_channel",
]
