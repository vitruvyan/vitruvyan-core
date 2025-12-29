# core/leo/factor_persistence.py

import logging
from .postgres_agent import PostgresAgent

def save_factor_score(
    ticker: str,
    date: str,
    value: float = None,
    growth: float = None,
    size: float = None,
    quality: float = None,
    momentum: float = None
):
    """
    Inserts a record into factor_scores.
    If a record already exists for the same ticker and date, updates the values.
    """
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS factor_scores (
                    id SERIAL PRIMARY KEY,
                    ticker TEXT NOT NULL REFERENCES tickers(ticker),
                    date DATE NOT NULL,
                    value NUMERIC,
                    growth NUMERIC,
                    size NUMERIC,
                    quality NUMERIC,
                    momentum NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT factor_scores_unique UNIQUE(ticker, date)
                )
            """)

            cur.execute("""
                INSERT INTO factor_scores (ticker, date, value, growth, size, quality, momentum)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO UPDATE
                SET value = EXCLUDED.value,
                    growth = EXCLUDED.growth,
                    size = EXCLUDED.size,
                    quality = EXCLUDED.quality,
                    momentum = EXCLUDED.momentum,
                    created_at = CURRENT_TIMESTAMP
            """, (ticker, date, value, growth, size, quality, momentum))
            pg.connection.commit()
        logging.info(f"[FactorPersistence] ✅ Saved factors for {ticker} ({date})")
        return True
    except Exception as e:
        logging.error(f"[FactorPersistence] ❌ Errore salvataggio factors per {ticker} ({date}): {e}")
        pg.connection.rollback()
        return False
