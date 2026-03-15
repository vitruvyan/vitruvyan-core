"""
Enterprise Domain — Graph Nodes Registry
=========================================

Factory functions consumed by graph_flow.py via the GRAPH_DOMAIN hook.

Required exports:
  - get_enterprise_graph_nodes()   → Dict[str, Callable]

Optional exports:
  - get_enterprise_graph_edges()   → List[Tuple[str, str]]
  - get_enterprise_route_targets() → Dict[str, str]

The hook loader:
  domains.enterprise.graph_nodes.registry
  is imported dynamically by _load_domain_graph_extension() in graph_flow.py
  when GRAPH_DOMAIN=enterprise (or INTENT_DOMAIN=enterprise as fallback).

Phase 2A — Conservative: no custom nodes yet.
  - All enterprise intents route through default exec flow (dispatcher_exec)
  - No edges (no custom analysis pipeline)
  - No route targets (no intent→node routing override)

Phase 2B (future) will:
  - Define enterprise-specific nodes (e.g., erp_query_node, crm_analysis_node)
  - Define edges: erp_query → output_normalizer
  - Define route targets: dispatcher_exec → erp_query (override)

Vertical: Enterprise
Contract: VERTICAL_CONTRACT_V1

Created: March 2026
Status: Phase 2A — CONSERVATIVE (no custom nodes)

> **Last updated**: Mar 15, 2026
"""

import logging
from typing import Callable, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Registry of (node_name, module_path, function_name)
# Phase 2A: empty — enterprise intents use default exec flow
_NODE_SPECS: List[Tuple[str, str, str]] = []


def get_enterprise_graph_nodes() -> Dict[str, Callable]:
    """
    Return enterprise-specific LangGraph nodes.

    These are injected into the StateGraph by build_graph() in graph_flow.py.
    Node names must NOT collide with core node names (parse, intent_detection, etc.).

    Phase 2A: No custom nodes. Enterprise intents use the default
    dispatcher_exec → exec_node flow.
    """
    import importlib

    nodes: Dict[str, Callable] = {}

    for name, mod_path, fn_name in _NODE_SPECS:
        try:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            nodes[name] = fn
            logger.info("[EnterpriseRegistry] Registered node: %s", name)
        except (ImportError, AttributeError) as e:
            logger.warning("[EnterpriseRegistry] %s unavailable: %s", name, e)

    return nodes


def get_enterprise_graph_edges() -> List[Tuple[str, str]]:
    """
    Return additional edges for enterprise domain nodes.

    Phase 2A: No edges. Enterprise intents use default flow.
    """
    return []


def get_enterprise_route_targets() -> Dict[str, str]:
    """
    Return route_value → node_name mappings for the decide conditional edge.

    Phase 2A: No route targets. Enterprise intents use default
    dispatcher_exec → exec_node flow.
    """
    return {}
