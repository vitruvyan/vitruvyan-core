"""
Pattern Weavers LIVELLO 2 Adapters
==================================

ONLY I/O point for external systems.

Adapters:
- PersistenceAdapter: PostgresAgent + QdrantAgent
- EmbeddingAdapter: httpx calls to Babel Gardens
- BusAdapter: StreamBus orchestration with pure consumers
- LLMCompilerAdapter: LLMAgent-based semantic compilation (v3)
"""

from .bus_adapter import BusAdapter, get_bus_adapter
from .embedding import EmbeddingAdapter, get_embedding_adapter
from .llm_compiler import LLMCompilerAdapter, get_compiler_adapter
from .persistence import PersistenceAdapter, get_persistence

__all__ = [
    # Persistence
    "PersistenceAdapter",
    "get_persistence",
    # Embedding
    "EmbeddingAdapter",
    "get_embedding_adapter",
    # Bus
    "BusAdapter",
    "get_bus_adapter",
    # LLM Compiler (v3)
    "LLMCompilerAdapter",
    "get_compiler_adapter",
]
