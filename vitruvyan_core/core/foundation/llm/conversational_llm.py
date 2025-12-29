# core/llm/conversational_llm.py
"""
🧠 Vitruvyan Conversational LLM

ChatGPT-level conversational intelligence per Vitruvyan AI.
Trasforma output tecnici (VEE, Neural Engine) in narrativa human-friendly.

Features:
- 4 generation methods specializzati
- Prometheus metrics integrate
- Git-versionable prompts
- Cost tracking automatico
- Multi-language support (IT/EN/ES + auto-detection con fallback)

Epistemic Order: DISCOURSE (Linguistic Reasoning)

Language Detection:
- Babel Gardens API chiamato per language detection
- LIMITATION: Babel Gardens attualmente supporta solo IT/EN/ES (keyword-based)
- Fallback: Heuristic IT/EN/ES se Babel non disponibile
- TODO: Integrare langdetect in Babel Gardens per vero supporto 84 lingue

Integration:
- Babel Gardens: Sentiment + basic language detection (IT/EN/ES only)
- GPT-4o-mini: Generazione conversazionale in qualsiasi lingua
- VEE Engine: Technical analysis specialist (z-scores, patterns)

Usage:
    from core.foundation.llm.conversational_llm import ConversationalLLM
    
    llm = ConversationalLLM()
    narrative = llm.generate_vee_narrative(vee_data, user_context, language="auto")
"""

import os
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI
from prometheus_client import Histogram, Counter, Gauge

# Import prompt system
from .prompts import get_base_prompt, get_scenario_prompt, get_combined_prompt

# Babel Gardens API endpoint
BABEL_GARDENS_API = os.getenv("SENTIMENT_API_URL", "http://vitruvyan_babel_gardens:8009")

# ============================================================
# PROMETHEUS METRICS
# ============================================================

llm_latency_seconds = Histogram(
    'vitruvyan_llm_latency_seconds',
    'LLM response latency in seconds',
    buckets=[0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 2.0, 5.0],
    labelnames=['model', 'method', 'language']
)

llm_cost_usd = Counter(
    'vitruvyan_llm_cost_usd_total',
    'Total LLM cost in USD',
    labelnames=['model', 'method']
)

llm_tokens_used = Counter(
    'vitruvyan_llm_tokens_total',
    'Total tokens used',
    labelnames=['model', 'method', 'type']  # type: input, output
)

llm_scenario_usage = Counter(
    'vitruvyan_llm_scenario_total',
    'LLM calls by conversation scenario',
    labelnames=['scenario', 'language']
)

llm_errors_total = Counter(
    'vitruvyan_llm_errors_total',
    'Total LLM errors',
    labelnames=['model', 'method', 'error_type']
)


# ============================================================
# CONVERSATIONAL LLM CLASS
# ============================================================

