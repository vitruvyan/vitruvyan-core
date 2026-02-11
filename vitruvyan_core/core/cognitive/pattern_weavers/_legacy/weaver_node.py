"""
Pattern Weaver Node — LangGraph Integration

Epistemic Order: REASON (Semantic Layer)
Position: Between intent_detection and entity_resolver

Enriches user queries with semantic context (concepts, sectors, regions, risk).
Populates state["weaver_context"] for downstream nodes.

Author: Sacred Orders
Created: November 9, 2025
"""

from typing import Dict, Any
from core.cognitive.pattern_weavers._legacy.weaver_client import PatternWeaverClient


def weaver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pattern Weaver LangGraph node.
    
    Extracts semantic context from user query using Pattern Weaver API.
    
    Args:
        state: LangGraph state dict
        
    Returns:
        Updated state with weaver_context
    """
    # Extract query and user_id from state
    query_text = state.get("input_text", "").strip()
    user_id = state.get("user_id", "unknown")
    
    # Skip weaving if no query text
    if not query_text:
        return_dict = {
            "weaver_context": {
                "concepts": [],
                "patterns": [],
                "risk_profile": {},
                "status": "skipped_no_query"
            }
        }
        # 🎯 Preserve validated_entities
        if state.get("validated_entities") is not None:
            return_dict["validated_entities"] = state["validated_entities"]
        return return_dict
    
    # Call Pattern Weaver API
    try:
        with PatternWeaverClient() as client:
            result = client.weave(
                query_text=query_text,
                user_id=user_id,
                top_k=5,
                similarity_threshold=0.4  # 🟣 LOWERED from 0.6 to 0.4 (Dec 10, 2025) - Financials matches at 0.41
            )
        
        # Add status
        result["status"] = "success" if result["concepts"] else "no_matches"
        
        # 🎯 CONVERSATIONAL-FIRST: Preserve validated_entities (Nov 23, 2025)
        return_dict = {"weaver_context": result}
        if state.get("validated_entities") is not None:
            return_dict["validated_entities"] = state["validated_entities"]
        
        return return_dict
    
    except Exception as e:
        print(f"❌ Pattern Weaver node error: {e}")
        
        return_dict = {
            "weaver_context": {
                "concepts": [],
                "patterns": [],
                "risk_profile": {},
                "status": "error",
                "error": str(e)
            }
        }
        # 🎯 Preserve validated_entities
        if state.get("validated_entities") is not None:
            return_dict["validated_entities"] = state["validated_entities"]
        return return_dict


# Optional: Helper function to check if weaving succeeded
def has_weaver_context(state: Dict[str, Any]) -> bool:
    """
    Check if weaver_context is populated.
    
    Args:
        state: LangGraph state dict
        
    Returns:
        True if weaver_context has concepts
    """
    weaver = state.get("weaver_context", {})
    return len(weaver.get("concepts", [])) > 0
