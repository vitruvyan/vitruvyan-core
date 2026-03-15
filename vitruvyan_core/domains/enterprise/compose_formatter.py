# vitruvyan_core/domains/enterprise/compose_formatter.py
"""
Enterprise Domain — Compose Formatter Hook

Provides domain-specific context formatting for compose_node.py.
This module is loaded dynamically by compose_node via the GRAPH_DOMAIN hook:

    domains.enterprise.compose_formatter.format_domain_context(raw_output, state)

Returns a list of context strings that compose_node appends to the LLM prompt.
This keeps enterprise-specific rendering (ERP data, KPIs, CRM metrics)
out of the core orchestration layer.

Vertical: Enterprise
Contract: VERTICAL_CONTRACT_V1
"""

from typing import Any, Dict, List, Optional


def format_domain_context(
    raw_output: Dict[str, Any],
    state: Dict[str, Any],
) -> Optional[List[str]]:
    """
    Extract enterprise-specific context from raw_output for LLM synthesis.

    Called by compose_node when GRAPH_DOMAIN=enterprise.
    Returns a list of context lines, or None if no enterprise data is present.
    """
    parts: List[str] = []

    intent = state.get("intent", "unknown")

    # Service result from dispatcher_exec (Odoo connector data)
    service_result = raw_output.get("service_result") or state.get("service_result")
    if isinstance(service_result, dict):
        # Summary statistics
        if "total" in service_result or "count" in service_result:
            count = service_result.get("total") or service_result.get("count", 0)
            parts.append(f"Total records found: {count}")

        # Revenue / financial data
        if "revenue" in service_result:
            parts.append(f"Revenue: {service_result['revenue']}")
        if "total_amount" in service_result:
            parts.append(f"Total amount: {service_result['total_amount']}")

        # CRM pipeline data
        if "pipeline_value" in service_result:
            parts.append(f"Pipeline value: {service_result['pipeline_value']}")
        if "conversion_rate" in service_result:
            parts.append(f"Conversion rate: {service_result['conversion_rate']}%")

        # If raw data list, summarize
        if "data" in service_result and isinstance(service_result["data"], list):
            data = service_result["data"]
            parts.append(f"Records returned: {len(data)}")
            if data and len(data) <= 20:
                # Include compact summary for small datasets
                parts.append(f"Data sample: {data[:5]}")

    # Semantic search results (from Qdrant)
    semantic = raw_output.get("semantic_results") or state.get("semantic_results")
    if semantic and isinstance(semantic, list):
        parts.append(f"Semantic search returned {len(semantic)} relevant documents")
        for i, doc in enumerate(semantic[:3]):
            if isinstance(doc, dict):
                text = doc.get("text", doc.get("payload", {}).get("text", ""))
                if text:
                    parts.append(f"  [{i+1}] {text[:200]}")

    # Context about the intent for narrative generation
    intent_context = {
        "partner_query": "Analyzing customer/supplier data from ERP",
        "invoice_analysis": "Analyzing invoicing and revenue data",
        "crm_pipeline": "Analyzing CRM pipeline and sales funnel",
        "sales_orders": "Analyzing sales orders",
        "purchase_orders": "Analyzing purchase orders and procurement",
        "product_catalog": "Querying product catalog",
        "employee_query": "Querying HR/employee data",
        "business_analysis": "Performing overall business analysis",
        "comparison": "Comparing entities or periods",
        "document_search": "Searching enterprise knowledge base",
    }
    if intent in intent_context:
        parts.insert(0, f"Context: {intent_context[intent]}")

    return parts if parts else None
