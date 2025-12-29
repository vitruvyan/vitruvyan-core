#!/usr/bin/env python3
"""
Backfill completo per Vitruvyan:
- Trend, Momentum, Volatility (tool CrewAI → loggano in PG)
- Sentiment (API vitruvyan_api_sentiment → log in PG)

Supporta batching e sleep tra batch per non saturare API/DB.
"""

import os
import sys
import argparse
import time
import requests
from datetime import datetime

# Consenti import da core/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.foundation.persistence.postgres_agent import PostgresAgent
from core.crewai.tools.trend_tool import TrendAnalysisTool
from core.crewai.tools.momentum_tool import MomentumAnalysisTool
from core.crewai.tools.volatility_tool import VolatilityAnalysisTool


# ===========================
# Helpers
# ===========================

def get_active_tickers(limit: int | None = None, only_us: bool = False) -> list[str]:
    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        sql = "SELECT ticker FROM tickers WHERE active = true"
        if only_us:
            sql += " AND country = 'US'"
        sql += " ORDER BY ticker ASC"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        cur.execute(sql)
        return [r[0] for r in cur.fetchall()]


def safe_call(label: str, func, **kwargs) -> bool:
    try:
        func(**kwargs)  # i tool loggano già su DB + console
        print(f"  → {label:<10} [OK]")
        return True
    except Exception as e:
        print(f"  → {label:<10} [ERR] {e}")
        return False


def run_sentiment(ticker: str) -> bool:
    try:
        url = os.getenv("SENTIMENT_URL", "http://localhost:8001/analyze_combined")
        resp = requests.post(url, json={"ticker": ticker}, timeout=60)
        if resp.status_code == 200:
            print(f"  → Sentiment  [OK]")
            return True
        else:
            print(f"  → Sentiment  [ERR] HTTP {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"  → Sentiment  [ERR] {e}")
        return False

def process_ticker(ticker: str,
                   run_trend: bool = True,
                   run_momentum: bool = True,
                   run_volatility: bool = True,
                   run_sent: bool = True) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== {ticker} === {ts} ===")

    if run_trend:
        safe_call("Trend", TrendAnalysisTool().run, ticker=ticker)

    if run_momentum:
        safe_call("Momentum", MomentumAnalysisTool().run, ticker=ticker)

    if run_volatility:
        safe_call("Volatility", VolatilityAnalysisTool().run, ticker=ticker)

    if run_sent:
        run_sentiment(ticker)

    print(f"✅ Completato {ticker}")


# ===========================
# Main
# ===========================

def main():
    ap = argparse.ArgumentParser(description="Backfill completo (tecnico + sentiment) con batching.")
    ap.add_argument("--limit", type=int, default=None, help="Limita il numero di ticker dal DB.")
    ap.add_argument("--tickers", type=str, default="", help="Lista manuale di ticker separati da virgola (override DB).")
    ap.add_argument("--batch-size", type=int, default=20, help="Numero di ticker per batch (default=20).")
    ap.add_argument("--sleep-batch", type=int, default=5, help="Pausa in secondi tra i batch (default=5).")
    ap.add_argument("--only-us", action="store_true", help="Filtra solo ticker US.")
    ap.add_argument("--only", choices=["all", "trend", "momentum", "volatility", "sentiment"], default="all",
                    help="Esegui solo un tool.")
    args = ap.parse_args()

    # quali tool
    run_trend = args.only in ("all", "trend")
    run_momentum = args.only in ("all", "momentum")
    run_volatility = args.only in ("all", "volatility")
    run_sent = args.only in ("all", "sentiment")

    # tickers
    if args.tickers.strip():
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = get_active_tickers(limit=args.limit, only_us=args.only_us)

    print(f"🔍 Trovati {len(tickers)} ticker target")
    if not tickers:
        print("Nessun ticker da processare. Esco.")
        return

    # batching
    for i in range(0, len(tickers), args.batch_size):
        batch = tickers[i:i + args.batch_size]
        print(f"\n🚀 Batch {i // args.batch_size + 1}/{(len(tickers) - 1) // args.batch_size + 1} → {batch}")

        for t in batch:
            process_ticker(
                t,
                run_trend=run_trend,
                run_momentum=run_momentum,
                run_volatility=run_volatility,
                run_sent=run_sent,
            )

        if i + args.batch_size < len(tickers):
            print(f"⏳ Attendo {args.sleep_batch}s prima del prossimo batch…")
            time.sleep(args.sleep_batch)

    print("\n✅ Backfill COMPLETATO.")


if __name__ == "__main__":
    main()
