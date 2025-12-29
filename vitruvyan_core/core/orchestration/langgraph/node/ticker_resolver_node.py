# core/langgraph/node/ticker_resolver_node.py
# 🚀 NUCLEAR OPTION: LLM-First Ticker Extraction (Nov 1, 2025)

from typing import Dict, Any, List
from core.foundation.persistence.postgres_agent import get_active_tickers, PostgresAgent
from core.orchestration.langgraph.utilities.llm_ticker_extractor import extract_tickers_with_cache
import re
import logging

logger = logging.getLogger(__name__)


COMPANY_SYNONYMS = {
    # 🇺🇸 English - Tech Giants & Popular Stocks (30 entries)
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
    "slack": "WORK",
    "spotify": "SPOT",
    "twitter": "TWTR",
    "snap": "SNAP",
    "snapchat": "SNAP",
    "pinterest": "PINS",
    "reddit": "RDDT",
    "roblox": "RBLX",
    "unity": "U",
    
    # 🇯🇵 Japanese (Katakana) - 25 entries
    "アップル": "AAPL",
    "テスラ": "TSLA",
    "マイクロソフト": "MSFT",
    "グーグル": "GOOGL",
    "アマゾン": "AMZN",
    "フェイスブック": "META",
    "メタ": "META",
    "エヌビディア": "NVDA",
    "ネットフリックス": "NFLX",
    "インテル": "INTC",
    "アドビ": "ADBE",
    "オラクル": "ORCL",
    "シスコ": "CSCO",
    "ペイパル": "PYPL",
    "ウーバー": "UBER",
    "エアビーアンドビー": "ABNB",
    "ズーム": "ZM",
    "スポティファイ": "SPOT",
    "コインベース": "COIN",
    "ソニー": "SONY",
    "トヨタ": "TM",
    "ホンダ": "HMC",
    "任天堂": "NTDOY",
    "ソフトバンク": "SFTBY",
    "パナソニック": "PCRFY",
    
    # 🇨🇳 Chinese (Simplified) - 25 entries
    "苹果": "AAPL",
    "特斯拉": "TSLA",
    "微软": "MSFT",
    "谷歌": "GOOGL",
    "亚马逊": "AMZN",
    "脸书": "META",
    "英伟达": "NVDA",
    "网飞": "NFLX",
    "奈飞": "NFLX",
    "英特尔": "INTC",
    "思科": "CSCO",
    "甲骨文": "ORCL",
    "贝宝": "PYPL",
    "优步": "UBER",
    "爱彼迎": "ABNB",
    "缩放": "ZM",
    "推特": "TWTR",
    "币安": "COIN",
    "阿里巴巴": "BABA",
    "腾讯": "TCEHY",
    "百度": "BIDU",
    "京东": "JD",
    "拼多多": "PDD",
    "美团": "MEITUAN",
    "小米": "XIACY",
    
    # �� Korean (Hangul) - 20 entries
    "애플": "AAPL",
    "테슬라": "TSLA",
    "마이크로소프트": "MSFT",
    "구글": "GOOGL",
    "아마존": "AMZN",
    "엔비디아": "NVDA",
    "넷플릭스": "NFLX",
    "메타": "META",
    "페이스북": "META",
    "인텔": "INTC",
    "시스코": "CSCO",
    "페이팔": "PYPL",
    "우버": "UBER",
    "에어비앤비": "ABNB",
    "줌": "ZM",
    "스포티파이": "SPOT",
    "삼성": "SSNLF",
    "현대": "HYMTF",
    "기아": "KIMTF",
    "엘지": "LPL",
    
    # 🇷🇺 Russian (Cyrillic) - 20 entries
    "яблоко": "AAPL",
    "тесла": "TSLA",
    "майкрософт": "MSFT",
    "гугл": "GOOGL",
    "амазон": "AMZN",
    "нвидиа": "NVDA",
    "нетфликс": "NFLX",
    "мета": "META",
    "фейсбук": "META",
    "интел": "INTC",
    "циско": "CSCO",
    "пейпал": "PYPL",
    "убер": "UBER",
    "эйрбнб": "ABNB",
    "зум": "ZM",
    "спотифай": "SPOT",
    "твиттер": "TWTR",
    "оракл": "ORCL",
    "адобе": "ADBE",
    "ибм": "IBM",
    
    # �� German - 15 entries
    "apfel": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    "amazon": "AMZN",
    "alphabet": "GOOGL",
    "meta": "META",
    "intel": "INTC",
    "oracle": "ORCL",
    "cisco": "CSCO",
    "paypal": "PYPL",
    "uber": "UBER",
    "airbnb": "ABNB",
    "spotify": "SPOT",
    
    # 🇫🇷 French - 10 entries
    "pomme": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "netflix": "NFLX",
    "nvidia": "NVDA",
    "meta": "META",
    "uber": "UBER",
    "spotify": "SPOT",
    
    # 🇪🇸 Spanish - 10 entries
    "manzana": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "netflix": "NFLX",
    "nvidia": "NVDA",
    "meta": "META",
    "uber": "UBER",
    "spotify": "SPOT",
    
    # 🇮🇹 Italian - 10 entries
    "mela": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "netflix": "NFLX",
    "nvidia": "NVDA",
    "meta": "META",
    "uber": "UBER",
    "spotify": "SPOT",
}

