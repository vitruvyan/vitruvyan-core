"""
VARE Risk Node — Finance LangGraph Adapter
===========================================

Thin adapter: extracts z-score metrics from state → calls VARE Engine
with FinanceRiskProvider → writes vare_risk to state.

State reads:
    entity_ids / validated_tickers  — list of tickers
    numerical_panel                 — z-score metrics per ticker
    screening_meta.profile          — risk profile hint (conservative/balanced/aggressive)

State writes:
    vare_risk  — Dict[ticker, Dict]  (overall_risk, risk_category, dimensions, explanation per ticker)

Placement: quality_check → vee_explain → vare_risk → output_normalizer

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
    """Lazy-init VARE Engine with Finance provider (once per process)."""
    global _ENGINE, _PROVIDER
    if _ENGINE is None:
        from core.vpar.vare.vare_engine import VAREEngine
        from domains.finance.vpar.risk_provider import FinanceRiskProvider
        _PROVIDER = FinanceRiskProvider()
        _ENGINE = VAREEngine(_PROVIDER, domain_tag="finance")
        logger.info("[VARE] Finance VARE Engine initialized")
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
    """Extract per-ticker z-score metrics from state (same cascade as VEE)."""
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


def vare_risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """VARE Risk Assessment Node — LangGraph thin adapter.

    For each ticker with z-score data, runs VARE Engine to produce
    multi-dimensional risk assessment.
    """
    t0 = time.time()
    engine = _get_engine()

    ticker_metrics = _extract_metrics(state)
    if not ticker_metrics:
        logger.info("[VARE] No ticker metrics available — skipping risk assessment")
        state["vare_risk"] = {}
        return state

    # Resolve risk profile from screening_meta or default
    from core.vpar.vare.types import RiskConfig
    profile_name = "balanced"
    screening_meta = state.get("screening_meta") or {}
    hint = screening_meta.get("profile", "")
    if hint in ("conservative", "balanced", "aggressive"):
        profile_name = hint

    config = RiskConfig(profile=profile_name)

    # Run VARE for each ticker
    vare_results: Dict[str, Dict] = {}
    for ticker, metrics in ticker_metrics.items():
        try:
            result = engine.assess_risk(
                entity_id=ticker,
                raw_data=metrics,
                config=config,
            )
            vare_results[ticker] = {
                "overall_risk": result.overall_risk,
                "risk_category": result.risk_category,
                "primary_factor": result.primary_risk_factor,
                "confidence": result.confidence,
                "dimensions": {
                    name: {
                        "score": ds.score,
                        "raw_value": ds.raw_value,
                        "explanation": ds.explanation,
                    }
                    for name, ds in result.dimension_scores.items()
                },
                "explanation": result.explanation,
            }
            logger.debug("[VARE] %s → %s (%s, %.1f/100)",
                         ticker, result.risk_category,
                         result.primary_risk_factor, result.overall_risk)
        except Exception as e:
            logger.warning("[VARE] Failed for %s: %s", ticker, e)
            vare_results[ticker] = {
                "overall_risk": 50.0,
                "risk_category": "UNKNOWN",
                "primary_factor": "error",
                "confidence": 0.0,
                "dimensions": {},
                "explanation": {"summary": f"Risk assessment failed: {e}"},
            }

    elapsed_ms = (time.time() - t0) * 1000
    state["vare_risk"] = vare_results
    logger.info("[VARE] Risk assessed for %d tickers in %.1fms",
                len(vare_results), elapsed_ms)

    return state
