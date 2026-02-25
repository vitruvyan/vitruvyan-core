"""
Comprehension Node — Unified HTTP Adapter to Babel Gardens v2
=============================================================

Replaces BOTH pattern_weavers_node AND emotion_detector_node in a single
graph node by calling Babel Gardens /v2/comprehend.

Feature flag: BABEL_COMPREHENSION_V3
    "1" = use this node (single call)
    "0" = fall back to separate weaver + emotion nodes (default)

Category: HTTP Domain Adapter (Contract Section 3.2)
Transport: HTTP (synchronous request/response)

Sets on state:
    comprehension_result  : dict  — Full ComprehensionResult payload
    weaver_context        : dict  — Ontology section (backward compat with PW)
    matched_concepts      : list  — Entities (backward compat)
    semantic_context      : list  — Topic list (backward compat)
    weave_confidence      : float — Gate confidence (backward compat)
    emotion_detected      : str   — Primary emotion (backward compat with emotion_detector)
    emotion_confidence    : float — Emotion confidence (backward compat)
    sentiment_label       : str   — Sentiment label
    sentiment_score       : float — Sentiment score [-1, 1]

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

BABEL_GARDENS_URL = os.getenv("BABEL_GARDENS_URL", "http://babel_gardens:8009")
COMPREHEND_ENDPOINT = f"{BABEL_GARDENS_URL}/v2/comprehend"
API_TIMEOUT = 8.0  # Slightly higher than separate calls (one call does more)


def comprehension_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified comprehension — ontology + semantics in one call.

    Calls Babel Gardens /v2/comprehend, then maps the result to
    all state fields that downstream nodes expect.
    """
    logger.info("🧠 [comprehension] Calling unified comprehend endpoint")

    query = state.get("input_text", "").strip()
    user_id = state.get("user_id", "anonymous")
    language = state.get("detected_language", "auto")

    if not query:
        logger.warning("🧠 [comprehension] No input_text, using defaults")
        return _set_defaults(state, reason="empty_query")

    try:
        response = httpx.post(
            COMPREHEND_ENDPOINT,
            json={
                "query": query,
                "user_id": user_id,
                "language": language,
                "domain": "auto",
                "context": _extract_context(state),
            },
            timeout=API_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})

            # Store full comprehension result
            state["comprehension_result"] = result

            # --- Backward compat: weaver / PW fields ---
            ontology = result.get("ontology", {})
            state["weaver_context"] = ontology
            state["weave_result"] = ontology

            entities = ontology.get("entities", [])
            state["matched_concepts"] = entities
            state["semantic_context"] = ontology.get("topics", [])
            state["weave_confidence"] = ontology.get("gate", {}).get("confidence", 0.0)
            state["pattern_metadata"] = ontology.get("compile_metadata", {})

            # Inject recognized entities into state for entity_resolver compat
            state["pw_entities"] = [
                {"raw": e.get("raw", ""), "canonical": e.get("canonical", ""), "type": e.get("entity_type", "concept")}
                for e in entities
            ]

            # --- Backward compat: emotion fields ---
            semantics = result.get("semantics", {})
            emotion = semantics.get("emotion", {})
            state["emotion_detected"] = emotion.get("primary", "neutral")
            state["emotion_confidence"] = emotion.get("confidence", 0.5)
            state["babel_emotion_result"] = emotion
            state["emotion_metadata"] = {
                "secondary": emotion.get("secondary", []),
                "intensity": emotion.get("intensity", 0.0),
                "cultural_context": emotion.get("cultural_context", "neutral"),
            }

            # --- New: sentiment fields ---
            sentiment = semantics.get("sentiment", {})
            state["sentiment_label"] = sentiment.get("label", "neutral")
            state["sentiment_score"] = sentiment.get("score", 0.0)
            state["sentiment_magnitude"] = sentiment.get("magnitude", 0.0)
            state["sentiment_aspects"] = sentiment.get("aspects", [])

            # --- New: linguistic quality ---
            linguistic = semantics.get("linguistic", {})
            state["linguistic_register"] = linguistic.get("text_register", "neutral")
            state["irony_detected"] = linguistic.get("irony_detected", False)
            state["ambiguity_score"] = linguistic.get("ambiguity_score", 0.0)

            gate = ontology.get("gate", {})
            logger.info(
                f"🧠 [comprehension] Done: "
                f"gate={gate.get('verdict', 'unknown')} "
                f"entities={len(entities)} "
                f"sentiment={sentiment.get('label', 'neutral')} "
                f"emotion={emotion.get('primary', 'neutral')} "
                f"elapsed={data.get('processing_time_ms', 0):.0f}ms"
            )

            return state

        elif response.status_code == 404:
            logger.warning("🧠 [comprehension] Endpoint not available (404)")
            return _set_defaults(state, reason="endpoint_not_found")

        else:
            logger.error(f"🧠 [comprehension] Service error ({response.status_code})")
            return _set_defaults(state, reason=f"api_error_{response.status_code}")

    except httpx.TimeoutException:
        logger.error(f"🧠 [comprehension] Timeout after {API_TIMEOUT}s")
        return _set_defaults(state, reason="timeout")

    except httpx.ConnectError:
        logger.error("🧠 [comprehension] Connection error to Babel Gardens")
        return _set_defaults(state, reason="connection_error")

    except Exception as e:
        logger.error(f"🧠 [comprehension] Unexpected error: {e}")
        return _set_defaults(state, reason=f"error: {e}")


def _set_defaults(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Set all comprehension fields to safe defaults on failure."""
    state["comprehension_result"] = {"status": "fallback", "reason": reason}
    # Weaver compat
    state["weaver_context"] = {}
    state["weave_result"] = {}
    state["matched_concepts"] = []
    state["semantic_context"] = []
    state["weave_confidence"] = 0.0
    state["pattern_metadata"] = {"fallback": True, "reason": reason}
    state["pw_entities"] = []
    # Emotion compat
    state["emotion_detected"] = "neutral"
    state["emotion_confidence"] = 0.3
    state["babel_emotion_result"] = {"status": "fallback"}
    state["emotion_metadata"] = {}
    # Sentiment
    state["sentiment_label"] = "neutral"
    state["sentiment_score"] = 0.0
    state["sentiment_magnitude"] = 0.0
    state["sentiment_aspects"] = []
    # Linguistic
    state["linguistic_register"] = "neutral"
    state["irony_detected"] = False
    state["ambiguity_score"] = 0.0
    return state


def _extract_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant context from state for the comprehension call."""
    context = {}
    # Pass conversation history hint if available
    if state.get("conversation_id"):
        context["conversation_id"] = state["conversation_id"]
    if state.get("session_id"):
        context["session_id"] = state["session_id"]
    # Pass any prior emotion/sentiment for consistency tracking
    if state.get("emotion_detected") and state["emotion_detected"] != "neutral":
        context["prior_emotion"] = state["emotion_detected"]
    return context
