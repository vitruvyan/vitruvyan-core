# Enhanced LLM Node with Intelligent Caching
# core/langgraph/node/cached_llm_node.py
#
# Domain-agnostic cached LLM orchestrator.
# System prompts come from PromptRegistry or env config — no hardcoded domain knowledge.

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Import our cache manager
from core.llm.cache_manager import get_cache_manager, CacheEntry
# Import LLMAgent
from core.agents.llm_agent import get_llm_agent

load_dotenv()

# Core personality prompt to inject consistent voice and behavior
VITRUVYAN_PERSONALITY_PROMPT = """
🎭 PERSONALITY CORE:
- Enthusiastic but never superficial
- Educational without being condescending
- Use emoji strategically (not spam)
- Celebrate user wins and admit uncertainty honestly

LANGUAGE:
- Use short validation phrases like "Perfect!", "Capisco..."
- Recap before acting: "If I understood correctly..."
- Offer options rather than commands

STRUCTURE:
1. Short emoji-led summary (1 sentence)
2. Key insight (bullet or short sentence)
3. Actionable next step
4. One question to keep engagement
"""

class CachedLLMOrchestrator:
    """
    Enhanced LLM orchestrator with intelligent caching.
    Domain-agnostic: system prompts are loaded from configuration,
    not hardcoded. Emotion detection adapts tone automatically.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm = get_llm_agent()
        self.cache_manager = get_cache_manager()
        
        # Model configuration (resolved via LLMAgent env var chain)
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1500"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
        self.logger.info("Cached LLM Orchestrator initialized")
    
    def process_with_cache(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method with multi-level caching strategy
        
        Cache levels:
        1. Exact match cache (Redis)
        2. Similar query cache (semantic similarity)
        3. Fresh LLM call (cached for future use)
        """
        
        try:
            # Determine prompt type for cache key
            prompt_type = self._determine_prompt_type(state)
            
            # Generate cache key
            cache_key = self.cache_manager.generate_cache_key(state, prompt_type)
            
            # Level 1: Try exact cache match
            cached_entry = self.cache_manager.get_cached_response(cache_key)
            if cached_entry:
                self.logger.info(f"CACHE HIT (exact): Saved {cached_entry.tokens_used} tokens")
                
                # Update state with cached response
                state["llm_response"] = cached_entry.response
                state["cache_info"] = {
                    "cache_hit": True,
                    "cache_type": "exact",
                    "tokens_saved": cached_entry.tokens_used,
                    "hit_count": cached_entry.hit_count,
                    "cached_at": cached_entry.timestamp.isoformat()
                }
                
                return state
            
            # Level 2: Try similar query cache
            similar_entries = self.cache_manager.find_similar_cached_responses(state, limit=3)
            if similar_entries:
                best_match = similar_entries[0]
                
                # Use similar response with adaptation note
                adapted_response = self._adapt_similar_response(best_match.response, state)
                
                self.logger.info(f"CACHE HIT (similar): Adapted response, saved ~{best_match.tokens_used * 0.7:.0f} tokens")
                
                state["llm_response"] = adapted_response
                state["cache_info"] = {
                    "cache_hit": True,
                    "cache_type": "similar",
                    "similarity_score": getattr(best_match, 'similarity_score', 0.0),
                    "tokens_saved": int(best_match.tokens_used * 0.7),
                    "adapted": True
                }
                
                # Cache this adapted response for exact future matches
                self.cache_manager.cache_response(
                    cache_key, adapted_response, state,
                    self.llm.default_model, int(best_match.tokens_used * 0.3)  # Estimated tokens for adaptation
                )
                
                return state
            
            # Level 3: Fresh LLM call
            return self._generate_fresh_response(state, cache_key, prompt_type)
            
        except Exception as e:
            self.logger.error(f"Cached LLM processing error: {e}")
            state["llm_response"] = self._generate_fallback_response(state)
            state["cache_info"] = {"cache_hit": False, "error": str(e)}
            return state
    
    def _determine_prompt_type(self, state: Dict[str, Any]) -> str:
        """Determine the type of prompt for cache optimization"""
        
        intent = state.get("intent", "").lower()
        
        if "analysis" in intent or "analisi" in intent:
            return "detailed_analysis"
        elif "compare" in intent or "confronta" in intent:
            return "comparison"
        elif "collection" in intent:
            return "collection"
        else:
            return "general"
    
    # NOTE: Emotion detection is handled by babel_emotion_node upstream in the graph.
    # No legacy fallback needed — if babel_emotion_node didn't run, default to neutral.
    
    def _adapt_similar_response(self, cached_response: str, current_state: Dict[str, Any]) -> str:
        """
        Adapt a similar cached response to current context
        Light adaptation to save tokens while maintaining relevance
        """
        
        # Extract key differences
        current_entitys = current_state.get("entity_ids", [])
        current_input = current_state.get("input_text", "")
        language = current_state.get("language", "it")
        
        # Simple adaptation prompts (very short to minimize token usage)
        
        # If entity_ids are different, add a brief adaptation note
        if current_entitys:
            entity_str = ", ".join(current_entitys[:3])  # Limit to 3 entities
            
            if language == "it":
                adaptation_note = f"\n\n*Risposta adattata per: {entity_str}*"
            else:
                adaptation_note = f"\n\n*Response adapted for: {entity_str}*"
            
            return cached_response + adaptation_note
        
        return cached_response
    
    def _generate_fresh_response(self, state: Dict[str, Any], cache_key: str, prompt_type: str) -> Dict[str, Any]:
        """Generate fresh LLM response and cache it"""
        
        # Build sophisticated prompt based on type
        system_prompt = self._build_system_prompt(state, prompt_type)
        user_prompt = self._build_user_prompt(state, prompt_type)
        
        try:
            # Track token usage
            start_time = datetime.now()
            
            llm_response = self.llm.complete(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            # Estimate tokens (LLMAgent tracks internally via metrics)
            tokens_used = len(system_prompt.split()) + len(user_prompt.split()) + len(llm_response.split())
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fresh LLM response: ~{tokens_used} tokens, {processing_time:.2f}s")
            
            # Cache the response
            self.cache_manager.cache_response(
                cache_key, llm_response, state, 
                self.llm.default_model, tokens_used
            )
            
            # Update state
            state["llm_response"] = llm_response
            state["cache_info"] = {
                "cache_hit": False,
                "tokens_used": tokens_used,
                "processing_time": processing_time,
                "model": self.llm.default_model
            }
            
            return state
            
        except Exception as e:
            self.logger.error(f"LLM API error: {e}")
            state["llm_response"] = self._generate_fallback_response(state)
            state["cache_info"] = {"cache_hit": False, "error": str(e)}
            return state
    
    def _build_system_prompt(self, state: Dict[str, Any], prompt_type: str) -> str:
        """Build sophisticated system prompt based on context"""
        
        language = state.get("language", "it")
        user_id = state.get("user_id", "user")
        
        base_prompts = {
            "it": {
                "detailed_analysis": """Sei Vitruvyan, un assistente AI esperto e professionale.

PERSONA: Analista senior con esperienza in analisi quantitativa e spiegazioni chiare.

STILE COMUNICATIVO:
- Tono professionale ma accessibile
- Combina dati tecnici con narrativa coinvolgente
- Usa metafore e analogie per concetti complessi
- Evidenzia sempre i rischi insieme alle opportunità

STRUTTURA RISPOSTA:
1. Sintesi esecutiva (2-3 frasi chiave)
2. Analisi dettagliata
3. Implicazioni e raccomandazioni
4. Avvertenze e limitazioni""",
            },
            
            "en": {
                "detailed_analysis": """You are Vitruvyan, a professional AI assistant with expertise in quantitative analysis.

PERSONA: Senior analyst specialized in clear explanations and data-driven insights.

COMMUNICATION STYLE:
- Professional yet accessible tone
- Combine technical data with engaging narrative
- Use metaphors and analogies for complex concepts
- Always highlight risks alongside opportunities

RESPONSE STRUCTURE:
1. Executive summary (2-3 key sentences)
2. Detailed analysis
3. Implications and recommendations
4. Caveats and limitations"""
            }
        }
        
        base = base_prompts.get(language, base_prompts["en"]).get(prompt_type, base_prompts[language]["detailed_analysis"])

        # Emotion-adaptive prompt injection
        # Emotion is populated by babel_emotion_node upstream in the graph.
        # If not available, default to neutral.
        emotion = state.get("emotion_detected", "neutral")
        emotion_conf = state.get("emotion_confidence", 0.0)
        
        # Simple emotion-to-prompt mapping (no legacy dependency)
        emotion_fragment = ""
        if emotion_conf >= 0.7 and emotion != "neutral":
            emotion_prompts = {
                "anxious": "User seems worried. Be reassuring, balanced, and risk-aware.",
                "frustrated": "User seems confused/frustrated. Be patient, break down concepts step-by-step.",
                "excited": "User is very enthusiastic. Balance their energy with professional caution.",
                "confused": "User doesn't understand. Explain simply, use examples, avoid jargon.",
                "confident": "User is confident. Provide concise, actionable information.",
                "curious": "User is curious. Provide informative, educational responses.",
            }
            emotion_fragment = emotion_prompts.get(emotion, "")

        # Compose final prompt: personality + emotion adaptation + base prompt
        final_prompt = VITRUVYAN_PERSONALITY_PROMPT + "\n\n"
        
        if emotion_fragment:
            final_prompt += emotion_fragment + "\n\n"
        
        final_prompt += base

        return final_prompt
    
    def _build_user_prompt(self, state: Dict[str, Any], prompt_type: str) -> str:
        """Build context-rich user prompt from state data"""
        
        user_input = state.get("input_text", "")
        entity_ids = state.get("entity_ids", [])
        raw_output = state.get("raw_output", {})
        language = state.get("language", "it")
        
        # Build context from available data
        context_sections = []
        
        if raw_output and isinstance(raw_output, dict):
            # Extract top-level data summary
            for key, value in raw_output.items():
                if isinstance(value, dict) and "ranking" in str(key).lower():
                    # Summarize ranked results
                    all_items = []
                    for group in value.values() if isinstance(value, dict) else []:
                        if isinstance(group, list):
                            all_items.extend(group)
                    if all_items:
                        # Contract-compliant: Assume results pre-sorted by service (no domain sorting in orchestration)
                        # Services MUST return results ordered by relevance/score
                        top_5 = all_items[:5]  # Take first 5 (pre-sorted)
                        context_sections.append("📊 TOP RESULTS:")
                        for item in top_5:
                            entity = item.get("entity_id", item.get("id", "unknown"))
                            score = item.get("score", item.get("composite_score", 0))
                            context_sections.append(f"• {entity}: Score {score:.1f}")
            
            if not context_sections and raw_output:
                # Generic summary of available data
                context_sections.append(f"📊 DATA AVAILABLE: {', '.join(list(raw_output.keys())[:5])}")
        
        # Add entity focus
        if entity_ids:
            context_sections.append(f"🎯 FOCUS: {', '.join(entity_ids[:5])}")
        
        context_str = "\n".join(context_sections)
        
        if language == "it":
            prompt = f"""CONTESTO ANALISI:\n{context_str}\n\nRICHIESTA UTENTE: {user_input}\n\nFornisci un'analisi dettagliata che integri i dati disponibili con insights qualitativi."""
        else:
            prompt = f"""ANALYSIS CONTEXT:\n{context_str}\n\nUSER REQUEST: {user_input}\n\nProvide detailed analysis integrating available data with qualitative insights."""
        
        return prompt
    
    def _generate_fallback_response(self, state: Dict[str, Any]) -> str:
        """Generate fallback response when LLM fails"""
        
        language = state.get("language", "it")
        
        if language == "it":
            return """Mi dispiace, sto riscontrando difficoltà tecniche temporanee.

Il sistema di analisi è operativo e sta elaborando le informazioni.

Ti consiglio di riprovare tra qualche minuto per un'analisi completa."""
        else:
            return """I apologize, I'm experiencing temporary technical difficulties.

The analysis system is operational and processing information.

Please try again in a few minutes for complete analysis."""


def cached_llm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function with intelligent caching
    Replacement for standard llm_soft_node with token optimization
    """
    
    orchestrator = CachedLLMOrchestrator()
    return orchestrator.process_with_cache(state)


def get_cache_stats_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Optional node to retrieve cache performance statistics"""
    
    cache_manager = get_cache_manager()
    stats = cache_manager.get_cache_statistics(days=7)
    
    state["cache_statistics"] = stats
    return state