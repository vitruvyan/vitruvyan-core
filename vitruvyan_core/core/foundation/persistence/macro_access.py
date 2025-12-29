# core/leo/macro_access.py

from typing import Optional, Dict, Any, List
from .postgres_agent import PostgresAgent

def get_latest_macro(date: Optional[str] = None, source: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve the latest available macroeconomic data.
    If `date` is provided → filter by that date.
    If `source` is provided → filter by that source.
    """
    query = """
        SELECT date, inflation_rate, interest_rate, market_volatility, source, created_at
        FROM macro_outlook
    """
    filters = []
    params: List[Any] = []

    if date:
        filters.append("date = %s")
        params.append(date)
    if source:
        filters.append("source = %s")
        params.append(source)

    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY date DESC LIMIT 1"

    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        cur.execute(query, tuple(params))
        row = cur.fetchone()

    if not row:
        return None

    return {
        "date": row[0],
        "inflation_rate": row[1],
        "interest_rate": row[2],
        "market_volatility": row[3],
        "source": row[4],
        "created_at": row[5],
    }
