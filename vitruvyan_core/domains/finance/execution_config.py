"""
Finance Domain — Execution Configuration
=========================================

Execution handler registered with the core ExecutionRegistry.

NOTE (Feb 24, 2026): For the finance vertical, most exec intents are routed
to screener_node via the GRAPH_DOMAIN hook (dispatcher_exec → screener).
This handler is a fallback for any finance intents that reach the generic
exec_node path (e.g. when screener_node is unavailable or when a new exec
intent is added without a corresponding route override in the registry).

See also:
  - domains/finance/graph_nodes/screener_node.py  (primary NE screening)
  - domains/finance/graph_nodes/registry.py       (route: dispatcher_exec → screener)

Author: Vitruvyan Core Team
Created: February 14, 2026
Updated: February 24, 2026 (docstring updated — screener_node is primary)
Status: FALLBACK (not auto-loaded; screener_node handles primary exec path)
"""

import logging
from typing import Any, Dict

from core.orchestration.execution_registry import (
    ExecutionHandlerDefinition,
    get_execution_registry
)

logger = logging.getLogger(__name__)


def finance_execution_handler(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finance-specific execution handler.
    
    Executes Neural Engine ranking for finance entities.
    
    Args:
        state: LangGraph state with intent, entity_ids, etc.
        
    Returns:
        Updated state with raw_output (results)
    """
    intent = state.get("intent")
    entity_ids = state.get("entity_ids", [])
    
    logger.info(
        f"[FinanceExecutionHandler] Executing intent '{intent}' "
        f"for {len(entity_ids)} entities"
    )
    
    # TODO: Implement actual Neural Engine integration
    # This is where you would:
    # 1. Map intent to Neural Engine analysis type (trend, momentum, risk, etc.)
    # 2. Call Neural Engine API with entity_ids + parameters
    # 3. Parse neural engine response into ranking structure
    # 4. Handle errors (invalid entities, API failures, etc.)
    
    # Example stub:
    ranking = []
    for idx, entity_id in enumerate(entity_ids):
        ranking.append({
            "entity_id": entity_id,
            "score": 0.8 - (idx * 0.1),  # Fake descending scores
            "rank": idx + 1,
            "analysis": {
                "intent": intent,
                "signals": ["momentum_positive", "volume_high"],
                "confidence": 0.75
            }
        })
    
    state["raw_output"] = {
        "results": ranking,
        "ranking": ranking,  # backward-compat shim for older composers
        "metadata": {
            "domain": "finance",
            "intent": intent,
            "entity_count": len(entity_ids),
            "timestamp": "2026-02-14T18:00:00Z"  # Use actual timestamp
        }
    }
    state["route"] = "exec_valid"
    state["ok"] = True
    state["error"] = None
    
    logger.info(f"[FinanceExecutionHandler] Ranking complete: {len(ranking)} entities scored")
    
    return state


def register_finance_execution_handler() -> None:
    """
    Register finance execution handler with global registry.
    
    Call this during service startup (api_graph/main.py) if EXEC_DOMAIN=finance.
    """
    registry = get_execution_registry()
    
    definition = ExecutionHandlerDefinition(
        domain="finance",
        handler_fn=finance_execution_handler,
        description="Execute Neural Engine ranking for finance entities",
        requires_fields=["intent", "entity_ids"],
        supported_intents=[
            "trend",
            "momentum",
            "risk",
            "volatility",
            "backtest",
            "allocate",
            "collection",
            "sentiment"
        ]
    )
    
    registry.register(definition)
    logger.info("✅ Finance execution handler registered")
