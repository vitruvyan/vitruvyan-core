"""
Emotion Detector Node - HTTP Adapter to Babel Gardens (Contract v1.1 Compliant)

Category: HTTP Domain Adapter (Contract Section 3.2, Category 1)
Purpose: Extract emotion from text via Babel Gardens Perception service
Transport: HTTP (synchronous request/response)

Responsibilities (✅ Allowed):
- Call Babel Gardens emotion detection endpoint
- Extract pre-calculated emotion + confidence from response
- Store opaque payload in state
- Route based on HTTP status code

Forbidden (❌):
- Pattern matching for emotion keywords (Perception layer responsibility)
- Calculate emotion scores or confidence (domain calculation)
- Apply threshold logic (comparison operations)
- Determine emotion winner via max() calculation

Contract Compliance:
- No domain arithmetic (max, min on emotion scores)
- No threshold comparisons (literal value checks)
- Extracts pre-calculated emotion from service
- HTTP adapter pattern (thin orchestration)
"""

from typing import Dict, Any
import os
import httpx
import logging

logger = logging.getLogger(__name__)

# Babel Gardens endpoint
BABEL_GARDENS_URL = os.getenv("BABEL_GARDENS_URL", "http://babel_gardens:8009")
EMOTION_ENDPOINT = f"{BABEL_GARDENS_URL}/v1/emotion/detect"


def emotion_detector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect user emotion via Babel Gardens Perception service.
    
    Contract-compliant HTTP adapter: calls service, extracts pre-calculated
    emotion and confidence, no pattern matching or threshold logic.
    
    Args:
        state: LangGraph state with input_text
        
    Returns:
        Updated state with emotion_detected, emotion_confidence, babel_emotion_result
    """
    logger.info("🎭 [emotion_detector] Calling Babel Gardens emotion detection")
    
    user_input = state.get("input_text", "")
    
    if not user_input:
        logger.warning("🎭 [emotion_detector] No input_text, defaulting to neutral")
        state["emotion_detected"] = "neutral"
        state["emotion_confidence"] = 0.5
        return state
    
    try:
        # Call Babel Gardens emotion detection service
        response = httpx.post(
            EMOTION_ENDPOINT,
            json={"text": user_input},
            timeout=5.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract pre-calculated emotion (no calculation)
            emotion = result.get("emotion", "neutral")
            confidence = result.get("confidence", 0.5)
            
            # Store opaque service payload
            state["babel_emotion_result"] = result
            state["emotion_detected"] = emotion
            state["emotion_confidence"] = confidence
            state["emotion_metadata"] = result.get("metadata", {})
            
            logger.info(f"🎭 [emotion_detector] Detected: {emotion} (confidence: {confidence:.2f})")
            
        elif response.status_code == 404:
            # Endpoint not implemented yet - graceful fallback
            logger.warning(f"🎭 [emotion_detector] Emotion endpoint not available (404), defaulting to neutral")
            state["emotion_detected"] = "neutral"
            state["emotion_confidence"] = 0.5
            state["babel_emotion_result"] = {"status": "endpoint_not_found"}
            
        else:
            # Service error - fallback to neutral
            logger.error(f"🎭 [emotion_detector] Service error ({response.status_code}), defaulting to neutral")
            state["emotion_detected"] = "neutral"
            state["emotion_confidence"] = 0.3
            state["babel_emotion_result"] = {
                "status": "error",
                "status_code": response.status_code
            }
    
    except httpx.TimeoutException:
        logger.error("🎭 [emotion_detector] Timeout calling Babel Gardens, defaulting to neutral")
        state["emotion_detected"] = "neutral"
        state["emotion_confidence"] = 0.3
        state["babel_emotion_result"] = {"status": "timeout"}
        
    except httpx.ConnectError:
        logger.error("🎭 [emotion_detector] Connection error to Babel Gardens, defaulting to neutral")
        state["emotion_detected"] = "neutral"
        state["emotion_confidence"] = 0.3
        state["babel_emotion_result"] = {"status": "connection_error"}
        
    except Exception as e:
        logger.error(f"🎭 [emotion_detector] Unexpected error: {e}, defaulting to neutral")
        state["emotion_detected"] = "neutral"
        state["emotion_confidence"] = 0.3
        state["babel_emotion_result"] = {"status": "error", "message": str(e)}
    
    return state


# Legacy compatibility: export detect_emotion as alias
detect_emotion = emotion_detector_node
