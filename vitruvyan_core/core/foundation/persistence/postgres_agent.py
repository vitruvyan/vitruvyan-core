import os
import psycopg2
import json
from dotenv import load_dotenv
import logging

# Caricamento variabili da .env
load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

db_params = {
    "host": DB_HOST,
    "port": DB_PORT,
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD
}

logger = logging.getLogger(__name__)

class PostgresAgent:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(**db_params)
            logger.info("✅ Connessione a PostgreSQL stabilita.")
        except Exception as e:
            logger.error(f"[PostgresAgent] Errore connessione: {e}")
            raise

    def insert_signal(self, ticker: str, pattern: str, confidence: float, source: str, timeframe: str = "daily"):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS signals (
                        id SERIAL PRIMARY KEY,
                        ticker TEXT,
                        pattern TEXT,
                        confidence FLOAT,
                        source TEXT,
                        timeframe TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO signals (ticker, pattern, confidence, source, timeframe)
                    VALUES (%s, %s, %s, %s, %s)
                """, (ticker, pattern, confidence, source, timeframe))
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"[PostgresAgent] Errore salvataggio segnale: {e}")
            return False

    def insert_sentiment(self, ticker: str, reddit: float, google: float, combined: float, tag: str, reddit_titles: list = None, google_titles: list = None, timeframe: str = "daily"):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sentiment_scores (
                        id SERIAL PRIMARY KEY,
                        ticker TEXT,
                        reddit_score FLOAT,
                        google_score FLOAT,
                        combined_score FLOAT,
                        sentiment_tag TEXT,
                        reddit_titles TEXT,
                        google_titles TEXT,
                        timeframe TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO sentiment_scores (ticker, reddit_score, google_score, combined_score, sentiment_tag, reddit_titles, google_titles, timeframe)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker,
                    reddit,
                    google,
                    combined,
                    tag,
                    json.dumps(reddit_titles) if reddit_titles else None,
                    json.dumps(google_titles) if google_titles else None,
                    timeframe
                ))
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"[PostgresAgent] Errore salvataggio sentiment: {e}")
            return False

    def insert_validation(self, ticker: str, decision: str, open_price: float, close_price: float, change_pct: float, outcome: str, validation_date: str = None):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS validations (
                        id SERIAL PRIMARY KEY,
                        ticker TEXT,
                        decision TEXT,
                        open NUMERIC,
                        close NUMERIC,
                        change_pct NUMERIC,
                        outcome TEXT,
                        validation_date DATE DEFAULT CURRENT_DATE
                    )
                """)
                cur.execute("""
                    INSERT INTO validations (ticker, decision, open, close, change_pct, outcome, validation_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker,
                    decision,
                    open_price,
                    close_price,
                    change_pct,
                    outcome,
                    validation_date if validation_date else 'now'
                ))
            self.connection.commit()
            print(f"✅ Validation inserted for {ticker}")
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"[PostgresAgent] Errore salvataggio validation: {e}")
            return False

    def get_cached_explanation(self, ticker, validation_date):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS explanations (
                        id SERIAL PRIMARY KEY,
                        ticker TEXT,
                        explanation_gpt TEXT,
                        explanation_gpt_ts DATE DEFAULT CURRENT_DATE
                    )
                """)
                cur.execute("""
                    SELECT explanation_gpt FROM explanations
                    WHERE ticker = %s AND explanation_gpt_ts = %s
                """, (ticker, validation_date))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"[PostgresAgent] Errore get_cached_explanation: {e}")
            return None

    def insert_explanation(self, ticker, explanation_gpt, validation_date):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO explanations (ticker, explanation_gpt, explanation_gpt_ts)
                    VALUES (%s, %s, %s)
                """, (ticker, explanation_gpt, validation_date))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"[PostgresAgent] Errore insert_explanation: {e}")

    def fetch_all(self, query: str, params: tuple = ()):
        """
        Esegue una query SELECT generica e restituisce tutte le righe.
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
            return rows
        except Exception as e:
            print(f"[PostgresAgent] Errore fetch_all: {e}")
            return []

    def get_latest_sentiments(self):
        """
        Restituisce un dizionario con l'ultimo sentiment per ogni ticker attivo.
        Output: dict {ticker: {"score": float, "tag": str}}
        """
        query = """
            SELECT DISTINCT ON (s.ticker)
                s.ticker,
                s.sentiment_tag,
                s.combined_score
            FROM sentiment_scores s
            JOIN tickers t ON s.ticker = t.ticker
            WHERE t.active = true
            ORDER BY s.ticker, s.created_at DESC;
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
            return {
                ticker: {"score": score, "tag": tag}
                for ticker, tag, score in rows
            }
        except Exception as e:
            print(f"[PostgresAgent] Errore get_latest_sentiments: {e}")
            return {}


    def insert_phrase(self, text: str, source: str, language: str, created_at: str = None, embedded: bool = False):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS phrases (
                        id SERIAL PRIMARY KEY,
                        phrase_text TEXT UNIQUE,
                        source TEXT,
                        language TEXT,
                        embedded BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO phrases (phrase_text, source, language, embedded, created_at, phrase_hash)
                    VALUES (%s, %s, %s, %s, NOW(), md5(%s))
                    ON CONFLICT (phrase_hash) DO NOTHING
                    """,
                    (text, source, language, False, text),
                )
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"[PostgresAgent] Errore insert_phrase: {e}")
            return False

    def log_conversation(self, user_id, prompt, llm_response, report=None):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT,
                        prompt TEXT,
                        llm_response TEXT,
                        report TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO conversations (user_id, prompt, llm_response, report)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, prompt, llm_response, report))
            self.connection.commit()
            logger.info(f"✅ Conversazione salvata per user_id {user_id}")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"[PostgresAgent] Errore salvataggio conversazione: {e}")

    def insert_holding(self, user_id: str, ticker: str, company_name: str, quantity: float, avg_price: float, current_price: float = None):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_holdings (user_id, ticker, company_name, quantity, avg_price, current_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, ticker) DO UPDATE
                    SET company_name = EXCLUDED.company_name,
                        quantity = EXCLUDED.quantity,
                        avg_price = EXCLUDED.avg_price,
                        current_price = EXCLUDED.current_price,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, ticker.upper(), company_name, quantity, avg_price, current_price))
            self.connection.commit()
            logging.info(f"✅ Holding inserito per {user_id}: {ticker} x {quantity}")
            return True
        except Exception as e:
            self.connection.rollback()
            logging.error(f"[PostgresAgent] Errore insert_holding: {e}")
            return False
        
    def ensure_user_exists(self, user_id: str, name: str = None, email: str = None):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (id, name, email)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (user_id, name, email))
            self.connection.commit()
            logging.info(f"✅ Utente {user_id} verificato o creato.")
            return True
        except Exception as e:
            self.connection.rollback()
            logging.error(f"[PostgresAgent] Errore ensure_user_exists: {e}")
            return False
    
