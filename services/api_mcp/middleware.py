# services/api_mcp/middleware.py
"""Sacred Orders Middleware for MCP tool calls."""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from prometheus_client import Counter

from config import get_config
from core.validation import (
    validate_factor_scores,
    validate_composite_score,
    validate_summary_length,
    aggregate_validation_results
)
from core.models import ValidationStatus
from core.agents.postgres_agent import PostgresAgent
from core.synaptic_conclave.transport.streams import StreamBus

logger = logging.getLogger(__name__)

# Prometheus metrics
mcp_orthodoxy_validations = Counter(
    'vitruvyan_mcp_orthodoxy_validations_total',
    'Orthodoxy Wardens validations',
    ['tool', 'status']
)

_stream_bus: StreamBus = None


def get_stream_bus() -> StreamBus:
    """Get or create StreamBus client (Synaptic Conclave integration)."""
    global _stream_bus
    if _stream_bus is None:
        config = get_config()
        try:
            _stream_bus = StreamBus(
                host=config.redis.host,
                port=config.redis.port
            )
            logger.info(f"✅ StreamBus connected: {config.redis.host}:{config.redis.port}")
        except Exception as e:
            logger.error(f"❌ StreamBus connection failed: {e}")
            _stream_bus = None
    return _stream_bus


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
    
    config = get_config()
    validation_results = []
    
    # 1. Synaptic Conclave orchestration (StreamBus, NOT Pub/Sub)
    bus = get_stream_bus()
    if bus:
        try:
            # FIXED: Use correct channel "conclave.mcp.actions" (consumed by Synaptic Conclave)
            bus.emit("conclave.mcp.actions", {
                "conclave_id": conclave_id,
                "tool": tool_name,
                "args": args,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            logger.debug(f"📡 StreamBus emit → conclave.mcp.actions")
        except Exception as e:
            logger.error(f"⚠️ StreamBus emit failed: {e}")
    
    # 2. Orthodoxy Wardens validation (config-driven, domain-agnostic)
    try:
        if tool_name == "screen_entities":
            # Validate factor scores (generic, not finance-specific)
            for entity_data in result.get("data", {}).get("entity_ids", []):
                z_scores = entity_data.get("z_scores", {})
                
                # Config-driven validation (no hardcoded ±3, ±5)
                factor_validation = validate_factor_scores(
                    factors=z_scores,
                    z_threshold=config.validation.z_score_threshold,
                    entity_id=entity_data.get("entity_id")
                )
                validation_results.append(factor_validation)
                
                # Composite score validation
                composite = entity_data.get("composite_score")
                if composite is not None:
                    composite_validation = validate_composite_score(
                        composite=composite,
                        composite_threshold=config.validation.composite_threshold,
                        entity_id=entity_data.get("entity_id")
                    )
                    validation_results.append(composite_validation)
        
        elif tool_name == "generate_vee_summary":
            # Generic summary length validation (not VEE-specific)
            word_count = result.get("data", {}).get("word_count", 0)
            summary_validation = validate_summary_length(
                word_count=word_count,
                min_words=config.validation.min_summary_words,
                max_words=config.validation.max_summary_words,
                summary_id=conclave_id
            )
            validation_results.append(summary_validation)
        
        # Aggregate all validation results
        final_validation = aggregate_validation_results(validation_results)
        orthodoxy_status = final_validation.status.value  # "blessed" | "purified" | "heretical"
        
        mcp_orthodoxy_validations.labels(tool=tool_name, status=orthodoxy_status).inc()
        logger.info(f"✅ Orthodoxy Wardens: {orthodoxy_status} ({len(final_validation.warnings)} warnings)")
    
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
