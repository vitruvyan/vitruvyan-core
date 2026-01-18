# Vitruvyan Cognitive Bus — Consumers (Tentacles)
# Architecture: Octopus-Mycelium Hybrid
# "80% of cognition in tentacles, 20% in minimal brain"

from .base_consumer import BaseConsumer, ConsumerType, ConsumerConfig, StreamEvent, ProcessResult
from .registry import ConsumerRegistry, get_registry
from .working_memory import WorkingMemory
from .listener_adapter import ListenerAdapter, StreamsEnabledListener, wrap_legacy_listener

__all__ = [
    # Base consumer pattern
    "BaseConsumer",
    "ConsumerType", 
    "ConsumerConfig",
    "StreamEvent",
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
