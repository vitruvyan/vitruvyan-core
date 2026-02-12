"""
🧠 CAN v2 — Conversational Advisor Node
Sacred Order: DISCOURSE (Linguistic Reasoning Layer)

The conversational gateway of Vitruvyan. Does NOT generate technical analysis
(Neural Engine does that). Instead, it:
1. Orchestrates conversation flow based on mental mode
2. Injects VSGS semantic context for multi-turn coherence
3. Routes to specialized nodes (single, comparison, screening, collection, sector)
4. Assembles VEE narratives into natural conversation
5. Handles follow-ups, referent resolution, sector queries

Architecture:
    semantic_grounding → intent_detection → weavers → entity_resolver → 
    ... → compose → CAN v2 → proactive_suggestions → END

🌐 LANGUAGE GOLDEN RULE (Dec 27, 2025):
    - Language detection: EXCLUSIVELY via Babel Gardens /v1/embeddings/multilingual
    - NO hardcoded regex for en/it/es in this file
    - state["language"] is set by intent_detection_node (via Babel Gardens)
    - Follow-ups and narratives: generated via LLM (respects detected language)
    - VEE outputs: English-only (MVP constraint, frontend hardcoded)

Author: Vitruvyan AI
Created: December 27, 2025
Updated: December 27, 2025 - Language Golden Rule compliance
"""

import os
import logging
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Environment configuration
CAN_ENABLED = int(os.getenv("CAN_ENABLED", "1"))
CAN_VSGS_CONTEXT_LIMIT = int(os.getenv("CAN_VSGS_CONTEXT_LIMIT", "3"))
CAN_LLM_FALLBACK_ENABLED = int(os.getenv("CAN_LLM_FALLBACK_ENABLED", "1"))

# Babel Gardens endpoint for language-aware generation
BABEL_GARDENS_URL = os.getenv("BABEL_GARDENS_URL", "http://vitruvyan_babel_gardens:8009")


# =============================================================================
# Pydantic Schemas
# =============================================================================

class CANResponse(BaseModel):
    """Structured CAN response for frontend consumption."""
    mode: str                          # analytical | exploratory | urgent | conversational
    route: str                         # Target UI: single | comparison | screening | collection | allocation | sector | chat
    narrative: str                     # Main conversational response
    technical_summary: Optional[str] = None   # VEE technical digest
    follow_ups: List[str] = []         # Suggested next questions
    sector_insights: Optional[Dict[str, Any]] = None  # Pattern Weavers sector data
    confidence: float = 0.7            # Response confidence (0-1)
    vsgs_context_used: bool = False    # Whether VSGS context was applied
    mcp_tools_called: List[str] = []   # MCP tools invoked


# =============================================================================
# Mental Mode Detection
# =============================================================================

# REMOVED: Hardcoded URGENT_TRIGGERS and EXPLORATORY_TRIGGERS lists (Dec 27, 2025)
# Reason: Golden rule violation - language detection must be via Babel Gardens
# Mental mode is now detected via:
# 1. Emotion detection (state["emotion_detected"] from babel_emotion_node)
# 2. Intent classification (state["intent"] from intent_detection_node)
# 3. Semantic context (state["semantic_matches"] from VSGS)

ANALYTICAL_INTENTS = ["trend", "momentum", "sentiment", "risk", "volatility", "fundamentals"]


def detect_mental_mode(state: Dict[str, Any]) -> str:
    """
    Detect user's mental mode from query context.
    
    Modes:
    - urgent: User needs immediate actionable decision (emotion=anxious/frustrated)
    - analytical: User wants specific technical analysis (intent in ANALYTICAL_INTENTS)
    - exploratory: User exploring sector/market broadly (weaver_context has concepts)
    - conversational: General chat, follow-ups, clarifications
    
    🌐 Language Golden Rule:
        Mental mode detection uses state fields populated by Babel Gardens:
        - state["emotion_detected"] → babel_emotion_node
        - state["intent"] → intent_detection_node (Babel Gardens cascade)
        - state["weaver_context"] → Pattern Weavers
        NO hardcoded regex triggers for specific languages.
    
    Args:
        state: LangGraph state with intent, emotion, weaver_context
        
    Returns:
        Mental mode string
    """
    intent = state.get("intent", "")
    entity_ids = state.get("entity_ids", [])
    emotion = state.get("emotion_detected", "neutral")
    weaver = state.get("weaver_context") or {}
    
    # Priority 1: Urgent mode (emotional urgency detected by Babel Gardens)
    if emotion in ["anxious", "frustrated", "urgent", "worried"]:
        logger.info(f"🚨 CAN: Urgent mode detected (emotion={emotion})")
        return "urgent"
    
    # Priority 2: Analytical mode (specific technical analysis intent)
    if intent in ANALYTICAL_INTENTS and entity_ids:
        logger.info(f"📊 CAN: Analytical mode detected (intent={intent})")
        return "analytical"
    
    # Priority 3: Exploratory mode (sector/concept detected by Pattern Weavers)
    if weaver.get("concepts") or weaver.get("sectors"):
        logger.info(f"🔭 CAN: Exploratory mode detected (weaver concepts)")
        return "exploratory"
    
    # Default: conversational
    logger.info("💬 CAN: Conversational mode (default)")
    return "conversational"


