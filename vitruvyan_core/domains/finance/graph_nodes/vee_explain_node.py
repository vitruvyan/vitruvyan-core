"""
VEE Explain Node — Finance LangGraph Adapter
=============================================

Thin adapter: extracts z-score metrics from state → calls VEE Engine
with FinanceExplainabilityProvider → writes vee_explanations to state.

State reads:
    entity_ids / validated_tickers  — list of tickers to explain
    numerical_panel                 — z-score metrics per ticker (from quality_check)
    raw_output.ranking.stocks       — fallback source of z-scores

State writes:
    vee_explanations  — Dict[ticker, Dict[str, str]]  (summary, technical, detailed per ticker)

Placement: quality_check → vee_explain → output_normalizer

Author: Vitruvyan Core Team
Created: February 25, 2026
Status: PRODUCTION
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Lazy-init singleton (same pattern as semantic_grounding_node)
_ENGINE = None
_PROVIDER = None


def _get_engine():
    """Lazy-init VEE Engine with Finance provider (once per process)."""
    global _ENGINE, _PROVIDER
    if _ENGINE is None:
        from core.vpar.vee.vee_engine import VEEEngine
        from domains.finance.vpar.explainability_provider import FinanceExplainabilityProvider
        _PROVIDER = FinanceExplainabilityProvider()
        _ENGINE = VEEEngine(auto_store=False, use_memory=False, domain_tag="finance")
        logger.info("[VEE] Finance VEE Engine initialized")
    return _ENGINE, _PROVIDER


def _extract_z_metrics(source: dict) -> Dict[str, float]:
    """Extract all z-score keys + composite_score from a single entry."""
    metrics: Dict[str, float] = {}
    for key, val in source.items():
        if val is None:
            continue
        if key == "composite_score" or key.endswith("_z"):
            try:
                metrics[key] = float(val)
            except (TypeError, ValueError):
                pass
    return metrics


def _extract_metrics(state: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Extract per-ticker z-score metrics from state.

    Sources (cascade):
      1. numerical_panel (best: quality_check already structured it)
      2. raw_output.ranking.stocks (fallback: screener NE response)
    """
    result: Dict[str, Dict[str, float]] = {}

    # Source 1: numerical_panel
    panel = state.get("numerical_panel") or []
    for entry in panel:
        ticker = entry.get("ticker") or entry.get("entity_id")
        if not ticker:
            continue
        metrics = _extract_z_metrics(entry)
        if metrics:
            result[ticker] = metrics

    if result:
        return result

    # Source 2: raw_output.ranking.stocks
    raw = state.get("raw_output") or {}
    ranking = raw.get("ranking", {})
    stocks = ranking.get("stocks", [])
    for stock in stocks:
        ticker = stock.get("ticker") or stock.get("entity_id")
        if not ticker:
            continue
        metrics = _extract_z_metrics(stock)
        if metrics:
            result[ticker] = metrics

    return result


def vee_explain_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """VEE Explainability Node — LangGraph thin adapter.

    For each ticker with z-score data, runs VEE Engine to produce
    multi-level explanations (summary, technical, detailed).
    """
    t0 = time.time()
    engine, provider = _get_engine()

    # Extract metrics per ticker
    ticker_metrics = _extract_metrics(state)
    if not ticker_metrics:
        logger.info("[VEE] No ticker metrics available — skipping VEE explanations")
        state["vee_explanations"] = {}
        return state

    # Get user profile hint (if available)
    profile = None
    screening_meta = state.get("screening_meta") or {}
    profile_name = screening_meta.get("profile")
    if profile_name:
        profile = {"name": profile_name}

    # Semantic context from VSGS (if available)
    semantic_context = None
    matches = state.get("semantic_matches")
    if matches:
        semantic_context = matches

    # Run VEE for each ticker
    vee_results: Dict[str, Dict[str, str]] = {}
    for ticker, metrics in ticker_metrics.items():
        try:
            explanation = engine.explain(
                entity_id=ticker,
                metrics=metrics,
                provider=provider,
                profile=profile,
                semantic_context=semantic_context,
            )
            vee_results[ticker] = explanation
            logger.debug("[VEE] %s → %d explanation levels",
                         ticker, len(explanation))
        except Exception as e:
            logger.warning("[VEE] Failed for %s: %s", ticker, e)
            vee_results[ticker] = {
                "summary": f"Analysis unavailable for {ticker}: {e}",
                "technical": "",
                "detailed": "",
            }

    elapsed_ms = (time.time() - t0) * 1000
    state["vee_explanations"] = vee_results
    logger.info("[VEE] Generated explanations for %d tickers in %.1fms",
                len(vee_results), elapsed_ms)

    return state
