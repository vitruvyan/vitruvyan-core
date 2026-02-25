"""
VWRE Attribution Node — Finance LangGraph Adapter
===================================================

Thin adapter: extracts z-score factors + composite_score from state →
calls VWRE Engine with FinanceAggregationProvider → writes vwre_attribution to state.

State reads:
    entity_ids / validated_tickers  — list of tickers
    numerical_panel                 — z-score metrics per ticker
    screening_meta.profile          — aggregation profile hint

State writes:
    vwre_attribution  — Dict[ticker, Dict]  (primary_driver, factors, explanation per ticker)

Placement: quality_check → vee_explain → vare_risk → vwre_attribution → output_normalizer

Author: Vitruvyan Core Team
Created: February 25, 2026
Status: PRODUCTION
"""

import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

_ENGINE = None
_PROVIDER = None


def _get_engine():
    """Lazy-init VWRE Engine with Finance provider (once per process)."""
    global _ENGINE, _PROVIDER
    if _ENGINE is None:
        from core.vpar.vwre.vwre_engine import VWREEngine
        from domains.finance.vpar.aggregation_provider import FinanceAggregationProvider
        _PROVIDER = FinanceAggregationProvider()
        _ENGINE = VWREEngine(_PROVIDER, domain_tag="finance")
        logger.info("[VWRE] Finance VWRE Engine initialized")
    return _ENGINE


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
    """Extract per-ticker z-score factors + composite_score from state."""
    result: Dict[str, Dict[str, float]] = {}

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

    # Fallback: raw_output.ranking.stocks
    raw = state.get("raw_output") or {}
    stocks = raw.get("ranking", {}).get("stocks", [])
    for stock in stocks:
        ticker = stock.get("ticker") or stock.get("entity_id")
        if not ticker:
            continue
        metrics = _extract_z_metrics(stock)
        if metrics:
            result[ticker] = metrics

    return result


def _resolve_profile(state: Dict[str, Any]) -> str:
    """Resolve VWRE aggregation profile from state hints."""
    meta = state.get("screening_meta") or {}
    profile = meta.get("profile", "balanced_mid")
    # Map risk profile names to VWRE profile names
    mapping = {
        "conservative": "long_quality",
        "balanced": "balanced_mid",
        "aggressive": "short_spec",
    }
    return mapping.get(profile, profile)


def vwre_attribution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """VWRE Attribution Node — LangGraph thin adapter.

    For each ticker with z-score data, runs VWRE Engine to decompose
    the composite_score into weighted factor contributions.
    """
    t0 = time.time()
    engine = _get_engine()

    ticker_metrics = _extract_metrics(state)
    if not ticker_metrics:
        logger.info("[VWRE] No ticker metrics available — skipping attribution")
        state["vwre_attribution"] = {}
        return state

    from core.vpar.vwre.types import AttributionConfig
    profile_name = _resolve_profile(state)
    config = AttributionConfig(profile=profile_name)

    # Run VWRE for each ticker
    vwre_results: Dict[str, Dict] = {}
    for ticker, metrics in ticker_metrics.items():
        composite = metrics.get("composite_score", 0.0)
        # Factors = all z-score keys except composite_score
        factors = {k: v for k, v in metrics.items() if k != "composite_score"}

        if not factors:
            logger.debug("[VWRE] No factors for %s, skipping", ticker)
            continue

        try:
            result = engine.analyze(
                entity_id=ticker,
                composite_score=composite,
                factors=factors,
                config=config,
            )
            vwre_results[ticker] = {
                "composite_score": result.composite_score,
                "primary_driver": result.primary_driver,
                "primary_contribution": result.primary_contribution,
                "secondary_drivers": result.secondary_drivers,
                "verification": result.verification_status,
                "rank_explanation": result.rank_explanation,
                "factors": {
                    name: {
                        "z_score": fa.z_score,
                        "weight": fa.weight,
                        "contribution": fa.contribution,
                        "percentage": fa.percentage,
                        "rank": fa.rank,
                        "narrative": fa.narrative,
                    }
                    for name, fa in result.factors.items()
                },
                "explanation": {
                    "summary": result.rank_explanation,
                    "technical": result.technical_summary,
                },
            }
            logger.debug("[VWRE] %s → primary=%s (%+.3f), %s",
                         ticker, result.primary_driver,
                         result.primary_contribution,
                         result.verification_status)
        except Exception as e:
            logger.warning("[VWRE] Failed for %s: %s", ticker, e)
            vwre_results[ticker] = {
                "composite_score": composite,
                "primary_driver": "unknown",
                "primary_contribution": 0.0,
                "verification": "error",
                "rank_explanation": f"Attribution failed: {e}",
                "factors": {},
                "explanation": {"summary": f"Attribution failed: {e}"},
            }

    elapsed_ms = (time.time() - t0) * 1000
    state["vwre_attribution"] = vwre_results
    logger.info("[VWRE] Attribution computed for %d tickers in %.1fms",
                len(vwre_results), elapsed_ms)

    return state
