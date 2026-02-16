# api_gemma_cognitive/modules/embedding_engine.py
"""
🧮 Embedding Engine Module
High-performance multilingual embedding generation with Gemma models
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import numpy as np
from datetime import datetime
import aiohttp

from ..shared import GemmaServiceBase, model_manager, vector_cache
from ..config import get_config
from ..schemas import (
    EmbeddingRequest, BatchEmbeddingRequest, EmbeddingResponse, 
    BatchEmbeddingResponse, SimilarityRequest, SimilarityResponse, 
    LanguageCode, ModelType
)

logger = logging.getLogger(__name__)


def _normalize_embedding_base_url(raw_url: str) -> str:
    """Normalize embedding service URL to host:port base (no endpoint suffix)."""
    url = (raw_url or "").strip().rstrip("/")
    for suffix in ("/v1/embeddings", "/embed"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url

class EmbeddingEngineModule(GemmaServiceBase):
    """
    🚀 Advanced embedding generation engine
    Supports multilingual, domain-specific embeddings with caching
    """
    
    def __init__(self):
        super().__init__("embedding_engine")
        self.name = "EmbeddingEngine"
        self.version = "1.0.0"
        self.max_batch_size = 32
        self.max_text_length = 8192
        self.supported_languages = set(lang.value for lang in LanguageCode)
        self.language_detection_cache = {}
        # Cooperative embedding API (resolved from config/env; docker default: embedding:8010)
        cfg = get_config()
        env_url = os.getenv("EMBEDDING_SERVICE_URL")
        configured_url = env_url or cfg.embedding.url
        self.embedding_api_url = _normalize_embedding_base_url(configured_url)
        self.use_cooperative_api = True  # Flag to enable/disable cooperation
        self.session = None
    
    async def _initialize_service(self):
        """Service-specific initialization for embedding engine"""
        # Initialize HTTP session for cooperative API calls
        self.session = aiohttp.ClientSession()
    
    async def initialize(self, model_manager, vector_cache, integrity_watcher):
        """Initialize embedding engine"""
        await super().initialize(model_manager, vector_cache, integrity_watcher)
        
        # Preload embedding models
        await model_manager.preload_models(["gemma_embeddings", "gemma_multilingual"])
        
        logger.info("🧮 Embedding Engine Module initialized")
    
    async def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Create embedding for single text
        
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
            if request.use_cache:
                cached_embedding = await vector_cache.get_embedding(
                    request.text,
                    request.model_type.value,
                    request.language.value
                )
                if cached_embedding is not None:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    return EmbeddingResponse(
                        status="success",
                        embedding=cached_embedding,
                        metadata={
                            "language": request.language.value,
                            "model_type": request.model_type.value,
                            "cached": True,
                            "processing_time_ms": processing_time,
                            "dimension": len(cached_embedding)
                        }
                    )
            
            # Detect language if auto
            detected_language = await self._detect_language(request.text, request.language)
            
            # Select appropriate model
            model_key = self._select_model(request.model_type, detected_language)
            model = await model_manager.get_model(model_key)
            tokenizer = await model_manager.get_tokenizer(model_key)
            
            if model is None or tokenizer is None:
                return EmbeddingResponse(
                    status="error",
                    embedding=[],
                    metadata={},
                    error=f"Failed to load model: {model_key}"
                )
            
            # Generate embedding
            embedding = await self._generate_embedding(
                request.text, model, tokenizer, model_key
            )
            
            # Cache result
            if request.use_cache and embedding:
                await vector_cache.set_embedding(
                    request.text,
                    embedding,
                    request.model_type.value,
                    detected_language
                )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EmbeddingResponse(
                status="success",
                embedding=embedding,
                metadata={
                    "language": detected_language,
                    "model_type": request.model_type.value,
                    "model_key": model_key,
                    "cached": False,
                    "processing_time_ms": processing_time,
                    "dimension": len(embedding) if embedding else 0
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Embedding generation error: {str(e)}")
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
        try:
            start_time = datetime.now()
            
            # Try cooperative API first
            if self.use_cooperative_api:
                logger.info(f"[BABEL GARDENS COOPERATIVE] Creating financial embedding: {text[:50]}...")
                cooperative_result = await self._call_cooperative_embedding_api(text, language)
                
                if cooperative_result["success"]:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    return EmbeddingResponse(
                        status="success",
                        embedding=cooperative_result["embedding"],
                        metadata={
                            "language": language,
                            "model_type": "financial",
                            "cached": False,
                            "processing_time_ms": processing_time,
                            "dimension": cooperative_result["dimension"],
                            "cooperative_mode": True,
                            "model_used": "sentence-transformers/all-MiniLM-L6-v2",
                            "api_processing_time": cooperative_result.get("processing_time", 0)
                        }
                    )
                else:
                    logger.warning(f"[BABEL GARDENS COOPERATIVE] ⚠️ API failed, falling back to local: {cooperative_result['error']}")
            
            # Fallback to original implementation
            request = EmbeddingRequest(
                text=text,
                language=LanguageCode(language if language in [l.value for l in LanguageCode] else "auto"),
                model_type=ModelType.FINANCIAL,
                use_cache=use_cache
            )
            
            return await self.create_embedding(request)
            
        except Exception as e:
            logger.error(f"[BABEL GARDENS COOPERATIVE] ❌ Financial embedding error: {str(e)}")
            return EmbeddingResponse(
                status="error",
                embedding=[],
                metadata={},
                error=str(e)
            )
    
    async def create_multilingual_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Create multilingual-optimized embedding via cooperative API
        Specialized for complex languages and cultural contexts
        
        Args:
            request: Embedding request with text and language parameters
            
        Returns:
            Embedding response optimized for multilingual analysis
        """
        try:
            start_time = datetime.now()
            
            # Try cooperative API first for multilingual processing
            if self.use_cooperative_api:
                logger.info(f"[BABEL GARDENS MULTILINGUAL] Creating embedding for {request.language.value}: {request.text[:50]}...")
                cooperative_result = await self._call_cooperative_embedding_api(
                    request.text, 
                    request.language.value if request.language != LanguageCode.AUTO else "auto"
                )
                
                if cooperative_result["success"]:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Detect actual language if auto was requested
                    detected_language = request.language.value
                    if request.language == LanguageCode.AUTO:
                        detected_language = await self._detect_language(request.text, request.language)
                    
                    return EmbeddingResponse(
                        status="success",
                        embedding=cooperative_result["embedding"],
                        metadata={
                            "language": detected_language,
                            "model_type": "multilingual",
                            "cached": False,
                            "processing_time_ms": processing_time,
                            "dimension": cooperative_result["dimension"],
                            "cooperative_mode": True,
                            "multilingual_specialized": True,
                            "model_used": "sentence-transformers/all-MiniLM-L6-v2",
                            "api_processing_time": cooperative_result.get("processing_time", 0),
                            "complexity_level": self._assess_language_complexity(detected_language)
                        }
                    )
                else:
                    logger.warning(f"[BABEL GARDENS MULTILINGUAL] ⚠️ API failed, falling back to local: {cooperative_result['error']}")
            
            # Fallback to create_embedding with multilingual optimizations
            return await self.create_embedding(request)
            
        except Exception as e:
            logger.error(f"[BABEL GARDENS MULTILINGUAL] ❌ Multilingual embedding error: {str(e)}")
            return EmbeddingResponse(
                status="error",
                embedding=[],
                metadata={},
                error=str(e)
            )
    
    def _assess_language_complexity(self, language_code: str) -> str:
        """Assess complexity level of language for specialized processing"""
        complex_languages = {"ar", "zh", "ja", "ko", "he", "th", "hi", "ru"}
        moderate_languages = {"es", "it", "fr", "de", "pt", "pl", "nl"}
        
        if language_code in complex_languages:
            return "high"
        elif language_code in moderate_languages:
            return "moderate"
        else:
            return "standard"
    
    async def create_batch_embeddings(self, request: BatchEmbeddingRequest) -> BatchEmbeddingResponse:
        """
        Create embeddings for multiple texts
        
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
            
            # Validate batch size
            if len(request.texts) > self.max_batch_size:
                return BatchEmbeddingResponse(
                    status="error", 
                    embeddings=[],
                    metadata={},
                    error=f"Batch size {len(request.texts)} exceeds limit {self.max_batch_size}"
                )
            
            # Check cache for existing embeddings
            cached_embeddings, missing_texts = await vector_cache.batch_get_embeddings(
                request.texts,
                request.model_type.value,
                request.language.value
            ) if request.use_cache else ([None] * len(request.texts), request.texts)
            
            # Generate embeddings for missing texts
            missing_embeddings = {}
            if missing_texts:
                # Detect language for missing texts
                detected_language = await self._detect_language(
                    " ".join(missing_texts[:3]), request.language  # Sample for detection
                )
                
                # Select model
                model_key = self._select_model(request.model_type, detected_language)
                model = await model_manager.get_model(model_key)
                tokenizer = await model_manager.get_tokenizer(model_key)
                
                if model is None or tokenizer is None:
                    return BatchEmbeddingResponse(
                        status="error",
                        embeddings=[],
                        metadata={},
                        error=f"Failed to load model: {model_key}"
                    )
                
                # Generate embeddings in batches
                batch_size = min(16, len(missing_texts))
                for i in range(0, len(missing_texts), batch_size):
                    batch_texts = missing_texts[i:i + batch_size]
                    batch_embeddings = await self._generate_batch_embeddings(
                        batch_texts, model, tokenizer, model_key
                    )
                    
                    for text, embedding in zip(batch_texts, batch_embeddings):
                        missing_embeddings[text] = embedding
                
                # Cache new embeddings
                if request.use_cache:
                    cache_pairs = [(text, emb) for text, emb in missing_embeddings.items() if emb]
                    if cache_pairs:
                        await vector_cache.batch_set_embeddings(
                            cache_pairs,
                            request.model_type.value,
                            detected_language
                        )
            
            # Combine cached and new embeddings
            final_embeddings = []
            cache_hits = 0
            
            for i, text in enumerate(request.texts):
                if cached_embeddings[i] is not None:
                    final_embeddings.append(cached_embeddings[i])
                    cache_hits += 1
                else:
                    embedding = missing_embeddings.get(text, [])
                    final_embeddings.append(embedding)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return BatchEmbeddingResponse(
                status="success",
                embeddings=final_embeddings,
                metadata={
                    "total_texts": len(request.texts),
                    "cache_hits": cache_hits,
                    "new_embeddings": len(missing_texts),
                    "language": detected_language if missing_texts else request.language.value,
                    "model_type": request.model_type.value,
                    "processing_time_ms": processing_time,
                    "average_dimension": np.mean([len(emb) for emb in final_embeddings if emb])
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Batch embedding error: {str(e)}")
            return BatchEmbeddingResponse(
                status="error",
                embeddings=[],
                metadata={},
                error=str(e)
            )
    
    async def compute_similarity(self, request: SimilarityRequest) -> SimilarityResponse:
        """
        Compute similarity between two texts
        
        Args:
            request: Similarity request with two texts
            
        Returns:
            Similarity response with score
        """
        try:
            start_time = datetime.now()
            
            # Check cache first
            cached_similarity = await vector_cache.get_similarity(
                request.text1, request.text2, request.language.value
            )
            if cached_similarity is not None:
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                return SimilarityResponse(
                    status="success",
                    similarity_score=cached_similarity,
                    metadata={
                        "language": request.language.value,
                        "cached": True,
                        "processing_time_ms": processing_time
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
            await vector_cache.set_similarity(
                request.text1, request.text2, similarity_score, request.language.value
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SimilarityResponse(
                status="success",
                similarity_score=similarity_score,
                metadata={
                    "language": request.language.value,
                    "cached": False,
                    "processing_time_ms": processing_time,
                    "embedding_dimensions": [len(emb) for emb in embeddings]
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Similarity computation error: {str(e)}")
            return SimilarityResponse(
                status="error",
                similarity_score=0.0,
                metadata={},
                error=str(e)
            )
    
    # ===========================
    # PRIVATE HELPER METHODS
    # ===========================
    
    async def _detect_language(self, text: str, language: LanguageCode) -> str:
        """Detect or validate language with enhanced multilingual support"""
        if language != LanguageCode.AUTO:
            return language.value
        
        # Cache language detection results
        text_hash = hash(text[:100])
        if text_hash in self.language_detection_cache:
            return self.language_detection_cache[text_hash]
        
        # Enhanced language detection with Unicode range analysis
        text_sample = text[:200].lower()
        
        # Arabic script detection (U+0600 to U+06FF, U+0750 to U+077F)
        if any(0x0600 <= ord(char) <= 0x06FF or 0x0750 <= ord(char) <= 0x077F for char in text):
            detected = LanguageCode.ARABIC.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Chinese script detection (CJK Unified Ideographs)
        if any(0x4E00 <= ord(char) <= 0x9FFF for char in text):
            detected = LanguageCode.CHINESE.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Japanese script detection (Hiragana, Katakana, Kanji)
        if any(0x3040 <= ord(char) <= 0x309F or 0x30A0 <= ord(char) <= 0x30FF or 0x4E00 <= ord(char) <= 0x9FFF for char in text):
            detected = LanguageCode.JAPANESE.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Korean script detection (Hangul)
        if any(0xAC00 <= ord(char) <= 0xD7AF or 0x1100 <= ord(char) <= 0x11FF for char in text):
            detected = LanguageCode.KOREAN.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Hebrew script detection (U+0590 to U+05FF)
        if any(0x0590 <= ord(char) <= 0x05FF for char in text):
            detected = LanguageCode.HEBREW.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Russian/Cyrillic detection (U+0400 to U+04FF)
        if any(0x0400 <= ord(char) <= 0x04FF for char in text):
            detected = LanguageCode.RUSSIAN.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Italian indicators
        if any(word in text_sample for word in ['della', 'delle', 'degli', 'questa', 'questo', 'anche', 'come', 'quando']):
            detected = LanguageCode.ITALIAN.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Spanish indicators  
        if any(word in text_sample for word in ['esta', 'este', 'estos', 'estas', 'para', 'donde', 'como', 'cuando']):
            detected = LanguageCode.SPANISH.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # French indicators
        if any(word in text_sample for word in ['cette', 'avec', 'dans', 'pour', 'mais', 'comme', 'où']):
            detected = LanguageCode.FRENCH.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # German indicators
        if any(word in text_sample for word in ['der', 'die', 'das', 'und', 'mit', 'für', 'ist', 'nicht']):
            detected = LanguageCode.GERMAN.value
            self.language_detection_cache[text_hash] = detected
            return detected
        
        # Default to English
        detected = LanguageCode.ENGLISH.value
        self.language_detection_cache[text_hash] = detected
        return detected
    
    def _select_model(self, model_type: ModelType, language: str) -> str:
        """Select appropriate model based on type and language"""
        if model_type == ModelType.FINANCIAL:
            return "gemma_embeddings"
        elif language in ["ja", "zh", "ar", "es", "it"]:
            return "gemma_multilingual"
        else:
            return "gemma_embeddings"
    
    async def _generate_embedding(
        self, text: str, model: Any, tokenizer: Any, model_key: str
    ) -> List[float]:
        """Generate single embedding"""
        try:
            # Check if it's a sentence-transformers model
            if hasattr(model, 'encode'):
                # Use sentence-transformers encode method
                embedding = model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
            
            # Fallback to transformers method
            # Tokenize
            inputs = tokenizer(
                text,
                return_tensors="pt",
                max_length=self.max_text_length,
                truncation=True,
                padding=True
            )
            
            # Move to GPU if available
            if torch.cuda.is_available() and next(model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                outputs = model(**inputs)
                # Use last hidden state, mean pooling
                embeddings = outputs.last_hidden_state
                attention_mask = inputs['attention_mask']
                
                # Mean pooling with attention mask
                masked_embeddings = embeddings * attention_mask.unsqueeze(-1)
                summed = torch.sum(masked_embeddings, dim=1)
                lengths = torch.sum(attention_mask, dim=1, keepdim=True)
                embedding = summed / lengths
                
                # Normalize
                embedding = F.normalize(embedding, p=2, dim=1)
                
                return embedding.cpu().numpy().flatten().tolist()
        
        except Exception as e:
            logger.error(f"❌ Embedding generation error: {str(e)}")
            return []
    
    async def _generate_batch_embeddings(
        self, texts: List[str], model: Any, tokenizer: Any, model_key: str
    ) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        try:
            # Check if it's a sentence-transformers model
            if hasattr(model, 'encode'):
                # Use sentence-transformers encode method
                embeddings = model.encode(texts, convert_to_tensor=False)
                return [emb.tolist() for emb in embeddings]
            
            # Fallback to transformers method
            # Tokenize batch
            inputs = tokenizer(
                texts,
                return_tensors="pt",
                max_length=self.max_text_length,
                truncation=True,
                padding=True
            )
            
            # Move to GPU if available
            if torch.cuda.is_available() and next(model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                outputs = model(**inputs)
                embeddings = outputs.last_hidden_state
                attention_mask = inputs['attention_mask']
                
                # Mean pooling with attention mask
                masked_embeddings = embeddings * attention_mask.unsqueeze(-1)
                summed = torch.sum(masked_embeddings, dim=1)
                lengths = torch.sum(attention_mask, dim=1, keepdim=True)
                pooled_embeddings = summed / lengths
                
                # Normalize
                normalized_embeddings = F.normalize(pooled_embeddings, p=2, dim=1)
                
                return [emb.cpu().numpy().tolist() for emb in normalized_embeddings]
        
        except Exception as e:
            logger.error(f"❌ Batch embedding generation error: {str(e)}")
            return [[] for _ in texts]
    
    def _compute_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        try:
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
            logger.error(f"❌ Similarity computation error: {str(e)}")
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for embedding engine"""
        try:
            # Check if models are loaded
            models_status = {}
            for model_key in ["gemma_embeddings", "gemma_multilingual"]:
                model_info = model_manager.get_model_info(model_key)
                models_status[model_key] = {
                    "loaded": model_info["loaded"] if model_info else False,
                    "last_used": model_info["last_used"].isoformat() if model_info and model_info["last_used"] else None
                }
            
            # Test embedding generation
            test_result = "not_tested"
            try:
                test_request = EmbeddingRequest(
                    text="Test embedding generation",
                    language=LanguageCode.ENGLISH,
                    model_type=ModelType.GENERAL,
                    use_cache=False
                )
                test_response = await self.create_embedding(test_request)
                test_result = "success" if test_response.status == "success" else "failed"
            except Exception as e:
                test_result = f"failed: {str(e)}"
            
            return {
                "status": "healthy",
                "module": self.name,
                "version": self.version,
                "models": models_status,
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
    
    async def _call_cooperative_embedding_api(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Call cooperative embedding API using configured embedding base URL."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.embedding_api_url}/v1/embeddings/create"
            payload = {
                "text": text,
                "language": language
            }
            
            logger.info(f"[GEMMA COOPERATIVE] Calling embedding API: {url}")
            
            async with self.session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        logger.info(f"[GEMMA COOPERATIVE] ✅ Success, embedding dim: {data.get('dimension', 0)}")
                        return {
                            "success": True,
                            "embedding": data.get("embedding", []),
                            "dimension": data.get("dimension", 0),
                            "processing_time": data.get("processing_time_ms", 0),
                            "cooperative": True
                        }
                    else:
                        logger.error(f"[GEMMA COOPERATIVE] ❌ API returned error: {data.get('error')}")
                        return {"success": False, "error": data.get("error", "Unknown API error")}
                else:
                    error_text = await response.text()
                    logger.error(f"[GEMMA COOPERATIVE] ❌ HTTP {response.status}: {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"[GEMMA COOPERATIVE] ❌ Exception: {str(e)}")
            return {"success": False, "error": str(e)}
