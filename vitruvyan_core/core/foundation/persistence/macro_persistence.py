# core/leo/macro_persistence.py

import logging
from .postgres_agent import PostgresAgent

def save_macro_outlook(date: str, inflation: float = None, rate: float = None, vola: float = None, source: str = "FRED"):
    """
    Inserts a record into macro_outlook.
    If already present for the same date and source, updates the existing record.
    """
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS macro_outlook (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    inflation_rate NUMERIC,
                    interest_rate NUMERIC,
                    market_volatility NUMERIC,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT macro_outlook_unique UNIQUE(date, source)
                )
            """)
            cur.execute("""
                INSERT INTO macro_outlook (date, inflation_rate, interest_rate, market_volatility, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date, source) DO UPDATE
                SET inflation_rate = EXCLUDED.inflation_rate,
                    interest_rate = EXCLUDED.interest_rate,
                    market_volatility = EXCLUDED.market_volatility,
                    created_at = CURRENT_TIMESTAMP
            """, (date, inflation, rate, vola, source))
            pg.connection.commit()
        logging.info(f"[MacroPersistence] ✅ Saved macro outlook for {date} ({source})")
        return True
    except Exception as e:
        logging.error(f"[MacroPersistence] ❌ Errore salvataggio macro_outlook: {e}")
        pg.connection.rollback()
        return False
