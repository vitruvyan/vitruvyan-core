"""
COGNITIVE BUS — Foundation Tier 0  
Vitruvian Core - Redis Streams Event Transport System

The Cognitive Bus is Vitruvyan's neural substrate - a Redis Streams-based
event-driven messaging system that enables asynchronous communication
between all Sacred Orders (Perception, Memory, Reason, Discourse, Truth).

ARCHITECTURAL VERSION: 2.0 (Redis Streams Canonical)
MIGRATION DATE: February 5, 2026
SOURCE: Synchronized from vitruvyan (production-ready)

Bio-Inspired Architecture:
- Octopus Neural System: 2/3 neurons in arms (local autonomy)
- Fungal Mycelial Networks: No central processor (emergent intelligence)

Sacred Invariants (ENFORCED):
1. Bus NEVER inspects payload content
2. Bus NEVER correlates events  
3. Bus NEVER does semantic routing
4. Bus NEVER synthesizes events

Phase Status (vitruvyan):
- Phase 0-7: ✅ Complete
- Test Coverage: 19/30 (63%)
- Listener Migration: 7/13 (54%)

See: Vitruvyan_Octopus_Mycelium_Architecture.md (416 lines)
     Vitruvyan_Bus_Invariants.md (216 lines)
     Vitruvyan_Epistemic_Charter.md (248 lines)
"""

import warnings
from typing import TYPE_CHECKING

# ============================================================================
# CORE BUS — Redis Streams (Level 1 Transport)
# ============================================================================

from .streams import StreamBus
from .event_envelope import (
    TransportEvent,
    CognitiveEvent,
    EventAdapter,
)
from .redis_client import (
    RedisBusClient,
    get_redis_bus,
    CognitiveEvent as LegacyCognitiveEvent,  # Alias for backward compat
    is_using_shim,
    log_migration_status,
)
from .lexicon import SacredLexicon, get_lexicon
from .metrics import (
    cognitive_bus_events_total,
    cognitive_bus_event_duration,
    herald_broadcast_total,
    scribe_write_total,
    listener_consumed_total,
    record_scribe_write,
    record_listener_consumption,
    update_stream_health,
)

# ============================================================================
# CONSUMERS — The Tentacle Pattern
# ============================================================================

from .consumers.base_consumer import (
    BaseConsumer,
    ConsumerType,
    ConsumerConfig,
    ProcessResult,
)
from .consumers.listener_adapter import ListenerAdapter
from .consumers.working_memory import WorkingMemory

try:
    from .consumers.registry import ConsumerRegistry
except ImportError:
    ConsumerRegistry = None

try:
    from .consumers.narrative_engine import NarrativeEngine
except ImportError:
    NarrativeEngine = None

try:
    from .consumers.risk_guardian import RiskGuardian
except ImportError:
    RiskGuardian = None

# ============================================================================
# PLASTICITY — Governed Learning System
# ============================================================================

from .plasticity.manager import (
    PlasticityManager,
    ParameterBounds,
    Adjustment,
)
from .plasticity.outcome_tracker import (
    OutcomeTracker,
    Outcome,
)
from .plasticity.learning_loop import PlasticityLearningLoop

try:
    from .plasticity.observer import PlasticityObserver
except ImportError:
    PlasticityObserver = None

from .plasticity.metrics import (
    plasticity_adjustment_total,
    plasticity_adjustment_delta,
    plasticity_parameter_value,
)

# ============================================================================
# ORTHODOXY — Validation & Governance
# ============================================================================

from .orthodoxy.formatter import format_verdict_to_text
from .orthodoxy.verdicts import OrthodoxyVerdict

# ============================================================================
# DEPRECATED APIs (Pub/Sub Legacy)
# ============================================================================
# The following components were ARCHIVED on January 24, 2026
# during Phase 0 Bus Hardening. They are available in:
# archive/legacy_pubsub/ for recovery purposes.
#
# Migration path:
# - ConclaveHeart → StreamBus.emit()
# - ConclaveHerald → Semantic routing in consumers
# - ConclaveScribe → Redis Streams native persistence
# - ConclavePulse → Prometheus metrics
# - SemanticEvent → CognitiveEvent
#
# See: docs/IMPLEMENTATION_ROADMAP.md (Phase 0 section)


