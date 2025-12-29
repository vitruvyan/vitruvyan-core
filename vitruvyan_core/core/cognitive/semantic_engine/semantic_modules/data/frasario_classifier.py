# core/logic/semantic_engine/data/frasario_classifier.py
import sys
import json
import re
import random
from typing import Dict

# 🔍 Sentiment semplificato
def classify_sentiment(text: str) -> str:
    text = text.lower()
    if any(word in text for word in ["bull", "rocket", "buy", "mooning", "long"]):
        return "bullish"
    elif any(word in text for word in ["bear", "short", "sell", "crash", "drop"]):
        return "bearish"
    return "neutral"

# 🎭 Tono stimato (versione naive)
def classify_tone(text: str) -> str:
    if "💎" in text or "🚀" in text or "stonks" in text:
        return "ironico"
    elif "considera" in text or "opportunità" in text:
        return "motivazionale"
    elif re.search(r"\bPE\b|\bdividend\b|\bvaluation\b", text, re.IGNORECASE):
        return "tecnico"
    return "neutro"

# 🧠 Contesto stimato (orizzonte temporale)
def classify_context(text: str) -> str:
    text = text.lower()
    if any(word in text for word in ["today", "short term", "questa settimana", "intraday"]):
        return "trend_short"
    elif any(word in text for word in ["next quarter", "medio termine", "3 mesi"]):
        return "trend_medium"
    elif any(word in text for word in ["2025", "long term", "lungo periodo"]):
        return "trend_long"
    elif any(word in text for word in ["inflation", "rate", "federal", "fed", "macro"]):
        return "macro"
    return "generico"

# 📦 Classificatore principale
def classify_phrase_metadata(phrase_obj: Dict) -> Dict:
    text = phrase_obj["text"]
    source = phrase_obj.get("source", "reddit")

    return {
        "text": text,
        "source": source,
        "sentiment": classify_sentiment(text),
        "tone": classify_tone(text),
        "context_type": classify_context(text),
        "timestamp": phrase_obj.get("timestamp")
    }

# ✅ Test standalone
if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            # ogni linea deve essere un JSON {"text": "...", "source": "...", "timestamp": "..."}
            phrase_obj = json.loads(line)
            result = classify_phrase_metadata(phrase_obj)
            print(json.dumps(result, ensure_ascii=False))
        except Exception as e:
            sys.stderr.write(f"[ERROR] Line skipped: {e}\n")