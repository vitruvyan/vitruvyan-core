"""
Codex Hunters - Domain Configuration
====================================

Domain-agnostic configuration dataclasses.
All values are parametric - no hardcoded domain-specific references.

Values are injected at runtime from:
- Environment variables (LIVELLO 2 service layer)
- Configuration files (future: YAML/JSON)
- Domain-specific configuration providers

Author: Vitruvyan Core Team
Created: February 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml


@dataclass(frozen=True)
class SourceConfig:
    """Configuration for a single data source."""
    name: str
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    description: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class CollectionConfig:
    """Configuration for a storage collection (Qdrant/vector store)."""
    name: str
    vector_size: int = 384
    distance_metric: str = "Cosine"
    description: str = ""


@dataclass(frozen=True)
class TableConfig:
    """Configuration for a database table (PostgreSQL)."""
    name: str
    schema: str = "public"
    primary_key: str = "id"
    description: str = ""


@dataclass(frozen=True)
class StreamConfig:
    """Configuration for event stream channels."""
    prefix: str = "codex"
    discovery_channel: str = "entity.discovered"
    restoration_channel: str = "entity.restored"
    binding_channel: str = "entity.bound"
    expedition_channel: str = "expedition.completed"
    
    def channel(self, event_type: str) -> str:
        """Build full channel name."""
        return f"{self.prefix}.{event_type}"


@dataclass(frozen=True)
class QualityConfig:
    """Configuration for data quality scoring."""
    
    threshold_valid: float = 0.5  # Minimum score for VALID status
    penalty_per_error: float = 0.1  # Score deduction per validation error
    penalty_null_ratio: float = 0.3  # Score deduction for null field ratio
    max_null_ratio: float = 0.5  # Maximum allowed null field ratio


@dataclass
class CodexConfig:
    """
    Master configuration for Codex Hunters.
    
    All values are domain-agnostic defaults.
    Override via environment variables or config files at runtime.
    
    Example usage:
        # Default (domain-agnostic)
        config = CodexConfig()
        
        # Domain-specific override (via code)
        config = CodexConfig(
            entity_table=TableConfig(name="products"),
            embedding_collection=CollectionConfig(name="product_embeddings"),
            streams=StreamConfig(prefix="codex.ecommerce")
        )
        
        # Domain-specific override (via YAML)
        config = CodexConfig.from_yaml("config/healthcare.yaml")
    """
    
    # Entity storage (PostgreSQL)
    entity_table: TableConfig = field(
        default_factory=lambda: TableConfig(
            name="entities",
            description="Primary entity storage"
        )
    )
    
    # Embedding storage (Qdrant)
    embedding_collection: CollectionConfig = field(
        default_factory=lambda: CollectionConfig(
            name="entity_embeddings",
            vector_size=384,
            description="Entity semantic embeddings"
        )
    )
    
    # Additional collections (domain can add more)
    collections: Dict[str, CollectionConfig] = field(default_factory=dict)
    
    # Additional tables (domain can add more)
    tables: Dict[str, TableConfig] = field(default_factory=dict)
    
    # Data sources (domain provides implementations)
    sources: Dict[str, SourceConfig] = field(
        default_factory=lambda: {
            "primary": SourceConfig(
                name="primary",
                rate_limit_per_minute=100,
                description="Primary data source"
            ),
            "secondary": SourceConfig(
                name="secondary",
                rate_limit_per_minute=30,
                description="Secondary data source"
            )
        }
    )
    
    # Event streams configuration
    streams: StreamConfig = field(default_factory=StreamConfig)
    
    # Quality scoring configuration
    quality: QualityConfig = field(default_factory=QualityConfig)
    
    # Embedding model (domain-agnostic default)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Expedition settings
    default_batch_size: int = 100
    max_concurrent_expeditions: int = 5
    expedition_timeout_seconds: int = 300
    
    def get_collection(self, key: str) -> Optional[CollectionConfig]:
        """Get collection config by key, or embedding_collection if 'default'."""
        if key == "default" or key == "embeddings":
            return self.embedding_collection
        return self.collections.get(key)
    
    def get_table(self, key: str) -> Optional[TableConfig]:
        """Get table config by key, or entity_table if 'default'."""
        if key == "default" or key == "entities":
            return self.entity_table
        return self.tables.get(key)
    
    def get_source(self, key: str) -> Optional[SourceConfig]:
        """Get source config by key."""
        return self.sources.get(key)
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "CodexConfig":
        """
        Load CodexConfig from YAML file.
        
        Expected format:
            entity_table:
              name: "my_entities"
              schema: "public"
            embedding_collection:
              name: "my_embeddings"
              vector_size: 384
            sources:
              source1:
                name: "Source One"
                rate_limit_per_minute: 100
            quality:
              threshold_valid: 0.6
              penalty_per_error: 0.15
        """
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            # Parse entity table
            entity_table = CodexConfig().entity_table  # default
            if "entity_table" in data:
                et_data = data["entity_table"]
                entity_table = TableConfig(
                    name=et_data.get("name", "entities"),
                    schema=et_data.get("schema", "public"),
                    primary_key=et_data.get("primary_key", "id"),
                    description=et_data.get("description", "")
                )
            
            # Parse embedding collection
            embedding_collection = CodexConfig().embedding_collection  # default
            if "embedding_collection" in data:
                ec_data = data["embedding_collection"]
                embedding_collection = CollectionConfig(
                    name=ec_data.get("name", "entity_embeddings"),
                    vector_size=ec_data.get("vector_size", 384),
                    distance_metric=ec_data.get("distance_metric", "Cosine"),
                    description=ec_data.get("description", "")
                )
            
            # Parse streams (optional)
            streams = StreamConfig()
            if "streams" in data and isinstance(data["streams"], dict):
                s_data = data["streams"]
                streams = StreamConfig(
                    prefix=s_data.get("prefix", streams.prefix),
                    discovery_channel=s_data.get("discovery_channel", streams.discovery_channel),
                    restoration_channel=s_data.get("restoration_channel", streams.restoration_channel),
                    binding_channel=s_data.get("binding_channel", streams.binding_channel),
                    expedition_channel=s_data.get("expedition_channel", streams.expedition_channel),
                )

            # Parse sources
            sources = {}
            if "sources" in data:
                for src_key, src_data in data["sources"].items():
                    sources[src_key] = SourceConfig(
                        name=src_data.get("name", src_key),
                        rate_limit_per_minute=src_data.get("rate_limit_per_minute", 60),
                        timeout_seconds=src_data.get("timeout_seconds", 30),
                        retry_attempts=src_data.get("retry_attempts", 3),
                        description=src_data.get("description", ""),
                        enabled=src_data.get("enabled", True)
                    )
            
            # Parse quality config
            quality = QualityConfig()
            if "quality" in data:
                q_data = data["quality"]
                quality = QualityConfig(
                    threshold_valid=q_data.get("threshold_valid", 0.5),
                    penalty_per_error=q_data.get("penalty_per_error", 0.1),
                    penalty_null_ratio=q_data.get("penalty_null_ratio", 0.3),
                    max_null_ratio=q_data.get("max_null_ratio", 0.5)
                )
            
            return cls(
                entity_table=entity_table,
                embedding_collection=embedding_collection,
                sources=sources if sources else cls().sources,
                streams=streams,
                quality=quality,
                embedding_model=data.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
                embedding_dimension=data.get("embedding_dimension", 384),
                default_batch_size=data.get("default_batch_size", 100),
                max_concurrent_expeditions=data.get("max_concurrent_expeditions", 5),
                expedition_timeout_seconds=data.get("expedition_timeout_seconds", 300)
            )
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")


# Default singleton instance (can be replaced at runtime)
_default_config: Optional[CodexConfig] = None


def get_config() -> CodexConfig:
    """Get current configuration (creates default if none set)."""
    global _default_config
    if _default_config is None:
        _default_config = CodexConfig()
    return _default_config


def set_config(config: CodexConfig) -> None:
    """Set configuration (called by service layer at startup)."""
    global _default_config
    _default_config = config
