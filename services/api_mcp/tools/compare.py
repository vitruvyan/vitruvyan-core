# services/api_mcp/tools/compare.py
"""Entity comparison tool executor."""

import logging
from datetime import datetime
from typing import Dict, Any
import httpx

from config import get_config
from errors import MCPError

logger = logging.getLogger(__name__)


async def execute_compare_entities(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute compare_entities tool via LangGraph comparison_node."""
    config = get_config()
    entity_ids = args.get("entity_ids", [])
    criteria = args.get("criteria", "composite")
    
    logger.info(f"⚖️ Executing compare_entities: entity_ids={entity_ids}, criteria={criteria}")
    
    if len(entity_ids) < 2:
        raise MCPError("compare_entities requires at least 2 entity_ids", "INVALID_ARGS")
    
    entities_str = " vs ".join(entity_ids)
    query = f"compare {entities_str}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"📡 Calling LangGraph API: {config.api.langgraph}/run")
            response = await client.post(
                f"{config.api.langgraph}/run",
                json={"input_text": query, "user_id": user_id}
            )
            response.raise_for_status()
            langgraph_data = response.json()
            
            comparison_matrix = langgraph_data.get("comparison_matrix", {})
            numerical_panel = langgraph_data.get("numerical_panel", [])
            
            # Domain-agnostic factor extraction (use config factor_keys)
            factor_keys = config.validation.default_factor_keys
            legacy_map = {
                "momentum_z": factor_keys[0] if len(factor_keys) > 0 else "factor_1",
                "trend_z": factor_keys[1] if len(factor_keys) > 1 else "factor_2",
                "volatility_z": factor_keys[2] if len(factor_keys) > 2 else "factor_3",
                "sentiment_z": factor_keys[3] if len(factor_keys) > 3 else "factor_4",
                "fundamental_z": factor_keys[4] if len(factor_keys) > 4 else "factor_5",
            }
            
            comparison_data = []
            for entity_data in numerical_panel:
                # Extract generic factors (backwards compatible with finance fields)
                factors = {}
                for legacy_key, generic_key in legacy_map.items():
                    value = entity_data.get(legacy_key, 0.0)
                    if value is not None:
                        factors[generic_key] = value
                
                comparison_data.append({
                    "entity_id": entity_data.get("entity_id"),
                    "composite_score": entity_data.get("composite_score", 0.0),
                    "rank": entity_data.get("rank", 0),
                    "percentile": entity_data.get("percentile", 0.0),
                    "factors": factors  # Generic factor mapping
                })
            
            winner = comparison_matrix.get("winner", entity_ids[0] if entity_ids else "")
            loser = comparison_matrix.get("loser", entity_ids[-1] if len(entity_ids) > 1 else "")
            deltas = comparison_matrix.get("deltas", {})
            
            return {
                "entity_ids": entity_ids,
                "comparison": comparison_data,
                "winner": winner,
                "loser": loser,
                "deltas": deltas,
                "criteria": criteria,
                "compared_at": datetime.utcnow().isoformat()
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ LangGraph API error: {e.response.status_code}")
        raise MCPError(f"LangGraph API failed: {e.response.status_code}", "LANGGRAPH_ERROR")
    except httpx.RequestError as e:
        logger.error(f"❌ LangGraph connection error: {e}")
        raise MCPError("Failed to connect to LangGraph", "LANGGRAPH_UNREACHABLE")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise MCPError(f"Unexpected error: {str(e)}", "INTERNAL_ERROR")
