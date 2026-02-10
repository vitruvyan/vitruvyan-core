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
from .qdrant_agent import QdrantAgent
from .alchemist_agent import AlchemistAgent

# LLM Gateway (Feb 10, 2026 - centralized access)
from .llm_agent import LLMAgent, get_llm_agent, LLMError, LLMRateLimitError, LLMCircuitOpenError

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
