# services/api_mcp/middleware.py
"""Sacred Orders Middleware for MCP tool calls."""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from redis import Redis
from prometheus_client import Counter

from .config import get_config
from core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)

# Prometheus metrics
mcp_orthodoxy_validations = Counter(
    'vitruvyan_mcp_orthodoxy_validations_total',
    'Orthodoxy Wardens validations',
    ['tool', 'status']
)

_redis_client: Redis = None


def get_redis() -> Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        config = get_config()
        try:
            _redis_client = Redis(host=config.redis.host, port=config.redis.port, decode_responses=True)
            _redis_client.ping()
            logger.info(f"✅ Redis connected: {config.redis.host}:{config.redis.port}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            _redis_client = None
    return _redis_client


async def sacred_orders_middleware(
    tool_name: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    user_id: str,
    conclave_id: str
) -> str:
    """
    Sacred Orders Middleware - ALL MCP tool calls pass through this.
    
    Returns: orthodoxy_status: "blessed" | "purified" | "heretical"
    """
    logger.info(f"🏛️ Sacred Orders Middleware: {tool_name} (conclave_id={conclave_id})")
    
    # 1. Synaptic Conclave orchestration
    redis_client = get_redis()
    if redis_client:
        try:
            redis_client.publish("conclave.mcp.request", json.dumps({
                "conclave_id": conclave_id, "tool": tool_name, "args": args,
                "user_id": user_id, "timestamp": datetime.utcnow().isoformat()
            }))
        except Exception as e:
            logger.error(f"⚠️ Redis publish failed: {e}")
    
    # 2. Orthodoxy Wardens validation
    orthodoxy_status = "blessed"
    
    try:
        if tool_name == "screen_entities":
            for entity_data in result.get("data", {}).get("entity_ids", []):
                z_scores = entity_data.get("z_scores", {})
                for factor, z in z_scores.items():
                    if z is not None and (z < -3 or z > 3):
                        logger.warning(f"⚠️ Outlier: {factor}={z:.3f} for {entity_data.get('entity_id')}")
                        if orthodoxy_status == "blessed":
                            orthodoxy_status = "purified"
                
                composite = entity_data.get("composite_score", 0)
                if composite < -5 or composite > 5:
                    logger.warning(f"⚠️ Extreme composite={composite:.3f} for {entity_data.get('entity_id')}")
                    if orthodoxy_status == "blessed":
                        orthodoxy_status = "purified"
        
        elif tool_name == "generate_vee_summary":
            word_count = result.get("data", {}).get("word_count", 0)
            if word_count < 100 or word_count > 200:
                logger.warning(f"⚠️ VEE word count {word_count} out of range")
                orthodoxy_status = "purified"
        
        mcp_orthodoxy_validations.labels(tool=tool_name, status=orthodoxy_status).inc()
        logger.info(f"✅ Orthodoxy Wardens: {orthodoxy_status}")
    
    except ValueError as e:
        logger.error(f"❌ Orthodoxy Wardens rejected: {e}")
        raise
    
    # 3. Vault Keepers archiving (PostgreSQL audit trail)
    try:
        pg = PostgresAgent()
        with pg.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO mcp_tool_calls (conclave_id, tool_name, args, result, orthodoxy_status, user_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (conclave_id, tool_name, json.dumps(args), json.dumps(result), orthodoxy_status, user_id, datetime.utcnow()))
        pg.connection.commit()
        logger.info(f"🏰 Vault Keepers: Archived {tool_name} (conclave={conclave_id})")
    except Exception as e:
        logger.error(f"❌ Vault Keepers archiving failed: {e}")
    
    return orthodoxy_status
