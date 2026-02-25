"""
Finance Domain — Screener Node
================================

Neural Engine screening for finance intents (trend, momentum, risk, etc.).
Replaces the generic exec_node when GRAPH_DOMAIN=finance.

Pipeline position: decide → screener → output_normalizer
Triggered when: route_type="exec" intents (trend, risk, momentum, volatility, etc.)

State inputs:
    - profile: str     — NE profile name (fallback: intent-based mapping)
    - top_k: int       — Number of results (default 5)
    - tickers: list    — Optional ticker filter
    - intent: str      — User intent (mapped to NE profile)

State outputs:
    - raw_output: dict — Neural Engine ranking response
    - route: str       — "screener_success" | "screener_error" | "screener_timeout"
    - ok: bool         — Success flag
    - error: str|None  — Error message if failed
    - screening_meta: dict — Profile used, result counts, etc.

Author: Vitruvyan Finance Vertical
Created: February 24, 2026
"""

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

# Neural Engine service URL (NE_BASE_URL from docker-compose, NEURAL_ENGINE_URL as fallback)
NEURAL_ENGINE_URL = os.getenv(
    "NE_BASE_URL", os.getenv("NEURAL_ENGINE_URL", "http://neural_engine:8003")
)

# Intent → Neural Engine profile mapping
INTENT_TO_PROFILE: Dict[str, str] = {
    "momentum": "momentum_focus",
    "trend": "trend_follow",
    "sentiment": "sentiment_boost",
    "volatility": "short_spec",
    "risk": "balanced_mid",
    "balanced": "balanced_mid",
    "collection": "balanced_mid",
    "backtest": "balanced_mid",
    "allocate": "balanced_mid",
}


def screener_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Neural Engine API for finance screening.

    Maps intent → NE profile, calls /screen endpoint,
    converts ranked_entities response to ranking.stocks format
    for downstream compatibility (quality_check, compose_node, VEE).
    """
    profile = state.get("profile", "balanced_mid")
    top_k = state.get("top_k", 5)
    tickers = state.get("entity_ids") or state.get("tickers", [])
    intent = state.get("intent", "screener")

    # Map intent to NE profile if no explicit profile set
    if intent in INTENT_TO_PROFILE and profile == "balanced_mid":
        profile = INTENT_TO_PROFILE[intent]

    logger.info(
        f"[screener_node] profile={profile}, top_k={top_k}, "
        f"tickers={tickers}, intent={intent}"
    )

    ne_payload: Dict[str, Any] = {
        "profile": profile,
        "top_k": top_k,
    }

    # Apply ticker filter if specific tickers requested
    if tickers:
        ne_payload["entity_ids"] = tickers

    # Call Neural Engine — /screen endpoint (mercator NE API)
    endpoint = f"{NEURAL_ENGINE_URL}/screen"

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, json=ne_payload)
            resp.raise_for_status()

        ne_result = resp.json()

        # Convert ranked_entities → ranking.stocks format
        # (downstream quality_check/compose expect this structure)
        ranked = ne_result.get("ranked_entities", [])
        stocks = []
        for entity in ranked:
            stock = {
                "ticker": entity.get("entity_id", ""),
                "name": entity.get("entity_name", ""),
                "composite_score": entity.get("composite_score", 0.0),
                "momentum_z": entity.get("momentum_z"),
                "trend_z": entity.get("trend_z"),
                "vola_z": entity.get("volatility_z"),
                "sentiment_z": entity.get("sentiment_z"),
                "fundamentals_z": entity.get("fundamentals_z"),
                "bucket": entity.get("bucket"),
                "rank": entity.get("rank"),
                "group": entity.get("group"),
            }
            # Forward ALL dynamic z-score fields from NE
            # (fundamentals, factor, macro z-scores beyond the 5 named ones)
            for key, val in entity.items():
                if key.endswith("_z") and key not in stock and val is not None:
                    stock[key] = val
            # Include VARE metadata if present
            meta = entity.get("metadata", {})
            if meta:
                stock["instrument_type"] = meta.get("instrument_type")
                stock["sector"] = meta.get("sector")
                stock["country"] = meta.get("country")
                stock["vare_risk_score"] = meta.get("vare_risk_score")
                stock["vare_risk_category"] = meta.get("vare_risk_category")
            stocks.append(stock)

        total = len(stocks)

        # Wrap in ranking structure for downstream compatibility
        state["raw_output"] = {
            "ranking": {
                "stocks": stocks,
                "etf": [],
                "funds": [],
            }
        }
        state["route"] = "screener_success"
        state["ok"] = True
        state["error"] = None
        state["screening_meta"] = {
            "profile_used": profile,
            "top_k_requested": top_k,
            "total_results": total,
            "total_evaluated": ne_result.get("total_entities_evaluated", 0),
            "has_stocks": total > 0,
            "has_etfs": False,
            "has_funds": False,
        }

        logger.info(
            f"[screener_node] Success: {total} results "
            f"(evaluated={ne_result.get('total_entities_evaluated', '?')})"
        )

    except httpx.TimeoutException:
        logger.warning("[screener_node] Neural Engine timeout")
        state["raw_output"] = {}
        state["route"] = "screener_timeout"
        state["ok"] = False
        state["error"] = "Neural Engine timeout during screening"

    except httpx.HTTPStatusError as e:
        logger.error(f"[screener_node] NE HTTP error: {e.response.status_code}")
        state["raw_output"] = {}
        state["route"] = "screener_error"
        state["ok"] = False
        state["error"] = f"Neural Engine HTTP {e.response.status_code}"

    except Exception as e:
        logger.error(f"[screener_node] Unexpected error: {e}")
        state["raw_output"] = {}
        state["route"] = "screener_error"
        state["ok"] = False
        state["error"] = f"Screening error: {e}"

    return state
