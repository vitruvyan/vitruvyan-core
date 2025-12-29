"""
🧠 Intent Detection Node - PHASE 2.1 Consolidation
=======================================================
Sacred Order: Discourse (Linguistic Processing)
Epistemic Layer: Language → Intent → Screening Filters

CONSOLIDATED FROM:
- babel_node.py (language detection)
- intent_llm_node.py (intent classification + screening filters)
- intent_mapper_node.py (synonym mapping)

OPTIMIZATION:
- Parallel API calls (Babel Gardens + GPT-3.5) via asyncio.gather
- Inline synonym dictionary (no separate node)
- Single responsibility: All linguistic + intent work in one place

STATE INPUTS:
- input_text: str - User query
- user_message: str - Alternative input field

STATE OUTPUTS:
- language_detected: str - Detected language (en, it, ru, sr, etc.)
- language_confidence: float - Detection confidence (0.0-1.0)
- cultural_context: str - Cultural interpretation
- intent: str - Canonical intent (trend, risk, portfolio, sentiment, etc.)
- screening_filters: dict - Extracted filters (risk_tolerance, momentum_breakout, sector, mode)
- route: str - "intent_detection"
"""

import os
import json
import asyncio
import httpx
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from prometheus_client import Counter

# Load environment
load_dotenv()
logger = logging.getLogger(__name__)

