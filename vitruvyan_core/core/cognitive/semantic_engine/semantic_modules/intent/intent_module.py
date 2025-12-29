# core/logic/semantic_modules/intent/intent_module.py
"""
⚠️ DEPRECATED: This module will be phased out in favor of GPT-3.5 intent detection.

Timeline: Q1 2026 complete removal after GPT baseline established.
Current role: Fallback layer in 3-tier cascade (GPT → Babel → Regex).

Sacred Orders Architecture:
- Layer 1 (Primary): GPT-3.5 intent_detection_node (95% accuracy, 84 languages)
- Layer 2 (Fallback): Babel Gardens sentiment mapping (91% accuracy)
- Layer 3 (Emergency): Regex patterns (70% accuracy, 4 languages) ← THIS MODULE

Post-deprecation: All intent detection delegated to LLM-first pipeline.
"""
import re
from typing import List, Union

# ------------------ Intent patterns ------------------
INTENT_PATTERNS = {
    "trend": [
        r"\btrend\b", r"how.*(perform|doing)", r"market outlook",
        r"(short|medium|long|breve|medio|lungo)[-\s]?(term|termine).*(trend|view|forecast|performance)",
        # Vague queries (generic analysis request)
        r"^e\s+\w+\?$",  # "E NVDA?"
        r"(come va|how.*going|what about|che ne pensi)",  # "come va?", "what about X?"
        r"(conviene|worth|good investment|buon investimento)",  # "Conviene TSLA?"
        r"(analizza|analyze|analysis)",  # "analizza SHOP"
    ],
    "strategy": [
        r"build.*portfolio", r"\bstrategy\b", r"investment plan", r"create.*allocation",
        r"(help|guide).*(invest|build)"
    ],
    "risk": [
        r"\b(risk|rischio|riesgo)\b", r"\b(volatility|volatilità|volatilidad)\b", 
        r"(safe|safest|sicuro|seguro)", r"low[ -]?risk", r"avoid.*loss",
        r"(protezione|protection|protección)", r"(hedge|copertura|cobertura)"
    ],
    "sentiment": [
        r"\bsentiment\b", r"what.*(people|market).*(think|feel|say)", 
        r"(opinion|opinione|opinión).*(market|mercato)", r"social.*(buzz|trend)",
        r"(cosa|what|qué).*(pensa|think|piensa).*(mercato|market)"
    ],
    "portfolio_review": [
        r"(check|controlla|verifica|review|analizza).*(my|il mio|mi).*(portfolio|portafoglio)",
        r"(portfolio|portafoglio).*(status|stato|check|review|analysis|analisi)",
        r"(dovrei|should I|devo).*(riequilibrare|rebalance)",
        r"(come sta|how.*doing|come va).*(my|il mio)?.*(portfolio|portafoglio)",
        r"(portfolio|portafoglio).*(risk|rischio|performance|rendimento|concentration|concentrazione)"
    ],
    "onboarding": [
        # Help/Support requests (IT/EN/ES)
        r"(aiut|help|support|assist|ayud)",
        # How it works questions
        r"(come|how|cómo).*(funzion|work|use|usa|funciona)",
        # Configuration/Setup
        r"(impost|configur|setup|set up|configurar)",
        # First time user indicators
        r"(first|primo|prima|primero).*(time|volta|vez)",
        r"(new|nuovo|nuov).*(user|utente|usuario)",
        # Tutorial/Guide requests
        r"(guid|tutorial|wizard|walkthrough|manual|guía)",
        # Uncertainty expressions
        r"(non so|don't know|no sé|no idea|unsure).*(come|how|cómo)",
        r"(lost|perso|perdido|confuso|confused)",
        # Start/Begin
        r"(inizi|start|begin|empiez|cominc)",
        # Capability queries
        r"(cosa posso|what can|qué puedo).*(fare|do|hacer)",
        r"(puoi|can you|podrías).*(spieg|explain|explica)",
        # Generic onboarding signals
        r"^(hi|hello|ciao|hola|hey)\s*$",  # Simple greeting
        r"(getting started|per iniziare|empezar)"
    ]
}

FALLBACK_INTENT = "unknown"

# ------------------ Intent classification ------------------
def classify_intents(
    text: str,
    tickers: List[str] = None,
    amount: Union[int, None] = None,
    allow_multiple: bool = False
) -> List[str] | str:
    """
    Classify the user intent.
    If budget + ticker are present → allocate.
    Otherwise fallback to regex patterns.
    """
    text = (text or "").lower()
    tickers = tickers or []

    # Rule: allocation if ticker + budget
    if tickers and amount:
        return "allocate"

    matched = []
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                matched.append(intent)
                break

    if not matched:
        return FALLBACK_INTENT if not allow_multiple else [FALLBACK_INTENT]
    return matched if allow_multiple else matched[0]

# ------------------ Horizon extraction ------------------
def extract_horizon(text: str) -> str:
    text = (text or "").lower()

    # numeric months
    m = re.search(r"(\d+)\s*(months?|m)\b", text)
    if m:
        val = int(m.group(1))
        return "short" if val <= 12 else "medium"

    # numeric years
    y = re.search(r"(\d+)\s*(years?|y|anni|anno)\b", text)
    if y:
        val = int(y.group(1))
        if val <= 1:
            return "short"
        elif 2 <= val <= 5:
            return "medium"
        else:
            return "long"

    # keywords
    if "short term" in text or "1 year" in text:
        return "short"
    elif "medium term" in text or "mid term" in text or "3-5 years" in text:
        return "medium"
    elif "long term" in text or "10 years" in text or "decade" in text:
        return "long"

    return "unspecified"

# ------------------ Standalone test ------------------
if __name__ == "__main__":
    samples = [
        "Investo 5000 euro su AAPL per 2 years",
        "I want to invest 100k in Tesla",
        "Vorrei comprare TSLA senza rischi",
        "What is the long term trend for NVDA?",
        "Help me build a portfolio",
        "What's the sentiment around AI?"
    ]
    for s in samples:
        intent = classify_intents(s, tickers=["AAPL"], amount=5000)
        horizon = extract_horizon(s)
        print(f"🧩 Input: {s}")
        print(f"➡️ Intent: {intent} | Horizon: {horizon}")
        print("---")