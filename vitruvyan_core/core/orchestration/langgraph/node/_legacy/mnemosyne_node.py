#!/usr/bin/env python3
"""
🔮 Mnemosyne Node - Vector Memory Event Processor
ORCHESTRATION CONTRACT v1.0 COMPLIANT

Event Processor Node (Category 2):
- Consumes Redis Streams events (memory.vector.match.fulfilled)
- Extracts pre-calculated metrics from event payload
- Performs NO domain calculations (see contract section 3.2)

Transport: Redis Streams (persistent event log, NOT Pub/Sub)
Pattern: Extract, don't calculate

Contract Compliance:
- ✅ No sum(), avg(), min(), max() calculations
- ✅ No sorted() on domain criteria
- ✅ Extracts metrics from event producer
- ✅ Thin formatting layer only

Author: Vitruvyan Development Team
Created: 2025-10-20
Refactored: 2026-02-11 (ORCHESTRATION CONTRACT v1.0)
Contract: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def mnemosyne_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mnemosyne Node - Extract semantic search results from Cognitive Bus
    
    Event-Driven Pattern (Redis Streams):
    - Consumes memory.vector.match.fulfilled events
    - Extracts pre-calculated metrics from event producer
    - Formats narrative for compose_node
    
    State Input:
    - conclave_event: Event from Redis Cognitive Bus
    - correlation_id: Request correlation ID
    - trace_log: Accumulated trace log
    
    State Output:
    - mnemosyne_narrative: Formatted narrative
    - mnemosyne_status: "success" | "error" | "no_event"
    - mnemosyne_metrics: Extracted telemetry metrics
    - trace_log: Updated trace log
    - route: "compose" or "error"
    
    Contract Compliance:
    - Event producer pre-calculates all metrics
    - Node extracts, never computes
    """
    node_start = datetime.now()
    logger.info("🔮 Mnemosyne node activated")
    
    # Extract event from state
    conclave_event = state.get("conclave_event")
    correlation_id = state.get("correlation_id", "unknown")
    trace_log = state.get("trace_log", [])
    
    if not conclave_event:
        logger.warning("⚠️ No conclave_event in state")
        return {
            "mnemosyne_narrative": "",
            "mnemosyne_status": "no_event",
            "mnemosyne_metrics": {},
            "trace_log": trace_log,
            "route": "compose"
        }
    
    event_type = conclave_event.get("event_type", "unknown")
    logger.info(f"📨 Processing event: {event_type} (correlation_id: {correlation_id})")
    
    # Route to handler
    if event_type == "memory.vector.match.fulfilled":
        result = _handle_vector_match_fulfilled(conclave_event, node_start)
    else:
        logger.warning(f"⚠️ Unhandled event type: {event_type}")
        result = {
            "mnemosyne_narrative": "",
            "mnemosyne_status": "unhandled_event",
            "mnemosyne_metrics": {"event_type": event_type}
        }
    
    # Update trace log
    trace_log = _update_graph_trace(
        trace_log=trace_log,
        node_name="mnemosyne",
        status=result["mnemosyne_status"],
        metrics=result["mnemosyne_metrics"]
    )
    
    # Determine routing
    route = "compose" if result["mnemosyne_status"] == "success" else "error"
    
    return {
        "mnemosyne_narrative": result.get("mnemosyne_narrative", ""),
        "mnemosyne_status": result["mnemosyne_status"],
        "mnemosyne_metrics": result["mnemosyne_metrics"],
        "trace_log": trace_log,
        "route": route,
        "response": result.get("mnemosyne_narrative", "")
    }


