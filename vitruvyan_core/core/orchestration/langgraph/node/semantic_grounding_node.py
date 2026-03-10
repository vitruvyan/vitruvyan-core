"""
VSGS Semantic Grounding Node — LangGraph thin adapter.

Delegates all logic to VSGSEngine (core.vpar.vsgs).
This node only handles: state extraction, state mutation, metrics, audit.

State Updates:
    semantic_matches  — List[Dict] top-k similar contexts
    vsgs_status       — "enabled" | "disabled" | "error" | "skipped"
    vsgs_elapsed_ms   — Processing time in milliseconds

Placement: babel_emotion → semantic_grounding → params_extraction
"""

import os
import logging
from typing import Dict, Any

from core.vpar.vsgs import VSGSEngine, GroundingConfig

# Metrics (non-critical)
try:
    from core.monitoring.vsgs_metrics import (
        record_grounding_request, record_grounding_hit,
        record_embedding_latency, record_qdrant_latency, record_error,
    )
except ImportError:
    def record_grounding_request(**kw): pass
    def record_grounding_hit(**kw): pass
    def record_embedding_latency(*a, **kw): pass
    def record_qdrant_latency(*a, **kw): pass
    def record_error(*a, **kw): pass

# NOTE: Configuration via environment variables only.
# load_dotenv() is called in service entrypoints (main.py), not in core modules.
logger = logging.getLogger(__name__)

# ── Configuration from environment ───────────────────────────────────────────

from config.api_config import get_embedding_url

_CONFIG = GroundingConfig(
    enabled=int(os.getenv("VSGS_ENABLED", "0")) == 1,
    top_k=int(os.getenv("VSGS_GROUNDING_TOPK", "3")),
    collection=os.getenv("VSGS_COLLECTION_NAME", "semantic_states"),
    prompt_budget_chars=int(os.getenv("VSGS_PROMPT_BUDGET_CHARS", "800")),
)

_ENGINE = VSGSEngine(config=_CONFIG, embedding_url=get_embedding_url())

# ── Node function ────────────────────────────────────────────────────────────


def semantic_grounding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """VSGS Semantic Grounding — LangGraph node.

    Extracts input from state, calls VSGSEngine.ground(), writes results
    back to state. All domain logic lives in VSGSEngine.
    """
    input_text = state.get("input_text", "")
    user_id = state.get("user_id", "demo")
    intent = state.get("intent", "unknown")
    language = state.get("language", "en")

    # Record request metric
    if _CONFIG.enabled and input_text:
        record_grounding_request(
            user_id=user_id, intent=intent, language=language)

    # Delegate to engine
    result = _ENGINE.ground(
        text=input_text, user_id=user_id,
        intent=intent, language=language,
        tenant_id=state.get("tenant_id", ""),
    )

    # Record hit metrics per match
    for match in result.matches:
        record_grounding_hit(
            user_id=user_id,
            collection=_CONFIG.collection,
            match_quality=match.quality,
        )

    # Record errors
    if result.error:
        record_error("grounding_failed", "semantic_grounding")

    # Trace log
    if result.matches:
        logger.info(
            "[VSGS] %d matches in %.1fms (top=%.3f, user=%s)",
            result.match_count, result.elapsed_ms,
            result.top_score, user_id,
        )

    # Write to state
    state.update(result.to_state_dict())
    return state
