#!/usr/bin/env python3
"""
🏛️ Archivarium Node - PostgreSQL Relational Memory
EPOCH II - PHASE 4.9

LangGraph node for Archivarium (PostgreSQL) memory operations.
Processes memory.read.fulfilled and memory.write.completed events from Redis Cognitive Bus.

Database Strategy:
- Uses EXISTING phrases table (no new tables)
- Uses PostgresAgent methods (no agent modification)
- Logs to existing log_agent table

Telemetry (PHASE 4.6 Pattern):
- event_latency_ms
- db_query_duration_ms  
- memories_retrieved / memories_written
- postgres_connection_time_ms

Author: Vitruvyan Development Team
Created: 2025-10-20 - EPOCH II Integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.foundation.cognitive_bus import get_scribe

logger = logging.getLogger(__name__)


def archivarium_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Archivarium Node - Process PostgreSQL memory events
    
    Handles:
    - memory.read.fulfilled: Format relational memory results for narrative
    - memory.write.completed: Acknowledge successful memory writes
    
    State Input:
    - conclave_event: Event from Redis Cognitive Bus
    - correlation_id: Request correlation ID
    - trace_log: Accumulated trace log (for graph tracing)
    
    State Output:
    - archivarium_narrative: Formatted narrative for compose_node
    - archivarium_status: "success" | "error" | "no_event"
    - archivarium_metrics: Telemetry metrics
    - trace_log: Updated trace log
    - route: Next node ("compose" or "error")
    
    Args:
        state: GraphState dictionary
    
    Returns:
        Dict: Updated state with archivarium outputs
    """
    node_start = datetime.now()
    logger.info("🏛️ Archivarium node activated")
    
    # Extract conclave_event from state
    conclave_event = state.get("conclave_event")
    correlation_id = state.get("correlation_id", "unknown")
    trace_log = state.get("trace_log", [])
    
    if not conclave_event:
        logger.warning("⚠️ No conclave_event in state")
        return {
            "archivarium_narrative": "",
            "archivarium_status": "no_event",
            "archivarium_metrics": {},
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
    if event_type == "memory.read.fulfilled":
        result = _handle_memory_read_fulfilled(conclave_event, correlation_id, node_start, event_latency_ms)
    elif event_type == "memory.write.completed":
        result = _handle_memory_write_completed(conclave_event, correlation_id, node_start, event_latency_ms)
    else:
        logger.warning(f"⚠️ Unhandled event type: {event_type}")
        result = {
            "archivarium_narrative": "",
            "archivarium_status": "unhandled_event",
            "archivarium_metrics": {
                "event_type": event_type,
                "event_latency_ms": event_latency_ms
            }
        }
    
    # Update graph trace log
    trace_log = _update_graph_trace(
        trace_log=trace_log,
        node_name="archivarium",
        status=result["archivarium_status"],
        metrics=result["archivarium_metrics"]
    )
    
    # Determine routing
    route = "compose" if result["archivarium_status"] == "success" else "error"
    
    return {
        "archivarium_narrative": result.get("archivarium_narrative", ""),
        "archivarium_status": result["archivarium_status"],
        "archivarium_metrics": result["archivarium_metrics"],
        "trace_log": trace_log,
        "route": route,
        "response": result.get("archivarium_narrative", "")  # For compose_node compatibility
    }


def _handle_memory_read_fulfilled(
    event_data: Dict[str, Any],
    correlation_id: str,
    node_start: datetime,
    event_latency_ms: float
) -> Dict[str, Any]:
    """
    Handle memory.read.fulfilled event
    
    Formats retrieved memories from Archivarium (PostgreSQL) into narrative.
    
    Args:
        event_data: Event payload from Redis
        correlation_id: Request correlation ID
        node_start: Node start timestamp
        event_latency_ms: Event latency in milliseconds
    
    Returns:
        Dict: Handler result with narrative, status, metrics
    """
    logger.info("📖 Processing memory.read.fulfilled")
    
    try:
        payload = event_data.get("payload", {})
        memories = payload.get("memories", [])
        query_type = payload.get("query_type", "unknown")
        count = payload.get("count", 0)
        
        logger.info(f"📊 Retrieved {count} memories from Archivarium (query_type: {query_type})")
        
        # Format narrative
        narrative = _format_memory_read_narrative(memories, query_type)
        
        # Calculate metrics
        node_duration_ms = (datetime.now() - node_start).total_seconds() * 1000
        
        metrics = {
            "event_latency_ms": event_latency_ms,
            "node_duration_ms": node_duration_ms,
            "memories_retrieved": count,
            "query_type": query_type,
            "node_start_time": node_start.isoformat()
        }
        
        logger.info(f"✅ Memory read narrative generated ({count} memories, {node_duration_ms:.2f}ms)")
        
        return {
            "archivarium_narrative": narrative,
            "archivarium_status": "success",
            "archivarium_metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"❌ Error handling memory.read.fulfilled: {e}", exc_info=True)
        
        return {
            "archivarium_narrative": f"⚠️ Archivarium read error: {str(e)}",
            "archivarium_status": "error",
            "archivarium_metrics": {
                "event_latency_ms": event_latency_ms,
                "error": str(e)
            }
        }


def _handle_memory_write_completed(
    event_data: Dict[str, Any],
    correlation_id: str,
    node_start: datetime,
    event_latency_ms: float
) -> Dict[str, Any]:
    """
    Handle memory.write.completed event
    
    Acknowledges successful memory write to Archivarium (PostgreSQL).
    
    Args:
        event_data: Event payload from Redis
        correlation_id: Request correlation ID
        node_start: Node start timestamp
        event_latency_ms: Event latency in milliseconds
    
    Returns:
        Dict: Handler result with narrative, status, metrics
    """
    logger.info("🖊️ Processing memory.write.completed")
    
    try:
        payload = event_data.get("payload", {})
        phrase_id = payload.get("phrase_id", "unknown")
        text_preview = payload.get("text_preview", "")
        archivarium_status = payload.get("archivarium_status", "unknown")
        mnemosyne_status = payload.get("mnemosyne_status", "unknown")
        write_duration_ms = payload.get("duration_ms", 0)
        
        logger.info(f"✅ Memory write acknowledged: phrase_id={phrase_id}")
        
        # Format narrative
        narrative = _format_memory_write_narrative(
            phrase_id=phrase_id,
            text_preview=text_preview,
            archivarium_status=archivarium_status,
            mnemosyne_status=mnemosyne_status,
            write_duration_ms=write_duration_ms
        )
        
        # Calculate metrics
        node_duration_ms = (datetime.now() - node_start).total_seconds() * 1000
        
        metrics = {
            "event_latency_ms": event_latency_ms,
            "node_duration_ms": node_duration_ms,
            "memories_written": 1,
            "phrase_id": phrase_id,
            "write_duration_ms": write_duration_ms,
            "archivarium_status": archivarium_status,
            "mnemosyne_status": mnemosyne_status,
            "node_start_time": node_start.isoformat()
        }
        
        logger.info(f"✅ Memory write narrative generated (phrase_id={phrase_id}, {node_duration_ms:.2f}ms)")
        
        return {
            "archivarium_narrative": narrative,
            "archivarium_status": "success",
            "archivarium_metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"❌ Error handling memory.write.completed: {e}", exc_info=True)
        
        return {
            "archivarium_narrative": f"⚠️ Archivarium write acknowledgment error: {str(e)}",
            "archivarium_status": "error",
            "archivarium_metrics": {
                "event_latency_ms": event_latency_ms,
                "error": str(e)
            }
        }


def _format_memory_read_narrative(memories: List[Dict[str, Any]], query_type: str) -> str:
    """
    Format memory read results into narrative for compose_node
    
    Args:
        memories: List of memory dicts from Archivarium
        query_type: Type of query executed
    
    Returns:
        str: Formatted narrative
    """
    if not memories:
        return "📖 Archivarium: No memories found matching query criteria."
    
    count = len(memories)
    
    narrative_parts = [
        f"📖 **Archivarium Memory Retrieval** ({query_type} query)",
        f"Retrieved {count} memory record{'s' if count > 1 else ''} from relational storage:\n"
    ]
    
    for i, memory in enumerate(memories[:5], 1):  # Limit to first 5 for narrative
        text = memory.get("text", "")
        timestamp = memory.get("timestamp", "unknown")
        phrase_id = memory.get("phrase_id", "unknown")
        
        # Truncate text for readability
        text_preview = text[:100] + "..." if len(text) > 100 else text
        
        narrative_parts.append(
            f"{i}. **Memory #{phrase_id}** ({timestamp}):\n"
            f"   {text_preview}\n"
        )
    
    if count > 5:
        narrative_parts.append(f"\n_(+{count - 5} additional memories omitted for brevity)_")
    
    return "\n".join(narrative_parts)


def _format_memory_write_narrative(
    phrase_id: Any,
    text_preview: str,
    archivarium_status: str,
    mnemosyne_status: str,
    write_duration_ms: float
) -> str:
    """
    Format memory write acknowledgment into narrative
    
    Args:
        phrase_id: PostgreSQL phrase ID
        text_preview: Preview of written text
        archivarium_status: Archivarium write status
        mnemosyne_status: Mnemosyne write status
        write_duration_ms: Write operation duration
    
    Returns:
        str: Formatted narrative
    """
    status_emoji = "✅" if archivarium_status == "success" and mnemosyne_status == "success" else "⚠️"
    
    narrative = [
        f"{status_emoji} **Memory Write Completed**",
        f"**Phrase ID:** {phrase_id}",
        f"**Text:** {text_preview}",
        f"**Archivarium (PostgreSQL):** {archivarium_status}",
        f"**Mnemosyne (Qdrant):** {mnemosyne_status}",
        f"**Duration:** {write_duration_ms:.2f}ms"
    ]
    
    return "\n".join(narrative)


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
async def archivarium_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for archivarium_node (for async graph execution)
    """
    return archivarium_node(state)
