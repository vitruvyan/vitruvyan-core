"""
COGNITIVE BUS — Foundation Tier 0
Redis Event Substrate for Epistemic Communication

The Cognitive Bus is Vitruvyan's neural substrate - a Redis-based
event-driven messaging system that enables asynchronous communication
between all Sacred Orders (Perception, Memory, Reason, Discourse, Truth).

Core Components:
- ConclaveHeart: Central event coordinator
- RedisBusClient: Connection manager and event publisher
- ConclaveScribe: Event logger and archival
- ConclaveHerald: Event broadcasting and routing
- ConclavePulse: Health monitoring and heartbeat
"""

from .redis_client import (
    get_redis_bus,
    reset_redis_bus,
    CognitiveEvent,
    RedisBusClient,
    publish_codex_event,
    subscribe_to_events,
)
from .heart import (
    ConclaveHeart,
    SemanticEvent,
)
from .scribe import (
    ConclaveScribe,
    EventRecord,
)
from .herald import (
    ConclaveHerald,
    OrderEndpoint,
)
from .pulse import ConclavePulse
from .event_schema import (
    EventSchemaValidator,
    EventDomain,
)
from .lexicon import SacredLexicon

__all__ = [
    # Core Components (Conclave naming)
    "ConclaveHeart",
    "ConclaveScribe",
    "ConclaveHerald",
    "ConclavePulse",
    # Redis Client
    "RedisBusClient",
    "get_redis_bus",
    "reset_redis_bus",
    # Event System
    "CognitiveEvent",
    "SemanticEvent",
    "EventRecord",
    "OrderEndpoint",
    "EventSchemaValidator",
    "EventDomain",
    "SacredLexicon",
    # Utility Functions
    "publish_codex_event",
    "subscribe_to_events",
]

# Helper functions
from .heart import get_heart
from .herald import get_herald  
from .pulse import get_pulse, start_system_pulse
from .scribe import get_scribe
from .heart import publish_event, subscribe_to_domain
from .lexicon import get_lexicon

# Add helper functions to exports
__all__.extend([
    "get_heart",
    "get_herald",
    "get_pulse",
    "get_scribe",
    "get_lexicon",
    "publish_event",
    "subscribe_to_domain",
    "start_system_pulse",
])
