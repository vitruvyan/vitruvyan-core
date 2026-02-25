"""Neural Engine response builder (service layer)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd


class ResponseBuilder:
    """Formats ranked dataframe into API payloads (legacy-compatible fields included)."""

    @staticmethod
    def build_screen_response(
        ranked_df: pd.DataFrame,
        profile: str,
        top_k: int,
        stratification_mode: str,
        profile_weights: Dict[str, float],
        total_entities: int,
        processing_time_ms: float,
        statistics: Dict[str, Any] | None = None,
        screening_criteria: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        response = {
            "ranked_entities": ResponseBuilder._pack_ranked_entities(ranked_df),
            "profile": profile,
            "top_k": top_k,
            "stratification_mode": stratification_mode,
            "total_entities_evaluated": int(total_entities),
            "profile_weights": profile_weights,
            "processing_time_ms": float(processing_time_ms),
            "statistics": statistics or {},
            "timestamp": datetime.utcnow().isoformat(),
            # Legacy-compatible rich payload sections
            "asof": datetime.now(timezone.utc).isoformat(),
            "screening_criteria": screening_criteria or {},
            "ranking": {
                "stocks": ResponseBuilder._pack_by_type(ranked_df, "stock"),
                "etf": ResponseBuilder._pack_by_type(ranked_df, "etf"),
                "funds": ResponseBuilder._pack_by_type(ranked_df, "fund"),
            },
        }
        return _sanitize_jsonable(response)

    @staticmethod
    def build_rank_response(
        ranked_df: pd.DataFrame,
        feature_name: str,
        higher_is_better: bool,
        processing_time_ms: float,
    ) -> Dict[str, Any]:
        response = {
            "ranked_entities": [
                {
                    "rank": int(row.get("rank", 0)),
                    "entity_id": row.get("entity_id"),
                    "entity_name": row.get("entity_name"),
                    "composite_score": _to_float(row.get(feature_name)),
                    "percentile": _to_float(row.get("percentile")),
                    "bucket": row.get("bucket"),
                }
                for _, row in ranked_df.iterrows()
            ],
            "feature_name": feature_name,
            "higher_is_better": higher_is_better,
            "total_entities_ranked": int(len(ranked_df)),
            "processing_time_ms": float(processing_time_ms),
        }
        return _sanitize_jsonable(response)

    @staticmethod
    def _pack_ranked_entities(df: pd.DataFrame) -> list[Dict[str, Any]]:
        # Collect ALL z-score columns dynamically (beyond the 5 hardcoded ones)
        z_columns = [c for c in df.columns if c.endswith("_z")]

        rows = []
        for _, row in df.iterrows():
            entity = {
                    "rank": int(row.get("rank", 0)),
                    "entity_id": row.get("entity_id"),
                    "entity_name": row.get("entity_name"),
                    "composite_score": _to_float(row.get("composite_score")),
                    "percentile": _to_float(row.get("percentile")),
                    "bucket": row.get("bucket"),
                    "momentum_z": _to_float(row.get("momentum_z")),
                    "trend_z": _to_float(row.get("trend_z")),
                    "volatility_z": _to_float(row.get("volatility_z")),
                    "sentiment_z": _to_float(row.get("sentiment_z")),
                    "fundamentals_z": _to_float(row.get("fundamentals_z")),
                    "group": row.get("stratification_field", row.get("group")),
                    "metadata": {
                        "instrument_type": row.get("instrument_type"),
                        "country": row.get("country"),
                        "sector": row.get("sector"),
                        "vare_risk_score": _to_float(row.get("vare_risk_score")),
                        "vare_risk_category": row.get("vare_risk_category"),
                        "selection_reason": ResponseBuilder._selection_reason(row),
                        "dominant_factor": ResponseBuilder._dominant_factor(row),
                    },
                }
            # Inject ALL z-score columns (dynamic — includes fundamentals, factor, etc.)
            for zc in z_columns:
                val = _to_float(row.get(zc))
                if val is not None and zc not in entity:
                    entity[zc] = val
            rows.append(entity)
        return rows

    @staticmethod
    def _pack_by_type(df: pd.DataFrame, instrument_type: str) -> list[Dict[str, Any]]:
        if df.empty:
            return []
        type_col = "instrument_type" if "instrument_type" in df.columns else "type"
        if type_col not in df.columns:
            return []
        sub = df[df[type_col].fillna("").str.lower() == instrument_type].copy()
        if sub.empty:
            return []

        payload = []
        for _, row in sub.iterrows():
            factors = {
                "momentum_z": _to_float(row.get("momentum_z")),
                "trend_z": _to_float(row.get("trend_z")),
                "volatility_z": _to_float(row.get("volatility_z")),
                "sentiment_z": _to_float(row.get("sentiment_z")),
                "value_z": _to_float(row.get("value_z", row.get("value"))),
                "growth_z": _to_float(row.get("growth_z", row.get("growth"))),
                "quality_z": _to_float(row.get("quality_z", row.get("quality"))),
                "dark_pool_z": _to_float(row.get("dark_pool_z")),
                "divergence_score": _to_float(row.get("divergence_score")),
                "divergence_type": row.get("divergence_type"),
                "mtf_consensus": _to_float(row.get("mtf_consensus")),
                "days_to_earnings": _to_float(row.get("days_to_earnings")),
                "vare_risk_score": _to_float(row.get("vare_risk_score")),
                "vare_risk_category": row.get("vare_risk_category"),
            }
            payload.append(
                {
                    "rank": int(row.get("rank", 0)),
                    "ticker": row.get("entity_id"),
                    "composite_score": _to_float(row.get("composite_score")),
                    "factors": factors,
                    "dominant_factor": ResponseBuilder._dominant_factor(row),
                    "selection_reason": ResponseBuilder._selection_reason(row),
                    "rationale": ResponseBuilder._selection_reason(row),
                }
            )
        return payload

    @staticmethod
    def _dominant_factor(row: pd.Series) -> str:
        candidates = {
            "momentum": abs(_to_float(row.get("momentum_z")) or 0.0),
            "trend": abs(_to_float(row.get("trend_z")) or 0.0),
            "volatility": abs(_to_float(row.get("volatility_z")) or 0.0),
            "sentiment": abs(_to_float(row.get("sentiment_z")) or 0.0),
            "fundamentals": abs(_to_float(row.get("fundamentals_z")) or 0.0),
        }
        if not any(candidates.values()):
            return "balanced"
        return max(candidates, key=candidates.get)

    @staticmethod
    def _selection_reason(row: pd.Series) -> str:
        dominant = ResponseBuilder._dominant_factor(row)
        rank = int(row.get("rank", 0))
        label = {1: "Top pick", 2: "Strong contender", 3: "Solid option"}.get(rank, f"Rank #{rank}")
        return f"{label}: {dominant} signal strongest for this entity"


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    try:
        return float(val)
    except Exception:
        return None


def _sanitize_jsonable(value: Any) -> Any:
    """Recursively replace NaN/Inf with None for JSON compliance."""
    if isinstance(value, dict):
        return {k: _sanitize_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_jsonable(v) for v in value)
    if isinstance(value, np.ndarray):
        return [_sanitize_jsonable(v) for v in value.tolist()]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value
