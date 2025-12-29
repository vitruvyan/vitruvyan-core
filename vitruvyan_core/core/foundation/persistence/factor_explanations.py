# core/leo/factor_explanations.py

import logging
from .postgres_agent import PostgresAgent

def save_explanations(run_id: int, explanations: list[dict]):
    """
    Save rationales (narratives) for each ticker in a NE run.
    explanations = [{"ticker": "AAPL", "rationale": "..."}]
    """
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS factor_explanations (
                    id SERIAL PRIMARY KEY,
                    run_id INT NOT NULL REFERENCES screener_results(id) ON DELETE CASCADE,
                    ticker TEXT NOT NULL,
                    rationale TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            for e in explanations:
                cur.execute(
                    """
                    INSERT INTO factor_explanations (run_id, ticker, rationale)
                    VALUES (%s, %s, %s)
                    """,
                    (run_id, e["ticker"], e["rationale"]),
                )
        pg.connection.commit()
        logging.info(f"[FactorExplanations] ✅ Salvate {len(explanations)} rationale per run_id={run_id}")
    except Exception as e:
        pg.connection.rollback()
        logging.error(f"[FactorExplanations] ❌ Errore salvataggio rationale: {e}")
