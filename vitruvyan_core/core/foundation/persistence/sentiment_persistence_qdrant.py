"""
🎭 Sentiment Persistence with Qdrant Integration (Dual-Memory Pattern)

Sacred Orders: Memory Order
Extends sentiment persistence to add Qdrant vector storage.

Architecture:
1. Store sentiment score in PostgreSQL (via PostgresAgent)
2. Generate embedding for sentiment text (via vitruvyan_api_embedding)
3. Store vector in Qdrant phrases_fused and sentiment_embeddings collections

Collections:
- phrases_fused: Babel Gardens fusion results (semantic + affective)
- sentiment_embeddings: Pure sentiment vectors for similarity search
"""

import httpx
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .postgres_agent import PostgresAgent
from .qdrant_agent import QdrantAgent

logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_API_URL = "http://localhost:8010"  # vitruvyan_api_embedding
VECTOR_SIZE = 384


def save_sentiment_dual(
    ticker: str,
    combined_score: float,
    sentiment_tag: str,
    user_text: str = "",
    confidence: float = 0.0,
    fusion_boost: float = 0.0,
    embedding_used: bool = False
) -> bool:
    """
    Dual-memory sentiment storage: PostgreSQL + Qdrant.
    
    Flow:
    1. Store in PostgreSQL via PostgresAgent.insert_sentiment()
    2. Generate embedding from user text + ticker context
    3. Upsert to Qdrant phrases_fused collection (Babel fusion)
    4. Upsert to Qdrant sentiment_embeddings collection (pure sentiment)
    
    Args:
        ticker: Stock ticker symbol
        combined_score: Sentiment score (-1.0 to 1.0)
        sentiment_tag: Sentiment label ("positive", "negative", "neutral")
        user_text: Original user input text for semantic embedding
        confidence: Babel Gardens confidence score
        fusion_boost: Fusion algorithm boost value
        embedding_used: Whether Babel Gardens used embedding
    
    Returns:
        True if all writes succeeded, False otherwise
    """
    try:
        # STEP 1: PostgreSQL write
        pg = PostgresAgent()
        pg.insert_sentiment(
            ticker=ticker,
            reddit=None,  # Unified score from Babel Gardens
            google=None,
            combined=combined_score,
            tag=sentiment_tag,
            reddit_titles=None,
            google_titles=None
        )
        logger.debug(f"✅ PostgreSQL write completed for {ticker}")
        
        # STEP 2: Generate embedding
        if not user_text:
            user_text = f"{ticker} stock sentiment analysis"
        
        embedding_text = _create_sentiment_embedding_text(
            ticker, sentiment_tag, combined_score, user_text
        )
        embedding = _generate_embedding(embedding_text)
        
        if not embedding:
            logger.warning(f"⚠️ Embedding generation failed for {ticker}, skipping Qdrant")
            return False
        
        # STEP 3: Qdrant writes (2 collections)
        success_fused = _upsert_to_phrases_fused(
            ticker, sentiment_tag, combined_score, user_text,
            confidence, fusion_boost, embedding_used, embedding
        )
        
        success_sentiment = _upsert_to_sentiment_embeddings(
            ticker, sentiment_tag, combined_score, embedding
        )
        
        if success_fused and success_sentiment:
            logger.info(f"✅ Dual-memory write completed for {ticker} (PostgreSQL + 2x Qdrant)")
            return True
        else:
            logger.warning(f"⚠️ Partial Qdrant write for {ticker}, PostgreSQL write still succeeded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Dual-memory sentiment storage failed for {ticker}: {e}", exc_info=True)
        return False


def _create_sentiment_embedding_text(
    ticker: str,
    sentiment_tag: str,
    score: float,
    user_text: str
) -> str:
    """
    Create semantic text for sentiment embedding.
    
    Combines user input with sentiment analysis results for rich vector representation.
    
    Args:
        ticker: Stock ticker
        sentiment_tag: "positive", "negative", "neutral"
        score: Sentiment score (-1.0 to 1.0)
        user_text: Original user input
    
    Returns:
        Text for embedding generation
    """
    sentiment_desc = f"{sentiment_tag} sentiment"
    
    if score > 0.5:
        sentiment_desc = "strongly " + sentiment_desc
    elif score < -0.5:
        sentiment_desc = "strongly " + sentiment_desc
    
    return f"Ticker: {ticker}, {sentiment_desc} (score: {score:.2f}). Context: {user_text}"


