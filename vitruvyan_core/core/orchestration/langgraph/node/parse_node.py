import re
import logging
from core.cognitive.semantic_engine import parse_user_input
from core.agents.llm_agent import get_llm_agent

# Phase 2 Migration (Nov 5, 2025): COMPLETED
# Migrated to VSGS semantic_matches from semantic_grounding_node
# conversation_persistence imports removed
from core.agents.postgres_agent import PostgresAgent

# Setup logger
logger = logging.getLogger(__name__)

def _is_valid_entity(entity_id: str) -> bool:
    """
    Validates if a entity_id exists in PostgreSQL entity_ids table.
    Used by vague query resolution to avoid false positives.
    """
    try:
        pg = PostgresAgent()
        query = "SELECT 1 FROM entity_ids WHERE entity_id = %s LIMIT 1"
        rows = pg.fetch_all(query, (entity_id.upper(),))
        return len(rows) > 0
    except Exception:
        return False

def _detect_vague_query(text: str) -> bool:
    """
    Detects vague queries where entity_id extraction failed but user intent is clear.
    Examples: 'E ENTITY_1?', 'What about ENTITY_2?', 'anche ENTITY_3', 'EXAMPLE_ENTITY_1?'
    """
    if not text:
        return False
    txt = text.strip().lower()
    
    patterns = [
        r"^\s*e\s+\w+",           # "E NVDA?" (Italian conjunction)
        r"what about",            # "What about Tesla?"
        r"how about",             # "How about AAPL?"
        r"come prima",            # "Come prima ma con NVDA"
        r"anche\s+\w+",           # "anche TSLA"
        r"^\s*[A-Z]{2,5}\s*\??$"  # Solo entity_id: "NVDA?" or "EXAMPLE_ENTITY_1"
    ]
    return any(re.search(p, txt, re.IGNORECASE) for p in patterns)

def _detect_contextual_reference(text: str) -> bool:
    """
    ✅ LLM-FIRST APPROACH (Nov 1, 2025): Use GPT to detect contextual references
    
    Detects queries that refer to previous context requiring semantic search.
    Uses GPT-3.5 for semantic understanding instead of rigid regex patterns.
    
    Philosophy: "NO regex, solo capacità semantica LLM" - Project rule
    
    Examples that should return True:
    - 'come prima ma con NVDA'
    - 'E se lo confronto con Microsoft?'
    - 'E NVDA?'
    - 'what about MSFT?'
    - 'rispetto a AAPL come va?'
    - 'anche quello'
    
    Returns:
        bool: True if query is a follow-up/contextual reference, False otherwise
    """
    if not text or len(text.strip()) < 3:
        return False
    
    # Quick heuristic: Very short queries (< 15 chars) are often follow-ups
    # "E NVDA?" = 7 chars, "what about AAPL?" = 16 chars
    if len(text.strip()) < 15 and any(word in text.lower() for word in ['e ', 'and ', 'what ', 'how ', 'vs ', 'anche']):
        return True  # High probability follow-up, skip LLM call for speed
    
    # Use GPT-3.5 for semantic detection (fast + accurate)
    try:
        llm = get_llm_agent()
        
        prompt = f"""Does this query refer to previous context or is it a follow-up question?

Query: "{text}"

Answer ONLY "yes" or "no".

Examples:
- "E NVDA?" → yes (follow-up)
- "E se lo confronto con Microsoft?" → yes (comparison to previous)
- "Analizza AAPL" → no (standalone)
- "what about Tesla?" → yes (follow-up)
- "come prima ma con TSLA" → yes (explicit reference)
- "Quali sono i migliori titoli tech?" → no (standalone)

Answer:"""
        
        answer = llm.complete(
            prompt=prompt,
            temperature=0.0,
            max_tokens=5
        ).strip().lower()
        is_contextual = answer.startswith("yes") or answer.startswith("sì") or answer.startswith("si")
        
        logger.info(f"🤖 [LLM Contextual Detection] Query: '{text[:50]}...' → {answer} (contextual={is_contextual})")
        return is_contextual
        
    except Exception as e:
        logger.warning(f"⚠️ [LLM Contextual Detection] Failed, using heuristic fallback: {e}")
        # Fallback: Simple heuristic for common cases
        txt_lower = text.lower()
        return any(word in txt_lower for word in [
            'come prima', 'stesso', 'anche', 'e se', 'confronto', 
            'rispetto', 'what about', 'how about', 'compared to'
        ])

