"""
Codex Hunters - Domain Layer
============================

Pure domain objects with no I/O dependencies.
"""

from .config import (
    CodexConfig,
    SourceConfig,
    CollectionConfig,
    TableConfig,
    StreamConfig,
    get_config,
    set_config,
)

from .entities import (
    CodexEvent,
    DiscoveredEntity,
    RestoredEntity,
    BoundEntity,
    ExpeditionRequest,
    ExpeditionResult,
    ExpeditionStatus,
    EntityStatus,
    Severity,
    HealthStatus,
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
    "HealthStatus",
]
