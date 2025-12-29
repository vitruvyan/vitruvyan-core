import os
import requests
import datetime
from dotenv import load_dotenv
from core.foundation.persistence.macro_persistence import save_macro_outlook

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Serie che ci servono
SERIES = {
    "CPIAUCSL": "inflation_rate",     # CPI (inflazione YoY)
    "FEDFUNDS": "interest_rate",      # Fed Funds
    "VIXCLS": "market_volatility"     # Volatilità implicita (VIX)
}


def fetch_series(series_id: str, start_date: str = "2020-01-01"):
    """Scarica osservazioni da FRED API per una serie"""
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }
    url = BASE_URL
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("observations", [])


def backfill_macro(start_date: str = "2020-01-01"):
    """
    Scarica serie macro e salva in macro_outlook.
    Ogni data ha un unico record con inflazione, tassi e volatilità.
    """
    print("📥 Scarico serie da FRED...")
    all_data = {field: {} for field in SERIES.values()}

    for sid, field in SERIES.items():
        observations = fetch_series(sid, start_date=start_date)
        for obs in observations:
            date = obs["date"]
            value = obs["value"]
            if value == ".":
                continue
            try:
                val = float(value)
            except Exception:
                continue
            all_data[field][date] = val

    # Unisci le serie per date comuni
    all_dates = sorted(
        set().union(*[set(vals.keys()) for vals in all_data.values()])
    )
    print(f"📊 Trovate {len(all_dates)} date")

    inserted = 0
    for d in all_dates:
        inflation = all_data["inflation_rate"].get(d)
        rate = all_data["interest_rate"].get(d)
        vola = all_data["market_volatility"].get(d)
        ok = save_macro_outlook(
            date=d,
            inflation=inflation,
            rate=rate,
            vola=vola,
            source="FRED"
        )
        if ok:
            inserted += 1

    print(f"✅ Backfill completato: {inserted} record inseriti/aggiornati.")


if __name__ == "__main__":
    backfill_macro(start_date="2020-01-01")
