"""
Finance Comprehension Plugin — Babel Gardens v3
================================================

Implements IComprehensionPlugin for the finance/markets domain.
Provides finance-specific:
- Ontology prompt section (entity types, intent vocabulary, gate rules)
- Semantics prompt section (FinBERT-calibrated sentiment, market emotions)
- Gate keywords for fast-path detection
- Signal schemas for Layer 2 contributors (FinBERT, multilingual)
- Payload validation (ticker normalization)

LIVELLO 1 — Pure Python, no I/O.

> **Last updated**: Feb 28, 2026 12:00 UTC

Author: Mercator Finance Vertical
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional

try:
    from contracts.comprehension import (
        IComprehensionPlugin,
        ComprehensionResult,
    )
    from contracts.pattern_weavers import OntologyPayload
except ModuleNotFoundError:
    from vitruvyan_core.contracts.comprehension import (
        IComprehensionPlugin,
        ComprehensionResult,
    )
    from vitruvyan_core.contracts.pattern_weavers import OntologyPayload

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Finance Ontology Prompt Section
# ─────────────────────────────────────────────────────────────

_FINANCE_ONTOLOGY_PROMPT = """\
=== ONTOLOGY SECTION ===
DOMAIN: finance (markets, trading, investment)

Produce the "ontology" JSON object with EXACTLY these fields:
{{
  "gate": {{
    "verdict": "in_domain" | "out_of_domain" | "ambiguous",
    "domain": "finance",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<brief>"
  }},
  "entities": [
    {{"raw": "<original text>", "canonical": "<resolved form>", "entity_type": "<type>", "confidence": <0.0-1.0>}}
  ],
  "intent_hint": "<intent>",
  "topics": ["<topic1>"],
  "sentiment_hint": "positive"|"negative"|"neutral"|"mixed",
  "temporal_context": "real_time"|"historical"|"forward_looking",
  "language": "<ISO 639-1>",
  "complexity": "simple"|"compound"|"multi_intent"
}}

ENTITY TYPES for entity_type field (use exactly these):
- "ticker": Individual stock/equity (e.g., AAPL, TSLA, MSFT)
- "sector": Industry sector (e.g., Technology, Healthcare, Energy)
- "index": Market index (e.g., S&P 500, NASDAQ, FTSE 100)
- "currency": Fiat currency or forex pair (e.g., USD, EUR/USD)
- "commodity": Physical commodity (e.g., Gold, Oil, Natural Gas)
- "crypto": Cryptocurrency (e.g., BTC, ETH)
- "fund": ETF or mutual fund (e.g., SPY, QQQ, ARKK)
- "region": Geographic market region (e.g., US, Europe, Asia)
- "indicator": Technical/fundamental indicator (e.g., RSI, P/E, EPS)
- "analyst": Named analyst or firm
- "concept": Abstract financial concept (e.g., inflation, recession)

INTENT VOCABULARY:
- "screening": Finding/filtering stocks or entities
- "risk_analysis": Assessing risk, volatility, VaR
- "portfolio_review": Analyzing portfolio composition/performance
- "valuation": Fundamental analysis, DCF, P/E
- "earnings": Earnings reports, revenue, EPS
- "technical_analysis": Chart patterns, technical indicators
- "fundamental_analysis": Financials, balance sheet, cash flow
- "comparison": Comparing entities or metrics
- "general_info": General information about a financial topic
- "news": Market news, events, announcements
- "unknown": Cannot determine intent

TOPIC VOCABULARY:
technology, healthcare, energy, financials, consumer_discretionary, \
consumer_staples, industrials, utilities, real_estate, materials, \
communications, earnings, dividends, ipo, mergers_acquisitions, \
regulation, macro, crypto, esg, fixed_income, forex, commodities, \
options, derivatives, etf, mutual_funds

GATE RULES:
- "in_domain": Query clearly about finance, markets, trading, or investment
- "out_of_domain": Query has no financial component whatsoever
- "ambiguous": Query could be financial depending on context

ENTITY RESOLUTION RULES:
- For company names, resolve to ticker symbol: raw="Apple" → canonical="AAPL", entity_type="ticker"
- For partial names, use best match: raw="Tesla" → canonical="TSLA", entity_type="ticker"
- For well-known indices, use standard names: raw="S&P" → canonical="S&P 500", entity_type="index"
- If unsure about a ticker, set confidence < 0.7
- Extract ALL entities even if uncertain
- IMPORTANT: Each entity MUST have exactly these 4 fields: "raw", "canonical", "entity_type", "confidence"

MULTILINGUAL SUPPORT:
Detect and handle queries in English, Italian, Spanish, French, German.
Always identify the query language in the "language" field.
"""


# ─────────────────────────────────────────────────────────────
# Finance Semantics Prompt Section
# ─────────────────────────────────────────────────────────────

_FINANCE_SEMANTICS_PROMPT = """\
=== SEMANTICS SECTION ===
Analyze HOW the text is expressed — sentiment, emotion, and linguistic quality.
Apply FINANCE-SPECIFIC calibration below.

Produce the "semantics" JSON object with EXACTLY these fields:
{{
  "sentiment": {{
    "label": "positive"|"negative"|"neutral"|"mixed",
    "score": <-1.0 to 1.0>,
    "confidence": <0.0-1.0>,
    "magnitude": <0.0-1.0>,
    "aspects": [{{"aspect": "<topic>", "sentiment": "<label>", "score": <-1.0 to 1.0>}}],
    "reasoning": "<brief>"
  }},
  "emotion": {{
    "primary": "<emotion>",
    "secondary": ["<emotion>"],
    "intensity": <0.0-1.0>,
    "confidence": <0.0-1.0>,
    "cultural_context": "<style or neutral>",
    "reasoning": "<brief>"
  }},
  "linguistic": {{
    "text_register": "formal"|"informal"|"technical"|"colloquial"|"neutral",
    "irony_detected": true|false,
    "ambiguity_score": <0.0-1.0>,
    "code_switching": true|false
  }}
}}

