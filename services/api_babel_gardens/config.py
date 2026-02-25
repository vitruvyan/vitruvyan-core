"""
Babel Gardens Service Configuration
====================================

Centralized environment variable loading.
ALL os.getenv() calls must be here.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


def _default_postgres_host() -> str:
    """
    Resolve sensible default PostgreSQL host.

    - In Docker containers: use compose service name (`mercator_postgres`)
    - On host/dev shell: use localhost (port-mapped container)
    """
    if os.getenv("POSTGRES_HOST"):
        return os.getenv("POSTGRES_HOST")
    if os.path.exists("/.dockerenv"):
        return "mercator_postgres"
    return "localhost"


def _default_postgres_port(resolved_host: str) -> int:
    """
    Resolve sensible default PostgreSQL port.

    - Docker internal network uses 5432
    - Host/dev shell typically reaches Mercator DB via mapped 2432
    """
    if os.getenv("POSTGRES_PORT"):
        return int(os.getenv("POSTGRES_PORT"))
    return 5432 if resolved_host == "mercator_postgres" else 2432


@dataclass(frozen=True)
class ServiceConfig:
    """Service-level configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8009
    debug: bool = False
    log_level: str = "INFO"
    babel_domain: str = "generic"


@dataclass(frozen=True)
class EmbeddingServiceConfig:
    """External embedding service configuration."""
    
    url: str = "http://localhost:8010"
    endpoint: str = "/v1/embeddings"
    timeout: float = 30.0
    max_retries: int = 3


@dataclass(frozen=True)
class SentimentServiceConfig:
    """External sentiment service configuration."""
    
    url: str = "http://localhost:8010"
    endpoint: str = "/v1/sentiment"
    timeout: float = 10.0


@dataclass(frozen=True)
class QdrantServiceConfig:
    """Qdrant vector store configuration."""
    
    host: str = "localhost"
    port: int = 6333
    collection_semantic: str = "babel_semantic"
    collection_sentiment: str = "babel_sentiment"


@dataclass(frozen=True)
class PostgresServiceConfig:
    """PostgreSQL configuration."""
    
    host: str = "localhost"
    port: int = 2432
    database: str = "mercator"
    user: str = "mercator_user"
    password: str = "mercator_pass"


@dataclass(frozen=True)
class RedisServiceConfig:
    """Redis configuration."""
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0


@dataclass
class Config:
    """Master service configuration."""
    
    service: ServiceConfig = field(default_factory=ServiceConfig)
    embedding: EmbeddingServiceConfig = field(default_factory=EmbeddingServiceConfig)
    sentiment: SentimentServiceConfig = field(default_factory=SentimentServiceConfig)
    qdrant: QdrantServiceConfig = field(default_factory=QdrantServiceConfig)
    postgres: PostgresServiceConfig = field(default_factory=PostgresServiceConfig)
    redis: RedisServiceConfig = field(default_factory=RedisServiceConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        resolved_pg_host = _default_postgres_host()
        resolved_pg_port = _default_postgres_port(resolved_pg_host)

        return cls(
            service=ServiceConfig(
                host=os.getenv("HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", "8009")),
                debug=os.getenv("DEBUG", "false").lower() == "true",
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                babel_domain=os.getenv("BABEL_DOMAIN", "generic"),
            ),
            embedding=EmbeddingServiceConfig(
                url=os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8010"),
                endpoint=os.getenv("EMBEDDING_ENDPOINT", "/v1/embeddings"),
                timeout=float(os.getenv("EMBEDDING_TIMEOUT", "30.0")),
                max_retries=int(os.getenv("EMBEDDING_RETRIES", "3")),
            ),
            sentiment=SentimentServiceConfig(
                url=os.getenv("SENTIMENT_SERVICE_URL", "http://localhost:8010"),
                endpoint=os.getenv("SENTIMENT_ENDPOINT", "/v1/sentiment"),
                timeout=float(os.getenv("SENTIMENT_TIMEOUT", "10.0")),
            ),
            qdrant=QdrantServiceConfig(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
                collection_semantic=os.getenv("QDRANT_COLLECTION_SEMANTIC", "babel_semantic"),
                collection_sentiment=os.getenv("QDRANT_COLLECTION_SENTIMENT", "babel_sentiment"),
            ),
            postgres=PostgresServiceConfig(
                host=resolved_pg_host,
                port=resolved_pg_port,
                database=os.getenv("POSTGRES_DB", "mercator"),
                user=os.getenv("POSTGRES_USER", "mercator_user"),
                password=os.getenv("POSTGRES_PASSWORD", "mercator_pass"),
            ),
            redis=RedisServiceConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
            ),
        )


# Singleton
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create service configuration."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
