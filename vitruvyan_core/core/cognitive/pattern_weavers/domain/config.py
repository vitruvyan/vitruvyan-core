"""
Pattern Weavers - Domain Configuration
======================================

Parametric configuration for Pattern Weavers - all domain-specific values
are configurable, NEVER hardcoded.

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026 - Domain-Agnostic Refactoring)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for embedding service."""
    
    api_url: str = "http://localhost:8010"
    endpoint: str = "/v1/embeddings/multilingual"
    dimension: int = 384
    timeout_seconds: float = 5.0
    cache_ttl_hours: int = 168  # 7 days


@dataclass(frozen=True)
class CollectionConfig:
    """Configuration for Qdrant collections."""
    
    embeddings: str = "patterns"
    taxonomy: str = "taxonomy"


@dataclass(frozen=True)
class TableConfig:
    """Configuration for PostgreSQL tables."""
    
    weave_logs: str = "weave_logs"
    taxonomy: str = "pattern_taxonomy"
    audit: str = "weave_audit"


@dataclass(frozen=True)
class StreamConfig:
    """Configuration for Redis Streams channels."""
    
    prefix: str = "pattern"
    request: str = "pattern.weave.request"
    response: str = "pattern.weave.response"
    error: str = "pattern.weave.error"


@dataclass(frozen=True)
class TaxonomyCategory:
    """A single taxonomic category (e.g., concept, entity type, domain-specific classification)."""
    
    name: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaxonomyConfig:
    """
    Domain-agnostic taxonomy configuration.
    
    Instead of hardcoding "Banking", "Healthcare", etc., 
    taxonomy is loaded from configuration file at deploy time.
    """
    
    categories: Dict[str, List[TaxonomyCategory]] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "TaxonomyConfig":
        """
        Load taxonomy from YAML file.
        
        Expected format:
            categories:
              concepts:
                - name: "Category1"
                  keywords: ["key1", "key2"]
                  metadata: {priority: "high", source: "manual"}
              entities:
                - name: "Entity1"
                  keywords: ["ent1", "ent2"]
                  metadata: {domain: "finance"}
        
        Metadata is domain-specific and NOT interpreted by Pattern Weavers.
        """
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            categories = {}
            raw_categories = data.get("categories", data)  # Backward compat
            
            for category_type, items in raw_categories.items():
                if isinstance(items, list):
                    categories[category_type] = [
                        TaxonomyCategory(
                            name=item.get("name", ""),
                            keywords=item.get("keywords", []),
                            metadata={
                                k: v for k, v in item.items()
                                if k not in ("name", "keywords")
                            },
                        )
                        for item in items
                        if isinstance(item, dict)
                    ]
            
            return cls(categories=categories)
            
        except FileNotFoundError:
            return cls(categories={})
        except Exception:
            return cls(categories={})
    
    def get_category(self, category_type: str) -> List[TaxonomyCategory]:
        """Get categories by type."""
        return self.categories.get(category_type, [])
    
    def get_all_keywords(self, category_type: str) -> List[str]:
        """Get all keywords for a category type."""
        keywords = []
        for cat in self.get_category(category_type):
            keywords.extend(cat.keywords)
        return keywords


@dataclass
class PatternConfig:
    """
    Master configuration for Pattern Weavers.
    
    All domain-specific values are in sub-configs.
    Default values are domain-agnostic placeholders.
    """
    
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    collection: CollectionConfig = field(default_factory=CollectionConfig)
    table: TableConfig = field(default_factory=TableConfig)
    stream: StreamConfig = field(default_factory=StreamConfig)
    taxonomy: TaxonomyConfig = field(default_factory=TaxonomyConfig)
    
    # Processing parameters
    top_k: int = 10
    similarity_threshold: float = 0.4
    max_query_length: int = 2000
    default_language: str = "auto"
    
    @classmethod
    def from_env(cls) -> "PatternConfig":
        """
        Create config from environment variables.
        
        Environment variables:
            PATTERN_EMBEDDING_URL: Embedding service URL
            PATTERN_COLLECTION_EMBEDDINGS: Qdrant collection name
            PATTERN_TABLE_LOGS: PostgreSQL table name
            PATTERN_STREAM_PREFIX: Redis Streams prefix
            PATTERN_TAXONOMY_PATH: Path to taxonomy YAML
            PATTERN_TOP_K: Default top_k
            PATTERN_SIMILARITY_THRESHOLD: Default threshold
        """
        import os
        
        taxonomy_path = os.getenv("PATTERN_TAXONOMY_PATH", "")
        taxonomy = (
            TaxonomyConfig.from_yaml(Path(taxonomy_path))
            if taxonomy_path
            else TaxonomyConfig()
        )
        
        return cls(
            embedding=EmbeddingConfig(
                api_url=os.getenv("PATTERN_EMBEDDING_URL", "http://localhost:8010"),
                endpoint=os.getenv("PATTERN_EMBEDDING_ENDPOINT", "/v1/embeddings/multilingual"),
                dimension=int(os.getenv("PATTERN_EMBEDDING_DIM", "384")),
            ),
            collection=CollectionConfig(
                embeddings=os.getenv("PATTERN_COLLECTION_EMBEDDINGS", "patterns"),
                taxonomy=os.getenv("PATTERN_COLLECTION_TAXONOMY", "taxonomy"),
            ),
            table=TableConfig(
                weave_logs=os.getenv("PATTERN_TABLE_LOGS", "weave_logs"),
                taxonomy=os.getenv("PATTERN_TABLE_TAXONOMY", "pattern_taxonomy"),
                audit=os.getenv("PATTERN_TABLE_AUDIT", "weave_audit"),
            ),
            stream=StreamConfig(
                prefix=os.getenv("PATTERN_STREAM_PREFIX", "pattern"),
                request=os.getenv("PATTERN_STREAM_REQUEST", "pattern.weave.request"),
                response=os.getenv("PATTERN_STREAM_RESPONSE", "pattern.weave.response"),
            ),
            taxonomy=taxonomy,
            top_k=int(os.getenv("PATTERN_TOP_K", "10")),
            similarity_threshold=float(os.getenv("PATTERN_SIMILARITY_THRESHOLD", "0.4")),
        )


# Global configuration instance (set by service layer)
_config: Optional[PatternConfig] = None


def get_config() -> PatternConfig:
    """Get the current Pattern Weavers configuration."""
    global _config
    if _config is None:
        _config = PatternConfig()
    return _config


def set_config(config: PatternConfig) -> None:
    """Set the Pattern Weavers configuration (call at service startup)."""
    global _config
    _config = config
