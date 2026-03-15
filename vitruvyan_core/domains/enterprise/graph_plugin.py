# STATUS: LEGACY — Superseded by domains/enterprise/graph_nodes/registry.py
# The graph_nodes pattern (get_enterprise_graph_nodes/edges/route_targets)
# is the canonical hook used by graph_flow.py since Feb 2026.
# Do NOT remove — kept for reference and backward compatibility.
"""
Enterprise Domain — Graph Plugin (LEGACY)
==========================================

Superseded by graph_nodes/registry.py.
See: finance and security domains for the canonical pattern.

Vertical: Enterprise
Contract: VERTICAL_CONTRACT_V1

Created: March 2026
"""

from contracts import GraphPlugin


class EnterpriseGraphPlugin(GraphPlugin):
    """Enterprise domain plugin for LangGraph integration."""

    def get_domain_name(self) -> str:
        return "enterprise"

    def get_state_extensions(self):
        return {
            "entity_type": None,      # customer|supplier|product|employee|invoice|order|lead
            "time_period": None,       # today|week|month|quarter|year|custom
            "department": None,        # sales|purchasing|accounting|hr|production|logistics
            "erp_connector": None,     # odoo|sap|oracle (connector type)
        }

    def get_nodes(self):
        return {}

    def get_route_map(self):
        return {
            "partner_query": "dispatcher_exec",
            "invoice_analysis": "dispatcher_exec",
            "crm_pipeline": "dispatcher_exec",
            "sales_orders": "dispatcher_exec",
            "purchase_orders": "dispatcher_exec",
            "product_catalog": "dispatcher_exec",
            "employee_query": "dispatcher_exec",
            "business_analysis": "dispatcher_exec",
            "comparison": "dispatcher_exec",
            "document_search": "dispatcher_exec",
            "business_advice": "llm_soft",
        }

    def get_intents(self):
        from domains.enterprise.intent_config import create_enterprise_registry
        registry = create_enterprise_registry()
        return list(registry.get_all_intents())

    def get_entry_pipeline(self):
        return []

    def get_post_routing_edges(self):
        return []


def get_enterprise_plugin() -> EnterpriseGraphPlugin:
    """Factory function for the enterprise graph plugin."""
    return EnterpriseGraphPlugin()