def get_heart():
    """DEPRECATED: Use StreamBus() instead."""
    warnings.warn(
        "get_heart() is deprecated. Use StreamBus() instead. "
        "ConclaveHeart was archived in Phase 0 (Jan 24, 2026). "
        "See archive/legacy_pubsub/ for recovery.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def get_herald():
    """DEPRECATED: Semantic routing moved to consumers."""
    warnings.warn(
        "get_herald() is deprecated. Semantic routing now handled by consumers. "
        "ConclaveHerald was archived in Phase 0 (Jan 24, 2026). "
        "See archive/legacy_pubsub/ for recovery.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def get_scribe():
    """DEPRECATED: Use Redis Streams native persistence."""
    warnings.warn(
        "get_scribe() is deprecated. Use Redis Streams native persistence. "
        "ConclaveScribe was archived in Phase 0 (Jan 24, 2026). "
        "See archive/legacy_pubsub/ for recovery.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def get_pulse():
    """DEPRECATED: Use Prometheus metrics."""
    warnings.warn(
        "get_pulse() is deprecated. Use Prometheus metrics instead. "
        "ConclavePulse was archived in Phase 0 (Jan 24, 2026). "
        "See archive/legacy_pubsub/ for recovery.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def start_system_pulse(*args, **kwargs):
    """DEPRECATED: Use Prometheus metrics."""
    warnings.warn(
        "start_system_pulse() is deprecated. Use Prometheus metrics instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def publish_event(*args, **kwargs):
    """DEPRECATED: Use StreamBus.emit() instead."""
    warnings.warn(
        "publish_event() is deprecated. Use StreamBus.emit() instead. "
        "Migrated in Phase 0 (Jan 24, 2026).",
        DeprecationWarning,
        stacklevel=2
    )
    # Attempt graceful degradation
    bus = StreamBus()
    if len(args) >= 2:
        return bus.emit(channel=args[0], payload=args[1], emitter=kwargs.get('emitter', 'legacy'))
    raise TypeError("publish_event() requires at least (channel, payload)")


def subscribe_to_domain(*args, **kwargs):
    """DEPRECATED: Use StreamBus.consume() instead."""
    warnings.warn(
        "subscribe_to_domain() is deprecated. Use StreamBus.consume() instead. "
        "Migrated in Phase 0 (Jan 24, 2026).",
        DeprecationWarning,
        stacklevel=2
    )
    raise NotImplementedError(
        "subscribe_to_domain() removed. Use StreamBus.consume(channel, group, consumer). "
        "See docs/REDIS_STREAMS_ARCHITECTURE.md for consumer group setup."
    )


# Type aliases for backward compatibility
SemanticEvent = CognitiveEvent  # Legacy alias


# ============================================================================
# PUBLIC API — Exports
# ============================================================================

__all__ = [
    # ========================================================================
    # CORE BUS (Redis Streams)
    # ========================================================================
    'StreamBus',              # Primary transport (Level 1)
    'TransportEvent',         # Immutable bus-level event
    'CognitiveEvent',         # Mutable consumer-level event
    'EventAdapter',           # Transport ↔ Cognitive conversion
    'RedisBusClient',         # Legacy client (backward compat)
    'get_redis_bus',          # Legacy getter (backward compat)
    'reset_redis_bus',        # Legacy reset (backward compat)
    
    # ========================================================================
    # CONSUMERS (Tentacle Pattern)
    # ========================================================================
    'BaseConsumer',           # Abstract base for all consumers
    'ConsumerType',           # CRITICAL/ADVISORY/AMBIENT
    'ConsumerConfig',         # Consumer configuration
    'ProcessResult',          # Standard output format
    'ListenerAdapter',        # Pub/Sub → Streams migration bridge
    'WorkingMemory',          # Proprioceptive local state
    'ConsumerRegistry',       # Consumer tracking registry
    'NarrativeEngine',        # Specialized consumer (example)
    'RiskGuardian',           # Specialized consumer (example)
    
    # ========================================================================
    # PLASTICITY (Governed Learning)
    # ========================================================================
    'PlasticityManager',      # Bounded parameter adjustments
    'ParameterBounds',        # (min, max, step) constraints
    'Adjustment',             # Immutable adjustment record
    'OutcomeTracker',         # Decision → outcome linkage
    'Outcome',                # Outcome dataclass
    'LearningLoop',           # Periodic adaptation
    'PlasticityObserver',     # Observability/metrics
    
    # ========================================================================
    # ORTHODOXY (Governance)
    # ========================================================================
    'format_orthodoxy_verdict',  # Verdict formatter
    'OrthodoxEdict',             # Verdict dataclass
    
    # ========================================================================
    # METRICS (Prometheus)
    # ========================================================================
    'cognitive_bus_events_total',
    'cognitive_bus_event_duration',
    'herald_broadcast_total',
    'scribe_write_total',
    'listener_consumed_total',
    'plasticity_adjustments_total',
    'plasticity_adjustment_magnitude',
    'plasticity_parameter_value',
    'record_scribe_write',
    'record_listener_consumption',
    'update_stream_health',
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    'SacredLexicon',          # Semantic schema definitions
    'get_lexicon',            # Lexicon singleton getter
    'publish_codex_event',    # Legacy event publisher (backward compat)
    'subscribe_to_events',    # Legacy subscriber (backward compat)
    
    # ========================================================================
    # DEPRECATED (Pub/Sub Legacy - Archived Jan 24, 2026)
    # ========================================================================
    'get_heart',              # DEPRECATED → Use StreamBus()
    'get_herald',             # DEPRECATED → Consumers handle routing
    'get_scribe',             # DEPRECATED → Redis Streams persistence
    'get_pulse',              # DEPRECATED → Prometheus metrics
    'start_system_pulse',     # DEPRECATED → Prometheus metrics
    'publish_event',          # DEPRECATED → StreamBus.emit()
    'subscribe_to_domain',    # DEPRECATED → StreamBus.consume()
    'SemanticEvent',          # DEPRECATED → CognitiveEvent
    'LegacyCognitiveEvent',   # Alias for redis_client version
]

# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = '2.0.0'  # Major version bump - Redis Streams canonical
__author__ = 'Vitruvyan Core Team'
__description__ = 'Cognitive Bus - Bio-Inspired Event Transport System'
__migration_date__ = '2026-02-05'
__source_repo__ = 'vitruvyan (production)'
__phase_status__ = 'Phase 0-7 Complete'
__test_coverage__ = '63% (19/30 tests)'
__listener_migration__ = '54% (7/13 listeners)'

# Audit report reference
__audit_report__ = '/home/caravaggio/vitruvyan/COGNITIVE_BUS_AUDIT_REPORT_FEB5_2026.md'