def _extract_entity_from_vague_query(text: str) -> list[str]:
    """
    Extracts entity_id from vague queries when semantic_engine fails.
    Returns list of entity_ids (usually 1 entity_id, or empty if extraction fails).
    """
    if not text:
        return []
    
    # Pattern 1: "E ENTITY_ID?" or "What about ENTITY_ID?" (1-5 char entity_ids)
    # Use \s+ to handle spaces, and allow 1-5 uppercase letters
    m = re.search(r"\b(e|and|what about|how about|anche)\s+([A-Z]{1,5})\b", text, re.IGNORECASE)
    if m:
        potential = m.group(2).upper()
        if _is_valid_entity(potential):
            return [potential]
    
    # Pattern 2: Solo entity_id "NVDA?" or "EXAMPLE_ENTITY_1" or "C?"
    m = re.search(r"^([A-Z]{1,5})\??$", text.strip())
    if m:
        potential = m.group(1).upper()
        if _is_valid_entity(potential):
            return [potential]
    
    # Pattern 3: Entity name → ID mapping (domain-configurable)
    # Override via ENTITY_NAME_MAP env var or domain plugin
    _entity_name_map = {
        # Minimal defaults — domain plugins extend this
    }
    for name, eid in _entity_name_map.items():
        if name in text.lower():
            if _is_valid_entity(eid):
                return [eid]
    
    return []

def _fallback_intent(user_input: str, entity_ids: list[str], budget: int, horizon: str) -> str:
    """Heuristic fallback — only used if intent_detection_node has not run."""
    txt = (user_input or "").lower()

    # Allocation: requires entity + budget
    if entity_ids and budget:
        return "allocate"

    # Soft intents: emotional / conversational
    if any(w in txt for w in ["preoccupato", "paura", "timore", "fiducia", "dubbi", "ansia",
                              "worry", "worried", "fear", "trust", "doubt", "concern"]):
        return "soft"

    # Generic analysis keywords
    if "analizza" in txt or "analyze" in txt or "study" in txt:
        return "trend"
    if "trend" in txt:
        return "trend"
    if "momentum" in txt:
        return "momentum"
    if "volatility" in txt or "volatilità" in txt:
        return "volatility"
    if "risk" in txt or "rischio" in txt:
        return "risk"
    if "backtest" in txt:
        return "backtest"
    if "collection" in txt or "portafoglio" in txt:
        return "collection"

    return "unknown"

def _extract_budget(text: str) -> int | None:
    """
    Extracts a numeric budget from user input if present.
    Examples: '5000 euro', '$10000', '2000 usd'
    """
    try:
        txt = text or ""
        m = re.search(r"(\d{3,})\s*(€|eur|euro|\$|usd)?", txt, flags=re.IGNORECASE)
        if m:
            return int(m.group(1))
    except Exception:
        return None
    return None


