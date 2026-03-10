# services/api_embedding/config.py
"""Centralized configuration for Embedding API."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    """Service configuration."""
    port: int = 8010
    log_level: str = "INFO"


@dataclass(frozen=True)
class ModelConfig:
    """Embedding model configuration."""
    name: str = "nomic-ai/nomic-embed-text-v1.5"
    collection_name: str = "phrases_embeddings"


@dataclass(frozen=True)
class EmbeddingConfig:
    """Master configuration."""
    service: ServiceConfig
    model: ModelConfig


_config: EmbeddingConfig = None


def get_config() -> EmbeddingConfig:
    """Get or create configuration from environment."""
    global _config
    if _config is None:
        _config = EmbeddingConfig(
            service=ServiceConfig(
                port=int(os.getenv("PORT", "8010")),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
            ),
            model=ModelConfig(
                name=os.getenv("EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5"),
                collection_name=os.getenv("QDRANT_COLLECTION", "phrases_embeddings"),
            ),
        )
    return _config
