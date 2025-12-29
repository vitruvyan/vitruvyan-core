# core/logic/semantic_modules/data/insert_phrases_pg.py

import os
import sys
import json
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [Phrase Log] %(message)s"
)

# 🔐 Credenziali PostgreSQL
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


def insert_phrases(phrases):
    """Inserisce frasi in PostgreSQL nella tabella 'phrases'."""
    if not phrases:
        logging.warning("Nessuna frase da inserire.")
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()

        for phrase in phrases:
            try:
                cur.execute("""
                    INSERT INTO phrases
                        (phrase_text, context_type, sentiment, tone, source, created_at, embedded, language)
                    VALUES (%s, %s, %s, %s, %s, %s, false, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    phrase.get("text"),
                    phrase.get("context_type"),
                    phrase.get("sentiment"),
                    phrase.get("tone"),
                    phrase.get("source"),
                    phrase.get("timestamp"),   # <-- va in created_at
                    phrase.get("language"),
                ))
                logging.info(f"✅ Inserita: {phrase.get('text')[:60]}...")
            except Exception as e:
                logging.warning(f"❌ Errore inserimento frase: {phrase.get('text')[:60]}... | {e}")

        cur.close()
        conn.close()
        logging.info("🏁 Inserimento frasi completato.")

    except Exception as e:
        logging.error(f"❌ Connessione DB fallita: {e}")


if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        phrases = json.loads(input_data)
        insert_phrases(phrases)
    except Exception as e:
        logging.error(f"❌ Errore esecuzione script: {e}")
