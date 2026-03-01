"""
CAN Node - Conversational Advisor (Contract v1.1 Compliant)

Category: LLM Node (Contract Section 3.2, Category 3)
Purpose: Orchestrate conversation flow with LLM-generated narrative
Transport: In-memory (LangGraph state)

Responsibilities (✅ Allowed):
- Extract pre-calculated context from state (vsgs, emotion, weaver)
- Generate conversational narrative using LLM
- Route based on extracted intent/conversation_type
- Assemble follow-up suggestions
- Inject semantic context into prompts

Forbidden (❌):
- Apply thresholds to similarity scores (threshold comparisons)
- Calculate confidence or quality metrics
- Determine mental mode via hardcoded triggers
- Domain-specific semantic interpretation

Contract Compliance:
- No threshold comparisons (score > X)- Extracts routing decision from state (not calculated)
- LLM = presentation layer, not decision layer
- Domain-agnostic conversation orchestration
"""

from typing import Dict, Any, List, Optional
import os
import logging
import time
import httpx
from core.agents.llm_agent import get_llm_agent
from core.agents.qdrant_agent import QdrantAgent

# NOTE: Configuration via environment variables only.
# load_dotenv() is called in service entrypoints (main.py), not in core modules.

logger = logging.getLogger(__name__)

# Environment configuration
CAN_ENABLED = int(os.getenv("CAN_ENABLED", "1"))
CAN_VSGS_CONTEXT_LIMIT = int(os.getenv("CAN_VSGS_CONTEXT_LIMIT", "3"))
CAN_STORE_CONVERSATIONS = int(os.getenv("CAN_STORE_CONVERSATIONS", "1"))

# Embedding API endpoint (same used by qdrant_node)
EMBEDDING_API = os.getenv("EMBEDDING_API_URL", "http://embedding:8010/v1/embeddings/batch")

# Lazy-init Qdrant agent (only when storing conversations)
_qdrant_agent: Optional[QdrantAgent] = None


def _get_qdrant_agent() -> QdrantAgent:
    """Lazy singleton for QdrantAgent (avoids connection at import time)."""
    global _qdrant_agent
    if _qdrant_agent is None:
        _qdrant_agent = QdrantAgent()
    return _qdrant_agent


def can_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conversational advisor - LLM-driven narrative generation.
    
    Contract-compliant LLM orchestrator: extracts pre-calculated context
    and generates conversation without semantic thresholds or calculations.
    Disabled when CAN_ENABLED=0 (pass-through).
    
    Args:
        state: LangGraph state with pre-calculated intent, emotion, vsgs_context
        
    Returns:
        Updated state with narrative, follow_ups, routing decision
    """
    if not CAN_ENABLED:
        logger.info("🚫 CAN: Disabled (CAN_ENABLED=0)")
        return state

    logger.info("🧠 [can_node] Orchestrating conversational response")
    
    # Extract pre-calculated data (domain-agnostic)
    intent = state.get("intent", "unknown")
    conversation_type = state.get("conversation_type", "chat")
    user_input = state.get("input_text", "")
    language = state.get("language", "en")
    # Validate language is a 2-letter ISO-639-1 code; fallback to env default or "en"
    if not language or not isinstance(language, str) or len(language) != 2 or language == "au":
        language = os.getenv("GRAPH_DEFAULT_LANGUAGE", "en")
        logger.warning(f"[can_node] Invalid language '{state.get('language')}', using fallback: {language}")
    
    # Extract pre-calculated emotion (from emotion_detector node)
    emotion = state.get("emotion_detected", "neutral")
    emotion_confidence = state.get("emotion_confidence", 0.5)
    
    # Extract VSGS semantic context (pre-calculated matches)
    vsgs_context = _extract_vsgs_context(state)
    
    # Extract Pattern Weavers context (pre-calculated concepts)
    weaver_context = state.get("weaver_context", {})
    
    # Determine routing (based on pre-calculated fields, not thresholds)
    route = _determine_route(state, conversation_type, weaver_context)
    
    logger.info(f"🧠 [can_node] Intent: {intent}, Route: {route}, Emotion: {emotion}")
    
    # Generate conversational narrative with LLM
    narrative = _generate_conversational_narrative(
        user_input=user_input,
        intent=intent,
        language=language,
        emotion=emotion,
        vsgs_context=vsgs_context,
        weaver_context=weaver_context,
        state=state
    )
    
    # Generate follow-up suggestions (LLM-generated, not rule-based)
    follow_ups = _generate_follow_ups(intent, language, vsgs_context)
    
    # Update state
    state["narrative"] = narrative
    state["follow_ups"] = follow_ups
    state["route"] = route
    state["vsgs_context_used"] = bool(vsgs_context)

    # 📝 Store conversation exchange in conversations_embeddings (RAG Contract V1)
    if CAN_STORE_CONVERSATIONS and narrative and user_input:
        _store_conversation_exchange(user_input, narrative, language, intent, state)

    logger.info(f"🧠 [can_node] Narrative generated ({len(narrative)} chars), route: {route}")
    return state


def _extract_vsgs_context(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract VSGS semantic context from state.
    
    ✅ Contract compliant: No threshold comparisons, extracts pre-calculated matches.
    
    Args:
        state: LangGraph state with semantic_matches
        
    Returns:
        List of top context items (limited by CAN_VSGS_CONTEXT_LIMIT)
    """
    matches = state.get("semantic_matches", [])[:CAN_VSGS_CONTEXT_LIMIT]
    
    if not matches:
        return []
    
    # Extract context items (no score filtering - already pre-ranked by Qdrant)
    context_items = []
    for m in matches:
        payload = m.get("payload", {})
        text = m.get("text", payload.get("phrase_text", ""))[:80]
        intent_ctx = payload.get("intent", "unknown")
        score = m.get("score", 0.0)  # Extract only, no comparison
        
        context_items.append({
            "text": text,
            "intent": intent_ctx,
            "score": round(score, 3)  # Display value, not threshold filter
        })
    
    logger.info(f"🧠 [can_node] VSGS context extracted ({len(context_items)} matches)")
    return context_items


