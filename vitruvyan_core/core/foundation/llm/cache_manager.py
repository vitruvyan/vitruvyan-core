"""
Vitruvyan Core — LLM Cache Manager (Foundation Compatibility)
==============================================================

Re-exports CacheManager from core.llm for backward compatibility.

Canonical location: core.llm.cache_manager

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: COMPATIBILITY LAYER
"""

from core.llm.cache_manager import (
    CacheEntry,
    get_cache_manager,
    LLMCacheManager,
)

__all__ = ["CacheEntry", "get_cache_manager", "LLMCacheManager"]