FINANCE-SPECIFIC SENTIMENT calibration:
- "positive": bullish, growth, outperform, buy signals, earnings beat
- "negative": bearish, decline, underperform, sell signals, earnings miss
- "neutral": hold, stable, in-line with expectations
- "mixed": conflicting signals (e.g., revenue up but margins declining)

Consider magnitude: a minor correction is low magnitude, a crash is high.
Aspect-level sentiment: extract per-entity or per-topic sentiment when present.
  Example: "AAPL earnings beat expectations but TSLA missed" →
    aspects: [{{"aspect": "AAPL_earnings", "sentiment": "positive", "score": 0.7}},
              {{"aspect": "TSLA_earnings", "sentiment": "negative", "score": -0.6}}]

MARKET EMOTIONS (primary emotion vocabulary):
- "fear": market panic, crash fears, regulatory threat, black swan
- "greed": FOMO, bubble language, euphoria, "to the moon"
- "confidence": institutional trust, strong fundamentals, proven track record
- "uncertainty": mixed signals, pending data, regulatory ambiguity
- "excitement": IPO hype, product launch, breakthrough technology
- "frustration": missed earnings repeatedly, stagnation, failed catalysts
- "anxious": worried about losses, portfolio decline fears
- "neutral": factual reporting, data queries, routine analysis
Cultural context matters: Italian markets use different emotional vocabulary
  than US markets (e.g., "crollo" = crash, "rialzo" = rally).

LINGUISTIC REGISTER:
- "formal": institutional reports, SEC filings, analyst notes
- "technical": quant terminology, Greeks, algorithmic trading language
- "informal": retail investor chat, Reddit/social media style
- "colloquial": casual market talk, slang ("stonks", "diamond hands")
- "neutral": standard financial news
Irony detection is critical in financial social media ("great earnings" said sarcastically).
"""


# ─────────────────────────────────────────────────────────────
# Finance Plugin Implementation
# ─────────────────────────────────────────────────────────────

class FinanceComprehensionPlugin(IComprehensionPlugin):
    """
    Finance domain plugin for Comprehension Engine v3.

    Registered at service startup when BABEL_DOMAIN=finance.
    Provides both ontology structure AND semantics calibration
    for the unified LLM call.
    """

    _ENTITY_TYPES = [
        "ticker", "sector", "index", "currency", "commodity",
        "crypto", "fund", "region", "indicator", "analyst", "concept",
    ]

    _GATE_KEYWORDS = [
        # English
        "stock", "stocks", "share", "shares", "equity", "equities",
        "bond", "bonds", "portfolio", "dividend", "earnings",
        "market", "trading", "investment", "investor",
        "ticker", "IPO", "ETF", "mutual fund",
        "P/E", "EPS", "RSI", "MACD", "volatility",
        "bull", "bear", "long", "short",
        "S&P", "NASDAQ", "Dow Jones", "FTSE",
        # Italian
        "borsa", "azioni", "titolo", "titoli", "portafoglio",
        "dividendo", "mercato", "mercati", "investimento",
        "obbligazione", "obbligazioni", "rendimento",
        # Spanish
        "bolsa", "acciones", "cartera", "inversión",
        "mercado", "dividendo", "bono", "bonos",
    ]

    _SIGNAL_SCHEMAS = {
        "sentiment_valence": {
            "range": [-1.0, 1.0],
            "description": "Market sentiment polarity (FinBERT)",
            "source": "finbert",
        },
        "market_fear_index": {
            "range": [0.0, 1.0],
            "description": "Market stress/uncertainty indicator",
            "source": "finbert",
        },
        "volatility_perception": {
            "range": [0.0, 1.0],
            "description": "Perceived volatility from text",
            "source": "finbert",
        },
    }

    def get_domain_name(self) -> str:
        return "finance"

    def get_ontology_prompt_section(self) -> str:
        return _FINANCE_ONTOLOGY_PROMPT

    def get_semantics_prompt_section(self) -> str:
        return _FINANCE_SEMANTICS_PROMPT

    def get_entity_types(self) -> List[str]:
        return self._ENTITY_TYPES

    def get_gate_keywords(self) -> List[str]:
        return self._GATE_KEYWORDS

    def get_signal_schemas(self) -> Dict[str, Dict]:
        """Return signal schemas for Layer 2 contributors (FinBERT)."""
        return self._SIGNAL_SCHEMAS

    def validate_result(self, result: ComprehensionResult) -> ComprehensionResult:
        """
        Finance-specific validation:
        1. Normalize ticker symbols to uppercase
        2. Ensure domain is set to "finance"
        """
        # Normalize ontology entities
        if result.ontology and result.ontology.entities:
            validated_entities = []
            for entity in result.ontology.entities:
                canonical = entity.canonical
                if entity.entity_type == "ticker" and canonical:
                    canonical = canonical.upper().strip()
                validated_entities.append(
                    entity.model_copy(update={"canonical": canonical})
                )

            result = result.model_copy(
                update={
                    "ontology": result.ontology.model_copy(
                        update={"entities": validated_entities}
                    )
                }
            )

        # Ensure gate domain is finance
        if result.ontology and result.ontology.gate:
            if result.ontology.gate.domain != "finance":
                result = result.model_copy(
                    update={
                        "ontology": result.ontology.model_copy(
                            update={
                                "gate": result.ontology.gate.model_copy(
                                    update={"domain": "finance"}
                                )
                            }
                        )
                    }
                )

        return result


__all__ = ["FinanceComprehensionPlugin"]