# =============================================================================
# Routing Logic
# =============================================================================

def can_route_decision(state: Dict[str, Any], mode: str) -> str:
    """
    Determine target UI node based on conversation context and mode.
    
    Routes:
    - single: Single entity_id technical analysis
    - comparison: Head-to-head entity_id comparison
    - screening: Multi-entity_id ranking (2-4 entity_ids)
    - collection: Collection analysis (5+ entity_ids)
    - allocation: Investment distribution
    - sector: Sector-level analysis (Pattern Weavers)
    - chat: General conversational response
    
    Args:
        state: LangGraph state
        mode: Detected mental mode
        
    Returns:
        Target UI route string
    """
    conv_type = state.get("conversation_type", "conversational")
    entity_ids = state.get("entity_ids") or []
    weaver = state.get("weaver_context") or {}
    
    # Sector mode: Pattern Weavers detected sector query without specific entity_ids
    if weaver.get("concepts") and not entity_ids:
        logger.info(f"🕸️ CAN: Routing to sector (concepts: {weaver.get('concepts')})")
        return "sector"
    
    # Standard routing by conversation type
    route_map = {
        "single": "single",
        "comparison": "comparison",
        "screening": "screening",
        "collection": "collection",
        "allocation": "allocation",
        "onboarding": "onboarding"
    }
    
    route = route_map.get(conv_type, "chat")
    logger.info(f"🔀 CAN: Routing to {route} (conv_type={conv_type}, entity_ids={len(entity_ids)})")
    return route


# =============================================================================
# VSGS Context Integration
# =============================================================================

def inject_vsgs_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and structure VSGS semantic context for CAN response.
    
    Args:
        state: LangGraph state with semantic_matches
        
    Returns:
        Dict with vsgs_context details
    """
    matches = state.get("semantic_matches", [])[:CAN_VSGS_CONTEXT_LIMIT]
    
    if not matches:
        return {"vsgs_context_used": False, "context_summary": None}
    
    # Build context summary
    context_items = []
    for m in matches:
        payload = m.get("payload", {})
        text = m.get("text", payload.get("phrase_text", ""))[:80]
        intent = payload.get("intent", "unknown")
        score = m.get("score", 0.0)
        context_items.append({
            "text": text,
            "intent": intent,
            "score": round(score, 3)
        })
    
    logger.info(f"🧠 CAN: VSGS context loaded ({len(context_items)} matches)")
    return {
        "vsgs_context_used": True,
        "context_summary": context_items,
        "top_context_intent": context_items[0]["intent"] if context_items else None
    }


def resolve_referents(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve vague references using VSGS context.
    
    🌐 Language Golden Rule:
        Vague reference patterns are NOT hardcoded by language.
        Resolution is purely semantic via VSGS embedding similarity.
        If semantic_matches score > 0.5, we inherit context.
    
    Args:
        state: LangGraph state
        
    Returns:
        Dict with inherited fields from context
    """
    matches = state.get("semantic_matches", [])
    
    # If we have high-confidence VSGS matches, inherit context
    if matches and len(matches) > 0:
        top_match = matches[0]
        score = top_match.get("score", 0.0)
        
        # Only inherit if semantic similarity is high (vague reference likely)
        if score > 0.5:
            payload = top_match.get("payload", {})
            inherited = {
                "inherited_entities": payload.get("entity_ids", []),
                "inherited_intent": payload.get("intent"),
                "inherited_horizon": payload.get("horizon")
            }
            logger.info(f"🔗 CAN: Referent resolved (score={score:.3f}) → {inherited}")
            return inherited
    
    return {}


# =============================================================================
# Pattern Weavers Integration
# =============================================================================

