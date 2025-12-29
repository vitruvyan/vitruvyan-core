#!/usr/bin/env python3
"""
🧠 Neural Engine Cache Layer
Phase 2.2 - Smart Caching for NE Results

Intelligent caching for Neural Engine ranking results with:
- Redis-backed storage
- Context-aware cache keys (tickers + profile + top_k)
- TTL-based expiration
- Hit/miss metrics tracking
- Cache invalidation on market events

Author: Vitruvyan Development Team
Created: 2025-10-26 - Phase 2.2 Implementation
"""

import redis
import json
import hashlib
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NECacheEntry:
    """Neural Engine cached result entry"""
    result: Dict[str, Any]
    profile: str
    top_k: int
    tickers: List[str]
    timestamp: datetime
    cache_key: str
    expires_at: datetime
    hit_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NECacheEntry':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class NECacheManager:
    """
    🧠 Intelligent caching for Neural Engine results
    
    Features:
    - Context-aware cache keys
    - Market-hours aware TTL
    - Automatic invalidation
    - Performance metrics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.logger.info(f"✅ NE Cache connected to Redis: {redis_host}:{redis_port}")
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
        
        # Cache configuration
        self.prefix = "vitruvyan:ne_cache"
        self.default_ttl_hours = int(os.getenv("NE_CACHE_TTL_HOURS", "1"))  # 1 hour default
        self.market_hours_ttl_minutes = int(os.getenv("NE_CACHE_MARKET_TTL_MINUTES", "15"))  # 15 min during market hours
        
        # Metrics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "invalidations": 0
        }
        
        self.logger.info(f"🧠 NE Cache initialized (TTL: {self.default_ttl_hours}h, Market: {self.market_hours_ttl_minutes}m)")
    
    def generate_cache_key(self, profile: str, top_k: int, tickers: List[str] = None, 
                          filters: Dict[str, Any] = None) -> str:
        """
        Generate deterministic cache key from NE request parameters
        
        Key format: vitruvyan:ne_cache:{hash}
        Hash includes: profile, top_k, sorted tickers, filters
        """
        # Normalize tickers (sort for consistent hashing)
        ticker_str = ",".join(sorted(tickers)) if tickers else "all"
        
        # Normalize filters
        filter_str = json.dumps(filters, sort_keys=True) if filters else "{}"
        
        # Create composite key
        key_parts = [
            profile,
            str(top_k),
            ticker_str,
            filter_str
        ]
        
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        
        cache_key = f"{self.prefix}:{key_hash}"
        
        self.logger.debug(f"🔑 Generated cache key: {cache_key} (profile={profile}, top_k={top_k}, tickers={len(tickers or [])})")
        
        return cache_key
    
    def get_cached_result(self, cache_key: str) -> Optional[NECacheEntry]:
        """
        Retrieve cached NE result if available and valid
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
            entry = NECacheEntry.from_dict(entry_dict)
            
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
            self.logger.info(f"✅ Cache HIT: {cache_key} (age: {age_seconds:.0f}s, hits: {entry.hit_count})")
            
            return entry
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ Cache get error: {e}")
            return None
    
    def cache_result(self, cache_key: str, result: Dict[str, Any], 
                    profile: str, top_k: int, tickers: List[str] = None) -> bool:
        """
        Cache Neural Engine result with TTL
        """
        if not self.redis_client:
            return False
        
        try:
            # Determine TTL based on market hours
            ttl_seconds = self._get_adaptive_ttl()
            
            # Create cache entry
            entry = NECacheEntry(
                result=result,
                profile=profile,
                top_k=top_k,
                tickers=tickers or [],
                timestamp=datetime.now(),
                cache_key=cache_key,
                expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
                hit_count=0
            )
            
            # Store in Redis
            self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(entry.to_dict())
            )
            
            self.stats["sets"] += 1
            
            self.logger.info(f"💾 Cached NE result: {cache_key} (TTL: {ttl_seconds}s, profile: {profile}, top_k: {top_k})")
            
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ Cache set error: {e}")
            return False
    
    def _get_adaptive_ttl(self) -> int:
        """
        Adaptive TTL based on market hours
        - During market hours (9:30 AM - 4:00 PM ET): shorter TTL
        - Outside market hours: longer TTL
        """
        now = datetime.now()
        hour = now.hour
        
        # Simple heuristic: market hours 9-16 (UTC-adjusted would be better)
        is_market_hours = 14 <= hour <= 21  # Rough US market hours in UTC
        
        if is_market_hours:
            ttl_seconds = self.market_hours_ttl_minutes * 60
            self.logger.debug(f"⏰ Market hours detected: using short TTL ({self.market_hours_ttl_minutes}m)")
        else:
            ttl_seconds = self.default_ttl_hours * 3600
            self.logger.debug(f"🌙 Outside market hours: using long TTL ({self.default_ttl_hours}h)")
        
        return ttl_seconds
    
    def invalidate_cache(self, pattern: str = None) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "vitruvyan:ne_cache:*AAPL*")
                    If None, invalidates all NE cache
        
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            search_pattern = pattern or f"{self.prefix}:*"
            
            keys = self.redis_client.keys(search_pattern)
            
            if not keys:
                self.logger.debug(f"🔍 No keys found matching: {search_pattern}")
                return 0
            
            deleted = self.redis_client.delete(*keys)
            self.stats["invalidations"] += deleted
            
            self.logger.info(f"🗑️ Invalidated {deleted} cache entries (pattern: {search_pattern})")
            
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
            "redis_connected": self.redis_client is not None
        }
    
    def warm_cache(self, common_profiles: List[str] = None, top_k_values: List[int] = None):
        """
        Pre-warm cache with common query patterns
        (To be called during initialization or off-peak hours)
        """
        if not common_profiles:
            common_profiles = ["balanced_mid", "momentum_focus", "trend_follow"]
        
        if not top_k_values:
            top_k_values = [5, 10, 20]
        
        self.logger.info(f"🔥 Cache warming started: {len(common_profiles)} profiles x {len(top_k_values)} top_k values")
        
        # Note: Actual warming would require calling NE API
        # This is a placeholder for the pattern
        # In production, this could be triggered by a cron job or background task


# Global singleton instance
_ne_cache_manager = None


def get_ne_cache_manager() -> NECacheManager:
    """Get or create NE cache manager singleton"""
    global _ne_cache_manager
    if _ne_cache_manager is None:
        _ne_cache_manager = NECacheManager()
    return _ne_cache_manager