class ConversationalLLM:
    """
    Vitruvyan Conversational LLM Engine
    
    Transforms technical analysis into human-friendly narratives.
    Uses GPT-4o-mini for cost-effective, fast conversational responses.
    
    Language Support:
    - 84 languages via Babel Gardens automatic detection
    - Fallback to IT/EN/ES if Babel Gardens unavailable
    - Dynamic prompt selection based on detected language
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # OpenAI configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("GRAPH_LLM_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
        # Babel Gardens configuration
        self.babel_api = BABEL_GARDENS_API
        self.babel_timeout = 5.0
        
        # Pricing (GPT-4o-mini as of Oct 2025)
        self.pricing = {
            "gpt-4o-mini": {
                "input": 0.150 / 1_000_000,   # $0.150 per 1M input tokens
                "output": 0.600 / 1_000_000   # $0.600 per 1M output tokens
            }
        }
        
        self.logger.info(f"ConversationalLLM initialized: model={self.model}, babel={self.babel_api}")
    
    # ============================================================
    # BABEL GARDENS LANGUAGE DETECTION
    # ============================================================
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language using Babel Gardens multilingual embeddings endpoint.
        
        Uses /v1/embeddings/multilingual which has proper language detection
        for 84+ languages (Unicode range analysis + keyword matching).
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with language_detected, confidence, cultural_context
            
        Example:
            {"language_detected": "fr", "confidence": 0.95, "cultural_context": "French"}
            
        Note:
            - Uses /v1/embeddings/multilingual NOT /v1/sentiment/batch
            - sentiment/batch only supports IT/EN/ES (keyword matching)
            - embeddings/multilingual supports 84+ languages (Unicode analysis)
        """
        try:
            response = httpx.post(
                f"{self.babel_api}/v1/embeddings/multilingual",
                json={
                    "text": text[:200],  # Only first 200 chars for detection
                    "language": "auto",
                    "use_cache": True
                },
                timeout=self.babel_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    metadata = result.get("metadata", {})
                    language = metadata.get("language", "en")
                    
                    # Estimate confidence based on detection method
                    # Unicode detection = high confidence, keyword = medium
                    confidence = 0.95 if language in ["ar", "zh", "ja", "ko", "he", "ru"] else 0.85
                    
                    self.logger.debug(f"🌍 Babel Gardens multilingual detected: {language} (confidence: {confidence:.2f})")
                    
                    return {
                        "language_detected": language,
                        "confidence": confidence,
                        "cultural_context": self._get_cultural_context(language),
                    "babel_status": "success"
                }
            else:
                self.logger.warning(f"⚠️ Babel Gardens HTTP {response.status_code}, using fallback")
                return self._fallback_language_detection(text)
                
        except Exception as e:
            self.logger.error(f"❌ Babel Gardens failed: {e}, using fallback")
            return self._fallback_language_detection(text)
    
    def _fallback_language_detection(self, text: str) -> Dict[str, Any]:
        """Fallback language detection when Babel Gardens unavailable."""
        # Simple heuristic fallback (detect IT/EN/ES)
        text_lower = text.lower()
        
        # Italian indicators
        if any(word in text_lower for word in ["analizza", "dimmi", "vorrei", "quali", "quanto"]):
            return {
                "language_detected": "it",
                "confidence": 0.7,
                "cultural_context": "Italian (fallback detection)",
                "babel_status": "fallback"
            }
        
        # Spanish indicators
        elif any(word in text_lower for word in ["analiza", "cuál", "quiero", "dime"]):
            return {
                "language_detected": "es",
                "confidence": 0.7,
                "cultural_context": "Spanish (fallback detection)",
                "babel_status": "fallback"
            }
        
        # Default to English
        else:
            return {
                "language_detected": "en",
                "confidence": 0.6,
                "cultural_context": "English (default)",
                "babel_status": "fallback"
            }
    
    def _get_cultural_context(self, language: str) -> str:
        """Get cultural context description for language."""
        contexts = {
            "it": "Italian financial culture (CONSOB-regulated)",
            "en": "English financial culture (SEC/FCA-regulated)",
            "es": "Spanish financial culture (CNMV-regulated)",
            "fr": "French financial culture (AMF-regulated)",
            "de": "German financial culture (BaFin-regulated)",
            "ru": "Russian financial culture (CBR-regulated)",
            "zh": "Chinese financial culture (CSRC-regulated)",
            "ja": "Japanese financial culture (FSA-regulated)",
            "ko": "Korean financial culture (FSC-regulated)",
            "pt": "Portuguese financial culture",
            "ar": "Arabic financial culture",
            "hi": "Hindi financial culture",
            "tr": "Turkish financial culture",
            "pl": "Polish financial culture",
            "nl": "Dutch financial culture",
            "sv": "Swedish financial culture"
        }
        return contexts.get(language, f"{language.upper()} financial culture")
    
    # ============================================================
    # CORE LLM CALL METHOD
    # ============================================================
    
    def _call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        method: str,
        language: str = "it",
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Internal method for OpenAI API calls with metrics tracking.
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            method: Method name for metrics (slot_filling, vee_narrative, etc.)
            language: Language code
            max_tokens: Override default max_tokens
            
        Returns:
            LLM response text
        """
        start_time = datetime.now()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            # Extract response
            content = response.choices[0].message.content.strip()
            
            # Track latency
            latency = (datetime.now() - start_time).total_seconds()
            llm_latency_seconds.labels(
                model=self.model,
                method=method,
                language=language
            ).observe(latency)
            
            # Track tokens
            usage = response.usage
            llm_tokens_used.labels(
                model=self.model,
                method=method,
                type="input"
            ).inc(usage.prompt_tokens)
            
            llm_tokens_used.labels(
                model=self.model,
                method=method,
                type="output"
            ).inc(usage.completion_tokens)
            
            # Track cost
            cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
            llm_cost_usd.labels(
                model=self.model,
                method=method
            ).inc(cost)
            
            self.logger.debug(
                f"LLM call completed: method={method}, tokens={usage.total_tokens}, "
                f"latency={latency:.3f}s, cost=${cost:.5f}"
            )
            
            return content
            
        except Exception as e:
            # Track errors
            llm_errors_total.labels(
                model=self.model,
                method=method,
                error_type=type(e).__name__
            ).inc()
            
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        pricing = self.pricing.get(self.model, self.pricing["gpt-4o-mini"])
        return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
    
    # ============================================================
    # METHOD 1: SLOT FILLING QUESTIONS
    # ============================================================
    
    def generate_slot_filling_question(
        self,
        user_input: str,
        missing_slots: List[str],
        known_context: Dict[str, Any],
        language: str = "auto",
        semantic_matches: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate natural follow-up question for missing slots.
        
        Replaces template-based slot filling with conversational LLM.
        Now includes semantic context from Qdrant vector search (34K phrase embeddings).
        
        Args:
            user_input: Original user query
            missing_slots: List of missing parameters (tickers, horizon, budget)
            known_context: Already collected information
            language: Response language ("auto" for Babel Gardens detection, or specific code)
            semantic_matches: Recent similar discussions from Qdrant (optional contextual boost)
            
        Returns:
            Natural question asking for missing information with contextual suggestions
            
        Example:
            Input: user_input="Voglio investire 10k", missing_slots=["tickers", "horizon"],
                   semantic_matches=[{"text": "NVDA momentum forte", "score": 0.85}]
            Output: "Ottimo! Ho visto discussioni recenti su NVDA con forte momentum.
                     Su quali titoli vorresti investire questi 10k? 
                     E preferisci un orizzonte breve (settimane) o lungo (anni)?"
        """
        # Auto-detect language via Babel Gardens if requested
        if language == "auto":
            lang_info = self.detect_language(user_input)
            language = lang_info["language_detected"]
            self.logger.info(f"🌍 Auto-detected language: {language} (confidence: {lang_info['confidence']:.2f})")
        
        # Track scenario usage
        llm_scenario_usage.labels(
            scenario="slot_filling",
            language=language
        ).inc()
        
        # Build system prompt (fallback to EN if language not in base prompts)
        try:
            system_prompt = get_base_prompt(language)
        except (ValueError, KeyError):
            self.logger.warning(f"⚠️ Language {language} not in base prompts, using English fallback")
            system_prompt = get_base_prompt("en")
        
        # Build contextual suggestions from Qdrant (Feature #1 enhancement)
        context_str = ""
        if semantic_matches and len(semantic_matches) > 0:
            top_matches = semantic_matches[:3]  # Use top 3 most relevant
            context_lines = []
            for m in top_matches:
                text_preview = m.get("text", "")[:80]  # Truncate long texts
                score = m.get("score", 0)
                if score > 0.70:  # Only high-relevance matches
                    context_lines.append(f"- {text_preview}")
            
            if context_lines:
                context_str = f"\n\nContesto recente (discussioni simili):\n" + "\n".join(context_lines)
                self.logger.info(f"🔍 [Slot Filling] Added {len(context_lines)} semantic suggestions")
        
        # Build user prompt
        missing_str = ", ".join(missing_slots)
        known_str = ", ".join([f"{k}={v}" for k, v in known_context.items() if v])
        
        user_prompt = f"""L'utente ha scritto: "{user_input}"{context_str}

Informazioni mancanti: {missing_str}
Informazioni già note: {known_str if known_str else "nessuna"}

Genera UNA domanda naturale che chieda tutte le informazioni mancanti in modo friendly.
Se ci sono discussioni recenti rilevanti, menzionale come suggerimenti contestuali.
NON usare template rigidi.
Includi esempi concreti per aiutare l'utente.
Max 2-3 frasi.
Rispondi nella lingua dell'utente ({language})."""
        
        return self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            method="slot_filling",
            language=language,
            max_tokens=150
        )
    
    # ============================================================
    # METHOD 2: VEE NARRATIVE (TECHNICAL → CONVERSATIONAL)
    # ============================================================
    
    def generate_vee_narrative(
        self,
        vee_data: Dict[str, Any],
        user_context: Dict[str, Any],
        language: str = "auto"
    ) -> str:
        """
        Transform VEE technical analysis into conversational narrative.
        
        This is the core VEE+LLM cooperation method.
        
        Args:
            vee_data: VEE technical output (z-scores, summary, technical, detailed)
            user_context: User query, emotion, preferences
            language: Response language ("auto" for Babel Gardens detection, or specific code)
            
        Returns:
            Human-friendly narrative explaining the analysis
            
        Example:
            VEE Input: {"momentum_z": 1.2, "trend_z": -0.3, "vola_z": -0.5}
            LLM Output: "Ho notato che AAPL ha ottimo momentum (+8% vs mercato) 🚀
                        Il trend è debole, non aspettarti crescita esplosiva.
                        Volatilità bassa, navigazione tranquilla 🚢"
        """
        # Auto-detect language if requested
        user_query = user_context.get("query", "")
        if language == "auto" and user_query:
            lang_info = self.detect_language(user_query)
            language = lang_info["language_detected"]
            self.logger.info(f"🌍 Auto-detected language: {language} (confidence: {lang_info['confidence']:.2f})")
        elif language == "auto":
            language = "en"  # Default if no query available
        
        # Track scenario usage
        llm_scenario_usage.labels(
            scenario="vee_narrative",
            language=language
        ).inc()
        
        # Build system prompt (with fallback to EN)
        try:
            system_prompt = get_combined_prompt("detailed_analysis", language)
        except (ValueError, KeyError):
            self.logger.warning(f"⚠️ Language {language} not in prompts, using English fallback")
            system_prompt = get_combined_prompt("detailed_analysis", "en")
        
        # Build user prompt with VEE data
        emotion = user_context.get("emotion", "neutral")
        
        user_prompt = f"""Analizza questi dati tecnici e trasformali in narrativa conversazionale:

QUERY UTENTE: "{user_query}"
EMOZIONE RILEVATA: {emotion}
LINGUA: {language}

DATI VEE:
{self._format_vee_data(vee_data)}

Genera una spiegazione conversazionale (NON tecnica) che:
1. Usa metafore e analogie
2. Spiega z-scores in linguaggio semplice
3. Evidenzia opportunità E rischi
4. Max 2-3 emoji strategici
5. 4-5 frasi max
6. IMPORTANTE: Rispondi nella lingua rilevata ({language})"""
        
        return self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            method="vee_narrative",
            language=language,
            max_tokens=400
        )
    
    def _format_vee_data(self, vee_data: Dict[str, Any]) -> str:
        """Format VEE data for LLM prompt."""
        lines = []
        
        # Extract key metrics
        if "summary" in vee_data:
            lines.append(f"Summary: {vee_data['summary']}")
        
        if "technical" in vee_data:
            lines.append(f"Technical: {vee_data['technical']}")
        
        # Extract z-scores if available
        for key in ["momentum_z", "trend_z", "vola_z", "sentiment_z"]:
            if key in vee_data:
                lines.append(f"{key}: {vee_data[key]}")
        
        return "\n".join(lines)
    
    # ============================================================
    # METHOD 3: PORTFOLIO REASONING (EXPLAIN WHY)
    # ============================================================
    
    def generate_portfolio_reasoning(
        self,
        portfolio_data: Dict[str, Any],
        analysis: Dict[str, Any],
        action: str,
        language: str = "auto"
    ) -> str:
        """
        Generate persuasive reasoning for portfolio recommendations.
        
        Explains PERCHÉ behind rebalancing, buying, selling decisions.
        
        Args:
            portfolio_data: Current portfolio composition
            analysis: Risk/concentration/performance analysis
            action: Recommended action (rebalance, reduce, increase)
            language: Response language ("auto" for detection, or specific code)
            
        Returns:
            Persuasive explanation of WHY to take action
            
        Example:
            Input: action="reduce_shop", concentration=65%
            Output: "Il tuo portfolio è esposto al 65% su SHOP. Se il titolo 
                    scende del 10%, perdi 6.5% del capitale totale. 
                    Considera di ridurre a 30-40% per dormire sonni tranquilli 💤"
        """
        # Auto-detect language from portfolio context or action description
        if language == "auto":
            # Try to detect from action string or default to user's previous language
            lang_info = self.detect_language(action)
            language = lang_info["language_detected"]
        
        # Track scenario usage
        llm_scenario_usage.labels(
            scenario="portfolio_reasoning",
            language=language
        ).inc()
        
        # Build system prompt (with fallback)
        try:
            system_prompt = get_combined_prompt("portfolio_review", language)
        except (ValueError, KeyError):
            self.logger.warning(f"⚠️ Language {language} not in prompts, using English fallback")
            system_prompt = get_combined_prompt("portfolio_review", "en")
        
        # Build user prompt
        user_prompt = f"""Genera ragionamento persuasivo per questa raccomandazione portfolio:

AZIONE RACCOMANDATA: {action}

DATI PORTFOLIO:
{self._format_portfolio_data(portfolio_data)}

ANALISI:
{self._format_analysis(analysis)}

Spiega PERCHÉ questa azione è importante con:
1. Dati concreti (percentuali, impatti)
2. Scenario examples (cosa succede se...)
3. Tono prudente ma incoraggiante
4. 3-4 frasi max
5. Rispondi in {language}"""
        
        return self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            method="portfolio_reasoning",
            language=language,
            max_tokens=350
        )
    
    def _format_portfolio_data(self, data: Dict[str, Any]) -> str:
        """Format portfolio data for LLM prompt."""
        lines = []
        if "holdings" in data:
            lines.append(f"Holdings: {data['holdings']}")
        if "total_value" in data:
            lines.append(f"Total Value: ${data['total_value']:,.2f}")
        if "concentration" in data:
            lines.append(f"Concentration: {data['concentration']}")
        return "\n".join(lines)
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format analysis for LLM prompt."""
        lines = []
        for key, value in analysis.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    # ============================================================
    # METHOD 4: COMPARISON NARRATIVE (MULTI-TICKER)
    # ============================================================
    
    def generate_comparison_narrative(
        self,
        comparison_matrix: Dict[str, Any],
        language: str = "auto"
    ) -> str:
        """
        Generate comparative narrative for multi-ticker analysis.
        
        Args:
            comparison_matrix: Comparative metrics for 2+ tickers
            language: Response language ("auto" for detection, or specific code)
            
        Returns:
            Comparative narrative highlighting winner and trade-offs
            
        Example:
            Input: SHOP vs PLTR vs COIN comparison
            Output: "PLTR domina per momentum (+2.1 vs +0.8 SHOP). 
                    SHOP vince su stabilità (volatilità -0.4). 
                    COIN troppo volatile per profili prudenti."
        """
        # Auto-detect language from comparison context
        if language == "auto":
            # Use first ticker or default to EN
            tickers = comparison_matrix.get("tickers", [])
            if tickers:
                lang_info = self.detect_language(" ".join(tickers))
                language = lang_info["language_detected"]
            else:
                language = "en"
        
        # Track scenario usage
        llm_scenario_usage.labels(
            scenario="comparison",
            language=language
        ).inc()
        
        # Build system prompt (with fallback)
        try:
            system_prompt = get_combined_prompt("comparison", language)
        except (ValueError, KeyError):
            self.logger.warning(f"⚠️ Language {language} not in prompts, using English fallback")
            system_prompt = get_combined_prompt("comparison", "en")
        
        # Build user prompt
        user_prompt = f"""Genera narrativa comparativa per questi ticker:

