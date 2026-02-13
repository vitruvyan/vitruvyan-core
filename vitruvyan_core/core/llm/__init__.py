"""
LLM — Prompt System & Cache Utilities
======================================

Provides prompt registry, caching, and utilities for LLM operations.
The canonical LLM gateway is LLMAgent (core/agents/llm_agent.py).

Core Components:
- LLMCacheManager: Redis-backed LRU caching for LLM responses
- cache_api: REST API module for cache operations
- prompts: Domain-agnostic prompt registry & versioning (sub-module)
- gemma_client: Gemma HTTP proxy bridge

Deprecated (removed Feb 13, 2026):
- LLMInterface → use core.agents.llm_agent.LLMAgent
- ConversationalLLM → use LLMAgent + PromptRegistry
"""

from .cache_manager import (
    get_cache_manager,
    CacheEntry,
    LLMCacheManager,
)

# cache_api is a module, not a class
from . import cache_api

# Re-export prompts utilities for external use
from .prompts import (
    PromptRegistry,
    register_generic_domain,
    ACTIVE_PROMPT_VERSION,
)

__all__ = [
    # Cache System
    "LLMCacheManager",
    "get_cache_manager",
    "CacheEntry",
    "cache_api",
    # Prompt Engineering (sub-module)
    "PromptRegistry",
    "register_generic_domain",
    "ACTIVE_PROMPT_VERSION",
]
