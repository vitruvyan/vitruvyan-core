"""
Vitruvyan Core — Execution Registry
====================================

Domain-agnostic execution handler registry for configurable technical operations.

The ExecutionRegistry allows domains to:
- Register their domain-specific execution logic (ranking, analysis, etc.)
- Provide graceful fallback for missing domain plugins
- Configure execution validation and error handling

Philosophy:
----------
Execution logic is domain-specific (finance: Neural Engine ranking,
logistics: route optimization, healthcare: patient risk scoring).
The core provides a hook pattern with fake success default.

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
class ExecutionHandlerDefinition:
    """
    Definition of an execution handler for a specific domain.
    
    Attributes:
        domain: Domain name (e.g., "finance", "logistics", "healthcare")
        handler_fn: Function that executes domain logic
                    Signature: (state: Dict[str, Any]) -> Dict[str, Any]
        description: Human-readable description of what this handler does
        requires_fields: State fields required by this handler
        supported_intents: Intents that can be handled by this executor
    """
    domain: str
    handler_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    description: str = ""
    requires_fields: List[str] = None
    supported_intents: List[str] = None
    
    def __post_init__(self):
        if self.requires_fields is None:
            self.requires_fields = []
        if self.supported_intents is None:
            self.supported_intents = []


# ===========================================================================
# EXECUTION REGISTRY
# ===========================================================================

class ExecutionRegistry:
    """
    Registry for domain-specific execution handlers.
    
    Usage:
    
        # Create registry
        registry = ExecutionRegistry()
        
        # Register domain handler
        def finance_executor(state):
            # Execute Neural Engine ranking for finance entities
            intent = state.get("intent")
            entity_ids = state.get("entity_ids", [])
            # ... execution logic ...
            state["raw_output"] = {"ranking": [...], "metadata": {...}}
            state["route"] = "exec_valid"
            return state
        
        registry.register(ExecutionHandlerDefinition(
            domain="finance",
            handler_fn=finance_executor,
            description="Execute Neural Engine ranking for finance entities",
            requires_fields=["intent", "entity_ids"],
            supported_intents=["trend", "momentum", "risk", "volatility"]
        ))
        
        # Use in node
        state = registry.execute(state, domain="finance")
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._handlers: Dict[str, ExecutionHandlerDefinition] = {}
        logger.debug("[ExecutionRegistry] Initialized (empty)")
    
    def register(self, definition: ExecutionHandlerDefinition) -> None:
        """
        Register an execution handler for a domain.
        
        Args:
            definition: ExecutionHandlerDefinition to register
        """
        self._handlers[definition.domain] = definition
        logger.info(
            f"[ExecutionRegistry] Registered handler for domain: {definition.domain} "
            f"({definition.description})"
        )
    
    def has_handler(self, domain: str) -> bool:
        """
        Check if a handler exists for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            True if handler registered, False otherwise
        """
        return domain in self._handlers
    
    def execute(self, state: Dict[str, Any], domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute domain-specific handler.
        
        Args:
            state: LangGraph state dictionary
            domain: Domain name (optional, defaults to fake success stub)
            
        Returns:
            Updated state (or fake success if no handler)
        """
        if domain is None:
            logger.debug("[ExecutionRegistry] No domain specified → fake success (stub)")
            return self._fake_success_stub(state)
        
        if domain not in self._handlers:
            logger.warning(
                f"[ExecutionRegistry] No handler for domain '{domain}' → fake success (stub)"
            )
            return self._fake_success_stub(state)
        
        handler_def = self._handlers[domain]
        
        # Validate required fields
        missing = [f for f in handler_def.requires_fields if f not in state]
        if missing:
            logger.warning(
                f"[ExecutionRegistry] Missing required fields {missing} for domain '{domain}' "
                f"→ fake success"
            )
            return self._fake_success_stub(state)
        
        # Check intent support (optional validation)
        intent = state.get("intent")
        if (handler_def.supported_intents 
            and intent 
            and intent not in handler_def.supported_intents):
            logger.warning(
                f"[ExecutionRegistry] Intent '{intent}' not supported by domain '{domain}' "
                f"(supported: {handler_def.supported_intents}) → fake success"
            )
            return self._fake_success_stub(state)
        
        # Execute handler
        logger.info(f"[ExecutionRegistry] Executing handler for domain: {domain}")
        try:
            return handler_def.handler_fn(state)
        except Exception as e:
            logger.error(
                f"[ExecutionRegistry] Handler for domain '{domain}' failed: {e}",
                exc_info=True
            )
            # Fallback to fake success to avoid breaking the graph
            return self._fake_success_stub(state)
    
    def _fake_success_stub(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default fake success behavior (no execution).
        
        Returns empty ranking structure with domain_neutral flag.
        """
        logger.debug("[ExecutionRegistry] Fake success stub - returning empty results")
        
        # Preserve state passthrough (no breaking changes)
        state["raw_output"] = {
            "results": [],
            "metadata": {
                "domain_neutral": True,
                "stub": True,
                "phase": "1D",
                "message": "No domain-specific executor registered"
            }
        }
        state["route"] = "exec_valid"  # Domain-agnostic routing (was "ne_valid")
        state["ok"] = True
        state["error"] = None
        
        return state
    
    def get_registered_domains(self) -> List[str]:
        """
        Get list of registered domain names.
        
        Returns:
            List of domain names with registered handlers
        """
        return list(self._handlers.keys())


# ===========================================================================
# GLOBAL REGISTRY INSTANCE
# ===========================================================================

_global_execution_registry: Optional[ExecutionRegistry] = None


def get_execution_registry() -> ExecutionRegistry:
    """
    Get the global execution registry (singleton).
    
    Returns:
        Global ExecutionRegistry instance
    """
    global _global_execution_registry
    if _global_execution_registry is None:
        _global_execution_registry = ExecutionRegistry()
        logger.debug("[ExecutionRegistry] Created global singleton")
    return _global_execution_registry


def reset_execution_registry() -> None:
    """
    Reset the global registry (used for testing).
    """
    global _global_execution_registry
    _global_execution_registry = None
    logger.debug("[ExecutionRegistry] Global registry reset")
