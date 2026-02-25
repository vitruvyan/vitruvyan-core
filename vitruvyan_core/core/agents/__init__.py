"""
Persistence Layer — Domain-Agnostic Database Interfaces

Core provides ONLY generic database connectivity:
- PostgresAgent: PostgreSQL connection with generic CRUD
- QdrantAgent: Vector database connection with generic operations
- AlchemistAgent: Schema migration capabilities (Alembic-based)
- LLMAgent: Centralized LLM gateway with caching/rate limiting

Each vertical implements its own:
- Schema (tables, indexes)
- Data Access Layer (get_*, search_*)
- Data Persistence Layer (save_*, insert_*)
"""

# Core Database Agents
from .postgres_agent import PostgresAgent, get_postgres
try:
    from .qdrant_agent import QdrantAgent
except Exception:  # Optional dependency (qdrant_client) may be absent in slim images
    QdrantAgent = None  # type: ignore[assignment]
try:
    from .alchemist_agent import AlchemistAgent
except Exception:  # Optional dependency (alembic) may be absent in slim service images
    AlchemistAgent = None  # type: ignore[assignment]

# LLM Gateway (optional in service-specific slim images)
try:
    from .llm_agent import LLMAgent, get_llm_agent, LLMError, LLMRateLimitError, LLMCircuitOpenError
except Exception:  # pragma: no cover - optional dependency safety
    LLMAgent = None  # type: ignore[assignment]
    get_llm_agent = None  # type: ignore[assignment]
    LLMError = None  # type: ignore[assignment]
    LLMRateLimitError = None  # type: ignore[assignment]
    LLMCircuitOpenError = None  # type: ignore[assignment]

__all__ = [
    # Core Agents (domain-agnostic)
    "PostgresAgent",
    "get_postgres",
    "QdrantAgent", 
    "AlchemistAgent",
    
    # LLM Gateway
    "LLMAgent",
    "get_llm_agent",
    "LLMError",
    "LLMRateLimitError",
    "LLMCircuitOpenError",
]
