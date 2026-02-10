"""
Pattern Weavers - Sacred Order #5
=================================

Domain-agnostic semantic contextualization engine.

"From chaos, patterns. From patterns, understanding."

Architecture:
- domain/: Configuration and entity dataclasses
- consumers/: Pure processing logic (WeaverConsumer, KeywordMatcherConsumer)
- events/: Event channel constants
- monitoring/: Metric name constants
- governance/: Rules and classifiers (future)
- philosophy/: Sacred Order charter
- _legacy/: Pre-refactoring code (frozen archive)

Integration:
- LIVELLO 1 (this module): Pure Python, no I/O
- LIVELLO 2 (services/api_pattern_weavers/): FastAPI, adapters, I/O

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026 - Domain-Agnostic Refactoring)
"""

__version__ = "2.0.0"
__epistemic_order__ = "REASON"
__layer__ = "SEMANTIC"

# Domain layer
from .domain import (
    PatternConfig,
    EmbeddingConfig,
    CollectionConfig,
    TableConfig,
    StreamConfig,
    TaxonomyConfig,
    TaxonomyCategory,
    get_config,
    set_config,
    WeaveStatus,
    MatchType,
    PatternMatch,
    RiskProfile,
    WeaveRequest,
    WeaveResult,
    EmbeddingVector,
    TaxonomyEntry,
    HealthStatus,
)

# Consumer layer
from .consumers import (
    BaseConsumer,
    ProcessResult,
    WeaverConsumer,
    KeywordMatcherConsumer,
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
    Labels,
)


__all__ = [
    # Config
    "PatternConfig",
    "EmbeddingConfig",
    "CollectionConfig",
    "TableConfig",
    "StreamConfig",
    "TaxonomyConfig",
    "TaxonomyCategory",
    "get_config",
    "set_config",
    # Entities
    "WeaveStatus",
    "MatchType",
    "PatternMatch",
    "RiskProfile",
    "WeaveRequest",
    "WeaveResult",
    "EmbeddingVector",
    "TaxonomyEntry",
    "HealthStatus",
    # Consumers
    "BaseConsumer",
    "ProcessResult",
    "WeaverConsumer",
    "KeywordMatcherConsumer",
    # Events
    "Channels",
    "EventEnvelope",
    "create_event_envelope",
    # Monitoring
    "MetricNames",
    "HealthCheckNames",
    "Labels",
]

