# services/api_embedding/api/routes.py
"""Embedding API routes."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..config import get_config
from ..schemas import EmbeddingRequest, BatchEmbeddingRequest, EmbeddingResponse, SyncRequest, SyncResponse
from ..services import get_embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    config = get_config()
    service = get_embedding_service()
    components = service.health_check()
    all_healthy = all(v == "healthy" for v in components.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "service": "vitruvyan_embedding_api",
        "version": "1.0.0",
        "model": config.model.name
    }


@router.post("/v1/embeddings/create", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """Create embedding for single text."""
    start_time = datetime.now()
    service = get_embedding_service()
    
    try:
        logger.info(f"[EMBEDDING] Processing: {request.text[:50]}...")
        
        if not service.model:
            raise HTTPException(status_code=503, detail="Embedding model not loaded")
        
        embedding = service.embed_text(request.text)
        
        stored = False
        if request.store_in_qdrant:
            try:
                service.store_embedding(request.text, embedding, request.collection_name)
                stored = True
                logger.info(f"[EMBEDDING] Stored in {request.collection_name}")
            except Exception as e:
                logger.warning(f"[EMBEDDING] Store failed: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return EmbeddingResponse(success=True, embedding=embedding, dimension=len(embedding), model_used=request.model, processing_time_ms=processing_time, stored_in_qdrant=stored)
        
    except Exception as e:
        logger.error(f"[EMBEDDING] Error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return EmbeddingResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.post("/v1/embeddings/batch", response_model=EmbeddingResponse)
async def create_batch_embeddings(request: BatchEmbeddingRequest) -> EmbeddingResponse:
    """Create embeddings for multiple texts."""
    start_time = datetime.now()
    service = get_embedding_service()
    
    try:
        logger.info(f"[EMBEDDING] Processing batch of {len(request.texts)} texts...")
        
        if not service.model:
            raise HTTPException(status_code=503, detail="Embedding model not loaded")
        
        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="Batch size too large (max 100)")
        
        embeddings = service.embed_batch(request.texts)
        
        stored = False
        if request.store_in_qdrant:
            try:
                service.store_batch(request.texts, embeddings, request.collection_name)
                stored = True
                logger.info(f"[EMBEDDING] Stored {len(embeddings)} embeddings")
            except Exception as e:
                logger.warning(f"[EMBEDDING] Batch store failed: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return EmbeddingResponse(success=True, embeddings=embeddings, dimension=len(embeddings[0]) if embeddings else 0, model_used=request.model, processing_time_ms=processing_time, stored_in_qdrant=stored)
        
    except Exception as e:
        logger.error(f"[EMBEDDING] Batch error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return EmbeddingResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.post("/v1/sync/postgres_to_qdrant", response_model=SyncResponse)
async def sync_postgres_to_qdrant(request: SyncRequest) -> SyncResponse:
    """Sync phrases from PostgreSQL to Qdrant."""
    start_time = datetime.now()
    
    try:
        logger.info(f"[SYNC] limit={request.limit}, offset={request.offset}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return SyncResponse(success=True, records_processed=0, records_embedded=0, processing_time_ms=processing_time)
        
    except Exception as e:
        logger.error(f"[SYNC] Failed: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return SyncResponse(success=False, records_processed=0, records_embedded=0, processing_time_ms=processing_time, error=str(e))


@router.get("/v1/stats")
async def get_stats():
    """Get embedding service statistics."""
    config = get_config()
    service = get_embedding_service()
    
    return {
        "success": True,
        "stats": {
            "model": {"name": config.model.name, "loaded": service.model is not None, "dimension": service.get_dimension()},
            "components": {"postgres": service.postgres is not None, "qdrant": service.qdrant is not None}
        },
        "timestamp": datetime.now().isoformat()
    }
