import os
import datetime
import yfinance as yf
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.factor_persistence import save_factor_score

load_dotenv()

def get_active_tickers():
    """Retrieve the list of active tickers from Postgres."""
    pg = PostgresAgent()
    query = "SELECT ticker FROM tickers WHERE active = true;"
    with pg.connection.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return [r[0] for r in rows]


def compute_factors(ticker: str) -> dict:
    """
    Compute basic factors using yfinance.
    Value: Earnings Yield (1/PE)
    Growth: earnings growth YoY
    Size: log market cap
    Quality: return on equity
    Academic Momentum: price change 12m
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Value
        pe_ratio = info.get("trailingPE")
        value = 1 / pe_ratio if pe_ratio and pe_ratio > 0 else None

        # Growth
        eps_growth = info.get("earningsGrowth")

        # Size (log market cap)
        mkt_cap = info.get("marketCap")
        size = float(np.log(mkt_cap)) if mkt_cap and mkt_cap > 0 else None

        # Quality (ROE)
        roe = info.get("returnOnEquity")

        # Academic momentum: 12m price change
        hist = t.history(period="1y")
        acad_mom = None
        if not hist.empty:
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            if start_price and end_price:
                acad_mom = (end_price - start_price) / start_price

        # Convert all numpy types to Python native types for PostgreSQL compatibility
        def to_python_type(val):
            if val is None:
                return None
            if pd.isna(val):
                return None
            # Convert numpy types to Python float
            if isinstance(val, (np.integer, np.floating)):
                val = float(val)
                # Check if it's NaN after conversion
                if np.isnan(val):
                    return None
            return float(val) if val is not None else None

        return {
            "value": to_python_type(value),
            "growth": to_python_type(eps_growth),
            "size": to_python_type(size),
            "quality": to_python_type(roe),
            "momentum": to_python_type(acad_mom),
        }
    except Exception as e:
        print(f"❌ Error computing factors for {ticker}: {e}")
        return {}


def backfill_factors():
    tickers = get_active_tickers()
    today = datetime.date.today().isoformat()
    print(f"📊 Backfill factors for {len(tickers)} tickers (date={today})")

    inserted = 0
    for i, t in enumerate(tickers, 1):
        factors = compute_factors(t)
        if not factors:
            continue
        ok = save_factor_score(
            ticker=t,
            date=today,
            value=factors.get("value"),
            growth=factors.get("growth"),
            size=factors.get("size"),
            quality=factors.get("quality"),
            momentum=factors.get("momentum"),
        )
        if ok:
            inserted += 1
            print(f"[{i:03d}/{len(tickers)}] ✅ {t}: {factors}")
        else:
            print(f"[{i:03d}/{len(tickers)}] ❌ {t}: insert failed")

    print(f"\n✅ Backfill completed: {inserted} records saved.")


if __name__ == "__main__":
    backfill_factors()
