from typing import Dict, Any, List
import re

# --- Definition of fundamental slots ---
SLOTS = ["budget", "entity_ids", "horizon", "language"]

def merge_slots(state: dict, res: dict) -> dict:
    """
    Merge known slots (budget, entity_ids, horizon, language) 
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

    # --- EntityIds ---
    # 🎯 NUCLEAR OPTION: Don't merge entity_ids - entity_resolver_node will set them
    # entity_ids = res.get("entity_ids") or state.get("entity_ids")
    # if entity_ids:
    #     merged["entity_ids"] = entity_ids
    # ✅ NEW: Store context entity_ids separately for entity_resolver fallback
    context_entities = state.get("entity_ids") or res.get("entity_ids")
    if context_entities:
        merged["context_entities"] = context_entities

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
    Special handling: entity_ids must be non-empty list to be considered present.
    """
    missing = []
    for slot in SLOTS:
        value = state.get(slot)
        # Special case: entity_ids must be a non-empty list
        if slot == "entity_ids":
            if not value or (isinstance(value, list) and len(value) == 0):
                missing.append(slot)
        # Other slots: just check truthiness
        elif not value:
            missing.append(slot)
    return missing


def is_complete(state: Dict[str, Any]) -> bool:
    """Return True if all fundamental slots are present."""
    return len(check_slots(state)) == 0
