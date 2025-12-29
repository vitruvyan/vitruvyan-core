# core/leo/sentiment_access.py

from typing import Optional, List, Dict, Union
from .postgres_agent import PostgresAgent


def get_latest_sentiments(limit: Optional[int] = None) -> List[Dict[str, Union[str, float]]]:
    """
    Recupera l'ultimo dato di sentiment per ciascun ticker.
    """
    query = """
        SELECT DISTINCT ON (ticker)
            ticker,
            sentiment_tag,
            combined_score,
            created_at
        FROM sentiment_scores
        ORDER BY ticker, created_at DESC
    """
    if limit and limit > 0:
        query = f"""
            WITH ranked AS (
                {query}
            )
            SELECT * FROM ranked LIMIT {limit}
        """

    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return [
        {
            "ticker": row[0],
            "sentiment_tag": row[1],
            "combined_score": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


def get_latest_sentiment_for_ticker(ticker: str) -> Optional[Dict[str, Union[str, float]]]:
    """
    Recupera l'ultimo dato di sentiment per un singolo ticker.
    """
    query = """
        SELECT sentiment_tag, combined_score, created_at
        FROM sentiment_scores
        WHERE ticker = %s
        ORDER BY created_at DESC
        LIMIT 1
    """

    agent = PostgresAgent()
    with agent.connection.cursor() as cur:
        cur.execute(query, (ticker,))
        row = cur.fetchone()

    if not row:
        return None

    return {
        "ticker": ticker,
        "sentiment_tag": row[0],
        "combined_score": row[1],
        "created_at": row[2],
    }
