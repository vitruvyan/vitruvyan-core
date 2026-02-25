"""
Pattern Weavers LIVELLO 2 Adapters
==================================

ONLY I/O point for external systems.

Adapters:
- PersistenceAdapter: PostgresAgent + QdrantAgent
- EmbeddingAdapter: httpx calls to Babel Gardens
- BusAdapter: StreamBus orchestration with pure consumers
- FinanceAdapter: conditional finance vertical integration
- LLMCompilerAdapter: LLMAgent-based semantic compilation (v3)
"""

from .bus_adapter import BusAdapter, get_bus_adapter
from .embedding import EmbeddingAdapter, get_embedding_adapter
from .finance_adapter import get_finance_adapter, is_finance_enabled
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
    # Finance vertical
    "get_finance_adapter",
    "is_finance_enabled",
    # LLM Compiler (v3)
    "LLMCompilerAdapter",
    "get_compiler_adapter",
]
