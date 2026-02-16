"""
Codex Hunters - Sacred Order #3
===============================

Domain-agnostic data discovery and preservation system.

"No codex left unfound" - The Hunter's Creed

Architecture:
- domain/: Configuration and entity dataclasses (CodexConfig, CodexEvent, etc.)
- consumers/: Pure processing logic (TrackerConsumer, RestorerConsumer, BinderConsumer)
- events/: Event channel constants
- monitoring/: Metric name constants
- governance/: Rules and classifiers (future)
- philosophy/: Sacred Order charter

Integration:
- LIVELLO 1 (this module): Pure Python, no I/O
- LIVELLO 2 (services/api_codex_hunters/): FastAPI, adapters, I/O

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026 - Domain-Agnostic Refactoring)
"""

# Domain layer
from .domain import (
    CodexConfig,
    SourceConfig,
    CollectionConfig,
    TableConfig,
    StreamConfig,
    get_config,
    set_config,
    CodexEvent,
    DiscoveredEntity,
    RestoredEntity,
    BoundEntity,
    ExpeditionRequest,
    ExpeditionResult,
    ExpeditionStatus,
    EntityStatus,
    Severity,
    ConsistencyStatus,
    CollectionPairInput,
    CollectionConsistency,
    InspectionReport,
    HealthStatus,
)

# Consumer layer
from .consumers import (
    BaseConsumer,
    ProcessResult,
    TrackerConsumer,
    RestorerConsumer,
    BinderConsumer,
    InspectorConsumer,
)

# Events
from .events import (
    Channels,
    EventEnvelope,
    create_event_envelope,
)

# Monitoring
from .monitoring import (
    MetricNames,
    HealthCheckNames,
)


__all__ = [
    # Config
    "CodexConfig",
    "SourceConfig",
    "CollectionConfig",
    "TableConfig",
    "StreamConfig",
    "get_config",
    "set_config",
    # Entities
    "CodexEvent",
    "DiscoveredEntity",
    "RestoredEntity",
    "BoundEntity",
    "ExpeditionRequest",
    "ExpeditionResult",
    "ExpeditionStatus",
    "EntityStatus",
    "Severity",
    "ConsistencyStatus",
    "CollectionPairInput",
    "CollectionConsistency",
    "InspectionReport",
    "HealthStatus",
    # Consumers
    "BaseConsumer",
    "ProcessResult",
    "TrackerConsumer",
    "RestorerConsumer",
    "BinderConsumer",
    "InspectorConsumer",
    # Events
    "Channels",
    "EventEnvelope",
    "create_event_envelope",
    # Monitoring
    "MetricNames",
    "HealthCheckNames",
]


__version__ = "2.0.0"
__author__ = "Vitruvyan Core Team"
__description__ = "Codex Hunters - Domain-Agnostic Data Discovery"
__motto__ = "No codex left unfound"
