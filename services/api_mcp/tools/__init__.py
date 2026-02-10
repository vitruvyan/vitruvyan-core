# services/api_mcp/tools/__init__.py
"""MCP Tool executors."""

from .screen import execute_screen_entities
from .vee import execute_generate_vee_summary
from .sentiment import execute_query_sentiment
from .compare import execute_compare_entities
from .semantic import execute_extract_semantic_context

TOOL_EXECUTORS = {
    "screen_entities": execute_screen_entities,
    "generate_vee_summary": execute_generate_vee_summary,
    "query_sentiment": execute_query_sentiment,
    "compare_entities": execute_compare_entities,
    "extract_semantic_context": execute_extract_semantic_context,
}

__all__ = [
    "TOOL_EXECUTORS",
    "execute_screen_entities",
    "execute_generate_vee_summary",
    "execute_query_sentiment",
    "execute_compare_entities",
    "execute_extract_semantic_context",
]
