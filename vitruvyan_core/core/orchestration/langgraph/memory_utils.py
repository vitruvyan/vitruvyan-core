from typing import Dict, Any, List
import re

# --- Definition of fundamental slots ---
SLOTS = ["budget", "tickers", "horizon", "language"]

def merge_slots(state: dict, res: dict) -> dict:
    """
    Merge known slots (budget, tickers, horizon, language) 
    between current state, dispatcher output, and user input parsing.
    """
    merged = dict(state)  # copy current state
    text = (state.get("input_text") or "").upper()

    # --- Budget ---
    budget = res.get("budget") or state.get("budget")
    if not budget:
        import re
        m = re.search(r"(\d{3,})\s*(EUR|EURO|\$)?", text)
        if m:
            try:
                budget = int(m.group(1))
            except Exception:
                budget = None
    if budget:
        merged["budget"] = budget

    # --- Tickers ---
    # 🎯 NUCLEAR OPTION: Don't merge tickers - ticker_resolver_node will set them
    # tickers = res.get("tickers") or state.get("tickers")
    # if tickers:
    #     merged["tickers"] = tickers
    # ✅ NEW: Store context tickers separately for ticker_resolver fallback
    context_tickers = state.get("tickers") or res.get("tickers")
    if context_tickers:
        merged["context_tickers"] = context_tickers

    # --- Horizon ---
    horizon = res.get("horizon") or state.get("horizon")
    if horizon:
        merged["horizon"] = horizon

    # --- Language ---
    # ✅ Trust Babel Gardens completely - use language_detected as source of truth
    # Babel Gardens (Gemma) supports 100+ languages, unlike old langdetect (only it/es/en)
    language = state.get("language") or state.get("language_detected") or res.get("language") or "en"
    merged["language"] = language

    return merged

def check_slots(state: Dict[str, Any]) -> List[str]:
    """
    Check which fundamental slots are missing.
    Special handling: tickers must be non-empty list to be considered present.
    """
    missing = []
    for slot in SLOTS:
        value = state.get(slot)
        # Special case: tickers must be a non-empty list
        if slot == "tickers":
            if not value or (isinstance(value, list) and len(value) == 0):
                missing.append(slot)
        # Other slots: just check truthiness
        elif not value:
            missing.append(slot)
    return missing


def is_complete(state: Dict[str, Any]) -> bool:
    """Return True if all fundamental slots are present."""
    return len(check_slots(state)) == 0
