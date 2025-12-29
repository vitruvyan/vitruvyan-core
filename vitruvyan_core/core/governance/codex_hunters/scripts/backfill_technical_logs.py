# scripts/backfill_technical_logs.py
import os
import sys
import argparse
from datetime import datetime

# Consenti import da core/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.foundation.persistence.postgres_agent import PostgresAgent
from core.crewai.tools.trend_tool import TrendAnalysisTool
from core.crewai.tools.momentum_tool import MomentumAnalysisTool
from core.crewai.tools.volatility_tool import VolatilityAnalysisTool

# Ensure momentum_logs schema on startup
try:
    from scripts.ensure_momentum_schema import ensure_momentum_logs_schema
    print("🔧 Verifying momentum_logs schema...")
    ensure_momentum_logs_schema()
except Exception as e:
    print(f"⚠️ Schema check failed (non-fatal): {e}")


def get_active_tickers(only_us: bool = False, limit: int | None = None) -> list[str]:
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
        func(**kwargs)   # i tool loggano già su DB + console
        print(f"  → {label:<10} [OK]")
        return True
    except Exception as e:
        print(f"  → {label:<10} [ERR] {e}")
        return False


def process_ticker(ticker: str,
                   run_trend: bool = True,
                   run_momentum: bool = True,
                   run_volatility: bool = True) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== {ticker} === {ts} ===")

    if run_trend:
        safe_call("Trend", TrendAnalysisTool().run, ticker=ticker)

    if run_momentum:
        safe_call("Momentum", MomentumAnalysisTool().run, ticker=ticker)

    if run_volatility:
        safe_call("Volatility", VolatilityAnalysisTool().run, ticker=ticker)

    print(f"✅ Completato {ticker}")


def main():
    ap = argparse.ArgumentParser(description="Backfill tecnico (trend/momentum/volatility) sequenziale e pulito.")
    ap.add_argument("--only-us", action="store_true", help="Filtra solo i ticker con country = 'US'.")
    ap.add_argument("--limit", type=int, default=None, help="Limita il numero di ticker dal DB (debug).")
    ap.add_argument("--tickers", type=str, default="", help="Lista manuale di ticker separati da virgola (override DB).")
    ap.add_argument("--only", choices=["all", "trend", "momentum", "volatility"], default="all",
                    help="Esegui solo un tool.")
    args = ap.parse_args()

    # quali tool eseguire
    run_trend = args.only in ("all", "trend")
    run_momentum = args.only in ("all", "momentum")
    run_volatility = args.only in ("all", "volatility")

    # selezione universo
    if args.tickers.strip():
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = get_active_tickers(only_us=args.only_us, limit=args.limit)

    print(f"🔍 Trovati {len(tickers)} ticker target: {tickers if len(tickers) <= 50 else tickers[:50] + ['…']}")

    if not tickers:
        print("Nessun ticker da processare. Esco.")
        return

    for t in tickers:
        process_ticker(
            t,
            run_trend=run_trend,
            run_momentum=run_momentum,
            run_volatility=run_volatility,
        )

    print("\n✅ Backfill tecnico COMPLETATO.")
    

if __name__ == "__main__":
    main()