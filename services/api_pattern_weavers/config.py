"""
Pattern Weavers Service Configuration
=====================================

Centralized environment variable loading for LIVELLO 2.
All os.getenv() calls are here - NOT scattered across the codebase.
"""

import os
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Service runtime configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8011
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class EmbeddingServiceConfig:
    """Embedding service connection config."""
    
    url: str = "http://localhost:8010"
    endpoint: str = "/v1/embeddings/multilingual"
    timeout: float = 5.0


@dataclass
class QdrantServiceConfig:
    """Qdrant connection config."""
    
    host: str = "localhost"
    port: int = 6333
    collection: str = "patterns"


@dataclass
class PostgresServiceConfig:
    """PostgreSQL connection config."""
    
    host: str = "localhost"
    port: int = 5432
    database: str = "vitruvyan"
    user: str = "vitruvyan"
    password: str = ""


@dataclass
class RedisServiceConfig:
    """Redis connection config."""
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0


@dataclass
class Config:
    """
    Master service configuration.
    
    All values come from environment variables with sensible defaults.
    """
    
    service: ServiceConfig
    embedding: EmbeddingServiceConfig
    qdrant: QdrantServiceConfig
    postgres: PostgresServiceConfig
    redis: RedisServiceConfig
    taxonomy_path: str
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            service=ServiceConfig(
                host=os.getenv("PATTERN_HOST", "0.0.0.0"),
                port=int(os.getenv("PATTERN_PORT", "8011")),
                debug=os.getenv("DEBUG", "false").lower() == "true",
                log_level=os.getenv("LOG_LEVEL", "INFO"),
            ),
            embedding=EmbeddingServiceConfig(
                url=os.getenv("EMBEDDING_URL", "http://localhost:8010"),
                endpoint=os.getenv("EMBEDDING_ENDPOINT", "/v1/embeddings/multilingual"),
                timeout=float(os.getenv("EMBEDDING_TIMEOUT", "5.0")),
            ),
            qdrant=QdrantServiceConfig(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
                collection=os.getenv("PATTERN_COLLECTION", "patterns"),
            ),
            postgres=PostgresServiceConfig(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "vitruvyan"),
                user=os.getenv("POSTGRES_USER", "vitruvyan"),
                password=os.getenv("POSTGRES_PASSWORD", ""),
            ),
            redis=RedisServiceConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
            ),
            taxonomy_path=os.getenv("PATTERN_TAXONOMY_PATH", ""),
        )


# Singleton
_config: Config = None


def get_config() -> Config:
    """Get service configuration (lazy loading)."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
