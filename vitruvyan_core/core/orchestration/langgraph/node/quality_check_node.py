"""
🔍 Quality Check Node - PHASE 2.2 Consolidation
=======================================================
Sacred Order: Reason (Data Quality & Validation)
Epistemic Layer: Neural Engine → Quality Validation → Output

CONSOLIDATED FROM:
- fallback_node.py (NE ranking check + PG fallback + CrewAI background)
- validation_node.py (ticker validation + data freshness + error handling)

OPTIMIZATION:
- Single responsibility: All data quality checks in one place
- Centralized ticker extraction from NE output
- Batch PostgresAgent queries (trend_logs, momentum_logs, volatility_logs)
- Unified error/warning structure

STATE INPUTS:
- raw_output: dict - Neural Engine response
- tickers: list - Ticker symbols
- horizon: str - Time horizon
- intent: str - User intent
- route: str - Previous routing state

STATE OUTPUTS:
- validation: dict - {errors: [], warnings: []}
- route: str - "ne_valid", "pg_fallback", "no_data", "validation_error"
- raw_output: dict - Potentially updated with PG fallback data
- ok: bool - Overall quality check status
- error: str - Error message if failed
"""

import logging
import threading
from typing import Dict, Any, List
from datetime import datetime

import requests
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.orchestration.langgraph.shared.state_preserv import preserve_ux_state  # 🎭 UX state preservation

logger = logging.getLogger(__name__)

# Configuration
FRESHNESS_DAYS = 7
CREW_URL = "http://vitruvyan_api_crewai:8005/run"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _is_empty_ranking(ranking: dict) -> bool:
    """
    Check if Neural Engine ranking is empty or invalid
    
    Returns True if:
    - ranking is None
    - ranking is empty dict
    - all values in ranking dict are falsy
    """
    if not ranking:
        return True
    if isinstance(ranking, dict):
        return all((not v) for v in ranking.values())
    return False


def _extract_tickers_from_ne_output(raw_output: Dict[str, Any]) -> List[str]:
    """
    Extract ticker list from Neural Engine output if state["tickers"] is empty
    
    Extraction priority:
    1. ranking.stocks[].ticker
    2. sentiment keys
    
    Returns:
        List of ticker symbols (empty list if none found)
    """
    tickers = []
    
    # Try extracting from ranking.stocks
    ranking = raw_output.get("ranking", {})
    stocks = ranking.get("stocks", [])
    
    if stocks:
        tickers = [stock.get("ticker") for stock in stocks if "ticker" in stock]
        if tickers:
            logger.info(f"🔍 [QUALITY_CHECK] Extracted {len(tickers)} tickers from NE ranking: {tickers}")
            return tickers
    
    # Fallback: try sentiment data
    sentiment_data = raw_output.get("sentiment", {})
    if sentiment_data:
        tickers = list(sentiment_data.keys())
        if tickers:
            logger.info(f"🔍 [QUALITY_CHECK] Extracted {len(tickers)} tickers from sentiment: {tickers}")
            return tickers
    
    logger.warning("⚠️ [QUALITY_CHECK] No tickers found in NE output")
    return []


def _validate_ticker_status(tickers: List[str], pg: PostgresAgent) -> Dict[str, List[str]]:
    """
    Validate ticker active status in database
    
    Returns:
        Dict with errors and warnings lists
    """
    result = {"errors": [], "warnings": []}
    
    try:
        rows = pg.fetch_all("SELECT ticker FROM tickers WHERE active = true")
        active_set = {r[0].upper() for r in rows}
        
        for tk in tickers:
            if tk.upper() not in active_set:
                result["errors"].append(f"Ticker {tk} non attivo o non riconosciuto")
        
        logger.debug(f"🔍 [QUALITY_CHECK] Validated {len(tickers)} tickers, {len(result['errors'])} inactive")
        
    except Exception as e:
        result["warnings"].append(f"Errore query ticker: {e}")
        logger.error(f"❌ [QUALITY_CHECK] Ticker validation failed: {e}")
    
    return result


