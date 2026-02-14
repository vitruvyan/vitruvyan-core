"""
Vitruvyan Core — Entity Resolver Registry
==========================================

Domain-agnostic entity resolution registry for configurable entity handling.

The EntityResolverRegistry allows domains to:
- Register their domain-specific entity resolution logic
- Provide graceful fallback for missing domain plugins
- Configure entity validation and enrichment

Philosophy:
----------
Entity resolution is domain-specific (finance: ticker→company,
logistics: route_id→route, healthcare: patient_id→patient).
The core provides a hook pattern with passthrough default.

Author: Vitruvyan Core Team
Created: February 14, 2026
Status: PRODUCTION
Version: 1.0
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ===========================================================================
# DATA CLASSES
# ===========================================================================

@dataclass
class EntityResolverDefinition:
    """
    Definition of an entity resolver for a specific domain.
    
    Attributes:
        domain: Domain name (e.g., "finance", "logistics", "healthcare")
        resolver_fn: Function that resolves entities from state
                     Signature: (state: Dict[str, Any]) -> Dict[str, Any]
        description: Human-readable description of what this resolver does
        requires_fields: State fields required by this resolver
    """
    domain: str
    resolver_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    description: str = ""
    requires_fields: List[str] = None
    
    def __post_init__(self):
        if self.requires_fields is None:
            self.requires_fields = []


# ===========================================================================
# ENTITY RESOLVER REGISTRY
# ===========================================================================

class EntityResolverRegistry:
    """
    Registry for domain-specific entity resolvers.
    
    Usage:
    
        # Create registry
        registry = EntityResolverRegistry()
        
        # Register domain resolver
        def finance_resolver(state):
            # Resolve ticker symbols to company entities
            entity_ids = state.get("entity_ids", [])
            # ... resolution logic ...
            return state
        
        registry.register(EntityResolverDefinition(
            domain="finance",
            resolver_fn=finance_resolver,
            description="Resolve ticker symbols to company entities",
            requires_fields=["entity_ids"]
        ))
        
        # Use in node
        state = registry.resolve(state, domain="finance")
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._resolvers: Dict[str, EntityResolverDefinition] = {}
        logger.debug("[EntityResolverRegistry] Initialized (empty)")
    
    def register(self, definition: EntityResolverDefinition) -> None:
        """
        Register an entity resolver for a domain.
        
        Args:
            definition: EntityResolverDefinition to register
        """
        self._resolvers[definition.domain] = definition
        logger.info(
            f"[EntityResolverRegistry] Registered resolver for domain: {definition.domain} "
            f"({definition.description})"
        )
    
    def has_resolver(self, domain: str) -> bool:
        """
        Check if a resolver exists for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            True if resolver registered, False otherwise
        """
        return domain in self._resolvers
    
    def resolve(self, state: Dict[str, Any], domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve entities using domain-specific resolver.
        
        Args:
            state: LangGraph state dictionary
            domain: Domain name (optional, defaults to passthrough)
            
        Returns:
            Updated state (or unchanged if no resolver)
        """
        if domain is None:
            logger.debug("[EntityResolverRegistry] No domain specified → passthrough (stub)")
            return self._passthrough_stub(state)
        
        if domain not in self._resolvers:
            logger.warning(
                f"[EntityResolverRegistry] No resolver for domain '{domain}' → passthrough (stub)"
            )
            return self._passthrough_stub(state)
        
        resolver_def = self._resolvers[domain]
        
        # Validate required fields
        missing = [f for f in resolver_def.requires_fields if f not in state]
        if missing:
            logger.warning(
                f"[EntityResolverRegistry] Missing required fields {missing} for domain '{domain}' "
                f"→ passthrough"
            )
            return self._passthrough_stub(state)
        
        # Execute resolver
        logger.info(f"[EntityResolverRegistry] Resolving entities for domain: {domain}")
        try:
            return resolver_def.resolver_fn(state)
        except Exception as e:
            logger.error(
                f"[EntityResolverRegistry] Resolver for domain '{domain}' failed: {e}",
                exc_info=True
            )
            return self._passthrough_stub(state)
    
    def _passthrough_stub(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default passthrough behavior (no resolution).
        
        Preserves existing entity_ids if any, sets flow to 'direct'.
        """
        entity_ids = state.get("entity_ids", [])
        
        if entity_ids:
            logger.debug(
                f"[EntityResolverRegistry] Passthrough - preserving {len(entity_ids)} entity IDs"
            )
        else:
            logger.debug("[EntityResolverRegistry] Passthrough - no entity IDs in state")
        
        # Set flow to direct (no conversational clarification needed in stub)
        state["flow"] = "direct"
        
        return state
    
    def get_registered_domains(self) -> List[str]:
        """
        Get list of registered domain names.
        
        Returns:
            List of domain names with registered resolvers
        """
        return list(self._resolvers.keys())


# ===========================================================================
# GLOBAL REGISTRY INSTANCE
# ===========================================================================

_global_entity_resolver_registry: Optional[EntityResolverRegistry] = None


def get_entity_resolver_registry() -> EntityResolverRegistry:
    """
    Get the global entity resolver registry (singleton).
    
    Returns:
        Global EntityResolverRegistry instance
    """
    global _global_entity_resolver_registry
    if _global_entity_resolver_registry is None:
        _global_entity_resolver_registry = EntityResolverRegistry()
        logger.debug("[EntityResolverRegistry] Created global singleton")
    return _global_entity_resolver_registry


def reset_entity_resolver_registry() -> None:
    """
    Reset the global registry (used for testing).
    """
    global _global_entity_resolver_registry
    _global_entity_resolver_registry = None
    logger.debug("[EntityResolverRegistry] Global registry reset")
