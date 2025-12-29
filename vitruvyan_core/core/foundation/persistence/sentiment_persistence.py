import logging
import psycopg2
from .postgres_agent import PostgresAgent

def save_sentiment_score(ticker: str, score: float, sentiment_tag: str, dedupe_key: str):
    """
    Inserisce un record di sentiment_scores con deduplica su dedupe_key.
    Se già presente aggiorna i valori.
    """
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO sentiment_scores (ticker, combined_score, sentiment_tag, dedupe_key)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (dedupe_key) DO UPDATE
                SET combined_score = EXCLUDED.combined_score,
                    sentiment_tag = EXCLUDED.sentiment_tag,
                    created_at = CURRENT_TIMESTAMP
            """, (ticker, score, sentiment_tag, dedupe_key))
            pg.connection.commit()
        logging.info(f"[SentimentPersistence] ✅ Saved sentiment for {ticker} (dedupe_key={dedupe_key})")
        return True
    except Exception as e:
        logging.error(f"[SentimentPersistence] ❌ Errore salvataggio sentiment per {ticker}: {e}")
        pg.connection.rollback()
        return False
