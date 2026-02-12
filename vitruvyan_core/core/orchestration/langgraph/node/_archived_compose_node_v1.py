from typing import Dict, Any
from core.orchestration.langgraph.memory_utils import merge_slots, check_slots
from core.vpar.vee.vee_engine import explain_entity
from core.vpar.vee.vee_engine import VEEEngine
from core.orchestration.langgraph.node.emotion_detector import detect_emotion, format_emotion_aware_response
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.orchestration.langgraph.shared.state_preserv import merge_ux_into_response  # 🎭 UX injection helper
from core.llm._legacy.conversational_llm import ConversationalLLM  # 🧠 LLM for natural conversations (LEGACY)
from openai import OpenAI
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# ----------------------------
# Helper: Preserve language metadata in responses
# ----------------------------
def _add_language_metadata(response: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Add Babel Gardens language metadata + essential state fields to response"""
    response["language_detected"] = state.get("language_detected")
    response["language_confidence"] = state.get("language_confidence")
    response["babel_status"] = state.get("babel_status")
    response["cultural_context"] = state.get("cultural_context")
    
    # 🆕 CRITICAL FIX (Nov 1, 2025): Include entity_ids in API response
    # Without this, frontend and tests receive entity_ids=null even when extracted
    response["entity_ids"] = state.get("entity_ids")
    
    return response

# ----------------------------
# Intents that require technical parameters (entity_id/budget/horizon)
# ----------------------------
TECHNICAL_INTENTS = [
    "collection", "trend", "momentum", "volatility", "backtest", "sentiment", 
    "horizon_advice", "risk_assessment", "soft", "screener", "exec", "unknown"
]

# ----------------------------
# Multilingual defaults for slot filling
# ----------------------------
DEFAULT_QUESTIONS = {
    "en": {
        "budget": "What is your investment budget?",
        "horizon": "Do you prefer a short, medium or long investment horizon?",
        "entity_ids": "Which entity would you like to invest in? (e.g., MSFT for Microsoft)"
    },
    "it": {
        "budget": "Qual è il tuo budget di investimento?",
        "horizon": "Preferisci un orizzonte breve, medio o lungo?",
        "entity_ids": "Su quale titolo vuoi investire? (es. MSFT per Microsoft)"
    },
    "es": {
        "budget": "¿Cuál es tu presupuesto de inversión?",
        "horizon": "¿Prefieres un horizonte de inversión corto, medio o largo?",
        "entity_ids": "¿En qué acción te gustaría invertir? (p. ej., MSFT para Microsoft)"
    }
}

# ----------------------------
# Slot filler question generator
# ----------------------------
def _humanize_slot_questions(missing: list[str], state: Dict[str, Any]) -> list[str]:
    lang = state.get("language", "en")
    defaults = DEFAULT_QUESTIONS.get(lang, DEFAULT_QUESTIONS["en"])

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = (
            f"You are Vitruvyan, a human and motivating financial advisor. "
            f"The user’s language is {lang}. "
            f"The following data is missing: {', '.join(missing)}. "
            "For each missing item, generate one clear, natural question. "
            f"Always answer in {lang}. "
            "Do not generate multiple variations, only one question per slot."
        )
        resp = client.chat.completions.create(
            model=os.getenv("GRAPH_LLM_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Reply only with the questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=120
        )
        text = resp.choices[0].message.content.strip()
        questions = [q.strip() for q in text.split("\n") if q.strip()]
        if not questions:
            questions = [defaults[s] for s in missing if s in defaults]
        return questions
    except Exception as e:
        print(f"⚠️ Error generating slot filler questions: {e}")
        return [defaults[s] for s in missing if s in defaults]


def _humanize_slot_questions_bundled(missing: list[str], state: Dict[str, Any]) -> str:
    """
    Generate ONE bundled question using ConversationalLLM for natural slot filling.
    
    🧠 NEW: Uses LLM to generate natural, context-aware questions instead of templates.
    This provides ChatGPT-level conversational fluidity.
    
    Args:
        missing: List of missing slot names (e.g., ["entity_ids", "horizon"])
        state: Full conversation state with user_input, known context, language, emotion
    
    Returns:
        Single natural bundled question asking for all missing slots with examples
    """
    lang = state.get("language", "en")
    user_input = state.get("input_text", "") or ""
    
    # Gather already known context
    merged = merge_slots(state, state.get("result", {}))
    known_context = {k: merged.get(k) for k in ["entity_ids", "budget", "horizon", "sectors"] if merged.get(k)}
    
    # 🔍 Extract semantic matches from Qdrant (Feature #1 + #4 integration)
    semantic_matches = state.get("semantic_matches", [])
    
    # 🧠 Use ConversationalLLM for natural question generation
    try:
        llm = ConversationalLLM()
        bundled_llm = llm.generate_slot_filling_question(
            user_input=user_input,
            missing_slots=missing,
            known_context=known_context,
            language=lang,
            semantic_matches=semantic_matches  # ✅ Qdrant contextual boost
        )
        
        # Apply emotion adaptation (existing UX enhancement)
        emotion = detect_emotion(user_input)
        bundled_adapted = format_emotion_aware_response(bundled_llm, emotion, lang, add_prefix=True)
        
        print(f"🧠 [compose_node] LLM slot filling question ({lang}): {bundled_adapted[:100]}...")
        return bundled_adapted
        
    except Exception as e:
        print(f"⚠️ [compose_node] LLM slot filling failed: {e}, falling back to template")
        # Fallback to template-based (legacy behavior)
        return _humanize_slot_questions_bundled_template(missing, state)


def _humanize_slot_questions_bundled_template(missing: list[str], state: Dict[str, Any]) -> str:
    """
    LEGACY: Template-based slot filling (fallback if LLM fails).
    Original implementation preserved for reliability.
    """
    lang = state.get("language", "en")
    user_input = state.get("input_text", "") or ""
    defaults = DEFAULT_QUESTIONS.get(lang, DEFAULT_QUESTIONS["en"])

    # Try simple inference from the user input (lightweight, local)
    inferred = {}
    ui = user_input.lower()
    if any(k in ui for k in ["conserv", "conservative", "prudente", "basso rischio", "low risk"]):
        inferred["risk_tolerance"] = "low"
    if "tech" in ui or "tecn" in ui or "tecnologia" in ui:
        inferred["sector"] = "Technology"
    if "short" in ui or "breve" in ui or "giorni" in ui or "settim" in ui:
        inferred["horizon"] = "short"

    # Build bundled question in user's language with examples
    pieces = []
    for slot in missing:
        sample = defaults.get(slot, slot)
        if slot == "entity_ids":
            pieces.append(f"{sample} (es: AAPL, MSFT)")
        elif slot == "budget":
            pieces.append(f"{sample} (es: 5000, 10000 EUR)")
        elif slot == "horizon":
            pieces.append(f"{sample} (es: 6 mesi, 1 anno)")
        else:
            pieces.append(sample)

    # Chain-of-thought short recap to build trust
    cot = _generate_chain_of_thought_clarification(state, missing)

    if lang == "it":
        bundled = (
            f"{cot}\nPer darti un'analisi precisa, avrei bisogno di: {', '.join(pieces)}. "
            "Puoi rispondere in una sola riga, es.: 'AAPL, 5000 euro, 6 mesi'. "
            "Se preferisci, posso procedere con parametri conservativi." 
        )
    else:
        bundled = (
            f"{cot}\nTo give you a precise analysis I need: {', '.join(pieces)}. "
            "Please reply in a single line, e.g.: 'AAPL, 5000, 6 months'. "
            "If you prefer, I can proceed with conservative defaults." 
        )

    return bundled


def _generate_chain_of_thought_clarification(state: Dict[str, Any], missing: list[str]) -> str:
    """
    Enhanced chain-of-thought with emoji formatting for better UX.
    Shows what Vitruvyan understood, inferred, and needs - with clear visual structure.
    """
    lang = state.get("language", "en")
    intent = state.get("intent") or state.get("result", {}).get("intent", "analisi finanziaria")
    understood = []
    inferred = []

    merged = merge_slots(state, state.get("result", {}))
    for k in ["entity_ids", "budget", "horizon"]:
        if merged.get(k):
            understood.append(f"{k}: {merged.get(k)}")

    # reuse light inference from bundled function (but not to overwrite user data)
    ui = (state.get("input_text") or "").lower()
    if any(x in ui for x in ["conserv", "conservative", "basso rischio"]):
        inferred.append("risk_tolerance=low")
    if "tech" in ui:
        inferred.append("sector=Technology")

    if lang == "it":
        lines = ["🧠 Ho capito che stai chiedendo un'analisi finanziaria."]
        if understood:
            lines.append("\n✅ Identificato: " + ", ".join(understood) + ".")
        if inferred:
            lines.append("\n🔍 Dal contesto deduco: " + ", ".join(inferred) + ".")
        lines.append("\n\n💡 Mi serve ancora:")
        return " ".join(lines)
    elif lang == "ru":
        lines = ["🧠 Я понял, что вы просите финансовый анализ."]
        if understood:
            lines.append("\n✅ Определено: " + ", ".join(understood) + ".")
        if inferred:
            lines.append("\n🔍 Из контекста я вижу: " + ", ".join(inferred) + ".")
        lines.append("\n\n💡 Мне еще нужно:")
        return " ".join(lines)
    elif lang == "sr":
        lines = ["🧠 Razumem da tražite finansijsku analizu."]
        if understood:
            lines.append("\n✅ Identifikovano: " + ", ".join(understood) + ".")
        if inferred:
            lines.append("\n🔍 Iz konteksta vidim: " + ", ".join(inferred) + ".")
        lines.append("\n\n💡 Još mi treba:")
        return " ".join(lines)
    else:
        lines = ["🧠 I understand you are asking for a financial analysis."]
        if understood:
            lines.append("\n✅ Identified: " + ", ".join(understood) + ".")
        if inferred:
            lines.append("\n🔍 From context I infer: " + ", ".join(inferred) + ".")
        lines.append("\n\n💡 I still need:")
        return " ".join(lines)

# ----------------------------
# Conversation Type Detection (Multi-Scenario UX)
# ----------------------------
def detect_conversation_type(intent: str, entity_ids: list, has_ne_results: bool, user_input: str = "") -> str:
    """
    Detect UX scenario type for frontend rendering based on conversation context.
    
    This enables multi-scenario UX where the frontend adapts based on:
    - Single entity_id analysis → Strategic card with gauges
    - Multi-entity_id comparison → Comparison table with rankings
    - Onboarding/exploratory → Interactive wizard
    - Conversational fallback → Simple chat
    
    Args:
        intent: Detected intent (e.g., "trend", "momentum", "onboarding")
        entity_ids: List of extracted entity_ids
        has_ne_results: Whether Neural Engine results are available
        user_input: Original user query for context inference
    
    Returns:
        Conversation type: "single_entity_analysis" | "multi_entity_comparison" | 
                          "onboarding" | "conversational"
    """
    # Scenario 3: Onboarding (no entity_ids, exploratory intent)
    onboarding_intents = ["onboarding", "unknown", "general_question"]
    onboarding_keywords = [
        "non so", "aiutami", "vorrei investire", "come faccio", "principiante",
        "i don't know", "help me", "want to invest", "how do i", "beginner",
        "no sé", "ayúdame", "quiero invertir", "cómo hago", "principiante"
    ]
    
    if intent in onboarding_intents or (not entity_ids and any(kw in user_input.lower() for kw in onboarding_keywords)):
        return "onboarding"
    
    # Scenario 2: Multi-EntityId Comparison (2+ entity_ids with analysis intent)
    comparison_intents = ["trend", "momentum", "ranking", "screener", "sentiment"]
    comparison_keywords = ["confronta", "compare", "vs", "versus", "mejor", "migliore", "best"]
    
    if len(entity_ids) > 1 and has_ne_results:
        # Check if user explicitly requested comparison
        if intent in comparison_intents or any(kw in user_input.lower() for kw in comparison_keywords):
            return "multi_entity_comparison"
    
    # Scenario 1: Single EntityId Analysis (1 entity_id with technical analysis)
    technical_intents = ["trend", "momentum", "volatility", "sentiment", "ranking", "screener"]
    
    if len(entity_ids) == 1 and has_ne_results and intent in technical_intents:
        return "single_entity_analysis"
    
    # Default: Conversational (slot filling, general chat, unclear intent)
    return "conversational"


# ----------------------------
# Helper Functions for Multi-Scenario UX
# ----------------------------
def generate_final_verdict(composite_score: float) -> Dict[str, Any]:
    """
    Convert composite score to human-readable verdict for Scenario 1 (Single EntityId).
    
    Maps numerical composite score to actionable investment label with color coding.
    Used by frontend to render strategic card with clear Buy/Hold/Sell recommendation.
    
    Args:
        composite_score: Neural Engine composite z-score (-3.0 to +3.0 typical range)
    
    Returns:
        Dict with label, color, composite_score, confidence (0-1 scale)
    
    Example:
        generate_final_verdict(1.85) → {
            "label": "Strong Buy",
            "color": "green",
            "composite_score": 1.85,
            "confidence": 0.93
        }
    """
    if composite_score is None:
        return {
            "label": "Insufficient Data",
            "color": "gray",
            "composite_score": None,
            "confidence": 0.0
        }
    
    # Thresholds based on z-score distribution (normal distribution)
    # >1.5 = top 7% (Strong Buy), >0.5 = top 31% (Buy), etc.
    if composite_score > 1.5:
        label = "Strong Buy"
        color = "green"
    elif composite_score > 0.5:
        label = "Buy"
        color = "green"
    elif composite_score > -0.5:
        label = "Hold"
        color = "yellow"
    elif composite_score > -1.5:
        label = "Sell"
        color = "red"
    else:
        label = "Strong Sell"
        color = "red"
    
    # Confidence: higher absolute z-score = higher confidence
    # Map |z| to 0-1 scale (saturate at |z|=2.0)
    confidence = min(abs(composite_score) / 2.0, 1.0)
    
    return {
        "label": label,
        "color": color,
        "composite_score": composite_score,
        "confidence": round(confidence, 2)
    }


def generate_gauge(momentum_z: float, trend_z: float, vola_z: float, sentiment_z: float) -> Dict[str, str]:
    """
    Convert z-scores to traffic light colors for Scenario 1 (Single EntityId).
    
    Maps each factor's z-score to visual color indicator (green/yellow/orange/red/gray).
    Used by frontend to render 4 mini circular gauges in strategic card.
    
    Args:
        momentum_z: Momentum factor z-score (None if unavailable)
        trend_z: Trend factor z-score (None if unavailable)
        vola_z: Volatility factor z-score (None if unavailable, negative=low risk)
        sentiment_z: Sentiment factor z-score (None if unavailable)
    
    Returns:
        Dict mapping factor name to color string
    
    Example:
        generate_gauge(1.2, -0.3, -0.5, 0.8) → {
            "momentum": "green",    # Strong positive
            "trend": "orange",      # Weak negative
            "risk": "green",        # Low volatility (good)
            "sentiment": "yellow"   # Neutral-positive
        }
    """
    def get_color(z: float, invert: bool = False) -> str:
        """
        Map z-score to traffic light color.
        
        Args:
            z: Z-score value
            invert: If True, negative z is good (for volatility/risk)
        """
        if z is None:
            return "gray"
        
        # Invert for risk (negative volatility = good)
        if invert:
            z = -z
        
        # Thresholds: >1.0 excellent, >0.0 good, >-1.0 caution, <-1.0 bad
        if z > 1.0:
            return "green"
        elif z > 0.0:
            return "yellow"
        elif z > -1.0:
            return "orange"
        else:
            return "red"
    
    return {
        "momentum": get_color(momentum_z),
        "trend": get_color(trend_z),
        "risk": get_color(vola_z, invert=True),  # Low volatility = green (good)
        "sentiment": get_color(sentiment_z)
    }


def generate_comparison_matrix(entity_ids: list, ne_raw: Dict[str, Any]) -> list:
    """
    Extract comparison data from Neural Engine for Scenario 2 (Multi-EntityId).
    
    Builds ranked comparison matrix with all factors for each entity_id.
    Used by frontend to render comparison table with rankings and winner indicators.
    
    Args:
        entity_ids: List of entity_id symbols to compare
        ne_raw: Raw Neural Engine response with screener_results
    
    Returns:
        List of dicts sorted by composite_score (best to worst), each containing:
        - entity_id, rank, momentum_z, trend_z, vola_z, sentiment_z, composite_score
    
    Example:
        generate_comparison_matrix(["EXAMPLE_ENTITY_2", "EXAMPLE_ENTITY_1", "EXAMPLE_ENTITY_3"], ne_raw) → [
            {"entity_id": "EXAMPLE_ENTITY_2", "rank": 1, "momentum_z": 2.1, "composite_score": 1.92},
            {"entity_id": "EXAMPLE_ENTITY_1", "rank": 2, "momentum_z": 1.2, "composite_score": 0.85},
            {"entity_id": "EXAMPLE_ENTITY_3", "rank": 3, "momentum_z": -0.5, "composite_score": -0.73}
        ]
    """
    matrix = []
    
    # Extract screener results from Neural Engine response
    screener_results = ne_raw.get("screener_results", [])
    if not screener_results:
        print(f"⚠️ [generate_comparison_matrix] No screener_results in ne_raw")
        return []
    
    # Build matrix for each entity_id
    for entity_id in entity_ids:
        # Find entity_id in screener results
        entity_data = None
        for result in screener_results:
            if result.get("entity_id") == entity_id:
                entity_data = result
                break
        
        if not entity_data:
            print(f"⚠️ [generate_comparison_matrix] EntityId {entity_id} not found in screener_results")
            continue
        
        # Extract factors from entity_id data
        factors = entity_data.get("factors", {})
        
        matrix.append({
            "entity_id": entity_id,
            "momentum_z": factors.get("momentum_z"),
            "trend_z": factors.get("trend_z"),
            "vola_z": factors.get("vola_z"),
            "sentiment_z": factors.get("sentiment_z"),
            "composite_score": entity_data.get("composite_score"),
            "rank": 0  # Will be set after sorting
        })
    
    # Sort by composite score (best to worst)
    matrix.sort(key=lambda x: x["composite_score"] if x["composite_score"] is not None else -999, reverse=True)
    
    # Assign ranks
    for i, item in enumerate(matrix):
        item["rank"] = i + 1
    
    print(f"✅ [generate_comparison_matrix] Built matrix for {len(matrix)} entity_ids")
    return matrix


def generate_onboarding_cards() -> list:
    """
    Generate interactive cards for Scenario 3 (Onboarding).
    
    Creates wizard-style interactive cards for collecting user investment preferences.
    Used by frontend to render onboarding flow with sliders, buttons, and chips.
    
    Returns:
        List of card configs with type, field, label, options
    
    Example:
        generate_onboarding_cards() → [
            {
                "type": "slider",
                "field": "budget",
                "label": "Qual è il tuo budget? 💰",
                "min": 1000, "max": 100000, "step": 1000, "default": 10000
            },
            {
                "type": "buttons",
                "field": "horizon",
                "label": "Quanto a lungo pensi di investire? ⏰",
                "options": [
                    {"key": "short", "label": "Breve termine", "desc": "3-6 mesi", "icon": "⚡"},
                    {"key": "mid", "label": "Medio termine", "desc": "1-2 anni", "icon": "📈"},
                    {"key": "long", "label": "Lungo termine", "desc": "3+ anni", "icon": "🏔️"}
                ]
            },
            {
                "type": "chips",
                "field": "sectors",
                "label": "Quali settori ti interessano? 🎯",
                "options": ["Tech", "Finance", "Healthcare", "Energy", "Consumer", "Real Estate"]
            }
        ]
    """
    return [
        {
            "type": "slider",
            "field": "budget",
            "label": "Qual è il tuo budget? 💰",
            "label_en": "What is your budget? 💰",
            "label_es": "¿Cuál es tu presupuesto? 💰",
            "min": 1000,
            "max": 100000,
            "step": 1000,
            "default": 10000,
            "unit": "EUR"
        },
        {
            "type": "buttons",
            "field": "horizon",
            "label": "Quanto a lungo pensi di investire? ⏰",
            "label_en": "How long do you plan to invest? ⏰",
            "label_es": "¿Cuánto tiempo planeas invertir? ⏰",
            "options": [
                {
                    "key": "short",
                    "label": "Breve termine",
                    "label_en": "Short term",
                    "label_es": "Corto plazo",
                    "desc": "3-6 mesi",
                    "desc_en": "3-6 months",
                    "desc_es": "3-6 meses",
                    "icon": "⚡"
                },
                {
                    "key": "mid",
                    "label": "Medio termine",
                    "label_en": "Mid term",
                    "label_es": "Medio plazo",
                    "desc": "1-2 anni",
                    "desc_en": "1-2 years",
                    "desc_es": "1-2 años",
                    "icon": "📈"
                },
                {
                    "key": "long",
                    "label": "Lungo termine",
                    "label_en": "Long term",
                    "label_es": "Largo plazo",
                    "desc": "3+ anni",
                    "desc_en": "3+ years",
                    "desc_es": "3+ años",
                    "icon": "🏔️"
                }
            ]
        },
        {
            "type": "chips",
            "field": "sectors",
            "label": "Quali settori ti interessano? 🎯",
            "label_en": "Which sectors interest you? 🎯",
            "label_es": "¿Qué sectores te interesan? 🎯",
            "multi_select": True,
            "options": [
                "Technology",
                "Finance",
                "Healthcare",
                "Energy",
                "Consumer",
                "Real Estate",
                "Utilities",
                "Industrials"
            ]
        }
    ]


# ----------------------------
# Main Compose Node
# ----------------------------
def compose_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print(f"\n🎨 [compose_node] EXECUTING!")
    print(f"🎨 [compose_node] Route: {state.get('route')}, Intent: {state.get('intent')}")
    print(f"🎨 [compose_node] Has raw_output: {'raw_output' in state}")
    
    uid = state.get("user_id") or "demo"
    res = state.get("result") or {}

    # --- Semantic hits (Qdrant fallback) ---
    hits = res.get("hits", [])
    if hits:
        top = hits[0].get("payload", {})
        ctx_type = top.get("context_type")
        if ctx_type:
            res["intent"] = ctx_type
            res["summary"] = f"Semantic match: {ctx_type}"
            res["route"] = "semantic_qdrant"

    intent = res.get("intent", state.get("intent", "unknown"))
    route = res.get("route", state.get("route", "direct"))
    summary = res.get("summary", "")

    merged = merge_slots(state, res)
    merged["user_id"] = uid
    lang = state.get("language", "en")
    
    # ----------------------------
    # 🧠 CONVERSATIONAL ROUTING FIX (Oct 31, 2025)
    # Early return for pure conversational queries (no entity_ids + generic intent)
    # Prevents using stale raw_output from previous technical queries
    # ----------------------------
    entity_ids = state.get("entity_ids", [])
    user_input = state.get("input_text", "")
    
    # Intents that should trigger natural conversation when NO entity_ids present
    CONVERSATIONAL_INTENTS = ['unknown', 'help', 'greeting', 'clarify']
    
    if intent in CONVERSATIONAL_INTENTS and len(entity_ids) == 0:
        print(f"🧠 [compose_node] CONVERSATIONAL MODE: intent={intent}, entity_ids=[], bypassing Neural Engine")
        
        # Get emotion from Babel Gardens if available
        emotion = state.get("emotion_detected", "neutral")
        emotion_conf = state.get("emotion_confidence", 0.5)
        
        # 🌍 Language detection fallback (workaround for Babel Gardens short-phrase limitation)
        # Check for common Italian greetings/words that Babel might miss
        user_input_lower = user_input.lower()
        italian_markers = ["ciao", "buongiorno", "buonasera", "salve", "grazie", "prego", "scusa"]
        spanish_markers = ["hola", "buenos", "gracias", "por favor", "disculpa"]
        french_markers = ["bonjour", "bonsoir", "merci", "s'il vous plaît", "pardon"]
        
        print(f"🌍 [compose_node] Language check: lang={lang}, user_input_lower='{user_input_lower}'")
        print(f"🌍 [compose_node] Italian markers check: {[m for m in italian_markers if m in user_input_lower]}")
        
        if lang == "en" and any(marker in user_input_lower for marker in italian_markers):
            lang = "it"
            print(f"🌍 [compose_node] Language override: en → it (detected Italian markers)")
        elif lang == "en" and any(marker in user_input_lower for marker in spanish_markers):
            lang = "es"
            print(f"🌍 [compose_node] Language override: en → es (detected Spanish markers)")
        elif lang == "en" and any(marker in user_input_lower for marker in french_markers):
            lang = "fr"
            print(f"🌍 [compose_node] Language override: en → fr (detected French markers)")
        
        # Generate natural conversational response using OpenAI
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Build emotion-aware system prompt (multilingual)
            emotion_prompts = {
                "it": {
                    "curious": "Rispondi con entusiasmo e voglia di spiegare.",
                    "frustrated": "Rispondi con calma e chiarezza, aiutando l'utente a capire.",
                    "excited": "Rispondi con energia positiva e incoraggiamento.",
                    "confident": "Rispondi in modo diretto e professionale.",
                    "uncertain": "Rispondi con pazienza e offri rassicurazioni."
                },
                "en": {
                    "curious": "Respond with enthusiasm and willingness to explain.",
                    "frustrated": "Respond calmly and clearly, helping the user understand.",
                    "excited": "Respond with positive energy and encouragement.",
                    "confident": "Respond directly and professionally.",
                    "uncertain": "Respond patiently and offer reassurance."
                },
                "es": {
                    "curious": "Responde con entusiasmo y ganas de explicar.",
                    "frustrated": "Responde con calma y claridad, ayudando al usuario a entender.",
                    "excited": "Responde con energía positiva y aliento.",
                    "confident": "Responde de forma directa y profesional.",
                    "uncertain": "Responde con paciencia y ofrece tranquilidad."
                }
            }
            
            lang_prompts = emotion_prompts.get(lang, emotion_prompts["en"])
            emotion_prefix = lang_prompts.get(emotion, lang_prompts.get("confident"))
            
            system_intros = {
                "it": "Sei Leonardo, l'assistente AI di Vitruvyan, esperto di analisi finanziaria.",
                "en": "You are Leonardo, Vitruvyan's AI assistant, expert in financial analysis.",
                "es": "Eres Leonardo, el asistente de IA de Vitruvyan, experto en análisis financiero.",
                "fr": "Tu es Leonardo, l'assistant IA de Vitruvyan, expert en analyse financière."
            }
            
            system_prompt = (
                f"{system_intros.get(lang, system_intros['en'])} "
                f"{emotion_prefix} "
                f"Sei cordiale, professionale, e aiuti gli utenti con investimenti e analisi di mercato."
            )
            
            resp = client.chat.completions.create(
                model=os.getenv("GRAPH_LLM_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            narrative = resp.choices[0].message.content.strip()
            print(f"🧠 [compose_node] Generated conversational response: {narrative[:100]}...")
            
        except Exception as e:
            print(f"⚠️ [compose_node] Error generating conversational response: {e}")
            # Fallback to simple greeting
            greetings = {
                "it": "Ciao! Sono Leonardo, il tuo assistente per analisi finanziarie. Come posso aiutarti?",
                "en": "Hello! I'm Leonardo, your financial analysis assistant. How can I help you?",
                "es": "¡Hola! Soy Leonardo, tu asistente de análisis financiero. ¿Cómo puedo ayudarte?"
            }
            narrative = greetings.get(lang, greetings["en"])
        
        response_dict = {
            "narrative": narrative,
            "action": "conversation",
            "intent": intent,
            "emotion_detected": emotion,
            "emotion_confidence": emotion_conf,
            "explainability": {
                "simple": f"Natural conversation (intent: {intent})",
                "technical": f"• Route: conversational_llm\n• Intent: {intent}\n• EntityIds: 0\n• Emotion: {emotion} ({emotion_conf:.2f})",
                "detailed": f"Pure conversational query without technical parameters. Generated response with emotion awareness ({emotion})."
            },
            "user_id": uid
        }
        
        # Add language metadata
        response_dict = _add_language_metadata(response_dict, state)
        
        return {
            **state,
            "response": response_dict,
            "final_response": narrative,
            "route": "conversational_complete"
        }

    # ----------------------------
    # 🎯 PHASE 1.1: PRIORITY SLOT FILLING CHECK
    # Check slots BEFORE any other processing for intents that need technical params
    # BUT: Skip if we already have Neural Engine results to show!
    # ----------------------------
    # LLM Fallback: EntityId Disambiguation (if multiple entity_ids from same query)
    # ----------------------------
    entity_ids = state.get("entity_ids", [])
    if len(entity_ids) > 1 and intent in TECHNICAL_INTENTS:
        # Check if user intended multiple entity_ids or it's ambiguous extraction
        user_input = state.get("input_text", "").lower()
        
        # Heuristic: if query has "confronta", "compare", "vs", it's intentional multi-entity_id
        is_intentional = any(kw in user_input for kw in ["confronta", "compare", "vs", "versus", "e", "and", ","])
        
        if not is_intentional:
            # Ambiguous extraction - ask LLM for clarification
            from core.foundation.persistence.postgres_agent import PostgresAgent
            pg = PostgresAgent()
            
            # Get company names for entity_ids
            entity_names = {}
            for entity_id in entity_ids:
                query = "SELECT company_name FROM entity_ids WHERE entity_id = %s LIMIT 1"
                rows = pg.fetch_all(query, (entity_id,))
                if rows:
                    entity_names[entity_id] = rows[0][0]
                else:
                    entity_names[entity_id] = entity_id
            
            # Build clarification message
            lang = state.get("language", "en")
            if lang == "it":
                options = " o ".join([f"{t} ({entity_names.get(t, t)})" for t in entity_ids])
                clarification = f"Non ho capito quale titolo intendevi. Cercavi {options}?"
            elif lang == "es":
                options = " o ".join([f"{t} ({entity_names.get(t, t)})" for t in entity_ids])
                clarification = f"No entendí qué entity_id querías. ¿Buscabas {options}?"
            else:
                options = " or ".join([f"{t} ({entity_names.get(t, t)})" for t in entity_ids])
                clarification = f"I didn't understand which entity_id you meant. Were you looking for {options}?"
            
            response_dict = {
                "action": "clarify",
                "needed_slots": ["entity_choice"],
                "bundled_question": clarification,
                "questions": [clarification],
                "entity_options": [{"entity_id": t, "name": entity_names.get(t, t)} for t in entity_ids],
                "semantic_fallback": True,
                "proposed_changes": [],
                "explainability": {
                    "simple": "Multiple entity_ids matched - requesting user clarification",
                    "technical": f"Ambiguous extraction: {entity_ids}",
                    "detailed": f"Query '{user_input}' matched multiple entity_ids: {', '.join(entity_ids)}. No explicit comparison keywords found."
                }
            }
            
            return {
                **state,
                "response": _add_language_metadata(response_dict, state),
                "route": "entity_disambiguation"
            }
    
    # ----------------------------
    # Slot Filling (if technical intent and missing data)
    # ----------------------------
    print(f"🎨 [compose_node] Intent in TECHNICAL_INTENTS: {intent in TECHNICAL_INTENTS}")
    
    # Check if we have NE results - if yes, skip slot filling and show results!
    has_ne_results = "raw_output" in state and isinstance(state.get("raw_output"), dict) and "ranking" in state.get("raw_output", {})
    print(f"🎨 [compose_node] Has NE results: {has_ne_results}")
    
    if intent in TECHNICAL_INTENTS and not has_ne_results:
        missing = check_slots(merged)
        print(f"🎨 [compose_node] Missing slots: {missing}")
        
        if missing:
            # � Phase 2.1: Use Babel Gardens emotion if available, fallback to legacy
            user_input = state.get("input_text", "")
            
            # Check if babel_emotion_node already detected emotion
            if state.get("emotion_detected") is not None and state.get("emotion_confidence") is not None:
                emotion = state.get("emotion_detected")
                emotion_conf = state.get("emotion_confidence")
                print(f"🎭 [emotion] Using Babel Gardens (slot filler): {emotion} (confidence: {emotion_conf:.2f})")
            else:
                # Fallback to legacy detection
                babel_sentiment = {
                    "sentiment_label": state.get("sentiment_label"),
                    "sentiment_score": state.get("sentiment_score")
                } if state.get("sentiment_label") else None
                
                emotion, emotion_conf = detect_emotion(user_input, lang, babel_sentiment)
                print(f"🎭 [emotion] Detected (legacy - slot filler): {emotion} (confidence: {emotion_conf:.2f})")
            
            # Use bundled single-question clarification plus a short chain-of-thought recap
            bundled = _humanize_slot_questions_bundled(missing, merged)
            cot = _generate_chain_of_thought_clarification(merged, missing)
            
            # 🆕 Adapt bundled question based on emotion
            bundled_adapted = format_emotion_aware_response(bundled, emotion, lang, add_prefix=True)
            
            response_dict = {
                "action": "clarify", 
                "needed_slots": missing,
                "emotion_detected": emotion,  # 🆕 Store detected emotion
                "emotion_confidence": emotion_conf,  # 🆕 Store confidence
                "chain_of_thought": cot,  # Add as top-level field for display
                "bundled_question": bundled_adapted,  # 🆕 Emotion-adapted question
                "questions": [bundled_adapted],  # Legacy field for compatibility
                "semantic_fallback": True,
                "proposed_changes": [],
                "explainability": {
                    "simple": f"Missing slots: {', '.join(missing)}",
                    "technical": f"• Routing: slot_filler_priority\n• Intent: {intent}\n• Emotion: {emotion} ({emotion_conf:.2f})",
                    "detailed": cot
                },
                "user_id": uid
            }
            
            # 🎭 Phase 2.1: Merge UX metadata (belt-and-suspenders with manual emotion above)
            response_dict = merge_ux_into_response(response_dict, state)
            
            # Return with proper state update + emotion metadata
            return {
                **state,  # Preserve existing state
                "emotion_detected": emotion,  # 🆕 Add to global state
                "emotion_confidence": emotion_conf,  # 🆕 Add to global state
                "response": _add_language_metadata(response_dict, state),
                "route": "slot_filler_complete"
            }

    # ----------------------------
    # Neural Engine or Hybrid Response
    # ----------------------------
    print(f"🎨 [compose_node] Checking for Neural Engine output...")
    print(f"🎨 [compose_node] 'raw_output' in state: {'raw_output' in state}")
    if "raw_output" in state:
        print(f"🎨 [compose_node] raw_output type: {type(state['raw_output'])}")
        if isinstance(state["raw_output"], dict):
            print(f"🎨 [compose_node] raw_output keys: {list(state['raw_output'].keys())}")
    
    # 🆕 EMOTIONAL INTELLIGENCE: Use Babel Gardens emotion if available, fallback to legacy
    user_input = state.get("input_text", "")
    
    # 🎭 DEBUG: Check if babel_emotion fields are in state
    print(f"🎭 [compose_node] DEBUG: emotion_detected in state: {state.get('emotion_detected')}")
    print(f"🎭 [compose_node] DEBUG: emotion_confidence in state: {state.get('emotion_confidence')}")
    print(f"🎭 [compose_node] DEBUG: _ux_metadata in state: {state.get('_ux_metadata')}")
    print(f"🎭 [compose_node] DEBUG: State keys: {list(state.keys())}")
    
    # 🎭 Phase 2.1: Restore UX metadata from protected namespace if lost
    if "_ux_metadata" in state and not state.get("emotion_detected"):
        ux = state["_ux_metadata"]
        state["emotion_detected"] = ux.get("emotion_detected")
        state["emotion_confidence"] = ux.get("emotion_confidence")
        state["emotion_intensity"] = ux.get("emotion_intensity")
        state["emotion_secondary"] = ux.get("emotion_secondary")
        state["emotion_reasoning"] = ux.get("emotion_reasoning")
        state["emotion_sentiment_label"] = ux.get("emotion_sentiment_label")
        state["emotion_sentiment_score"] = ux.get("emotion_sentiment_score")
        state["emotion_metadata"] = ux.get("emotion_metadata")
        if "cultural_context" not in state or not state.get("cultural_context"):
            state["cultural_context"] = ux.get("cultural_context")
        print(f"🎭 [compose_node] Restored emotion from _ux_metadata: {state.get('emotion_detected')}")
    
    # 🎭 Phase 2.1: Prioritize babel_emotion_node over legacy detection
    # Check if emotion_detected exists (not just truthy, could be "neutral")
    if state.get("emotion_detected") is not None and state.get("emotion_confidence") is not None:
        # Use Babel Gardens emotion detection (already in state from babel_emotion_node)
        emotion = state.get("emotion_detected")
        emotion_conf = state.get("emotion_confidence")
        print(f"🎭 [emotion] Using Babel Gardens: {emotion} (confidence: {emotion_conf:.2f})")
    else:
        # Fallback to legacy regex-based detection ONLY for prompt adaptation
        # ⚠️ CRITICAL: Do NOT overwrite state! Legacy is only for local use.
        babel_sentiment = {
            "sentiment_label": state.get("sentiment_label"),
            "sentiment_score": state.get("sentiment_score")
        } if state.get("sentiment_label") else None
        
        emotion, emotion_conf = detect_emotion(user_input, lang, babel_sentiment)
        print(f"🎭 [emotion] Detected (legacy - for prompt only): {emotion} (confidence: {emotion_conf:.2f})")
        
        # ✅ FIX: Only update state if Babel didn't provide emotion
        # This prevents legacy from overwriting Babel Gardens detection
        if state.get("emotion_detected") is None:
            state["emotion_detected"] = emotion
            state["emotion_confidence"] = emotion_conf
            print(f"🎭 [emotion] No Babel emotion found, using legacy in state")
    
    if "raw_output" in state and isinstance(state["raw_output"], dict):
        ne_raw = state["raw_output"]
        if "ranking" in ne_raw:
            narrative_parts = []
            tech_parts = {}
            numerical_panel = []
            detailed = ne_raw

            # --- Factor phrases per language ---
            FACTOR_PHRASES = {
                "en": {"momentum": ("momentum positive", "momentum weak"),
                        "trend": ("trend strong", "trend weak"),
                        "volatility": ("volatility high", "volatility contained"),
                        "sentiment": ("sentiment bullish", "sentiment bearish")},
                "it": {"momentum": ("momentum positivo", "momentum debole"),
                        "trend": ("trend forte", "trend debole"),
                        "volatility": ("volatilità alta", "volatilità contenuta"),
                        "sentiment": ("sentiment rialzista", "sentiment ribassista")},
                "es": {"momentum": ("momentum positivo", "momentum débil"),
                        "trend": ("tendencia fuerte", "tendencia débil"),
                        "volatility": ("volatilidad alta", "volatilidad contenida"),
                        "sentiment": ("sentimiento alcista", "sentimiento bajista")},
            }
            phrases = FACTOR_PHRASES.get(lang, FACTOR_PHRASES["en"])

            for group_name in ["entities", "etf", "funds"]:
                items = ne_raw.get("ranking", {}).get(group_name, [])
                for item in items:
                    entity_id = item.get("entity_id")
                    comp = item.get("composite_score")
                    factors = item.get("factors", {})

                    mom = factors.get("momentum_z")
                    trd = factors.get("trend_z")
                    vol = factors.get("vola_z")
                    sent = factors.get("sentiment_z")

                    desc = []
                    def factor_phrase(name, val):
                        if val is None:
                            return f"{name} not available"
                        pos, neg = phrases[name]
                        return pos if val > 0 else neg

                    if mom is not None:
                        desc.append(factor_phrase("momentum", mom))
                    if trd is not None:
                        desc.append(factor_phrase("trend", trd))
                    if vol is not None:
                        desc.append(factor_phrase("volatility", vol))
                    if sent is not None:
                        desc.append(factor_phrase("sentiment", sent))

                    desc_text = ", ".join(desc) if desc else ""

                    # --- Narrative (will be replaced by VEE if available) ---
                    if comp is not None:
                        borderline = -0.2 < comp < 0.2
                        if borderline:
                            if lang == "it":
                                desc_text += ", ma il punteggio è borderline: valuta attentamente il rischio"
                            elif lang == "es":
                                desc_text += ", pero la puntuación es borderline: considera el riesgo"
                            else:
                                desc_text += ", but the score is borderline: consider the risk"
                        # Placeholder narrative (will be replaced by VEE)
                        if desc_text:
                            narrative_parts.append(f"{entity_id} {desc_text}. Composite score {comp}.")
                        else:
                            narrative_parts.append(f"{entity_id}: Composite score {comp}.")
                    else:
                        if desc_text:
                            narrative_parts.append(f"{entity_id}: {desc_text} (score not available).")
                        else:
                            narrative_parts.append(f"{entity_id}: Data being processed.")

                    # --- Panel row ---
                    numerical_panel.append({
                        "entity_id": entity_id,
                        "momentum_z": mom,
                        "trend_z": trd,
                        "vola_z": vol,
                        "sentiment_z": sent,
                        "composite_score": comp,
                        "borderline": -0.2 < (comp or 0) < 0.2 if comp is not None else False
                    })

                    # --- Explainability VEE 2.0 ---
                    tech_parts[entity_id] = {
                        "momentum_z": mom,
                        "trend_z": trd,
                        "vola_z": vol,
                        "sentiment_z": sent,
                        "composite_score": comp,
                    }
                    
                    # Use VEE 2.0 with fallback to legacy - PRESERVE MULTI-LEVEL STRUCTURE
                    vee_expl = None
                    vee_narrative = ""
                    print(f"🔮 [compose_node] Generating VEE for {entity_id}...")
                    try:
                        vee_engine = VEEEngine()
                        vee_expl = vee_engine.explain_entity(
                            entity_id=entity_id,
                            kpi={"momentum_z": mom, "trend_z": trd, "vola_z": vol, "sentiment_z": sent, "composite_score": comp},
                            profile={"level": "intermediate", "lang": lang, "source": "oracle"}
                        )
                        print(f"🔮 [compose_node] VEE 2.0 result type: {type(vee_expl)}")
                        # Extract narrative from VEE 2.0 for backward compatibility
                        if isinstance(vee_expl, dict):
                            print(f"🔮 [compose_node] VEE 2.0 dict keys: {list(vee_expl.keys())}")
                            # VEE 2.0 structure: {summary, technical, detailed, contextualized}
                            # Use summary for narrative (most accessible), full dict preserved below
                            vee_narrative = vee_expl.get("summary") or vee_expl.get("contextualized") or vee_expl.get("detailed") or vee_expl.get("narrative", vee_expl.get("explanation", ""))
                            print(f"🔮 [compose_node] VEE narrative (dict): {vee_narrative[:100] if vee_narrative else 'EMPTY'}")
                        elif isinstance(vee_expl, str):
                            vee_narrative = vee_expl
                            print(f"🔮 [compose_node] VEE narrative (str): {vee_narrative[:100]}")
                    except Exception as e:
                        # Fallback to legacy VEE
                        print(f"⚠️ VEE 2.0 fallback for {entity_id}: {e}")
                        try:
                            vee_expl = explain_entity(
                                entity_id=entity_id,
                                kpi={"momentum_z": mom, "trend_z": trd, "vola_z": vol, "sentiment_z": sent, "composite_score": comp},
                                profile={"lang": lang}
                            )
                            # Extract narrative from legacy VEE
                            if isinstance(vee_expl, dict):
                                vee_narrative = vee_expl.get("explanation", vee_expl.get("narrative", ""))
                            elif isinstance(vee_expl, str):
                                vee_narrative = vee_expl
                            print(f"🔮 [compose_node] Legacy VEE narrative: {vee_narrative[:100] if vee_narrative else 'EMPTY'}")
                        except Exception as e2:
                            print(f"❌ Legacy VEE fallback also failed for {entity_id}: {e2}")
                            vee_narrative = ""
                    
                    # ✅ PRESERVE FULL MULTI-LEVEL VEE STRUCTURE
                    tech_parts[entity_id]["vee"] = vee_expl
                    
                    # 🧠 VEE + LLM COOPERATION: Transform technical VEE into conversational narrative
                    print(f"🔮 [compose_node] VEE narrative for {entity_id}: {len(vee_narrative)} chars")
                    conversational_narrative = ""
                    
                    if vee_narrative and vee_narrative.strip():
                        # Try to generate conversational narrative using LLM
                        try:
                            llm = ConversationalLLM()
                            user_context = {
                                "query": state.get("input_text", ""),
                                "emotion": state.get("emotion_detected", "neutral"),
                                "history": state.get("last_conversation", {})
                            }
                            
                            # Transform VEE technical → conversational
                            conversational_narrative = llm.generate_vee_narrative(
                                vee_data=vee_expl if isinstance(vee_expl, dict) else {"narrative": vee_narrative},
                                user_context=user_context,
                                language=lang
                            )
                            print(f"🧠 [compose_node] LLM conversational narrative ({len(conversational_narrative)} chars): {conversational_narrative[:150]}...")
                            
                            # Use conversational narrative for user-facing response
                            if conversational_narrative and conversational_narrative.strip():
                                narrative_parts[-1] = f"{entity_id}: {conversational_narrative}"
                                # Store conversational version in vee structure
                                if isinstance(tech_parts[entity_id]["vee"], dict):
                                    tech_parts[entity_id]["vee"]["conversational"] = conversational_narrative
                            else:
                                # Fallback to VEE technical narrative
                                narrative_parts[-1] = f"{entity_id}: {vee_narrative}"
                                
                        except Exception as llm_error:
                            print(f"⚠️ [compose_node] LLM narrative generation failed for {entity_id}: {llm_error}, using VEE technical")
                            # Fallback to VEE technical narrative
                            if narrative_parts:
                                narrative_parts[-1] = f"{entity_id}: {vee_narrative}"
                    else:
                        print(f"⚠️ [compose_node] VEE narrative is empty for {entity_id}!")

            narrative = ". ".join([n.strip() for n in narrative_parts]) or "No data available."
            print(f"✨ [compose_node] Final narrative ({len(narrative)} chars): {narrative[:200]}...")

            # ✅ Extract VEE multi-level explanations from tech_parts
            vee_explanations = {}
            for entity_id, data in tech_parts.items():
                if "vee" in data and isinstance(data["vee"], dict):
                    vee_explanations[entity_id] = {
                        "summary": data["vee"].get("summary", ""),
                        "technical": data["vee"].get("technical", ""),
                        "detailed": data["vee"].get("detailed", ""),
                        "contextualized": data["vee"].get("contextualized", ""),
                        "conversational": data["vee"].get("conversational", "")  # 🧠 NEW: LLM-generated
                    }
            
            # 🎯 Detect conversation type for frontend multi-scenario UX
            entities_list = state.get("entity_ids", [])
            conversation_type = detect_conversation_type(
                intent=intent,
                entity_ids=entities_list,
                has_ne_results=True,  # We're in NE branch, so results exist
                user_input=state.get("input_text", "")
            )
            print(f"🎯 [compose_node] Conversation type: {conversation_type} (entity_ids={len(entities_list)}, intent={intent})")

            # 🎨 Generate scenario-specific data based on conversation type
            final_verdict = None
            gauge = None
            comparison_matrix = None
            comparison_narrative = None
            onboarding_cards = None
            
            if conversation_type == "single_entity_analysis" and len(entities_list) == 1:
                # Scenario 1: Single EntityId Analysis
                entity_id = entities_list[0]
                entity_data = tech_parts.get(entity_id, {})
                composite = entity_data.get("composite_score")
                
                if composite is not None:
                    final_verdict = generate_final_verdict(composite)
                    print(f"📊 [compose_node] Final verdict for {entity_id}: {final_verdict}")
                
                gauge = generate_gauge(
                    momentum_z=entity_data.get("momentum_z"),
                    trend_z=entity_data.get("trend_z"),
                    vola_z=entity_data.get("vola_z"),
                    sentiment_z=entity_data.get("sentiment_z")
                )
                print(f"🚦 [compose_node] Gauge colors: {gauge}")
                
            elif conversation_type == "multi_entity_comparison" and len(entities_list) > 1:
                # Scenario 2: Multi-EntityId Comparison
                comparison_matrix = generate_comparison_matrix(entities_list, ne_raw)
                print(f"📊 [compose_node] Comparison matrix: {len(comparison_matrix)} entity_ids ranked")
                
                # Generate LLM comparison narrative
                if comparison_matrix:
                    try:
                        llm = ConversationalLLM()
                        comparison_narrative = llm.generate_comparison_narrative(
                            comparison_matrix=comparison_matrix,
                            language=lang
                        )
                        print(f"💬 [compose_node] Comparison narrative ({len(comparison_narrative)} chars): {comparison_narrative[:150]}...")
                    except Exception as e:
                        print(f"⚠️ [compose_node] LLM comparison narrative failed: {e}")
                        comparison_narrative = None
                        
            elif conversation_type == "onboarding":
                # Scenario 3: Onboarding
                onboarding_cards = generate_onboarding_cards()
                print(f"🎛️ [compose_node] Generated {len(onboarding_cards)} onboarding cards")

            response = {
                "action": "answer",
                "narrative": narrative,
                "conversation_type": conversation_type,  # 🎯 NEW: Multi-scenario UX detection
                "numerical_panel": numerical_panel,
                "needed_slots": [],
                "questions": [],
                "semantic_fallback": res.get("semantic_fallback", False),  # ✅ Read from result
                "proposed_changes": [],
                "explainability": {
                    "simple": narrative,
                    "technical": tech_parts,
                    "detailed": detailed
                },
                # ✅ NEW: Multi-level VEE explanations (Motley Fool style)
                "vee_explanations": vee_explanations,
                
                # 🎨 NEW: Scenario-specific fields for multi-scenario UX
                "final_verdict": final_verdict,  # Scenario 1: Single entity_id
                "gauge": gauge,  # Scenario 1: Traffic light colors
                "comparison_matrix": comparison_matrix,  # Scenario 2: Multi-entity_id rankings
                "comparison_narrative": comparison_narrative,  # Scenario 2: LLM comparison text
                "onboarding_cards": onboarding_cards,  # Scenario 3: Interactive wizard
                
                # 🆕 CRITICAL FIX (Nov 1, 2025): Include entity_ids in response
                "entity_ids": state.get("entity_ids")  # ✅ Frontend and tests need this field
            }
            
            # 🎭 Phase 2.1: Inject emotion/language/cultural UX metadata
            response = merge_ux_into_response(response, state)

            out = {
                **state,  # 🆕 Preserve full state (includes emotion_detected and emotion_confidence)
                "response": response, 
                "user_id": uid, 
                "raw_output": ne_raw,
                "final_response": narrative  # Add plain text for easy access
            }

            # --- Sentiment enrichment ---
            if state.get("sentiment"):
                sentiment_lines = []
                for tk, data in state["sentiment"].items():
                    tag = data.get("sentiment_label", "NEUTRAL")
                    score = data.get("avg_score", 0.0)
                    if lang == "it":
                        sentiment_lines.append(f"Il sentiment su {tk} è {tag.lower()} (media={score:.2f}).")
                    elif lang == "es":
                        sentiment_lines.append(f"El sentimiento sobre {tk} es {tag.lower()} (media={score:.2f}).")
                    else:
                        sentiment_lines.append(f"Sentiment on {tk} is {tag.lower()} (avg={score:.2f}).")
                out["response"]["narrative"] += "\n\n" + " ".join(sentiment_lines)
                for row in out["response"]["numerical_panel"]:
                    if row["entity_id"] in state["sentiment"]:
                        # Adapt to sentiment_node format: sentiment_tag instead of sentiment_label
                        row["sentiment_label"] = state["sentiment"][row["entity_id"]].get("sentiment_tag") or state["sentiment"][row["entity_id"]].get("sentiment_label")
                        row["sentiment_avg"] = state["sentiment"][row["entity_id"]].get("sentiment_raw") or state["sentiment"][row["entity_id"]].get("avg_score", 0.0)

            return out

    # ----------------------------
    # Case: no_data fallback
    # ----------------------------
    if route == "no_data":
        messages = {
            "en": "Data is not currently available, but we are processing it. Please try again in a few minutes.",
            "it": "I dati non sono momentaneamente disponibili, ma li stiamo elaborando. Riprova tra qualche minuto.",
            "es": "Los datos no están disponibles en este momento, pero los estamos procesando. Vuelve a intentarlo en unos minutos."
        }
        response = {
            "action": "info",
            "narrative": messages.get(lang, messages["en"]),
            "semantic_fallback": False,
            "proposed_changes": [],
            "explainability": {
                "simple": "No recent data available.",
                "technical": f"Route=no_data; PG empty for entity_ids={state.get('entity_ids')}",
                "detailed": "The Neural Engine could not find recent logs in Postgres. CrewAI was triggered in background to populate them."
            },
            "user_id": uid
        }
        
        # 🎭 Phase 2.1: Inject UX metadata
        response = merge_ux_into_response(response, state)
        
        return _add_language_metadata(response, state)

    # ----------------------------
    # Slot Filler (Fallback for non-technical intents)
    # ----------------------------
    # Note: Technical intents already checked above with priority
    if intent not in TECHNICAL_INTENTS:
        missing = check_slots(merged)
        if missing:
            # Use bundled single-question clarification plus a short chain-of-thought recap
            bundled = _humanize_slot_questions_bundled(missing, merged)
            cot = _generate_chain_of_thought_clarification(merged, missing)
            response = {
                "action": "clarify", 
                "needed_slots": missing, 
                "questions": [bundled], 
                "semantic_fallback": True,
                "proposed_changes": [],
                "explainability": {
                    "simple": f"Missing slots: {', '.join(missing)}",
                    "technical": f"• Routing: semantic_fallback\n• Intent: {intent}",
                    "detailed": cot
                },
                "user_id": uid
            }
            
            # 🎭 Phase 2.1: Inject UX metadata
            response = merge_ux_into_response(response, state)
            
            return _add_language_metadata(response, state)

    # ----------------------------
    # Soft Response
    # ----------------------------
    if route == "llm_soft":
        raw = res.get("raw_output", {})
        answer = raw.get("answer") if isinstance(raw, dict) else str(raw)
        response = {
            "action": "answer",
            "needed_slots": [],
            "questions": [],
            "semantic_fallback": False,
            "proposed_changes": [],
            "summary": summary or answer,
            "explainability": {
                "simple": "Empathic response",
                "technical": f"• Routing: {route}\n• Intent: {intent}",
                "detailed": "Generated by LLM Soft Node (empathetic advisor)."
            },
            "user_id": uid
        }
        
        # 🎭 Phase 2.1: Inject UX metadata
        response = merge_ux_into_response(response, state)
        
        return _add_language_metadata(response, state)

    # ----------------------------
    # Normal Dispatcher Fallback
    # ----------------------------
    response = {
        "action": res.get("action", "answer"),
        "needed_slots": [],
        "questions": [],
        "semantic_fallback": res.get("semantic_fallback", False),
        "proposed_changes": res.get("proposed_changes", []),
        "explainability": {
            "simple": summary,
            "technical": f"• Routing: {route}\n• Intent: {intent}",
            "detailed": "Raw dispatcher output available in 'raw_output'."
        },
        "intent": intent,
        "route": route,
        "summary": summary,
        "user_id": uid
    }
    
    # 🎭 Phase 2.1: Inject UX metadata
    response = merge_ux_into_response(response, state)
    
    return _add_language_metadata(response, state)
    if "raw_output" in state:
        response["raw_output"] = state["raw_output"]
    elif "raw_output" in res:
        response["raw_output"] = res["raw_output"]

    if "sentiment" in state:
        response["sentiment"] = state["sentiment"]
    
    return _add_language_metadata(response, state)
