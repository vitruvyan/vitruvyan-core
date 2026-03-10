"""
Compose Node - Narrative Synthesis (Contract v1.1 Compliant)

Category: LLM Node (Contract Section 3.2, Category 3)
Purpose: Synthesize pre-calculated results into natural language narrative
Transport: In-memory (LangGraph state)

Responsibilities (✅ Allowed):
- Extract pre-calculated metrics from state
- Synthesize information from multiple node outputs
- Generate natural language explanations
- Combine qualitative signals into narrative
- Adapt response based on user language/context

Forbidden (❌):
- Calculate domain metrics (z-scores, confidence, thresholds)
- Apply business logic thresholds
- Slot-filling (deprecated in favor of LLM-first)
- Domain-specific interpretation (finance, medical, etc.)

Contract Compliance:
- No sum(), min(), max(), sorted() on domain data
- No threshold comparisons (score > X)
- Extracts pre-calculated values only
- LLM = presentation layer, not calculation layer
"""

from typing import Dict, Any
import os
from core.agents.llm_agent import get_llm_agent
from core.agents.prompt_agent import get_prompt_agent
from vitruvyan_core.contracts.prompting import PromptRequest

# NOTE: Configuration via environment variables only.
# load_dotenv() is called in service entrypoints (main.py), not in core modules.

# Domain compose formatter hook — loaded lazily from domains/<domain>/compose_formatter.py
_COMPOSE_DOMAIN = os.getenv("GRAPH_DOMAIN", os.getenv("INTENT_DOMAIN", "generic"))
_domain_formatter = None
_domain_formatter_loaded = False


def _get_domain_formatter():
    """Lazy-load domain-specific compose formatter (returns callable or None)."""
    global _domain_formatter, _domain_formatter_loaded
    if _domain_formatter_loaded:
        return _domain_formatter
    _domain_formatter_loaded = True
    if _COMPOSE_DOMAIN and _COMPOSE_DOMAIN != "generic":
        try:
            import importlib
            mod = importlib.import_module(f"domains.{_COMPOSE_DOMAIN}.compose_formatter")
            _domain_formatter = getattr(mod, "format_domain_context", None)
        except (ImportError, AttributeError):
            pass
    return _domain_formatter