COMPARISON MATRIX:
{self._format_comparison_matrix(comparison_matrix)}

Evidenzia:
1. 🏆 Winner complessivo (e perché)
2. Forze/debolezze relative
3. Trade-off chiave
4. 4-5 frasi max
5. Rispondi in {language}"""
        
        return self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            method="comparison_narrative",
            language=language,
            max_tokens=400
        )
    
    def _format_comparison_matrix(self, matrix: Dict[str, Any]) -> str:
        """Format comparison matrix for LLM prompt."""
        lines = []
        
        # Extract tickers
        tickers = matrix.get("tickers", [])
        lines.append(f"Tickers: {', '.join(tickers)}")
        
        # Extract metrics
        if "metrics" in matrix:
            for metric, values in matrix["metrics"].items():
                lines.append(f"{metric}: {values}")
        
        return "\n".join(lines)
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def get_cost_stats(self) -> Dict[str, float]:
        """
        Get cost statistics from Prometheus metrics.
        
        Returns:
            Dict with total_cost_usd and avg_cost_per_call
        """
        # This would require Prometheus query, simplified for now
        return {
            "model": self.model,
            "pricing_input": self.pricing[self.model]["input"] * 1_000_000,
            "pricing_output": self.pricing[self.model]["output"] * 1_000_000
        }
