#!/usr/bin/env python3
"""
🧮 Vitruvyan Embedding API Server
Expose MiniLM embedding functionality as HTTP service for Gemma cooperation
"""

import asyncio
import logging
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import numpy as np
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import existing components
from sentence_transformers import SentenceTransformer
from core.agents import PostgresAgent
from core.agents import QdrantAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vitruvyan Embedding API",
    description="MiniLM embedding service for Gemma cooperation",
    version="1.0.0"
)

# ===========================
# REQUEST/RESPONSE MODELS
# ===========================

class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to embed")
    model: Optional[str] = Field("sentence-transformers/all-MiniLM-L6-v2", description="Model to use")
    store_in_qdrant: Optional[bool] = Field(True, description="Store in Qdrant collection")
    collection_name: Optional[str] = Field("phrases_embeddings", description="Qdrant collection")

class BatchEmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to embed")
    model: Optional[str] = Field("sentence-transformers/all-MiniLM-L6-v2", description="Model to use")
    store_in_qdrant: Optional[bool] = Field(False, description="Store in Qdrant collection")
    collection_name: Optional[str] = Field("phrases_embeddings", description="Qdrant collection")

class EmbeddingResponse(BaseModel):
    success: bool
    embedding: Optional[List[float]] = None
    embeddings: Optional[List[List[float]]] = None
    dimension: Optional[int] = None
    model_used: Optional[str] = None
    processing_time_ms: Optional[float] = None
    stored_in_qdrant: Optional[bool] = None
    error: Optional[str] = None

class SyncRequest(BaseModel):
    limit: Optional[int] = Field(100, description="Number of records to sync")
    offset: Optional[int] = Field(0, description="Starting offset")

class SyncResponse(BaseModel):
    success: bool
    records_processed: int
    records_embedded: int
    processing_time_ms: float
    error: Optional[str] = None

# ===========================
# GLOBAL COMPONENTS
# ===========================

embedding_model: Optional[SentenceTransformer] = None
postgres_agent: Optional[PostgresAgent] = None
qdrant_agent: Optional[QdrantAgent] = None

# Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "phrases_embeddings"

# ===========================
# STARTUP/SHUTDOWN
# ===========================

@app.on_event("startup")
async def startup_event():
    """Initialize embedding engine and connections"""
    global embedding_model, postgres_agent, qdrant_agent
    
    try:
        logger.info("🚀 Starting Vitruvyan Embedding API Server...")
        
        # Initialize connections (synchronous constructors)
        logger.info("🔌 Connecting to PostgreSQL...")
        postgres_agent = PostgresAgent()
        logger.info("✅ PostgreSQL connection established")
        
        logger.info("🔌 Connecting to Qdrant...")
        qdrant_agent = QdrantAgent()
        logger.info("✅ Qdrant connection established")
        
        # Initialize embedding model
        logger.info(f"🤖 Loading model: {MODEL_NAME}")
        embedding_model = SentenceTransformer(MODEL_NAME)
        logger.info("✅ Embedding model loaded")
        
        logger.info("🎯 Embedding API Server ready on port 8010")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        logger.error(traceback.format_exc())
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    global embedding_model, postgres_agent, qdrant_agent
    
    logger.info("🔄 Shutting down Embedding API Server...")
    
    if postgres_agent and hasattr(postgres_agent, 'connection'):
        try:
            postgres_agent.connection.close()
            logger.info("✅ PostgreSQL connection closed")
        except Exception as e:
            logger.warning(f"PostgreSQL cleanup error: {e}")
    
    embedding_model = None
    postgres_agent = None
    qdrant_agent = None
    
    logger.info("✅ Shutdown complete")

