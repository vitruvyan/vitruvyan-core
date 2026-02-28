"""
Pattern Weavers v3 — Compile Node (domain-agnostic)
====================================================

Semantic compilation node for LangGraph pipeline.
Calls Pattern Weavers ``/compile`` endpoint and produces ``ontology_payload``
in the graph state.

Feature flag: ``PATTERN_WEAVERS_V3=1``
    When enabled, graph_flow.py imports this instead of pattern_weavers_node.

Backward compatible: also populates legacy fields (weaver_context,
matched_concepts, semantic_context, weave_confidence) so downstream
nodes work without changes.

ZERO business logic — pure HTTP adapter pattern.

> **Last updated**: Feb 24, 2026 18:00 UTC

Author: Vitruvyan Core Team
Version: 3.0.0
"""

import logging
from datetime import datetime
from typing import Any, Dict

import httpx
from config.api_config import get_weavers_url
from contracts.pattern_weavers import OntologyPayload

logger = logging.getLogger(__name__)

# API endpoint
COMPILE_API = f"{get_weavers_url()}/compile"
API_TIMEOUT = 10.0  # Longer than /weave (LLM latency)


def pw_compile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic compilation via Pattern Weavers /compile.

    Enrichment:
        - ontology_payload: Dict — Full OntologyPayload (v3 contract)
        - weaver_context: Dict — Backward compat (= compile response)
        - matched_concepts: List[Dict] — Entities as concept-like dicts
        - semantic_context: List[str] — Entity canonical names
        - weave_confidence: float — Gate confidence

    Args:
        state: LangGraph state with input_text

    Returns:
        Updated state with ontology payload

    Fallback:
        On failure, returns empty ontology with fallback flag
    """
    query = state.get("input_text", "").strip()
    user_id = state.get("user_id", "anonymous")

    if not query:
        logger.warning("pw_compile_node: Empty query")
        return _create_fallback(state, "empty_query")

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            response = client.post(
                COMPILE_API,
                json={
                    "query": query,
                    "user_id": user_id,
                    "language": state.get("language", "auto"),
                    "domain": "auto",
                    "context": {
                        k: state.get(k)
                        for k in ("intent", "emotion_label", "sentiment_label")
                        if state.get(k)
                    },
                },
            )

            if response.status_code == 404:
                # /compile not enabled — silent fallback to v2 behavior
                logger.info("pw_compile_node: /compile disabled (404), skipping")
                return _create_fallback(state, "compile_disabled")

            if response.status_code != 200:
                logger.error(
                    f"pw_compile_node: API error {response.status_code}"
                )
                return _create_fallback(state, f"api_error_{response.status_code}")

            result = response.json()
            payload = result.get("payload", {})

            # ── Pydantic re-validation at service→graph boundary ──
            try:
                validated = OntologyPayload.model_validate(payload)
                payload = validated.model_dump()
            except Exception as ve:
                logger.warning(
                    f"pw_compile_node: OntologyPayload validation failed: {ve}"
                )
                # Use raw dict as fallback — warn mode behavior

            # ── v3 primary field ──
            state["ontology_payload"] = payload

            # ── Backward-compatible fields ──
            state["weaver_context"] = result
            state["weave_result"] = result

            # Map entities → matched_concepts format
            entities = payload.get("entities", [])
            state["matched_concepts"] = [
                {
                    "name": e.get("canonical", e.get("raw", "")),
                    "category": e.get("entity_type", "entity"),
                    "score": e.get("confidence", 0.0),
                    "match_type": "llm",
                    "metadata": {"raw": e.get("raw", "")},
                }
                for e in entities
            ]
            state["semantic_context"] = [
                e.get("canonical", e.get("raw", "")) for e in entities
            ]

            # Gate confidence
            gate = payload.get("gate", {})
            state["weave_confidence"] = gate.get("confidence", 0.0)
            state["pattern_metadata"] = payload.get("compile_metadata", {})

            logger.info(
                f"pw_compile_node: gate={gate.get('verdict', '?')} "
                f"entities={len(entities)} "
                f"intent_hint={payload.get('intent_hint', '?')} "
                f"confidence={state['weave_confidence']:.2f} "
                f"fallback={result.get('fallback_used', False)}"
            )

            return state

    except httpx.TimeoutException:
        logger.error(f"pw_compile_node: Timeout after {API_TIMEOUT}s")
        return _create_fallback(state, "timeout")

    except httpx.RequestError as e:
        logger.error(f"pw_compile_node: Request error: {e}")
        return _create_fallback(state, "request_error")

    except Exception as e:
        logger.error(f"pw_compile_node: Unexpected error: {e}")
        return _create_fallback(state, "unexpected_error")


def _create_fallback(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Create fallback state when /compile fails."""
    logger.warning(f"pw_compile_node: Using fallback (reason: {reason})")

    fallback_payload = {
        "schema_version": "1.0.0",
        "gate": {
            "verdict": "ambiguous",
            "domain": "generic",
            "confidence": 0.0,
            "reasoning": f"Fallback: {reason}",
        },
        "entities": [],
        "intent_hint": "unknown",
        "topics": [],
        "sentiment_hint": "neutral",
        "temporal_context": "real_time",
        "language": "en",
        "complexity": "simple",
        "raw_query": state.get("input_text", ""),
        "compile_metadata": {"fallback": True, "reason": reason},
    }

    state["ontology_payload"] = fallback_payload
    state["weaver_context"] = {"payload": fallback_payload, "fallback_used": True}
    state["weave_result"] = state["weaver_context"]
    state["matched_concepts"] = []
    state["semantic_context"] = []
    state["weave_confidence"] = 0.0
    state["pattern_metadata"] = {"fallback": True, "reason": reason}

    return state
