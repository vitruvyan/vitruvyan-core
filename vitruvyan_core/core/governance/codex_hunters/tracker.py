# core/agents/codex_hunters/tracker.py
"""
🗺️ THE TRACKER - Codex Discovery Agent
========================================
Tracks lost codices across multiple archives and data sources.

Like Poggio Bracciolini discovering Lucretius in forgotten monasteries,
The Tracker searches yfinance, Reddit, Google News, and FRED archives
for lost financial manuscripts.

Publishes CodexEvent(type="codex.discovered") for downstream restoration.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Data source imports
import yfinance as yf
import praw
import feedparser
from urllib.parse import quote

# Vitruvyan imports
from core.governance.codex_hunters.hunter import (
    BaseHunter,
    CodexEvent
)
from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent
from core.foundation.cognitive_bus.event_schema import (
    create_codex_discovery_event,
    CodexIntent,
    EventSchemaValidator
)

load_dotenv()
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter with sliding window"""
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.call_times: List[float] = []
    
    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        now = time.time()
        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        if len(self.call_times) >= self.calls_per_minute:
            # Wait until oldest call expires
            sleep_time = 60 - (now - self.call_times[0]) + 0.1
            if sleep_time > 0:
                logger.info(f"⏳ Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.call_times = []  # Reset after wait
        
        self.call_times.append(now)


class Tracker(BaseHunter):
    """
    Multi-source data fetcher with intelligent rate limiting.
    
    Supported sources:
    - yfinance: Entity prices, fundamentals, historical data
    - reddit: Social sentiment from financial subreddits
    - google_news: News articles and headlines
    - fred: Macro economic indicators
    """
    
    def __init__(self):
        super().__init__("Tracker")
        
        # Rate limiters per source
        self.rate_limiters = {
            "yfinance": RateLimiter(calls_per_minute=100),  # yfinance is generous
            "reddit": RateLimiter(calls_per_minute=30),      # PRAW rate limits
            "google_news": RateLimiter(calls_per_minute=60), # RSS is fast
            "fred": RateLimiter(calls_per_minute=50),        # FRED API limit
        }
        
        # Reddit client (lazy init)
        self._reddit_client: Optional[praw.Reddit] = None
        
        # Track fetch statistics
        self.fetch_stats = {
            "yfinance": {"success": 0, "failed": 0, "total_records": 0},
            "reddit": {"success": 0, "failed": 0, "total_records": 0},
            "google_news": {"success": 0, "failed": 0, "total_records": 0},
            "fred": {"success": 0, "failed": 0, "total_records": 0},
        }
    
    @property
    def reddit_client(self) -> praw.Reddit:
        """Lazy initialization of Reddit client"""
        if self._reddit_client is None:
            self._reddit_client = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_USER_AGENT", "VitruvyanFetcher/1.0")
            )
        return self._reddit_client
    
    def fetch_yfinance_data(self, entity_id: str, period: str = "1mo") -> Dict[str, Any]:
        """
        Fetch entity data from yfinance.
        
        Returns:
            {
                "entity_id": str,
                "info": dict,           # Company fundamentals
                "history": list[dict],  # Price history
                "source": "yfinance",
                "timestamp": str
            }
        """
        self.rate_limiters["yfinance"].wait_if_needed()
        
        try:
            entity = yf.EntityId(entity_id)
            info = entity.info
            history = entity.history(period=period)
            
            # Convert DataFrame to list of dicts
            history_data = []
            for date, row in history.iterrows():
                history_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                })
            
            result = {
                "entity_id": entity_id,
                "info": {
                    "name": info.get("longName", entity_id),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "market_cap": info.get("marketCap"),
                    "pe_ratio": info.get("trailingPE"),
                    "dividend_yield": info.get("dividendYield"),
                },
                "history": history_data,
                "source": "yfinance",
                "timestamp": datetime.now().isoformat()
            }
            
            self.fetch_stats["yfinance"]["success"] += 1
            self.fetch_stats["yfinance"]["total_records"] += len(history_data)
            logger.info(f"✅ [yfinance] Fetched {entity_id}: {len(history_data)} records")
            return result
            
        except Exception as e:
            self.fetch_stats["yfinance"]["failed"] += 1
            logger.error(f"❌ [yfinance] Failed to fetch {entity_id}: {e}")
            return {
                "entity_id": entity_id,
                "error": str(e),
                "source": "yfinance",
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_reddit_sentiment(self, entity_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch Reddit posts mentioning the entity_id.
        
        Returns:
            {
                "entity_id": str,
                "posts": list[dict],  # Post data
                "source": "reddit",
                "timestamp": str
            }
        """
        self.rate_limiters["reddit"].wait_if_needed()
        
        try:
            query = f"{entity_id} entity"
            posts = []
            
            # Search across financial subreddits
            subreddits = ["investing", "entities", "wallstreetbets", "ValueInvesting"]
            for subreddit_name in subreddits[:2]:  # Limit to 2 for speed
                try:
                    subreddit = self.reddit_client.subreddit(subreddit_name)
                    for post in subreddit.search(query, sort="new", limit=limit // 2):
                        if entity_id.upper() in post.title.upper():
                            posts.append({
                                "subreddit": subreddit_name,
                                "title": post.title,
                                "selftext": post.selftext[:200],  # Truncate
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                                "url": post.url,
                            })
                except Exception as sub_err:
                    logger.warning(f"⚠️ [reddit] Error in r/{subreddit_name}: {sub_err}")
                    continue
            
            result = {
                "entity_id": entity_id,
                "posts": posts,
                "source": "reddit",
                "timestamp": datetime.now().isoformat()
            }
            
            self.fetch_stats["reddit"]["success"] += 1
            self.fetch_stats["reddit"]["total_records"] += len(posts)
            logger.info(f"✅ [reddit] Fetched {entity_id}: {len(posts)} posts")
            return result
            
        except Exception as e:
            self.fetch_stats["reddit"]["failed"] += 1
            logger.error(f"❌ [reddit] Failed to fetch {entity_id}: {e}")
            return {
                "entity_id": entity_id,
                "error": str(e),
                "posts": [],
                "source": "reddit",
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_google_news(self, entity_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch Google News articles for the entity_id.
        
        Returns:
            {
                "entity_id": str,
                "articles": list[dict],  # News articles
                "source": "google_news",
                "timestamp": str
            }
        """
        self.rate_limiters["google_news"].wait_if_needed()
        
        try:
            query = quote(f"{entity_id} entity")
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries[:limit]:
                articles.append({
                    "title": entry.title,
                    "summary": entry.get("summary", ""),
                    "link": entry.link,
                    "published": entry.get("published", ""),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                })
            
            result = {
                "entity_id": entity_id,
                "articles": articles,
                "source": "google_news",
                "timestamp": datetime.now().isoformat()
            }
            
            self.fetch_stats["google_news"]["success"] += 1
            self.fetch_stats["google_news"]["total_records"] += len(articles)
            logger.info(f"✅ [google_news] Fetched {entity_id}: {len(articles)} articles")
            return result
            
        except Exception as e:
            self.fetch_stats["google_news"]["failed"] += 1
            logger.error(f"❌ [google_news] Failed to fetch {entity_id}: {e}")
            return {
                "entity_id": entity_id,
                "error": str(e),
                "articles": [],
                "source": "google_news",
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_fred_data(self, series_id: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch macro data from FRED API.
        
        Args:
            series_id: FRED series ID (e.g., "CPIAUCSL", "FEDFUNDS", "VIXCLS")
            start_date: Start date in YYYY-MM-DD format
        
        Returns:
            {
                "series_id": str,
                "observations": list[dict],
                "source": "fred",
                "timestamp": str
            }
        """
        self.rate_limiters["fred"].wait_if_needed()
        
        try:
            import requests
            
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            fred_api_key = os.getenv("FRED_API_KEY")
            if not fred_api_key:
                raise ValueError("FRED_API_KEY not found in .env")
            
            params = {
                "series_id": series_id,
                "api_key": fred_api_key,
                "file_type": "json",
                "observation_start": start_date
            }
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            observations = []
            
            for obs in data.get("observations", []):
                if obs["value"] != ".":
                    observations.append({
                        "date": obs["date"],
                        "value": float(obs["value"])
                    })
            
            result = {
                "series_id": series_id,
                "observations": observations,
                "source": "fred",
                "timestamp": datetime.now().isoformat()
            }
            
            self.fetch_stats["fred"]["success"] += 1
            self.fetch_stats["fred"]["total_records"] += len(observations)
            logger.info(f"✅ [fred] Fetched {series_id}: {len(observations)} observations")
            return result
            
        except Exception as e:
            self.fetch_stats["fred"]["failed"] += 1
            logger.error(f"❌ [fred] Failed to fetch {series_id}: {e}")
            return {
                "series_id": series_id,
                "error": str(e),
                "observations": [],
                "source": "fred",
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_batch(
        self,
        entity_ids: List[str],
        sources: List[str] = ["yfinance", "reddit", "google_news"],
        batch_size: int = 10,
        sleep_between_batches: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Fetch data for multiple entity_ids with batching.
        
        Args:
            entity_ids: List of entity_id symbols
            sources: List of data sources to fetch from
            batch_size: Number of entity_ids per batch
            sleep_between_batches: Seconds to sleep between batches
        
        Returns:
            List of raw data dicts
        """
        all_results = []
        
        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i:i + batch_size]
            logger.info(f"📦 Processing batch {i // batch_size + 1}/{(len(entity_ids) - 1) // batch_size + 1}: {batch}")
            
            for entity_id in batch:
                entity_results = {}
                
                if "yfinance" in sources:
                    entity_results["yfinance"] = self.fetch_yfinance_data(entity_id)
                
                if "reddit" in sources:
                    entity_results["reddit"] = self.fetch_reddit_sentiment(entity_id)
                
                if "google_news" in sources:
                    entity_results["google_news"] = self.fetch_google_news(entity_id)
                
                # Publish raw data event
                self.publish_event(
                    event_type="codex.discovered",
                    payload={
                        "entity_id": entity_id,
                        "sources": entity_results,
                        "timestamp": datetime.now().isoformat(),
                        "batch_id": i // batch_size
                    }
                )
                all_results.append(entity_results)
            
            # Sleep between batches to avoid overwhelming APIs
            if i + batch_size < len(entity_ids):
                logger.info(f"⏳ Sleeping {sleep_between_batches}s before next batch...")
                time.sleep(sleep_between_batches)
        
        return all_results
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method (required by BaseHunter).
        
        Kwargs:
            entity_ids: List[str] - EntityIds to fetch
            sources: List[str] - Data sources to use
            batch_size: int - Batch size
            fred_series: List[str] - FRED series to fetch
        """
        entity_ids = kwargs.get("entity_ids", [])
        sources = kwargs.get("sources", ["yfinance", "reddit", "google_news"])
        batch_size = kwargs.get("batch_size", 10)
        fred_series = kwargs.get("fred_series", [])
        
        logger.info(f"🚀 [Tracker] Starting execution: {len(entity_ids)} entity_ids, sources={sources}")
        
        # Fetch entity_id data
        results = []
        if entity_ids:
            results = self.fetch_batch(
                entity_ids=entity_ids,
                sources=sources,
                batch_size=batch_size
            )
        
        # Fetch FRED data separately
        fred_results = []
        if "fred" in sources and fred_series:
            for series_id in fred_series:
                fred_data = self.fetch_fred_data(series_id)
                fred_results.append(fred_data)
                
                # Publish FRED event
                self.publish_event(
                    event_type="codex.discovered.macro",
                    payload={
                        **fred_data,
                        "series_id": series_id
                    }
                )
        
        # Flush remaining events
        self.flush_events()
        
        # Log to backfill history
        total_records = sum(s["total_records"] for s in self.fetch_stats.values())
        total_success = sum(s["success"] for s in self.fetch_stats.values())
        total_failed = sum(s["failed"] for s in self.fetch_stats.values())
        
        self.log_event(
            event_type="expedition.fetch.completed",
            payload={
                "operation_type": "fetch",
                "records_processed": total_success + total_failed,
                "records_succeeded": total_success,
                "records_failed": total_failed,
                "sources": sources,
                "entities_count": len(entity_ids),
                "fetch_stats": self.fetch_stats
            },
            severity="info"
        )
        
        logger.info(f"✅ [Tracker] Completed: {total_records} records, {total_success} success, {total_failed} failed")
        
        return {
            "status": "completed",
            "total_records": total_records,
            "fetch_stats": self.fetch_stats,
            "entity_results": results,
            "fred_results": fred_results
        }


# CLI Test
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tracker CLI")
    parser.add_argument("--entity_ids", nargs="+", default=["EXAMPLE_ENTITY_1", "EXAMPLE_ENTITY_4"], help="EntityIds to fetch")
    parser.add_argument("--sources", nargs="+", default=["yfinance", "reddit", "google_news"],
                       choices=["yfinance", "reddit", "google_news", "fred"])
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size")
    parser.add_argument("--fred-series", nargs="+", default=[], help="FRED series IDs")
    
    args = parser.parse_args()
    
    with Tracker() as agent:
        result = agent.execute(
            entity_ids=args.entity_ids,
            sources=args.sources,
            batch_size=args.batch_size,
            fred_series=args.fred_series
        )
        
        print("\n" + "="*60)
        print("FETCH STATISTICS")
        print("="*60)
        for source, stats in result["fetch_stats"].items():
            print(f"{source:15} → {stats['success']:3} success, {stats['failed']:3} failed, {stats['total_records']:5} records")
        print("="*60)
