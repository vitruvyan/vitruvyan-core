# Enhanced LLM Node with Intelligent Caching
# core/langgraph/node/cached_llm_node.py

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import openai
import os
from dotenv import load_dotenv

# Import our cache manager
from core.foundation.llm.cache_manager import get_cache_manager, CacheEntry
# 🆕 Import emotion detection
from core.orchestration.langgraph.node.emotion_detector import detect_emotion, get_emotion_system_prompt_fragment

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
    Enhanced LLM orchestrator with intelligent caching
    Combines the sophisticated prompting from enhanced_llm_node 
    with aggressive token cost optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.cache_manager = get_cache_manager()
        
        # Model configuration
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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
                    self.model, int(best_match.tokens_used * 0.3)  # Estimated tokens for adaptation
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
        elif "recommendation" in intent or "consiglio" in intent:
            return "recommendation"
        elif "portfolio" in intent:
            return "portfolio"
        elif "market" in intent or "mercato" in intent:
            return "market_overview"
        elif "compare" in intent or "confronta" in intent:
            return "comparison"
        else:
            return "general"

    def _analyze_user_emotion(self, user_input: str) -> str:
        """
        Lightweight emotion classifier to pick a tone adaptation.
        Returns: 'anxious'|'excited'|'confused'|'neutral'
        """
        # Backwards-compatible wrapper; prefer using _detect_user_emotion for label+confidence
        label, _ = self._detect_user_emotion(user_input)
        return label

    def _detect_user_emotion(self, user_input: str) -> tuple:
        """
        Detect user emotion with a lightweight heuristic-based classifier.
        Returns (label, confidence) where label in {anxious, excited, confused, neutral}
        and confidence is 0.0-1.0.
        """
        if not user_input:
            return ("neutral", 0.0)

        ui = user_input.lower()

        # multilingual keyword lists (small curated sets)
        anxiety_keywords = ["paura", "preoccup", "anxious", "worried", "scared", "rischio", "perdere", "ansia"]
        excitement_keywords = ["wow", "fantastico", "grande opportunità", "explosive", "moon", "🚀", "entusiast", "eufor", "fantastica"]
        confusion_keywords = ["non capisco", "confus", "come funziona", "spiegami", "cosa significa", "non ho capito"]

        score = {"anxious": 0.0, "excited": 0.0, "confused": 0.0}

        # keyword matching gives base score
        for k in anxiety_keywords:
            if k in ui:
                score["anxious"] += 1.0
        for k in excitement_keywords:
            if k in ui:
                score["excited"] += 1.0
        for k in confusion_keywords:
            if k in ui:
                score["confused"] += 1.0

        # emoji heuristics
        if "🚀" in user_input or "🔥" in user_input:
            score["excited"] += 1.2

        # punctuation/upper heuristics (multiple exclamation marks -> excitement)
        excl = user_input.count("!")
        if excl >= 2:
            score["excited"] += 0.8

        # question-heavy -> possible confusion
        qmarks = user_input.count("?")
        if qmarks >= 1:
            score["confused"] += 0.6

        # length-based heuristic: very short urgent phrases -> anxious
        words = ui.split()
        if len(words) <= 3 and any(w in ui for w in ["aiuto", "help", "preoccupa", "urgent"]):
            score["anxious"] += 0.9

        # Normalize scores to confidences
        max_label = max(score, key=lambda k: score[k])
        max_score = score[max_label]

        # If all zeros -> neutral
        if max_score == 0:
            return ("neutral", 0.0)

        # rough confidence scaling: sigmoid-ish mapping
        # map max_score (0.5..inf) to 0.3..0.95
        conf = min(0.95, 0.3 + (max_score / (1.0 + max_score)) * 0.8)
        return (max_label, round(conf, 2))

    def _get_emotion_adaptation(self, language: str, emotion: str) -> str:
        """
        Return a short adaptation string to append to the system prompt
        according to detected emotion and language.
        """
        adaptations = {
            "it": {
                "anxious": "🛡️ TONO ADATTIVO: RASSICURANTE\nL'utente sembra preoccupato. Riconosci le preoccupazioni prima di dare consigli. Usa frasi come 'È normale avere dubbi su...' e enfatizza risk management.",
                "excited": "⚖️ TONO ADATTIVO: CAUTO ED EDUCATIVO\nL'utente sembra entusiasta. Celebra l'entusiasmo ma bilancia con realismo; suggerisci sizing prudente.",
                "confused": "📚 TONO ADATTIVO: DIDATTICO E SEMPLIFICANTE\nL'utente sembra confuso. Scomponi concetti complessi, usa analogie e offri spiegazioni semplici.",
                "neutral": ""
            },
            "en": {
                "anxious": "🛡️ ADAPTIVE TONE: REASSURING\nUser seems worried. Acknowledge concerns before advice. Use phrases like 'It's normal to have doubts...' and emphasize risk management.",
                "excited": "⚖️ ADAPTIVE TONE: CAUTIOUS & EDUCATIONAL\nUser seems excited. Celebrate but add realism; suggest prudent position sizing.",
                "confused": "📚 ADAPTIVE TONE: DIDACTIC & SIMPLIFYING\nUser seems confused. Break concepts into simple steps and offer analogies.",
                "neutral": ""
            }
        }
        return adaptations.get(language, adaptations["en"]).get(emotion, "")
    
    def _adapt_similar_response(self, cached_response: str, current_state: Dict[str, Any]) -> str:
        """
        Adapt a similar cached response to current context
        Light adaptation to save tokens while maintaining relevance
        """
        
        # Extract key differences
        current_tickers = current_state.get("tickers", [])
        current_input = current_state.get("input_text", "")
        language = current_state.get("language", "it")
        
        # Simple adaptation prompts (very short to minimize token usage)
        adaptation_prompts = {
            "it": "Adatta questa analisi per {tickers}: {response}",
            "en": "Adapt this analysis for {tickers}: {response}"
        }
        
        # If tickers are different, add a brief adaptation note
        if current_tickers:
            ticker_str = ", ".join(current_tickers[:3])  # Limit to 3 tickers
            
            if language == "it":
                adaptation_note = f"\n\n*Analisi adattata per: {ticker_str}*"
            else:
                adaptation_note = f"\n\n*Analysis adapted for: {ticker_str}*"
            
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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract response and token usage
            llm_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fresh LLM response: {tokens_used} tokens, {processing_time:.2f}s")
            
            # Cache the response
            self.cache_manager.cache_response(
                cache_key, llm_response, state, 
                self.model, tokens_used
            )
            
            # Update state
            state["llm_response"] = llm_response
            state["cache_info"] = {
                "cache_hit": False,
                "tokens_used": tokens_used,
                "processing_time": processing_time,
                "model": self.model
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
                "detailed_analysis": """Sei Vitruvyan, un consulente finanziario AI di livello istituzionale.

PERSONA: Analista senior con 15+ anni di esperienza, specializzato in analisi quantitativa e spiegazioni chiare.

STILE COMUNICATIVO:
- Tono professionale ma accessibile
- Combina dati tecnici con narrativa coinvolgente  
- Usa metafore e analogie per concetti complessi
- Evidenzia sempre i rischi insieme alle opportunità

STRUTTURA RISPOSTA:
1. Sintesi esecutiva (2-3 frasi chiave)
2. Analisi tecnica dettagliata
3. Implicazioni e raccomandazioni
4. Avvertenze e limitazioni

ELEMENTI DISTINTIVI:
- Usa termini tecnici spiegati in modo semplice
- Fornisci sempre il "perché" dietro ogni conclusione
- Integra fattori macro e micro
- Mantieni obiettività assoluta""",

                "recommendation": """Sei Vitruvyan, consulente finanziario che trasforma dati in consigli azionabili.

OBIETTIVO: Fornire raccomandazioni chiare e motivate.

APPROCCIO:
- Analizza rischio/rendimento atteso
- Contestualizza nel portafoglio complessivo
- Suggerisci timing e sizing delle posizioni
- Evidenzia catalizzatori positivi/negativi

FORMATO:
✅ RACCOMANDAZIONE: [BUY/HOLD/SELL con conviction level]
📊 RAZIONALE: [Punti chiave dell'analisi]
⚠️ RISCHI: [Principali downside]
📈 TARGET: [Obiettivi di prezzo/timeframe]""",

                "market_overview": """Sei Vitruvyan, esperto di macroeconomia e dinamiche di mercato.

FOCUS: Quadro generale dei mercati con insight actionable.

ELEMENTI:
- Sentiment generale e driver principali
- Rotazioni settoriali e tematiche emergenti  
- Impatti geopolitici e macro
- Implicazioni per asset allocation

TONE: Narrator esperto che connette i punti tra eventi apparentemente scollegati."""
            },
            
            "en": {
                "detailed_analysis": """You are Vitruvyan, an institutional-grade AI financial advisor.

PERSONA: Senior analyst with 15+ years experience, specialized in quantitative analysis and clear explanations.

COMMUNICATION STYLE:
- Professional yet accessible tone
- Combine technical data with engaging narrative
- Use metaphors and analogies for complex concepts  
- Always highlight risks alongside opportunities

RESPONSE STRUCTURE:
1. Executive summary (2-3 key sentences)
2. Detailed technical analysis
3. Implications and recommendations
4. Caveats and limitations

DISTINCTIVE ELEMENTS:
- Use technical terms explained simply
- Always provide the "why" behind conclusions
- Integrate macro and micro factors
- Maintain absolute objectivity"""
            }
        }
        
        base = base_prompts.get(language, base_prompts["en"]).get(prompt_type, base_prompts[language]["detailed_analysis"])

        # 🆕 Emotion-adaptive prompt injection with new emotion_detector
        user_input = state.get("input_text", "") if state is not None else ""
        
        # 🎭 Phase 2.1: Prioritize Babel Gardens emotion over legacy detection
        if state.get("emotion_detected") is not None and state.get("emotion_confidence") is not None:
            # Use emotion from babel_emotion_node (already in state)
            emotion = state.get("emotion_detected")
            emotion_conf = state.get("emotion_confidence")
            print(f"🎭 [cached_llm] Using Babel Gardens emotion: {emotion} (confidence: {emotion_conf:.2f})")
        else:
            # Fallback to legacy detection if Babel didn't provide emotion
            # Get Babel Gardens sentiment if available
            babel_sentiment = None
            if state.get("sentiment_label"):
                babel_sentiment = {
                    "sentiment_label": state.get("sentiment_label"),
                    "sentiment_score": state.get("sentiment_score")
                }
            
            # Detect emotion using legacy sophisticated system
            emotion, emotion_conf = detect_emotion(user_input, language, babel_sentiment)
            print(f"🎭 [cached_llm] Detected emotion (legacy): {emotion} (confidence: {emotion_conf:.2f})")
        
        # Get emotion-specific system prompt fragment
        emotion_fragment = get_emotion_system_prompt_fragment(emotion, language)

        # Compose final prompt: personality + emotion adaptation + base prompt
        final_prompt = VITRUVYAN_PERSONALITY_PROMPT + "\n\n"
        
        if emotion_fragment:
            final_prompt += emotion_fragment + "\n\n"
        
        final_prompt += base

        return final_prompt
    
    def _build_user_prompt(self, state: Dict[str, Any], prompt_type: str) -> str:
        """Build context-rich user prompt"""
        
        user_input = state.get("input_text", "")
        tickers = state.get("tickers", [])
        raw_output = state.get("raw_output", {})
        language = state.get("language", "it")
        
        # Build context from technical data
        context_sections = []
        
        if raw_output and "ranking" in raw_output:
            ranking = raw_output["ranking"]
            
            # Top performers
            all_stocks = []
            for group in ranking.values():
                all_stocks.extend(group)
            
            top_5 = sorted(all_stocks, key=lambda x: x.get("composite_score", 0), reverse=True)[:5]
            
            if language == "it":
                context_sections.append("📊 TOP PERFORMERS:")
                for stock in top_5:
                    score = stock.get("composite_score", 0)
                    momentum = stock.get("momentum_score", 0)
                    risk = stock.get("risk_score", 0)
                    context_sections.append(f"• {stock['ticker']}: Score {score:.1f} (Momentum: {momentum:.1f}, Risk: {risk:.1f})")
            else:
                context_sections.append("📊 TOP PERFORMERS:")
                for stock in top_5:
                    score = stock.get("composite_score", 0)
                    momentum = stock.get("momentum_score", 0)
                    risk = stock.get("risk_score", 0)
                    context_sections.append(f"• {stock['ticker']}: Score {score:.1f} (Momentum: {momentum:.1f}, Risk: {risk:.1f})")
        
        # Add user context
        if tickers:
            ticker_context = f"🎯 FOCUS TICKERS: {', '.join(tickers[:5])}"
            context_sections.append(ticker_context)
        
        # Combine all context
        context_str = "\n".join(context_sections)
        
        if language == "it":
            prompt = f"""CONTESTO ANALISI:
{context_str}

RICHIESTA UTENTE: {user_input}

Fornisci un'analisi dettagliata che integri i dati quantitativi con insights qualitativi. 
Spiega il ragionamento passo dopo passo e contestualizza nel panorama di mercato attuale."""
        else:
            prompt = f"""ANALYSIS CONTEXT:
{context_str}

USER REQUEST: {user_input}

Provide detailed analysis integrating quantitative data with qualitative insights.
Explain reasoning step by step and contextualize in current market landscape."""
        
        return prompt
    
    def _generate_fallback_response(self, state: Dict[str, Any]) -> str:
        """Generate fallback response when LLM fails"""
        
        language = state.get("language", "it")
        
        if language == "it":
            return """Mi dispiace, sto riscontrando difficoltà tecniche temporanee. 

Basandomi sui dati disponibili, posso confermare che il sistema di analisi è operativo e sta elaborando le informazioni di mercato.

Ti consiglio di riprovare tra qualche minuto per un'analisi completa, oppure puoi consultare i dati numerici nel pannello sottostante."""
        else:
            return """I apologize, I'm experiencing temporary technical difficulties.

Based on available data, I can confirm the analysis system is operational and processing market information.

Please try again in a few minutes for complete analysis, or you can review the numerical data in the panel below."""


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