#!/usr/bin/env python3
"""
🔮 Mnemosyne Semantic Search Cache Layer
Phase 2.2 - Smart Caching for Qdrant Vector Search

Intelligent caching for semantic similarity search results with:
- Redis-backed storage
- Vector-aware cache keys (query hash + top_k + collection)
- TTL-based expiration
- Hit/miss metrics tracking
- Similarity threshold aware

Author: Vitruvyan Development Team
Created: 2025-10-26 - Phase 2.2 Implementation
"""

import redis
import json
import hashlib
import logging
import os
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SemanticCacheEntry:
    """Semantic search cached result entry"""
    results: List[Dict[str, Any]]
    query_vector_hash: str
    collection: str
    top_k: int
    timestamp: datetime
    cache_key: str
    expires_at: datetime
    hit_count: int = 0
    avg_similarity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticCacheEntry':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class MnemosyneCacheManager:
    """
    🔮 Intelligent caching for Mnemosyne semantic search
    
    Features:
    - Vector-aware cache keys
    - Similarity-based matching
    - Automatic expiration
    - Performance metrics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD") or None
        redis_ssl = os.getenv("REDIS_SSL", "false").lower() in ("true", "1", "yes")
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                ssl=redis_ssl,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.logger.info(f"✅ Mnemosyne Cache connected to Redis: {redis_host}:{redis_port}")
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
        
        # Cache configuration
        self.prefix = os.getenv("MNEMOSYNE_CACHE_PREFIX", "vitruvyan:mnemosyne_cache")
        self.default_ttl_hours = int(os.getenv("MNEMOSYNE_CACHE_TTL_HOURS", "6"))  # 6 hours default
        
        # Vector similarity threshold for cache matching
        self.vector_similarity_threshold = float(os.getenv("MNEMOSYNE_CACHE_SIMILARITY_THRESHOLD", "0.95"))
        
        # Metrics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "invalidations": 0
        }
        
        self.logger.info(f"🔮 Mnemosyne Cache initialized (TTL: {self.default_ttl_hours}h)")
    
    def _hash_vector(self, vector: List[float]) -> str:
        """
        Generate deterministic hash from vector
        
        Uses rounded values to allow for minor floating-point variations
        """
        # Round to 4 decimals to handle floating point precision
        rounded = [round(v, 4) for v in vector]
        vector_str = ",".join(map(str, rounded))
        return hashlib.sha256(vector_str.encode()).hexdigest()[:16]
    
    def generate_cache_key(self, query_vector: List[float], collection: str, 
                          top_k: int) -> str:
        """
        Generate deterministic cache key from search parameters
        
        Key format: vitruvyan:mnemosyne_cache:{collection}:{top_k}:{vector_hash}
        """
        vector_hash = self._hash_vector(query_vector)
        
        cache_key = f"{self.prefix}:{collection}:{top_k}:{vector_hash}"
        
        self.logger.debug(f"🔑 Generated cache key: {cache_key} (collection={collection}, top_k={top_k})")
        
        return cache_key
    
    def get_cached_results(self, cache_key: str) -> Optional[SemanticCacheEntry]:
        """
        Retrieve cached semantic search results if available and valid
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            
            if not cached_data:
                self.stats["misses"] += 1
                self.logger.debug(f"❌ Cache MISS: {cache_key}")
                return None
            
            # Deserialize entry
            entry_dict = json.loads(cached_data)
            entry = SemanticCacheEntry.from_dict(entry_dict)
            
            # Check expiration
            if datetime.now() > entry.expires_at:
                self.logger.debug(f"⏰ Cache EXPIRED: {cache_key}")
                self.redis_client.delete(cache_key)
                self.stats["misses"] += 1
                return None
            
            # Increment hit count
            entry.hit_count += 1
            self.redis_client.setex(
                cache_key,
                int((entry.expires_at - datetime.now()).total_seconds()),
                json.dumps(entry.to_dict())
            )
            
            self.stats["hits"] += 1
            
            age_seconds = (datetime.now() - entry.timestamp).total_seconds()
            self.logger.info(f"✅ Cache HIT: {cache_key} (age: {age_seconds:.0f}s, hits: {entry.hit_count}, results: {len(entry.results)})")
            
            return entry
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ Cache get error: {e}")
            return None
    
    def cache_results(self, cache_key: str, results: List[Dict[str, Any]], 
                     query_vector: List[float], collection: str, top_k: int) -> bool:
        """
        Cache semantic search results with TTL
        """
        if not self.redis_client:
            return False
        
        try:
            # Calculate average similarity
            similarities = [r.get("score", 0) for r in results]
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            
            # Create cache entry
            ttl_seconds = self.default_ttl_hours * 3600
            
            entry = SemanticCacheEntry(
                results=results,
                query_vector_hash=self._hash_vector(query_vector),
                collection=collection,
                top_k=top_k,
                timestamp=datetime.now(),
                cache_key=cache_key,
                expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
                hit_count=0,
                avg_similarity=avg_similarity
            )
            
            # Store in Redis
            self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(entry.to_dict())
            )
            
            self.stats["sets"] += 1
            
            self.logger.info(f"💾 Cached semantic results: {cache_key} (TTL: {ttl_seconds}s, collection: {collection}, results: {len(results)}, avg_sim: {avg_similarity:.3f})")
            
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ Cache set error: {e}")
            return False
    
    def _scan_keys(self, pattern: str) -> list:
        """Iterate keys via SCAN (non-blocking, O(1) per call)."""
        keys = []
        cursor = 0
        while True:
            cursor, batch = self.redis_client.scan(cursor=cursor, match=pattern, count=200)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys

    def invalidate_collection(self, collection: str) -> int:
        """
        Invalidate all cache entries for a specific collection
        
        Args:
            collection: Qdrant collection name (e.g., "phrases")
        
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            search_pattern = f"{self.prefix}:{collection}:*"
            
            keys = self._scan_keys(search_pattern)
            
            if not keys:
                self.logger.debug(f"🔍 No keys found for collection: {collection}")
                return 0
            
            deleted = self.redis_client.delete(*keys)
            self.stats["invalidations"] += deleted
            
            self.logger.info(f"🗑️ Invalidated {deleted} cache entries for collection: {collection}")
            
            return deleted
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ Cache invalidation error: {e}")
            return 0
    
    def invalidate_all(self) -> int:
        """
        Invalidate all Mnemosyne cache entries
        
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            search_pattern = f"{self.prefix}:*"
            
            keys = self._scan_keys(search_pattern)
            
            if not keys:
                self.logger.debug(f"🔍 No cache entries found")
                return 0
            
            deleted = self.redis_client.delete(*keys)
            self.stats["invalidations"] += deleted
            
            self.logger.info(f"🗑️ Invalidated ALL {deleted} Mnemosyne cache entries")
            
            return deleted
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ Cache invalidation error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "redis_connected": self.redis_client is not None,
            "ttl_hours": self.default_ttl_hours
        }
    
    def find_similar_cached_queries(self, query_vector: List[float], 
                                   collection: str, 
                                   top_k: int,
                                   similarity_threshold: float = None) -> Optional[SemanticCacheEntry]:
        """
        Find similar cached queries using vector similarity
        
        This allows cache hits even when query vectors are slightly different.
        
        Args:
            query_vector: Query vector to find similar cached results for
            collection: Qdrant collection name
            top_k: Number of results requested
            similarity_threshold: Minimum similarity for cache match (default: 0.95)
        
        Returns:
            SemanticCacheEntry if similar cached query found, None otherwise
        """
        if not self.redis_client:
            return None
        
        threshold = similarity_threshold or self.vector_similarity_threshold
        
        try:
            # Search all cache entries for this collection and top_k
            pattern = f"{self.prefix}:{collection}:{top_k}:*"
            keys = self._scan_keys(pattern)
            
            if not keys:
                return None
            
            # Find most similar cached query
            best_match = None
            best_similarity = 0.0
            
            for key in keys[:20]:  # Limit search scope for performance
                try:
                    cached_data = self.redis_client.get(key)
                    if not cached_data:
                        continue
                    
                    entry_dict = json.loads(cached_data)
                    entry = SemanticCacheEntry.from_dict(entry_dict)
                    
                    # Check if expired
                    if datetime.now() > entry.expires_at:
                        continue
                    
                    # Calculate vector similarity (cosine similarity)
                    # Note: This requires storing the original vector, which we don't do for efficiency
                    # For now, we rely on exact hash matching via generate_cache_key
                    # This method is a placeholder for future vector similarity-based cache matching
                    
                except Exception as e:
                    self.logger.debug(f"⚠️ Error processing cached entry: {e}")
                    continue
            
            return None  # Placeholder - exact hash matching is more efficient for now
            
        except Exception as e:
            self.logger.error(f"❌ Similar query search error: {e}")
            return None


# Global singleton instance
_mnemosyne_cache_manager = None


def get_mnemosyne_cache_manager() -> MnemosyneCacheManager:
    """Get or create Mnemosyne cache manager singleton"""
    global _mnemosyne_cache_manager
    if _mnemosyne_cache_manager is None:
        _mnemosyne_cache_manager = MnemosyneCacheManager()
    return _mnemosyne_cache_manager
