"""
🔍 Quality Check Node - PHASE 2.2 Consolidation
=======================================================
Sacred Order: Reason (Data Quality & Validation)
Epistemic Layer: Neural Engine → Quality Validation → Output

CONSOLIDATED FROM:
- fallback_node.py (NE ranking check + PG fallback + CrewAI background)
- validation_node.py (entity_id validation + data freshness + error handling)

OPTIMIZATION:
- Single responsibility: All data quality checks in one place
- Centralized entity_id extraction from NE output
- Batch PostgresAgent queries (trend_logs, momentum_logs, volatility_logs)
- Unified error/warning structure

STATE INPUTS:
- raw_output: dict - Neural Engine response
- entity_ids: list - EntityId symbols
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


def _extract_entities_from_output(raw_output: Dict[str, Any]) -> List[str]:
    """
    Extract entity_id list from Neural Engine output if state["entity_ids"] is empty
    
    Extraction priority:
    1. ranking.entities[].entity_id
    2. sentiment keys
    
    Returns:
        List of entity_id symbols (empty list if none found)
    """
    entity_ids = []
    
    # Try extracting from ranking.entities (COO fix: defensive type check Feb 10, 2026)
    ranking = raw_output.get("ranking", {})
    
    # Handle case where ranking is a list instead of expected dict
    if isinstance(ranking, list):
        # Ranking is already list of entities
        entities = ranking
    elif isinstance(ranking, dict):
        # Ranking is dict with "entities" key
        entities = ranking.get("entities", [])
    else:
        logger.warning(f"⚠️ [QUALITY_CHECK] Unexpected ranking type: {type(ranking)}")
        entities = []
    
    if entities:
        entity_ids = [entity.get("entity_id") for entity in entities if isinstance(entity, dict) and "entity_id" in entity]
        if entity_ids:
            logger.info(f"🔍 [QUALITY_CHECK] Extracted {len(entity_ids)} entity_ids from NE ranking: {entity_ids}")
            return entity_ids
    
    # Fallback: try sentiment data
    sentiment_data = raw_output.get("sentiment", {})
    if sentiment_data:
        entity_ids = list(sentiment_data.keys())
        if entity_ids:
            logger.info(f"🔍 [QUALITY_CHECK] Extracted {len(entity_ids)} entity_ids from sentiment: {entity_ids}")
            return entity_ids
    
    logger.warning("⚠️ [QUALITY_CHECK] No entity_ids found in NE output")
    return []


def _validate_entity_status(entity_ids: List[str], pg: PostgresAgent) -> Dict[str, List[str]]:
    """
    Validate entity_id active status in database
    
    Returns:
        Dict with errors and warnings lists
    """
    result = {"errors": [], "warnings": []}
    
    try:
        rows = pg.fetch_all("SELECT entity_id FROM entity_ids WHERE active = true")
        active_set = {r[0].upper() for r in rows}
        
        for tk in entity_ids:
            if tk.upper() not in active_set:
                result["errors"].append(f"EntityId {tk} non attivo o non riconosciuto")
        
        logger.debug(f"🔍 [QUALITY_CHECK] Validated {len(entity_ids)} entity_ids, {len(result['errors'])} inactive")
        
    except Exception as e:
        result["warnings"].append(f"Errore query entity_id: {e}")
        logger.error(f"❌ [QUALITY_CHECK] EntityId validation failed: {e}")
    
    return result


def _validate_data_freshness(entity_ids: List[str], pg: PostgresAgent) -> Dict[str, List[str]]:
    """
    Validate data freshness for entity_ids (trend_logs, momentum_logs, volatility_logs)
    
    Returns:
        Dict with errors and warnings lists
    """
    result = {"errors": [], "warnings": []}
    
    try:
        for tk in entity_ids:
            # Check trend_logs freshness
            rows = pg.fetch_all(
                "SELECT MAX(timestamp) FROM trend_logs WHERE entity_id=%s",
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


def _try_postgres_fallback(entity_ids: List[str], pg: PostgresAgent) -> tuple[bool, Dict[str, Any]]:
    """
    Try to fetch data from PostgreSQL as fallback when NE is empty
    
    Queries trend_logs, momentum_logs, volatility_logs for each entity_id
    
    Returns:
        Tuple of (data_found: bool, results: dict)
    """
    results = {}
    pg_found = False
    
    for tk in entity_ids:
        try:
            rows = {}
            for table in ["trend_logs", "momentum_logs", "volatility_logs"]:
                res = pg.fetch(
                    f"SELECT * FROM {table} WHERE entity_id=%s ORDER BY timestamp DESC LIMIT 1",
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
        logger.info(f"✅ [QUALITY_CHECK] PG fallback successful for {len(results)} entity_ids")
    else:
        logger.warning(f"⚠️ [QUALITY_CHECK] PG fallback found no data")
    
    return pg_found, results


def _spawn_crew_background(entity_ids: List[str], horizon: str, intent: str, amount: Any = None) -> None:
    """
    Launch CrewAI analysis in background thread (non-blocking)
    
    Used when both NE and PG have no data
    """
    
    def run_crew_analysis():
        """Background thread function for CrewAI calls"""
        for tk in entity_ids:
            try:
                payload = {
                    "entity_id": tk,
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
        logger.info(f"🧠 [QUALITY_CHECK] CrewAI launched in background for {len(entity_ids)} entity_ids")
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
    2. Extract entity_ids from NE output if missing
    3. Validate entity_id active status
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
    
    # Extract state (COO fix: defensive type check for raw_output, Feb 10, 2026)
    raw_output_raw = state.get("raw_output", {})
    
    # Handle case where raw_output is list instead of expected dict
    if isinstance(raw_output_raw, list):
        logger.warning(f"⚠️ [QUALITY_CHECK] raw_output is list (len={len(raw_output_raw)}), wrapping in dict")
        raw_output = {"ranking": raw_output_raw}  # Assume list is ranking entities
    elif isinstance(raw_output_raw, dict):
        raw_output = raw_output_raw
    else:
        logger.warning(f"⚠️ [QUALITY_CHECK] Unexpected raw_output type: {type(raw_output_raw)}")
        raw_output = {}
    
    entity_ids = state.get("entity_ids", [])
    horizon = state.get("horizon", "medium")
    intent = state.get("intent", "analysis")
    route = state.get("route", "exec_node")
    
    # ========================================================================
    # STEP 1: Extract entity_ids from NE output if missing (centralized logic)
    # ========================================================================
    if not entity_ids:
        extracted_entities = _extract_entities_from_output(raw_output)
        
        if extracted_entities:
            entity_ids = extracted_entities
            state["entity_ids"] = entity_ids
            validation["warnings"].append(
                f"EntityId estratti da Neural Engine output: {', '.join(entity_ids)}"
            )
        else:
            validation["errors"].append("Nessun entity_id riconosciuto nell'input")
            logger.error("❌ [QUALITY_CHECK] No entity_ids available after extraction")
    
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
        
        # Validate entity_ids if available
        if entity_ids:
            pg = PostgresAgent()
            
            # EntityId status validation
            entity_validation = _validate_entity_status(entity_ids, pg)
            validation["errors"].extend(entity_validation["errors"])
            validation["warnings"].extend(entity_validation["warnings"])
            
            # Data freshness validation
            freshness_validation = _validate_data_freshness(entity_ids, pg)
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
    
    if not entity_ids:
        logger.error("❌ [QUALITY_CHECK] No entity_ids available for fallback")
        state["route"] = "error"
        state["raw_output"] = {}
        state["ok"] = False
        state["error"] = "No entity_ids available for fallback"
        state["validation"] = validation
        return state
    
    pg = PostgresAgent()
    pg_found, pg_results = _try_postgres_fallback(entity_ids, pg)
    
    if pg_found:
        logger.info(f"✅ [QUALITY_CHECK] PostgreSQL fallback successful for {entity_ids}")
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
    
    _spawn_crew_background(entity_ids, horizon, intent, amount=state.get("budget"))
    
    # Immediate response (don't block user)
    validation["warnings"].append("Analisi CrewAI avviata in background")
    state["route"] = "no_data"
    state["raw_output"] = {}
    state["ok"] = False
    state["error"] = "Data not available yet"
    state["validation"] = validation
    
    logger.info("🧠 [QUALITY_CHECK] CrewAI launched, returning no_data route")
    
    return state