# Funzioni standalone fuori dalla classe
def insert_strategy(data: dict):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        sql = """
            INSERT INTO strategies (
                ticker, trend_short, trend_mid, trend_long,
                roc_value, roc_trend, macd_value, macd_trend,
                atr, atr_trend, bandwidth, bandwidth_trend,
                sentiment_label, sentiment_score,
                backtest_total_return, backtest_annualized, backtest_drawdown,
                final_decision, explanation
            ) VALUES (
                %(ticker)s, %(trend_short)s, %(trend_mid)s, %(trend_long)s,
                %(roc_value)s, %(roc_trend)s, %(macd_value)s, %(macd_trend)s,
                %(atr)s, %(atr_trend)s, %(bandwidth)s, %(bandwidth_trend)s,
                %(sentiment_label)s, %(sentiment_score)s,
                %(backtest_total_return)s, %(backtest_annualized)s, %(backtest_drawdown)s,
                %(final_decision)s, %(explanation)s
            )
        """
        cur.execute(sql, data)
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Strategy inserted for {data['ticker']}")
    except Exception as e:
        print(f"[PostgresAgent] Errore salvataggio strategia: {e}")

def get_user_profile(user_id: str):
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_entity WHERE id = %s", (user_id,))
            result = cur.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"[PostgresAgent] Errore get_user_profile: {e}")
        return None

def get_active_tickers() -> list[str]:
    conn = None
    try:
        conn = psycopg2.connect(PG_CONN)
        cur = conn.cursor()
        cur.execute("SELECT ticker FROM tickers WHERE active = true;")
        rows = cur.fetchall()
        cur.close()
        return [r[0].upper() for r in rows]
    except Exception:
        # se Postgres non è raggiungibile → fallback sicuro
        return ["AAPL", "MSFT", "TSLA", "NVDA", "GOOGL", "AMZN", "META"]
    finally:
        if conn:
            conn.close()
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            sql = """
                SELECT ticker
                FROM tickers
                WHERE active = true
                  AND type = ANY(%s::asset_type[])
            """
            cur.execute(sql, (list(include_types),))
            rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()

