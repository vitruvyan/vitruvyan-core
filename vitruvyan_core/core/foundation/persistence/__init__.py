"""
Vitruvyan Core — Persistence Layer
===================================

Re-exports database agents from core.agents for backward compatibility.

The canonical location for agents is core.agents.* but many modules
import from core.foundation.persistence.* for historical reasons.

Usage:
    from core.foundation.persistence.postgres_agent import PostgresAgent
    from core.foundation.persistence.qdrant_agent import QdrantAgent
    
    # Or import from canonical location:
    from core.agents.postgres_agent import PostgresAgent
    from core.agents.qdrant_agent import QdrantAgent

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: COMPATIBILITY LAYER
"""

# Re-export from canonical location
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent

__all__ = ["PostgresAgent", "QdrantAgent"]