def _generate_embedding(text: str) -> Optional[list]:
    """
    Generate embedding via vitruvyan_api_embedding:8010.
    
    Args:
        text: Text to embed
    
    Returns:
        384-dim vector or None if failed
    """
    try:
        response = httpx.post(
            f"{EMBEDDING_API_URL}/v1/embeddings/create",
            json={"text": text},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding")
            
            if embedding and len(embedding) == VECTOR_SIZE:
                return embedding
            else:
                logger.warning(f"Invalid embedding size: {len(embedding) if embedding else 0}")
                return None
        else:
            logger.error(f"Embedding API error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


def _upsert_to_phrases_fused(
    ticker: str,
    sentiment_tag: str,
    score: float,
    user_text: str,
    confidence: float,
    fusion_boost: float,
    embedding_used: bool,
    embedding: list
) -> bool:
    """
    Upsert to Qdrant phrases_fused collection (Babel Gardens fusion results).
    
    This collection stores the unified semantic + affective representation
    from Babel Gardens fusion algorithm.
    """
    try:
        qdrant = QdrantAgent()
        
        # Point ID: hash of ticker + date for daily deduplication
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ticker}_sentiment_{datetime.now().date()}"))
        
        payload = {
            "ticker": ticker,
            "sentiment_tag": sentiment_tag,
            "sentiment_score": score,
            "user_text": user_text[:500],  # Truncate long texts
            "confidence": confidence,
            "fusion_boost": fusion_boost,
            "embedding_used": embedding_used,
            "source": "babel_gardens_fusion",
            "timestamp": datetime.now().isoformat(),
            "data_type": "sentiment_fused"
        }
        
        points = [{
            "id": point_id,
            "vector": embedding,
            "payload": payload
        }]
        
        qdrant.upsert("phrases_fused", points)
        logger.debug(f"✅ phrases_fused upsert completed for {ticker}")
        return True
        
    except Exception as e:
        logger.error(f"phrases_fused upsert failed for {ticker}: {e}", exc_info=True)
        return False


def _upsert_to_sentiment_embeddings(
    ticker: str,
    sentiment_tag: str,
    score: float,
    embedding: list
) -> bool:
    """
    Upsert to Qdrant sentiment_embeddings collection (pure sentiment vectors).
    
    This collection stores simplified sentiment representations
    for quick similarity searches.
    """
    try:
        qdrant = QdrantAgent()
        
        # Point ID: hash of ticker + date for daily deduplication
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ticker}_pure_sentiment_{datetime.now().date()}"))
        
        payload = {
            "ticker": ticker,
            "sentiment_tag": sentiment_tag,
            "sentiment_score": score,
            "timestamp": datetime.now().isoformat(),
            "data_type": "pure_sentiment"
        }
        
        points = [{
            "id": point_id,
            "vector": embedding,
            "payload": payload
        }]
        
        qdrant.upsert("sentiment_embeddings", points)
        logger.debug(f"✅ sentiment_embeddings upsert completed for {ticker}")
        return True
        
    except Exception as e:
        logger.error(f"sentiment_embeddings upsert failed for {ticker}: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Test dual-memory sentiment storage
    logging.basicConfig(level=logging.INFO)
    
    success = save_sentiment_dual(
        ticker="AAPL",
        combined_score=0.75,
        sentiment_tag="positive",
        user_text="Apple stock showing strong growth with new product launches",
        confidence=0.85,
        fusion_boost=0.12,
        embedding_used=True
    )
    
    print(f"\n🎭 Dual-memory sentiment test result: {'SUCCESS' if success else 'FAILED'}")
