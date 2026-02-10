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


@dataclass
class CodexConfig:
    """
    Master configuration for Codex Hunters.
    
    All values are domain-agnostic defaults.
    Override via environment variables or config files at runtime.
    
    Example usage:
        # Default (domain-agnostic)
        config = CodexConfig()
        
        # Finance domain override
        config = CodexConfig(
            entity_table=TableConfig(name="tickers"),
            embedding_collection=CollectionConfig(name="ticker_embeddings"),
            streams=StreamConfig(prefix="codex.finance")
        )
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
