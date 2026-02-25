"""
Finance Semantic Plugin — Pattern Weavers v3
=============================================

Implements ISemanticPlugin for the finance/markets domain.
Provides finance-specific:
- LLM system prompt (entity types, intent vocabulary, topic vocabulary)
- Gate keywords for fast-path detection
- Payload validation (ticker normalization, sector verification)

LIVELLO 1 — Pure Python, no I/O.

> **Last updated**: Feb 24, 2026 18:00 UTC

Author: Mercator Finance Vertical
Version: 1.0.0
"""

import logging
from typing import List

try:
    from contracts.pattern_weavers import ISemanticPlugin, OntologyPayload
except ModuleNotFoundError:
    from vitruvyan_core.contracts.pattern_weavers import ISemanticPlugin, OntologyPayload

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Finance System Prompt
# ─────────────────────────────────────────────────────────────

_FINANCE_SYSTEM_PROMPT = """\
You are a financial semantic compiler. Given a user query about \
finance, markets, trading, or investment, extract structured ontology.

Return ONLY valid JSON matching this EXACT schema (no extra fields):
{
  "gate": {
    "verdict": "in_domain" | "out_of_domain" | "ambiguous",
    "domain": "finance",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<brief explanation>"
  },
  "entities": [
    {
      "raw": "<text from query>",
      "canonical": "<resolved form: ticker symbol, index name, etc.>",
      "entity_type": "<see entity types below>",
      "confidence": <float 0.0-1.0>
    }
  ],
  "intent_hint": "<see intent vocabulary below>",
  "topics": ["<topic1>", "<topic2>"],
  "sentiment_hint": "positive" | "negative" | "neutral" | "mixed",
  "temporal_context": "real_time" | "historical" | "forward_looking",
  "language": "<ISO 639-1 code>",
  "complexity": "simple" | "compound" | "multi_intent"
}

ENTITY TYPES (use exactly these):
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
- For company names, resolve to ticker symbol: "Apple" → canonical="AAPL"
- For partial names, use best match: "Tesla" → canonical="TSLA"
- For well-known indices, use standard names: "S&P" → canonical="S&P 500"
- If unsure about a ticker, set confidence < 0.7
- Extract ALL entities even if uncertain

MULTILINGUAL SUPPORT:
Detect and handle queries in English, Italian, Spanish, French, German.
Always identify the query language in the "language" field.
"""


# ─────────────────────────────────────────────────────────────
# Finance Plugin Implementation
# ─────────────────────────────────────────────────────────────

class FinanceSemanticPlugin(ISemanticPlugin):
    """
    Finance domain plugin for Pattern Weavers v3.

    Registered at service startup when PATTERN_DOMAIN=finance.
    """

    _ENTITY_TYPES = [
        "ticker", "sector", "index", "currency", "commodity",
        "crypto", "fund", "region", "indicator", "analyst", "concept",
    ]

    _INTENT_VOCABULARY = [
        "screening", "risk_analysis", "portfolio_review", "valuation",
        "earnings", "technical_analysis", "fundamental_analysis",
        "comparison", "general_info", "news", "unknown",
    ]

    _TOPIC_VOCABULARY = [
        "technology", "healthcare", "energy", "financials",
        "consumer_discretionary", "consumer_staples", "industrials",
        "utilities", "real_estate", "materials", "communications",
        "earnings", "dividends", "ipo", "mergers_acquisitions",
        "regulation", "macro", "crypto", "esg", "fixed_income",
        "forex", "commodities", "options", "derivatives", "etf",
        "mutual_funds",
    ]

    # Gate keywords — high-confidence signals for fast-path
    # If ANY of these appear and embedding confidence > 0.92,
    # we can skip LLM gate and go straight to "in_domain"
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

    def get_domain_name(self) -> str:
        return "finance"

    def get_system_prompt(self) -> str:
        return _FINANCE_SYSTEM_PROMPT

    def get_entity_types(self) -> List[str]:
        return self._ENTITY_TYPES

    def get_gate_keywords(self) -> List[str]:
        return self._GATE_KEYWORDS

    def get_intent_vocabulary(self) -> List[str]:
        return self._INTENT_VOCABULARY

    def get_topic_vocabulary(self) -> List[str]:
        return self._TOPIC_VOCABULARY

    def validate_payload(self, payload: OntologyPayload) -> OntologyPayload:
        """
        Finance-specific validation:
        1. Normalize ticker symbols to uppercase
        2. Warn on unknown entity types
        """
        validated_entities = []
        for entity in payload.entities:
            canonical = entity.canonical

            # Normalize tickers to uppercase
            if entity.entity_type == "ticker" and canonical:
                canonical = canonical.upper().strip()

            # Rebuild entity with normalized canonical
            validated_entities.append(
                entity.model_copy(update={"canonical": canonical})
            )

        return payload.model_copy(update={"entities": validated_entities})


__all__ = ["FinanceSemanticPlugin"]
