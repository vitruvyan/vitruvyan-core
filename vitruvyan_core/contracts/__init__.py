"""
Contracts Module
================

Defines abstract interfaces (contracts) for domain-specific implementations.
These contracts enable core components to depend on stable abstractions.

Layout:
- Root package: cross-system contracts (orchestration, llm provider)
- Subpackages: component-scoped contracts (for example neural_engine)

Author: vitruvyan-core
Date: February 8, 2026
"""

from .neural_engine.data_provider import (
    IDataProvider,
    DataProviderError,
    EntityNotFoundError,
    FeatureNotAvailableError,
)
from .llm_provider import ILLMProvider
from .orchestration import (
    BaseGraphState,
    GraphStateType,
    ESSENTIAL_FIELDS,
    INTENT_FIELDS,
    LANGUAGE_FIELDS,
    EMOTION_FIELDS,
    ORTHODOXY_FIELDS,
    VAULT_FIELDS,
    TRACING_FIELDS,
    WEAVER_FIELDS,
    CAN_FIELDS,
    ALL_BASE_FIELDS,
    get_base_field_count,
    is_base_field,
    get_domain_fields,
    GraphPlugin,
    NodeContract,
    GraphEngine,
    Parser,
    BaseParser,
    ParsedSlots,
)
from .neural_engine.scoring_strategy import (
    IScoringStrategy,
    ScoringStrategyError,
    InvalidProfileError,
    InvalidWeightsError,
)

__all__ = [
    # Data Provider
    "IDataProvider",
    "DataProviderError",
    "EntityNotFoundError",
    "FeatureNotAvailableError",
    # Orchestration
    "BaseGraphState",
    "GraphStateType",
    "ESSENTIAL_FIELDS",
    "INTENT_FIELDS",
    "LANGUAGE_FIELDS",
    "EMOTION_FIELDS",
    "ORTHODOXY_FIELDS",
    "VAULT_FIELDS",
    "TRACING_FIELDS",
    "WEAVER_FIELDS",
    "CAN_FIELDS",
    "ALL_BASE_FIELDS",
    "get_base_field_count",
    "is_base_field",
    "get_domain_fields",
    "GraphPlugin",
    "NodeContract",
    "GraphEngine",
    "Parser",
    "BaseParser",
    "ParsedSlots",
    # LLM
    "ILLMProvider",
    # Scoring Strategy
    "IScoringStrategy",
    "ScoringStrategyError",
    "InvalidProfileError",
    "InvalidWeightsError",
]
