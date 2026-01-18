# Enhanced LLM Fallback Node - Proposal
# core/langgraph/node/enhanced_llm_node.py

from typing import Dict, Any, List
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class VitruvyanLLMOrchestrator:
    """
    Enhanced LLM orchestrator that makes Vitruvyan conversationally sophisticated
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("GRAPH_LLM_MODEL", "gpt-4o-mini")
        
    def build_advanced_prompt(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """Advanced prompt engineering per conversational excellence"""
        
        lang = state.get("language", "en")
        user_input = state.get("input_text", "")
        intent = state.get("intent", "soft")
        entity_ids = state.get("entity_ids", [])
        
        # Market context (dynamic)
        market_context = self._get_market_context()
        
        # Technical data formatting
        tech_summary = self._format_technical_data(state)
        
        # Emotional intelligence
        emotional_context = self._detect_emotional_context(user_input, lang)
        
        # Domain expertise persona
        persona_prompt = self._build_expert_persona(lang)
        
        system_message = f"""
{persona_prompt}

MARKET CONTEXT (Today: {datetime.now().strftime('%Y-%m-%d')}):
{market_context}

EMOTIONAL CONTEXT:
{emotional_context}

TECHNICAL DATA AVAILABLE:
{tech_summary}

CONVERSATIONAL GUIDELINES:
1. Speak like a seasoned financial advisor with 20+ years experience
2. Use storytelling: connect data to market narratives
3. Acknowledge emotions: "I understand your concern about..."  
4. Vary language: avoid repetitive patterns
5. Contextual insights: relate entity_id performance to sector/market trends
6. Educational tone: explain WHY something happens, not just WHAT
7. Never invent numbers - always ground in provided data
8. Include appropriate disclaimers naturally in conversation

LANGUAGE: Always respond in {lang}
ENTITY_IDS IN FOCUS: {', '.join(entity_ids) if entity_ids else 'General market discussion'}
"""

        user_message = f"""
USER QUERY: {user_input}

Respond as Leonardo, the expert financial advisor of Vitruvyan. 
Make this conversation feel like talking to the best financial advisor they've ever met.
"""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _build_expert_persona(self, lang: str) -> str:
        """Build expert financial advisor persona"""
        personas = {
            "en": """
You are Leonardo, a senior financial advisor with deep market expertise and exceptional communication skills.
Your background: 20+ years analyzing markets, helping clients navigate volatility, former sell-side analyst.
Your style: Empathetic, insightful, educational. You make complex concepts accessible.
Your approach: Data-driven but human-centered. You understand that investing is emotional as much as analytical.
""",
            "it": """
Sei Leonardo, un consulente finanziario senior con profonda competenza di mercato e eccezionali capacità comunicative.
Il tuo background: 20+ anni di analisi dei mercati, aiuti i clienti a navigare la volatilità, ex analista sell-side.
Il tuo stile: Empatico, intuitivo, educativo. Rendi accessibili concetti complessi.
Il tuo approccio: Basato sui dati ma centrato sull'umano. Capisci che investire è emotivo quanto analitico.
""",
            "es": """
Eres Leonardo, un asesor financiero senior con profunda experiencia en mercados y habilidades comunicativas excepcionales.
Tu experiencia: 20+ años analizando mercados, ayudando clientes a navegar volatilidad, ex-analista sell-side.
Tu estilo: Empático, perspicaz, educativo. Haces accesibles conceptos complejos.
Tu enfoque: Basado en datos pero centrado en humanos. Entiendes que invertir es emocional tanto como analítico.
"""
        }
        return personas.get(lang, personas["en"])
    
    def _get_market_context(self) -> str:
        """Dynamic market context - could be enhanced with live data"""
        # For now, static but structured for future enhancement
        return """
