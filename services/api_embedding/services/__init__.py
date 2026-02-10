# services/api_embedding/services/__init__.py
"""Embedding service components."""

from .embedding_service import EmbeddingService, get_embedding_service

__all__ = ["EmbeddingService", "get_embedding_service"]
