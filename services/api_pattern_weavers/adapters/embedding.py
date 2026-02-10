"""
Embedding Adapter for Pattern Weavers
=====================================

Handles all embedding generation via external services (Babel Gardens).
This is the ONLY place where httpx calls are made.
"""

import logging
from typing import List, Optional

import httpx

from ..config import get_config

logger = logging.getLogger(__name__)


class EmbeddingAdapter:
    """
    Adapter for embedding generation via Babel Gardens.
    
    All httpx/HTTP calls for embeddings are centralized here.
    LIVELLO 1 consumers never make HTTP calls.
    """
    
    def __init__(self):
        """Initialize with config."""
        config = get_config()
        self._base_url = config.embedding.url
        self._endpoint = config.embedding.endpoint
        self._timeout = config.embedding.timeout
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        """Lazy-load httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (empty list on failure)
        """
        try:
            response = self.client.post(
                self._endpoint,
                json={"text": text},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding failed for text: {e}")
            return []
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.post(
                self._endpoint,
                json={"texts": texts},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embeddings", [])
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [[] for _ in texts]
    
    def check_health(self) -> bool:
        """Check if embedding service is healthy."""
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None


# Singleton
_adapter: Optional[EmbeddingAdapter] = None


def get_embedding_adapter() -> EmbeddingAdapter:
    """Get or create embedding adapter singleton."""
    global _adapter
    if _adapter is None:
        _adapter = EmbeddingAdapter()
    return _adapter
