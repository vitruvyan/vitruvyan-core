"""Embedding API — Persistence Adapter (Qdrant + PostgreSQL)."""

from ..services.embedding_service import EmbeddingService

# EmbeddingService already encapsulates PostgresAgent + QdrantAgent access.
# This module re-exports it as the canonical persistence adapter.
PersistenceAdapter = EmbeddingService