def _store_conversation_exchange(
    user_input: str,
    narrative: str,
    language: str,
    intent: str,
    state: Dict[str, Any],
) -> None:
    """
    Embed and store the conversation exchange in conversations_embeddings.

    RAG Contract V1 compliance: CAN node is the designated writer for
    conversations_embeddings (CORE tier). The exchange text is the
    concatenation of user input + assistant narrative, embedded via the
    shared Embedding API and upserted with a deterministic point ID
    to ensure idempotency.

    Runs fire-and-forget: failures are logged but never block the pipeline.
    Gated by CAN_STORE_CONVERSATIONS env var (default: 1).
    """
    try:
        from contracts.rag import deterministic_point_id, RAGPayload

        # Build exchange text for embedding (user turn + assistant turn)
        exchange_text = f"USER: {user_input}\nASSISTANT: {narrative[:500]}"

        # Generate embedding via shared API
        resp = httpx.post(
            EMBEDDING_API,
            json={"texts": [exchange_text]},
            timeout=10.0,
        )
        resp.raise_for_status()
        vector = resp.json()["embeddings"][0]

        # Deterministic point ID (same exchange = same ID = upsert idempotency)
        point_id = deterministic_point_id(exchange_text, "conversations_embeddings")

        # Build contract-compliant payload
        payload = RAGPayload(
            source="can_node",
            text=exchange_text[:1000],
            domain="generic",
            extra={
                "user_input": user_input[:500],
                "language": language,
                "intent": intent,
                "emotion": state.get("emotion_detected", "neutral"),
                "user_id": state.get("user_id", "anonymous"),
                "trace_id": state.get("trace_id", ""),
            },
        )

        # Upsert to Qdrant via agent
        agent = _get_qdrant_agent()
        agent.upsert(
            collection="conversations_embeddings",
            points=[{
                "id": point_id,
                "vector": vector,
                "payload": payload.to_dict(),
            }],
        )
        logger.info(f"📝 [can_node] Stored conversation exchange → conversations_embeddings (id={point_id[:12]}...)")

    except Exception as e:
        # Fire-and-forget: never block the pipeline
        logger.warning(f"⚠️ [can_node] Failed to store conversation exchange: {e}")


def _determine_route(
    state: Dict[str, Any],
    conversation_type: str,
    weaver_context: Dict[str, Any]
) -> str:
    """
    Determine UI route based on pre-calculated conversation type.
    
    ✅ Contract compliant: Routes based on extracted fields, not semantic interpretation.
    
    Args:
        state: LangGraph state
        conversation_type: Pre-calculated by intent_detection_node
        weaver_context: Pre-calculated by Pattern Weavers
        
    Returns:
        Route string (single, comparison, etc.)
    """
    entity_ids = state.get("entity_ids", [])
    
    # Sector mode: Pattern Weavers detected concepts without specific entities
    if weaver_context.get("concepts") and not entity_ids:
        logger.info(f"🕸️ [can_node] Routing to sector (concepts: {weaver_context.get('concepts')})")
        return "sector"
    
    # Standard routing map (domain-agnostic, extensible via conversation_type)
    route_map = {
        "single": "single",
        "comparison": "comparison",
        "onboarding": "onboarding"
    }
    
    # Pass through any conversation_type not in the map (domain plugins define their own)
    route = route_map.get(conversation_type, conversation_type if conversation_type else "chat")
    logger.info(f"🔀 [can_node] Routing to {route} (conversation_type={conversation_type})")
    return route