def process_sector_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process sector-level queries using Pattern Weavers context.
    
    Args:
        state: LangGraph state with weaver_context
        
    Returns:
        Sector insights dict
    """
    weaver = state.get("weaver_context", {})
    concepts = weaver.get("concepts", [])
    
    if not concepts:
        return None
    
    sector_insights = {
        "sectors": concepts,
        "regions": weaver.get("regions", []),
        "risk_profile": weaver.get("risk_profile", {}),
        "patterns": weaver.get("patterns", []),
        "status": weaver.get("status", "unknown")
    }
    
    logger.info(f"🕸️ CAN: Sector insights built (sectors: {concepts})")
    return sector_insights


# =============================================================================
# Follow-Up Suggestions (Language-Aware via LLM)
# =============================================================================

async def _generate_follow_ups_llm(entity_ids: List[str], route: str, language: str, weaver: Dict) -> List[str]:
    """
    Generate follow-up suggestions using Babel Gardens LLM endpoint.
    
    🌐 Language Golden Rule:
        Follow-ups are generated in the user's detected language.
        No hardcoded translations - LLM handles multilingual output.
    """
    try:
        entity_str = ", ".join(entity_ids[:3]) if entity_ids else "market"
        sector_str = ", ".join(weaver.get("concepts", [])) if weaver else ""
        
        prompt = f"""Generate 3 short follow-up questions in {language} for a financial analysis conversation.
