"""
Babel Gardens - Domain Configuration
=====================================

Parametric configuration for Babel Gardens - all domain-specific values
are configurable, NEVER hardcoded.

Babel Gardens is the multilingual semantic layer:
- Embedding generation (semantic, sentiment, domain-specific)
- Language detection and translation
- Topic classification
- Sentiment analysis

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026 - Domain-Agnostic Refactoring)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml


@dataclass(frozen=True)
class EmbeddingModelConfig:
    """Configuration for an embedding model."""
    
    name: str = "multilingual"
    endpoint: str = "/v1/embeddings"
    dimension: int = 768
    max_tokens: int = 512
    batch_size: int = 32


@dataclass(frozen=True)
class SentimentModelConfig:
    """Configuration for sentiment analysis model."""
    
    name: str = "sentiment"
    endpoint: str = "/v1/sentiment"
    labels: List[str] = field(default_factory=lambda: ["positive", "negative", "neutral"])
    threshold: float = 0.6


@dataclass(frozen=True)
class EmotionModelConfig:
    """Configuration for emotion detection model."""
    
    name: str = "emotion"
    endpoint: str = "/v1/emotion"
    labels: List[str] = field(default_factory=lambda: [
        "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"
    ])
    threshold: float = 0.5


@dataclass(frozen=True)
class LanguageConfig:
    """Configuration for language detection and support."""
    
    default_language: str = "en"
    supported_languages: List[str] = field(default_factory=lambda: [
        "en", "it", "es", "fr", "de", "pt", "zh", "ja", "ko", "ar"
    ])
    detection_threshold: float = 0.8
    fallback_language: str = "en"


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for embedding cache."""
    
    enabled: bool = True
    ttl_hours: int = 168  # 7 days
    max_entries: int = 100000


@dataclass(frozen=True)
class StreamConfig:
    """Configuration for Redis Streams channels."""
    
    prefix: str = "babel"
    embedding_request: str = "babel.embedding.request"
    embedding_response: str = "babel.embedding.response"
    sentiment_request: str = "babel.sentiment.request"
    sentiment_response: str = "babel.sentiment.response"
    error: str = "babel.error"


@dataclass(frozen=True)
class TableConfig:
    """Configuration for PostgreSQL tables."""
    
    embeddings: str = "babel_embeddings"
    profiles: str = "babel_profiles"
    audit: str = "babel_audit"


@dataclass(frozen=True)
class CollectionConfig:
    """Configuration for Qdrant collections.
    
    NOTE: Babel Gardens does NOT currently own any Qdrant collection.
    These defaults are placeholders for future wiring.
    See RAG_GOVERNANCE_CONTRACT_V1 Section 4.3.
    """
    
    semantic: str = "phrases_embeddings"
    sentiment: str = "phrases_embeddings"


@dataclass
class TopicCategory:
    """A single topic category for classification."""
    
    name: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopicConfig:
    """
    Domain-agnostic topic configuration.
    
    Instead of hardcoding "trading", "financial", etc.,
    topics are loaded from configuration file at deploy time.
    """
    
    categories: Dict[str, TopicCategory] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "TopicConfig":
        """
        Load topic configuration from YAML file.
        
        Expected format:
            categories:
              category1:
                name: "Category One"
                keywords: ["key1", "key2"]
                metadata: {priority: high}
              category2:
                name: "Category Two"
                keywords: ["key3", "key4"]
        """
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            categories = {}
            raw_categories = data.get("categories", data)
            
            for cat_id, cat_data in raw_categories.items():
                if isinstance(cat_data, dict):
                    categories[cat_id] = TopicCategory(
                        name=cat_data.get("name", cat_id),
                        keywords=cat_data.get("keywords", []),
                        metadata={
                            k: v for k, v in cat_data.items()
                            if k not in ("name", "keywords")
                        },
                    )
            
            return cls(categories=categories)
            
        except FileNotFoundError:
            return cls(categories={})
        except Exception:
            return cls(categories={})
    
    def get_category(self, category_id: str) -> Optional[TopicCategory]:
        """Get a topic category by ID."""
        return self.categories.get(category_id)
    
    def get_all_keywords(self) -> List[str]:
        """Get all keywords from all categories."""
        keywords = []
        for category in self.categories.values():
            keywords.extend(category.keywords)
        return keywords
    
    def find_category_by_keyword(self, keyword: str) -> Optional[str]:
        """Find category ID that contains the keyword."""
        keyword_lower = keyword.lower()
        for cat_id, category in self.categories.items():
            if keyword_lower in [k.lower() for k in category.keywords]:
                return cat_id
        return None


@dataclass
class BabelConfig:
    """
    Master configuration for Babel Gardens.
    
    All values are configurable - no hardcoded domain-specific terms.
    """
    
    # Model configurations
    embedding: EmbeddingModelConfig = field(default_factory=EmbeddingModelConfig)
    sentiment: SentimentModelConfig = field(default_factory=SentimentModelConfig)
    emotion: EmotionModelConfig = field(default_factory=EmotionModelConfig)
    
    # Language support
    language: LanguageConfig = field(default_factory=LanguageConfig)
    
    # Infrastructure
    cache: CacheConfig = field(default_factory=CacheConfig)
    streams: StreamConfig = field(default_factory=StreamConfig)
    tables: TableConfig = field(default_factory=TableConfig)
    collections: CollectionConfig = field(default_factory=CollectionConfig)
    
    # Topic taxonomy (loaded from YAML at deploy time)
    topics: TopicConfig = field(default_factory=TopicConfig)
    
    # Synthesis settings
    divine_weights: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.7,
        "sentiment": 0.3,
    })


# Singleton pattern
_config: Optional[BabelConfig] = None


def get_config() -> BabelConfig:
    """Get or create global BabelConfig singleton."""
    global _config
    if _config is None:
        _config = BabelConfig()
    return _config


def set_config(config: BabelConfig) -> None:
    """Set the global BabelConfig (for testing or runtime injection)."""
    global _config
    _config = config


def load_config_from_yaml(
    config_path: Optional[Path] = None,
    topics_path: Optional[Path] = None,
) -> BabelConfig:
    """
    Load BabelConfig from YAML files.
    
    Args:
        config_path: Path to main config YAML (optional)
        topics_path: Path to topics taxonomy YAML (optional)
        
    Returns:
        Configured BabelConfig instance
    """
    config = BabelConfig()
    
    if topics_path and topics_path.exists():
        topics = TopicConfig.from_yaml(topics_path)
        config = BabelConfig(
            embedding=config.embedding,
            sentiment=config.sentiment,
            emotion=config.emotion,
            language=config.language,
            cache=config.cache,
            streams=config.streams,
            tables=config.tables,
            collections=config.collections,
            topics=topics,
            divine_weights=config.divine_weights,
        )
    
    set_config(config)
    return config