def _validate_data_freshness(tickers: List[str], pg: PostgresAgent) -> Dict[str, List[str]]:
    """
    Validate data freshness for tickers (trend_logs, momentum_logs, volatility_logs)
    
    Returns:
        Dict with errors and warnings lists
    """
    result = {"errors": [], "warnings": []}
    
    try:
        for tk in tickers:
            # Check trend_logs freshness
            rows = pg.fetch_all(
                "SELECT MAX(timestamp) FROM trend_logs WHERE ticker=%s",
                (tk,)
            )
            
            if rows and rows[0][0]:
                age_days = (datetime.now() - rows[0][0]).days
                if age_days > FRESHNESS_DAYS:
                    result["warnings"].append(
                        f"Dati trend per {tk} vecchi di {age_days} giorni"
                    )
            else:
                result["warnings"].append(f"Nessun dato trend per {tk}")
        
        logger.debug(f"🔍 [QUALITY_CHECK] Data freshness check: {len(result['warnings'])} warnings")
        
    except Exception as e:
        result["warnings"].append(f"Errore freschezza dati: {e}")
        logger.error(f"❌ [QUALITY_CHECK] Data freshness check failed: {e}")
    
    return result


def _try_postgres_fallback(tickers: List[str], pg: PostgresAgent) -> tuple[bool, Dict[str, Any]]:
    """
    Try to fetch data from PostgreSQL as fallback when NE is empty
    
    Queries trend_logs, momentum_logs, volatility_logs for each ticker
    
    Returns:
        Tuple of (data_found: bool, results: dict)
    """
    results = {}
    pg_found = False
    
    for tk in tickers:
        try:
            rows = {}
            for table in ["trend_logs", "momentum_logs", "volatility_logs"]:
                res = pg.fetch(
                    f"SELECT * FROM {table} WHERE ticker=%s ORDER BY timestamp DESC LIMIT 1",
                    (tk,)
                )
                if res:
                    rows[table] = res
                    pg_found = True
            
            results[tk] = {"pg_result": rows}
            
        except Exception as e:
            results[tk] = {"error": str(e)}
            logger.warning(f"⚠️ [QUALITY_CHECK] PG fallback failed for {tk}: {e}")
    
    if pg_found:
        logger.info(f"✅ [QUALITY_CHECK] PG fallback successful for {len(results)} tickers")
    else:
        logger.warning(f"⚠️ [QUALITY_CHECK] PG fallback found no data")
    
    return pg_found, results


def _spawn_crew_background(tickers: List[str], horizon: str, intent: str, amount: Any = None) -> None:
    """
    Launch CrewAI analysis in background thread (non-blocking)
    
    Used when both NE and PG have no data
    """
    
    def run_crew_analysis():
        """Background thread function for CrewAI calls"""
        for tk in tickers:
            try:
                payload = {
                    "ticker": tk,
                    "horizon": horizon,
                    "intent": intent
                }
                if amount:
                    payload["amount"] = amount
                
                resp = requests.post(CREW_URL, json=payload, timeout=15)
                resp.raise_for_status()
                
                logger.info(f"✅ [QUALITY_CHECK][CREW] Analysis complete for {tk}")
                
            except Exception as e:
                logger.error(f"❌ [QUALITY_CHECK][CREW] Analysis failed for {tk}: {e}")
    
    try:
        threading.Thread(
            target=run_crew_analysis,
            daemon=True
        ).start()
        logger.info(f"🧠 [QUALITY_CHECK] CrewAI launched in background for {len(tickers)} tickers")
    except Exception as e:
        logger.error(f"❌ [QUALITY_CHECK] Failed to launch CrewAI background: {e}")


# ============================================================================
# MAIN QUALITY CHECK NODE
# ============================================================================

