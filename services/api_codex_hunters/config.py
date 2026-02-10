"""
Codex Hunters API Service Configuration
=======================================

Centralized environment variable loading.
All configurable values must be defined here - no os.getenv() elsewhere.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ServiceConfig:
    """Service-level configuration (host, port, debug)."""
    
    host: str = "0.0.0.0"
    port: int = 8008
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 1


@dataclass(frozen=True)
class PostgresConfig:
    """PostgreSQL connection configuration."""
    
    host: str = "172.17.0.1"
    port: int = 5432
    database: str = "vitruvyan"
    user: str = "vitruvyan"
    password: str = ""


@dataclass(frozen=True)
class QdrantConfig:
    """Qdrant vector database configuration."""
    
    host: str = "172.17.0.1"
    port: int = 6333
    grpc_port: int = 6334


@dataclass(frozen=True)
class RedisConfig:
    """Redis Streams configuration."""
    
    host: str = "172.17.0.1"
    port: int = 6379
    db: int = 0


@dataclass(frozen=True)
class CodexHuntersConfig:
    """Complete Codex Hunters service configuration."""
    
    service: ServiceConfig = field(default_factory=ServiceConfig)
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)


def load_config() -> CodexHuntersConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        CodexHuntersConfig: Complete service configuration.
    """
    service = ServiceConfig(
        host=os.getenv("CODEX_API_HOST", "0.0.0.0"),
        port=int(os.getenv("CODEX_API_PORT", "8008")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        workers=int(os.getenv("WORKERS", "1")),
    )
    
    postgres = PostgresConfig(
        host=os.getenv("POSTGRES_HOST", "172.17.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "vitruvyan"),
        user=os.getenv("POSTGRES_USER", "vitruvyan"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )
    
    qdrant = QdrantConfig(
        host=os.getenv("QDRANT_HOST", "172.17.0.1"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        grpc_port=int(os.getenv("QDRANT_GRPC_PORT", "6334")),
    )
    
    redis = RedisConfig(
        host=os.getenv("REDIS_HOST", "172.17.0.1"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
    )
    
    return CodexHuntersConfig(
        service=service,
        postgres=postgres,
        qdrant=qdrant,
        redis=redis,
    )


# Singleton configuration instance
_config: Optional[CodexHuntersConfig] = None


def get_config() -> CodexHuntersConfig:
    """Get or create the singleton configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: CodexHuntersConfig) -> None:
    """Set the configuration instance (for testing)."""
    global _config
    _config = config
