# core/agents/codex_hunters/restorer.py
"""
🔧 THE RESTORER - Codex Restoration Agent
==========================================
Restores damaged and corrupted codices to their original glory.

Like medieval manuscript restorers who cleaned palimpsests and repaired
damaged pages, The Restorer deduplicates, validates, and normalizes
discovered financial data.

Listens to CodexEvent(type="codex.discovered"), 
Publishes CodexEvent(type="page.restored")
"""

import hashlib
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import numpy as np

from core.governance.codex_hunters.hunter import (
    BaseHunter,
    CodexEvent
)

logger = logging.getLogger(__name__)


class Restorer(BaseHunter):
    """
    Data cleaning and normalization engine.
    
    Features:
    - Hash-based deduplication
    - Missing field imputation
    - Z-score normalization for sentiment scores
    - Text cleaning (URLs, special chars, whitespace)
    - Sentiment tag validation
    - Outlier detection and capping
    """
    
    def __init__(self):
        super().__init__("Restorer")
        
        # Deduplication cache (ticker -> set of hashes)
        self.seen_hashes: Dict[str, set] = defaultdict(set)
        
        # Track normalization statistics
        self.norm_stats = {
            "total_records": 0,
            "duplicates_removed": 0,
            "fields_imputed": 0,
            "outliers_capped": 0,
            "text_cleaned": 0,
            "normalized": 0,
        }
        
        # Sentiment score distribution for z-score
        self.sentiment_scores: List[float] = []
    
    def compute_hash(self, data: Dict[str, Any], fields: List[str]) -> str:
        """
        Compute deterministic hash from selected fields.
        
        Args:
            data: Data dictionary
            fields: Fields to include in hash
        
        Returns:
            32-char hex hash
        """
        hash_input = ""
        for field in fields:
            value = data.get(field, "")
            hash_input += str(value)
        
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def is_duplicate(self, ticker: str, record_hash: str) -> bool:
        """Check if record hash is already seen for this ticker"""
        if record_hash in self.seen_hashes[ticker]:
            return True
        self.seen_hashes[ticker].add(record_hash)
        return False
    
    def clean_text(self, text: str) -> str:
        """
        Clean text from markdown, URLs, special characters.
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove Reddit markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        
        # Remove Reddit links
        text = re.sub(r'/u/\w+', '', text)
        text = re.sub(r'/r/\w+', '', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters (keep letters, numbers, basic punctuation)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text
    
    def validate_sentiment_tag(self, tag: str) -> str:
        """
        Validate and normalize sentiment tag.
        
        Args:
            tag: Raw sentiment tag
        
        Returns:
            Normalized tag (BULLISH, BEARISH, NEUTRAL)
        """
        if not tag:
            return "NEUTRAL"
        
        tag_upper = tag.upper()
        
        if tag_upper in ["BULLISH", "POSITIVE", "BUY", "STRONG_BUY"]:
            return "BULLISH"
        elif tag_upper in ["BEARISH", "NEGATIVE", "SELL", "STRONG_SELL"]:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def normalize_sentiment_score(self, score: float, method: str = "clip") -> float:
        """
        Normalize sentiment score to [-1, 1] range.
        
        Args:
            score: Raw sentiment score
            method: "clip" or "zscore"
        
        Returns:
            Normalized score
        """
        if method == "clip":
            # Simple clipping to [-1, 1]
            return max(-1.0, min(1.0, score))
        
        elif method == "zscore":
            # Z-score normalization (if we have enough data)
            if len(self.sentiment_scores) < 10:
                return self.normalize_sentiment_score(score, method="clip")
            
            mean = np.mean(self.sentiment_scores)
            std = np.std(self.sentiment_scores)
            
            if std == 0:
                return 0.0
            
            z_score = (score - mean) / std
            # Map z-score to [-1, 1] using tanh
            return float(np.tanh(z_score))
        
        return score
    
    def impute_missing_fields(self, data: Dict[str, Any], field_defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill missing fields with defaults or computed values.
        
        Args:
            data: Record with potentially missing fields
            field_defaults: Default values for missing fields
        
        Returns:
            Record with imputed fields
        """
        imputed_count = 0
        
        for field, default_value in field_defaults.items():
            if field not in data or data[field] is None:
                data[field] = default_value
                imputed_count += 1
        
        if imputed_count > 0:
            self.norm_stats["fields_imputed"] += imputed_count
        
        return data
    
    def normalize_yfinance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize yfinance data structure.
        
        Args:
            data: Raw yfinance data
        
        Returns:
            Normalized data
        """
        if "error" in data:
            return data  # Don't normalize error responses
        
        ticker = data.get("ticker", "UNKNOWN")
        
        # Deduplicate history records
        history = data.get("history", [])
        unique_history = []
        
        for record in history:
            record_hash = self.compute_hash(record, ["date", "close"])
            if not self.is_duplicate(f"{ticker}_history", record_hash):
                unique_history.append(record)
            else:
                self.norm_stats["duplicates_removed"] += 1
        
        # Impute missing info fields
        info = data.get("info", {})
        info = self.impute_missing_fields(info, {
            "name": ticker,
            "sector": "Unknown",
            "industry": "Unknown",
            "market_cap": None,
            "pe_ratio": None,
            "dividend_yield": None,
        })
        
        normalized = {
            "ticker": ticker,
            "info": info,
            "history": unique_history,
            "source": "yfinance",
            "normalized_at": datetime.now().isoformat()
        }
        
        self.norm_stats["normalized"] += 1
        return normalized
    
    def normalize_reddit_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Reddit data structure.
        
        Args:
            data: Raw Reddit data
        
        Returns:
            Normalized data
        """
        if "error" in data:
            return data
        
        ticker = data.get("ticker", "UNKNOWN")
        posts = data.get("posts", [])
        
        # Clean and deduplicate posts
        unique_posts = []
        
        for post in posts:
            # Clean text fields
            post["title"] = self.clean_text(post.get("title", ""))
            post["selftext"] = self.clean_text(post.get("selftext", ""))
            
            # Compute hash
            record_hash = self.compute_hash(post, ["title", "created_utc"])
            
            if not self.is_duplicate(f"{ticker}_reddit", record_hash):
                # Impute missing fields
                post = self.impute_missing_fields(post, {
                    "subreddit": "unknown",
                    "score": 0,
                    "num_comments": 0,
                })
                unique_posts.append(post)
                self.norm_stats["text_cleaned"] += 1
            else:
                self.norm_stats["duplicates_removed"] += 1
        
        normalized = {
            "ticker": ticker,
            "posts": unique_posts,
            "source": "reddit",
            "normalized_at": datetime.now().isoformat()
        }
        
        self.norm_stats["normalized"] += 1
        return normalized
    
    def normalize_google_news_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Google News data structure.
        
        Args:
            data: Raw Google News data
        
        Returns:
            Normalized data
        """
        if "error" in data:
            return data
        
        ticker = data.get("ticker", "UNKNOWN")
        articles = data.get("articles", [])
        
        # Clean and deduplicate articles
        unique_articles = []
        
        for article in articles:
            # Clean text fields
            article["title"] = self.clean_text(article.get("title", ""))
            article["summary"] = self.clean_text(article.get("summary", ""))
            
            # Compute hash
            record_hash = self.compute_hash(article, ["title", "link"])
            
            if not self.is_duplicate(f"{ticker}_news", record_hash):
                # Impute missing fields
                article = self.impute_missing_fields(article, {
                    "source": "Unknown",
                    "published": datetime.now().isoformat(),
                })
                unique_articles.append(article)
                self.norm_stats["text_cleaned"] += 1
            else:
                self.norm_stats["duplicates_removed"] += 1
        
        normalized = {
            "ticker": ticker,
            "articles": unique_articles,
            "source": "google_news",
            "normalized_at": datetime.now().isoformat()
        }
        
        self.norm_stats["normalized"] += 1
        return normalized
    
    def normalize_sentiment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize sentiment scores and tags.
        
        Args:
            data: Sentiment data with scores and tags
        
        Returns:
            Normalized sentiment data
        """
        ticker = data.get("ticker", "UNKNOWN")
        
        # Extract scores
        reddit_score = data.get("reddit_score")
        google_score = data.get("google_score")
        combined_score = data.get("combined_score")
        
        # Normalize scores
        if reddit_score is not None:
            reddit_score = self.normalize_sentiment_score(reddit_score)
            self.sentiment_scores.append(reddit_score)
        
        if google_score is not None:
            google_score = self.normalize_sentiment_score(google_score)
            self.sentiment_scores.append(google_score)
        
        if combined_score is not None:
            combined_score = self.normalize_sentiment_score(combined_score)
            self.sentiment_scores.append(combined_score)
        
        # Validate sentiment tag
        sentiment_tag = self.validate_sentiment_tag(data.get("sentiment_tag", ""))
        
        normalized = {
            "ticker": ticker,
            "reddit_score": reddit_score,
            "google_score": google_score,
            "combined_score": combined_score,
            "sentiment_tag": sentiment_tag,
            "reddit_titles": data.get("reddit_titles", []),
            "google_titles": data.get("google_titles", []),
            "source": "sentiment",
            "normalized_at": datetime.now().isoformat()
        }
        
        self.norm_stats["normalized"] += 1
        return normalized
    
    def normalize_batch(self, raw_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a batch of raw data records.
        
        Args:
            raw_data_list: List of raw data dicts from FetcherAgent
        
        Returns:
            List of normalized data dicts
        """
        normalized_results = []
        
        for raw_data in raw_data_list:
            self.norm_stats["total_records"] += 1
            
            # Route to appropriate normalizer based on source
            source = raw_data.get("source")
            
            if source == "yfinance":
                normalized = self.normalize_yfinance_data(raw_data)
            elif source == "reddit":
                normalized = self.normalize_reddit_data(raw_data)
            elif source == "google_news":
                normalized = self.normalize_google_news_data(raw_data)
            elif source == "sentiment":
                normalized = self.normalize_sentiment_data(raw_data)
            else:
                logger.warning(f"⚠️ Unknown source: {source}, skipping normalization")
                normalized = raw_data
            
            normalized_results.append(normalized)
            
            # Publish normalized event
            self.publish_event(
                event_type="page.restored",
                payload={
                    **normalized,
                    "original_source": source
                }
            )
        
        return normalized_results
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method (required by BaseHunter).
        
        Kwargs:
            raw_data: List[Dict] - Raw data from FetcherAgent
        """
        raw_data = kwargs.get("raw_data", [])
        
        logger.info(f"🚀 [Restorer] Starting execution: {len(raw_data)} records")
        
        # Normalize batch
        normalized_results = self.normalize_batch(raw_data)
        
        # Flush events
        self.flush_events()
        
        # Log to backfill history
        self.log_event(
            event_type="expedition.normalize.completed",
            payload={
                "operation_type": "normalize",
                "records_processed": self.norm_stats["total_records"],
                "records_succeeded": self.norm_stats["normalized"],
                "records_failed": self.norm_stats["total_records"] - self.norm_stats["normalized"],
                "statistics": self.norm_stats
            },
            severity="info"
        )
        
        logger.info(f"✅ [Restorer] Completed: {self.norm_stats['normalized']} normalized, "
                   f"{self.norm_stats['duplicates_removed']} duplicates removed, "
                   f"{self.norm_stats['fields_imputed']} fields imputed")
        
        return {
            "status": "completed",
            "normalized_results": normalized_results,
            "statistics": self.norm_stats
        }


# CLI Test
if __name__ == "__main__":
    import json
    
    # Sample raw data for testing
    sample_raw_data = [
        {
            "ticker": "AAPL",
            "info": {"name": "Apple Inc.", "sector": "Technology"},
            "history": [
                {"date": "2025-10-01", "close": 150.0},
                {"date": "2025-10-01", "close": 150.0},  # Duplicate
            ],
            "source": "yfinance",
            "timestamp": datetime.now().isoformat()
        },
        {
            "ticker": "AAPL",
            "posts": [
                {
                    "title": "**AAPL** to the moon! http://spam.com",
                    "selftext": "Great   stock   with /u/user mention",
                    "score": 100,
                    "created_utc": datetime.now().isoformat()
                }
            ],
            "source": "reddit",
            "timestamp": datetime.now().isoformat()
        },
        {
            "ticker": "AAPL",
            "reddit_score": 0.8,
            "google_score": 0.6,
            "combined_score": 0.7,
            "sentiment_tag": "positive",
            "source": "sentiment"
        }
    ]
    
    with Restorer() as agent:
        result = agent.execute(raw_data=sample_raw_data)
        
        print("\n" + "="*60)
        print("NORMALIZATION STATISTICS")
        print("="*60)
        for key, value in result["statistics"].items():
            print(f"{key:25} → {value}")
        print("="*60)
        
        print("\nNormalized Results:")
        print(json.dumps(result["normalized_results"], indent=2))
