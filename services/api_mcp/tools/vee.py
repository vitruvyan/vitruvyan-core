# services/api_mcp/tools/vee.py
"""VEE summary generation tool executor."""

import logging
from datetime import datetime
from typing import Dict, Any
import httpx

from ..config import get_config
from ..errors import MCPError

logger = logging.getLogger(__name__)


async def execute_generate_vee_summary(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute generate_vee_summary tool via LangGraph VEE Engine."""
    config = get_config()
    entity_id = args.get("entity_id")
    language = args.get("language", "it")
    level = args.get("level", "summary")
    
    logger.info(f"📝 Executing generate_vee_summary: entity_id={entity_id}, language={language}")
    
    query_templates = {
        "it": f"analizza {entity_id} momentum breve termine",
        "en": f"analyze {entity_id} momentum short term",
        "es": f"analizar {entity_id} momentum corto plazo",
        "fr": f"analyser {entity_id} momentum court terme"
    }
    query = query_templates.get(language, query_templates["en"])
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"📡 Calling LangGraph API: {config.api.langgraph}/run")
            response = await client.post(
                f"{config.api.langgraph}/run",
                json={"input_text": query, "user_id": user_id}
            )
            response.raise_for_status()
            langgraph_data = response.json()
            
            vee_explanations = langgraph_data.get("vee_explanations", {})
            entity_vee = vee_explanations.get(entity_id, {})
            narrative = entity_vee.get(level, entity_vee.get("summary", ""))
            
            if not narrative:
                narrative = langgraph_data.get("response", {}).get("narrative", "")
            
            return {
                "entity_id": entity_id,
                "level": level,
                "narrative": narrative,
                "word_count": len(narrative.split()),
                "language": language,
                "generated_at": datetime.utcnow().isoformat()
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
