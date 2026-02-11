# services/api_mcp/tools/semantic.py
"""Semantic context extraction tool executor."""

import logging
from datetime import datetime
from typing import Dict, Any
import httpx

from config import get_config
from errors import MCPError

logger = logging.getLogger(__name__)


async def execute_extract_semantic_context(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute extract_semantic_context tool via Pattern Weavers."""
    config = get_config()
    query = args.get("query", "")
    
    logger.info(f"🧵 Executing extract_semantic_context: query={query}")
    
    if not query:
        raise MCPError("extract_semantic_context requires non-empty query", "INVALID_ARGS")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"📡 Calling Pattern Weavers API: {config.api.pattern_weavers}/weave")
            response = await client.post(
                f"{config.api.pattern_weavers}/weave",
                json={"query_text": query, "user_id": user_id}
            )
            response.raise_for_status()
            weaver_data = response.json()
            
            return {
                "query": query,
                "concepts": weaver_data.get("concepts", []),
                "regions": weaver_data.get("regions", []),
                "sectors": weaver_data.get("sectors", []),
                "risk_profile": weaver_data.get("risk_profile", "balanced"),
                "confidence": weaver_data.get("confidence", 0.0),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Pattern Weavers API error: {e.response.status_code}")
        raise MCPError(f"Pattern Weavers API failed: {e.response.status_code}", "PATTERN_WEAVERS_ERROR")
    except httpx.RequestError as e:
        logger.error(f"❌ Pattern Weavers connection error: {e}")
        raise MCPError("Failed to connect to Pattern Weavers", "PATTERN_WEAVERS_UNREACHABLE")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise MCPError(f"Unexpected error: {str(e)}", "INTERNAL_ERROR")