@preserve_ux_state
def quality_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔍 Unified Quality Check Node - PHASE 2.2
    
    Consolidates fallback_node + validation_node logic:
    
    1. Check NE ranking validity
    2. Extract tickers from NE output if missing
    3. Validate ticker active status
    4. Validate data freshness
    5. Try PostgreSQL fallback if NE empty
    6. Launch CrewAI background if all sources empty
    
    Returns:
        Updated state with:
        - validation: {errors: [], warnings: []}
        - route: "ne_valid" | "pg_fallback" | "no_data" | "validation_error"
        - raw_output: potentially updated with PG data
        - ok: bool
    """
    
    logger.info("🔍 [QUALITY_CHECK] Starting unified quality validation...")
    
    # Initialize validation structure
    validation = {"errors": [], "warnings": []}
    
    # Extract state
    raw_output = state.get("raw_output", {})
    tickers = state.get("tickers", [])
    horizon = state.get("horizon", "medium")
    intent = state.get("intent", "analysis")
    route = state.get("route", "exec_node")
    
    # ========================================================================
    # STEP 1: Extract tickers from NE output if missing (centralized logic)
    # ========================================================================
    if not tickers:
        extracted_tickers = _extract_tickers_from_ne_output(raw_output)
        
        if extracted_tickers:
            tickers = extracted_tickers
            state["tickers"] = tickers
            validation["warnings"].append(
                f"Ticker estratti da Neural Engine output: {', '.join(tickers)}"
            )
        else:
            validation["errors"].append("Nessun ticker riconosciuto nell'input")
            logger.error("❌ [QUALITY_CHECK] No tickers available after extraction")
    
    # ========================================================================
    # STEP 2: Check NE ranking validity
    # ========================================================================
    ranking = raw_output.get("ranking") if isinstance(raw_output, dict) else None
    ne_empty = (
        not raw_output
        or route == "error"
        or _is_empty_ranking(ranking)
    )
    
    if not ne_empty:
        # NE is valid → proceed with validation
        logger.info("✅ [QUALITY_CHECK] Neural Engine ranking valid")
        
        # Validate tickers if available
        if tickers:
            pg = PostgresAgent()
            
            # Ticker status validation
            ticker_validation = _validate_ticker_status(tickers, pg)
            validation["errors"].extend(ticker_validation["errors"])
            validation["warnings"].extend(ticker_validation["warnings"])
            
            # Data freshness validation
            freshness_validation = _validate_data_freshness(tickers, pg)
            validation["warnings"].extend(freshness_validation["warnings"])
        
        # Check if raw_output exists
        if not raw_output:
            validation["errors"].append("raw_output mancante o vuoto")
        
        # Propagate validation to state
        state["validation"] = validation
        state["result"] = state.get("result", {})
        state["result"]["validation"] = validation
        
        # If errors → set validation_error route
        if validation["errors"]:
            logger.warning(f"⚠️ [QUALITY_CHECK] Validation errors: {validation['errors']}")
            state["route"] = "validation_error"
            state["response"] = {
                "action": "answer",
                "narrative": "Errore di validazione: " + "; ".join(validation["errors"]),
                "explainability": {
                    "simple": "Dati non validi",
                    "technical": "; ".join(validation["warnings"]),
                    "detailed": validation,
                },
            }
            state["ok"] = False
            state["error"] = "; ".join(validation["errors"])
        else:
            logger.info(f"✅ [QUALITY_CHECK] Validation passed: {len(validation['warnings'])} warnings")
            state["route"] = "ne_valid"
            state["ok"] = True
            state["error"] = None
        
        return state
    
    # ========================================================================
    # STEP 3: NE is empty → Try PostgreSQL fallback
    # ========================================================================
    logger.warning("⚠️ [QUALITY_CHECK] Neural Engine empty, trying PostgreSQL fallback...")
    
    if not tickers:
        logger.error("❌ [QUALITY_CHECK] No tickers available for fallback")
        state["route"] = "error"
        state["raw_output"] = {}
        state["ok"] = False
        state["error"] = "No tickers available for fallback"
        state["validation"] = validation
        return state
    
    pg = PostgresAgent()
    pg_found, pg_results = _try_postgres_fallback(tickers, pg)
    
    if pg_found:
        logger.info(f"✅ [QUALITY_CHECK] PostgreSQL fallback successful for {tickers}")
        state["route"] = "pg_fallback"
        state["raw_output"] = pg_results
        state["ok"] = True
        state["error"] = None
        state["validation"] = validation
        return state
    
    # ========================================================================
    # STEP 4: PG is empty → Launch CrewAI background (non-blocking)
    # ========================================================================
    logger.warning("⚠️ [QUALITY_CHECK] PostgreSQL empty, launching CrewAI background...")
    
    _spawn_crew_background(tickers, horizon, intent, amount=state.get("budget"))
    
    # Immediate response (don't block user)
    validation["warnings"].append("Analisi CrewAI avviata in background")
    state["route"] = "no_data"
    state["raw_output"] = {}
    state["ok"] = False
    state["error"] = "Data not available yet"
    state["validation"] = validation
    
    logger.info("🧠 [QUALITY_CHECK] CrewAI launched, returning no_data route")
    
    return state
