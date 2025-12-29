# api_gemma_cognitive/shared/vector_cache.py
"""
🗃️ Unified Vector Cache
Redis-based caching for embeddings, sentiments, and computed results
"""

import asyncio
import json
import hashlib
import logging
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import numpy as np
import redis.asyncio as redis
from redis.asyncio import Redis

from .base_service import GemmaServiceBase

logger = logging.getLogger(__name__)

class UnifiedVectorCache(GemmaServiceBase):
    """
    🚀 High-performance vector and result caching
    Supports embeddings, sentiment results, and general JSON data
    """
    
    def __init__(self):
        super().__init__("unified_vector_cache")
        self.redis_client: Optional[Redis] = None
        self.prefix = "gemma_cognitive"
        self.default_ttl = 3600 * 24  # 24 hours
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }
    
    async def _initialize_service(self):
        """Service-specific initialization for vector cache"""
        # This will be called by the base class initialize method
        pass
    
    async def initialize(self):
        """Initialize Redis connection"""
        await super().initialize()
        
        try:
            # Initialize Redis connection
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            self.redis_client = None
    
    def _generate_key(self, namespace: str, identifier: str, **kwargs) -> str:
        """Generate cache key with namespace and parameters"""
        # Create deterministic hash from identifier and kwargs
        content = f"{identifier}_{json.dumps(kwargs, sort_keys=True)}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{self.prefix}:{namespace}:{hash_suffix}"
    
    async def get_embedding(
        self, 
        text: str, 
        model_type: str = "financial",
        language: str = "auto"
    ) -> Optional[List[float]]:
        """Get cached embedding"""
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_key(
                "embeddings", 
                text, 
                model_type=model_type,
                language=language
            )
            
            cached_data = await self.redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
                self.stats["hits"] += 1
                logger.debug(f"🎯 Embedding cache hit: {key}")
                return data["embedding"]
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Embedding cache get error: {str(e)}")
            return None
    
    async def set_embedding(
        self,
        text: str,
        embedding: List[float],
        model_type: str = "financial", 
        language: str = "auto",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache embedding result"""
        if not self.redis_client:
            return False
        
        try:
            key = self._generate_key(
                "embeddings",
                text,
                model_type=model_type,
                language=language
            )
            
            data = {
                "embedding": embedding,
                "model_type": model_type,
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "dimension": len(embedding)
            }
            
            await self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(data)
            )
            
            self.stats["sets"] += 1
            logger.debug(f"💾 Embedding cached: {key}")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Embedding cache set error: {str(e)}")
            return False
    
    async def get_sentiment(
        self,
        text: str,
        fusion_mode: str = "enhanced",
        language: str = "auto"
    ) -> Optional[Dict[str, Any]]:
        """Get cached sentiment result"""
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_key(
                "sentiment",
                text,
                fusion_mode=fusion_mode,
                language=language
            )
            
            cached_data = await self.redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
                self.stats["hits"] += 1
                logger.debug(f"🎯 Sentiment cache hit: {key}")
                return data["result"]
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Sentiment cache get error: {str(e)}")
            return None
    
    async def set_sentiment(
        self,
        text: str,
        result: Dict[str, Any],
        fusion_mode: str = "enhanced",
        language: str = "auto",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache sentiment result"""
        if not self.redis_client:
            return False
        
        try:
            key = self._generate_key(
                "sentiment",
                text,
                fusion_mode=fusion_mode,
                language=language
            )
            
            data = {
                "result": result,
                "fusion_mode": fusion_mode,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(data)
            )
            
            self.stats["sets"] += 1
            logger.debug(f"💾 Sentiment cached: {key}")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Sentiment cache set error: {str(e)}")
            return False
    
    async def get_similarity(
        self,
        text1: str,
        text2: str,
        language: str = "auto"
    ) -> Optional[float]:
        """Get cached similarity score"""
        if not self.redis_client:
            return None
        
        try:
            # Normalize order for consistent caching
            if text1 > text2:
                text1, text2 = text2, text1
            
            key = self._generate_key(
                "similarity",
                f"{text1}||{text2}",
                language=language
            )
            
            cached_data = await self.redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
                self.stats["hits"] += 1
                logger.debug(f"🎯 Similarity cache hit: {key}")
                return data["score"]
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Similarity cache get error: {str(e)}")
            return None
    
    async def set_similarity(
        self,
        text1: str,
        text2: str,
        score: float,
        language: str = "auto",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache similarity score"""
        if not self.redis_client:
            return False
        
        try:
            # Normalize order for consistent caching
            if text1 > text2:
                text1, text2 = text2, text1
            
            key = self._generate_key(
                "similarity",
                f"{text1}||{text2}",
                language=language
            )
            
            data = {
                "score": score,
                "text1": text1,
                "text2": text2,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(data)
            )
            
            self.stats["sets"] += 1
            logger.debug(f"💾 Similarity cached: {key}")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Similarity cache set error: {str(e)}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_key("profile", user_id)
            cached_data = await self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                self.stats["hits"] += 1
                logger.debug(f"🎯 Profile cache hit: {user_id}")
                return data["profile"]
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Profile cache get error: {str(e)}")
            return None
    
    async def set_user_profile(
        self,
        user_id: str,
        profile: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache user profile"""
        if not self.redis_client:
            return False
        
        try:
            key = self._generate_key("profile", user_id)
            
            data = {
                "profile": profile,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Longer TTL for profiles
            profile_ttl = ttl or (self.default_ttl * 7)  # 7 days
            await self.redis_client.setex(
                key,
                profile_ttl,
                json.dumps(data)
            )
            
            self.stats["sets"] += 1
            logger.debug(f"💾 Profile cached: {user_id}")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Profile cache set error: {str(e)}")
            return False
    
    async def batch_get_embeddings(
        self,
        texts: List[str],
        model_type: str = "financial",
        language: str = "auto"
    ) -> Tuple[List[Optional[List[float]]], List[str]]:
        """Batch get embeddings, returns embeddings and missing text indices"""
        if not self.redis_client:
            return [None] * len(texts), texts
        
        results = []
        missing_texts = []
        
        for text in texts:
            embedding = await self.get_embedding(text, model_type, language)
            results.append(embedding)
            if embedding is None:
                missing_texts.append(text)
        
        return results, missing_texts
    
    async def batch_set_embeddings(
        self,
        text_embedding_pairs: List[Tuple[str, List[float]]],
        model_type: str = "financial",
        language: str = "auto",
        ttl: Optional[int] = None
    ) -> int:
        """Batch set embeddings, returns count of successful sets"""
        if not self.redis_client:
            return 0
        
        success_count = 0
        for text, embedding in text_embedding_pairs:
            if await self.set_embedding(text, embedding, model_type, language, ttl):
                success_count += 1
        
        return success_count
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            full_pattern = f"{self.prefix}:{pattern}"
            keys = await self.redis_client.keys(full_pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} cache entries: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Cache invalidation error: {str(e)}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_info = {}
            if self.redis_client:
                info = await self.redis_client.info()
                redis_info = {
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "keyspace": info.get("db0", {})
                }
            
            hit_rate = 0.0
            total_requests = self.stats["hits"] + self.stats["misses"]
            if total_requests > 0:
                hit_rate = self.stats["hits"] / total_requests
            
            return {
                "stats": self.stats.copy(),
                "hit_rate": round(hit_rate, 3),
                "redis_info": redis_info,
                "connected": self.redis_client is not None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Cache stats error: {str(e)}")
            return {"error": str(e), "connected": False}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache system"""
        try:
            if not self.redis_client:
                return {
                    "status": "unhealthy",
                    "error": "Redis not connected",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Test Redis connection
            await self.redis_client.ping()
            
            # Get basic stats
            stats = await self.get_cache_stats()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🗃️ Vector Cache cleaned up")
        
        await super().cleanup()

# Global singleton instance
vector_cache = UnifiedVectorCache()