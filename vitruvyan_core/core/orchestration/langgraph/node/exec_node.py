# core/langgraph/node/exec_node.py
# 🌐 PHASE 1D: DOMAIN_NEUTRAL - Neural Engine removed

from typing import Dict, Any
import traceback


def exec_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌐 [DOMAIN_NEUTRAL] exec_node:
    - Original: Called Neural Engine for entity ranking
    - Neutralized: Returns empty ranking structure, logs passthrough
    - Preserved: State flow and routing logic (ok/error paths)
    
    PHASE 1D: Removed Neural Engine dependency for domain neutrality.
    """
    print("🌐 [exec_node] DOMAIN_NEUTRAL / NOT_IMPLEMENTED - Neural Engine removed")
    
    # Preserve state passthrough (no breaking changes)
    state["raw_output"] = {
        "ranking": [],
        "metadata": {"domain_neutral": True, "phase": "1D"}
    }
    state["route"] = "ne_valid"  # Maintain routing compatibility
    state["ok"] = True
    state["error"] = None
    
    return state
