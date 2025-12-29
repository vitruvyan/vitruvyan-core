from typing import List, Optional, Dict, Any
from .postgres_agent import PostgresAgent

SQL_BASE = """
SELECT DISTINCT ON (ticker)
  id, ticker, short_trend, medium_trend, long_trend,
  sma_short, sma_medium, sma_long, timestamp
FROM trend_logs
{where_clause}
ORDER BY ticker, timestamp DESC
"""

def get_latest_trends(tickers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    where_clause = ""
    params: tuple = ()
    if tickers:
        placeholders = ",".join(["%s"] * len(tickers))
        where_clause = f"WHERE ticker IN ({placeholders})"
        params = tuple(tickers)
    query = SQL_BASE.format(where_clause=where_clause)

    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    cols = ["id","ticker","short_trend","medium_trend","long_trend",
            "sma_short","sma_medium","sma_long","timestamp"]
    return [dict(zip(cols, r)) for r in rows]

def get_latest_trend_for_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    res = get_latest_trends([ticker])
    return res[0] if res else None
