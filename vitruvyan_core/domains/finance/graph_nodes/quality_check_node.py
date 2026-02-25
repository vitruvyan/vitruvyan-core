"""
Quality Check Node — Finance Domain
====================================

Validates Neural Engine output and provides PostgreSQL fallback.

Pipeline position:
  screener → quality_check → output_normalizer

Validation steps:
  1. Extract tickers from NE output (if missing from state)
  2. Validate NE ranking (empty check)
  3. If NE valid: validate tickers (active in PG) + data freshness check
  4. If NE empty: try PostgreSQL fallback (trend_logs, momentum_logs, volatility_logs)
  5. Factor flattening (nested factors → top-level keys)

State outputs:
  - validation: {errors: [], warnings: []}
  - route: "ne_valid" | "pg_fallback" | "no_data" | "validation_error"
  - raw_output: potentially updated with PG fallback data
  - ok: bool
  - error: str | None

Ported from vitruvyan upstream (quality_check_node.py, 576 lines)
Adapted: February 24, 2026 (mercator domain pattern)
Removed: CrewAI background spawning (not applicable)
Removed: preserve_ux_state decorator (not in mercator)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

FRESHNESS_DAYS = 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_empty_ranking(ranking) -> bool:
    """Return True when the NE ranking carries no stock data."""
    if not ranking:
        return True
    if isinstance(ranking, dict):
        return not ranking.get("stocks")
    return False


def _extract_tickers_from_ne_output(raw_output: Dict[str, Any]) -> List[str]:
    """Extract ticker symbols from NE ranking or sentiment keys."""
    ranking = raw_output.get("ranking", {})
    stocks = ranking.get("stocks", [])
    if stocks:
        tickers = [s.get("ticker") for s in stocks if "ticker" in s]
        if tickers:
            logger.info(f"[quality_check] Extracted {len(tickers)} tickers from NE ranking")
            return tickers
    sentiment = raw_output.get("sentiment", {})
    if sentiment:
        tickers = list(sentiment.keys())
        if tickers:
            logger.info(f"[quality_check] Extracted {len(tickers)} tickers from sentiment")
            return tickers
    return []


def _validate_tickers(tickers: List[str], pg) -> Dict[str, List[str]]:
    """Check which tickers are active in the tickers table."""
    result: Dict[str, List[str]] = {"errors": [], "warnings": []}
    try:
        rows = pg.fetch("SELECT ticker FROM tickers WHERE active = true")
        active = {r["ticker"].upper() for r in rows}
        for tk in tickers:
            if tk.upper() not in active:
                result["errors"].append(f"Ticker {tk} non attivo o non riconosciuto")
    except Exception as e:
        result["warnings"].append(f"Ticker validation query failed: {e}")
        logger.error(f"[quality_check] Ticker validation error: {e}")
    return result


def _validate_freshness(tickers: List[str], pg) -> Dict[str, List[str]]:
    """Check data freshness via trend_logs timestamps."""
    result: Dict[str, List[str]] = {"errors": [], "warnings": []}
    try:
        for tk in tickers:
            rows = pg.fetch(
                "SELECT MAX(timestamp) as max_ts FROM trend_logs WHERE ticker=%s", (tk,)
            )
            if rows and rows[0].get("max_ts"):
                age = (datetime.now() - rows[0]["max_ts"]).days
                if age > FRESHNESS_DAYS:
                    result["warnings"].append(
                        f"Dati trend per {tk} vecchi di {age} giorni"
                    )
            else:
                result["warnings"].append(f"Nessun dato trend per {tk}")
    except Exception as e:
        result["warnings"].append(f"Freshness check failed: {e}")
    return result


# ---------------------------------------------------------------------------
# Z-score calculators (for PG fallback conversion to NE-compatible format)
# ---------------------------------------------------------------------------

def _momentum_z(data: Dict[str, Any]) -> float:
    """RSI-based momentum z-score."""
    rsi = data.get("rsi")
    if rsi is None:
        return 0.0
    return round(max(min((rsi - 50) / 15.0, 2.0), -2.0), 2)


def _trend_z(data: Dict[str, Any]) -> float:
    """Trend alignment z-score from short/medium/long trend signals."""
    trends = [data.get("short_trend"), data.get("medium_trend"), data.get("long_trend")]
    bullish = sum(1 for t in trends if t == "bullish")
    bearish = sum(1 for t in trends if t == "bearish")
    if bullish == 3:
        return 1.5
    if bullish == 2:
        return 0.8
    if bearish == 3:
        return -1.5
    if bearish == 2:
        return -0.8
    return 0.0


def _vola_z(data: Dict[str, Any]) -> float:
    """Standard deviation-based volatility z-score."""
    stdev = data.get("stdev")
    if stdev is None:
        return 0.0
    return round(max(min((stdev - 1.5) / 0.8, 2.0), -2.0), 2)


# ---------------------------------------------------------------------------
# PostgreSQL fallback
# ---------------------------------------------------------------------------

def _pg_fallback(tickers: List[str], pg) -> Tuple[bool, Dict[str, Any]]:
    """Build NE-compatible ranking dict from PostgreSQL log tables."""
    ranking = []
    for tk in tickers:
        entry: Dict[str, Any] = {
            "ticker": tk,
            "source": "postgresql_fallback",
            "composite_score": 0.0,
        }
        try:
            trend = pg.fetch(
                "SELECT short_trend, medium_trend, long_trend, "
                "sma_short, sma_medium, sma_long "
                "FROM trend_logs WHERE ticker=%s ORDER BY timestamp DESC LIMIT 1",
                (tk,),
            )
            momentum = pg.fetch(
                "SELECT rsi, signal, macd, macd_signal "
                "FROM momentum_logs WHERE ticker=%s ORDER BY timestamp DESC LIMIT 1",
                (tk,),
            )
            vola = pg.fetch(
                "SELECT atr, stdev, signal "
                "FROM volatility_logs WHERE ticker=%s ORDER BY timestamp DESC LIMIT 1",
                (tk,),
            )

            if not (trend or momentum or vola):
                continue

            if trend:
                r = trend[0]
                entry.update({
                    "short_trend": r.get("short_trend"),
                    "medium_trend": r.get("medium_trend"),
                    "long_trend": r.get("long_trend"),
                    "sma_short": float(r["sma_short"]) if r.get("sma_short") else None,
                    "sma_medium": float(r["sma_medium"]) if r.get("sma_medium") else None,
                    "sma_long": float(r["sma_long"]) if r.get("sma_long") else None,
                })
            if momentum:
                r = momentum[0]
                entry.update({
                    "rsi": float(r["rsi"]) if r.get("rsi") else None,
                    "momentum_signal": r.get("signal"),
                    "macd": float(r["macd"]) if r.get("macd") else None,
                    "macd_signal": float(r["macd_signal"]) if r.get("macd_signal") else None,
                })
            if vola:
                r = vola[0]
                entry.update({
                    "atr": float(r["atr"]) if r.get("atr") else None,
                    "stdev": float(r["stdev"]) if r.get("stdev") else None,
                    "volatility_signal": r.get("signal"),
                })

            entry["momentum_z"] = _momentum_z(entry)
            entry["trend_z"] = _trend_z(entry)
            entry["vola_z"] = _vola_z(entry)
            entry["sentiment_z"] = None
            ranking.append(entry)
            logger.info(
                f"[quality_check] PG fallback for {tk}: "
                f"trend={entry.get('short_trend')}, rsi={entry.get('rsi')}"
            )
        except Exception as e:
            logger.warning(f"[quality_check] PG fallback failed for {tk}: {e}")

    if ranking:
        # Build summary text for compose_node compatibility
        summaries = []
        for r in ranking:
            parts = [r["ticker"]]
            if r.get("trend_z") is not None:
                parts.append(f"trend_z={r['trend_z']}")
            if r.get("momentum_z") is not None:
                parts.append(f"momentum_z={r['momentum_z']}")
            if r.get("vola_z") is not None:
                parts.append(f"vola_z={r['vola_z']}")
            summaries.append(" ".join(parts))

        summary_text = (
            f"PostgreSQL fallback analysis for {len(ranking)} entities: "
            + "; ".join(summaries)
        )

        return True, {
            "ranking": {"stocks": ranking, "etf": [], "funds": []},
            "summary": summary_text,
            "source": "postgresql_fallback",
        }
    return False, {}


# ---------------------------------------------------------------------------
# Main node
# ---------------------------------------------------------------------------

def quality_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate NE output, flatten factors, optionally fall back to PostgreSQL.

    Routes (written to state['route']):
      - ne_valid          NE data present and valid
      - pg_fallback       NE empty, PG data substituted
      - no_data           Nothing available
      - validation_error  Ticker validation failed
    """
    logger.info("[quality_check] Starting validation...")
    validation: Dict[str, List[str]] = {"errors": [], "warnings": []}
    raw_output = state.get("raw_output", {})
    tickers = state.get("entity_ids") or state.get("tickers", [])

    # ── Step 1: Extract tickers from raw_output if missing ──
    if not tickers:
        extracted = _extract_tickers_from_ne_output(raw_output)
        if extracted:
            tickers = extracted
            state["tickers"] = tickers
            validation["warnings"].append(
                f"Ticker estratti da NE output: {', '.join(tickers)}"
            )
        else:
            validation["errors"].append("Nessun ticker riconosciuto nell'input")

    # ── Step 2: Is the NE ranking usable? ──
    ranking = raw_output.get("ranking") if isinstance(raw_output, dict) else None
    ne_empty = (
        not raw_output
        or state.get("route") in ("screener_error", "screener_timeout", "error")
        or _is_empty_ranking(ranking)
    )

    if not ne_empty:
        # ── NE data valid — flatten factors + optional PG validation ──
        logger.info("[quality_check] NE ranking valid")
        stocks = ranking.get("stocks", []) if isinstance(ranking, dict) else []
        for stock in stocks:
            factors = stock.get("factors")
            if isinstance(factors, dict):
                for k, v in factors.items():
                    if k not in stock:
                        stock[k] = v

        if tickers:
            try:
                from core.agents.postgres_agent import PostgresAgent
                pg = PostgresAgent()
                tv = _validate_tickers(tickers, pg)
                validation["errors"].extend(tv["errors"])
                validation["warnings"].extend(tv["warnings"])
                fv = _validate_freshness(tickers, pg)
                validation["warnings"].extend(fv["warnings"])
            except Exception as e:
                validation["warnings"].append(f"PG validation unavailable: {e}")

        state["validation"] = validation
        if validation["errors"]:
            state["route"] = "validation_error"
            state["ok"] = False
            state["error"] = "; ".join(validation["errors"])
        else:
            # Build numerical_panel from NE stocks
            numerical_panel = []
            for s in stocks:
                entry = {
                    "ticker": s.get("ticker"),
                    "composite_score": s.get("composite_score", 0.0),
                    "momentum_z": s.get("momentum_z"),
                    "trend_z": s.get("trend_z"),
                    "vola_z": s.get("vola_z"),
                    "sentiment_z": s.get("sentiment_z"),
                    "short_trend": s.get("short_trend"),
                    "medium_trend": s.get("medium_trend"),
                    "long_trend": s.get("long_trend"),
                    "rsi": s.get("rsi"),
                    "source": s.get("source", "neural_engine"),
                }
                # Forward dynamic z-scores (fundamentals, etc.)
                for key, val in s.items():
                    if key.endswith("_z") and key not in entry and val is not None:
                        entry[key] = val
                numerical_panel.append(entry)
            state["numerical_panel"] = numerical_panel
            state["route"] = "ne_valid"
            state["ok"] = True
            state["error"] = None
        return state

    # ── Step 3: NE empty → PostgreSQL fallback ──
    logger.warning("[quality_check] NE empty, trying PostgreSQL fallback...")
    if not tickers:
        state["route"] = "no_data"
        state["raw_output"] = {}
        state["ok"] = False
        state["error"] = "No tickers available for fallback"
        state["validation"] = validation
        return state

    try:
        from core.agents.postgres_agent import PostgresAgent
        pg = PostgresAgent()
        found, pg_data = _pg_fallback(tickers, pg)
        if found:
            logger.info(f"[quality_check] PG fallback successful for {tickers}")
            state["route"] = "pg_fallback"
            state["raw_output"] = pg_data

            # Build numerical_panel for downstream (compose, advisor)
            stocks = pg_data.get("ranking", {}).get("stocks", [])
            numerical_panel = []
            for s in stocks:
                entry = {
                    "ticker": s.get("ticker"),
                    "composite_score": s.get("composite_score", 0.0),
                    "momentum_z": s.get("momentum_z"),
                    "trend_z": s.get("trend_z"),
                    "vola_z": s.get("vola_z"),
                    "sentiment_z": s.get("sentiment_z"),
                    "short_trend": s.get("short_trend"),
                    "medium_trend": s.get("medium_trend"),
                    "long_trend": s.get("long_trend"),
                    "rsi": s.get("rsi"),
                    "source": s.get("source", "pg_fallback"),
                }
                # Forward dynamic z-scores (fundamentals, etc.)
                for key, val in s.items():
                    if key.endswith("_z") and key not in entry and val is not None:
                        entry[key] = val
                numerical_panel.append(entry)
            state["numerical_panel"] = numerical_panel
            state["ok"] = True
            state["error"] = None
            state["validation"] = validation
            return state
    except Exception as e:
        logger.error(f"[quality_check] PG fallback error: {e}")

    # ── Step 4: Nothing available ──
    state["route"] = "no_data"
    state["raw_output"] = {}
    state["ok"] = False
    state["error"] = "No data available from NE or PostgreSQL"
    state["validation"] = validation
    return state
