"""
Pattern Weavers - Domain Layer
==============================

Pure Python domain objects. No I/O, no external dependencies.

Configuration:
- PatternConfig: Master configuration
- EmbeddingConfig, CollectionConfig, TableConfig, StreamConfig
- TaxonomyConfig: Domain taxonomy (loaded from YAML)

Entities:
- WeaveRequest, WeaveResult: Operation request/response
- PatternMatch, RiskProfile: Match results
- EmbeddingVector: Embedding with metadata
- WeaveStatus, MatchType, HealthStatus: Enums
"""

from .config import (
    PatternConfig,
    EmbeddingConfig,
    CollectionConfig,
    TableConfig,
    StreamConfig,
    TaxonomyConfig,
    TaxonomyCategory,
    get_config,
    set_config,
)

from .entities import (
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
]
