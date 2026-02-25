"""
Finance Domain — Entity Resolver Configuration
===============================================

Real ticker resolution logic for the finance vertical.
Ported from vitruvyan upstream ticker_resolver_node.py (Dec 2025).

Resolution cascade:
  A. Shadow trading → force extraction from parse_tickers
  B. validated_tickers from frontend (explicit list → trust it)
  C. parse_node extracted tickers (semantic_engine validated)
  D. Company synonym resolution (multilingual)
  E. Conversational fallback (no tickers found)

Registered via EntityResolverRegistry hook pattern.
Called by entity_resolver_node → EntityResolverRegistry.resolve(state, domain="finance").

Author: Vitruvyan Core Team
Created: February 14, 2026 (stub)
Updated: February 24, 2026 (real ticker resolution logic)
Status: PRODUCTION
"""

import re
import logging
from typing import Any, Dict, List, Optional

from core.orchestration.entity_resolver_registry import (
    EntityResolverDefinition,
    get_entity_resolver_registry,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Multilingual company synonym map
# ---------------------------------------------------------------------------
COMPANY_SYNONYMS: Dict[str, str] = {
    # English — Tech Giants & Popular Stocks
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "facebook": "META",
    "meta": "META",
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "netflix": "NFLX",
    "nvidia": "NVDA",
    "intel": "INTC",
    "amd": "AMD",
    "qualcomm": "QCOM",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "cisco": "CSCO",
    "ibm": "IBM",
    "paypal": "PYPL",
    "square": "SQ",
    "block": "SQ",
    "coinbase": "COIN",
    "uber": "UBER",
    "lyft": "LYFT",
    "airbnb": "ABNB",
    "zoom": "ZM",
    "spotify": "SPOT",
    "snap": "SNAP",
    "snapchat": "SNAP",
    "pinterest": "PINS",
    "reddit": "RDDT",
    "roblox": "RBLX",
    "disney": "DIS",
    "walmart": "WMT",
    "jpmorgan": "JPM",
    "goldman": "GS",
    "visa": "V",
    "mastercard": "MA",
    "cocacola": "KO",
    "coca-cola": "KO",
    "pepsi": "PEP",
    "exxon": "XOM",
    "chevron": "CVX",
    "berkshire": "BRK.B",
    # Italian
    "mela": "AAPL",
    # Japanese (Katakana)
    "アップル": "AAPL",
    "テスラ": "TSLA",
    "マイクロソフト": "MSFT",
    "グーグル": "GOOGL",
    "アマゾン": "AMZN",
    "エヌビディア": "NVDA",
    "ネットフリックス": "NFLX",
    "ソニー": "SONY",
    "トヨタ": "TM",
    "任天堂": "NTDOY",
    # Chinese (Simplified)
    "苹果": "AAPL",
    "特斯拉": "TSLA",
    "微软": "MSFT",
    "谷歌": "GOOGL",
    "亚马逊": "AMZN",
    "英伟达": "NVDA",
    "阿里巴巴": "BABA",
    "腾讯": "TCEHY",
    "百度": "BIDU",
    "京东": "JD",
    # Korean (Hangul)
    "애플": "AAPL",
    "테슬라": "TSLA",
    "구글": "GOOGL",
    "엔비디아": "NVDA",
    "삼성": "SSNLF",
    # Russian (Cyrillic)
    "тесла": "TSLA",
    "гугл": "GOOGL",
    "амазон": "AMZN",
    "нвидиа": "NVDA",
}


# Common false positives to filter out
_COMMON_WORDS = frozenset({
    "AND", "OR", "IT", "ON", "AT", "IN", "TO", "SO", "AS", "IF",
    "BY", "UP", "NO", "GO", "DO", "BE", "WE", "HE", "ME", "MY",
    "THE", "FOR", "ARE", "NOT", "BUT", "ALL", "CAN", "HAD",
    "HER", "WAS", "ONE", "OUR", "OUT",
})


def _resolve_company_synonyms(text: str) -> List[str]:
    """Resolve company names to ticker symbols from text."""
    found: List[str] = []
    txt_lower = text.lower()
    for company, ticker in COMPANY_SYNONYMS.items():
        if company in txt_lower and ticker not in found:
            found.append(ticker)
    return found


def _extract_single_ticker_from_followup(text: str) -> Optional[str]:
    """
    Extract a single ticker from follow-up queries.

    Patterns: "e DPZ?", "and TSLA", "anche GOOGL", "et NVDA"
    """
    pattern = r"\b(?:e|and|anche|also|plus|inoltre|et|und|y)\s+([A-Z]{2,5})\b"
    match = re.search(pattern, text)
    if match:
        candidate = match.group(1).upper()
        if candidate not in _COMMON_WORDS:
            return candidate
    return None


def finance_entity_resolver(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finance-specific entity resolver — real ticker resolution.

    Resolution cascade:
      A. Shadow trading → force extraction from tickers/validated_tickers
      B. validated_tickers from frontend (trust the client)
      C. parse_node extracted tickers (semantic_engine validated)
      D. Company synonym resolution (multilingual fallback)
      E. Conversational fallback (no tickers found)
    """
    input_text = (state.get("input_text") or "").strip()
    # Finance-specific field OR domain-agnostic field (graph_runner sets validated_entities)
    validated_tickers = state.get("validated_tickers") or state.get("validated_entities")
    parse_tickers = state.get("tickers", [])
    intent = state.get("intent", "unknown")

    # ----- CASE A: Shadow Trading — force ticker extraction -----
    if intent in ("shadow_buy", "shadow_sell"):
        extracted = validated_tickers if validated_tickers else parse_tickers
        if extracted:
            logger.info(
                f"[FinanceEntityResolver] Shadow trading: {extracted}"
            )
            state["tickers"] = extracted
            state["entity_ids"] = extracted
            state["validated_tickers"] = extracted
            state["extraction_method"] = "shadow_trading_extraction"
            state["extraction_confidence"] = 0.95
            state["flow"] = "direct"
            return state

        # Try company synonym resolution as last resort
        synonyms = _resolve_company_synonyms(input_text) if input_text else []
        if synonyms:
            logger.info(
                f"[FinanceEntityResolver] Shadow trading synonym: {synonyms}"
            )
            state["tickers"] = synonyms
            state["entity_ids"] = synonyms
            state["validated_tickers"] = synonyms
            state["extraction_method"] = "shadow_trading_synonym"
            state["extraction_confidence"] = 0.8
            state["flow"] = "direct"
            return state

        logger.warning(
            f"[FinanceEntityResolver] Shadow trading: no tickers in '{input_text[:50]}'"
        )
        state["tickers"] = []
        state["entity_ids"] = []
        state["extraction_method"] = "shadow_trading_extraction_failed"
        state["extraction_confidence"] = 0.0
        state["flow"] = "conversational"
        return state

    # ----- CASE B: Frontend validated tickers -----
    # Contract: validated_tickers is not None → trust the client.
    #   Non-empty list → direct analysis.
    #   Empty list []  → user explicitly chose "no entities".
    if validated_tickers is not None:
        if validated_tickers:
            logger.info(
                f"[FinanceEntityResolver] Frontend validated: {validated_tickers}"
            )
            state["tickers"] = validated_tickers
            state["entity_ids"] = validated_tickers
            state["extraction_method"] = "frontend_validated"
            state["extraction_confidence"] = 1.0
            state["flow"] = "direct"
            return state
        else:
            logger.info(
                "[FinanceEntityResolver] Frontend validated empty [] → conversational"
            )
            state["tickers"] = []
            state["entity_ids"] = []
            state["extraction_method"] = "frontend_validated_empty"
            state["extraction_confidence"] = 1.0
            state["flow"] = "conversational"
            return state

    # ----- CASE C: parse_node semantic_engine extraction -----
    if parse_tickers:
        logger.info(
            f"[FinanceEntityResolver] parse_node tickers: {parse_tickers}"
        )
        state["tickers"] = parse_tickers
        state["entity_ids"] = parse_tickers
        state["extraction_method"] = "semantic_engine"
        state["extraction_confidence"] = 1.0
        state["flow"] = "direct"
        return state

    # ----- CASE D: Company synonym resolution -----
    if input_text:
        synonyms = _resolve_company_synonyms(input_text)
        if synonyms:
            logger.info(
                f"[FinanceEntityResolver] Synonym resolution: {synonyms}"
            )
            state["tickers"] = synonyms
            state["entity_ids"] = synonyms
            state["extraction_method"] = "company_synonym"
            state["extraction_confidence"] = 0.85
            state["flow"] = "direct"
            return state

        # Try follow-up pattern ("e DPZ?", "and TSLA")
        followup = _extract_single_ticker_from_followup(input_text)
        if followup:
            logger.info(
                f"[FinanceEntityResolver] Follow-up extraction: {followup}"
            )
            state["tickers"] = [followup]
            state["entity_ids"] = [followup]
            state["extraction_method"] = "followup_extraction"
            state["extraction_confidence"] = 0.7
            state["flow"] = "direct"
            return state

    # ----- CASE E: No tickers → conversational -----
    logger.info(
        f"[FinanceEntityResolver] No tickers → conversational: "
        f"'{input_text[:50]}'"
    )
    state["tickers"] = []
    state["entity_ids"] = []
    state["extraction_method"] = "none"
    state["extraction_confidence"] = 0.0
    state["flow"] = "conversational"
    return state


def register_finance_entity_resolver() -> None:
    """
    Register finance entity resolver with global registry.

    Called automatically by graph_flow.py when ENTITY_DOMAIN=finance.
    """
    registry = get_entity_resolver_registry()

    definition = EntityResolverDefinition(
        domain="finance",
        resolver_fn=finance_entity_resolver,
        description="Resolve ticker symbols / company names to validated entities",
        requires_fields=[],  # Works even without entity_ids
    )

    registry.register(definition)
    logger.info("✅ Finance entity resolver registered (real ticker resolution)")
