"""
Vitruvyan Core — Route Registry
================================

Domain-agnostic route registry for LangGraph graph routing.

The RouteRegistry allows domains to:
- Register route destinations (nodes/subgraphs)
- Define intent → route mappings
- Configure routing priorities
- Provide custom routing logic

Philosophy:
----------
Routing logic is domain-specific. Core provides the registry
infrastructure, domains register their routes and mappings.

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: PRODUCTION
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ===========================================================================
# DATA CLASSES
# ===========================================================================

@dataclass
class RouteDefinition:
    """
    Definition of a route destination.
    
    Attributes:
        name: Route name (e.g., "dispatcher_exec", "llm_soft")
        description: Human-readable description
        node_name: Target node name in the graph
        is_terminal: Whether this is a terminal route (ends pipeline)
        requires_entities: Whether this route requires entity_ids
        requires_amount: Whether this route requires budget/amount
    """
    name: str
    description: str
    node_name: str = None  # Defaults to same as name
    is_terminal: bool = False
    requires_entities: bool = False
    requires_amount: bool = False
    
    def __post_init__(self):
        if self.node_name is None:
            self.node_name = self.name


@dataclass
class IntentRouteMapping:
    """
    Mapping from intent to route.
    
    Attributes:
        intent: Intent name (e.g., "trend", "soft")
        route: Target route name
        priority: Higher priority = checked first (default 0)
        condition: Optional condition function(state) -> bool
    """
    intent: str
    route: str
    priority: int = 0
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None


# ===========================================================================
# ROUTE REGISTRY
# ===========================================================================

class RouteRegistry:
    """
    Registry for domain-specific route configuration.
    
    Usage:
    
        registry = RouteRegistry(domain_name="finance")
        
        # Register routes
        registry.register_route(RouteDefinition(
            name="dispatcher_exec",
            description="Technical analysis execution",
            requires_entities=True,
        ))
        
        # Register intent mappings
        registry.register_intent_mapping(IntentRouteMapping(
            intent="trend",
            route="dispatcher_exec",
        ))
        
        # Determine route for a state
        route = registry.determine_route(state)
    """
    
    def __init__(self, domain_name: str = "generic"):
        """
        Initialize registry for a domain.
        
        Args:
            domain_name: Name of the domain (for logging/debugging)
        """
        self.domain_name = domain_name
        self._routes: Dict[str, RouteDefinition] = {}
        self._intent_mappings: List[IntentRouteMapping] = []
        self._custom_routers: List[Callable[[Dict[str, Any]], Optional[str]]] = []
        
        # Register core routes
        self._register_core_routes()
    
    def _register_core_routes(self) -> None:
        """Register core routes available in all domains."""
        core_routes = [
            RouteDefinition(
                name="semantic_fallback",
                description="Fallback for unrecognized intents",
                is_terminal=False,
            ),
            RouteDefinition(
                name="end",
                description="Pipeline termination",
                node_name="__end__",
                is_terminal=True,
            ),
        ]
        for route in core_routes:
            self.register_route(route)
        
        # Core intent mappings (lowest priority)
        self.register_intent_mapping(IntentRouteMapping(
            intent="unknown",
            route="semantic_fallback",
            priority=-100,  # Lowest priority
        ))
    
    def register_route(self, route: RouteDefinition) -> None:
        """
        Register a route definition.
        
        Args:
            route: RouteDefinition to register
        """
        self._routes[route.name] = route
        logger.debug(f"[RouteRegistry:{self.domain_name}] Registered route: {route.name}")
    
    def register_intent_mapping(self, mapping: IntentRouteMapping) -> None:
        """
        Register an intent → route mapping.
        
        Args:
            mapping: IntentRouteMapping to register
        """
        self._intent_mappings.append(mapping)
        # Keep sorted by priority (descending)
        self._intent_mappings.sort(key=lambda m: m.priority, reverse=True)
        logger.debug(f"[RouteRegistry:{self.domain_name}] Registered mapping: {mapping.intent} → {mapping.route}")
    
    def register_custom_router(
        self,
        router: Callable[[Dict[str, Any]], Optional[str]],
        priority: int = 0
    ) -> None:
        """
        Register a custom routing function.
        
        Custom routers are called before intent mappings.
        They can inspect the full state and return a route name,
        or None to continue to the next router.
        
        Args:
            router: Function(state) -> route_name or None
            priority: Higher priority = called first
        """
        self._custom_routers.append((priority, router))
        # Keep sorted by priority (descending)
        self._custom_routers.sort(key=lambda x: x[0], reverse=True)
    
    def get_route(self, name: str) -> Optional[RouteDefinition]:
        """Get route definition by name."""
        return self._routes.get(name)
    
    def get_all_routes(self) -> List[RouteDefinition]:
        """Get all registered routes."""
        return list(self._routes.values())
    
    def get_route_names(self) -> List[str]:
        """Get list of all registered route names."""
        return list(self._routes.keys())
    
    def get_technical_intents(self) -> List[str]:
        """
        Get list of intents that route to technical execution.
        
        These are intents that map to routes with requires_entities=True.
        """
        technical = set()
        for mapping in self._intent_mappings:
            route = self._routes.get(mapping.route)
            if route and route.requires_entities:
                technical.add(mapping.intent)
        return list(technical)
    
    def get_soft_intents(self) -> List[str]:
        """
        Get list of "soft" intents (emotional, non-technical).
        
        These are intents that typically route to empathetic handlers.
        """
        soft_routes = {"llm_soft", "soft_handler", "empathy"}
        soft = set()
        for mapping in self._intent_mappings:
            if mapping.route in soft_routes:
                soft.add(mapping.intent)
        return list(soft)
    
    def determine_route(self, state: Dict[str, Any]) -> str:
        """
        Determine the route for a given state.
        
        Priority:
        1. Custom routers (in priority order)
        2. proposed_exec field (if present)
        3. Intent mappings (in priority order)
        4. Fallback to semantic_fallback
        
        Args:
            state: Current graph state
            
        Returns:
            Route name
        """
        # 1. Try custom routers first
        for _, router in self._custom_routers:
            try:
                route = router(state)
                if route and route in self._routes:
                    logger.debug(f"[RouteRegistry] Custom router returned: {route}")
                    return route
            except Exception as e:
                logger.warning(f"[RouteRegistry] Custom router error: {e}")
        
        # 2. Check for explicit proposed_exec
        proposed_exec = state.get("proposed_exec")
        if proposed_exec:
            logger.debug(f"[RouteRegistry] Using proposed_exec: {proposed_exec}")
            # Find route that handles executions
            for route in self._routes.values():
                if route.requires_entities and "exec" in route.name.lower():
                    return route.name
        
        # 3. Intent-based routing
        intent = state.get("intent", "unknown")
        
        for mapping in self._intent_mappings:
            if mapping.intent == intent:
                # Check condition if present
                if mapping.condition:
                    try:
                        if not mapping.condition(state):
                            continue
                    except Exception as e:
                        logger.warning(f"[RouteRegistry] Condition check error: {e}")
                        continue
                
                # Route found
                if mapping.route in self._routes:
                    logger.debug(f"[RouteRegistry] Intent '{intent}' → {mapping.route}")
                    return mapping.route
        
        # 4. Fallback
        logger.debug(f"[RouteRegistry] No route found for intent '{intent}', using fallback")
        return "semantic_fallback"
    
    def validate_routes(self) -> List[str]:
        """
        Validate that all intent mappings point to registered routes.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        for mapping in self._intent_mappings:
            if mapping.route not in self._routes:
                errors.append(f"Intent '{mapping.intent}' maps to unknown route '{mapping.route}'")
        
        return errors


# ===========================================================================
# FACTORY FUNCTIONS
# ===========================================================================

def create_generic_registry() -> RouteRegistry:
    """
    Create a generic route registry with minimal routes.
    
    Returns:
        RouteRegistry with core routes only
    """
    return RouteRegistry(domain_name="generic")


# ===========================================================================
# EXPORTS
# ===========================================================================

__all__ = [
    "RouteRegistry",
    "RouteDefinition",
    "IntentRouteMapping",
    "create_generic_registry",
]
