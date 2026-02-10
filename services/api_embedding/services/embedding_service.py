# services/api_embedding/services/embedding_service.py
"""Embedding service with model management."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sentence_transformers import SentenceTransformer
from core.agents import PostgresAgent, QdrantAgent
from ..config import get_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages embedding model and storage connections."""
    
    def __init__(self):
        self.config = get_config()
        self.model: Optional[SentenceTransformer] = None
        self.postgres: Optional[PostgresAgent] = None
        self.qdrant: Optional[QdrantAgent] = None
    
    async def initialize(self) -> None:
        """Initialize model and connections."""
        logger.info("🚀 Initializing EmbeddingService...")
        
        logger.info("🔌 Connecting to PostgreSQL...")
        self.postgres = PostgresAgent()
        logger.info("✅ PostgreSQL connected")
        
        logger.info("🔌 Connecting to Qdrant...")
        self.qdrant = QdrantAgent()
        logger.info("✅ Qdrant connected")
        
        logger.info(f"🤖 Loading model: {self.config.model.name}")
        self.model = SentenceTransformer(self.config.model.name)
        logger.info("✅ Embedding model loaded")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("🔄 Cleaning up EmbeddingService...")
        if self.postgres and hasattr(self.postgres, 'connection'):
            try:
                self.postgres.connection.close()
                logger.info("✅ PostgreSQL closed")
            except Exception as e:
                logger.warning(f"PostgreSQL cleanup error: {e}")
        self.model = None
        self.postgres = None
        self.qdrant = None
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.encode(texts).tolist()
    
    def store_embedding(self, text: str, embedding: List[float], collection: str) -> str:
        """Store embedding in Qdrant."""
        if not self.qdrant:
            raise RuntimeError("Qdrant not connected")
        
        point_id = f"text_{int(datetime.now().timestamp() * 1000)}"
        points = [{
            "id": point_id,
            "vector": embedding,
            "payload": {"text": text, "model": self.config.model.name, "timestamp": datetime.now().isoformat()}
        }]
        self.qdrant.upsert(collection=collection, points=points)
        return point_id
    
    def store_batch(self, texts: List[str], embeddings: List[List[float]], collection: str) -> int:
        """Store batch of embeddings in Qdrant."""
        if not self.qdrant:
            raise RuntimeError("Qdrant not connected")
        
        points = []
        base_ts = int(datetime.now().timestamp() * 1000)
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            points.append({
                "id": f"batch_{base_ts}_{i}",
                "vector": embedding,
                "payload": {"text": text, "model": self.config.model.name, "batch_index": i, "timestamp": datetime.now().isoformat()}
            })
        self.qdrant.upsert(collection=collection, points=points)
        return len(points)
    
    def health_check(self) -> Dict[str, Any]:
        """Check component health."""
        pg_healthy = False
        qdrant_healthy = False
        
        if self.postgres:
            try:
                with self.postgres.connection.cursor() as cur:
                    cur.execute("SELECT 1")
                    pg_healthy = True
            except Exception:
                pass
        
        if self.qdrant:
            try:
                result = self.qdrant.health()
                qdrant_healthy = result.get("status") == "ok"
            except Exception:
                pass
        
        return {
            "postgres": "healthy" if pg_healthy else "unhealthy",
            "qdrant": "healthy" if qdrant_healthy else "unhealthy",
            "embedding_model": "healthy" if self.model else "unhealthy",
        }
    
    def get_dimension(self) -> Optional[int]:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension() if self.model else None


_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
