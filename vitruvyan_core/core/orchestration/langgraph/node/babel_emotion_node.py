# core/langgraph/node/babel_emotion_node.py
"""
Babel Gardens Emotion Detection Node for LangGraph

PHASE 2.1 - Conversational Intelligence Integration

This node integrates Babel Gardens EmotionDetectorModule into the LangGraph pipeline,
providing real-time emotion detection and cultural context adaptation for conversational UX.

Key Features:
- 7 emotion categories (frustrated, excited, anxious, satisfied, confident, curious, neutral)
- 9 cultural contexts (italian_expressive, japanese_formal, anglo_professional, etc)
- 12+ languages supported (IT, EN, ES, JA, ZH, FR, DE, RU, HI, SW, KO, PT)
- Fallback strategy: 5s timeout to neutral emotion (confidence 0.5)
- Synchronous implementation: Avoids async/sync event loop conflicts

Pipeline Position:
    parse → intent_detection → entity_resolver → babel_emotion → params_extraction → decide

State Enrichment:
    - emotion_detected (str): Primary emotion label
    - emotion_confidence (float): 0.0-1.0 confidence score
    - emotion_intensity (float): 0.0-1.0 intensity level
    - emotion_secondary (list): Additional detected emotions
    - cultural_context (str): Cultural communication style
    - emotion_reasoning (str): Explainability text
    - emotion_sentiment_label (str): Underlying sentiment (positive/negative/neutral)
    - emotion_sentiment_score (float): Sentiment confidence
    - emotion_metadata (dict): Processing metadata (latency, model, etc)

Usage:
    g.add_node("babel_emotion", babel_emotion_node)
    g.add_edge("entity_resolver", "babel_emotion")
    g.add_edge("babel_emotion", "params_extraction")

Sacred Orders: DISCOURSE (Linguistic Reasoning Layer)
Author: Leonardo (COO), Vitruvyan AI
Date: Oct 29, 2025
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

# Babel Gardens API endpoint (internal Docker network)
BABEL_GARDENS_EMOTION_API = "http://vitruvyan_babel_gardens:8009/v1/emotion/detect"
EMOTION_API_TIMEOUT = 5.0  # seconds


def babel_emotion_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect user emotion via Babel Gardens API (SYNCHRONOUS)
    
    Enriches state with:
    - emotion_detected: Primary emotion (frustrated, excited, anxious, etc)
    - emotion_confidence: Confidence score (0.0-1.0)
    - emotion_intensity: Intensity level (0.0-1.0)
    - emotion_secondary: List of secondary emotions
    - cultural_context: Cultural communication style
    - emotion_reasoning: Explainability text
    
    Args:
        state: LangGraph state with input_text, language
        
    Returns:
        Updated state with emotion metadata
        
    Fallback:
        If API fails or times out, returns neutral emotion (confidence 0.5)
    
    Note: Uses synchronous httpx.Client instead of async to avoid event loop conflicts
    """
    
    start_time = datetime.now()
    
    # Extract user input text
    user_input = state.get("input_text", "").strip()
    language = state.get("language", "auto")
    
    # Validate input
    if not user_input:
        logger.warning(" babel_emotion_node: Empty input text, skipping emotion detection")
        return _create_neutral_fallback(state, "empty_input")
    
    try:
        # Call Babel Gardens emotion detection API (SYNCHRONOUS)
        with httpx.Client(timeout=EMOTION_API_TIMEOUT) as client:
            response = client.post(
                BABEL_GARDENS_EMOTION_API,
                json={
                    "text": user_input,
                    "language": language,
                    "fusion_mode": "enhanced",
                    "use_cache": True,
                    "context": {
                        "conversation_id": state.get("conversation_id"),
                        "user_id": state.get("user_id")
                    }
                }
            )
            
            # Check response status
            if response.status_code != 200:
                logger.error(
                    f" babel_emotion_node: API error {response.status_code}: {response.text}"
                )
                return _create_neutral_fallback(state, f"api_error_{response.status_code}")
            
            # Parse response
            result = response.json()
            
            if result.get("status") != "success":
                logger.error(f" babel_emotion_node: API returned non-success status: {result}")
                return _create_neutral_fallback(state, "api_non_success")
            
            # Extract emotion data
            emotion_data = result.get("emotion", {})
            sentiment_data = result.get("sentiment", {})
            cultural_context = result.get("cultural_context", "neutral")
            reasoning = result.get("reasoning", "")
            metadata = result.get("metadata", {})
            
            # Enrich state with emotion metadata
            state["emotion_detected"] = emotion_data.get("primary", "neutral")
            state["emotion_confidence"] = emotion_data.get("confidence", 0.5)
            state["emotion_intensity"] = emotion_data.get("intensity", 0.5)
            state["emotion_secondary"] = emotion_data.get("secondary", [])
            state["cultural_context"] = cultural_context
            state["emotion_reasoning"] = reasoning
            state["emotion_sentiment_label"] = sentiment_data.get("label", "neutral")
            state["emotion_sentiment_score"] = sentiment_data.get("score", 0.0)
            
            # Metadata for debugging
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            state["emotion_metadata"] = {
                "processing_time_ms": processing_time,
                "api_latency_ms": metadata.get("processing_time_ms", 0),
                "language": metadata.get("language", language),
                "models_used": metadata.get("models_used", []),
                "cached": metadata.get("cached", False),
                "fallback_used": False
            }
            
            logger.info(
                f" babel_emotion_node: Detected '{state['emotion_detected']}' "
                f"(confidence: {state['emotion_confidence']:.2f}, "
                f"cultural: {cultural_context}, "
                f"latency: {processing_time:.0f}ms)"
            )
            
            # 🎭 PHASE 2.1: Store UX metadata in protected namespace
            # Sacred Orders may overwrite root fields, so we preserve in _ux_metadata
            state["_ux_metadata"] = {
                "emotion_detected": state["emotion_detected"],
                "emotion_confidence": state["emotion_confidence"],
                "emotion_intensity": state["emotion_intensity"],
                "emotion_secondary": state["emotion_secondary"],
                "emotion_reasoning": state["emotion_reasoning"],
                "emotion_sentiment_label": state["emotion_sentiment_label"],
                "emotion_sentiment_score": state["emotion_sentiment_score"],
                "emotion_metadata": state["emotion_metadata"],
                "cultural_context": cultural_context,
            }
            
            # 🎭 DEBUG: Verify state mutation AFTER _ux_metadata creation
            print(f"🎭 [babel_emotion_node] DEBUG: emotion_detected={state.get('emotion_detected')}, confidence={state.get('emotion_confidence')}")
            print(f"🎭 [babel_emotion_node] DEBUG: _ux_metadata created: {state.get('_ux_metadata') is not None}")
            print(f"🎭 [babel_emotion_node] DEBUG: State keys before return: {list(state.keys())}")
            
            return state
    
    except httpx.TimeoutException:
        logger.error(f" babel_emotion_node: API timeout after {EMOTION_API_TIMEOUT}s")
        return _create_neutral_fallback(state, "timeout")
    
    except httpx.RequestError as e:
        logger.error(f" babel_emotion_node: Request error: {e}")
        return _create_neutral_fallback(state, "request_error")
    
    except Exception as e:
        logger.error(f" babel_emotion_node: Unexpected error: {e}")
        return _create_neutral_fallback(state, "unexpected_error")


