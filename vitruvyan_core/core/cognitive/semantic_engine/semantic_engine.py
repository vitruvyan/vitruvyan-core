# core/logic/semantic_engine.py

import sys
import os
import re
from typing import Dict, Optional

# Assicura import relativi quando eseguito stand-alone
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from semantic_modules.intent.intent_module import classify_intents, extract_horizon
from semantic_modules.entity.entity_module import (
    extract_tickers,
    extract_amount,           # fallback
    extract_sector,
    get_company_names,
)
from semantic_modules.routing.routing_module import decide_strategy
from semantic_modules.formatting.formatting_module import clean_text
from semantic_modules.enrichment.enrichment_module import enrich_entities
from semantic_modules.retrieval.retrieval_module import find_similar_phrases  # ✅

# -------------------------
# Parser importi robusto (STRICT: richiede marker monetario o suffisso k)
# -------------------------
_AMOUNT_RX = re.compile(
    r"""
    (?P<sign>[\+\-])?\s*
    (?P<num>
        \d{1,3}(?:[.\s]\d{3})+      # 5.000 / 5 000
        |\d+(?:[.,]\d+)?            # 5000 o 2,5
    )
    (?:
        \s*(?P<k>[kK])\b              # suffisso k
        |
        \s*(?:€|euro|eur|\$)          # marker monetario
        |
        (?!\s*(mesi|mese|anni|anno|y|years?|months?))   # numero puro (no tempo)
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

def _parse_amount_robust(text: str) -> Optional[int]:
    m = _AMOUNT_RX.search(text or "")
    if not m:
        return None
    raw = m.group("num")
    s = raw.replace(".", "").replace(" ", "").replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    if m.group("k"):
        val *= 1000.0
    if m.group("sign") == "-":
        val = -val
    return int(round(val))

def parse_user_input(text: str, extract_intent: bool = False) -> Dict:
    """
    Parses user input text to extract semantic entities, intent, and enriches the result.
    
    🧠 Sacred Orders Architecture — Perception Layer (Order 1)
    This function feeds the Cognition Layer (LangGraph) with semantic context:
    - Entity extraction (tickers, amounts, horizons) → Features #1, #3, #4
    - Semantic retrieval (Qdrant 34K vectors) → Features #1, #4
    - Enrichment (company names) → Feature #9 (VEE cooperation)
    
    Args:
        text (str): The raw user input string.
        extract_intent (bool): If True, perform regex-based intent classification.
                               If False, delegate to GPT-3.5 intent_detection_node (DEFAULT).
                               ⚠️ DEPRECATED: Regex intent will be removed in Q1 2026.
    
    Returns:
        Dict: A dictionary containing extracted entities, intent (if requested), 
              enrichment, and semantic matches from Qdrant.
    """
    cleaned = clean_text(text)

    # 1) Extract base entities first
    tickers = extract_tickers(cleaned)

    # Amount detection (robust first, then fallback with guards)
    amount_robust = _parse_amount_robust(cleaned)
    if amount_robust is not None:
        amount = amount_robust
    else:
        amount_fallback = extract_amount(cleaned)
        if amount_fallback is not None:
            is_timey = re.search(r"\b\d+\s*(mesi|mese|m|anni|anno|y|years?|months?)\b", cleaned, re.IGNORECASE)
            has_money_marker = re.search(
                r"(€|euro|eur|\$|\d+\s*k\b|\d+k\b|\bmila\b|\bthousand\b)", cleaned, re.IGNORECASE
            )
            amount = None if (is_timey and not has_money_marker) else amount_fallback
        else:
            amount = None

    # 2) Horizon
    horizon = extract_horizon(cleaned)

    # 3) Intent classification (OPTIONAL - delegated to GPT by default)
    if extract_intent:
        intent = classify_intents(cleaned, tickers=tickers, amount=amount)
    else:
        intent = None  # Delegated to intent_detection_node (GPT-3.5)

    # 4) Other fields
    sectors = extract_sector(cleaned)
    companies = get_company_names(tickers)
    route = decide_strategy({"intent": intent}) if intent else None

    # 5) Enrichment
    enriched = enrich_entities({
        "raw_input": text,
        "cleaned_input": cleaned,
        "intent": intent,
        "tickers": tickers,
        "companies": companies,
        "amount": amount,
        "horizon": horizon,
        "sectors": sectors,
        "route": route
    })

    # 6) Semantic retrieval (multilingual)
    try:
        language = "en"
        low = text.lower()
        if low.startswith(("¿", "qué", "por", "cómo", "inversiones", "acciones")):
            language = "es"
        elif any(word in low for word in ["investire", "conviene", "titoli", "azioni", "portafoglio"]):
            language = "it"

        matches = find_similar_phrases(text, language=language, top_k=5)
        enriched["semantic_matches"] = matches
    except Exception as e:
        enriched["semantic_matches"] = []
        print(f"⚠️ Semantic retrieval failed: {e}")

    return enriched

    # 1) Importo: prova parser robusto, poi fallback
    # 1) Importo: prova parser robusto, poi fallback (con guardia solo sul fallback)
    amount_robust = _parse_amount_robust(cleaned)
    if amount_robust is not None:
        amount = amount_robust
    else:
        amount_fallback = extract_amount(cleaned)
        # Applica la guardia anti-tempo SOLO se stiamo usando il fallback
        if amount_fallback is not None:
            is_timey = re.search(r"\b\d+\s*(mesi|mese|m|anni|anno|y)\b", cleaned, re.IGNORECASE)
            has_money_marker = re.search(r"(€|euro|eur|\$|\d+\s*k\b|\d+k\b|\bmila\b|\bthousand\b)", cleaned, re.IGNORECASE)
            amount = None if (is_timey and not has_money_marker) else amount_fallback
        else:
            amount = None

    horizon = extract_horizon(cleaned)
    sectors = extract_sector(cleaned)
    companies = get_company_names(tickers)
    route = decide_strategy({"intent": intent})

    # 2) Enrichment
    enriched = enrich_entities({
        "raw_input": text,
        "cleaned_input": cleaned,
        "intent": intent,
        "tickers": tickers,
        "companies": companies,
        "amount": amount,           # pass iniziale
        "horizon": horizon,
        "sectors": sectors,
        "route": route
    })

    # 3) Retrieval semantico multilingua
    try:
        language = "en"
        low = text.lower()
        if low.startswith(("¿", "qué", "por", "cómo", "inversiones", "acciones")):
            language = "es"
        elif any(word in low for word in ["investire", "conviene", "titoli", "azioni", "portafoglio"]):
            language = "it"

        matches = find_similar_phrases(text, language=language, top_k=5)
        enriched["semantic_matches"] = matches
    except Exception as e:
        enriched["semantic_matches"] = []
        print(f"⚠️ Retrieval semantico fallito: {e}")

    return enriched

# ✅ Test standalone
if __name__ == "__main__":
    sample = "Voglio investire 5.000 € su AAPL (12 mesi), e magari altri 5k su NVDA."
    parsed = parse_user_input(sample)
    print("🎯 Semantic Output:")
    for k, v in parsed.items():
        print(f"{k}: {v}")