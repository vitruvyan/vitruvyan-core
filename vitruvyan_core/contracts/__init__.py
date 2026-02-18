"""
Contracts Module
================

Unified public contracts namespace for Vitruvyan Core.

Contracts:
- IDataProvider / IScoringStrategy: Neural Engine domain adapters
- BaseGraphState / GraphPlugin / Parser: Orchestration extension surface
- ILLMProvider: Pluggable LLM provider protocol

Author: vitruvyan-core
Date: February 8, 2026
"""

from .llm_provider import ILLMProvider
try:
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
    _ORCHESTRATION_EXPORTS = [
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
    ]
except Exception:
    _ORCHESTRATION_EXPORTS = []

from .data_provider import (
    IDataProvider,
    DataProviderError,
    EntityNotFoundError,
    FeatureNotAvailableError
)

from .scoring_strategy import (
    IScoringStrategy,
    ScoringStrategyError,
    InvalidProfileError,
    InvalidWeightsError
)

__all__ = [
    *_ORCHESTRATION_EXPORTS,
    # LLM
    "ILLMProvider",
    # Data Provider
    "IDataProvider",
    "DataProviderError",
    "EntityNotFoundError",
    "FeatureNotAvailableError",
    
    # Scoring Strategy
    "IScoringStrategy",
    "ScoringStrategyError",
    "InvalidProfileError",
    "InvalidWeightsError",
]
