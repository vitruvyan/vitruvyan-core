"""
Finance Domain — Graph Nodes
=============================

Domain-specific LangGraph nodes for the finance vertical.

These nodes are injected into the core graph via the GRAPH_DOMAIN hook
in graph_flow.py. The registry module exports the factory functions:

- get_finance_graph_nodes() → Dict[str, Callable]
- get_finance_graph_edges() → List[Tuple[str, str]]
- get_finance_route_targets() → Dict[str, str]

Author: Vitruvyan Core Team
Created: February 24, 2026
Status: PRODUCTION
"""
