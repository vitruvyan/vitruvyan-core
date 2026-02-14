"""
Finance Domain — Entity Resolver Configuration
===============================================

Example domain-specific entity resolver for finance vertical.

This demonstrates how to register a domain-specific entity resolver
with the EntityResolverRegistry hook pattern.

Author: Vitruvyan Core Team
Created: February 14, 2026
Status: EXAMPLE (not auto-loaded)
"""

import logging
from typing import Any, Dict

from core.orchestration.entity_resolver_registry import (
    EntityResolverDefinition,
    get_entity_resolver_registry
)

logger = logging.getLogger(__name__)


def finance_entity_resolver(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finance-specific entity resolver.
    
    Resolves ticker symbols to company entities.
    
    Args:
        state: LangGraph state with entity_ids (ticker symbols)
        
    Returns:
        Updated state with flow='direct' if entities found
    """
    entity_ids = state.get("entity_ids", [])
    
    if not entity_ids:
        logger.debug("[FinanceEntityResolver] No entity_ids → passthrough")
        state["flow"] = "direct"
        return state
    
    logger.info(f"[FinanceEntityResolver] Resolving {len(entity_ids)} ticker symbols")
    
    # TODO: Implement actual ticker→company resolution logic
    # This is where you would:
    # 1. Validate ticker symbols (check against market data)
    # 2. Enrich with company metadata (name, sector, market cap)
    # 3. Filter invalid/delisted tickers
    # 4. Set conversational flow if clarification needed
    
    # Example stub:
    resolved_entities = []
    for ticker in entity_ids:
        resolved_entities.append({
            "id": ticker,
            "type": "ticker",
            "validated": True,
            "metadata": {"source": "finance_resolver"}
        })
    
    state["resolved_entities"] = resolved_entities
    state["flow"] = "direct"
    
    logger.info(f"[FinanceEntityResolver] Resolved {len(resolved_entities)} entities")
    
    return state


def register_finance_entity_resolver() -> None:
    """
    Register finance entity resolver with global registry.
    
    Call this during service startup (api_graph/main.py) if ENTITY_DOMAIN=finance.
    """
    registry = get_entity_resolver_registry()
    
    definition = EntityResolverDefinition(
        domain="finance",
        resolver_fn=finance_entity_resolver,
        description="Resolve ticker symbols to company entities",
        requires_fields=["entity_ids"]
    )
    
    registry.register(definition)
    logger.info("✅ Finance entity resolver registered")
