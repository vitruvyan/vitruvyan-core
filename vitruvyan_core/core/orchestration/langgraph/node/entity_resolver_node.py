"""
Entity Resolver Node — Domain-Agnostic Hook Pattern
====================================================

Hook pattern implementation using EntityResolverRegistry.

The actual entity resolution logic is domain-specific and should be
registered via EntityResolverRegistry (e.g., finance domain registers
ticker→company resolver, logistics registers route_id→route resolver).

In the domain-agnostic core, this node uses the registry to:
1. Check if a domain-specific resolver is registered
2. Execute domain resolver if available
3. Gracefully fallback to passthrough stub if no resolver

Author: Vitruvyan Core Team  
Created: February 10, 2026
Updated: February 14, 2026 (Hook pattern implementation)
Status: PRODUCTION
Version: 2.0
"""

from typing import Dict, Any
import logging
import os

from core.orchestration.entity_resolver_registry import get_entity_resolver_registry

logger = logging.getLogger(__name__)


def entity_resolver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌐 [DOMAIN-AGNOSTIC] Entity Resolver Node (Hook Pattern)
    
    Uses EntityResolverRegistry to execute domain-specific entity resolution.
    
    Behavior:
    - If ENTITY_DOMAIN env var set → use registered domain resolver
    - If no domain or no resolver → graceful passthrough stub
    
    Domain examples:
    - finance: Resolves ticker symbols to company entities
    - logistics: Resolves route IDs to route objects
    - healthcare: Resolves patient IDs to patient records
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        Updated state (via domain resolver or passthrough stub)
    """
    # Get domain from environment (mirrors INTENT_DOMAIN pattern)
    domain = os.getenv("ENTITY_DOMAIN")
    
    if domain:
        logger.debug(f"[entity_resolver] 🔌 Domain: {domain} (from ENTITY_DOMAIN env var)")
    else:
        logger.debug("[entity_resolver] 🌐 No ENTITY_DOMAIN set → passthrough stub")
    
    # Get registry and execute
    registry = get_entity_resolver_registry()
    state = registry.resolve(state, domain=domain)
    
    return state