- Market Environment: Mixed signals with tech leading, value lagging
- Volatility: Elevated due to geopolitical tensions and rate uncertainty  
- Sentiment: Cautiously optimistic but fragile
- Key Themes: AI revolution, energy transition, demographic shifts
- Risk Factors: Inflation persistence, geopolitical instability
"""
    
    def _detect_emotional_context(self, user_input: str, lang: str) -> str:
        """Detect emotional context in user input"""
        anxiety_keywords = {
            "en": ["worried", "scared", "nervous", "concerned", "afraid", "risk", "lose"],
            "it": ["preoccupato", "paura", "nervoso", "timore", "rischio", "perdere"],
            "es": ["preocupado", "miedo", "nervioso", "temor", "riesgo", "perder"]
        }
        
        confidence_keywords = {
            "en": ["confident", "bullish", "optimistic", "positive", "opportunity"],
            "it": ["fiducioso", "ottimista", "positivo", "opportunità", "rialzista"],
            "es": ["confiado", "optimista", "positivo", "oportunidad", "alcista"]
        }
        
        user_lower = user_input.lower()
        lang_anxiety = anxiety_keywords.get(lang, anxiety_keywords["en"])
        lang_confidence = confidence_keywords.get(lang, confidence_keywords["en"])
        
        if any(word in user_lower for word in lang_anxiety):
            return "User shows signs of anxiety/concern - provide reassurance and education"
        elif any(word in user_lower for word in lang_confidence):  
            return "User shows confidence - provide balanced perspective and risk awareness"
        else:
            return "Neutral emotional context - provide informative, balanced analysis"
    
    def _format_technical_data(self, state: Dict[str, Any]) -> str:
        """Format technical data for LLM context"""
        raw_output = state.get("raw_output", {})
        sentiment = state.get("sentiment", {})
        
        summary = []
        
        if isinstance(raw_output, dict) and "ranking" in raw_output:
            ranking = raw_output["ranking"]
            total_stocks = sum(len(group) for group in ranking.values())
            summary.append(f"Neural Engine analyzed {total_stocks} securities")
            
            # Top performers
            all_stocks = []
            for group in ranking.values():
                all_stocks.extend(group)
            
            if all_stocks:
                top_3 = sorted(all_stocks, key=lambda x: x.get("composite_score", 0), reverse=True)[:3]
                top_entities = [entity["entity_id"] for entity in top_3]
                summary.append(f"Top performers: {', '.join(top_entities)}")
        
        if sentiment:
            sentiment_summary = []
            for entity_id, data in sentiment.items():
                label = data.get("sentiment_label", "NEUTRAL")
                sentiment_summary.append(f"{entity_id}: {label}")
            summary.append(f"Sentiment analysis: {', '.join(sentiment_summary)}")
        
        return "\n".join(summary) if summary else "Limited technical data available"
    
    def generate_response(self, state: Dict[str, Any]) -> str:
        """Generate sophisticated conversational response"""
        try:
            messages = self.build_advanced_prompt(state)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # Higher for more creativity
                max_tokens=600,   # Longer for detailed responses
                presence_penalty=0.1,  # Reduce repetition
                frequency_penalty=0.1   # Encourage variety
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            lang = state.get("language", "en")
            fallback_messages = {
                "en": "I'm experiencing a technical issue but I'm here to help. Could you please rephrase your question?",
                "it": "Sto riscontrando un problema tecnico ma sono qui per aiutarti. Potresti riformulare la domanda?",
                "es": "Estoy experimentando un problema técnico pero estoy aquí para ayudar. ¿Podrías reformular tu pregunta?"
            }
            return fallback_messages.get(lang, fallback_messages["en"])


def enhanced_llm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced LLM node with conversational excellence
    """
    orchestrator = VitruvyanLLMOrchestrator()
    response_text = orchestrator.generate_response(state)
    
    state["result"] = {
        "route": "enhanced_llm",
        "intent": state.get("intent", "conversational"),
        "response_text": response_text,
        "error": None,
        "sophistication_level": "expert"
    }
    
    return state