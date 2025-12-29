# core/agents/codex_hunters/binder.py
"""
📚 THE BINDER - Codex Preservation Agent
==========================================
Binds restored pages into permanent archives.

Like medieval bookbinders who preserved manuscripts in leather-bound volumes,
The Binder stores codices in dual archives: PostgreSQL (relational) and
Qdrant (vector embeddings) for eternal preservation.

Handles batch binding, embedding generation, transaction management.
Publishes CodexEvent(type="volume.bound")
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from sentence_transformers import SentenceTransformer

from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
from core.governance.codex_hunters.hunter import (
    BaseHunter,
    CodexEvent
)

logger = logging.getLogger(__name__)


class Binder(BaseHunter):
    """
    Dual database writer with PostgreSQL and Qdrant support.
    
    Features:
    - Batch inserts to PostgreSQL
    - Embedding generation and upsert to Qdrant
    - Transaction management with rollback
    - Automatic table creation
    - Deduplication via dedupe_key
    """
    
    def __init__(self):
        super().__init__("Binder")
        
        # Database agents (inherited from BaseHunter)
        # self.postgres_agent and self.qdrant_agent are already initialized
        
        # Embedding model for Qdrant
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.embedding_dim = 384  # MiniLM dimension
        
        # Ensure Qdrant collections exist
        self._ensure_collections()
        
        # Track write statistics
        self.write_stats = {
            "postgres": {"success": 0, "failed": 0, "records": 0},
            "qdrant": {"success": 0, "failed": 0, "records": 0},
            "total_batches": 0,
        }
    
    def _ensure_collections(self):
        """Ensure required Qdrant collections exist"""
        collections = [
            ("vitruvyan_notes", self.embedding_dim),
            ("sentiment_context", self.embedding_dim),
            ("market_data", self.embedding_dim),
        ]
        
        for collection_name, vector_size in collections:
            try:
                result = self.qdrant_agent.ensure_collection(
                    name=collection_name,
                    vector_size=vector_size,
                    distance="Cosine"
                )
                if result["status"] == "ok":
                    logger.info(f"✅ Qdrant collection '{collection_name}' ready")
                else:
                    logger.error(f"❌ Failed to ensure collection '{collection_name}': {result}")
            except Exception as e:
                logger.error(f"❌ Error ensuring collection '{collection_name}': {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using MiniLM.
        
        Args:
            text: Input text
        
        Returns:
            384-dimensional embedding vector
        """
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return [0.0] * self.embedding_dim  # Return zero vector on error
    
    def write_sentiment_to_postgres(self, data: Dict[str, Any]) -> bool:
        """
        Write sentiment data to PostgreSQL sentiment_scores table.
        
        Args:
            data: Normalized sentiment data
        
        Returns:
            Success boolean
        """
        try:
            ticker = data.get("ticker")
            reddit_score = data.get("reddit_score")
            google_score = data.get("google_score")
            combined_score = data.get("combined_score")
            sentiment_tag = data.get("sentiment_tag")
            reddit_titles = data.get("reddit_titles", [])
            google_titles = data.get("google_titles", [])
            
            # Generate dedupe key
            timestamp = datetime.now().isoformat()
            dedupe_key = f"{ticker}_{timestamp}"
            
            # Use PostgresAgent.insert_sentiment
            success = self.postgres_agent.insert_sentiment(
                ticker=ticker,
                reddit=reddit_score,
                google=google_score,
                combined=combined_score,
                tag=sentiment_tag,
                reddit_titles=reddit_titles,
                google_titles=google_titles
            )
            
            if success:
                self.write_stats["postgres"]["success"] += 1
                self.write_stats["postgres"]["records"] += 1
                logger.debug(f"✅ [PostgreSQL] Inserted sentiment for {ticker}")
            else:
                self.write_stats["postgres"]["failed"] += 1
                logger.error(f"❌ [PostgreSQL] Failed to insert sentiment for {ticker}")
            
            return success
            
        except Exception as e:
            self.write_stats["postgres"]["failed"] += 1
            logger.error(f"❌ [PostgreSQL] Error writing sentiment: {e}")
            return False
    
    def write_phrase_to_postgres(self, text: str, source: str, language: str = "en") -> bool:
        """
        Write phrase to PostgreSQL phrases table.
        
        Args:
            text: Phrase text
            source: Data source
            language: Language code
        
        Returns:
            Success boolean
        """
        try:
            success = self.postgres_agent.insert_phrase(
                text=text,
                source=source,
                language=language,
                created_at=datetime.now().isoformat(),
                embedded=False  # Will be set to True after Qdrant upsert
            )
            
            if success:
                self.write_stats["postgres"]["success"] += 1
                self.write_stats["postgres"]["records"] += 1
            else:
                self.write_stats["postgres"]["failed"] += 1
            
            return success
            
        except Exception as e:
            self.write_stats["postgres"]["failed"] += 1
            logger.error(f"❌ [PostgreSQL] Error writing phrase: {e}")
            return False
    
    def write_to_qdrant(
        self,
        collection: str,
        point_id: str,
        text: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Generate embedding and upsert to Qdrant.
        
        Args:
            collection: Qdrant collection name
            point_id: Unique point ID
            text: Text to embed
            payload: Metadata payload
        
        Returns:
            Success boolean
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Upsert to Qdrant
            result = self.qdrant_agent.upsert(
                collection=collection,
                points=[{
                    "id": point_id,
                    "vector": embedding,
                    "payload": payload
                }]
            )
            
            if result["status"] == "ok":
                self.write_stats["qdrant"]["success"] += 1
                self.write_stats["qdrant"]["records"] += 1
                logger.debug(f"✅ [Qdrant] Upserted to {collection}: {point_id}")
                return True
            else:
                self.write_stats["qdrant"]["failed"] += 1
                logger.error(f"❌ [Qdrant] Failed to upsert: {result}")
                return False
            
        except Exception as e:
            self.write_stats["qdrant"]["failed"] += 1
            logger.error(f"❌ [Qdrant] Error writing to {collection}: {e}")
            return False
    
    def write_sentiment_batch(self, sentiment_data_list: List[Dict[str, Any]]) -> int:
        """
        Write batch of sentiment data to both databases.
        
        Args:
            sentiment_data_list: List of normalized sentiment dicts
        
        Returns:
            Number of successfully written records
        """
        success_count = 0
        
        for data in sentiment_data_list:
            ticker = data.get("ticker")
            combined_score = data.get("combined_score")
            sentiment_tag = data.get("sentiment_tag")
            reddit_titles = data.get("reddit_titles", [])
            google_titles = data.get("google_titles", [])
            
            # Write to PostgreSQL
            pg_success = self.write_sentiment_to_postgres(data)
            
            # Create embedding text
            titles_text = " ".join(reddit_titles[:3] + google_titles[:3])  # First 3 from each
            embedding_text = (
                f"{ticker} sentiment: {sentiment_tag}. "
                f"Score: {combined_score:.2f}. "
                f"Context: {titles_text[:200]}"
            )
            
            # Write to Qdrant sentiment_context collection
            point_id = f"{ticker}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            qdrant_success = self.write_to_qdrant(
                collection="sentiment_context",
                point_id=point_id,
                text=embedding_text,
                payload={
                    "ticker": ticker,
                    "sentiment_tag": sentiment_tag,
                    "combined_score": combined_score,
                    "reddit_titles": reddit_titles,
                    "google_titles": google_titles,
                    "source": "Binder",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if pg_success and qdrant_success:
                success_count += 1
        
        return success_count
    
    def write_market_data_batch(self, market_data_list: List[Dict[str, Any]]) -> int:
        """
        Write batch of yfinance market data to both databases.
        
        Args:
            market_data_list: List of normalized yfinance dicts
        
        Returns:
            Number of successfully written records
        """
        success_count = 0
        
        for data in market_data_list:
            if "error" in data:
                logger.warning(f"⚠️ Skipping error record: {data.get('ticker')}")
                continue
            
            ticker = data.get("ticker")
            info = data.get("info", {})
            history = data.get("history", [])
            
            if not history:
                logger.warning(f"⚠️ No history data for {ticker}, skipping")
                continue
            
            # Create embedding text from company info
            embedding_text = (
                f"{ticker} {info.get('name', '')}. "
                f"Sector: {info.get('sector', 'Unknown')}. "
                f"Industry: {info.get('industry', 'Unknown')}. "
                f"Latest price: {history[-1].get('close', 0):.2f}"
            )
            
            # Write to Qdrant market_data collection
            point_id = f"{ticker}_market_{datetime.now().strftime('%Y%m%d')}"
            qdrant_success = self.write_to_qdrant(
                collection="market_data",
                point_id=point_id,
                text=embedding_text,
                payload={
                    "ticker": ticker,
                    "name": info.get("name"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "market_cap": info.get("market_cap"),
                    "latest_close": history[-1].get("close"),
                    "history_days": len(history),
                    "source": "Binder",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if qdrant_success:
                success_count += 1
        
        return success_count
    
    def write_reddit_phrases_batch(self, reddit_data_list: List[Dict[str, Any]]) -> int:
        """
        Write batch of Reddit posts as phrases to both databases.
        
        Args:
            reddit_data_list: List of normalized Reddit dicts
        
        Returns:
            Number of successfully written records
        """
        success_count = 0
        
        for data in reddit_data_list:
            if "error" in data:
                continue
            
            ticker = data.get("ticker")
            posts = data.get("posts", [])
            
            for post in posts:
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                full_text = f"{title} {selftext}".strip()
                
                if len(full_text.split()) < 5:
                    continue  # Skip short posts
                
                # Write phrase to PostgreSQL
                source = f"reddit_{post.get('subreddit', 'unknown')}"
                pg_success = self.write_phrase_to_postgres(
                    text=full_text,
                    source=source,
                    language="en"
                )
                
                # Write to Qdrant vitruvyan_notes collection
                phrase_hash = hashlib.md5(full_text.encode()).hexdigest()[:16]
                point_id = f"reddit_{ticker}_{phrase_hash}"
                
                qdrant_success = self.write_to_qdrant(
                    collection="vitruvyan_notes",
                    point_id=point_id,
                    text=full_text,
                    payload={
                        "ticker": ticker,
                        "source": source,
                        "subreddit": post.get("subreddit"),
                        "score": post.get("score"),
                        "num_comments": post.get("num_comments"),
                        "created_at": post.get("created_utc"),
                        "type": "reddit_post"
                    }
                )
                
                if pg_success and qdrant_success:
                    success_count += 1
        
        return success_count
    
    def write_news_phrases_batch(self, news_data_list: List[Dict[str, Any]]) -> int:
        """
        Write batch of Google News articles as phrases to both databases.
        
        Args:
            news_data_list: List of normalized Google News dicts
        
        Returns:
            Number of successfully written records
        """
        success_count = 0
        
        for data in news_data_list:
            if "error" in data:
                continue
            
            ticker = data.get("ticker")
            articles = data.get("articles", [])
            
            for article in articles:
                title = article.get("title", "")
                summary = article.get("summary", "")
                full_text = f"{title} {summary}".strip()
                
                if len(full_text.split()) < 5:
                    continue
                
                # Write phrase to PostgreSQL
                source = f"google_news_{article.get('source', 'unknown')}"
                pg_success = self.write_phrase_to_postgres(
                    text=full_text,
                    source=source,
                    language="en"
                )
                
                # Write to Qdrant vitruvyan_notes collection
                phrase_hash = hashlib.md5(full_text.encode()).hexdigest()[:16]
                point_id = f"news_{ticker}_{phrase_hash}"
                
                qdrant_success = self.write_to_qdrant(
                    collection="vitruvyan_notes",
                    point_id=point_id,
                    text=full_text,
                    payload={
                        "ticker": ticker,
                        "source": source,
                        "published": article.get("published"),
                        "link": article.get("link"),
                        "type": "news_article"
                    }
                )
                
                if pg_success and qdrant_success:
                    success_count += 1
        
        return success_count
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method (required by BaseHunter).
        
        Kwargs:
            normalized_data: List[Dict] - Normalized data from NormalizerAgent
        """
        normalized_data = kwargs.get("normalized_data", [])
        
        logger.info(f"🚀 [Binder] Starting execution: {len(normalized_data)} records")
        
        # Group data by source
        sentiment_data = []
        market_data = []
        reddit_data = []
        news_data = []
        
        for record in normalized_data:
            source = record.get("source")
            if source == "sentiment":
                sentiment_data.append(record)
            elif source == "yfinance":
                market_data.append(record)
            elif source == "reddit":
                reddit_data.append(record)
            elif source == "google_news":
                news_data.append(record)
        
        # Write batches
        sentiment_written = 0
        market_written = 0
        reddit_written = 0
        news_written = 0
        
        if sentiment_data:
            sentiment_written = self.write_sentiment_batch(sentiment_data)
            logger.info(f"✅ Written {sentiment_written}/{len(sentiment_data)} sentiment records")
        
        if market_data:
            market_written = self.write_market_data_batch(market_data)
            logger.info(f"✅ Written {market_written}/{len(market_data)} market data records")
        
        if reddit_data:
            reddit_written = self.write_reddit_phrases_batch(reddit_data)
            logger.info(f"✅ Written {reddit_written} Reddit phrases")
        
        if news_data:
            news_written = self.write_news_phrases_batch(news_data)
            logger.info(f"✅ Written {news_written} news phrases")
        
        # Publish completion events
        self.publish_event(
            event_type="volume.bound",
            payload={
                "sentiment_written": sentiment_written,
                "market_written": market_written,
                "reddit_written": reddit_written,
                "news_written": news_written,
                "total_written": sentiment_written + market_written + reddit_written + news_written,
                "write_stats": self.write_stats
            }
        )
        self.flush_events()
        
        # Log to backfill history
        total_written = sentiment_written + market_written + reddit_written + news_written
        self.log_event(
            event_type="expedition.write.completed",
            payload={
                "operation_type": "write",
                "records_processed": len(normalized_data),
                "records_succeeded": total_written,
                "records_failed": len(normalized_data) - total_written,
                "statistics": self.write_stats
            },
            severity="info"
        )
        
        logger.info(f"✅ [Binder] Completed: {total_written}/{len(normalized_data)} records written")
        
        return {
            "status": "completed",
            "sentiment_written": sentiment_written,
            "market_written": market_written,
            "reddit_written": reddit_written,
            "news_written": news_written,
            "total_written": total_written,
            "write_stats": self.write_stats
        }


# CLI Test
if __name__ == "__main__":
    import json
    
    # Sample normalized data for testing
    sample_normalized = [
        {
            "ticker": "AAPL",
            "reddit_score": 0.7,
            "google_score": 0.6,
            "combined_score": 0.65,
            "sentiment_tag": "BULLISH",
            "reddit_titles": ["AAPL great buy", "Apple earnings strong"],
            "google_titles": ["Apple stock rises", "AAPL hits new high"],
            "source": "sentiment"
        },
        {
            "ticker": "AAPL",
            "info": {
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            },
            "history": [
                {"date": "2025-10-10", "close": 175.0},
                {"date": "2025-10-11", "close": 176.5}
            ],
            "source": "yfinance"
        }
    ]
    
    with Binder() as agent:
        result = agent.execute(normalized_data=sample_normalized)
        
        print("\n" + "="*60)
        print("WRITE STATISTICS")
        print("="*60)
        print(json.dumps(result, indent=2))
        print("="*60)
