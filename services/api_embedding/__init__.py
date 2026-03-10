"""
API Embedding — Cognitive Service (Tier 1)
Sacred Order: Perception (Order I)

Embedding service for semantic vectorization using SentenceTransformers.
Provides HTTP API for Nomic embeddings with Qdrant storage integration.

Architecture:
- Model: nomic-ai/nomic-embed-text-v1.5 (768 dimensions)
- Storage: Qdrant collections (phrases_embeddings, semantic_states)
- Caching: PostgreSQL + Qdrant cooperative storage

Dependencies:
- Foundation Tier 0: PostgresAgent, QdrantAgent (from persistence)

Endpoints:
- POST /embed - Single text embedding
- POST /embed/batch - Batch embedding
- GET /health - Health check
- GET /sacred-health - Sacred Orders health status
"""

__version__ = "1.0.0"
__sacred_order__ = "Perception (Order I)"