# ===========================
# API ENDPOINTS
# ===========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check component health
        pg_healthy = False
        qdrant_healthy = False
        
        if postgres_agent:
            try:
                # Test PostgreSQL connection
                with postgres_agent.connection.cursor() as cur:
                    cur.execute("SELECT 1")
                    pg_healthy = True
            except Exception as e:
                logger.warning(f"PostgreSQL health check failed: {e}")
        
        if qdrant_agent:
            try:
                # Test Qdrant connection
                health_result = qdrant_agent.health()
                qdrant_healthy = health_result.get("status") == "ok"
            except Exception as e:
                logger.warning(f"Qdrant health check failed: {e}")
        
        model_healthy = embedding_model is not None
        
        return {
            "status": "healthy" if all([pg_healthy, qdrant_healthy, model_healthy]) else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "postgres": "healthy" if pg_healthy else "unhealthy",
                "qdrant": "healthy" if qdrant_healthy else "unhealthy",
                "embedding_model": "healthy" if model_healthy else "unhealthy"
            },
            "service": "vitruvyan_embedding_api",
            "version": "1.0.0",
            "model": MODEL_NAME
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/v1/embeddings/create", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """Create embedding for single text"""
    start_time = datetime.now()
    
    try:
        logger.info(f"[EMBEDDING] Processing text: {request.text[:50]}...")
        
        if not embedding_model:
            raise HTTPException(status_code=503, detail="Embedding model not loaded")
        
        # Generate embedding
        embedding = embedding_model.encode(request.text).tolist()
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Store in Qdrant if requested
        stored = False
        if request.store_in_qdrant and qdrant_agent:
            try:
                point_id = f"text_{int(datetime.now().timestamp() * 1000)}"
                points = [{
                    "id": point_id,
                    "vector": embedding,
                    "payload": {
                        "text": request.text,
                        "model": request.model,
                        "timestamp": datetime.now().isoformat()
                    }
                }]
                
                qdrant_agent.upsert(
                    collection=request.collection_name,
                    points=points
                )
                stored = True
                logger.info(f"[EMBEDDING] Stored in Qdrant collection: {request.collection_name}")
            except Exception as e:
                logger.warning(f"[EMBEDDING] Failed to store in Qdrant: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EmbeddingResponse(
            success=True,
            embedding=embedding,
            dimension=len(embedding),
            model_used=request.model,
            processing_time_ms=processing_time,
            stored_in_qdrant=stored
        )
        
    except Exception as e:
        logger.error(f"[EMBEDDING] Error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return EmbeddingResponse(
            success=False,
            processing_time_ms=processing_time,
            error=str(e)
        )

@app.post("/v1/embeddings/batch", response_model=EmbeddingResponse)
async def create_batch_embeddings(request: BatchEmbeddingRequest) -> EmbeddingResponse:
    """Create embeddings for multiple texts"""
    start_time = datetime.now()
    
    try:
        logger.info(f"[EMBEDDING] Processing batch of {len(request.texts)} texts...")
        
        if not embedding_model:
            raise HTTPException(status_code=503, detail="Embedding model not loaded")
        
        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="Batch size too large (max 100)")
        
        # Generate embeddings
        embeddings = embedding_model.encode(request.texts).tolist()
        
        if not embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate embeddings")
        
        # Store in Qdrant if requested
        stored = False
        if request.store_in_qdrant and qdrant_agent:
            try:
                points = []
                for i, (text, embedding) in enumerate(zip(request.texts, embeddings)):
                    point_id = f"batch_{int(datetime.now().timestamp() * 1000)}_{i}"
                    points.append({
                        "id": point_id,
                        "vector": embedding,
                        "payload": {
                            "text": text,
                            "model": request.model,
                            "batch_index": i,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                
                qdrant_agent.upsert(
                    collection=request.collection_name,
                    points=points
                )
                stored = True
                logger.info(f"[EMBEDDING] Stored {len(embeddings)} embeddings in Qdrant")
            except Exception as e:
                logger.warning(f"[EMBEDDING] Failed to store batch in Qdrant: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EmbeddingResponse(
            success=True,
            embeddings=embeddings,
            dimension=len(embeddings[0]) if embeddings else 0,
            model_used=request.model,
            processing_time_ms=processing_time,
            stored_in_qdrant=stored
        )
        
    except Exception as e:
        logger.error(f"[EMBEDDING] Batch error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return EmbeddingResponse(
            success=False,
            processing_time_ms=processing_time,
            error=str(e)
        )

@app.post("/v1/sync/postgres_to_qdrant", response_model=SyncResponse)
async def sync_postgres_to_qdrant(request: SyncRequest, background_tasks: BackgroundTasks) -> SyncResponse:
    """Sync phrases from PostgreSQL to Qdrant (background task)"""
    
    start_time = datetime.now()
    
    try:
        logger.info(f"[SYNC] Sync request received: limit={request.limit}, offset={request.offset}")
        
        if not all([postgres_agent, qdrant_agent, embedding_model]):
            raise HTTPException(status_code=503, detail="Required components not initialized")
        
        # For now, return a placeholder response
        # TODO: Implement full sync functionality with proper database queries
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SyncResponse(
            success=True,
            records_processed=0,
            records_embedded=0,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"[SYNC] Sync request failed: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return SyncResponse(
            success=False,
            records_processed=0,
            records_embedded=0,
            processing_time_ms=processing_time,
            error=str(e)
        )

@app.get("/v1/stats")
async def get_stats():
    """Get embedding service statistics"""
    try:
        stats = {
            "model": {
                "name": MODEL_NAME,
                "loaded": embedding_model is not None,
                "dimension": embedding_model.get_sentence_embedding_dimension() if embedding_model else None
            },
            "components": {
                "postgres": postgres_agent is not None,
                "qdrant": qdrant_agent is not None
            }
        }
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[STATS] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===========================
# MAIN SERVER
# ===========================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010,
        reload=False,
        log_level="info"
    )