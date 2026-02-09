# api_gemma_cognitive/modules/embedding_engine_cooperative.py
"""
🔗 Embedding Engine Module - Cooperative Version
High-performance embedding generation via cooperation with vitruvyan_api_embedding:8010
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..shared import GemmaServiceBase, vector_cache
from ..schemas import (
    EmbeddingRequest, BatchEmbeddingRequest, EmbeddingResponse, 
    BatchEmbeddingResponse, SimilarityRequest, SimilarityResponse, 
    LanguageCode, ModelType
)

logger = logging.getLogger(__name__)

class EmbeddingEngineCooperative(GemmaServiceBase):
    """
    🤝 Cooperative Embedding Engine
    Delegates embedding generation to vitruvyan_api_embedding:8010
    Provides intelligent caching and fallback mechanisms
    """
    
    def __init__(self):
        super().__init__("embedding_engine_cooperative")
        self.name = "EmbeddingEngineCooperative"
        self.version = "2.0.0"
        self.embedding_api_url = "http://vitruvyan_api_embedding:8010"  # Docker service name
        self.embedding_api_url_fallback = "http://localhost:8010"  # Local fallback
        self.max_batch_size = 32
        self.max_text_length = 8192
        self.supported_languages = set(lang.value for lang in LanguageCode)
        self.timeout = 30  # seconds
        self.session = None
        self.api_healthy = False
        
    async def _initialize_service(self):
        """Service-specific initialization for cooperative embedding engine"""
        # Create aiohttp session for API calls
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Test API connection
        await self._test_api_connection()
        
        logger.info(f"🤝 Cooperative Embedding Engine initialized - API healthy: {self.api_healthy}")
    
    async def initialize(self, model_manager, vector_cache, integrity_watcher):
        """Initialize cooperative embedding engine"""
        # Store references but don't use model_manager since we use external API
        self.vector_cache = vector_cache
        self.integrity_watcher = integrity_watcher
        
        await self._initialize_service()
        
        logger.info("🤝 Embedding Engine Cooperative Module initialized")
    
    async def _test_api_connection(self):
        """Test connection to embedding API"""
        try:
            # Try primary URL first
            test_url = f"{self.embedding_api_url}/health"
            logger.info(f"[GEMMA] Testing embedding API connection: {test_url}")
            
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"[GEMMA] ✅ Primary embedding API healthy: {health_data}")
                    self.api_healthy = True
                    return
                    
        except Exception as e:
            logger.warning(f"[GEMMA] Primary embedding API unavailable: {e}")
        
        try:
            # Try fallback URL
            test_url = f"{self.embedding_api_url_fallback}/health"
            logger.info(f"[GEMMA] Testing fallback embedding API: {test_url}")
            
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"[GEMMA] ✅ Fallback embedding API healthy: {health_data}")
                    self.embedding_api_url = self.embedding_api_url_fallback
                    self.api_healthy = True
                    return
                    
        except Exception as e:
            logger.error(f"[GEMMA] ❌ Both embedding APIs unavailable: {e}")
            self.api_healthy = False
    
    async def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Create embedding for single text via cooperative API call
        
        Args:
            request: Embedding request with text and parameters
            
        Returns:
            Embedding response with vector and metadata
        """
        try:
            start_time = datetime.now()
            
            # Input validation
            if len(request.text.strip()) == 0:
                return EmbeddingResponse(
                    status="error",
                    embedding=[],
                    metadata={},
                    error="Empty text provided"
                )
            
            # Check cache first
            if request.use_cache and self.vector_cache:
                cached_embedding = await self.vector_cache.get_embedding(
                    request.text,
                    request.model_type.value,
                    request.language.value
                )
                if cached_embedding is not None:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"[GEMMA] ✅ Cache hit for embedding: {request.text[:50]}...")
                    return EmbeddingResponse(
                        status="success",
                        embedding=cached_embedding,
                        metadata={
                            "language": request.language.value,
                            "model_type": request.model_type.value,
                            "cached": True,
                            "processing_time_ms": processing_time,
                            "dimension": len(cached_embedding),
                            "cooperative_mode": True
                        }
                    )
            
            # Check API health
            if not self.api_healthy:
                await self._test_api_connection()
                if not self.api_healthy:
                    return EmbeddingResponse(
                        status="error",
                        embedding=[],
                        metadata={},
                        error="Embedding API service unavailable"
                    )
            
            # Call cooperative embedding API
            embedding_result = await self._call_embedding_api(request.text, request.language.value)
            
            if not embedding_result["success"]:
                return EmbeddingResponse(
                    status="error",
                    embedding=[],
                    metadata={},
                    error=embedding_result["error"]
                )
            
            embedding = embedding_result["embedding"]
            api_metadata = embedding_result["metadata"]
            
            # Cache result
            if request.use_cache and embedding and self.vector_cache:
                await self.vector_cache.set_embedding(
                    request.text,
                    embedding,
                    request.model_type.value,
                    request.language.value
                )
                logger.info(f"[GEMMA] ✅ Cached new embedding: {request.text[:50]}...")
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EmbeddingResponse(
                status="success",
                embedding=embedding,
                metadata={
                    "language": request.language.value,
                    "model_type": request.model_type.value,
                    "cached": False,
                    "processing_time_ms": processing_time,
                    "dimension": len(embedding) if embedding else 0,
                    "cooperative_mode": True,
                    "api_metadata": api_metadata
                }
            )
            
        except Exception as e:
            logger.error(f"[GEMMA] ❌ Cooperative embedding generation error: {str(e)}")
            return EmbeddingResponse(
                status="error",
                embedding=[],
                metadata={},
                error=str(e)
            )
    
    async def create_financial_embedding(self, text: str, language: str = "auto", use_cache: bool = True) -> EmbeddingResponse:
        """
        Create financial-optimized embedding via cooperative API
        
        Args:
            text: Text to embed
            language: Language code (auto-detect if 'auto')
            use_cache: Whether to use cache
            
        Returns:
            Embedding response optimized for financial analysis
        """
        logger.info(f"[GEMMA] Creating financial embedding for: {text[:50]}...")
        
        # Create embedding request with financial optimizations
        request = EmbeddingRequest(
            text=text,
            language=LanguageCode(language if language in [l.value for l in LanguageCode] else "auto"),
            model_type=ModelType.FINANCIAL,  # Use financial-optimized model
            use_cache=use_cache
        )
        
        return await self.create_embedding(request)
    
    async def create_batch_embeddings(self, request: BatchEmbeddingRequest) -> BatchEmbeddingResponse:
        """
        Create embeddings for multiple texts via cooperative API
        
        Args:
            request: Batch embedding request
            
        Returns:
            Batch embedding response with all vectors
        """
        try:
            start_time = datetime.now()
            
            if not request.texts:
                return BatchEmbeddingResponse(
                    status="error",
                    embeddings=[],
                    metadata={},
                    error="No texts provided"
                )
            
            logger.info(f"[GEMMA] Creating batch embeddings for {len(request.texts)} texts...")
            
            # Validate batch size
            if len(request.texts) > self.max_batch_size:
                return BatchEmbeddingResponse(
                    status="error", 
                    embeddings=[],
                    metadata={},
                    error=f"Batch size {len(request.texts)} exceeds limit {self.max_batch_size}"
                )
            
            # Check cache for existing embeddings
            cached_embeddings = []
            missing_texts = []
            cache_hits = 0
            
            if request.use_cache and self.vector_cache:
                for text in request.texts:
                    cached_embedding = await self.vector_cache.get_embedding(
                        text,
                        request.model_type.value,
                        request.language.value
                    )
                    if cached_embedding is not None:
                        cached_embeddings.append(cached_embedding)
                        cache_hits += 1
                    else:
                        cached_embeddings.append(None)
                        missing_texts.append(text)
            else:
                cached_embeddings = [None] * len(request.texts)
                missing_texts = request.texts
            
            # Generate embeddings for missing texts via batch API
            missing_embeddings = {}
            if missing_texts:
                logger.info(f"[GEMMA] Calling batch API for {len(missing_texts)} missing embeddings...")
                
                batch_result = await self._call_batch_embedding_api(missing_texts, request.language.value)
                
                if batch_result["success"]:
                    for text, embedding in zip(missing_texts, batch_result["embeddings"]):
                        missing_embeddings[text] = embedding
                        
                        # Cache new embeddings
                        if request.use_cache and embedding and self.vector_cache:
                            await self.vector_cache.set_embedding(
                                text,
                                embedding,
                                request.model_type.value,
                                request.language.value
                            )
                else:
                    logger.error(f"[GEMMA] ❌ Batch API failed: {batch_result['error']}")
                    return BatchEmbeddingResponse(
                        status="error",
                        embeddings=[],
                        metadata={},
                        error=batch_result["error"]
                    )
            
            # Combine cached and new embeddings
            final_embeddings = []
            
            for i, text in enumerate(request.texts):
                if cached_embeddings[i] is not None:
                    final_embeddings.append(cached_embeddings[i])
                else:
                    embedding = missing_embeddings.get(text, [])
                    final_embeddings.append(embedding)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"[GEMMA] ✅ Batch embeddings completed: {len(final_embeddings)} embeddings, {cache_hits} cache hits")
            
            return BatchEmbeddingResponse(
                status="success",
                embeddings=final_embeddings,
                metadata={
                    "total_texts": len(request.texts),
                    "cache_hits": cache_hits,
                    "new_embeddings": len(missing_texts),
                    "language": request.language.value,
                    "model_type": request.model_type.value,
                    "processing_time_ms": processing_time,
                    "cooperative_mode": True,
                    "average_dimension": sum(len(emb) for emb in final_embeddings if emb) / len([emb for emb in final_embeddings if emb]) if final_embeddings else 0
                }
            )
            
        except Exception as e:
            logger.error(f"[GEMMA] ❌ Cooperative batch embedding error: {str(e)}")
            return BatchEmbeddingResponse(
                status="error",
                embeddings=[],
                metadata={},
                error=str(e)
            )
    
    async def _call_embedding_api(self, text: str, language: str) -> Dict[str, Any]:
        """Call cooperative embedding API for single text"""
        try:
            url = f"{self.embedding_api_url}/v1/embeddings/create"
            payload = {
                "text": text,
                "language": language
            }
            
            logger.info(f"[GEMMA] Calling embedding API: {url}")
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"[GEMMA] ✅ API call successful, embedding dim: {len(data.get('embedding', []))}")
                    return {
                        "success": True,
                        "embedding": data.get("embedding", []),
                        "metadata": data.get("metadata", {})
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"[GEMMA] ❌ API call failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"API call failed: {response.status} - {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"[GEMMA] ❌ API call exception: {str(e)}")
            # Mark API as unhealthy and retry connection test
            self.api_healthy = False
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_batch_embedding_api(self, texts: List[str], language: str) -> Dict[str, Any]:
        """Call cooperative embedding API for batch of texts"""
        try:
            url = f"{self.embedding_api_url}/v1/embeddings/batch"
            payload = {
                "texts": texts,
                "language": language
            }
            
            logger.info(f"[GEMMA] Calling batch embedding API: {url} with {len(texts)} texts")
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    embeddings = data.get("embeddings", [])
                    logger.info(f"[GEMMA] ✅ Batch API call successful, got {len(embeddings)} embeddings")
                    return {
                        "success": True,
                        "embeddings": embeddings,
                        "metadata": data.get("metadata", {})
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"[GEMMA] ❌ Batch API call failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Batch API call failed: {response.status} - {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"[GEMMA] ❌ Batch API call exception: {str(e)}")
            # Mark API as unhealthy and retry connection test
            self.api_healthy = False
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compute_similarity(self, request: SimilarityRequest) -> SimilarityResponse:
        """
        Compute similarity between two texts via cooperative embeddings
        
        Args:
            request: Similarity request with two texts
            
        Returns:
            Similarity response with score
        """
        try:
            start_time = datetime.now()
            
            logger.info(f"[GEMMA] Computing similarity between texts...")
            
            # Check cache first
            if self.vector_cache:
                cached_similarity = await self.vector_cache.get_similarity(
                    request.text1, request.text2, request.language.value
                )
                if cached_similarity is not None:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"[GEMMA] ✅ Similarity cache hit: {cached_similarity}")
                    return SimilarityResponse(
                        status="success",
                        similarity_score=cached_similarity,
                        metadata={
                            "language": request.language.value,
                            "cached": True,
                            "processing_time_ms": processing_time,
                            "cooperative_mode": True
                        }
                    )
            
            # Generate embeddings for both texts
            embedding_requests = [
                EmbeddingRequest(text=request.text1, language=request.language),
                EmbeddingRequest(text=request.text2, language=request.language)
            ]
            
            embeddings = []
            for emb_req in embedding_requests:
                emb_resp = await self.create_embedding(emb_req)
                if emb_resp.status != "success":
                    return SimilarityResponse(
                        status="error",
                        similarity_score=0.0,
                        metadata={},
                        error=f"Failed to generate embedding: {emb_resp.error}"
                    )
                embeddings.append(emb_resp.embedding)
            
            # Compute cosine similarity
            similarity_score = self._compute_cosine_similarity(embeddings[0], embeddings[1])
            
            # Cache result
            if self.vector_cache:
                await self.vector_cache.set_similarity(
                    request.text1, request.text2, similarity_score, request.language.value
                )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"[GEMMA] ✅ Similarity computed: {similarity_score}")
            
            return SimilarityResponse(
                status="success",
                similarity_score=similarity_score,
                metadata={
                    "language": request.language.value,
                    "cached": False,
                    "processing_time_ms": processing_time,
                    "embedding_dimensions": [len(emb) for emb in embeddings],
                    "cooperative_mode": True
                }
            )
            
        except Exception as e:
            logger.error(f"[GEMMA] ❌ Cooperative similarity computation error: {str(e)}")
            return SimilarityResponse(
                status="error",
                similarity_score=0.0,
                metadata={},
                error=str(e)
            )
    
    def _compute_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        try:
            import numpy as np
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Clamp to valid range
            return float(np.clip(similarity, -1.0, 1.0))
        
        except Exception as e:
            logger.error(f"[GEMMA] ❌ Similarity computation error: {str(e)}")
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cooperative embedding engine"""
        try:
            # Test API connection
            await self._test_api_connection()
            
            # Test embedding generation
            test_result = "not_tested"
            try:
                test_request = EmbeddingRequest(
                    text="Test cooperative embedding generation",
                    language=LanguageCode.ENGLISH,
                    model_type=ModelType.GENERAL,
                    use_cache=False
                )
                test_response = await self.create_embedding(test_request)
                test_result = "success" if test_response.status == "success" else "failed"
            except Exception as e:
                test_result = f"failed: {str(e)}"
            
            return {
                "status": "healthy" if self.api_healthy else "degraded",
                "module": self.name,
                "version": self.version,
                "cooperative_mode": True,
                "embedding_api_url": self.embedding_api_url,
                "api_healthy": self.api_healthy,
                "test_result": test_result,
                "supported_languages": list(self.supported_languages),
                "max_batch_size": self.max_batch_size,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "module": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        if self.session:
            await self.session.close()
            logger.info("[GEMMA] 🔄 HTTP session closed")
    
    def is_healthy(self) -> bool:
        """Check if the module is healthy"""
        return self.api_healthy and self.session is not None