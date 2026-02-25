# services/api_mcp/tools/sentiment.py
"""Sentiment/signal query tool executor."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable

from adapters.finance_adapter import get_finance_adapter
try:
    from core.agents.postgres_agent import PostgresAgent
except ModuleNotFoundError:
    from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_identifier(value: str) -> str:
    """Allow only SQL-safe identifiers for dynamic table/column names."""
    if not _IDENTIFIER_RE.match(value or ""):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return value


def _default_signal_sources() -> Dict[str, tuple[str, ...]]:
    """Fallback source candidates when finance adapter is disabled."""
    return {
        "tables": ("entity_signals", "sentiment_scores"),
        "entity_columns": ("entity_id", "ticker"),
    }


def _normalize_signal_request(args: Dict[str, Any]) -> tuple[str, int, bool]:
    """Normalize query args for both generic and finance contracts."""
    entity_id = (
        args.get("entity_id")
        or args.get("ticker")
        or args.get("symbol")
        or ""
    )
    entity_id = str(entity_id).strip()
    if not entity_id:
        raise ValueError("query_signals/query_sentiment requires entity_id (or ticker)")

    raw_window = args.get("time_window", args.get("days", 7))
    try:
        window_days = int(raw_window)
    except Exception:
        window_days = 7
    window_days = max(1, min(90, window_days))

    include_context = args.get("include_context", args.get("include_phrases", True))
    include_context = bool(include_context)
    return entity_id, window_days, include_context


def _candidate_pairs(tables: Iterable[str], entity_columns: Iterable[str]) -> list[tuple[str, str]]:
    """Build ordered table/column candidate combinations."""
    pairs: list[tuple[str, str]] = []
    for table in tables:
        for entity_column in entity_columns:
            pairs.append((table, entity_column))
    return pairs


async def execute_query_sentiment(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute query_signals/query_sentiment via PostgreSQL."""
    entity_id, window_days, include_context = _normalize_signal_request(args or {})
    logger.info(
        "💭 Executing query_signals: entity_id=%s, window_days=%s",
        entity_id,
        window_days,
    )

    finance_adapter = get_finance_adapter()
    if finance_adapter is None:
        sources = _default_signal_sources()
        phrase_samples = [
            f"Positive outlook on {entity_id}",
            f"{entity_id} showing resilient momentum",
            f"Recent sentiment context on {entity_id}",
        ]
    else:
        sources = finance_adapter.get_signal_source_candidates()
        phrase_samples = finance_adapter.build_phrase_samples(entity_id, limit=3)

    score_column = "combined_score"
    tag_column = "sentiment_tag"
    created_at_column = "created_at"

    candidate_pairs = _candidate_pairs(
        tables=sources.get("tables", ()),
        entity_columns=sources.get("entity_columns", ()),
    )

    try:
        pg = PostgresAgent()
        with pg.connection.cursor() as cur:
            for table_name, entity_column in candidate_pairs:
                try:
                    safe_table = _safe_identifier(table_name)
                    safe_entity_col = _safe_identifier(entity_column)
                    safe_score_col = _safe_identifier(score_column)
                    safe_tag_col = _safe_identifier(tag_column)
                    safe_created_col = _safe_identifier(created_at_column)
                except ValueError:
                    continue

                try:
                    cur.execute(
                        f"""
                        SELECT
                            AVG({safe_score_col}) AS avg_signal,
                            COUNT(*) AS samples,
                            MAX({safe_created_col}) AS latest_timestamp
                        FROM {safe_table}
                        WHERE {safe_entity_col} = %s
                          AND {safe_created_col} >= NOW() - (%s * INTERVAL '1 day')
                        """,
                        (entity_id, window_days),
                    )
                    row = cur.fetchone()
                except Exception as query_error:
                    logger.debug(
                        "Signal query failed for %s.%s: %s",
                        safe_table,
                        safe_entity_col,
                        query_error,
                    )
                    continue

                if not row or row[0] is None:
                    continue

                avg_sentiment = float(row[0])
                samples = int(row[1] or 0)
                latest_timestamp = row[2]
                trend = (
                    "positive"
                    if avg_sentiment > 0.3
                    else ("negative" if avg_sentiment < -0.3 else "neutral")
                )

                latest_score = avg_sentiment
                latest_tag = "neutral"
                try:
                    cur.execute(
                        f"""
                        SELECT {safe_score_col}, {safe_tag_col}
                        FROM {safe_table}
                        WHERE {safe_entity_col} = %s
                        ORDER BY {safe_created_col} DESC
                        LIMIT 1
                        """,
                        (entity_id,),
                    )
                    latest_row = cur.fetchone()
                    if latest_row:
                        latest_score = float(latest_row[0])
                        latest_tag = str(latest_row[1] or "neutral")
                except Exception as latest_error:
                    logger.debug(
                        "Latest signal query failed for %s.%s: %s",
                        safe_table,
                        safe_entity_col,
                        latest_error,
                    )

                return {
                    "entity_id": entity_id,
                    "avg_sentiment": round(avg_sentiment, 3),
                    "trend": trend,
                    "samples": samples,
                    "latest_score": round(latest_score, 3),
                    "latest_tag": latest_tag,
                    "phrases": phrase_samples if include_context else [],
                    "days_analyzed": window_days,
                    "latest_timestamp": latest_timestamp.isoformat() if latest_timestamp else None,
                    "source_table": safe_table,
                    "source_entity_column": safe_entity_col,
                }

        logger.warning("No signal data found for %s in last %s days", entity_id, window_days)
        return {
            "entity_id": entity_id,
            "avg_sentiment": 0.0,
            "trend": "unknown",
            "samples": 0,
            "latest_score": 0.0,
            "latest_tag": "unknown",
            "phrases": [],
            "days_analyzed": window_days,
            "latest_timestamp": None,
            "message": f"No signal data found for {entity_id} in last {window_days} days",
        }

    except Exception as exc:
        logger.error("Error querying signals for %s: %s", entity_id, exc)
        raise
