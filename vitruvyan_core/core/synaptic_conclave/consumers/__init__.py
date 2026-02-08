# Vitruvyan Cognitive Bus — Consumers (Tentacles)
# Architecture: Octopus-Mycelium Hybrid
# "80% of cognition in tentacles, 20% in minimal brain"

from .base_consumer import BaseConsumer, ConsumerType, ConsumerConfig, ProcessResult
from ..events.event_envelope import CognitiveEvent, TransportEvent, EventAdapter
from .registry import ConsumerRegistry, get_registry
from .working_memory import WorkingMemory
from .listener_adapter import ListenerAdapter, StreamsEnabledListener, wrap_legacy_listener

__all__ = [
    # Base consumer pattern
    "BaseConsumer",
    "ConsumerType", 
    "ConsumerConfig",
    "CognitiveEvent",  # Canonical event model
    "TransportEvent",  # Bus-level event
    "EventAdapter",    # Conversion layer
    "ProcessResult",
    
    # Registry
    "ConsumerRegistry",
    "get_registry",
    
    # Working memory
    "WorkingMemory",
    
    # Migration adapters
    "ListenerAdapter",
    "StreamsEnabledListener",
    "wrap_legacy_listener",
]

