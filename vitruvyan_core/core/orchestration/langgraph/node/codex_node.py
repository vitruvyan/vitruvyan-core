#!/usr/bin/env python3
"""
Codex Node for LangGraph - PHASE 4.6 Enhanced Integration  
=========================================================

Enhanced node for processing Codex Hunters discovery results and generating 
narrative responses. This version includes Orthodoxy bridge integration,
telemetry metrics, and graph state logging for PHASE 4.6.

Key Features (PHASE 4.6):
- Event-driven processing with automatic Orthodoxy validation bridge
- Performance telemetry (latency, duration, source counts)
- Graph state trace logging integration
- Enhanced Redis event publishing with structured metrics
- Self-reflective expedition logging

Usage in graph_flow.py:
from core.orchestration.langgraph.node.codex_node import codex_node
g.add_node("codex", codex_node)

Author: Vitruvyan Development Team  
Created: 2025-10-19 - PHASE 4.5 Implementation
Updated: 2025-10-20 - PHASE 4.6 Refinement
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from core.synaptic_conclave.redis_client import get_redis_bus, publish_codex_event
from core.synaptic_conclave.event_schema import (
    create_codex_discovery_event, 
    CodexIntent, 
    EventSchemaValidator
)

logger = logging.getLogger(__name__)


def codex_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    PHASE 4.6 Codex Node - Enhanced Event-Driven Processing
    
    Expected state inputs:
    - conclave_event: Dict[str, Any] - Event from Synaptic Conclave
    - codex_discovery_results: Dict[str, Any] - Results from Codex Hunters
    - correlation_id: str - For event tracking
    - trace_log: List[str] - Graph execution trace (optional)
    
    State outputs:
    - response: str - Narrative summary of Codex expedition
    - codex_status: str - "success", "failed", "partial"
    - sources_discovered: List[str] - Sources found during expedition
    - route: str - Next graph routing destination
    - trace_log: List[str] - Updated with Codex expedition logs
    - codex_metrics: Dict - Performance telemetry
    """
    
    start_time = time.time()
    
    try:
        logger.info("🗺️ [CODEX] Processing Codex discovery results...")
        
        # Extract event data
        conclave_event = state.get("conclave_event", {})
        discovery_results = state.get("codex_discovery_results", {})
        correlation_id = state.get("correlation_id", f"codex_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        trace_log = state.get("trace_log", [])
        
        # Initialize response structure
        response_data = {
            "response": "",
            "codex_status": "unknown",
            "sources_discovered": [],
            "route": "compose",
            "codex_expedition_summary": {},
            "codex_metrics": {
                "event_latency_ms": 0,
                "sources_count": 0,
                "expedition_duration_ms": 0,
                "node_start_time": datetime.now().isoformat()
            }
        }
        
        # Process Conclave event if present
        if conclave_event:
            event_type = conclave_event.get("event_type", "")
            payload = conclave_event.get("payload", {})
            
            logger.info(f"🧠 [CODEX] Processing Conclave event: {event_type}")
            
            # Calculate event latency
            event_timestamp = conclave_event.get("timestamp")
            if event_timestamp:
                try:
                    event_time = datetime.fromisoformat(event_timestamp) if isinstance(event_timestamp, str) else event_timestamp
                    latency_ms = (datetime.now() - event_time).total_seconds() * 1000
                    response_data["codex_metrics"]["event_latency_ms"] = round(latency_ms, 2)
                except Exception as e:
                    logger.warning(f"⚠️ [CODEX] Could not calculate event latency: {e}")
            
            # Handle data refresh requests
            if "data.refresh.requested" in event_type:
                response_data.update(_handle_data_refresh_event(payload, correlation_id))
                
            # Handle discovery requests  
            elif "data.discovery.requested" in event_type:
                response_data.update(_handle_discovery_event(payload, correlation_id))
                
            else:
                logger.warning(f"⚠️ [CODEX] Unknown event type: {event_type}")
                response_data["response"] = f"Codex received unknown event: {event_type}"
                response_data["codex_status"] = "unknown_event"
        
        # Process direct discovery results
        elif discovery_results:
            response_data.update(_process_discovery_results(discovery_results, correlation_id))
            
        # No valid input
        else:
            logger.warning("⚠️ [CODEX] No valid input data found")
            response_data["response"] = "🗺️ Codex Hunters awaiting expedition orders..."
            response_data["codex_status"] = "idle"
            response_data["route"] = "compose"
        
        # Calculate expedition duration
        expedition_duration_ms = (time.time() - start_time) * 1000
        response_data["codex_metrics"]["expedition_duration_ms"] = round(expedition_duration_ms, 2)
        response_data["codex_metrics"]["sources_count"] = len(response_data.get("sources_discovered", []))
        
        # Update graph trace log
        trace_log = _update_graph_trace(
            trace_log=trace_log,
            node_name="codex",
            status=response_data["codex_status"],
            summary=response_data.get("codex_expedition_summary", {}),
            metrics=response_data["codex_metrics"]
        )
        
        # Log expedition summary
        _log_expedition_summary(response_data, correlation_id)
        
        # Update state with results
        updated_state = {**state, **response_data, "trace_log": trace_log}
        
        logger.info(f"✅ [CODEX] Node processing complete - Status: {response_data['codex_status']} - Duration: {expedition_duration_ms:.2f}ms")
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ [CODEX] Node processing failed: {e}")
        
        expedition_duration_ms = (time.time() - start_time) * 1000
        
        return {
            **state,
            "response": f"🚨 Codex expedition encountered an error: {str(e)}",
            "codex_status": "error",
            "sources_discovered": [],
            "route": "error_handler",
            "codex_metrics": {
                "expedition_duration_ms": round(expedition_duration_ms, 2),
                "error": str(e)
            }
        }


def _handle_data_refresh_event(payload: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Handle data refresh request events"""
    
    entity_id = payload.get("entity_id", "")
    entity_ids = payload.get("entity_ids", [])
    sources = payload.get("sources", [])
    priority = payload.get("priority", "medium")
    
    # Determine scope
    if entity_id:
        scope = f"entity_id {entity_id}"
        target_list = [entity_id]
    elif entity_ids:
        scope = f"{len(entity_ids)} entity_ids"
        target_list = entity_ids
    else:
        scope = "general market data"
        target_list = []
    
    # Generate narrative response
    priority_desc = {
        "critical": "🚨 URGENT",
        "high": "⚡ HIGH PRIORITY", 
        "medium": "📋 STANDARD",
        "low": "⏳ LOW PRIORITY"
    }.get(priority, "📋 STANDARD")
    
    response = (
        f"🗺️ Codex Hunters expedition launched!\n"
        f"Priority: {priority_desc}\n"
        f"Scope: Data refresh for {scope}\n"
        f"Sources: {', '.join(sources) if sources else 'All available'}\n"
        f"📡 Archaeological survey in progress..."
    )
    
    return {
        "response": response,
        "codex_status": "expedition_launched",
        "sources_discovered": [],
        "codex_expedition_summary": {
            "type": "data_refresh", 
            "scope": scope,
            "targets": target_list,
            "sources": sources,
            "priority": priority
        }
    }


def _handle_discovery_event(payload: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Handle discovery request events"""
    
    discovery_type = payload.get("discovery_type", "general")
    target_collections = payload.get("target_collections", [])
    
    response = (
        f"🔍 Codex Hunters discovery expedition initiated!\n"
        f"Type: {discovery_type.replace('_', ' ').title()}\n"
        f"Collections: {', '.join(target_collections) if target_collections else 'All available'}\n"
        f"⚗️ Archaeological analysis commencing..."
    )
    
    return {
        "response": response,
        "codex_status": "discovery_launched",
        "sources_discovered": [],
        "codex_expedition_summary": {
            "type": "discovery",
            "discovery_type": discovery_type,
            "target_collections": target_collections
        }
    }


def _process_discovery_results(results: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Process completed discovery results and trigger Orthodoxy validation"""
    
    sources_found = results.get("sources_found", [])
    collections_mapped = results.get("collections_mapped", [])
    inconsistencies = results.get("inconsistencies_found", 0)
    expedition_type = results.get("expedition_type", "unknown")
    
    # Generate success/failure narrative
    if sources_found and len(sources_found) > 0:
        if sources_found:
            sources_desc = f"📚 {len(sources_found)} new sources discovered"
        else:
            sources_desc = f"📊 {len(collections_mapped)} collections analyzed"
            
        status_desc = "🎯 SUCCESS" if inconsistencies == 0 else f"⚠️ PARTIAL ({inconsistencies} issues found)"
        
        response = (
            f"✅ Codex expedition completed!\n"
            f"Status: {status_desc}\n"
            f"Results: {sources_desc}\n"
            f"Type: {expedition_type.replace('_', ' ').title()}\n"
            f"🏛️ Archives updated with new discoveries."
        )
        
        codex_status = "success" if inconsistencies == 0 else "partial_success"
        
        # Publish success event to Conclave
        try:
            publish_codex_event(
                domain="codex",
                intent="discovery.mapped",
                emitter="codex_node",
                target="langgraph",
                payload={
                    "discovery_results": results,
                    "sources_found": sources_found,
                    "expedition_type": expedition_type,
                    "metrics": {
                        "sources_count": len(sources_found),
                        "collections_count": len(collections_mapped),
                        "inconsistencies": inconsistencies
                    }
                },
                correlation_id=correlation_id
            )
            logger.info(f"📡 [CODEX] Published discovery.mapped event - {len(sources_found)} sources")
            
            # PHASE 4.6: Auto-trigger Orthodoxy validation bridge
            _trigger_orthodoxy_validation(
                sources_found=sources_found,
                collections_mapped=collections_mapped,
                expedition_type=expedition_type,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            logger.error(f"❌ [CODEX] Failed to publish success event: {e}")
        
    else:
        response = (
            f"❌ Codex expedition failed.\n"
            f"Type: {expedition_type.replace('_', ' ').title()}\n"
            f"Result: No new sources discovered\n"
            f"🏺 Archives remain unchanged."
        )
        
        codex_status = "failed"
        
        # Publish failure event to Conclave
        try:
            publish_codex_event(
                domain="codex",
                intent="discovery.failed",
                emitter="codex_node", 
                target="langgraph",
                payload={
                    "expedition_type": expedition_type,
                    "failure_reason": "No sources discovered",
                    "collections_attempted": collections_mapped,
                    "metrics": {
                        "sources_count": 0,
                        "collections_count": len(collections_mapped)
                    }
                },
                correlation_id=correlation_id
            )
            logger.info(f"📡 [CODEX] Published discovery.failed event")
        except Exception as e:
            logger.error(f"❌ [CODEX] Failed to publish failure event: {e}")
    
    return {
        "response": response,
        "codex_status": codex_status,
        "sources_discovered": sources_found,
        "codex_expedition_summary": {
            "type": expedition_type,
            "sources_found_count": len(sources_found),
            "collections_mapped": collections_mapped,
            "inconsistencies": inconsistencies
        }
    }


def _log_expedition_summary(response_data: Dict[str, Any], correlation_id: str) -> None:
    """Log expedition summary in Synaptic format"""
    
    status = response_data.get("codex_status", "unknown")
    summary = response_data.get("codex_expedition_summary", {})
    sources_count = len(response_data.get("sources_discovered", []))
    metrics = response_data.get("codex_metrics", {})
    
    log_message = (
        f"[CODEX][EXPEDITION] Status: {status} | "
        f"Sources: {sources_count} | "
        f"Type: {summary.get('type', 'unknown')} | "
        f"Duration: {metrics.get('expedition_duration_ms', 0):.2f}ms | "
        f"Correlation: {correlation_id}"
    )
    
    if status == "success":
        logger.info(f"✅ {log_message}")
    elif status == "partial_success":
        logger.warning(f"⚠️ {log_message}")
    elif status == "failed":
        logger.error(f"❌ {log_message}")
    else:
        logger.info(f"📋 {log_message}")


def _update_graph_trace(
    trace_log: List[str],
    node_name: str,
    status: str,
    summary: Dict[str, Any],
    metrics: Dict[str, Any]
) -> List[str]:
    """
    PHASE 4.6: Update graph trace log with Codex expedition details
    
    Appends structured trace entry to GraphState['trace_log'] for observability
    """
    
    timestamp = datetime.now().isoformat()
    
    trace_entry = (
        f"[{timestamp}] NODE={node_name} | "
        f"STATUS={status} | "
        f"SOURCES={metrics.get('sources_count', 0)} | "
        f"DURATION={metrics.get('expedition_duration_ms', 0):.2f}ms | "
        f"TYPE={summary.get('type', 'unknown')}"
    )
    
    # Add latency if available
    if metrics.get('event_latency_ms', 0) > 0:
        trace_entry += f" | LATENCY={metrics['event_latency_ms']:.2f}ms"
    
    trace_log.append(trace_entry)
    
    logger.debug(f"📝 [CODEX][TRACE] {trace_entry}")
    
    return trace_log


def _trigger_orthodoxy_validation(
    sources_found: List[str],
    collections_mapped: List[str],
    expedition_type: str,
    correlation_id: str
) -> None:
    """
    PHASE 4.6: Orthodoxy Bridge - Auto-trigger epistemic validation
    
    After successful Codex discovery, immediately request Orthodoxy Wardens
    to validate the newly discovered sources for epistemic integrity.
    """
    
    if not sources_found:
        logger.debug("[CODEX][ORTHODOXY] No sources to validate - skipping bridge")
        return
    
    try:
        # Prepare validation request payload
        validation_payload = {
            "validation_target": "codex_discovery",
            "sources_to_validate": sources_found,
            "collections_context": collections_mapped,
            "discovery_type": expedition_type,
            "priority": "high" if len(sources_found) > 10 else "medium",
            "triggered_by": "codex_node",
            "auto_bridge": True
        }
        
        # Publish validation request to Orthodoxy domain
        publish_codex_event(
            domain="orthodoxy",
            intent="validation.requested",
            emitter="codex_node",
            target="orthodoxy_wardens",
            payload=validation_payload,
            correlation_id=correlation_id
        )
        
        logger.info(
            f"🔗 [CODEX][ORTHODOXY] Bridge activated - "
            f"Validation requested for {len(sources_found)} sources "
            f"(correlation: {correlation_id})"
        )
        
    except Exception as e:
        logger.error(f"❌ [CODEX][ORTHODOXY] Failed to trigger validation bridge: {e}")


# Alternative factory function for complex scenarios
def create_codex_node_with_config(config: Dict[str, Any]) -> callable:
    """
    Factory function to create a configured Codex node
    
    Args:
        config: Configuration dictionary with node settings
        
    Returns:
        Configured codex_node function
    """
    
    def configured_codex_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # Merge config into state
        enhanced_state = {**state, "codex_config": config}
        return codex_node(enhanced_state)
    
    return configured_codex_node


if __name__ == "__main__":
    # Test the simplified Codex node
    print("🧪 Testing PHASE 4.5 Codex Node...")
    
    # Test data refresh event
    test_state_refresh = {
        "conclave_event": {
            "event_type": "codex.data.refresh.requested",
            "payload": {
                "entity_id": "EXAMPLE_ENTITY_1",
                "sources": ["yfinance", "reddit"],
                "priority": "high"
            }
        },
        "correlation_id": "test_refresh_001"
    }
    
    result_refresh = codex_node(test_state_refresh)
    print(f"✅ Data Refresh Test - Status: {result_refresh['codex_status']}")
    print(f"📝 Response: {result_refresh['response'][:100]}...")
    
    # Test discovery results
    test_state_results = {
        "codex_discovery_results": {
            "sources_found": ["yahoo_finance_aapl", "reddit_post_12345"],
            "collections_mapped": ["phrases", "entity_ids"],
            "inconsistencies_found": 0,
            "expedition_type": "data_refresh"
        },
        "correlation_id": "test_results_001"
    }
    
    result_discovery = codex_node(test_state_results)
    print(f"✅ Discovery Results Test - Status: {result_discovery['codex_status']}")
    print(f"📝 Response: {result_discovery['response'][:100]}...")
    
    print("\n🗺️ PHASE 4.5 Codex Node: READY FOR INTEGRATION ✅")