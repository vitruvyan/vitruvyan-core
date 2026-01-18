"""
Persistence Layer — Domain-Agnostic Database Interfaces

Core provides ONLY generic database connectivity:
- PostgresAgent: PostgreSQL connection with generic CRUD
- QdrantAgent: Vector database connection with generic operations
- AlchemistAgent: Schema migration capabilities (Alembic-based)

Each vertical implements its own:
- Schema (tables, indexes)
- Data Access Layer (get_*, search_*)
- Data Persistence Layer (save_*, insert_*)
"""

# Core Database Agents
from .postgres_agent import PostgresAgent, get_postgres
from .qdrant_agent import QdrantAgent
from .alchemist_agent import AlchemistAgent

__all__ = [
    # Core Agents (domain-agnostic)
    "PostgresAgent",
    "get_postgres",
    "QdrantAgent", 
    "AlchemistAgent",
]