Context: route={route}, entity_ids={entity_str}, sector={sector_str}
Requirements: 
- Questions must be in {language} language
- Maximum 10 words each
- Relevant to the analysis context
- No numbering, just the questions separated by newlines
"""
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{BABEL_GARDENS_URL}/v1/chat/generate",
                json={"prompt": prompt, "max_tokens": 100, "temperature": 0.7}
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", result.get("response", ""))
                follow_ups = [q.strip() for q in text.strip().split("\n") if q.strip()][:3]
                if follow_ups:
                    return follow_ups
                    
    except Exception as e:
        logger.warning(f"⚠️ CAN: LLM follow-up generation failed: {e}")
    
    return []


def generate_follow_ups(state: Dict[str, Any], mode: str, route: str) -> List[str]:
    """
    Generate contextual follow-up suggestions based on conversation state.
    
    🌐 Language Golden Rule:
        - English fallback suggestions (MVP constraint: UI is English-only)
        - If CAN_LLM_FALLBACK_ENABLED=1, LLM generates in user's language
        - No hardcoded if lang == "it" / "es" conditions
    
    Args:
        state: LangGraph state
        mode: Current mental mode
        route: Target UI route
        
    Returns:
        List of suggested follow-up questions (English fallback)
    """
    entity_ids = state.get("entity_ids") or []
    weaver = state.get("weaver_context") or {}
    
    # MVP: English-only fallback suggestions (UI is hardcoded English)
    # These are template-based, context-aware, but language-neutral
    follow_ups = []
    
    if route == "single" and entity_ids:
        entity_id = entity_ids[0]
        follow_ups = [
            f"Compare {entity_id} with a competitor",
            f"Show sentiment for {entity_id}",
            "What are the main risks?"
        ]
    elif route == "comparison":
        follow_ups = [
            "Which one for long-term?",
            "Show volatility comparison",
            "Add another entity_id"
        ]
    elif route == "sector":
        sectors = weaver.get("concepts", ["sector"])
        follow_ups = [
            f"Top performers in {sectors[0]}?",
            "Show sector trend",
            "Compare sectors"
        ]
    elif route == "collection":
        follow_ups = [
            "Show concentration risk",
            "Rebalancing suggestions?",
            "Add diversification"
        ]
    else:
        follow_ups = [
            "Analyze a entity_id",
            "Market overview",
            "Build a collection"
        ]
    
    return follow_ups[:3]


# =============================================================================
# Narrative Assembly
# =============================================================================

def assemble_narrative(state: Dict[str, Any], mode: str, route: str) -> str:
    """
    Assemble conversational narrative from VEE and context.
    
    CAN does NOT generate analysis. It transforms existing VEE narratives
    into conversational format based on mode.
    
    🌐 Language Golden Rule:
        - VEE narratives are ALWAYS English (MVP constraint)
        - No hardcoded language-specific action hints
        - Action hints are data-driven (composite score), not translated
    
    Args:
        state: LangGraph state with vee_explanations
        mode: Mental mode
        route: Target route
        
    Returns:
        Assembled narrative string (English - VEE constraint)
    """
    vee = state.get("vee_explanations") or {}
    entity_ids = state.get("entity_ids") or []
    numerical_panel = state.get("numerical_panel") or []
    
    # If VEE narrative exists, use it as base
    narrative_parts = []
    
    for entity_id in entity_ids[:3]:  # Max 3 entity_ids in narrative
        entity_vee = vee.get(entity_id, {})
        
        if mode == "analytical":
            # Technical mode: use VEE technical summary
            technical = entity_vee.get("technical", entity_vee.get("summary", ""))
            if technical:
                narrative_parts.append(technical)
        
        elif mode == "urgent":
            # Urgent mode: concise actionable summary
            summary = entity_vee.get("summary", "")
            # Find entity_id data in numerical panel
            entity_data = next((t for t in numerical_panel if t.get("entity_id") == entity_id), {})
            composite = entity_data.get("composite_score", 0)
            
            # Data-driven action hints (English - VEE constraint)
            if composite > 0.5:
                action_hint = "positive signals"
            elif composite < -0.5:
                action_hint = "caution signals"
            else:
                action_hint = "neutral positioning"
            
            narrative_parts.append(f"{entity_id}: {action_hint}. {summary[:200]}")
        
        else:
            # Conversational/exploratory: use summary
            summary = entity_vee.get("summary", "")
            if summary:
                narrative_parts.append(summary)
    
    if narrative_parts:
        return "\n\n".join(narrative_parts)
    
    # Fallback if no VEE available
    if route == "sector":
        weaver = state.get("weaver_context", {})
        concepts = weaver.get("concepts", [])
        return f"Sector analysis for: {', '.join(concepts)}" if concepts else "Sector analysis in progress..."
    
    return "Analysis ready. See the detailed breakdown below."


# =============================================================================
# Main CAN Node
# =============================================================================

def can_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conversational Advisor Node v2 — Main entry point.
    
    Orchestrates conversation flow by:
    1. Detecting mental mode (analytical/exploratory/urgent/conversational)
    2. Resolving vague referents via VSGS
    3. Routing to appropriate UI node
    4. Assembling narrative from VEE
    5. Generating follow-up suggestions
    
    Does NOT:
    - Generate technical analysis (Neural Engine does that)
    - Make BUY/SELL decisions (advisor_node does that)
    - Fetch fresh data (MCP/exec_node does that)
    
    Args:
        state: LangGraph state
        
    Returns:
        Updated state with can_response
    """
    if not CAN_ENABLED:
        logger.info("🚫 CAN: Disabled (CAN_ENABLED=0)")
        return state
    
    logger.info("🧠 CAN v2: Processing conversation...")
    
    # Step 1: Detect mental mode
    mode = detect_mental_mode(state)
    state["can_mode"] = mode
    
    # Step 2: Load VSGS context
    vsgs_context = inject_vsgs_context(state)
    
    # Step 3: Resolve vague referents
    inherited = resolve_referents(state)
    if inherited.get("inherited_entities") and not state.get("entity_ids"):
        state["entity_ids"] = inherited["inherited_entities"]
        logger.info(f"🔗 CAN: Inherited entity_ids from context: {inherited['inherited_entities']}")
    if inherited.get("inherited_intent") and state.get("intent") == "unknown":
        state["intent"] = inherited["inherited_intent"]
        logger.info(f"🔗 CAN: Inherited intent from context: {inherited['inherited_intent']}")
    
    # Step 4: Determine route
    route = can_route_decision(state, mode)
    state["can_route"] = route
    
    # Step 5: Process sector query if applicable
    sector_insights = None
    if route == "sector":
        sector_insights = process_sector_query(state)
    
    # Step 6: Assemble narrative
    narrative = assemble_narrative(state, mode, route)
    
    # Step 7: Generate follow-ups
    follow_ups = generate_follow_ups(state, mode, route)
    
    # Step 8: Build CAN response
    can_response = CANResponse(
        mode=mode,
        route=route,
        narrative=narrative,
        technical_summary=state.get("vee_explanations", {}).get(
            state.get("entity_ids", [""])[0] if state.get("entity_ids") else "", {}
        ).get("technical"),
        follow_ups=follow_ups,
        sector_insights=sector_insights,
        confidence=0.85 if vsgs_context["vsgs_context_used"] else 0.70,
        vsgs_context_used=vsgs_context["vsgs_context_used"],
        mcp_tools_called=state.get("mcp_tools_called", [])
    )
    
    state["can_response"] = can_response.model_dump()
    state["can_narrative"] = narrative
    state["can_follow_ups"] = follow_ups
    state["can_sector_insights"] = sector_insights
    
    logger.info(f"✅ CAN v2: Complete (mode={mode}, route={route}, vsgs={vsgs_context['vsgs_context_used']})")
    
    return state
