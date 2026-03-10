# services/api_embedding/schemas.py
"""Pydantic request/response models for Embedding API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Single text embedding request."""
    text: str = Field(..., description="Text to embed")
    model: Optional[str] = Field("nomic-ai/nomic-embed-text-v1.5", description="Model to use")
    store_in_qdrant: Optional[bool] = Field(True, description="Store in Qdrant collection")
    collection_name: Optional[str] = Field("phrases_embeddings", description="Qdrant collection")


class BatchEmbeddingRequest(BaseModel):
    """Batch embedding request."""
    texts: List[str] = Field(..., description="List of texts to embed")
    model: Optional[str] = Field("nomic-ai/nomic-embed-text-v1.5", description="Model to use")
    store_in_qdrant: Optional[bool] = Field(False, description="Store in Qdrant collection")
    collection_name: Optional[str] = Field("phrases_embeddings", description="Qdrant collection")


class EmbeddingResponse(BaseModel):
    """Embedding response."""
    success: bool
    embedding: Optional[List[float]] = None
    embeddings: Optional[List[List[float]]] = None
    dimension: Optional[int] = None
    model_used: Optional[str] = None
    processing_time_ms: Optional[float] = None
    stored_in_qdrant: Optional[bool] = None
    error: Optional[str] = None


class SyncRequest(BaseModel):
    """Postgres to Qdrant sync request."""
    limit: Optional[int] = Field(100, description="Number of records to sync")
    offset: Optional[int] = Field(0, description="Starting offset")


class SyncResponse(BaseModel):
    """Sync response."""
    success: bool
    records_processed: int
    records_embedded: int
    processing_time_ms: float
    error: Optional[str] = None
