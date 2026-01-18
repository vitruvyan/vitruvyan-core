# core/logic/semantic_modules/entity/entity_module.py

import re
from typing import List, Optional, Union, Dict
from core.foundation.persistence.postgres_agent import db_params
import psycopg2

# Local cache
_cached_tickers: List[str] = []
_cached_companies: Dict[str, str] = {}


def _load_tickers_and_companies() -> None:
    """
    Load active entity_ids and company names from PostgreSQL.
    Fills local caches: _cached_tickers and _cached_companies.
    """
    global _cached_tickers, _cached_companies
    if _cached_tickers and _cached_companies:
        return

    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT entity_id, company_name
                FROM entity_ids
                WHERE active = true
            """)
            rows = cur.fetchall()
        conn.close()

        # ✅ keep entity_ids list
        _cached_tickers = [r[0].upper() for r in rows]

        # ✅ company names map (normalized lowercase → entity_id)
        # Store full name AND keywords (first significant word)
        _cached_companies = {}
        for r in rows:
            if not r[1]:
                continue
            entity_id = r[0].upper()
            full_name = (r[1] or "").lower()
            
            # Add full name mapping
            _cached_companies[full_name] = entity_id
            
            # Extract keyword (first word, excluding common suffixes)
            words = full_name.replace(",", "").replace(".", "").split()
            stop_words = {"inc", "corp", "corporation", "ltd", "limited", "company", "co", "plc", "the"}
            keywords = [w for w in words if w not in stop_words and len(w) > 2]
            
            # Add keyword mappings (first 2 significant words)
            for keyword in keywords[:2]:
                if keyword not in _cached_companies:  # Don't overwrite existing
                    _cached_companies[keyword] = entity_id
    except Exception as e:
        print(f"⚠️ Failed to load entity_ids from PostgreSQL: {e}")
        _cached_tickers = ["EXAMPLE_ENTITY_4", "EXAMPLE_ENTITY_3", "EXAMPLE_ENTITY_2", "EXAMPLE_ENTITY_5", "AMZN"]
        _cached_companies = {
            "apple": "EXAMPLE_ENTITY_1",
            "microsoft": "EXAMPLE_ENTITY_4",
            "tesla": "EXAMPLE_ENTITY_3",
            "nvidia": "EXAMPLE_ENTITY_2",
            "alphabet": "EXAMPLE_ENTITY_5",
            "amazon": "AMZN"
        }


def extract_tickers(text: str) -> List[str]:
    """
    Extract entity_ids or company names from the text (case-insensitive).
    
    If multiple entity_ids match, returns ALL of them. The UI/LLM fallback 
    should handle disambiguation by asking user for clarification.
    
    Returns:
        List[str]: All matched entity_ids (may include ambiguous matches)
    """
    _load_tickers_and_companies()
    if not text:
        return []

    t_up = text.upper()
    t_low = text.lower()
    matches = set()  # Use set for deduplication

    # 1) Match entity_id symbols (exact word boundary)
    for sym in _cached_tickers:
        if re.search(rf"\b{sym}\b", t_up):
            matches.add(sym)

    # 2) Match company names/keywords
    # Return ALL matches - let UI or LLM handle ambiguity
    for name, sym in _cached_companies.items():
        if name in t_low:
            matches.add(sym)

    return list(matches)


def get_company_names(entity_ids: List[str]) -> List[str]:
    """Return company names corresponding to entity_ids (fallback to entity_id if missing)."""
    _load_tickers_and_companies()
    return [_cached_companies.get(t, t) for t in entity_ids]


# ---------- Sector keywords ----------
SECTOR_KEYWORDS = [
    "ai", "technology", "tech",
    "renewable", "energy", "green",
    "healthcare", "health",
    "finance", "financials", "bank",
    "etf",
]

def extract_sector(text: str) -> List[str]:
    """Extract mentioned sectors (simple substring match, case-insensitive)."""
    t = (text or "").lower()
    return [s for s in SECTOR_KEYWORDS if s in t]


# ---------- Amount (robust, EUR/USD first) ----------
_EURO_AFTER = re.compile(
    r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(?=\s*(?:€|\beuro\b|\beur\b))",
    re.IGNORECASE,
)
_EURO_BEFORE = re.compile(
    r"€\s*(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_K_SUFFIX = re.compile(
    r"(\d+(?:[.,]\d+)?)(?:\s*(k|mila|thousand))\b",
    re.IGNORECASE,
)
_USD = re.compile(
    r"\$\s*(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(?:\s*(k))?",
    re.IGNORECASE,
)
_TIME_GUARDS = [
    re.compile(r"\b\d+\s*(mesi|mese|m)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*(anni|anno|y|years?)\b", re.IGNORECASE),
]

def _looks_like_time(text: str) -> bool:
    return any(rx.search(text or "") for rx in _TIME_GUARDS)

def _to_int(number_str: str, k_suffix: Optional[str]) -> int:
    s = (number_str or "").replace(".", "").replace(",", ".")
    try:
        val = float(s)
    except Exception:
        return 0
    if k_suffix and k_suffix.lower() in {"k", "mila", "thousand"}:
        val *= 1000.0
    return int(round(val))

def extract_amount(text: str) -> Union[int, None]:
    """
    Extract budget amount.
    - Supports: "5000 euro", "€ 5.000", "5k", "€2,5k", "$10,000"
    - Ignores time-like numbers ("12 mesi") if no money marker.
    """
    t = text or ""

    m = _EURO_AFTER.search(t)
    if m:
        return _to_int(m.group(1), None)

    m = _EURO_BEFORE.search(t)
    if m:
        return _to_int(m.group(1), None)

    m = _K_SUFFIX.search(t)
    if m:
        return _to_int(m.group(1), m.group(2))

    m = _USD.search(t)
    if m:
        return _to_int(m.group(1), m.group(2))

    if _looks_like_time(t):
        return None

    return None


# ---------- Standalone test ----------
if __name__ == "__main__":
    samples = [
        "voglio investire 5000 euro in AAPL (12 mesi)",
        "investo € 5.000 su MSFT per 6m",
        "metto 2,5k su NVDA",
        "budget 10k e orizzonte 3 anni",
        "voglio investire in AAPL per 12 mesi",  # <- no amount
        "investo $10,000 in GOOG",
        "investo 5k per 12 mesi",  # <- must return 5000
    ]
    for s in samples:
        entity_ids = extract_tickers(s)
        companies = get_company_names(entity_ids)
        amt = extract_amount(s)
        print(f"{s} => entity_ids={entity_ids}, companies={companies}, amount={amt}")