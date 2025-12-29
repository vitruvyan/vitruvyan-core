"""
LLM — Foundation Tier 0
Language Model Interface & Conversational Layer

Provides unified interface to multiple LLM providers (OpenAI, Anthropic, Gemini)
with built-in caching, conversation management, and prompt engineering.

Core Components:
- LLMInterface: Unified API for all LLM providers
- ConversationalLLM: Multi-turn conversation management
- LLMCacheManager: LRU caching for LLM responses
- cache_api: REST API module for cache operations
- prompts: Prompt engineering & versioning (sub-module)
"""

from .llm_interface import LLMInterface
from .conversational_llm import ConversationalLLM
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
