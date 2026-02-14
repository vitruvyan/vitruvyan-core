"""
Vitruvyan Core — Graph Engine & Plugin Architecture
=====================================================

This module provides the domain-agnostic orchestration engine for LangGraph.

Key Components:
1. GraphPlugin (ABC) — Contract that domains implement to register nodes/routes
2. GraphEngine — Builder that assembles plugins into a runnable graph
3. NodeContract — Base contract for node implementations

This is LEVEL 1 (Pure Python, no I/O, no infrastructure).

The actual LangGraph compilation happens in graph_flow.py, which imports
from here. This separation allows:
- Testing without LangGraph dependency
- Multiple graph implementations (LangGraph, custom, etc.)
- Clean domain extension via plugins

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: LEVEL 1 — FOUNDATIONAL
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Tuple, Optional, Type
from dataclasses import dataclass, field

from core.orchestration.base_state import BaseGraphState


# =============================================================================
# NODE CONTRACT — Base interface for all graph nodes
# =============================================================================

@dataclass
class NodeContract:
    """
    Metadata contract for a graph node.
    
    This decouples node registration from implementation,
    allowing domain plugins to describe nodes without importing them.
    """
    name: str                                  # Unique node identifier
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]  # The node function
    description: str = ""                      # Human-readable description
    required_fields: List[str] = field(default_factory=list)  # State fields this node reads
    produced_fields: List[str] = field(default_factory=list)  # State fields this node writes
    is_conditional: bool = False               # True if node does conditional routing
    domain: str = "core"                       # Which domain owns this node


# =============================================================================
# GRAPH PLUGIN — ABC for domain extensions
# =============================================================================

class GraphPlugin(ABC):
    """
    Abstract base class for domain-specific graph extensions.
    
    Every domain (finance, logistics, healthcare) implements this
    to register its nodes, routes, state extensions, and intents.
    
    The GraphEngine collects all registered plugins and assembles
    them into a single compiled graph.
    
    Example:
        class ExampleGraphPlugin(GraphPlugin):
            def get_domain_name(self) -> str:
                return "example"
            
            def get_nodes(self) -> Dict[str, NodeContract]:
                return {
                    "entity_resolver": NodeContract(
                        name="entity_resolver",
                        handler=entity_resolver_node,
                        description="Resolves entity IDs to enriched entities"
                    ),
                    ...
                }
    """
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """
        Return the domain identifier.
        
        Examples: 'finance', 'logistics', 'healthcare', 'example'
        """
        pass
    
    @abstractmethod
    def get_state_extensions(self) -> Dict[str, Any]:
        """
        Return additional state fields for this domain.
        
        These are merged with BaseGraphState to create the
        domain-specific GraphState TypedDict.
        
        Example:
            return {
                "domain_entities": Optional[List[str]],
                "collection_data": Optional[Dict[str, Any]],
                "weight_map": Optional[Dict[str, float]],
            }
        """
        pass
    
    @abstractmethod
    def get_nodes(self) -> Dict[str, NodeContract]:
        """
        Return domain-specific nodes to register.
        
        Keys are node names, values are NodeContract instances.
        
        Example:
            return {
                "entity_resolver": NodeContract(...),
                "scorer": NodeContract(...),
            }
        """
        pass
    
    @abstractmethod
    def get_route_map(self) -> Dict[str, str]:
        """
        Return domain-specific routing rules.
        
        Keys are route values (from state["route"]),
        values are target node names.
        
        Example:
            return {
                "custom_action": "action_node",
                "collection_review": "collection_node",
                "scorer": "scorer",
            }
        """
        pass
    
    @abstractmethod
    def get_intents(self) -> List[str]:
        """
        Return domain-specific intents recognized by intent_detection.
        
        These are merged with core intents and used by the LLM
        for intent classification.
        
        Example:
            return ["analyze", "score", "validate", "custom_action", "collection_review"]
        """
        pass
    
    @abstractmethod
    def get_entry_pipeline(self) -> List[str]:
        """
        Return domain-specific nodes for the entry pipeline.
        
        These are inserted after core nodes (parse, intent_detection)
        but before routing (decide).
        
        Example:
            return ["entity_resolver"]  # Domain-specific entity resolution
        """
        pass
    
    @abstractmethod
    def get_post_routing_edges(self) -> List[Tuple[str, str]]:
        """
        Return additional edges after routing.
        
        Each tuple is (source_node, target_node).
        
        Example:
            return [
                ("sentiment_node", "exec"),
                ("exec", "quality_check"),
            ]
        """
        pass
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """
        Return domain-specific keywords for Sacred Orders.
        
        Used by orthodoxy_node and vault_node for domain-aware
        validation and protection.
        
        Default returns empty (core handles generic cases).
        
        Example:
            return {
                "sensitive_terms": ["protected", "classified", "restricted"],
                "action_verbs": ["execute", "override", "escalate"],
            }
        """
        return {}
    
    def get_config(self) -> Dict[str, Any]:
        """
        Return domain-specific configuration.
        
        Used for API URLs, feature flags, thresholds, etc.
        
        Default returns empty dict.
        """
        return {}


# =============================================================================
# GRAPH ENGINE — Builder that assembles plugins into a graph
# =============================================================================

class GraphEngine:
    """
    Domain-agnostic graph builder.
    
    Collects GraphPlugins and provides the assembled configuration
    for graph_flow.py to compile.
    
    Usage:
        engine = GraphEngine()
        engine.register_plugin(FinanceGraphPlugin())
        engine.register_plugin(AuditingPlugin())  # Optional add-ons
        
        # graph_flow.py uses engine to build:
        config = engine.get_build_config()
        compiled = compile_graph(config)
    
    Note: This class does NOT import LangGraph directly.
    The actual compilation is done in graph_flow.py.
    """
    
    def __init__(self):
        self._plugins: List[GraphPlugin] = []
        self._core_nodes: Dict[str, NodeContract] = {}
        self._core_routes: Dict[str, str] = {}
        self._core_intents: List[str] = []
    
    def register_plugin(self, plugin: GraphPlugin) -> "GraphEngine":
        """
        Register a domain plugin.
        
        Args:
            plugin: A GraphPlugin implementation
            
        Returns:
            self (for chaining)
        """
        self._plugins.append(plugin)
        return self
    
    def register_core_node(self, contract: NodeContract) -> "GraphEngine":
        """
        Register a core (domain-agnostic) node.
        
        Called internally to register nodes like parse, intent_detection,
        orthodoxy, vault, etc.
        """
        self._core_nodes[contract.name] = contract
        return self
    
    def register_core_route(self, route_value: str, target_node: str) -> "GraphEngine":
        """Register a core routing rule."""
        self._core_routes[route_value] = target_node
        return self
    
    def register_core_intent(self, intent: str) -> "GraphEngine":
        """Register a core intent."""
        self._core_intents.append(intent)
        return self
    
    # =========================================================================
    # BUILD CONFIGURATION — Used by graph_flow.py
    # =========================================================================
    
    def get_all_nodes(self) -> Dict[str, NodeContract]:
        """
        Return all nodes (core + plugins).
        
        Plugin nodes are prefixed with domain name if there are conflicts.
        """
        all_nodes = dict(self._core_nodes)
        
        for plugin in self._plugins:
            domain = plugin.get_domain_name()
            for name, contract in plugin.get_nodes().items():
                # Check for conflicts
                if name in all_nodes and all_nodes[name].domain != domain:
                    # Prefix with domain to avoid collision
                    prefixed_name = f"{domain}_{name}"
                    contract.name = prefixed_name
                    all_nodes[prefixed_name] = contract
                else:
                    all_nodes[name] = contract
        
        return all_nodes
    
    def get_all_routes(self) -> Dict[str, str]:
        """Return all routes (core + plugins)."""
        all_routes = dict(self._core_routes)
        
        for plugin in self._plugins:
            all_routes.update(plugin.get_route_map())
        
        return all_routes
    
    def get_all_intents(self) -> List[str]:
        """Return all intents (core + plugins), deduplicated."""
        all_intents = list(self._core_intents)
        
        for plugin in self._plugins:
            for intent in plugin.get_intents():
                if intent not in all_intents:
                    all_intents.append(intent)
        
        return all_intents
    
    def get_state_extensions(self) -> Dict[str, Any]:
        """
        Return merged state extensions from all plugins.
        
        Later plugins override earlier ones for conflicting keys.
        """
        extensions = {}
        
        for plugin in self._plugins:
            extensions.update(plugin.get_state_extensions())
        
        return extensions
    
    def get_entry_pipeline(self) -> List[str]:
        """
        Return the combined entry pipeline.
        
        Order: core nodes, then plugin nodes in registration order.
        """
        pipeline = []
        
        for plugin in self._plugins:
            for node_name in plugin.get_entry_pipeline():
                if node_name not in pipeline:
                    pipeline.append(node_name)
        
        return pipeline
    
    def get_post_routing_edges(self) -> List[Tuple[str, str]]:
        """Return all post-routing edges from plugins."""
        edges = []
        
        for plugin in self._plugins:
            edges.extend(plugin.get_post_routing_edges())
        
        return edges
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """Return merged keywords from all plugins."""
        keywords: Dict[str, List[str]] = {}
        
        for plugin in self._plugins:
            for key, values in plugin.get_keywords().items():
                if key not in keywords:
                    keywords[key] = []
                keywords[key].extend(values)
        
        return keywords
    
    def get_config(self) -> Dict[str, Any]:
        """Return merged config from all plugins."""
        config = {}
        
        for plugin in self._plugins:
            config.update(plugin.get_config())
        
        return config
    
    def get_domains(self) -> List[str]:
        """Return list of registered domain names."""
        return [p.get_domain_name() for p in self._plugins]
    
    def get_build_config(self) -> Dict[str, Any]:
        """
        Return complete build configuration for graph_flow.py.
        
        This is the single interface between GraphEngine and LangGraph.
        """
        return {
            "nodes": self.get_all_nodes(),
            "routes": self.get_all_routes(),
            "intents": self.get_all_intents(),
            "state_extensions": self.get_state_extensions(),
            "entry_pipeline": self.get_entry_pipeline(),
            "post_routing_edges": self.get_post_routing_edges(),
            "keywords": self.get_keywords(),
            "config": self.get_config(),
            "domains": self.get_domains(),
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_node_contract(
    name: str,
    handler: Callable,
    description: str = "",
    required_fields: Optional[List[str]] = None,
    produced_fields: Optional[List[str]] = None,
    domain: str = "core"
) -> NodeContract:
    """Factory function to create NodeContract with defaults."""
    return NodeContract(
        name=name,
        handler=handler,
        description=description,
        required_fields=required_fields or [],
        produced_fields=produced_fields or [],
        domain=domain
    )


# =============================================================================
# GLOBAL ENGINE INSTANCE — Optional singleton pattern
# =============================================================================

_global_engine: Optional[GraphEngine] = None


def get_engine() -> GraphEngine:
    """Get or create the global GraphEngine instance."""
    global _global_engine
    if _global_engine is None:
        _global_engine = GraphEngine()
    return _global_engine


def reset_engine() -> None:
    """Reset the global engine (useful for testing)."""
    global _global_engine
    _global_engine = None
