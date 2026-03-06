# core/langgraph/graph_runner.py

import os
import json
import logging
import uuid
from typing import Dict, Any
from core.orchestration.langgraph.graph_flow import build_graph, build_minimal_graph
from core.orchestration.langgraph.memory_utils import merge_slots
from core.orchestration.execution_guard import get_execution_guard
from core.logging.audit import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)
# proactive_suggestions: ARCHIVED (was domain-specific finance feature)

# Domain extension keys — loaded from domain plugin at boot.
# These keys are NOT part of the core GraphState; they are collected into an
# opaque 'domain_extensions' dict so the API response stays domain-agnostic.
# Each domain declares its own keys via domains/<domain>/compose_formatter.py
def _load_domain_extension_keys() -> set:
    """Load domain extension keys from domain plugin (or empty set for generic)."""
    domain = os.getenv("GRAPH_DOMAIN", os.getenv("INTENT_DOMAIN", "generic"))
    if not domain or domain == "generic":
        return set()
    try:
        import importlib
        mod = importlib.import_module(f"domains.{domain}.compose_formatter")
        keys = getattr(mod, "DOMAIN_EXTENSION_KEYS", set())
        return set(keys)
    except (ImportError, AttributeError):
        return set()

_DOMAIN_EXTENSION_KEYS = _load_domain_extension_keys()


def _collect_domain_extensions(state: Dict[str, Any]) -> Dict[str, Any]:
    """Collect domain-specific keys from state into an opaque extensions dict."""
    if not _DOMAIN_EXTENSION_KEYS:
        return None
    ext = {}
    for k in _DOMAIN_EXTENSION_KEYS:
        v = state.get(k)
        if v is not None:
            ext[k] = v
    return ext or None


# Full UUID4 trace_id (not truncated — collision-safe at high volume)
def generate_trace_id():
    return str(uuid.uuid4())

from langdetect import detect
from langdetect import DetectorFactory

# Deterministic language detection
DetectorFactory.seed = 0

# --- Language detection (returns ISO-639-1 code directly) ---
def _detect_language(text: str) -> str:
    """
    Detect ISO-639-1 language code from text.
    Returns the raw detected code (e.g., 'fr', 'de', 'ja', 'zh-cn').
    Babel Gardens will provide more accurate detection downstream.
    Defaults to 'en' if detection fails.
    """
    try:
        code = (detect(text or "") or "en").lower()
    except Exception:
        code = "en"
    return code


# In-memory session cache with LRU eviction (thread-safe)
# Max 1000 entries, TTL 1 hour. Lazy eviction on read/write.
import threading
import time

_SESSION_LOCK = threading.Lock()
_SESSION_STATE: Dict[str, Dict[str, Any]] = {}  # user_id → {state..., _ts: float}
_SESSION_MAX = int(os.getenv("SESSION_CACHE_MAX", "1000"))
_SESSION_TTL = int(os.getenv("SESSION_CACHE_TTL", "3600"))  # seconds


def _session_get(user_id: str) -> Dict[str, Any]:
    """Thread-safe read with TTL check. Returns {} on miss/expired."""
    with _SESSION_LOCK:
        entry = _SESSION_STATE.get(user_id)
        if entry is None:
            return {}
        if time.monotonic() - entry.get("_ts", 0) > _SESSION_TTL:
            _SESSION_STATE.pop(user_id, None)
            return {}
        return {k: v for k, v in entry.items() if k != "_ts"}


def _session_put(user_id: str, state: Dict[str, Any]) -> None:
    """Thread-safe write with LRU eviction when over capacity."""
    with _SESSION_LOCK:
        # Evict oldest entries if over capacity
        while len(_SESSION_STATE) >= _SESSION_MAX and user_id not in _SESSION_STATE:
            _SESSION_STATE.pop(next(iter(_SESSION_STATE)))
        state_with_ts = dict(state)
        state_with_ts["_ts"] = time.monotonic()
        _SESSION_STATE[user_id] = state_with_ts