def _generate_conversational_narrative(
    user_input: str,
    intent: str,
    language: str,
    emotion: str,
    vsgs_context: List[Dict[str, Any]],
    weaver_context: Dict[str, Any],
    state: Dict[str, Any]
) -> str:
    """
    Generate conversational narrative using LLM.
    
    ✅ Contract compliant: Pure synthesis, no calculations or thresholds.
    
    Args:
        user_input: User's query
        intent: Pre-calculated intent
        language: Detected language
        emotion: Pre-calculated emotion
        vsgs_context: Pre-extracted VSGS matches
        weaver_context: Pre-calculated Pattern Weavers concepts
        state: Full state for additional pre-calculated fields
        
    Returns:
        Natural language narrative string
    """
    try:
        llm = get_llm_agent()
        
        # Build context summary (no semantic interpretation)
        context_summary = []
        if vsgs_context:
           context_summary.append(f"Previous context: {vsgs_context[0]['text'][:50]}...")
        if weaver_context.get("concepts"):
            context_summary.append(f"Concepts: {', '.join(weaver_context['concepts'][:3])}")
        
        context_str = " ".join(context_summary) if context_summary else "No prior context"
        
        # Build emotion-aware system prompt
        emotion_hints = {
            "en": {
                "anxious": "Respond calmly and reassuringly.",
                "frustrated": "Respond patiently and clearly.",
                "excited": "Match the enthusiasm positively.",
                "neutral": "Respond professionally and helpfully."
            },
            "it": {
                "anxious": "Rispondi con calma e rassicurazione.",
                "frustrated": "Rispondi con pazienza e chiarezza.",
                "excited": "Condividi l'entusiasmo positivamente.",
                "neutral": "Rispondi in modo professionale e utile."
            }
        }
        
        lang_hints = emotion_hints.get(language, emotion_hints["en"])
        emotion_hint = lang_hints.get(emotion, lang_hints["neutral"])
        
        system_prompt = (
            f"You are a conversational AI assistant. "
            f"User language: {language}. User intent: {intent}. "
            f"{emotion_hint} "
            f"Respond in {language}."
        )
        
        user_prompt = (
            f"User query: {user_input}\n"
            f"Context: {context_str}\n\n"
            f"Generate a natural, helpful conversational response."
        )
        
        narrative = llm.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=400,
        )
        
        logger.info(f"🧠 [can_node] LLM narrative: {narrative[:80]}...")
        return narrative
        
    except Exception as e:
        logger.error(f"⚠️ [can_node] LLM generation failed: {e}")
        # Fallback to simple response
        fallbacks = {
            "it": "Al momento non riesco a generare una risposta completa. Riprova.",
            "en": "I'm unable to generate a full response right now. Please try again.",
            "es": "No puedo generar una respuesta completa en este momento. Inténtalo de nuevo."
        }
        return fallbacks.get(language, fallbacks["en"])


def _generate_follow_ups(
    intent: str,
    language: str,
    vsgs_context: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate follow-up question suggestions using LLM.
    
    ✅ Contract compliant: Pure generation, no semantic filtering.
    
    Args:
        intent: Pre-calculated intent
        language: Detected language
        vsgs_context: Pre-extracted context
        
    Returns:
        List of follow-up question strings
    """
    try:
        llm = get_llm_agent()
        
        context_hint = ""
        if vsgs_context:
            context_hint = f"Previous context intent: {vsgs_context[0]['intent']}"
        
        prompt = (
            f"Generate 2-3 natural follow-up questions for intent '{intent}'. "
            f"{context_hint}. Language: {language}. "
            f"Return only the questions, one per line."
        )
        
        text = llm.complete(
            prompt=prompt,
            temperature=0.8,
            max_tokens=150,
        )
        follow_ups = [q.strip().lstrip("-•").strip() for q in text.split("\n") if q.strip()][:3]
        
        logger.info(f"🧠 [can_node] Generated {len(follow_ups)} follow-ups")
        return follow_ups
        
    except Exception as e:
        logger.error(f"⚠️ [can_node] Follow-up generation failed: {e}")
        return []  # Empty list on failure (graceful degradation)
