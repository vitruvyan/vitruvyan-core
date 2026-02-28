"""
Contracts Module
================

Unified public contracts namespace for Vitruvyan Core.

Layout:
- Root package: cross-system contracts (orchestration, llm provider)
- Subpackages: component-scoped contracts (for example neural_engine)

Author: vitruvyan-core
Date: February 8, 2026
"""

from .base import BaseContract, ContractMeta, ContractRegistry, IContractPlugin
from .ingestion import (
    CHANNEL_INGESTION_ACQUIRED,
    CHANNEL_INGESTION_DUPLICATE,
    CHANNEL_INGESTION_NORMALIZED,
    CHANNEL_INGESTION_REJECTED,
    IngestionPayload,
    IngestionQuality,
    IIngestionPlugin,
    NormalizedChunk,
    SourceDescriptor,
    SourceType,
    build_chunk_id,
    build_source_id,
    compute_content_hash,
)
from .base import BaseContract, ContractMeta, ContractRegistry, IContractPlugin
from .ingestion import (
    CHANNEL_INGESTION_ACQUIRED,
    CHANNEL_INGESTION_DUPLICATE,
    CHANNEL_INGESTION_NORMALIZED,
    CHANNEL_INGESTION_REJECTED,
    IngestionPayload,
    IngestionQuality,
    IIngestionPlugin,
    NormalizedChunk,
    SourceDescriptor,
    SourceType,
    build_chunk_id,
    build_source_id,
    compute_content_hash,
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
from .graph_response import (
    SessionMin,
    GraphResponseMin,
    OrthodoxyStatusType,
    build_correlation_id,
)

# Neural Engine contracts depend on pandas — lazy-load to avoid crashes
# in services that don't have pandas installed (Pattern Weavers, Babel Gardens, etc.)
try:
    from .neural_engine.data_provider import (
        IDataProvider,
        DataProviderError,
        EntityNotFoundError,
        FeatureNotAvailableError,
    )
    from .neural_engine.scoring_strategy import (
        IScoringStrategy,
        ScoringStrategyError,
        InvalidProfileError,
        InvalidWeightsError,
    )
    from .neural_engine.filter_strategy import (
        IFilterStrategy,
        FilterStrategyError,
    )
except ImportError:
    IDataProvider = None  # type: ignore[assignment,misc]
    DataProviderError = None  # type: ignore[assignment,misc]
    EntityNotFoundError = None  # type: ignore[assignment,misc]
    FeatureNotAvailableError = None  # type: ignore[assignment,misc]
    IScoringStrategy = None  # type: ignore[assignment,misc]
    ScoringStrategyError = None  # type: ignore[assignment,misc]
    InvalidProfileError = None  # type: ignore[assignment,misc]
    InvalidWeightsError = None  # type: ignore[assignment,misc]
    IFilterStrategy = None  # type: ignore[assignment,misc]
    FilterStrategyError = None  # type: ignore[assignment,misc]
from .pattern_weavers import (
    GateVerdict,
    DomainGate,
    OntologyEntity,
    OntologyPayload,
    CompileRequest,
    CompileResponse,
    ISemanticPlugin,
)
from .comprehension import (
    SentimentPayload,
    EmotionPayload,
    LinguisticPayload,
    SemanticPayload,
    ComprehensionResult,
    ComprehendRequest,
    ComprehendResponse,
    SignalEvidence,
    FusionStrategy,
    FusionContributor,
    FusionResult,
    FuseRequest,
    FuseResponse,
    IComprehensionPlugin,
    ISignalContributor,
)
from .rag import (
    CollectionTier,
    CollectionDeclaration,
    DistanceMetric,
    RAGPayload,
    RAG_NAMESPACE,
    deterministic_point_id,
    content_hash_id,
    validate_collection_name,
    CORE_COLLECTIONS,
    ORDER_COLLECTIONS,
    ALL_DECLARED_COLLECTIONS,
    get_collection_declaration,
    is_declared_collection,
)

__all__ = [
    # Base contracts
    "BaseContract",
    "ContractMeta",
    "ContractRegistry",
    "IContractPlugin",
    # Ingestion Contract
    "CHANNEL_INGESTION_ACQUIRED",
    "CHANNEL_INGESTION_DUPLICATE",
    "CHANNEL_INGESTION_NORMALIZED",
    "CHANNEL_INGESTION_REJECTED",
    "SourceType",
    "SourceDescriptor",
    "IngestionQuality",
    "NormalizedChunk",
    "IngestionPayload",
    "IIngestionPlugin",
    "compute_content_hash",
    "build_source_id",
    "build_chunk_id",
    # LLM
    "ILLMProvider",
    # Graph Response Contract (channel-agnostic)
    "SessionMin",
    "GraphResponseMin",
    "OrthodoxyStatusType",
    "build_correlation_id",
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
    # Scoring Strategy
    "IScoringStrategy",
    "ScoringStrategyError",
    "InvalidProfileError",
    "InvalidWeightsError",
    # Filter Strategy
    "IFilterStrategy",
    "FilterStrategyError",
    # Pattern Weavers v3
    "GateVerdict",
    "DomainGate",
    "OntologyEntity",
    "OntologyPayload",
    "CompileRequest",
    "CompileResponse",
    "ISemanticPlugin",
    # Comprehension Engine
    "SentimentPayload",
    "EmotionPayload",
    "LinguisticPayload",
    "SemanticPayload",
    "ComprehensionResult",
    "ComprehendRequest",
    "ComprehendResponse",
    "SignalEvidence",
    "FusionStrategy",
    "FusionContributor",
    "FusionResult",
    "FuseRequest",
    "FuseResponse",
    "IComprehensionPlugin",
    "ISignalContributor",
    # RAG Governance Contract V1
    "CollectionTier",
    "CollectionDeclaration",
    "DistanceMetric",
    "RAGPayload",
    "RAG_NAMESPACE",
    "deterministic_point_id",
    "content_hash_id",
    "validate_collection_name",
    "CORE_COLLECTIONS",
    "ORDER_COLLECTIONS",
    "ALL_DECLARED_COLLECTIONS",
    "get_collection_declaration",
    "is_declared_collection",
]
