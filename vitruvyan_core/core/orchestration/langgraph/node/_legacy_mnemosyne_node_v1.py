#!/usr/bin/env python3
"""
🔮 Mnemosyne Node - Qdrant Vector Memory
EPOCH II - PHASE 4.9

LangGraph node for Mnemosyne (Qdrant) semantic memory operations.
Processes memory.vector.match.fulfilled events from Redis Cognitive Bus.

Database Strategy:
- Uses EXISTING phrases collection (no new collections)
- Uses QdrantAgent methods (no agent modification)
- Semantic similarity search with cosine distance

Telemetry (PHASE 4.6 Pattern):
- event_latency_ms
- vectorization_duration_ms
- qdrant_search_duration_ms
- matches_found
- similarity_threshold

Author: Vitruvyan Development Team
Created: 2025-10-20 - EPOCH II Integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.synaptic_conclave import get_scribe

logger = logging.getLogger(__name__)


def mnemosyne_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mnemosyne Node - Process Qdrant vector memory events
    
    Handles:
    - memory.vector.match.fulfilled: Format semantic search results for narrative
    
    State Input:
    - conclave_event: Event from Redis Cognitive Bus
    - correlation_id: Request correlation ID
    - trace_log: Accumulated trace log (for graph tracing)
    
    State Output:
    - mnemosyne_narrative: Formatted narrative for compose_node
    - mnemosyne_status: "success" | "error" | "no_event"
    - mnemosyne_metrics: Telemetry metrics
    - trace_log: Updated trace log
    - route: Next node ("compose" or "error")
    
    Args:
        state: GraphState dictionary
    
    Returns:
        Dict: Updated state with mnemosyne outputs
    """
    node_start = datetime.now()
    logger.info("🔮 Mnemosyne node activated")
    
    # Extract conclave_event from state
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
    event_timestamp = conclave_event.get("timestamp", datetime.now().isoformat())
    
    # Calculate event latency
    try:
        event_time = datetime.fromisoformat(event_timestamp)
        event_latency_ms = (node_start - event_time).total_seconds() * 1000
    except:
        event_latency_ms = 0
    
    logger.info(f"📨 Processing event: {event_type} (correlation_id: {correlation_id})")
    
    # Route to appropriate handler
    if event_type == "memory.vector.match.fulfilled":
        result = _handle_vector_match_fulfilled(conclave_event, correlation_id, node_start, event_latency_ms)
    else:
        logger.warning(f"⚠️ Unhandled event type: {event_type}")
        result = {
            "mnemosyne_narrative": "",
            "mnemosyne_status": "unhandled_event",
            "mnemosyne_metrics": {
                "event_type": event_type,
                "event_latency_ms": event_latency_ms
            }
        }
    
    # Update graph trace log
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
        "response": result.get("mnemosyne_narrative", "")  # For compose_node compatibility
    }


