"""
Finance Domain — Graph Nodes Registry
======================================

Factory functions consumed by graph_flow.py via the GRAPH_DOMAIN hook.

Required exports:
  - get_finance_graph_nodes()   → Dict[str, Callable]

Optional exports:
  - get_finance_graph_edges()   → List[Tuple[str, str]]
  - get_finance_route_targets() → Dict[str, str]

The hook loader:
  domains.finance.graph_nodes.registry
  is imported dynamically by _load_domain_graph_extension() in graph_flow.py
  when GRAPH_DOMAIN=finance (or INTENT_DOMAIN=finance as fallback).

Author: Vitruvyan Core Team
Created: February 24, 2026
Updated: February 24, 2026 — Phase 2.5 (quality_check, proactive_suggestions wiring)
Status: PRODUCTION
"""

import logging
from typing import Callable, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Registry of (node_name, module_path, function_name)
_NODE_SPECS: List[Tuple[str, str, str]] = [
    ("shadow_trading", "domains.finance.graph_nodes.shadow_trading_node", "shadow_trading_node"),
    ("screener", "domains.finance.graph_nodes.screener_node", "screener_node"),
    ("quality_check", "domains.finance.graph_nodes.quality_check_node", "quality_check_node"),
    ("vee_explain", "domains.finance.graph_nodes.vee_explain_node", "vee_explain_node"),
    ("vare_risk", "domains.finance.graph_nodes.vare_risk_node", "vare_risk_node"),
    ("vwre_attribution", "domains.finance.graph_nodes.vwre_attribution_node", "vwre_attribution_node"),
    ("comparison", "domains.finance.graph_nodes.comparison_node", "comparison_node"),
    ("sentiment", "domains.finance.graph_nodes.sentiment_node", "sentiment_node"),
    ("allocation", "domains.finance.graph_nodes.allocation_node", "allocation_node"),
    ("portfolio", "domains.finance.graph_nodes.portfolio_node", "portfolio_node"),
    ("guardian_monitor", "domains.finance.graph_nodes.guardian_monitor_node", "guardian_monitor_node"),
    ("proactive_suggestions", "domains.finance.graph_nodes.proactive_suggestions_node", "proactive_suggestions_node"),
]

# Set of successfully-loaded node names (populated by get_finance_graph_nodes).
# Used by get_finance_graph_edges() to build adaptive edges.
_loaded_nodes: set = set()


def get_finance_graph_nodes() -> Dict[str, Callable]:
    """
    Return finance-specific LangGraph nodes.

    These are injected into the StateGraph by build_graph() in graph_flow.py.
    Node names must NOT collide with core node names (parse, intent_detection, etc.).

    NOTE: graph_flow.py calls this BEFORE get_finance_graph_edges(), so
    _loaded_nodes is fully populated when edges are constructed.
    """
    import importlib
    global _loaded_nodes

    nodes: Dict[str, Callable] = {}
    _loaded_nodes = set()

    for name, mod_path, fn_name in _NODE_SPECS:
        try:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            nodes[name] = fn
            _loaded_nodes.add(name)
            logger.info(f"[FinanceRegistry] Registered node: {name}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"[FinanceRegistry] {name} unavailable: {e}")

    return nodes


def get_finance_graph_edges() -> List[Tuple[str, str]]:
    """
    Return additional edges for finance domain nodes.

    Finance analysis nodes → output_normalizer (rejoin core pipeline).
    Screener → quality_check → output_normalizer (validation gate).
    Advisor → proactive_suggestions → END (post-pipeline enrichment).

    Edges degrade gracefully: if quality_check or proactive_suggestions
    failed to load, edges fall back to direct wiring.
    """
    edges: List[Tuple[str, str]] = [
        ("shadow_trading", "output_normalizer"),
        ("comparison", "output_normalizer"),
        ("sentiment", "output_normalizer"),
        ("allocation", "output_normalizer"),
        ("portfolio", "output_normalizer"),
        ("guardian_monitor", "output_normalizer"),
    ]

    # Screener routing: through quality_check → VPAR nodes → output_normalizer
    # VPAR chain: vee_explain → vare_risk → vwre_attribution (each degrades gracefully)
    if "quality_check" in _loaded_nodes:
        edges.append(("screener", "quality_check"))

        # Build VPAR chain: quality_check → [vee → vare → vwre] → output_normalizer
        vpar_chain = [n for n in ("vee_explain", "vare_risk", "vwre_attribution")
                      if n in _loaded_nodes]

        if vpar_chain:
            # quality_check → first VPAR node
            edges.append(("quality_check", vpar_chain[0]))
            # Chain VPAR nodes together
            for i in range(len(vpar_chain) - 1):
                edges.append((vpar_chain[i], vpar_chain[i + 1]))
            # Last VPAR node → output_normalizer
            edges.append((vpar_chain[-1], "output_normalizer"))
        else:
            edges.append(("quality_check", "output_normalizer"))
    else:
        edges.append(("screener", "output_normalizer"))

    # Post-pipeline enrichment: proactive_suggestions after advisor
    # graph_flow.py detects this edge and adapts can/advisor terminal wiring
    if "proactive_suggestions" in _loaded_nodes:
        edges.extend([
            ("advisor", "proactive_suggestions"),
            ("proactive_suggestions", "END"),
        ])

    return edges


def get_finance_route_targets() -> Dict[str, str]:
    """
    Return route_value → node_name mappings for the decide conditional edge.

    These extend _decide_route_targets in graph_flow.py.
    The route_value is what route_node puts in state["route"];
    the node_name is the target graph node.

    Also used to build direct_routes for route_node.configure():
      route_key → route_key (identity mapping).
    """
    return {
        # Shadow trading
        "shadow_buy": "shadow_trading",
        "shadow_sell": "shadow_trading",
        "shadow_portfolio": "shadow_trading",
        # Screening (replaces generic exec for finance intents)
        "dispatcher_exec": "screener",
        # Enrichment / analysis
        "comparison": "comparison",
        "sentiment_enrichment": "sentiment",
        "allocate": "allocation",
        # Portfolio management
        "portfolio_review": "portfolio",
        "portfolio_monitor": "guardian_monitor",
    }