def save_conversation(user_id: str, input_text: str, slots: dict, intent: str = "unknown"):
    conn = psycopg2.connect(PG_CONN)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations (user_id, input_text, slots, intent)
        VALUES (%s, %s, %s, %s)
    """, (user_id, input_text, json.dumps(slots), intent))
    conn.commit()
    cur.close()
    conn.close()

def get_last_conversation(user_id: str) -> dict:
    conn = psycopg2.connect(PG_CONN)
    cur = conn.cursor()
    cur.execute("""
        SELECT slots
        FROM conversations
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else {}


# ============================================================
# 🧠 VSGS PR-B — Semantic Grounding Event Persistence
# ============================================================

def save_grounding_event(conn, **data):
    """
    Save semantic grounding event to PostgreSQL (VSGS PR-B).
    
    Args:
        conn: PostgreSQL connection
        **data: user_id, trace_id, query_text, language, affective_state,
                semantic_context, grounding_confidence, phrase_hash, phase
    
    Returns:
        int: Inserted row ID, or None if duplicate (phrase_hash conflict)
    
    Example:
        import hashlib
        phrase_hash = hashlib.sha256(f"{user_id}:{query_text}:{language}".encode()).hexdigest()
        row_id = save_grounding_event(
            conn,
            user_id="user123",
            trace_id="trace_abc",
            query_text="analizza AAPL",
            language="it",
            affective_state="confident",
            semantic_context={"matches": [...]},
            grounding_confidence=0.87,
            phrase_hash=phrase_hash,
            phase="ingest"
        )
    """
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO semantic_grounding_events
                (user_id, trace_id, query_text, language, affective_state,
                 semantic_context, grounding_confidence, phrase_hash, phase)
                VALUES (%(user_id)s, %(trace_id)s, %(query_text)s, %(language)s,
                        %(affective_state)s, %(semantic_context)s::jsonb,
                        %(grounding_confidence)s, %(phrase_hash)s, %(phase)s)
                ON CONFLICT (phrase_hash) DO NOTHING
                RETURNING id;
            """
            # Convert semantic_context to JSON if dict
            if isinstance(data.get('semantic_context'), dict):
                data['semantic_context'] = json.dumps(data['semantic_context'])
            
            cur.execute(query, data)
            result = cur.fetchone()
            conn.commit()
            return result[0] if result else None
    except Exception as e:
        conn.rollback()
        logger.error(f"[PostgresAgent] save_grounding_event failed: {e}")
        return None


def fetch_unsynced_groundings(conn, limit=100):
    """
    Fetch semantic grounding events not yet synced to Qdrant.
    
    Args:
        conn: PostgreSQL connection
        limit: Maximum number of rows to fetch
    
    Returns:
        list[dict]: Unsynced grounding events
    """
    try:
        with conn.cursor() as cur:
            query = """
                SELECT id, user_id, trace_id, query_text, language,
                       affective_state, semantic_context, embedding_vector,
                       grounding_confidence, phrase_hash, phase, created_at
                FROM semantic_grounding_events
                WHERE qdrant_synced = false
                ORDER BY created_at ASC
                LIMIT %s;
            """
            cur.execute(query, (limit,))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"[PostgresAgent] fetch_unsynced_groundings failed: {e}")
        return []


def mark_grounding_synced(conn, grounding_id):
    """
    Mark semantic grounding event as synced to Qdrant.
    
    Args:
        conn: PostgreSQL connection
        grounding_id: ID of the grounding event
    
    Returns:
        bool: True if successful
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE semantic_grounding_events SET qdrant_synced = true WHERE id = %s",
                (grounding_id,)
            )
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"[PostgresAgent] mark_grounding_synced failed: {e}")
        return False


def count_grounding_events(conn):
    """
    Count total semantic grounding events (for drift monitoring).
    
    Args:
        conn: PostgreSQL connection
    
    Returns:
        int: Total count of grounding events
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM semantic_grounding_events;")
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"[PostgresAgent] count_grounding_events failed: {e}")
        return 0
