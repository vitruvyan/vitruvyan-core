"""
CACHE — Smart Caching Infrastructure

Intelligent caching for:
- Semantic search results via Qdrant/Mnemosyne (MnemosyneCacheManager)
- LLM responses (in core/llm)

Note: CachedQdrantAgent archived to _legacy/ (2026-02-14, no external consumers)

Author: Vitruvyan Development Team
Created: 2025-10-26
Updated: 2026-02-14 (Archived CachedQdrantAgent — dead code)
"""

from .mnemosyne_cache import (
    MnemosyneCacheManager,
    get_mnemosyne_cache_manager,
    SemanticCacheEntry,
)

__all__ = [
    # Mnemosyne Semantic Cache
    "MnemosyneCacheManager",
    "get_mnemosyne_cache_manager",
    "SemanticCacheEntry",
]