def _create_neutral_fallback(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """
    Create neutral emotion fallback when API fails
    
    Args:
        state: Current LangGraph state
        reason: Failure reason for logging
        
    Returns:
        State with neutral emotion metadata
    """
    
    logger.warning(f" babel_emotion_node: Using neutral fallback (reason: {reason})")
    
    state["emotion_detected"] = "neutral"
    state["emotion_confidence"] = 0.5
    state["emotion_intensity"] = 0.5
    state["emotion_secondary"] = []
    state["cultural_context"] = "neutral"
    state["emotion_reasoning"] = f"Neutral fallback due to: {reason}"
    state["emotion_sentiment_label"] = "neutral"
    state["emotion_sentiment_score"] = 0.0
    state["emotion_metadata"] = {
        "processing_time_ms": 0,
        "api_latency_ms": 0,
        "language": state.get("language", "auto"),
        "models_used": [],
        "cached": False,
        "fallback_used": True,
        "fallback_reason": reason
    }
    
    return state


def get_emotion_system_prompt_fragment(
    emotion: str,
    confidence: float,
    cultural_context: str,
    intensity: float = 0.5
) -> str:
    """
    Generate system prompt fragment based on detected emotion
    
    Used by cached_llm_node and compose_node to adapt response tone
    
    Args:
        emotion: Primary emotion (frustrated, excited, anxious, etc)
        confidence: Confidence score (0.0-1.0)
        cultural_context: Cultural communication style
        intensity: Emotion intensity (0.0-1.0)
        
    Returns:
        System prompt fragment string
    """
    
    # Only adapt tone if confidence is high enough
    if confidence < 0.7:
        return ""
    
    # Emotion-specific tone adaptations
    if emotion == "frustrated":
        if intensity > 0.7:
            return "\nUser seems very confused/frustrated. Be extra patient and clear. Break down complex concepts step-by-step."
        else:
            return "\nUser seems uncertain. Provide clear explanations with examples."
    
    elif emotion == "excited":
        if intensity > 0.7:
            return "\nUser is very enthusiastic! Match their energy with positive, motivating responses."
        else:
            return "\nUser shows interest. Provide engaging, encouraging responses."
    
    elif emotion == "anxious":
        if intensity > 0.7:
            return "\nUser expresses significant worry/anxiety. Be reassuring, cautious, and balanced. Acknowledge risks."
        else:
            return "\nUser seems cautious. Provide balanced, risk-aware guidance."
    
    elif emotion == "satisfied":
        return "\nUser is satisfied and grateful. Acknowledge their understanding and offer next steps."
    
    elif emotion == "confident":
        return "\nUser is confident and decisive. Provide concise, actionable information."
    
    elif emotion == "curious":
        return "\nUser is curious and exploring. Provide informative, educational responses."
    
    elif emotion == "skeptical":
        return "\nUser is skeptical/analytical. Provide evidence-based, well-reasoned responses."
    
    elif emotion == "bored":
        return "\nUser seems disengaged. Make responses more engaging and varied."
    
    else:  # neutral or unknown
        return ""


# Removed: No longer needed (synchronous implementation above)


# Export for use in graph_flow.py
__all__ = ["babel_emotion_node", "get_emotion_system_prompt_fragment"]
