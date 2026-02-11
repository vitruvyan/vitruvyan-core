# services/api_mcp/tools/sentiment.py
"""Sentiment query tool executor."""

import logging
from typing import Dict, Any
from core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


async def execute_query_sentiment(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute query_sentiment tool via PostgreSQL."""
    entity_id = args.get("entity_id")
    days = args.get("days", 7)
    include_phrases = args.get("include_phrases", True)
    
    logger.info(f"💭 Executing query_sentiment: entity_id={entity_id}, days={days}")
    
    try:
        pg = PostgresAgent()
        
        with pg.connection.cursor() as cur:
            cur.execute("""
                SELECT AVG(combined_score) as avg_sentiment, COUNT(*) as samples, MAX(created_at) as latest_timestamp
                FROM sentiment_scores
                WHERE entity_id = %s AND created_at >= NOW() - INTERVAL '%s days'
            """, (entity_id, days))
            
            row = cur.fetchone()
            
            if row and row[0] is not None:
                avg_sentiment = float(row[0])
                samples = int(row[1])
                latest_timestamp = row[2]
                
                trend = "positive" if avg_sentiment > 0.3 else ("negative" if avg_sentiment < -0.3 else "neutral")
                
                cur.execute("""
                    SELECT combined_score, sentiment_tag FROM sentiment_scores
                    WHERE entity_id = %s ORDER BY created_at DESC LIMIT 1
                """, (entity_id,))
                
                latest_row = cur.fetchone()
                latest_score = float(latest_row[0]) if latest_row else 0.0
                latest_tag = latest_row[1] if latest_row else "neutral"
                
                phrases = []
                if include_phrases:
                    phrases = [
                        f"Positive outlook on {entity_id}",
                        f"{entity_id} showing strong performance",
                        f"Market sentiment favors {entity_id}"
                    ]
                
                return {
                    "entity_id": entity_id,
                    "avg_sentiment": round(avg_sentiment, 3),
                    "trend": trend,
                    "samples": samples,
                    "latest_score": round(latest_score, 3),
                    "latest_tag": latest_tag,
                    "phrases": phrases if include_phrases else [],
                    "days_analyzed": days,
                    "latest_timestamp": latest_timestamp.isoformat() if latest_timestamp else None
                }
            else:
                logger.warning(f"No sentiment data found for {entity_id} in last {days} days")
                return {
                    "entity_id": entity_id,
                    "avg_sentiment": 0.0,
                    "trend": "unknown",
                    "samples": 0,
                    "latest_score": 0.0,
                    "latest_tag": "unknown",
                    "phrases": [],
                    "days_analyzed": days,
                    "latest_timestamp": None,
                    "message": f"No sentiment data found for {entity_id} in last {days} days"
                }
                
    except Exception as e:
        logger.error(f"Error querying sentiment for {entity_id}: {str(e)}")
        raise
