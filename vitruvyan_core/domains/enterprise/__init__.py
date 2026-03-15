# domains/enterprise/__init__.py
"""
Enterprise Domain — Vitruvyan Frontier

Enterprise/ERP vertical providing intent detection, prompt engineering,
and governance rules for business data analysis.

Vertical: Enterprise
Contract: VERTICAL_CONTRACT_V1
Domain name: enterprise

Usage:
    # Via environment:
    INTENT_DOMAIN=enterprise

    # Via direct import:
    from domains.enterprise.intent_config import create_enterprise_registry
"""

__all__ = [
    "intent_config",
    "graph_plugin",
    "governance_rules",
]
