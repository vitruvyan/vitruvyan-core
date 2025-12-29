# core/logic/semantic_engine/data/reddit_scraper.py

import os
import re
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import praw
from core.foundation.persistence import PostgresAgent

pg = PostgresAgent()

load_dotenv()

# 🔐 Reddit credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "VitruvyanBot/0.1 by Davide")

# 🔐 PostgreSQL credentials
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# 🌍 Subreddits per lingua
LANG_SUBREDDITS = {
    "en": ["investing", "stocks", "wallstreetbets", "options", "valueinvesting", "securityanalysis"],
    "it": ["finanza", "borsaitaliana", "tradingitalia", "criptovaluteitalia", "italy", "italia"],
    "es": ["inversiones", "bolsa", "finanzaspersonales", "criptomonedas", "economia", "mexico", "espanol"]
}

LIMIT_PER_FEED = 200  # 🔁 per ciascun tipo di feed

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)


def clean_phrase(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\s.,!?-]", "", text)
    text = re.sub(r"\s{2,}", " ", text)  # rimuove doppie spaziature
    return text.strip()


def get_existing_phrases() -> set:
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        with conn.cursor() as cur:
            cur.execute("SELECT phrase_text FROM phrases")
            existing = set(row[0].lower() for row in cur.fetchall())
        conn.close()
        return existing
    except Exception as e:
        print(f"⚠️ DB error: {e}")
        return set()


def scrape_reddit_phrases():
    phrases = []
    for lang, subreddits in LANG_SUBREDDITS.items():
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            for feed in ["hot", "new", "top"]:
                try:
                    submissions = getattr(subreddit, feed)(limit=LIMIT_PER_FEED)
                    for post in submissions:
                        if post.stickied or post.over_18:
                            continue
                        raw = f"{post.title} {post.selftext}".strip()
                        cleaned = clean_phrase(raw)
                        if len(cleaned.split()) > 4:
                            pg.insert_phrase(
                                text=cleaned,
                                source=f"reddit_{lang}/{sub}/{feed}",
                                language=lang,
                                created_at=datetime.utcnow().isoformat()
                            )
                except Exception as e:
                    print(f"⚠️ Error on {lang}/{sub}/{feed}: {e}")
    phrases = set()
    existing_phrases = get_existing_phrases()

    for lang, subreddits in LANG_SUBREDDITS.items():
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            for feed in ["hot", "new", "top"]:
                try:
                    submissions = getattr(subreddit, feed)(limit=LIMIT_PER_FEED)
                    for post in submissions:
                        if post.stickied or post.over_18:
                            continue
                        raw = f"{post.title} {post.selftext}".strip()
                        cleaned = clean_phrase(raw)
                        if len(cleaned.split()) > 4 and cleaned.lower() not in existing_phrases:
                            phrases.add((
                                cleaned,
                                f"reddit_{lang}/{sub}/{feed}",
                                lang,
                                datetime.utcnow().isoformat()
                            ))
                except Exception as e:
                    print(f"⚠️ Error on {lang}/{sub}/{feed}: {e}")

    return [
        {"text": p[0], "source": p[1], "language": p[2], "timestamp": p[3]}
        for p in phrases
    ]


def test_scraper():
    results = scrape_reddit_phrases()
    for r in results[:10]:
        print(f"🌍 {r['language']} | {r['source']} ➜ {r['text']}")
    print(f"\n✅ Raccolte {len(results)} frasi totali.")


if __name__ == "__main__":
    test_scraper()
