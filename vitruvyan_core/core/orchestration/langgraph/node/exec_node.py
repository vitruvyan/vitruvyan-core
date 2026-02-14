# core/langgraph/node/exec_node.py
# 🌐 PHASE 1D: DOMAIN_NEUTRAL - Hook Pattern Implementation

from typing import Dict, Any
import logging
import os
import traceback

from core.orchestration.execution_registry import get_execution_registry

logger = logging.getLogger(__name__)


def exec_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌐 [DOMAIN-AGNOSTIC] Execution Node (Hook Pattern)
    
    Uses ExecutionRegistry to execute domain-specific logic.
    
    Behavior:
    - If EXEC_DOMAIN env var set → use registered domain handler
    - If no domain or no handler → graceful fake success stub
    
    Domain examples:
    - finance: Neural Engine entity ranking (trend, momentum, risk)
    - logistics: Route optimization scoring
    - healthcare: Patient risk assessment
    
    Original (pre-Phase 1D): Called Neural Engine for entity ranking
    Neutralized (Phase 1D): Hook pattern with registry
    Preserved: State flow and routing logic (ok/error paths)
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        Updated state (via domain handler or fake success stub)
    """
    # Get domain from environment (mirrors INTENT_DOMAIN pattern)
    domain = os.getenv("EXEC_DOMAIN")
    
    if domain:
        logger.debug(f"[exec_node] 🔌 Domain: {domain} (from EXEC_DOMAIN env var)")
    else:
        logger.debug("[exec_node] 🌐 No EXEC_DOMAIN set → fake success stub")
    
    # Get registry and execute
    registry = get_execution_registry()
    
    try:
        state = registry.execute(state, domain=domain)
    except Exception as e:
        logger.error(f"[exec_node] Execution failed: {e}", exc_info=True)
        # Fallback to fake success
        state["raw_output"] = {
            "ranking": [],
            "metadata": {"error": str(e), "stub": True}
        }
        state["route"] = "ne_valid"
        state["ok"] = False
        state["error"] = str(e)
    
    return state
