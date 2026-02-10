"""
Entity Resolver Node — Domain-Agnostic Stub
============================================

This is a STUB implementation for vitruvyan-core.
The actual entity resolution logic is domain-specific and should be
provided by a GraphPlugin (e.g., FinanceGraphPlugin for ticker resolution).

In the domain-agnostic core, this node simply passes through,
preserving any entity_ids already in the state.

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: STUB — Override with domain-specific implementation
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def entity_resolver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌐 [DOMAIN-AGNOSTIC] Entity Resolver Node
    
    Stub implementation that passes through without modification.
    Domain plugins override this with actual entity resolution logic.
    
    In finance domain: Resolves ticker symbols to company entities
    In logistics domain: Resolves route IDs to route objects
    In healthcare domain: Resolves patient IDs to patient records
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        State unchanged (stub behavior)
    """
    logger.debug("[entity_resolver] 🌐 STUB - passthrough (no domain-specific resolver loaded)")
    
    # Simply preserve existing entity_ids if any
    entity_ids = state.get("entity_ids", [])
    
    if entity_ids:
        logger.info(f"[entity_resolver] 📋 Preserving {len(entity_ids)} entity IDs from state")
    else:
        logger.debug("[entity_resolver] 📋 No entity IDs in state")
    
    # Set flow to direct (no conversational clarification needed in stub)
    state["flow"] = "direct"
    
    return state
