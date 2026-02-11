"""
Babel Gardens - Domain Layer
============================

Pure domain objects and configuration.
NO I/O - this module can be imported without external dependencies.

Exports:
- Configuration: BabelConfig, TopicConfig, SignalConfig, get_config, set_config
- Entities: EmbeddingResult, SentimentResult (legacy), SignalExtractionResult
- Signal Primitives: SignalSchema, MultiSignalFusionConfig (v2.1+)
- Enums: ProcessingStatus, SentimentLabel, EmotionLabel
"""

from .config import (
    # Master config
    BabelConfig,
    get_config,
    set_config,
    load_config_from_yaml,
    # Sub-configs
    EmbeddingModelConfig,
    SentimentModelConfig,
    EmotionModelConfig,
    LanguageConfig,
    CacheConfig,
    StreamConfig,
    TableConfig,
    CollectionConfig,
    # Topic taxonomy
    TopicConfig,
    TopicCategory,
)

from .entities import (
    # Enums
    ProcessingStatus,
    SentimentLabel,
    EmotionLabel,
    # Embedding
    EmbeddingVector,
    EmbeddingRequest,
    EmbeddingResult,
    # Sentiment
    SentimentScore,
    SentimentResult,
    # Emotion
    EmotionScore,
    EmotionResult,
    # Language
    LanguageDetection,
    # Topics
    TopicMatch,
    TopicClassificationResult,
    # Synthesis
    SynthesisRequest,
    SynthesisResult,
)

# Signal Primitives (v2.1+)
from .signal_schema import (
    SignalSchema,
    SignalConfig,
    SignalExtractionResult,
    MultiSignalFusionConfig,
    merge_configs,
)

__all__ = [
    # Config
    "BabelConfig",
    "get_config",
    "set_config",
    "load_config_from_yaml",
    "EmbeddingModelConfig",
    "SentimentModelConfig",
    "EmotionModelConfig",
    "LanguageConfig",
    "CacheConfig",
    "StreamConfig",
    "TableConfig",
    "CollectionConfig",
    "TopicConfig",
    "TopicCategory",
    # Enums
    "ProcessingStatus",
    "SentimentLabel",
    "EmotionLabel",
    # Entities
    "EmbeddingVector",
    "EmbeddingRequest",
    "EmbeddingResult",
    "SentimentScore",
    "SentimentResult",
    "EmotionScore",
    "EmotionResult",
    "LanguageDetection",
    "TopicMatch",
    "TopicClassificationResult",
    "SynthesisRequest",
    "SynthesisResult",
    # Signal Primitives (v2.1+)
    "SignalSchema",
    "SignalConfig",
    "SignalExtractionResult",
    "MultiSignalFusionConfig",
    "merge_configs",
]
