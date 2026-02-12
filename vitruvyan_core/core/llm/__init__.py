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

Legacy (in _legacy/):
- LLMInterface: Superseded by LLMAgent (Feb 12, 2026)
- ConversationalLLM: Superseded by LLMAgent + PromptRegistry (Feb 12, 2026)
"""

# Backward compatibility — redirect to _legacy/
from ._legacy.llm_interface import LLMInterface
from ._legacy.conversational_llm import ConversationalLLM
from .cache_manager import (
    get_cache_manager,
    CacheEntry,
    LLMCacheManager,
)

# cache_api is a module, not a class
from . import cache_api

# Re-export prompts utilities for external use
from .prompts import (
    get_base_prompt,
    get_scenario_prompt,
    get_combined_prompt,
    VITRUVYAN_SYSTEM_PROMPT_V1_0,
    SCENARIO_TYPES,
    ACTIVE_PROMPT_VERSION,
)

__all__ = [
    # Core LLM Interface
    "LLMInterface",
    "ConversationalLLM",
    # Cache System
    "LLMCacheManager",
    "get_cache_manager",
    "CacheEntry",
    "cache_api",
    # Prompt Engineering (sub-module)
    "get_base_prompt",
    "get_scenario_prompt",
    "get_combined_prompt",
    "VITRUVYAN_SYSTEM_PROMPT_V1_0",
    "SCENARIO_TYPES",
    "ACTIVE_PROMPT_VERSION",
]
