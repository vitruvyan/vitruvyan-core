# core/langgraph/node/llm_soft_node.py
"""
📊 VSGS PR-C — Semantic Context Injection in LLM Prompts
Sacred Order: Discourse Layer (Linguistic Reasoning)

Injects semantic grounding context from VSGS into LLM prompts
with structured sections and budget enforcement.

VSGS Integration (PR-C):
- Semantic context injection with VSGS_PROMPT_BUDGET_CHARS limit
- Multi-section prompt: USER INTENT → SEMANTIC CONTEXT → TECHNICAL DATA → VEE MODE
- Prometheus metrics: vsgs_context_chars tracking
- Audit logging: prompt_injection events

Author: Vitruvyan Team
Date: November 4, 2025
Sacred Order: Discourse
"""

from typing import Dict, Any, List
from core.agents.llm_agent import get_llm_agent
import os
from dotenv import load_dotenv

# VSGS PR-C imports
try:
    from core.monitoring.vsgs_metrics import record_context_chars, record_prompt_injection
except ImportError:
    def record_context_chars(*args, **kwargs): pass
    def record_prompt_injection(*args, **kwargs): pass

# from core.logging.audit import  # TODO: audit module not available audit
def audit(*args, **kwargs):
    pass  # Stub for audit

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# VSGS PR-C configuration
VSGS_ENABLED = int(os.getenv("VSGS_ENABLED", "0"))
VSGS_PROMPT_BUDGET_CHARS = int(os.getenv("VSGS_PROMPT_BUDGET_CHARS", "800"))
VSGS_GROUNDING_TOPK = int(os.getenv("VSGS_GROUNDING_TOPK", "3"))


def build_prompt(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Build structured prompt with VSGS semantic context injection (PR-C).
    
    Prompt Structure:
    1. USER INTENT: Raw user query
    2. SEMANTIC CONTEXT: Top-k semantic matches from Qdrant (if VSGS_ENABLED)
    3. TECHNICAL DATA: Neural Engine / CrewAI outputs
    4. VEE MODE: Explainability level requested
    
    Args:
        state: LangGraph state with semantic_matches, raw_output, intent
    
    Returns:
        List of messages for OpenAI API
    
    VSGS Integration:
        - Respects VSGS_PROMPT_BUDGET_CHARS limit
        - Records vsgs_context_chars metric
        - Audit logs prompt_injection event
    """
    lang = state.get("language", "en")
    user_input = state.get("input_text", "")
    intent = state.get("intent", "soft")
    user_id = state.get("user_id", "demo")
    trace_id = state.get("trace_id", "")
    vee_mode = state.get("vee_mode", "summary")
    
    # ============================================================
    # Section 1: USER INTENT
    # ============================================================
    prompt_sections = []
    prompt_sections.append(f"### USER INTENT\n{user_input.strip()}\n")

    # ============================================================
    # Section 2: SEMANTIC CONTEXT (VSGS PR-C)
    # ============================================================
    semantic_context_chars = 0
    if VSGS_ENABLED and state.get("semantic_matches"):
        context_lines = []
        semantic_matches = state["semantic_matches"][:VSGS_GROUNDING_TOPK]
        
        for i, match in enumerate(semantic_matches):
            # Extract match details
            text = match.get("text", match.get("payload", {}).get("phrase_text", "")).strip().replace("\n", " ")
            score = round(match.get("score", 0.0), 3)
            match_lang = match.get("language", match.get("payload", {}).get("language", lang))
            
            # Format context line
            context_line = f"{i+1}. [{match_lang}] ({score}) {text}"
            context_lines.append(context_line)
        
        # Build semantic context block
        context_block = "\n".join(context_lines)
        
        # Enforce budget limit
        if len(context_block) > VSGS_PROMPT_BUDGET_CHARS:
            context_block = context_block[:VSGS_PROMPT_BUDGET_CHARS] + "..."
        
        semantic_context_chars = len(context_block)
        prompt_sections.append(f"### SEMANTIC CONTEXT\n{context_block}\n")
        
        # Record metrics
        record_context_chars(chars=semantic_context_chars, user_id=user_id, node="llm_soft_node")
        record_prompt_injection(user_id=user_id, node="llm_soft_node", intent=intent)  # PR-C metric
        
        # Audit log
        audit(
            agent="prompt_injection",
            payload={
                "chars": semantic_context_chars,
                "matches": len(semantic_matches),
                "budget": VSGS_PROMPT_BUDGET_CHARS,
                "intent": intent
            },
            trace_id=trace_id,
            user_id=user_id
        )
    else:
        prompt_sections.append("### SEMANTIC CONTEXT\n(no grounding data available)\n")

    # ============================================================
    # Section 3: TECHNICAL DATA
    # ============================================================
    if state.get("raw_output"):
        tech_data_str = str(state['raw_output'])[:500]  # Limit technical data size
        prompt_sections.append(f"### TECHNICAL DATA\n{tech_data_str}\n")

    # ============================================================
    # Section 4: VEE MODE
    # ============================================================
    prompt_sections.append(f"### EXPLAINABILITY MODE\n{vee_mode}\n")

    # ============================================================
    # Base system message
    # ============================================================
    system_msg = (
        f"You are Leonardo, the empathetic and motivating AI advisor of Vitruvyan.\n"
        f"User language is {lang}.\n"
        "NEVER invent numbers or financial signals.\n"
        "NEVER output BUY/SELL recommendations.\n"
        "Always include a disclaimer about investment risk.\n"
    )

    if intent in ["soft", "horizon_advice"]:
        system_msg += (
            "Your job is to respond with empathy, clarity, and motivation. "
            "Focus on trust, fear, or doubts expressed by the user. "
            "Do not use technical jargon unless the user explicitly asks."
        )
    else:
        system_msg += (
            "Your job is to narrate technical analysis results in natural language. "
            "Translate structured outputs (trend, momentum, volatility, sentiment, neural engine) "
            "into an empathetic explanation the user can understand. "
            "If data is missing, acknowledge it gracefully instead of inventing values."
        )

    # Combine all sections
    full_prompt = "\n".join(prompt_sections)
    
    messages = [
        {"role": "system", "content": system_msg + "\n\n" + full_prompt},
        {"role": "user", "content": user_input},
    ]

    return messages


def llm_soft_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evolved node: handles both soft and technical intents.
    - Pure empathy if intent=soft
    - Technical narration if intent=trend/momentum/risk/... etc.
    - Integrates grounding from Qdrant
    """
    llm = get_llm_agent()
    try:
        messages = build_prompt(state)
        answer = llm.complete_with_messages(
            messages=messages,
            temperature=0.6,
            max_tokens=400,
        )
    except Exception as e:
        answer = f"(Soft node error: {e})"

    state["result"] = {
        "route": "llm_soft",
        "intent": state.get("intent", "soft"),
        "response_text": answer,
        "error": None,
    }
    return state