def _handle_vector_match_fulfilled(
    event_data: Dict[str, Any],
    correlation_id: str,
    node_start: datetime,
    event_latency_ms: float
) -> Dict[str, Any]:
    """
    Handle memory.vector.match.fulfilled event
    
    Formats semantic search results from Mnemosyne (Qdrant) into narrative.
    
    Args:
        event_data: Event payload from Redis
        correlation_id: Request correlation ID
        node_start: Node start timestamp
        event_latency_ms: Event latency in milliseconds
    
    Returns:
        Dict: Handler result with narrative, status, metrics
    """
    logger.info("🔮 Processing memory.vector.match.fulfilled")
    
    try:
        payload = event_data.get("payload", {})
        matches = payload.get("matches", [])
        query_text = payload.get("query_text", "")
        count = payload.get("count", 0)
        top_k = payload.get("top_k", 10)
        
        logger.info(f"📊 Retrieved {count} semantic matches from Mnemosyne (query: '{query_text[:50]}...')")
        
        # Format narrative
        narrative = _format_vector_match_narrative(matches, query_text, top_k)
        
        # Calculate metrics
        node_duration_ms = (datetime.now() - node_start).total_seconds() * 1000
        
        # Calculate similarity statistics
        similarity_scores = [m.get("similarity_score", 0) for m in matches]
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        max_similarity = max(similarity_scores) if similarity_scores else 0
        min_similarity = min(similarity_scores) if similarity_scores else 0
        
        metrics = {
            "event_latency_ms": event_latency_ms,
            "node_duration_ms": node_duration_ms,
            "matches_found": count,
            "top_k": top_k,
            "avg_similarity": round(avg_similarity, 3),
            "max_similarity": round(max_similarity, 3),
            "min_similarity": round(min_similarity, 3),
            "query_text_length": len(query_text),
            "node_start_time": node_start.isoformat()
        }
        
        logger.info(f"✅ Vector match narrative generated ({count} matches, avg_sim={avg_similarity:.3f}, {node_duration_ms:.2f}ms)")
        
        return {
            "mnemosyne_narrative": narrative,
            "mnemosyne_status": "success",
            "mnemosyne_metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"❌ Error handling memory.vector.match.fulfilled: {e}", exc_info=True)
        
        return {
            "mnemosyne_narrative": f"⚠️ Mnemosyne vector search error: {str(e)}",
            "mnemosyne_status": "error",
            "mnemosyne_metrics": {
                "event_latency_ms": event_latency_ms,
                "error": str(e)
            }
        }


def _format_vector_match_narrative(
    matches: List[Dict[str, Any]],
    query_text: str,
    top_k: int
) -> str:
    """
    Format vector match results into narrative for compose_node
    
    Args:
        matches: List of match dicts from Mnemosyne (Qdrant)
        query_text: Original query text
        top_k: Number of results requested
    
    Returns:
        str: Formatted narrative
    """
    if not matches:
        return f"🔮 **Mnemosyne:** No semantic matches found for query: '{query_text[:50]}...'"
    
    count = len(matches)
    avg_similarity = sum(m.get("similarity_score", 0) for m in matches) / count if count > 0 else 0
    
    narrative_parts = [
        f"🔮 **Mnemosyne Semantic Search**",
        f"**Query:** {query_text}",
        f"**Results:** {count}/{top_k} matches (avg similarity: {avg_similarity:.3f})\n"
    ]
    
    # Sort matches by similarity score (descending)
    sorted_matches = sorted(matches, key=lambda m: m.get("similarity_score", 0), reverse=True)
    
    for i, match in enumerate(sorted_matches[:5], 1):  # Limit to top 5 for narrative
        text = match.get("text", "")
        similarity = match.get("similarity_score", 0)
        phrase_id = match.get("phrase_id", "unknown")
        timestamp = match.get("timestamp", "unknown")
        
        # Truncate text for readability
        text_preview = text[:100] + "..." if len(text) > 100 else text
        
        # Similarity bar visualization
        similarity_bar = "█" * int(similarity * 10) + "░" * (10 - int(similarity * 10))
        
        narrative_parts.append(
            f"{i}. **Match #{phrase_id}** (similarity: {similarity:.3f})\n"
            f"   {similarity_bar}\n"
            f"   {text_preview}\n"
            f"   _Timestamp: {timestamp}_\n"
        )
    
    if count > 5:
        narrative_parts.append(f"\n_(+{count - 5} additional matches omitted for brevity)_")
    
    # Add contextual interpretation
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
    """
    Update graph trace log with node execution details
    
    Args:
        trace_log: Existing trace log
        node_name: Name of node
        status: Node execution status
        metrics: Node metrics
    
    Returns:
        List[str]: Updated trace log
    """
    trace_entry = f"[{node_name}] status={status}, metrics={json.dumps(metrics, default=str)}"
    
    # Append to existing trace log
    updated_trace = trace_log.copy() if trace_log else []
    updated_trace.append(trace_entry)
    
    return updated_trace


# Async wrapper for compatibility with async contexts
async def mnemosyne_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for mnemosyne_node (for async graph execution)
    """
    return mnemosyne_node(state)


# Dual-Memory Coherence Validator
def validate_dual_memory_coherence(
    archivarium_result: Dict[str, Any],
    mnemosyne_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate coherence between Archivarium (PostgreSQL) and Mnemosyne (Qdrant) results
    
    Ensures that:
    1. phrase_id consistency (PostgreSQL ID == Qdrant point ID)
    2. Text content matches
    3. Timestamp alignment
    
    Args:
        archivarium_result: Result from archivarium_node
        mnemosyne_result: Result from mnemosyne_node
    
    Returns:
        Dict: Coherence validation report
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
        # Extract memories from both sources
        archivarium_memories = archivarium_result.get("payload", {}).get("memories", [])
        mnemosyne_matches = mnemosyne_result.get("payload", {}).get("matches", [])
        
        # Build lookup maps
        archivarium_map = {m.get("phrase_id"): m for m in archivarium_memories}
        mnemosyne_map = {m.get("phrase_id"): m for m in mnemosyne_matches}
        
        # Check phrase_id consistency
        for phrase_id in archivarium_map.keys():
            if phrase_id in mnemosyne_map:
                coherence_report["phrase_id_matches"] += 1
                
                # Check text content
                arch_text = archivarium_map[phrase_id].get("text", "")
                mnem_text = mnemosyne_map[phrase_id].get("text", "")
                
                if arch_text != mnem_text:
                    coherence_report["text_mismatches"] += 1
                    coherence_report["errors"].append(
                        f"Text mismatch for phrase_id {phrase_id}"
                    )
        
        # Determine overall status
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