# Prometheus metrics
intent_override_counter = Counter(
    'vitruvyan_intent_override_total',
    'Professional boundaries enforced - ambiguous queries rejected'
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Babel Gardens API URL
BABEL_API_URL = os.getenv("SENTIMENT_API_URL", "http://vitruvyan_babel_gardens:8009")

# Intent labels
INTENT_LABELS = [
    "trend", "momentum", "volatility", "risk", "backtest",
    "allocate", "portfolio", "sentiment",
    "soft", "horizon_advice", "unknown"
]

# Synonym mapping (inline, from intent_mapper_node)
INTENT_SYNONYMS = {
    "invest": "allocate",
    "investire": "allocate",
    "comprare": "allocate",
    "buy": "allocate",
    "acquista": "allocate",
    "acquisto": "allocate",
    "portfolio analysis": "portfolio",
    "analizza portafoglio": "portfolio",
}

# GPT-3.5 Prompt Template
INTENT_PROMPT_TEMPLATE = """You are Vitruvyan's intent classification engine. Analyze the user's financial query and extract structured parameters.

INTENT CATEGORIES:
- trend: stock analysis, technical analysis
- risk: risk assessment of specific tickers
- portfolio: portfolio management
- sentiment: market sentiment analysis
- momentum: momentum indicators (RSI, MACD, breakout detection)
- volatility: volatility analysis
- backtest: backtesting strategies
- allocate: asset allocation
- soft: emotional/psychological queries, greetings
- horizon_advice: investment time horizon questions
- unknown: unclear requests

EXTRACT SCREENING FILTERS (if applicable):
- risk_tolerance: "low" (conservative, prudent, stable), "medium" (balanced), "high" (aggressive, growth)
- momentum_breakout: true if user wants strong momentum/breakout stocks (keywords: breakout, momentum forte, explosive, rottura resistenza)
- value_screening: true if user wants undervalued stocks (keywords: sottovalutati, undervalued, cheap, buon prezzo, bargain, economici)
- divergence_detection: true if user wants divergence/contrarian signals (keywords: divergenza, divergence, segnale contrarian, reversal, inversione, price-RSI divergence)
- multi_timeframe_filter: true if user wants multi-timeframe consensus (keywords: consensus multi-timeframe, allineamento timeframe, trend confermato su tutti i timeframe, bullish across timeframes)
- sector: extract sector name if mentioned (Technology, Healthcare, Energy, Financial Services, Consumer Cyclical, Industrials, Real Estate, Basic Materials, Communication Services, Utilities, Consumer Defensive)
- mode: "analyze" (specific tickers), "discovery" (general screening), "comparative" (compare alternatives), "sector" (sector-focused)

EXAMPLES:
"Analizza AAPL" → {{"intent": "trend", "mode": "analyze"}}
"Dammi titoli conservativi a basso rischio" → {{"intent": "risk", "risk_tolerance": "low"}}
"Trova titoli con forte momentum breakout" → {{"intent": "momentum", "momentum_breakout": true}}
"Titoli tech sottovalutati" → {{"intent": "trend", "sector": "Technology", "value_screening": true}}
"Azioni economiche ma solide" → {{"intent": "trend", "value_screening": true, "risk_tolerance": "low"}}
"Cerca divergenze rialziste" → {{"intent": "momentum", "divergence_detection": true}}
"Titoli con trend confermato su tutti i timeframe" → {{"intent": "trend", "multi_timeframe_filter": true}}
"ho paura del mercato" → {{"intent": "soft"}}

Query: "{user_input}"

Return ONLY valid JSON (no markdown):
{{
  "intent": "category",
  "risk_tolerance": "low|medium|high|null",
  "momentum_breakout": true|false,
  "value_screening": true|false,
  "divergence_detection": true|false,
  "multi_timeframe_filter": true|false,
  "sector": "sector_name|null",
  "mode": "analyze|discovery|comparative|sector|null"
}}
"""


async def _call_babel_gardens(input_text: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Call Babel Gardens API for TRUE multilingual language detection (84 languages)
    
    ✅ CORRECT ENDPOINT: /v1/embeddings/multilingual
       - Uses embedding_engine._detect_language() with Unicode range analysis
       - Detects: IT/FR/DE/ES/RU/ZH/AR/JA/KO/HE + 74 more languages
       - Confidence: Unicode-based (0.95), Keyword-based (0.85)
    
    ❌ WRONG ENDPOINT: /v1/sentiment/batch
       - Uses sentiment_fusion._detect_language() with limited keywords
       - Only detects: IT/EN/ES (all others default to "en")
       - Do NOT use for language detection!
    
    Returns:
        Dict with language_detected, language_confidence, cultural_context
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # ✅ Use embeddings/multilingual for TRUE 84-language detection
            response = await client.post(
                f"{BABEL_API_URL}/v1/embeddings/multilingual",
                json={
                    "text": input_text[:200],  # First 200 chars sufficient for detection
                    "language": "auto",
                    "use_cache": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse embeddings endpoint response format
                # {"status": "success", "embedding": [...], "metadata": {"language": "fr", "cached": false}}
                metadata = result.get("metadata", {})
                language = metadata.get("language", "unknown")
                
                # Estimate confidence based on detection method
                # Unicode-based detection (AR/ZH/JA/KO/HE/RU) = 0.95
                # Keyword-based detection (IT/FR/DE/ES) = 0.85
                unicode_langs = {"ar", "zh", "ja", "ko", "he", "ru"}
                confidence = 0.95 if language in unicode_langs else 0.85
                
                logger.info(f"🌍 [INTENT_DETECTION] Babel Gardens: language={language}, confidence={confidence}")
                
                return {
                    "language_detected": language,
                    "language_confidence": confidence,
                    "cultural_context": f"Text analyzed in {language} context",
                    "babel_status": "success"
                }
            else:
                logger.warning(f"⚠️ [INTENT_DETECTION] Babel Gardens HTTP {response.status_code}")
                return _fallback_language_detection(input_text)
                
    except Exception as e:
        logger.error(f"❌ [INTENT_DETECTION] Babel Gardens API failed: {e}")
        # ✅ TRUST ONLY BABEL GARDENS - No langdetect fallback
        # Babel Gardens supports 84+ languages, langdetect only supports limited subset
        # Fallback to langdetect was causing language overwrite bugs (commit 55d20b93)
        return {
            "language_detected": "unknown",
            "language_confidence": 0.0,
            "cultural_context": "",
            "babel_status": "failed",
            "error": f"Babel Gardens unavailable: {str(e)}"
        }


async def _call_gpt_intent(input_text: str, timeout: float = 10.0) -> Dict[str, Any]:
    """
    Call GPT-3.5 for intent classification + screening filters extraction
    
    Returns:
        Dict with intent, screening_filters
    """
    prompt = INTENT_PROMPT_TEMPLATE.format(user_input=input_text)
    
    try:
        # OpenAI client is synchronous, run in executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.0
            )
        )
        
        raw_content = response.choices[0].message.content.strip()
        logger.debug(f"🔍 [INTENT_DETECTION] GPT raw response: {repr(raw_content)}")
        
        # Clean markdown formatting
        if raw_content.startswith("```"):
            lines = raw_content.split('\n')
            if '```' in lines[0]:
                lines = lines[1:]
            if lines and '```' in lines[-1]:
                lines = lines[:-1]
            raw_content = '\n'.join(lines).strip()
        
        # Parse JSON
        parsed = json.loads(raw_content)
        
        # Extract intent
        intent_raw = parsed.get("intent", "unknown").lower()
        intent = intent_raw if intent_raw in INTENT_LABELS else "unknown"
        
        # Apply synonym mapping (inline from intent_mapper_node)
        intent = INTENT_SYNONYMS.get(intent.lower(), intent)
        
        # Extract screening filters
        screening_filters = {}
        
        if parsed.get("risk_tolerance") and parsed["risk_tolerance"] != "null":
            screening_filters["risk_tolerance"] = parsed["risk_tolerance"]
        
        if parsed.get("momentum_breakout") is True:
            screening_filters["momentum_breakout"] = True
        
        if parsed.get("value_screening") is True:
            screening_filters["value_screening"] = True
        
        if parsed.get("divergence_detection") is True:
            screening_filters["divergence_detection"] = True
        
        if parsed.get("multi_timeframe_filter") is True:
            screening_filters["multi_timeframe_filter"] = True
        
        if parsed.get("sector") and parsed["sector"] != "null":
            screening_filters["sector"] = parsed["sector"]
        
        if parsed.get("mode") and parsed["mode"] != "null":
            screening_filters["mode"] = parsed["mode"]
        
        logger.info(f"🔍 [INTENT_DETECTION] GPT: intent={intent}, filters={screening_filters}")
        
        return {
            "intent": intent,
            "screening_filters": screening_filters,
            "intent_status": "success"
        }
        
    except json.JSONDecodeError as je:
        logger.warning(f"⚠️ [INTENT_DETECTION] JSON decode error: {je}")
        # Fallback: extract intent from raw text
        intent_raw = raw_content.lower()
        intent = intent_raw if intent_raw in INTENT_LABELS else "unknown"
        intent = INTENT_SYNONYMS.get(intent, intent)
        
        return {
            "intent": intent,
            "screening_filters": {},
            "intent_status": "fallback_text"
        }
        
    except Exception as e:
        logger.error(f"❌ [INTENT_DETECTION] GPT API error: {e}")
        return {
            "intent": "unknown",
            "screening_filters": {},
            "intent_status": "failed"
        }


async def _parallel_linguistic_processing(input_text: str) -> Dict[str, Any]:
    """
    Execute Babel Gardens + GPT-3.5 calls in parallel via asyncio.gather
    
    Returns:
        Combined dict with language + intent + screening filters
    """
    start_time = datetime.now()
    
    # Parallel execution
    babel_result, intent_result = await asyncio.gather(
        _call_babel_gardens(input_text),
        _call_gpt_intent(input_text),
        return_exceptions=True  # Don't fail if one API fails
    )
    
    # Handle exceptions
    if isinstance(babel_result, Exception):
        logger.error(f"❌ [INTENT_DETECTION] Babel exception: {babel_result}")
        babel_result = _fallback_language_detection(input_text)
    
    if isinstance(intent_result, Exception):
        logger.error(f"❌ [INTENT_DETECTION] GPT exception: {intent_result}")
        intent_result = {"intent": "unknown", "screening_filters": {}, "intent_status": "failed"}
    
    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    logger.info(f"⚡ [INTENT_DETECTION] Parallel processing completed in {duration_ms:.2f}ms")
    
    # Combine results
    return {
        **babel_result,
        **intent_result,
        "processing_duration_ms": duration_ms
    }


def _has_explicit_context(user_input: str, intent: str) -> bool:
    """
    ✅ PROFESSIONAL BOUNDARIES ENFORCEMENT (Oct 30-31, 2025)
    
    Verifica se query ha CONTESTO ESPLICITO per intent rilevato.
    Previene che GPT classifiqui query ambigue come intent validi.
    
    Design Philosophy:
    - Vitruvyan = professional analyst, NOT fortune teller
    - Ambiguous queries → reject with intent='unknown'
    - Clear questions get clear, data-driven answers
    
    Examples:
    - intent=risk + "volatility" in text → True ✅
    - intent=risk + "ho troppo SHOP" → False ❌ (no risk keywords)
    - intent=portfolio_review + "my portfolio" → True ✅
    - intent=portfolio_review + "ho troppo SHOP" → False ❌ (no portfolio keywords)
    - intent=trend + "analizza NVDA" → True ✅ (generic OK for trend)
    - intent=sentiment + "sentiment AAPL" → True ✅
    
    Args:
        user_input: User query text
        intent: GPT-detected intent
    
    Returns:
        True if query has explicit context for intent, False if ambiguous
    
    References:
    - docs/audit/UX_CURRENT_STATE_ANALYSIS_OCT30.md
    - .github/copilot-instructions.md - "Intent Detection & Professional Boundaries"
    - Git commit e8ab866a (27 Oct 2025)
    """
    
    text_lower = user_input.lower()
    
    # Context keywords per intent (multilingual: IT/EN/ES)
    context_keywords = {
        "risk": [
            # Italian
            "volatility", "volatilità", "rischio", "risk", "sicuro", "protezione", 
            "hedge", "copertura", "difesa", "prudente", "conservativo",
            # English
            "safe", "protect", "defensive", "volatility exposure",
            # Spanish
            "riesgo", "seguro", "protección", "volatilidad"
        ],
        "portfolio_review": [
            # Italian
            "portfolio", "portafoglio", "il mio", "mio", "my", "holdings",
            "posizioni", "investimenti", "asset", "allocazione",
            # English
            "my portfolio", "my holdings", "my positions", "my investments",
            # Spanish
            "mi cartera", "mis inversiones", "mi portfolio"
        ],
        "sentiment": [
            # Italian
            "sentiment", "opinione", "opinion", "cosa pensa", "people think",
            "mercato dice", "sentiment", "buzz", "social", "reddit",
            # English
            "what people think", "market sentiment", "public opinion",
            # Spanish
            "sentimiento", "opinión pública", "lo que piensa"
        ],
        "momentum": [
            # Italian
            "momentum", "breakout", "rottura", "resistenza", "esplosivo",
            "forte momentum", "accelerazione", "impulso", "spinta",
            # English
            "strong momentum", "breakout", "explosive", "thrust",
            # Spanish
            "impulso fuerte", "ruptura", "explosivo"
        ],
        "volatility": [
            # Italian
            "volatilità", "volatility", "oscillazione", "instabilità",
            "fluttuazione", "variazione", "swing",
            # English
            "volatile", "swings", "fluctuation", "instability",
            # Spanish
            "volatilidad", "oscilación", "inestabilidad"
        ],
        "allocate": [
            # Italian
            "investire", "comprare", "acquisto", "allocare", "budget",
            "capitale", "somma", "euro", "dollari", "$", "€",
            # English
            "invest", "buy", "allocate", "capital", "budget",
            # Spanish
            "invertir", "comprar", "capital", "presupuesto"
        ],
        # Generic analysis intents = allow without explicit keywords
        "trend": [],          # "analizza NVDA" is valid
        "backtest": [],       # "backtest strategy" is valid
        "soft": [],           # Emotional queries = always allow
        "horizon_advice": [], # Time horizon questions = always allow
        "unknown": []         # Unknown = already rejected
    }
    
    # ✅ CRITICAL FIX (Nov 2, 2025): Check for ambiguous portfolio statements FIRST
    # These are ALWAYS ambiguous regardless of GPT intent classification
    ambiguous_portfolio_patterns = [
        # Italian portfolio statements without explicit analysis request
        r'\b(ho|posseggo|detengo)\s+(troppo|poco|tanto|molto)\s+[A-Z]{1,5}\b',
        # "ho troppo SHOP", "posseggo poco NVDA", "detengo tanto AAPL"
        r'\b(conviene|vale la pena)\s*\??$',  # "conviene?", "vale la pena?"
        r'\b(e|ma|però)\s+[A-Z]{1,5}\s*\??$',  # "e NVDA?", "ma SHOP?"
        # English equivalents
        r'\b(i have|i hold)\s+(too much|too little)\s+[A-Z]{1,5}\b',
        r'\b(is it worth|should i)\s*\??$',
        r'\b(what about|how about)\s+[A-Z]{1,5}\s*\??$',
    ]
    
    import re
    for pattern in ambiguous_portfolio_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.warning(
                f"🚨 [PROFESSIONAL_BOUNDARIES] AMBIGUOUS PORTFOLIO STATEMENT detected: "
                f"'{user_input[:80]}...' (pattern: {pattern})"
            )
            return False  # Force rejection regardless of intent
    
    # Get required keywords for intent
    required_keywords = context_keywords.get(intent, [])
    
    # If no keywords required (e.g., trend, soft), allow
    if not required_keywords:
        return True
    
    # Check if at least ONE required keyword is present
    has_context = any(keyword in text_lower for keyword in required_keywords)
    
    if not has_context:
        logger.warning(
            f"⚠️ [PROFESSIONAL_BOUNDARIES] Query lacks explicit context for intent={intent}: "
            f"'{user_input[:80]}...'"
        )
    
    return has_context


def intent_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🧠 Unified Intent Detection Node - PHASE 2.1 + PHASE 3.5 (Professional Boundaries)
    
    Consolidates:
    - Language detection (Babel Gardens)
    - Intent classification (GPT-3.5)
    - Synonym mapping (inline dictionary)
    - Screening filters extraction
    - ✅ NEW: Professional boundaries validation (Oct 30-31, 2025)
    
    Optimization: Parallel API calls via asyncio.gather
    
    Professional Boundaries Enforcement:
    - GPT intent MUST be validated with _has_explicit_context()
    - Ambiguous queries → override to intent='unknown'
    - Examples:
      ❌ "ho troppo SHOP" → lacks portfolio context → intent='unknown'
      ✅ "controlla il mio portfolio" → explicit context → intent='portfolio_review'
    
    State Updates:
    - language_detected: str
    - language_confidence: float
    - cultural_context: str
    - intent: str (with synonym mapping + validation)
    - screening_filters: dict
    - needs_clarification: bool (if intent overridden to unknown)
    - clarification_reason: str (why query was rejected)
    - route: "intent_detection"
    
    References:
    - .github/copilot-instructions.md - "Intent Detection & Professional Boundaries"
    - docs/audit/UX_CURRENT_STATE_ANALYSIS_OCT30.md
    
    ✅ FIX (Nov 1, 2025): Use asyncio.run() instead of new_event_loop()
       - Was: asyncio.new_event_loop() → ERROR "Cannot run loop while another loop is running"
       - Now: asyncio.run() → Creates new loop correctly in sync context
    """
    
    # Extract input text
    user_input = state.get("user_message", "") or state.get("input_text", "")
    
    if not user_input:
        logger.warning("⚠️ [INTENT_DETECTION] No input text provided")
        return {
            **state,
            "language_detected": "unknown",
            "intent": "unknown",
            "screening_filters": {},
            "route": "intent_detection",
            "error": "No input text provided"
        }
    
    logger.info(f"🧠 [INTENT_DETECTION] Processing: '{user_input[:80]}...'")
    
    # Execute parallel linguistic processing (async → sync via ThreadPoolExecutor)
    try:
        import concurrent.futures
        
        def run_async_in_thread():
            """Run async function in a new thread with its own event loop"""
            return asyncio.run(_parallel_linguistic_processing(user_input))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_in_thread)
            result = future.result(timeout=10.0)  # 10s timeout
    except Exception as e:
        logger.error(f"❌ [INTENT_DETECTION] Parallel processing failed: {e}")
        result = {
            "language_detected": "unknown",
            "language_confidence": 0.0,
            "cultural_context": "",
            "intent": "unknown",
            "screening_filters": {},
            "babel_status": "failed",
            "intent_status": "failed",
            "processing_duration_ms": 0
        }
    
    # ✅ PHASE 3.5: PROFESSIONAL BOUNDARIES VALIDATION (Oct 30-31, 2025)
    # Verify GPT intent has explicit context, override to 'unknown' if ambiguous
    detected_intent = result["intent"]
    
    if detected_intent != "unknown":
        if not _has_explicit_context(user_input, detected_intent):
            logger.info(
                f"🚨 [PROFESSIONAL_BOUNDARIES] GPT classified as '{detected_intent}' "
                f"but lacks explicit context. Overriding to 'unknown'. "
                f"Query: '{user_input[:80]}...'"
            )
            # Override to unknown + set clarification flags
            result["intent"] = "unknown"
            state["needs_clarification"] = True
            state["clarification_reason"] = (
                f"Query ambigua per intent {detected_intent}. "
                f"Specifica cosa vuoi sapere (es: sentiment, trend, rischio, portfolio)"
            )
            
            # Add UX counter for monitoring
            intent_override_counter.inc()
            logger.info(
                f"✅ [PROFESSIONAL_BOUNDARIES] Intent override applied. "
                f"User will receive: 'Riformula la domanda'"
            )
    
    # Update state
    state.update({
        "language_detected": result["language_detected"],
        "language": result["language_detected"],  # Alias for slot check compatibility
        "language_confidence": result.get("language_confidence", 0.0),
        "cultural_context": result.get("cultural_context", ""),
        "intent": result["intent"],
        "screening_filters": result.get("screening_filters", {}),
        "route": "intent_detection",
        "intent_detection_metrics": {
            "processing_duration_ms": result.get("processing_duration_ms", 0),
            "babel_status": result.get("babel_status", "unknown"),
            "intent_status": result.get("intent_status", "unknown"),
            "node_timestamp": datetime.now().isoformat()
        }
    })
    
    logger.info(
        f"✅ [INTENT_DETECTION] Complete: "
        f"lang={state['language_detected']}, "
        f"intent={state['intent']}, "
        f"filters={state.get('screening_filters', {})}, "
        f"duration={result.get('processing_duration_ms', 0):.2f}ms"
    )
    
    return state