def _handle_vector_match_fulfilled(
    event_data: Dict[str, Any],
    node_start: datetime
) -> Dict[str, Any]:
    """
    Handle memory.vector.match.fulfilled event
    
    Contract Pattern:
    - Extract pre-calculated metrics from event payload
    - No sum(), avg(), sorted() operations
    - Producer calculates, consumer extracts
    
    Event Producer: services/api_memory_orders/adapters/bus_adapter.py
    """
    logger.info("🔮 Processing memory.vector.match.fulfilled")
    
    try:
        payload = event_data.get("payload", {})
        
        # Extract core data (opaque)
        matches = payload.get("matches", [])
        query_text = payload.get("query_text", "")
        
        # ✅ Extract pre-calculated metrics (NO calculation)
        metrics_payload = payload.get("metrics", {})
        avg_similarity = metrics_payload.get("avg_similarity", 0.0)
        max_similarity = metrics_payload.get("max_similarity", 0.0)
        min_similarity = metrics_payload.get("min_similarity", 0.0)
        match_count = metrics_payload.get("match_count", 0)
        top_k = payload.get("top_k", 10)
        
        logger.info(f"📊 Retrieved {match_count} semantic matches (avg_sim={avg_similarity:.3f})")
        
        # Format narrative (presentation only, no calculation)
        narrative = _format_vector_match_narrative(
            matches=matches,
            query_text=query_text,
            avg_similarity=avg_similarity,
            match_count=match_count,
            top_k=top_k
        )
        
        # Node timing
        node_duration_ms = (datetime.now() - node_start).total_seconds() * 1000
        
        # Store extracted metrics
        metrics = {
            "node_duration_ms": node_duration_ms,
            "matches_found": match_count,
            "top_k": top_k,
            "avg_similarity": avg_similarity,  # ✅ Extracted, not calculated
            "max_similarity": max_similarity,  # ✅ From event payload
            "min_similarity": min_similarity,  # ✅ From event payload
            "query_text_length": len(query_text),
            "node_start_time": node_start.isoformat()
        }
        
        logger.info(f"✅ Narrative generated ({match_count} matches, {node_duration_ms:.2f}ms)")
        
        return {
            "mnemosyne_narrative": narrative,
            "mnemosyne_status": "success",
            "mnemosyne_metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"❌ Error handling memory.vector.match.fulfilled: {e}", exc_info=True)
        
        return {
            "mnemosyne_narrative": f"⚠️ Mnemosyne error: {str(e)}",
            "mnemosyne_status": "error",
            "mnemosyne_metrics": {"error": str(e)}
        }


def _format_vector_match_narrative(
    matches: List[Dict[str, Any]],
    query_text: str,
    avg_similarity: float,
    match_count: int,
    top_k: int
) -> str:
    """
    Format vector match results into narrative
    
    Contract Compliance:
    - Receives avg_similarity as parameter (pre-calculated)
    - No sorted() on domain criteria (preserves producer ordering)
    - Pure formatting, zero computation
    """
    if not matches:
        return f"🔮 **Mnemosyne:** No semantic matches found for query: '{query_text[:50]}...'"
    
    narrative_parts = [
        f"🔮 **Mnemosyne Semantic Search**",
        f"**Query:** {query_text}",
        f"**Results:** {match_count}/{top_k} matches (avg similarity: {avg_similarity:.3f})\n"
    ]
    
    # ✅ Iterate in producer-provided order (NO sorted())
    for i, match in enumerate(matches[:5], 1):
        text = match.get("text", "")
        similarity = match.get("similarity_score", 0)
        phrase_id = match.get("phrase_id", "unknown")
        timestamp = match.get("timestamp", "unknown")
        
        # Truncate for readability
        text_preview = text[:100] + "..." if len(text) > 100 else text
        
        # Visualization bar
        similarity_bar = "█" * int(similarity * 10) + "░" * (10 - int(similarity * 10))
        
        narrative_parts.append(
            f"{i}. **Match #{phrase_id}** (similarity: {similarity:.3f})\n"
            f"   {similarity_bar}\n"
            f"   {text_preview}\n"
            f"   _Timestamp: {timestamp}_\n"
        )
    
    if match_count > 5:
        narrative_parts.append(f"\n_(+{match_count - 5} additional matches omitted for brevity)_")
    
    # Add contextual interpretation (using pre-calculated avg_similarity)
    if avg_similarity > 0.8:
        narrative_parts.append("\n💡 **High semantic relevance** - strong contextual matches found")
    elif avg_similarity > 0.6:
        narrative_parts.append("\n💡 **Moderate semantic relevance** - related concepts identified")
    elif avg_similarity > 0.4:
        narrative_parts.append("\n💡 **Weak semantic relevance** - some thematic overlap detected")
    else:
        narrative_parts.append("\n💡 **Low semantic relevance** - consider refining query")
    
    return "\n".join(narrative_parts)


def _update_graph_trace(
    trace_log: List[str],
    node_name: str,
    status: str,
    metrics: Dict[str, Any]
) -> List[str]:
    """Update graph trace log with node execution details"""
    trace_entry = f"[{node_name}] status={status}, metrics={json.dumps(metrics, default=str)}"
    
    updated_trace = trace_log.copy() if trace_log else []
    updated_trace.append(trace_entry)
    
    return updated_trace


# Async wrapper for compatibility
async def mnemosyne_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """Async wrapper for mnemosyne_node (for async graph execution)"""
    return mnemosyne_node(state)


# Coherence validator
def validate_dual_memory_coherence(
    archivarium_result: Dict[str, Any],
    mnemosyne_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate coherence between Archivarium (PostgreSQL) and Mnemosyne (Qdrant)
    
    Ensures:
    - phrase_id consistency
    - Text content matches
    - Timestamp alignment
    """
    logger.info("🔍 Validating dual-memory coherence...")
    
    coherence_report = {
        "status": "unknown",
        "phrase_id_matches": 0,
        "text_mismatches": 0,
        "timestamp_drifts": 0,
        "errors": []
    }
    
    try:
        archivarium_memories = archivarium_result.get("payload", {}).get("memories", [])
        mnemosyne_matches = mnemosyne_result.get("payload", {}).get("matches", [])
        
        archivarium_map = {m.get("phrase_id"): m for m in archivarium_memories}
        mnemosyne_map = {m.get("phrase_id"): m for m in mnemosyne_matches}
        
        # Check consistency
        for phrase_id in archivarium_map.keys():
            if phrase_id in mnemosyne_map:
                coherence_report["phrase_id_matches"] += 1
                
                arch_text = archivarium_map[phrase_id].get("text", "")
                mnem_text = mnemosyne_map[phrase_id].get("text", "")
                
                if arch_text != mnem_text:
                    coherence_report["text_mismatches"] += 1
                    coherence_report["errors"].append(
                        f"Text mismatch for phrase_id {phrase_id}"
                    )
        
        # Determine status
        if coherence_report["text_mismatches"] == 0:
            coherence_report["status"] = "coherent"
        else:
            coherence_report["status"] = "incoherent"
        
        logger.info(f"✅ Coherence validation: {coherence_report['status']} "
                   f"({coherence_report['phrase_id_matches']} matches, "
                   f"{coherence_report['text_mismatches']} mismatches)")
    
    except Exception as e:
        logger.error(f"❌ Coherence validation error: {e}", exc_info=True)
        coherence_report["status"] = "error"
        coherence_report["errors"].append(str(e))
    
    return coherence_report
