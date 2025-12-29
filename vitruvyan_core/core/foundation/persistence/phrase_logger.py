import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logger = logging.getLogger("phrase_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Connessione diretta (NO PostgresAgent)
DB_PARAMS = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

def log_phrase_to_db(phrase_dict: dict) -> bool:
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO phrases (phrase_text, context_type, sentiment, tone, source, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            phrase_dict.get("text"),
            phrase_dict.get("context_type"),
            phrase_dict.get("sentiment"),
            phrase_dict.get("tone"),
            phrase_dict.get("source"),
            phrase_dict.get("timestamp", datetime.utcnow())
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"[Phrase Log] ✅ Inserita frase: {phrase_dict.get('text')[:60]}...")
        return True
    except Exception as e:
        logger.warning(f"[Phrase Log] ❌ Errore inserimento frase: {e}")
        return False
