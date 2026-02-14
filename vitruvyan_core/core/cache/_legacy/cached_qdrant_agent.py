#!/usr/bin/env python3
"""
🔮 Cached Qdrant Agent Wrapper
Phase 2.2 - Smart Caching for Semantic Search

Transparent caching layer for QdrantAgent operations.
Drop-in replacement that adds intelligent caching without modifying QdrantAgent.

Usage:
    from core.cache.cached_qdrant_agent import CachedQdrantAgent
    
    # Use exactly like QdrantAgent, but with automatic caching
    agent = CachedQdrantAgent()
    results = agent.search(
        collection="phrases",
        query_vector=embedding,
        top_k=10
    )

Author: Vitruvyan Development Team
Created: 2025-10-26 - Phase 2.2 Implementation
"""

import logging
from typing import List, Optional, Dict, Any
from qdrant_client.http.models import Filter

from core.agents.qdrant_agent import QdrantAgent
from .mnemosyne_cache import get_mnemosyne_cache_manager

logger = logging.getLogger(__name__)


class CachedQdrantAgent(QdrantAgent):
    """
    🔮 Cached wrapper for QdrantAgent
    
    Extends QdrantAgent with transparent caching for search operations.
    All other methods (upsert, delete, etc.) pass through unchanged.
    
    Features:
    - Automatic cache checking before search
    - Automatic result caching after search
    - Transparent fallback on cache failures
    - Cache performance metrics
    """
    
    def __init__(self):
        """Initialize with cache manager"""
        super().__init__()  # Initialize QdrantAgent
        self.cache = get_mnemosyne_cache_manager()
        self.cache_enabled = True
        logger.info("🔮 CachedQdrantAgent initialized with Mnemosyne cache layer")
    
    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        qfilter: Optional[Filter] = None,
        with_payload: bool = True,
    ) -> Dict[str, Any]:
        """
        Search with intelligent caching
        
        Cache strategy:
        1. Generate cache key from query_vector + collection + top_k
        2. Check cache for existing results
        3. If hit: return cached results
        4. If miss: call parent search() and cache results
        
        Note: Filters are NOT cached (too complex and rarely reused)
        
        Args:
            collection: Qdrant collection name
            query_vector: Query embedding vector
            top_k: Number of results to return
            qfilter: Optional Qdrant filter (not cached)
            with_payload: Include payload in results
        
        Returns:
            Dict: {"status": "ok"|"error", "results": [...], "from_cache": bool}
        """
        
        # Skip cache if filters are used (too complex to cache reliably)
        if qfilter is not None:
            logger.debug(f"🔍 Filter detected - bypassing cache for collection: {collection}")
            result = super().search(collection, query_vector, top_k, qfilter, with_payload)
            result["from_cache"] = False
            return result
        
        # Skip cache if disabled
        if not self.cache_enabled:
            result = super().search(collection, query_vector, top_k, qfilter, with_payload)
            result["from_cache"] = False
            return result
        
        # ═══════════════════════════════════════════════════════════════
        # 🔮 PHASE 2.2: SMART CACHING LAYER
        # ═══════════════════════════════════════════════════════════════
        
        # Generate cache key
        cache_key = self.cache.generate_cache_key(query_vector, collection, top_k)
        
        # Try to get cached results
        cached_entry = self.cache.get_cached_results(cache_key)
        
        if cached_entry:
            logger.info(f"✅ Cache HIT for Qdrant search (collection={collection}, top_k={top_k}, results={len(cached_entry.results)})")
            
            return {
                "status": "ok",
                "results": cached_entry.results,
                "from_cache": True,
                "cache_age_seconds": (datetime.now() - cached_entry.timestamp).total_seconds(),
                "cache_hit_count": cached_entry.hit_count
            }
        
        logger.debug(f"❌ Cache MISS - calling Qdrant API (collection={collection}, top_k={top_k})")
        
        # ═══════════════════════════════════════════════════════════════
        # 🔍 CALL QDRANT API (CACHE MISS)
        # ═══════════════════════════════════════════════════════════════
        
        # Call parent search method
        result = super().search(collection, query_vector, top_k, qfilter, with_payload)
        
        # Check if search was successful
        if result.get("status") == "ok":
            # Cache the results for future queries
            results = result.get("results", [])
            
            cache_success = self.cache.cache_results(
                cache_key=cache_key,
                results=results,
                query_vector=query_vector,
                collection=collection,
                top_k=top_k
            )
            
            if cache_success:
                logger.info(f"💾 Cached Qdrant search results (collection={collection}, top_k={top_k}, results={len(results)})")
            else:
                logger.warning(f"⚠️ Failed to cache Qdrant results (continuing anyway)")
            
            result["from_cache"] = False
        else:
            logger.error(f"❌ Qdrant search failed: {result.get('error')}")
            result["from_cache"] = False
        
        return result
    
    def invalidate_cache(self, collection: str = None):
        """
        Invalidate cache entries
        
        Args:
            collection: If provided, only invalidate this collection
                       If None, invalidate all Mnemosyne cache
        """
        if collection:
            deleted = self.cache.invalidate_collection(collection)
            logger.info(f"🗑️ Invalidated {deleted} cache entries for collection: {collection}")
        else:
            deleted = self.cache.invalidate_all()
            logger.info(f"🗑️ Invalidated ALL {deleted} Mnemosyne cache entries")
        
        return deleted
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self.cache.get_stats()
    
    def enable_cache(self):
        """Enable caching"""
        self.cache_enabled = True
        logger.info("✅ Mnemosyne cache ENABLED")
    
    def disable_cache(self):
        """Disable caching (useful for debugging or testing)"""
        self.cache_enabled = False
        logger.info("⚠️ Mnemosyne cache DISABLED")


# Import for datetime (needed for cache_age_seconds calculation)
from datetime import datetime