def compose_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesize pre-calculated results into natural language narrative.
    
    Contract-compliant LLM node: extracts domain-agnostic data from state
    and uses LLM to generate user-facing narrative without calculations.
    
    Args:
        state: LangGraph state with pre-calculated results from domain services
        
    Returns:
        Updated state with 'narrative' field containing synthesized response
        
    Example State Flow:
        Input:  state['service_result'] = {"status": "completed", "metrics": {"confidence": 0.85}}
        Output: state['narrative'] = "Analysis completed with high confidence (85%)."
    """
    print(f"\n🎨 [compose_node] Synthesizing narrative from pre-calculated results")
    
    # Extract pre-calculated data (domain-agnostic)
    intent = state.get("intent", "unknown")
    route = state.get("route", "direct")
    user_input = state.get("input_text", "")
    language = state.get("language", "en")
    # Validate language is a 2-letter ISO-639-1 code; fallback to env default or "en"
    if not language or not isinstance(language, str) or len(language) != 2 or language == "au":
        language = os.getenv("GRAPH_DEFAULT_LANGUAGE", "en")
    
    # Extract service results (opaque payloads)
    service_result = state.get("service_result", {})
    babel_result = state.get("babel_result", {})
    pattern_result = state.get("pattern_result", {})
    raw_output = state.get("raw_output", {})
    
    print(f"🎨 [compose_node] Intent: {intent}, Route: {route}, Language: {language}")
    print(f"🎨 [compose_node] Service results available: {list(service_result.keys()) if service_result else 'none'}")
    print(f"🎨 [compose_node] raw_output keys: {list(raw_output.keys()) if raw_output else 'empty'}")
    
    # Conversational mode (no service results)
    if not service_result and not raw_output and intent in ["greeting", "help", "clarify", "unknown"]:
        print(f"🎨 [compose_node] Conversational mode (no service results)")
        narrative = _generate_conversational_response(user_input, language, state)
        state["narrative"] = narrative
        state["action"] = "conversation"
        return state
    
    # Synthesis mode (has service results)
    narrative = _synthesize_from_results(
        service_result=service_result,
        babel_result=babel_result,
        pattern_result=pattern_result,
        raw_output=raw_output,
        user_input=user_input,
        language=language,
        intent=intent
    )
    
    state["narrative"] = narrative
    state["action"] = "synthesis"
    
    print(f"🎨 [compose_node] Generated narrative ({len(narrative)} chars)")
    return state


def _generate_conversational_response(
    user_input: str,
    language: str,
    state: Dict[str, Any]
) -> str:
    """
    Generate natural conversational response for queries without service results.
    
    ✅ Contract compliant: No domain calculations, pure LLM synthesis.
    
    Args:
        user_input: User's input text
        language: Detected language code (en, it, es, etc.)
        state: Full state for context extraction
        
    Returns:
        Natural language response string
    """
    try:
        llm = get_llm_agent()
        
        # Resolve system prompt via PromptAgent (domain-agnostic, multilingual)
        prompt_agent = get_prompt_agent()
        domain = state.get("domain", "generic")
        resolution = prompt_agent.resolve(PromptRequest(
            domain=domain,
            scenario="conversational",
            language=language,
        ))
        system_prompt = resolution.system_prompt
        
        # Extract emotion context if available (pre-calculated by emotion_detector node)
        emotion = state.get("emotion_detected", "neutral")
        if emotion and emotion != "neutral":
            emotion_hints = {
                "it": f"L'utente sembra {emotion}. Adatta il tono di conseguenza.",
                "en": f"The user seems {emotion}. Adapt your tone accordingly.",
                "es": f"El usuario parece {emotion}. Adapta tu tono en consecuencia.",
            }
            system_prompt += f" {emotion_hints.get(language, emotion_hints['en'])}"
        
        narrative = llm.complete(
            prompt=user_input,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=300,
        )
        
        print(f"🧠 [compose_node] LLM conversational response: {narrative[:80]}...")
        return narrative
        
    except Exception as e:
        print(f"⚠️ [compose_node] LLM generation failed: {e}")
        # Fallback to simple greeting (no LLM)
        fallbacks = {
            "it": "Ciao! Come posso aiutarti?",
            "en": "Hello! How can I help you?",
            "es": "¡Hola! ¿Cómo puedo ayudarte?",
        }
        return fallbacks.get(language, fallbacks["en"])


def _synthesize_from_results(
    service_result: Dict[str, Any],
    babel_result: Dict[str, Any],
    pattern_result: Dict[str, Any],
    raw_output: Dict[str, Any],
    user_input: str,
    language: str,
    intent: str
) -> str:
    """
    Synthesize narrative from pre-calculated service results.
    
    ✅ Contract compliant: Extracts metrics, doesn't calculate them.
    
    Args:
        service_result: Opaque payload from domain service
        babel_result: Language analysis results (pre-calculated)
        pattern_result: Pattern matching results (pre-calculated)
        raw_output: Neural engine or other processor results (pre-calculated)
        user_input: Original user query
        language: Detected language
        intent: Classified intent
        
    Returns:
        Synthesized natural language narrative
    """
    try:
        llm = get_llm_agent()
        
        # Build context from pre-calculated results (no computation)
        context_parts = []
        
        # Extract status (domain-agnostic)
        if service_result:
            status = service_result.get("status", "unknown")
            context_parts.append(f"Service status: {status}")
            
            # Extract metrics if available (pre-calculated)
            metrics = service_result.get("metrics", {})
            if metrics:
                context_parts.append(f"Metrics available: {list(metrics.keys())}")
        
        # Extract pattern confidence (pre-calculated by Pattern Weavers)
        if pattern_result:
            pattern_confidence = pattern_result.get("metrics", {}).get("avg_confidence")
            if pattern_confidence is not None:
                context_parts.append(f"Pattern confidence: {pattern_confidence:.2f}")
        
        # Extract raw output summary (pre-calculated)
        if raw_output:
            summary = raw_output.get("summary")
            if summary:
                context_parts.append(f"Analysis summary: {summary}")
            # Domain-specific context formatting (loaded via hook pattern)
            formatter = _get_domain_formatter()
            if formatter:
                domain_ctx = formatter(raw_output, state)
                if domain_ctx:
                    context_parts.extend(domain_ctx)
        
        context_str = "\n".join(context_parts) if context_parts else "No detailed results available"
        
        # Resolve system prompt via PromptAgent (domain-agnostic)
        prompt_agent = get_prompt_agent()
        resolution = prompt_agent.resolve(PromptRequest(
            domain=state.get("domain", "generic") if hasattr(state, 'get') else "generic",
            scenario="synthesis",
            language=language,
        ))
        system_prompt = (
            f"{resolution.system_prompt}\n"
            f"User language: {language}. Intent: {intent}. "
            f"Respond in {language}."
        )
        
        user_prompt = (
            f"User query: {user_input}\n\n"
            f"Pre-calculated results:\n{context_str}\n\n"
            f"Synthesize a natural, helpful response explaining these results."
        )
        
        narrative = llm.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=400,
        )
        
        print(f"🧠 [compose_node] LLM synthesis: {narrative[:80]}...")
        return narrative
        
    except Exception as e:
        print(f"⚠️ [compose_node] Synthesis failed: {e}")
        # Fallback to simple status report (no LLM)
        status = service_result.get("status", "completed") if service_result else "completed"
        return f"Analysis {status}."