def _extract_tokens(text: str) -> List[str]:
    """Extract tokens from text, supporting international characters"""
    tokens = []
    # Split by whitespace and common punctuation
    words = re.split(r'[\s,;.!?]+', text)
    for word in words:
        clean = word.strip()
        # Accept both ASCII and Unicode letters (for CJK, Cyrillic, etc.)
        if clean and len(clean) <= 20:  # Increased from 10 for CJK characters
            tokens.append(clean.upper())
    return tokens

def ticker_resolver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌐 DOMAIN_NEUTRAL: Entity Resolution Node
    
    [PHASE 1D - NOT_IMPLEMENTED]
    This node would resolve domain entities (e.g., tickers → stocks, SKUs → products, patient_ids → patients).
    Finance-specific logic has been stripped. Domain plugins will implement actual resolution.
    
    Original architecture preserved:
    - Semantic grounding integration point maintained
    - Context merging logic structure intact
    - Intent defaulting flow preserved
    
    For domain implementation, see: vitruvyan_core/domains/base_domain.py
    """
    input_text = (state.get("input_text") or "").strip()
    if not input_text:
        return state
    
    logger.info(f"🌐 [entity_resolver] DOMAIN_NEUTRAL / NOT_IMPLEMENTED - input: '{input_text[:50]}'")
    
    # PRESERVED STRUCTURE: Semantic matches integration point
    semantic_matches = state.get("semantic_matches", [])
    logger.info(
        f"🌐 [entity_resolver] Semantic context available: {len(semantic_matches)} matches "
        f"(domain plugin would use these for entity resolution)"
    )
    
    # PRESERVED STRUCTURE: Context entity merging point
    context_entities = state.get("context_tickers", []) or []  # Field name preserved for compatibility
    
    # DOMAIN_NEUTRAL PASSTHROUGH: No actual entity extraction
    # Domain plugin would implement: domain.resolve_entities(input_text, semantic_matches)
    state["tickers"] = context_entities  # Pass through context entities unchanged
    
    logger.info(
        f"🌐 [entity_resolver] PASSTHROUGH: entities={state.get('tickers', [])} "
        f"(domain plugin required for actual resolution)"
    )
    
    # PRESERVED STRUCTURE: Intent defaulting logic
    if state.get("tickers") and state.get("intent") in (None, "unknown"):
        if not state.get("needs_clarification", False):
            state["intent"] = "trend"  # Generic analysis intent
            logger.info(f"🌐 [entity_resolver] Defaulted intent='trend' (entities present)")
        else:
            logger.info(
                f"🌐 [entity_resolver] Keeping intent='unknown' (clarification needed: "
                f"{state.get('clarification_reason', 'N/A')})"
            )

    state["route"] = "entity_resolver"
    return state
