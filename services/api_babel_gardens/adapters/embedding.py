"""
Embedding Adapter for Babel Gardens
====================================

Handles all embedding generation via external ML models.
This is the ONLY place where httpx calls are made for embeddings.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_config

logger = logging.getLogger(__name__)


class EmbeddingAdapter:
    """
    Adapter for embedding generation.
    
    All httpx/HTTP calls for embeddings are centralized here.
    LIVELLO 1 consumers never make HTTP calls.
    """
    
    def __init__(self):
        """Initialize with config."""
        config = get_config()
        self._base_url = config.embedding.url
        self._endpoint = config.embedding.endpoint
        self._timeout = config.embedding.timeout
        self._max_retries = config.embedding.max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-load async httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client
    
    @property
    def sync_client(self) -> httpx.Client:
        """Lazy-load sync httpx client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._sync_client
    
    async def get_embedding(
        self,
        text: str,
        model_type: str = "multilingual",
        language: str = "auto",
    ) -> Dict[str, Any]:
        """
        Get embedding for text asynchronously.
        
        Args:
            text: Text to embed
            model_type: Model type (multilingual, sentiment, etc.)
            language: Language hint (auto for detection)
            
        Returns:
            Dict with embedding, dimension, model info
        """
        try:
            response = await self.client.post(
                self._endpoint,
                json={
                    "text": text,
                    "model_type": model_type,
                    "language": language,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            return {"error": str(e), "embedding": []}
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        model_type: str = "multilingual",
    ) -> List[Dict[str, Any]]:
        """Get embeddings for multiple texts."""
        try:
            response = await self.client.post(
                f"{self._endpoint}/batch",
                json={
                    "texts": texts,
                    "model_type": model_type,
                },
            )
            response.raise_for_status()
            return response.json().get("embeddings", [])
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [{"error": str(e)} for _ in texts]
    
    def get_embedding_sync(
        self,
        text: str,
        model_type: str = "multilingual",
    ) -> Dict[str, Any]:
        """Synchronous embedding generation."""
        try:
            response = self.sync_client.post(
                self._endpoint,
                json={
                    "text": text,
                    "model_type": model_type,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Sync embedding failed: {e}")
            return {"error": str(e), "embedding": []}
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text."""
        try:
            response = await self.client.post(
                "/v1/language/detect",
                json={"text": text},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"language": "en", "confidence": 0.0, "error": str(e)}
    
    async def check_health(self) -> bool:
        """Check if embedding service is healthy."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP clients."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None


# Singleton
_adapter: Optional[EmbeddingAdapter] = None


def get_embedding_adapter() -> EmbeddingAdapter:
    """Get or create embedding adapter singleton."""
    global _adapter
    if _adapter is None:
        _adapter = EmbeddingAdapter()
    return _adapter