def parse_node(state: dict) -> dict:
    """
    Parses the user input with the semantic engine and updates the state.
    Always populates entity_ids, budget, and horizon if found.
    If the intent remains 'unknown', applies local fallback.
    Also merges with the last conversation slots from Postgres/Qdrant.
    """

    # Ensure 'result' is not present in the state at parse stage
    state.pop("result", None)

    def _extract_horizon(text: str) -> str | None:
        import re
        txt = (text or "").lower()

        # mesi
        m = re.search(r"(\d+)\s*(mesi|month|months|m)\b", txt)
        if m:
            val = int(m.group(1))
            if val <= 6:
                return "short"
            elif val <= 24:
                return "medium"
            else:
                return "long"

        # anni
        m = re.search(r"(\d+)\s*(anni|years|y)\b", txt)
        if m:
            val = int(m.group(1))
            if val <= 1:
                return "short"
            elif val <= 3:
                return "medium"
            else:
                return "long"

        return None
    user_input = state.get("input_text", "")
    user_id = state.get("user_id", "demo")
    
    # 🧠 Semantic Engine: Extract entities WITHOUT intent (delegated to GPT)
    # ⚠️ ENTITY_IDS DISABLED: Delegated to entity_resolver_node (Nuclear Option LLM-first)
    parsed = parse_user_input(user_input, extract_intent=False)

    # Extract base fields (NO INTENT SETTING - handled by intent_detection_node)
    entity_ids = []  # ✅ DISABLED - entity_resolver_node will extract via LLM
    horizon = parsed.get("horizon")
    budget = parsed.get("amount")
    semantic_matches = parsed.get("semantic_matches", [])  # ✅ Qdrant retrieval preserved

    # Regex fallback for budget
    if not budget:
        budget = _extract_budget(user_input)

    # Fallback per horizon
    if not horizon:
        horizon = _extract_horizon(user_input)

    # --- 🔑 VSGS SEMANTIC CONVERSATION HISTORY (Phase 2 Migration Nov 2025) ---
    # ✅ NEW: Use state["semantic_matches"] from semantic_grounding_node
    # semantic_matches is auto-populated by LangGraph pipeline with:
    # - Top 3-5 semantically similar past conversations
    # - User-scoped (filtered by user_id automatically)
    # - Scored by cosine similarity (0-1)
    
    # Get semantic matches from state (already populated by semantic_grounding_node)
    semantic_matches = state.get("semantic_matches", [])
    last_slots = {}
    
    if semantic_matches:
        # Use most similar conversation (first in list = highest score)
        last_slots = semantic_matches[0]
        score = last_slots.get("score", 0.0)
        print(f"🧠 [parse_node] Using VSGS semantic match (score={score:.3f})")
    else:
        print(f"🔙 [parse_node] No semantic matches found in state")
    
    # --- 🧠 CONTEXTUAL REFERENCE DETECTION ---
    # If query refers to previous context (e.g., "come prima ma con NVDA"),
    # use semantic search to find similar past queries
    contextual_slots = {}
    is_contextual = _detect_contextual_reference(user_input)
    if is_contextual:
        # Use most recent semantic match (already in last_slots)
        contextual_slots = last_slots
        print(f"🧠 [parse_node] Contextual reference detected! Using VSGS match")
        print(f"   Context slots: entity_ids={contextual_slots.get('entity_ids')}, horizon={contextual_slots.get('horizon')}")
    
    # Merge: current input > contextual search > last conversation
    # ✅ ENTITY_IDS: Delegated to entity_resolver_node (Nuclear Option)
    # 🎯 NUCLEAR OPTION: Store context entity_ids separately, don't set state["entity_ids"]
    context_entities = contextual_slots.get("entity_ids", []) or last_slots.get("entity_ids", [])
    
    merged_slots = {
        "budget": budget or contextual_slots.get("budget") or last_slots.get("budget"),
        "context_entities": context_entities,  # 🆕 Store as fallback, don't use immediately
        "horizon": horizon or contextual_slots.get("horizon") or last_slots.get("horizon"),
        # ❌ REMOVED: intent (delegated to intent_detection_node GPT-3.5)
    }

    # --- 🎯 VAGUE QUERY RESOLUTION ---
    # If no entity_ids extracted and query looks vague, try explicit extraction
    if not entity_ids and _detect_vague_query(user_input):
        vague_entities = _extract_entity_from_vague_query(user_input)
        if vague_entities:
            entity_ids = vague_entities
            merged_slots["context_entities"] = vague_entities  # 🆕 Update fallback

    # Update state with merged slots (NO INTENT - delegated to intent_detection_node)
    state["input_text"] = user_input  # ✅ CRITICAL: Always preserve original user input
    # ❌ REMOVED: state["intent"] = intent  (delegated to GPT intent_detection_node)
    # 🎯 NUCLEAR OPTION: Don't set state["entity_ids"] here - entity_resolver_node will set it
    state["context_entities"] = merged_slots.get("context_entities", [])  # 🆕 Fallback for entity_resolver
    state["horizon"] = merged_slots["horizon"]
    state["budget"] = merged_slots["budget"]
    state["amount"] = merged_slots["budget"]  # 🔑 ensure route_node sees amount
    state["companies"] = parsed.get("companies", [])
    state["route"] = parsed.get("route", "dispatcher_exec") if parsed.get("route") else "dispatcher_exec"
    state["semantic_matches"] = semantic_matches  # ✅ Qdrant matches for compose_node
    # Do NOT set state['result'] here. Only worker nodes should populate 'result'.

    return state