# Lazy graph compilation — deferred to first use instead of import-time
_ENABLE_MINIMAL = os.getenv("ENABLE_MINIMAL_GRAPH", "false").lower() == "true"
_GRAPH = None


def _get_graph():
    """Return the compiled graph, building it on first call (lazy init)."""
    global _GRAPH
    if _GRAPH is None:
        logger.info("Compiling LangGraph (minimal=%s)...", _ENABLE_MINIMAL)
        _GRAPH = build_minimal_graph() if _ENABLE_MINIMAL else build_graph()
        logger.info("LangGraph compiled successfully")
    return _GRAPH


def run_graph_once(
    input_text: str,
    user_id: str = "demo",
    return_full: bool = False,
    validated_entities: list = None,
    language: str = None,
) -> Dict[str, Any]:
    """
    Execute the graph once for a given user input.
    
    Pipeline:
    1. Load last known conversation state (RAM → Postgres).
    2. Merge with new input (slots, language, validated_entities).
    3. 🆕 Generate trace_id for VSGS audit trail.
    4. Run the LangGraph.
    5. Persist final state to RAM (cache) and Postgres/Qdrant.
    6. Return final response or full state.
    """
    # 1) Load previous state — thread-safe LRU cache first, PostgreSQL fallback (Feb 23, 2026)
    # Ensures conversation continuity survives container restarts and scale-out.
    # CAN node receives _previous_* fields and can produce contextual responses.
    state = _session_get(user_id)
    if not state:
        # RAM miss (restart, new replica, or first request) — recover from PG
        try:
            from core.agents.postgres_agent import PostgresAgent
            pg = PostgresAgent()
            last = pg.fetch_one(
                "SELECT slots, intent, language FROM conversations "
                "WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            )
            if last and last.get("slots"):
                prev = last["slots"] if isinstance(last["slots"], dict) else json.loads(last["slots"])
                state["_previous_intent"] = prev.get("intent")
                state["_previous_entities"] = prev.get("entity_ids", [])
                state["_previous_language"] = prev.get("language")
                # Carry forward the last narrative summary (truncated for token budget)
                can_resp = prev.get("can_response")
                if isinstance(can_resp, dict):
                    state["_conversation_summary"] = can_resp.get("narrative", "")[:500]
                logger.info("[graph_runner] Session recovered from PostgreSQL for user=%s (prev_intent=%s)",
                            user_id, state.get("_previous_intent"))
        except Exception as e:
            logger.warning("[graph_runner] Session recovery from PostgreSQL failed: %s", e)

    state["input_text"] = input_text
    state["user_id"] = user_id
    
    # Clear stale error/route/result from previous sessions (avoid codex_trigger false positives)
    for _clear_key in ("error", "codex_error_message", "route", "result", "ok", "raw_output"):
        state.pop(_clear_key, None)

    # Golden Rule: validated_entities are authoritative (client validation contract)
    # None → server may attempt extraction; [] → user chose "no entities"; [...] → trust list
    if validated_entities is not None:
        state["entity_ids"] = validated_entities
        state["validated_entities"] = validated_entities
    if language:
        state["language"] = language
    
    # 🆕 2) Generate trace_id for VSGS audit trail (propagated through all nodes)
    state["trace_id"] = generate_trace_id()
    logger.debug("[graph_runner] Request trace_id: %s", state['trace_id'])

    # 2) Detect and set language
    # Priority chain: client-provided > GRAPH_DEFAULT_LANGUAGE env > langdetect > prior session > "en"
    # Note: GRAPH_DEFAULT_LANGUAGE overrides prior session language (which may be stale/wrong)
    if not language:  # Client didn't explicitly provide language
        default_lang = os.getenv("GRAPH_DEFAULT_LANGUAGE")
        if default_lang:
            state["language"] = default_lang
            logger.debug("[graph_runner] Language from GRAPH_DEFAULT_LANGUAGE: %s", default_lang)
        elif not state.get("language"):
            lang = _detect_language(input_text) if input_text else "en"
            state["language"] = lang or "en"
            logger.debug("[graph_runner] Language from langdetect: %s", state["language"])

    # Merge slots (budget, entity_ids, horizon, language)
    state = merge_slots(state, state)
    logger.info("[graph_runner] Pre-pipeline language=%s", state.get("language"))

    # 3) Run the LangGraph with hard timeout protection
    _graph_timeout = int(os.getenv("GRAPH_EXEC_TIMEOUT_SECONDS", "120"))
    guard = get_execution_guard()
    result = guard.execute_node(
        node_name="langgraph_pipeline",
        handler=lambda s: _get_graph().invoke(s),
        state=state,
        timeout=_graph_timeout,
    )

    if result.timed_out:
        logger.error("[graph_runner] Pipeline timed out after %ds", _graph_timeout)
        # Emit audit event for timeout
        try:
            audit = get_audit_logger()
            audit.log(
                event_id=state.get("trace_id", "unknown"),
                correlation_id=state.get("trace_id", ""),
                node_id="langgraph_pipeline",
                status="timeout",
                execution_time_ms=result.execution_time_ms,
                error_code="PIPELINE_TIMEOUT",
            )
        except Exception:
            pass

    final_state = result.state

    # ✅ Override language with Babel Gardens detection (more accurate than langdetect)
    _resolved_lang = None
    if final_state.get("emotion_metadata") and final_state["emotion_metadata"].get("language"):
        babel_lang = final_state["emotion_metadata"]["language"].lower()
        # Use Babel Gardens language directly — supports 100+ languages (ISO-639-1)
        # Map common long-form names to ISO codes
        _LANG_NAME_MAP = {
            "italian": "it", "ita": "it",
            "spanish": "es", "esp": "es", "spa": "es",
            "english": "en", "eng": "en",
            "french": "fr", "fra": "fr",
            "german": "de", "deu": "de",
            "portuguese": "pt", "por": "pt",
            "japanese": "ja", "jpn": "ja",
            "chinese": "zh", "zho": "zh",
            "arabic": "ar", "ara": "ar",
            "russian": "ru", "rus": "ru",
            "korean": "ko", "kor": "ko",
        }
        mapped = _LANG_NAME_MAP.get(babel_lang, babel_lang)
        # "auto" or other non-ISO values are NOT valid languages
        if mapped and len(mapped) == 2 and mapped != "au":
            _resolved_lang = mapped

    # Fallback chain: Babel → langdetect → env default → "en"
    if not _resolved_lang:
        _resolved_lang = _detect_language(input_text) if input_text else None
    if not _resolved_lang or _resolved_lang == "auto":
        _resolved_lang = os.getenv("GRAPH_DEFAULT_LANGUAGE", "en")

    final_state["language"] = _resolved_lang
    logger.info(f"[graph_runner] Language resolved: babel={final_state.get('emotion_metadata', {}).get('language', 'N/A')} → {_resolved_lang}")

    # Debug log (safe truncation)
    logger.debug("[graph_runner] Final state after invoke: %s",
                  json.dumps(final_state, indent=2, default=str)[:1000])
    logger.debug("[graph_runner] emotion_detected=%s keys=%s",
                 final_state.get('emotion_detected'),
                 list(final_state.keys()) if isinstance(final_state, dict) else 'NOT A DICT')

    # 4) Persist results (thread-safe LRU cache + PostgreSQL write-through)
    _session_put(user_id, final_state)

    # 4b) Persist conversation to PostgreSQL (restored Feb 23, 2026)
    # Note: save_conversation() was removed in Nov 2025 under the incorrect
    # assumption that semantic_grounding_node auto-saves to the conversations
    # table. In reality, VSGS only writes to Qdrant (semantic_states), not PG.
    # This restores relational persistence for multi-user production readiness.
    try:
        from core.agents.postgres_agent import PostgresAgent
        pg = PostgresAgent()
        pg.execute(
            "INSERT INTO conversations (user_id, input_text, slots, intent, language) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                user_id,
                input_text,
                json.dumps(final_state, default=str),
                final_state.get("intent", "unknown"),
                final_state.get("language", "en"),
            ),
        )
        logger.info("[graph_runner] Conversation persisted to PostgreSQL (user=%s, intent=%s)",
                     user_id, final_state.get("intent"))
    except Exception as e:
        logger.warning("[graph_runner] Failed to persist conversation to PostgreSQL: %s", e)

    # 5) Return final result
    if return_full:
        return final_state

    # Extract response - prioritize structured response from compose_node
    # Handle both nested and flattened response structures
    response = final_state.get("response") if isinstance(final_state, dict) else None
    
    # proactive_suggestions: ARCHIVED (domain-specific)
    
    # CASE 1: Valid nested response dict from compose_node
    if isinstance(response, dict) and "action" in response:
        # Already in correct format, just ensure Babel Gardens fields are present
        if not response.get("language_detected") and final_state.get("language_detected"):
            response["language_detected"] = final_state.get("language_detected")
            response["language_confidence"] = final_state.get("language_confidence")
            response["babel_status"] = final_state.get("babel_status")
            response["cultural_context"] = final_state.get("cultural_context")
        
        # 🎭 Phase 2.1: Propagate emotion detection from babel_emotion_node
        if final_state.get("emotion_detected"):
            response["emotion_detected"] = final_state.get("emotion_detected")
            response["emotion_confidence"] = final_state.get("emotion_confidence")
            response["emotion_intensity"] = final_state.get("emotion_intensity")
            response["emotion_secondary"] = final_state.get("emotion_secondary")
            response["emotion_reasoning"] = final_state.get("emotion_reasoning")
            response["emotion_sentiment_label"] = final_state.get("emotion_sentiment_label")
            response["emotion_sentiment_score"] = final_state.get("emotion_sentiment_score")
            response["emotion_metadata"] = final_state.get("emotion_metadata")
        
        # �️ FIX (Feb 10, 2026): Propagate Sacred Orders metadata (Orthodoxy + Vault)
        if final_state.get("orthodoxy_verdict"):
            response["orthodoxy_verdict"] = final_state.get("orthodoxy_verdict")
            response["orthodoxy_blessing"] = final_state.get("orthodoxy_blessing")
            response["orthodoxy_confidence"] = final_state.get("orthodoxy_confidence")
            response["orthodoxy_findings"] = final_state.get("orthodoxy_findings")
            response["orthodoxy_message"] = final_state.get("orthodoxy_message")
            response["orthodoxy_timestamp"] = final_state.get("orthodoxy_timestamp")
            response["theological_metadata"] = final_state.get("theological_metadata")
        
        if final_state.get("vault_blessing"):
            response["vault_blessing"] = final_state.get("vault_blessing")
            response["vault_status"] = final_state.get("vault_status")
        
        # ✅ FIX (Nov 2, 2025): Add intent, route, entity_ids to API response
        response["intent"] = final_state.get("intent")
        response["route"] = final_state.get("route")
        response["entity_ids"] = final_state.get("entity_ids")
        response["domain_params"] = final_state.get("domain_params", {})
        response["horizon"] = final_state.get("horizon")  # DEPRECATED backward-compat
        response["user_id"] = final_state.get("user_id")
        response["needed_slots"] = final_state.get("needed_slots", [])
        
        # ✅ FIX (Nov 4, 2025): Add VSGS fields to API response
        response["vsgs_status"] = final_state.get("vsgs_status")
        response["vsgs_elapsed_ms"] = final_state.get("vsgs_elapsed_ms")
        response["vsgs_error"] = final_state.get("vsgs_error")
        response["semantic_matches_count"] = len(final_state.get("semantic_matches", []))
        
        # 🕸️ FIX (Dec 25, 2025): Add Pattern Weaver context to API response
        response["weaver_context"] = final_state.get("weaver_context")
        
        # 🧠 FIX (Dec 28, 2025): Add CAN v2 fields to API response
        response["can_mode"] = final_state.get("can_mode")
        response["can_route"] = final_state.get("can_route")
        response["can_response"] = final_state.get("can_response")
        response["follow_ups"] = final_state.get("follow_ups")
        response["conversation_type"] = final_state.get("conversation_type")
        
        # 🎯 FIX (Dec 28, 2025): Add Advisor Node fields to API response
        response["advisor_recommendation"] = final_state.get("advisor_recommendation")
        response["user_requests_action"] = final_state.get("user_requests_action")
        
        # Domain extensions (opaque pass-through for domain graph_nodes)
        response["domain_extensions"] = _collect_domain_extensions(final_state)
        response["narrative"] = final_state.get("narrative")
        response["ok"] = final_state.get("ok")
        
        return response
    
    # CASE 2: Flattened structure - response fields at root level
    if isinstance(final_state, dict) and "action" in final_state:
        result = {
            "action": final_state.get("action"),
            "questions": final_state.get("questions", []),
            "needed_slots": final_state.get("needed_slots", []),
            "language_detected": final_state.get("language_detected"),
            "language_confidence": final_state.get("language_confidence"),
            "babel_status": final_state.get("babel_status"),
            "cultural_context": final_state.get("cultural_context"),
            "sentiment_label": final_state.get("sentiment_label"),
            "raw_output": final_state.get("raw_output"),
            # 🎭 Phase 2.1: Include emotion detection from babel_emotion_node
            "emotion_detected": final_state.get("emotion_detected"),
            "emotion_confidence": final_state.get("emotion_confidence"),
            "emotion_intensity": final_state.get("emotion_intensity"),
            "emotion_secondary": final_state.get("emotion_secondary"),
            "emotion_reasoning": final_state.get("emotion_reasoning"),
            "emotion_sentiment_label": final_state.get("emotion_sentiment_label"),
            "emotion_sentiment_score": final_state.get("emotion_sentiment_score"),
            "emotion_metadata": final_state.get("emotion_metadata"),
            # 🛡️ FIX (Feb 10, 2026): Add Sacred Orders metadata (Orthodoxy + Vault)
            "orthodoxy_verdict": final_state.get("orthodoxy_verdict"),
            "orthodoxy_blessing": final_state.get("orthodoxy_blessing"),
            "orthodoxy_confidence": final_state.get("orthodoxy_confidence"),
            "orthodoxy_findings": final_state.get("orthodoxy_findings"),
            "orthodoxy_message": final_state.get("orthodoxy_message"),
            "orthodoxy_timestamp": final_state.get("orthodoxy_timestamp"),
            "theological_metadata": final_state.get("theological_metadata"),
            "vault_blessing": final_state.get("vault_blessing"),
            "vault_status": final_state.get("vault_status"),
            # ✅ FIX (Nov 2, 2025): Add intent, route, entity_ids to API response
            "intent": final_state.get("intent"),
            "route": final_state.get("route"),
            "entity_ids": final_state.get("entity_ids"),
            "domain_params": final_state.get("domain_params", {}),
            "horizon": final_state.get("horizon"),  # DEPRECATED backward-compat
            "user_id": final_state.get("user_id"),
            # ✅ FIX (Nov 4, 2025): Add VSGS fields to API response
            "vsgs_status": final_state.get("vsgs_status"),
            "vsgs_elapsed_ms": final_state.get("vsgs_elapsed_ms"),
            "vsgs_error": final_state.get("vsgs_error"),
            "semantic_matches_count": len(final_state.get("semantic_matches", [])),
            # 🕸️ FIX (Dec 25, 2025): Add Pattern Weaver context to API response
            "weaver_context": final_state.get("weaver_context"),
            # 🧠 FIX (Dec 28, 2025): Add CAN v2 fields to API response
            "can_mode": final_state.get("can_mode"),
            "can_route": final_state.get("can_route"),
            "can_response": final_state.get("can_response"),
            "follow_ups": final_state.get("follow_ups"),
            "conversation_type": final_state.get("conversation_type"),
            # 🎯 FIX (Dec 28, 2025): Add Advisor Node fields to API response
            "advisor_recommendation": final_state.get("advisor_recommendation"),
            "user_requests_action": final_state.get("user_requests_action"),
            # Domain extensions (opaque pass-through for domain graph_nodes)
            "domain_extensions": _collect_domain_extensions(final_state),
            "narrative": final_state.get("narrative"),
            "ok": final_state.get("ok"),
        }
        
        return result
    
    # CASE 3: No action field - likely semantic_fallback or error
    # Compose a minimal valid response with available metadata
    # Propagate ALL fields consistently (parity with CASE 1 and CASE 2)
    _s = final_state if isinstance(final_state, dict) else {}
    return {
        "action": "clarify",
        "questions": ["Unable to process request. Please provide more details."],
        "semantic_fallback": True,
        "needed_slots": _s.get("needed_slots", []),
        "language_detected": _s.get("language_detected"),
        "language_confidence": _s.get("language_confidence"),
        "babel_status": _s.get("babel_status"),
        "cultural_context": _s.get("cultural_context"),
        # Emotion detection
        "emotion_detected": _s.get("emotion_detected"),
        "emotion_confidence": _s.get("emotion_confidence"),
        "emotion_intensity": _s.get("emotion_intensity"),
        "emotion_secondary": _s.get("emotion_secondary"),
        "emotion_reasoning": _s.get("emotion_reasoning"),
        "emotion_sentiment_label": _s.get("emotion_sentiment_label"),
        "emotion_sentiment_score": _s.get("emotion_sentiment_score"),
        "emotion_metadata": _s.get("emotion_metadata"),
        # Core routing
        "intent": _s.get("intent"),
        "route": _s.get("route"),
        "entity_ids": _s.get("entity_ids"),
        "horizon": _s.get("horizon"),
        "user_id": _s.get("user_id"),
        # Sacred Orders: Orthodoxy
        "orthodoxy_verdict": _s.get("orthodoxy_verdict"),
        "orthodoxy_blessing": _s.get("orthodoxy_blessing"),
        "orthodoxy_confidence": _s.get("orthodoxy_confidence"),
        "orthodoxy_findings": _s.get("orthodoxy_findings"),
        "orthodoxy_message": _s.get("orthodoxy_message"),
        "orthodoxy_timestamp": _s.get("orthodoxy_timestamp"),
        "theological_metadata": _s.get("theological_metadata"),
        # Sacred Orders: Vault
        "vault_blessing": _s.get("vault_blessing"),
        "vault_status": _s.get("vault_status"),
        # VSGS
        "vsgs_status": _s.get("vsgs_status"),
        "vsgs_elapsed_ms": _s.get("vsgs_elapsed_ms"),
        "vsgs_error": _s.get("vsgs_error"),
        "semantic_matches_count": len(_s.get("semantic_matches", [])),
        # Pattern Weavers
        "weaver_context": _s.get("weaver_context"),
        # CAN
        "can_mode": _s.get("can_mode"),
        "can_route": _s.get("can_route"),
        "can_response": _s.get("can_response"),
        "follow_ups": _s.get("follow_ups"),
        "conversation_type": _s.get("conversation_type"),
        # Advisor
        "advisor_recommendation": _s.get("advisor_recommendation"),
        "user_requests_action": _s.get("user_requests_action"),
        # Domain extensions (opaque pass-through for domain graph_nodes)
        "domain_extensions": _collect_domain_extensions(_s),
        "narrative": _s.get("narrative"),
        "ok": _s.get("ok"),
    }


def run_graph(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Variant that accepts an API-style payload:
    - { "input": "..." }
    - { "input_text": "..." }
    - { "user_id": "..." }
    """
    logger.debug("[run_graph] Incoming payload: %s", payload)

    if not payload:
        return run_graph_once("", "demo")

    text = payload.get("input") or payload.get("input_text") or ""
    user_id = payload.get("user_id", "demo")
    logger.debug("[run_graph] user_id=%s, input_text=%s", user_id, text.strip())

    return run_graph_once(text.strip(), user_id)
