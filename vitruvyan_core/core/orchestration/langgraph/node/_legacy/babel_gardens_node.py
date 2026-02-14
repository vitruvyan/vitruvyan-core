"""
Babel Gardens Node (domain-agnostic)
=====================================

Thin adapter for Babel Gardens Sacred Order #2 (Perception/Linguistic).
Invokes Babel Gardens API for semantic embedding generation.

ZERO business logic - pure HTTP adapter pattern.
Domain-agnostic: no hardcoded emotions, cultural contexts, or tone adaptations.

Author: Vitruvyan Core Team
Date: February 11, 2026
Version: 2.0.0 (Rewritten from scratch for domain-agnostic architecture)
"""

import logging
from datetime import datetime
from typing import Any, Dict

import httpx
from config.api_config import get_babel_url

logger = logging.getLogger(__name__)

# API endpoints
BABEL_EMBEDDINGS_API = f"{get_babel_url()}/v1/embeddings/create"
API_TIMEOUT = 5.0  # seconds


def babel_gardens_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate semantic embedding via Babel Gardens API.
    
    Enrichment (domain-agnostic):
        - semantic_embedding: List[float] - Dense vector representation
        - language_detected: str - ISO language code (e.g., 'en', 'it', 'ja')
        - embedding_dimension: int - Vector dimension
        - embedding_model: str - Model used for generation
        - babel_metadata: Dict - Processing metadata
    
    Args:
        state: LangGraph state with input_text
        
    Returns:
        Updated state with semantic embedding
        
    Fallback:
        On failure, returns empty embedding with metadata flag
    """
    start_time = datetime.now()
    
    # Extract input text
    user_input = state.get("input_text", "").strip()
    language = state.get("language", "auto")
    
    # Validate input
    if not user_input:
        logger.warning("babel_gardens_node: Empty input text")
        return _create_fallback(state, "empty_input")
    
    try:
        # Call Babel Gardens embedding API
        with httpx.Client(timeout=API_TIMEOUT) as client:
            response = client.post(
                BABEL_EMBEDDINGS_API,
                json={
                    "texts": [user_input],  # Batch API (single item)
                    "language": language,
                    "model": "multilingual",  # Service decides actual model
                    "use_cache": True,
                },
            )
            
            # Check response
            if response.status_code != 200:
                logger.error(f"babel_gardens_node: API error {response.status_code}")
                return _create_fallback(state, f"api_error_{response.status_code}")
            
            # Parse response
            result = response.json()
            
            if not result.get("embeddings"):
                logger.error("babel_gardens_node: No embeddings in response")
                return _create_fallback(state, "no_embeddings")
            
            embedding_data = result["embeddings"][0]  # First item from batch
            
            # Enrich state (domain-agnostic fields)
            state["semantic_embedding"] = embedding_data.get("embedding", [])
            state["language_detected"] = embedding_data.get("language", "unknown")
            state["embedding_dimension"] = embedding_data.get("dimension", 0)
            state["embedding_model"] = embedding_data.get("model", "unknown")
            
            # Metadata for debugging
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            state["babel_metadata"] = {
                "processing_time_ms": processing_time,
                "api_latency_ms": result.get("processing_time_ms", 0),
                "cached": result.get("cached", False),
                "fallback_used": False,
            }
            
            logger.info(
                f"babel_gardens_node: Generated embedding "
                f"({state['embedding_dimension']}D, {state['language_detected']}, "
                f"{processing_time:.0f}ms)"
            )
            
            return state
    
    except httpx.TimeoutException:
        logger.error(f"babel_gardens_node: Timeout after {API_TIMEOUT}s")
        return _create_fallback(state, "timeout")
    
    except httpx.RequestError as e:
        logger.error(f"babel_gardens_node: Request error: {e}")
        return _create_fallback(state, "request_error")
    
    except Exception as e:
        logger.error(f"babel_gardens_node: Unexpected error: {e}")
        return _create_fallback(state, "unexpected_error")


def _create_fallback(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Create fallback state when API fails."""
    logger.warning(f"babel_gardens_node: Using fallback (reason: {reason})")
    
    state["semantic_embedding"] = []
    state["language_detected"] = state.get("language", "unknown")
    state["embedding_dimension"] = 0
    state["embedding_model"] = "fallback"
    state["babel_metadata"] = {
        "processing_time_ms": 0,
        "api_latency_ms": 0,
        "cached": False,
        "fallback_used": True,
        "fallback_reason": reason,
    }
    
    return state


__all__ = ["babel_gardens_node"]
