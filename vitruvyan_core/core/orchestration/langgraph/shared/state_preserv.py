# core/langgraph/shared/state_preserv.py
"""
State Preservation Utilities for LangGraph Nodes

Ensures critical UX fields (emotion, language, cultural_context) survive
through the Sacred Orders pipeline without manual propagation in each node.

Sacred Orders: MEMORY (State Coherence Layer)
Author: Leonardo (COO), Vitruvyan AI
Date: Oct 30, 2025
"""

from typing import Dict, Any, Callable
from functools import wraps

# Critical fields that MUST survive through all nodes
CRITICAL_UX_FIELDS = [
    "emotion_detected",
    "emotion_confidence", 
    "emotion_intensity",
    "emotion_secondary",
    "emotion_reasoning",
    "emotion_sentiment_label",
    "emotion_sentiment_score",
    "emotion_metadata",
    "cultural_context",
    "language_detected",
    "language_confidence",
    "babel_status",
]


def preserve_ux_state(node_func: Callable) -> Callable:
    """
    Decorator that preserves critical UX fields across node execution.
    
    Usage:
        @preserve_ux_state
        def my_node(state: Dict[str, Any]) -> Dict[str, Any]:
            # Your logic here
            return new_state
    
    Guarantees:
    - If input state has emotion_detected, output will too (unless explicitly None)
    - Prevents accidental field loss during state mutations
    - Zero overhead if fields don't exist
    """
    @wraps(node_func)
    def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        # Snapshot critical fields BEFORE node execution
        ux_snapshot = {
            field: state.get(field)
            for field in CRITICAL_UX_FIELDS
            if field in state and state.get(field) is not None
        }
        
        # Execute node
        result = node_func(state)
        
        # Restore any critical fields that disappeared
        if isinstance(result, dict):
            for field, value in ux_snapshot.items():
                if field not in result or result.get(field) is None:
                    result[field] = value
        
        return result
    
    return wrapper


def inject_ux_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to inject UX metadata into response dicts.
    Call this in compose_node before returning final response.
    
    Args:
        state: LangGraph state with UX fields
        
    Returns:
        Dict with emotion/language/cultural fields extracted
    """
    return {
        "emotion_detected": state.get("emotion_detected"),
        "emotion_confidence": state.get("emotion_confidence"),
        "emotion_intensity": state.get("emotion_intensity"),
        "emotion_reasoning": state.get("emotion_reasoning"),
        "cultural_context": state.get("cultural_context"),
        "language_detected": state.get("language_detected"),
        "language_confidence": state.get("language_confidence"),
    }


def merge_ux_into_response(response: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge UX fields from state into response dict.
    Use in compose_node to ensure API response includes emotion/language.
    
    Args:
        response: Response dict being built
        state: Full LangGraph state
        
    Returns:
        Response dict with UX fields merged
    """
    ux_fields = inject_ux_metadata(state)
    
    # Only merge non-None fields
    for key, value in ux_fields.items():
        if value is not None:
            response[key] = value
    
    return response
