"""
Embedding Routes — HTTP adapter for EmbeddingEngineModule.

Thin delegation layer: validate request → call module → return response.
No business logic here. All logic lives in modules/embedding_engine.py.
"""

import logging
from fastapi import APIRouter, HTTPException

from ..schemas import (
    EmbeddingRequest,
    BatchEmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingResponse,
    SimilarityRequest,
    SimilarityResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])


def _get_service():
    """Lazy import to avoid circular dependency with main.py."""
    from ..main import service
    if service is None:
        raise HTTPException(status_code=503, detail="Babel Gardens not initialized")
    return service


@router.post("/create", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """Create embedding for a single text."""
    svc = _get_service()
    return await svc.semantic_grove.create_embedding(request)


@router.post("/multilingual", response_model=EmbeddingResponse)
async def create_multilingual_embedding(request: EmbeddingRequest):
    """Create multilingual-optimized embedding with language detection."""
    svc = _get_service()
    return await svc.semantic_grove.create_multilingual_embedding(request)


@router.post("/batch", response_model=BatchEmbeddingResponse)
async def create_batch_embeddings(request: BatchEmbeddingRequest):
    """Create embeddings for multiple texts in a single call."""
    svc = _get_service()
    return await svc.semantic_grove.create_batch_embeddings(request)


@router.post("/similarity", response_model=SimilarityResponse)
async def compute_similarity(request: SimilarityRequest):
    """Compute cosine similarity between two texts."""
    svc = _get_service()
    return await svc.semantic_grove.compute_similarity(request)
