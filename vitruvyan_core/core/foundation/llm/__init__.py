"""
Vitruvyan Core — LLM Layer (Foundation)
========================================

Re-exports LLM clients from core.llm for backward compatibility.

The canonical location for LLM clients is core.llm.* but some modules
import from core.foundation.llm.* for historical reasons.

Usage:
    from core.foundation.llm.conversational_llm import ConversationalLLM
    from core.foundation.llm.cache_manager import get_cache_manager, CacheEntry
    
    # Or import from canonical location:
    from core.llm.conversational_llm import ConversationalLLM
    from core.llm.cache_manager import get_cache_manager, CacheEntry

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: COMPATIBILITY LAYER
"""

from core.llm.conversational_llm import ConversationalLLM
from core.llm.cache_manager import CacheEntry, get_cache_manager, LLMCacheManager

__all__ = [
    "ConversationalLLM",
    "CacheEntry",
    "get_cache_manager",
    "LLMCacheManager",
]
