"""
Pattern Weavers Service Configuration
=====================================

Centralized environment variable loading for LIVELLO 2.
ALL os.getenv() calls should stay in this file.
"""

import os
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Optional


def _default_postgres_host() -> str:
    """
    Resolve sensible default PostgreSQL host.

    - In Docker containers: use compose service name (`mercator_postgres`)
    - On host/dev shell: use localhost (port-mapped DB)
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
    - Host/dev shell reaches Mercator DB via mapped 2432
    """
    if os.getenv("POSTGRES_PORT"):
        return int(os.getenv("POSTGRES_PORT"))
    return 5432 if resolved_host == "mercator_postgres" else 2432


def _default_taxonomy_path(pattern_domain: str) -> str:
    """
    Resolve taxonomy path.

    Finance mode gets a canonical bundled taxonomy unless explicitly overridden
    by PATTERN_TAXONOMY_PATH.
    """
    explicit = os.getenv("PATTERN_TAXONOMY_PATH")
    if explicit:
        return explicit

    if pattern_domain != "finance":
        return ""

    try:
        candidate = resources.files("domains.finance.pattern_weavers").joinpath(
            "taxonomy_finance.yaml"
        )
        if candidate.is_file():
            return str(candidate)
    except Exception:
        try:
            candidate = resources.files(
                "vitruvyan_core.domains.finance.pattern_weavers"
            ).joinpath("taxonomy_finance.yaml")
            if candidate.is_file():
                return str(candidate)
        except Exception:
            pass

    candidates = [
        Path(__file__).resolve().parents[2]
        / "vitruvyan_core/domains/finance/pattern_weavers/taxonomy_finance.yaml",
        Path("/app/vitruvyan_core/domains/finance/pattern_weavers/taxonomy_finance.yaml"),
        Path("/app/domains/finance/pattern_weavers/taxonomy_finance.yaml"),
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return ""


@dataclass(frozen=True)
class ServiceConfig:
    """Service runtime configuration."""

    host: str = "0.0.0.0"
    port: int = 8011
    debug: bool = False
    log_level: str = "INFO"
    pattern_domain: str = "generic"
    cors_allowed_origins: str = "http://localhost:3000"


@dataclass(frozen=True)
class EmbeddingServiceConfig:
    """Embedding service connection config."""

    url: str = "http://localhost:8010"
    endpoint: str = "/v1/embeddings/create"
    timeout: float = 5.0


@dataclass(frozen=True)
class QdrantServiceConfig:
    """Qdrant connection config."""

    host: str = "localhost"
    port: int = 6333
    collection: str = "patterns"


@dataclass(frozen=True)
class PostgresServiceConfig:
    """PostgreSQL connection config."""

    host: str = "localhost"
    port: int = 2432
    database: str = "mercator"
    user: str = "mercator_user"
    password: str = "mercator_pass"


@dataclass(frozen=True)
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
        pattern_domain = os.getenv("PATTERN_DOMAIN", "generic")
        resolved_pg_host = _default_postgres_host()
        resolved_pg_port = _default_postgres_port(resolved_pg_host)

        return cls(
            service=ServiceConfig(
                host=os.getenv("PATTERN_HOST", os.getenv("HOST", "0.0.0.0")),
                port=int(os.getenv("PATTERN_PORT", os.getenv("PORT", "8011"))),
                debug=os.getenv("DEBUG", "false").lower() == "true",
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                pattern_domain=pattern_domain,
                cors_allowed_origins=os.getenv(
                    "CORS_ALLOWED_ORIGINS",
                    os.getenv("CORS_ORIGINS", "http://localhost:3000"),
                ),
            ),
            embedding=EmbeddingServiceConfig(
                url=os.getenv("EMBEDDING_URL", "http://localhost:8010"),
                endpoint=os.getenv("EMBEDDING_ENDPOINT", "/v1/embeddings/create"),
                timeout=float(os.getenv("EMBEDDING_TIMEOUT", "5.0")),
            ),
            qdrant=QdrantServiceConfig(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
                collection=os.getenv("PATTERN_COLLECTION", "patterns"),
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
            taxonomy_path=_default_taxonomy_path(pattern_domain),
        )


# Singleton
_config: Optional[Config] = None


def get_config() -> Config:
    """Get service configuration (lazy loading)."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
