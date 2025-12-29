#!/usr/bin/env python3
"""
Quick Technical Backfill for Neural Engine
==========================================

Popola trend_logs, momentum_logs, volatility_logs per i ticker attivi
usando Scribe senza passare da __init__.py (evita duplicazione Prometheus).
"""

import sys
import logging
from datetime import datetime, timedelta
import yfinance as yf

sys.path.insert(0, '/home/caravaggio/vitruvyan')

# Import diretto senza __init__.py per evitare Prometheus duplicates
from core.governance.codex_hunters.scribe import Scribe
from core.foundation.persistence.postgres_agent import PostgresAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_ticker_data(ticker: str, days: int = 250) -> dict:
    """Fetch OHLCV data from yfinance"""
    try:
        end = datetime.now()
        start = end - timedelta(days=days + 50)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, end=end)
        
        if df.empty:
            return None
        
        history = []
        for date, row in df.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        return {
            "ticker": ticker,
            "history": history,
            "source": "yfinance"
        }
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Max tickers")
    args = parser.parse_args()
    
    # Get active tickers
    pg = PostgresAgent()
    with pg.connection.cursor() as cur:
        cur.execute(f"SELECT ticker FROM tickers WHERE active = true LIMIT {args.limit}")
        tickers = [row[0] for row in cur.fetchall()]
    
    logger.info(f"🔬 Starting Scribe backfill for {len(tickers)} tickers...")
    
    # Fetch data for all tickers
    normalized_data = []
    for ticker in tickers:
        logger.info(f"📊 Fetching {ticker}...")
        data = fetch_ticker_data(ticker)
        if data:
            normalized_data.append(data)
    
    if not normalized_data:
        logger.error("❌ No data fetched!")
        return 1
    
    logger.info(f"✅ Fetched {len(normalized_data)} tickers, calculating indicators...")
    
    # Run Scribe
    scribe = Scribe(user_id="quick_backfill")
    result = scribe.execute(normalized_data=normalized_data, batch_size=50)
    
    logger.info(f"""
🎉 BACKFILL COMPLETE!
    Processed: {result['processed']}
    Successful: {result['successful']}
    Failed: {result['failed']}
    Duration: {result['duration_seconds']:.2f}s
    """)
    
    return 0 if result['successful'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
