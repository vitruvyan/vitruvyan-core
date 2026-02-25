"""
Finance MCP configuration and compatibility mapping.

Ports the practical MCP finance tool contract from Vitruvyan:
- finance tool aliases (`screen_tickers`, `compare_tickers`, `query_sentiment`)
- ticker/entity argument mapping
- finance criteria/profile normalization
- sentiment source fallback candidates
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    """Deduplicate non-empty strings preserving order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        value = (raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


@dataclass(frozen=True)
class FinanceMCPConfig:
    """Finance defaults used by the MCP service adapter."""

    domain_name: str = "finance"
    default_language: str = "it"
    default_screen_profile: str = "balanced_mid"
    default_signal_window_days: int = 7
    min_signal_window_days: int = 1
    max_signal_window_days: int = 30

    # Candidate sources for query_sentiment/query_signals
    primary_signal_table: str = "sentiment_scores"
    primary_entity_column: str = "ticker"
    legacy_signal_table: str = "entity_signals"
    legacy_entity_column: str = "entity_id"
    score_column: str = "combined_score"
    tag_column: str = "sentiment_tag"
    created_at_column: str = "created_at"

    # Finance aliases from Vitruvyan MCP contracts
    tool_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "screen_tickers": "screen_entities",
            "screen_entities": "screen_entities",
            "compare_tickers": "compare_entities",
            "compare_entities": "compare_entities",
            "query_sentiment": "query_signals",
            "query_signals": "query_signals",
            "generate_vee_summary": "generate_vee_summary",
            "extract_semantic_context": "extract_semantic_context",
        }
    )
    screen_profile_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "balanced_mid": "balanced",
            "momentum_focus": "aggressive",
            "trend_follow": "aggressive",
            "short_spec": "aggressive",
            "sentiment_boost": "custom",
            "balanced": "balanced",
            "aggressive": "aggressive",
            "conservative": "conservative",
            "custom": "custom",
        }
    )
    compare_criteria_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "composite": "composite",
            "momentum": "factor_1",
            "trend": "factor_2",
            "volatility": "factor_3",
            "sentiment": "factor_4",
            "fundamentals": "factor_5",
            "factor_1": "factor_1",
            "factor_2": "factor_2",
            "factor_3": "factor_3",
            "factor_4": "factor_4",
            "factor_5": "factor_5",
        }
    )


def resolve_finance_tool_name(tool_name: str) -> str:
    """
    Resolve finance/legacy tool names to canonical executor names.

    Unknown names are returned as-is.
    """
    cfg = FinanceMCPConfig()
    return cfg.tool_aliases.get((tool_name or "").strip(), (tool_name or "").strip())


def normalize_finance_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize finance tool arguments into canonical MCP shape.

    Examples:
    - `screen_tickers(tickers=[...])` -> `screen_entities(entity_ids=[...])`
    - `query_sentiment(ticker='AAPL', days=7)` -> `query_signals(entity_id='AAPL', time_window=7)`
    """
    cfg = FinanceMCPConfig()
    canonical_tool = resolve_finance_tool_name(tool_name)
    normalized: Dict[str, Any] = dict(args or {})

    if canonical_tool == "screen_entities":
        tickers = normalized.pop("tickers", None)
        if tickers and "entity_ids" not in normalized:
            normalized["entity_ids"] = tickers

        profile = str(normalized.get("profile", cfg.default_screen_profile)).strip().lower()
        normalized["profile"] = cfg.screen_profile_aliases.get(profile, "balanced")
        normalized.pop("horizon", None)

    elif canonical_tool == "compare_entities":
        tickers = normalized.pop("tickers", None)
        if tickers and "entity_ids" not in normalized:
            normalized["entity_ids"] = tickers

        criteria = str(normalized.get("criteria", "composite")).strip().lower()
        normalized["criteria"] = cfg.compare_criteria_aliases.get(criteria, "composite")

    elif canonical_tool == "query_signals":
        ticker = normalized.pop("ticker", None)
        if ticker and "entity_id" not in normalized:
            normalized["entity_id"] = ticker

        days = normalized.pop("days", None)
        if days is not None and "time_window" not in normalized:
            normalized["time_window"] = days

        window = int(normalized.get("time_window", cfg.default_signal_window_days))
        window = max(cfg.min_signal_window_days, min(cfg.max_signal_window_days, window))
        normalized["time_window"] = window

        include_phrases = normalized.pop("include_phrases", None)
        if include_phrases is not None and "include_context" not in normalized:
            normalized["include_context"] = bool(include_phrases)

    elif canonical_tool == "generate_vee_summary":
        ticker = normalized.pop("ticker", None)
        if ticker and "entity_id" not in normalized:
            normalized["entity_id"] = ticker
        language = str(normalized.get("language", cfg.default_language)).strip().lower()
        normalized["language"] = language or cfg.default_language

    return normalized


def get_finance_signal_source_candidates(
    table_override: Optional[str] = None,
    entity_column_override: Optional[str] = None,
) -> Dict[str, tuple[str, ...]]:
    """Return ordered fallback candidates for sentiment/signal reads."""
    cfg = FinanceMCPConfig()
    return {
        "tables": _ordered_unique(
            (
                table_override or "",
                cfg.primary_signal_table,
                cfg.legacy_signal_table,
            )
        ),
        "entity_columns": _ordered_unique(
            (
                entity_column_override or "",
                cfg.primary_entity_column,
                cfg.legacy_entity_column,
            )
        ),
    }


def build_finance_phrase_samples(entity_id: str, limit: int = 3) -> list[str]:
    """Build deterministic fallback phrases (Vitruvyan-compatible style)."""
    canonical = (entity_id or "entity").strip() or "entity"
    samples = [
        f"Positive outlook on {canonical}",
        f"{canonical} showing resilient momentum",
        f"Market sentiment favors {canonical}",
    ]
    bounded_limit = max(0, int(limit))
    return samples[:bounded_limit]

