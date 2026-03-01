"""
Intent Detection Node — Domain-Agnostic
========================================

Classifies user intent and detects language via parallel API calls:
  1. Babel Gardens → language detection (84 languages)
  2. LLM (GPT) → intent classification + screening filters

The node is 100% domain-agnostic.  All domain vocabulary (intents,
filters, synonyms, prompt templates, context keywords) comes from
the IntentRegistry, which is populated by a domain plugin at boot.

Default behaviour (no plugin):  "soft" + "unknown" intents only.

Author: Vitruvyan Core Team
Rewritten: February 12, 2026 (from-zero rewrite)
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from prometheus_client import Counter

from core.agents.llm_agent import get_llm_agent
from core.orchestration.intent_registry import IntentRegistry, create_generic_registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
intent_override_counter = Counter(
    "vitruvyan_intent_override_total",
    "Professional boundaries enforced — ambiguous queries rejected",
)

# ---------------------------------------------------------------------------
# Babel Gardens configuration
# ---------------------------------------------------------------------------
BABEL_API_URL = os.getenv("SENTIMENT_API_URL", "http://babel_gardens:8009")

# ---------------------------------------------------------------------------
# Registry (loaded once at import time; domain plugin can replace it)
# ---------------------------------------------------------------------------
_registry: IntentRegistry = create_generic_registry()

# Professional-boundary helpers (populated by domain plugin)
_context_keywords: Dict[str, List[str]] = {}
_ambiguous_patterns: List[str] = []


def configure(
    registry: IntentRegistry,
    context_keywords: Optional[Dict[str, List[str]]] = None,
    ambiguous_patterns: Optional[List[str]] = None,
) -> None:
    """
    Configure the node at application boot.

    Call this once from the service entrypoint (main.py / graph_flow.py)
    BEFORE the graph starts processing.

    Args:
        registry: A domain-populated IntentRegistry
        context_keywords: Per-intent context-validation keywords
        ambiguous_patterns: Regex patterns that always trigger rejection
    """
    global _registry, _context_keywords, _ambiguous_patterns
    _registry = registry
    _context_keywords = context_keywords or {}
    _ambiguous_patterns = ambiguous_patterns or []
    logger.info(
        f"[INTENT_DETECTION] Configured: domain={registry.domain_name}, "
        f"intents={len(registry.get_intent_labels())}, "
        f"filters={len(registry.get_filter_names())}"
    )


# ===================================================================
# BABEL GARDENS — language detection
# ===================================================================

async def _call_babel_gardens(input_text: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Call Babel Gardens /v1/embeddings/multilingual for language detection.

    Uses Unicode-range analysis (84 languages).
    Falls back to {"language_detected": "unknown"} on error.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{BABEL_API_URL}/v1/embeddings/multilingual",
                json={"text": input_text[:200], "language": "auto", "use_cache": True},
            )
            if resp.status_code == 200:
                meta = resp.json().get("metadata", {})
                lang = meta.get("language", "unknown")
                # Contract-compliant: Trust service-provided confidence (no threshold logic)
                confidence = meta.get("confidence", 0.9)  # Babel Gardens pre-calculates confidence
                return {
                    "language_detected": lang,
                    "language_confidence": confidence,
                    "cultural_context": f"Text analyzed in {lang} context",
                    "babel_status": "success",
                }
            logger.warning(f"[INTENT_DETECTION] Babel HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"[INTENT_DETECTION] Babel API failed: {e}")

    return {
        "language_detected": "unknown",
        "language_confidence": 0.0,
        "cultural_context": "",
        "babel_status": "failed",
    }


# ===================================================================
# LLM — intent classification + filter extraction
# ===================================================================

async def _call_llm_intent(input_text: str, timeout: float = 10.0) -> Dict[str, Any]:
    """
    Call LLM for intent classification using the configured registry.
    """
    prompt = _registry.build_classification_prompt(input_text)

    try:
        llm = get_llm_agent()
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: llm.complete(prompt=prompt, temperature=0.0, max_tokens=200),
        )
        raw = raw.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:] if "```" in lines[0] else lines
            if lines and "```" in lines[-1]:
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        parsed = json.loads(raw)
        intent, filters = _registry.parse_classification_response(parsed)

        logger.info(f"[INTENT_DETECTION] LLM: intent={intent}, filters={filters}")
        return {"intent": intent, "query_filters": filters, "intent_status": "success"}

    except json.JSONDecodeError:
        logger.warning(f"[INTENT_DETECTION] JSON decode error from LLM")
        return {"intent": "unknown", "query_filters": {}, "intent_status": "fallback"}
    except Exception as e:
        logger.error(f"[INTENT_DETECTION] LLM error: {e}")
        return {"intent": "unknown", "query_filters": {}, "intent_status": "failed"}


# ===================================================================
# PARALLEL PROCESSING
# ===================================================================

async def _parallel_processing(input_text: str) -> Dict[str, Any]:
    """Run Babel + LLM in parallel via asyncio.gather."""
    t0 = datetime.now()

    babel, intent = await asyncio.gather(
        _call_babel_gardens(input_text),
        _call_llm_intent(input_text),
        return_exceptions=True,
    )

    if isinstance(babel, Exception):
        logger.error(f"[INTENT_DETECTION] Babel exception: {babel}")
        babel = {"language_detected": "unknown", "language_confidence": 0.0,
                 "cultural_context": "", "babel_status": "failed"}
    if isinstance(intent, Exception):
        logger.error(f"[INTENT_DETECTION] LLM exception: {intent}")
        intent = {"intent": "unknown", "query_filters": {}, "intent_status": "failed"}

    duration = (datetime.now() - t0).total_seconds() * 1000
    return {**babel, **intent, "processing_duration_ms": duration}


# ===================================================================
# PROFESSIONAL BOUNDARIES
# ===================================================================

def _has_explicit_context(user_input: str, intent: str) -> bool:
    """
    Verify the user query has explicit context for the detected intent.

    If _context_keywords was not supplied by a domain plugin this
    function always returns True (no restriction).
    """
    if not _context_keywords:
        return True  # No domain plugin → no keyword validation

    text_lower = user_input.lower()

    # Check ambiguous-pattern rejection first
    for pattern in _ambiguous_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.warning(
                f"[PROFESSIONAL_BOUNDARIES] Ambiguous pattern matched: '{user_input[:80]}...'"
            )
            return False

    keywords = _context_keywords.get(intent, [])
    if not keywords:
        return True  # No keywords → always allow

    return any(kw in text_lower for kw in keywords)


# ===================================================================
# NODE ENTRY POINT
# ===================================================================

def intent_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Domain-agnostic intent detection node.

    1. Extracts language (Babel Gardens — parallel)
    2. Classifies intent (LLM — parallel)
    3. Validates professional boundaries (domain plugin keywords)
    4. Updates state with language + intent + query_filters

    State updates:
        language_detected, language_confidence, cultural_context,
        intent, query_filters, needs_clarification,
        clarification_reason, route, intent_detection_metrics
    """
    user_input = state.get("user_message", "") or state.get("input_text", "")

    if not user_input:
        logger.warning("[INTENT_DETECTION] No input text")
        return {
            **state,
            "language_detected": "unknown",
            "intent": "unknown",
            "query_filters": {},
            "route": "intent_detection",
            "error": "No input text provided",
        }

    logger.info(f"[INTENT_DETECTION] Processing: '{user_input[:80]}...'")

    # --- parallel Babel + LLM ---
    try:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(lambda: asyncio.run(_parallel_processing(user_input)))
            result = future.result(timeout=15.0)
    except Exception as e:
        logger.error(f"[INTENT_DETECTION] Parallel processing failed: {e}")
        result = {
            "language_detected": "unknown",
            "language_confidence": 0.0,
            "cultural_context": "",
            "intent": "unknown",
            "query_filters": {},
            "babel_status": "failed",
            "intent_status": "failed",
            "processing_duration_ms": 0,
        }

    # --- professional-boundary validation ---
    detected = result["intent"]
    if detected != "unknown" and not _has_explicit_context(user_input, detected):
        logger.info(
            f"[PROFESSIONAL_BOUNDARIES] Override '{detected}' → 'unknown' "
            f"(no explicit context)"
        )
        result["intent"] = "unknown"
        state["needs_clarification"] = True
        state["clarification_reason"] = (
            f"Ambiguous query for intent '{detected}'. "
            "Please specify what you need."
        )
        intent_override_counter.inc()

    # --- update state ---
    # language_detected: always store Babel's raw detection for metadata
    # language: only update if no valid language was set pre-pipeline
    # (GRAPH_DEFAULT_LANGUAGE or client-provided language takes precedence over Babel)
    _existing_lang = state.get("language")
    _detected_lang = result["language_detected"]
    _use_detected = (
        not _existing_lang
        or not isinstance(_existing_lang, str)
        or len(_existing_lang) != 2
    )
    state.update(
        {
            "language_detected": _detected_lang,
            "language": _detected_lang if _use_detected else _existing_lang,
            "language_confidence": result.get("language_confidence", 0.0),
            "cultural_context": result.get("cultural_context", ""),
            "babel_status": result.get("babel_status", "unknown"),
            "intent": result["intent"],
            "query_filters": result.get("query_filters", {}),
            "route": "intent_detection",
            "intent_detection_metrics": {
                "processing_duration_ms": result.get("processing_duration_ms", 0),
                "babel_status": result.get("babel_status", "unknown"),
                "intent_status": result.get("intent_status", "unknown"),
                "node_timestamp": datetime.now().isoformat(),
            },
        }
    )

    logger.info(
        f"[INTENT_DETECTION] Done: lang={state['language_detected']}, "
        f"intent={state['intent']}, filters={state.get('query_filters', {})}, "
        f"duration={result.get('processing_duration_ms', 0):.1f}ms"
    )
    return state
