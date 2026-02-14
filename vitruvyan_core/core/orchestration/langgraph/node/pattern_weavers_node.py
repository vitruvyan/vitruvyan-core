"""
Pattern Weavers Node (domain-agnostic)
======================================

Thin adapter for Pattern Weavers Sacred Order #5 (Reason/Semantic Contextualization).
Invokes Pattern Weavers API for taxonomy-based concept extraction.

ZERO business logic - pure HTTP adapter pattern.
Domain-agnostic: taxonomy loaded from service config, no hardcoded categories.

Author: Vitruvyan Core Team
Date: February 11, 2026
Version: 2.0.0 (Rewritten from scratch for domain-agnostic architecture)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

import httpx
from config.api_config import get_weavers_url

logger = logging.getLogger(__name__)

# API endpoint
PATTERN_WEAVERS_API = f"{get_weavers_url()}/weave"
API_TIMEOUT = 5.0  # seconds


def pattern_weavers_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract semantic concepts via Pattern Weavers API.
    
    Enrichment (domain-agnostic):
        - matched_concepts: List[Dict] - Taxonomy matches with scores
        - semantic_context: List[str] - Extracted concept names
        - weave_confidence: float - Average matching confidence
        - pattern_metadata: Dict - Processing metadata
    
    Args:
        state: LangGraph state with input_text
        
    Returns:
        Updated state with matched patterns
        
    Fallback:
        On failure, returns empty concepts with metadata flag
    """
    start_time = datetime.now()
    
    # Extract input text
    query = state.get("input_text", "").strip()
    user_id = state.get("user_id", "anonymous")
    
    # Validate input
    if not query:
        logger.warning("pattern_weavers_node: Empty query")
        return _create_fallback(state, "empty_query")
    
    try:
        # Call Pattern Weavers API
        with httpx.Client(timeout=API_TIMEOUT) as client:
            response = client.post(
                PATTERN_WEAVERS_API,
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": 10,  # Top-10 matches
                    "threshold": 0.4,  # Configurable in service
                },
            )
            
            # Check response
            if response.status_code == 422:
                logger.warning(f"pattern_weavers_node: Validation error (schema mismatch)")
                return _create_fallback(state, "validation_error")
            
            if response.status_code != 200:
                logger.error(f"pattern_weavers_node: API error {response.status_code}")
                return _create_fallback(state, f"api_error_{response.status_code}")
            
            # Parse response
            result = response.json()
            
            # Store weaver_context (primary field for downstream nodes)
            state["weaver_context"] = result
            
            # Store opaque result (full payload) - backward compatibility
            state["weave_result"] = result
            
            # Extract convenience fields (no calculation)
            matches = result.get("matches", [])
            state["matched_concepts"] = matches
            state["semantic_context"] = [m.get("name", "") for m in matches]
            
            # Extract pre-calculated metrics from service
            # (Contract: Services MUST return domain metrics, not calculate in node)
            metrics = result.get("metrics", {})
            state["weave_confidence"] = metrics.get("avg_confidence", 0.0)
            state["pattern_metadata"] = result.get("metadata", {})
            
            logger.info(
                f"pattern_weavers_node: Matched {len(matches)} concepts "
                f"(confidence: {state['weave_confidence']:.2f})"
            )
            
            return state
    
    except httpx.TimeoutException:
        logger.error(f"pattern_weavers_node: Timeout after {API_TIMEOUT}s")
        return _create_fallback(state, "timeout")
    
    except httpx.RequestError as e:
        logger.error(f"pattern_weavers_node: Request error: {e}")
        return _create_fallback(state, "request_error")
    
    except Exception as e:
        logger.error(f"pattern_weavers_node: Unexpected error: {e}")
        return _create_fallback(state, "unexpected_error")


def _create_fallback(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Create fallback state when API fails."""
    logger.warning(f"pattern_weavers_node: Using fallback (reason: {reason})")
    
    fallback_result = {
        "error": reason,
        "matches": [],
        "status": "fallback"
    }
    
    state["weaver_context"] = fallback_result  # Primary field
    state["weave_result"] = fallback_result    # Backward compatibility
    state["matched_concepts"] = []
    state["semantic_context"] = []
    state["weave_confidence"] = 0.0
    state["pattern_metadata"] = {"fallback_used": True, "fallback_reason": reason}
    
    return state


__all__ = ["pattern_weavers_node"]
