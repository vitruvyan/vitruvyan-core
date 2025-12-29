# core/leo/factor_access.py

from typing import Optional, Dict, Any, List
from .postgres_agent import PostgresAgent

def get_latest_factors(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the latest set of factors for a ticker.
    """
    query = """
        SELECT date, value, growth, size, quality, momentum, created_at
        FROM factor_scores
        WHERE ticker = %s
        ORDER BY date DESC
        LIMIT 1
    """
    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        cur.execute(query, (ticker,))
        row = cur.fetchone()

    if not row:
        return None

    return {
        "date": row[0],
        "value": row[1],
        "growth": row[2],
        "size": row[3],
        "quality": row[4],
        "momentum": row[5],
        "created_at": row[6],
    }

def get_factors_for_date(date: str) -> List[Dict[str, Any]]:
    """
    Recupera tutti i fattori disponibili per una data specifica.
    """
    query = """
        SELECT ticker, value, growth, size, quality, momentum, created_at
        FROM factor_scores
        WHERE date = %s
    """
    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        cur.execute(query, (date,))
        rows = cur.fetchall()

    cols = ["ticker", "value", "growth", "size", "quality", "momentum", "created_at"]
    return [dict(zip(cols, r)) for r in rows]
