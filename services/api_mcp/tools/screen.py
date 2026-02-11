# services/api_mcp/tools/screen.py
"""Screen entities tool executor."""

import logging
from datetime import datetime
from typing import Dict, Any
import httpx

from ..config import get_config
from ..errors import MCPError

logger = logging.getLogger(__name__)


async def execute_screen_entities(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute screen_entities tool via Neural Engine API."""
    config = get_config()
    entity_ids = args.get("entity_ids", [])
    profile = args.get("profile", "balanced")  # Changed from "balanced_mid" (agnostic)
    
    logger.info(f"🧠 Executing screen_entities: entity_ids={entity_ids}, profile={profile}")
    
    # Test mode: Inject heretical z-score for testing
    test_inject_heretical = args.get("_test_inject_heretical", False)
    test_heretical_factor = args.get("_test_heretical_factor", "factor_1")  # Generic factor name
    test_heretical_value = args.get("_test_heretical_value", 5.0)
    
    entities_str = ", ".join(entity_ids)
    query = f"screen {entities_str} with {profile} profile"
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            logger.info(f"📡 Calling LangGraph API: {config.api.langgraph}/run")
            response = await client.post(
                f"{config.api.langgraph}/run",
                json={"input_text": query, "user_id": user_id}
            )
            response.raise_for_status()
            langgraph_data = response.json()
            
            numerical_panel = langgraph_data.get("numerical_panel", [])
            logger.info(f"✅ LangGraph response: {len(numerical_panel)} entities")
            
            # Domain-agnostic factor extraction (use config factor_keys)
            factor_keys = config.validation.default_factor_keys
            legacy_map = {
                "momentum_z": factor_keys[0] if len(factor_keys) > 0 else "factor_1",
                "trend_z": factor_keys[1] if len(factor_keys) > 1 else "factor_2",
                "vola_z": factor_keys[2] if len(factor_keys) > 2 else "factor_3",
                "sentiment_z": factor_keys[3] if len(factor_keys) > 3 else "factor_4",
                "fundamental_z": factor_keys[4] if len(factor_keys) > 4 else "factor_5",
            }
            
            transformed_entities = []
            for entity_data in numerical_panel:
                # Extract generic factors (backwards compatible with finance fields)
                z_scores = {}
                for legacy_key, generic_key in legacy_map.items():
                    value = entity_data.get(legacy_key, 0.0)
                    if value is not None:
                        z_scores[generic_key] = value
                
                transformed_entities.append({
                    "entity_id": entity_data.get("entity_id"),
                    "composite_score": entity_data.get("composite_score", entity_data.get("composite", 0.0)),
                    "rank": entity_data.get("rank", 0),
                    "percentile": entity_data.get("percentile", 0.0),
                    "z_scores": z_scores,  # Generic factor scores
                    "metadata": {  # Generic metadata (replaces finance-specific "vare")
                        "risk_score": entity_data.get("vare_risk_score", 0.0),
                        "risk_category": entity_data.get("vare_risk_category", "unknown"),
                        "confidence": entity_data.get("vare_confidence", 0.0)
                    }
                })
            
            mock_data = {"entity_ids": transformed_entities, "profile_used": profile, "total_screened": len(transformed_entities)}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ LangGraph API error: {e.response.status_code}")
        raise MCPError(f"LangGraph API failed: {e.response.status_code}", "LANGGRAPH_ERROR")
    except httpx.RequestError as e:
        logger.error(f"❌ LangGraph connection error: {e}")
        raise MCPError("Failed to connect to LangGraph", "LANGGRAPH_UNREACHABLE")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise MCPError(f"Unexpected error: {str(e)}", "INTERNAL_ERROR")
    
    if test_inject_heretical and mock_data["entity_ids"]:
        logger.warning(f"⚠️ TEST MODE: Injecting heretical z-score")
        mock_data["entity_ids"][0]["z_scores"][test_heretical_factor] = test_heretical_value
    
    return mock_data
