"""
Babel Gardens - Domain Layer
============================

Pure domain objects and configuration.
NO I/O - this module can be imported without external dependencies.

Exports:
- Configuration: BabelConfig, TopicConfig, get_config, set_config
- Entities: EmbeddingResult, SentimentResult, EmotionResult, etc.
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
]
