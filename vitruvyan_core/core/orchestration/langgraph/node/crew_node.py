#!/usr/bin/env python3
"""
🧠 CREW NODE - LANGGRAPH INTEGRATION
====================================
CrewAI Strategic Order Node for LangGraph Cognitive Flow
Phase 4.6 - Strategic Analysis Cognitive Integration

"From Signals to Strategies, Through the Conclave's Wisdom"

Author: Vitruvian Development Team
Created: 2025-10-19 - CrewAI Synaptic Conclave Integration
Updated: 2025-10-20 - PHASE 4.6 Enhancement (Telemetry, Trace Logging, Response Listener)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import uuid
import json
import time

from core.foundation.cognitive_bus.event_schema import (
    EventDomain,
    CrewIntent
)
from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent
from core.foundation.persistence.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


def crew_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🧠 CrewAI Strategic Order Node - Cognitive Strategy Generation (PHASE 4.6)
    
    Processes strategic analysis requests and publishes events to the
    Synaptic Conclave for CrewAI Strategic Order execution.
    
    PHASE 4.6 Enhancements:
    - Performance telemetry (request_duration_ms, event_latency_ms)
    - Graph state trace logging integration
    - Structured metrics in response payload
    
    Event Types Published:
    - crew.strategy.analysis.requested: Comprehensive strategy analysis
    - crew.trend.analysis.requested: Trend-specific analysis
    - crew.momentum.analysis.requested: Momentum analysis
    - crew.risk.analysis.requested: Risk assessment
    
    Routing Logic:
    - Publishes request event to Redis Cognitive Bus
    - Returns immediate acknowledgment
    - Actual strategy generation happens asynchronously via CognitiveCrew
    - Result will be received via crew.strategy.generated event
    
    Args:
        state: LangGraph state dict containing:
            - ticker: Stock ticker to analyze
            - intent: Analysis intent (strategy, trend, momentum, risk)
            - horizon: Time horizon (short, medium, long)
            - capital: Available capital
            - user_id: User identifier
            - trace_log: List[str] - Graph execution trace (optional)
            
    Returns:
        Updated state with:
            - response: User-facing acknowledgment message
            - route: Next node in graph (typically "compose")
            - crew_correlation_id: For tracking async response
            - crew_metrics: Performance telemetry dict
            - trace_log: Updated with Crew request logs
    """
    
    start_time = time.time()
    
    logger.info("🧠 Crew Node activated - Processing strategic analysis request")
    
    start_time = time.time()
    
    logger.info("🧠 Crew Node activated - Processing strategic analysis request")
    
    # Extract parameters from state
    ticker = state.get("ticker")
    intent = state.get("intent", "strategy")
    horizon = state.get("horizon", "medium")
    capital = state.get("capital", 10000.0)
    user_id = state.get("user_id", "langgraph_user")
    user_query = state.get("user_query", "")
    trace_log = state.get("trace_log", [])
    
    # Initialize metrics
    crew_metrics = {
        "request_duration_ms": 0,
        "event_latency_ms": 0,
        "node_start_time": datetime.now().isoformat(),
        "analysis_type": ""
    }
    
    # Validate ticker
    if not ticker:
        logger.warning("⚠️ No ticker provided to Crew Node")
        
        request_duration_ms = (time.time() - start_time) * 1000
        crew_metrics["request_duration_ms"] = round(request_duration_ms, 2)
        
        # Update trace log
        trace_log = _update_graph_trace(
            trace_log=trace_log,
            node_name="crew",
            status="validation_failed",
            correlation_id="",
            metrics=crew_metrics
        )
        
        return {
            **state,
            "response": "⚠️ Cannot generate strategy without a stock ticker. Please specify a ticker (e.g., AAPL, TSLA).",
            "route": "compose",
            "crew_metrics": crew_metrics,
            "trace_log": trace_log
        }
    
    # Generate correlation ID for async tracking
    correlation_id = str(uuid.uuid4())
    
    # Initialize Redis and PostgreSQL
    redis_bus = get_redis_bus()
    postgres_agent = PostgresAgent()
    
    # Log request using EXISTING log_agent table structure
    # Schema: (agent TEXT NOT NULL, ticker TEXT NULL, payload_json JSONB NULL, created_at TIMESTAMP)
    try:
        with postgres_agent.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO log_agent (agent, ticker, payload_json)
                VALUES (%s, %s, %s::jsonb)
            """, (
                "LangGraph-CrewNode",
                ticker,
                json.dumps({
                    "action": "strategy_request_initiated",
                    "intent": intent,
                    "horizon": horizon,
                    "correlation_id": correlation_id,
                    "user_id": user_id
                })
            ))
        postgres_agent.connection.commit()
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL logging failed: {e}")

    
    # Determine analysis type based on intent
    analysis_type = _map_intent_to_analysis_type(intent)
    crew_metrics["analysis_type"] = analysis_type
    
    # Build event payload
    event_payload = {
        "ticker": ticker,
        "analysis_type": analysis_type,
        "horizon": horizon,
        "capital": capital,
        "user_id": user_id,
        "user_query": user_query,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Determine event channel based on analysis type
    if analysis_type == "trend":
        event_channel = "crew.trend.analysis.requested"
        event_intent = CrewIntent.TREND_ANALYSIS_REQUESTED
    elif analysis_type == "momentum":
        event_channel = "crew.momentum.analysis.requested"
        event_intent = CrewIntent.MOMENTUM_ANALYSIS_REQUESTED
    elif analysis_type == "risk":
        event_channel = "crew.risk.analysis.requested"
        event_intent = CrewIntent.RISK_ANALYSIS_REQUESTED
    else:
        # Default: comprehensive strategy
        event_channel = "crew.strategy.analysis.requested"
        event_intent = CrewIntent.STRATEGY_ANALYSIS_REQUESTED
    
    # Create event data
    event_data = {
        "event_type": f"{EventDomain.CREW.value}.{event_intent.value}",
        "emitter": "langgraph",
        "target": "crewai_strategic_order",
        "payload": event_payload,
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Publish to Redis Cognitive Bus
    try:
        logger.info(f"📡 Publishing {analysis_type} request for {ticker} to Conclave...")
        
        if not redis_bus.is_connected():
            redis_bus.connect()
        
        # Create CognitiveEvent (using proper dataclass constructor)
        event = CognitiveEvent(
            event_type=f"{EventDomain.CREW.value}.{event_intent.value}",
            emitter="langgraph",
            target="crewai_strategic_order",
            payload=event_payload,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id
        )
        
        success = redis_bus.publish_event(event)
        
        if success:
            logger.info(f"✅ Strategy request published successfully (correlation: {correlation_id})")
            
            # Calculate request duration
            request_duration_ms = (time.time() - start_time) * 1000
            crew_metrics["request_duration_ms"] = round(request_duration_ms, 2)
            
            # Log success using EXISTING log_agent table
            try:
                with postgres_agent.connection.cursor() as cur:
                    cur.execute("""
                        INSERT INTO log_agent (agent, ticker, payload_json)
                        VALUES (%s, %s, %s::jsonb)
                    """, (
                        "LangGraph-CrewNode",
                        ticker,
                        json.dumps({
                            "action": "strategy_request_published",
                            "analysis_type": analysis_type,
                            "correlation_id": correlation_id,
                            "event_channel": event_channel,
                            "metrics": crew_metrics
                        })
                    ))
                postgres_agent.connection.commit()
            except Exception as log_err:
                logger.warning(f"⚠️ Success log failed: {log_err}")
            
            # Update trace log
            trace_log = _update_graph_trace(
                trace_log=trace_log,
                node_name="crew",
                status="request_published",
                correlation_id=correlation_id,
                metrics=crew_metrics
            )
            
            # Build user response
            response = _build_acknowledgment_response(
                ticker=ticker,
                analysis_type=analysis_type,
                correlation_id=correlation_id
            )
            
            route = "compose"  # Continue to composition
            
        else:
            logger.error("❌ Failed to publish strategy request to Redis")
            
            # Calculate request duration
            request_duration_ms = (time.time() - start_time) * 1000
            crew_metrics["request_duration_ms"] = round(request_duration_ms, 2)
            
            # Calculate request duration
            request_duration_ms = (time.time() - start_time) * 1000
            crew_metrics["request_duration_ms"] = round(request_duration_ms, 2)
            
            # Log failure using EXISTING log_agent table
            try:
                with postgres_agent.connection.cursor() as cur:
                    cur.execute("""
                        INSERT INTO log_agent (agent, ticker, payload_json)
                        VALUES (%s, %s, %s::jsonb)
                    """, (
                        "LangGraph-CrewNode",
                        ticker,
                        json.dumps({
                            "action": "strategy_request_failed",
                            "error": "Redis publish failed",
                            "correlation_id": correlation_id,
                            "metrics": crew_metrics
                        })
                    ))
                postgres_agent.connection.commit()
            except Exception as log_err:
                logger.warning(f"⚠️ Failure log failed: {log_err}")
            
            # Update trace log
            trace_log = _update_graph_trace(
                trace_log=trace_log,
                node_name="crew",
                status="publish_failed",
                correlation_id=correlation_id,
                metrics=crew_metrics
            )
            
            response = (
                f"⚠️ Strategy request could not be processed at this time. "
                f"Please try again later."
            )
            route = "compose"
        
    except Exception as e:
        logger.error(f"❌ Error in Crew Node: {e}")
        
        # Calculate request duration
        request_duration_ms = (time.time() - start_time) * 1000
        crew_metrics["request_duration_ms"] = round(request_duration_ms, 2)
        crew_metrics["error"] = str(e)
        
        # Log error using EXISTING log_agent table
        try:
            with postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO log_agent (agent, ticker, payload_json)
                    VALUES (%s, %s, %s::jsonb)
                """, (
                    "LangGraph-CrewNode",
                    ticker,
                    json.dumps({
                        "action": "strategy_request_error",
                        "error": str(e),
                        "correlation_id": correlation_id,
                        "metrics": crew_metrics
                    })
                ))
            postgres_agent.connection.commit()
        except Exception as log_err:
            logger.warning(f"⚠️ Error log failed: {log_err}")
        
        # Update trace log
        trace_log = _update_graph_trace(
            trace_log=trace_log,
            node_name="crew",
            status="error",
            correlation_id=correlation_id,
            metrics=crew_metrics
        )
        
        response = (
            f"⚠️ An error occurred while processing your strategy request: {str(e)}"
        )
        route = "compose"
    
    # Update state
    updated_state = {
        **state,
        "response": response,
        "route": route,
        "crew_correlation_id": correlation_id,
        "crew_analysis_type": analysis_type,
        "crew_status": "requested",
        "crew_metrics": crew_metrics,
        "trace_log": trace_log
    }
    
    logger.info(
        f"🧠 [CREW] Node completed - Status: requested | "
        f"Ticker: {ticker} | "
        f"Type: {analysis_type} | "
        f"Duration: {crew_metrics['request_duration_ms']:.2f}ms | "
        f"Correlation: {correlation_id[:8]}..."
    )
    
    return updated_state


def _update_graph_trace(
    trace_log: List[str],
    node_name: str,
    status: str,
    correlation_id: str,
    metrics: Dict[str, Any]
) -> List[str]:
    """
    PHASE 4.6: Update graph trace log with Crew request details
    
    Appends structured trace entry to GraphState['trace_log'] for observability
    """
    
    timestamp = datetime.now().isoformat()
    
    trace_entry = (
        f"[{timestamp}] NODE={node_name} | "
        f"STATUS={status} | "
        f"CORRELATION={correlation_id[:8] if correlation_id else 'N/A'} | "
        f"DURATION={metrics.get('request_duration_ms', 0):.2f}ms | "
        f"TYPE={metrics.get('analysis_type', 'unknown')}"
    )
    
    trace_log.append(trace_entry)
    
    logger.debug(f"📝 [CREW][TRACE] {trace_entry}")
    
    return trace_log


def _map_intent_to_analysis_type(intent: str) -> str:
    """
    Map LangGraph intent to CrewAI analysis type.
    
    Args:
        intent: LangGraph intent (trend, momentum, risk, etc.)
        
    Returns:
        CrewAI analysis type string
    """
    intent_mapping = {
        "trend": "trend",
        "momentum": "momentum",
        "volatility": "volatility",
        "risk": "risk",
        "backtest": "backtest",
        "portfolio": "portfolio",
        "allocate": "comprehensive",
        "sentiment": "comprehensive"
    }
    
    return intent_mapping.get(intent.lower(), "comprehensive")


def _build_acknowledgment_response(
    ticker: str,
    analysis_type: str,
    correlation_id: str
) -> str:
    """
    Build user-facing acknowledgment message.
    
    Args:
        ticker: Stock ticker
        analysis_type: Type of analysis
        correlation_id: Correlation ID for tracking
        
    Returns:
        Human-readable acknowledgment message
    """
    
    analysis_descriptions = {
        "comprehensive": "comprehensive strategic analysis",
        "trend": "trend analysis",
        "momentum": "momentum analysis",
        "volatility": "volatility analysis",
        "risk": "risk assessment",
        "backtest": "backtest simulation",
        "portfolio": "portfolio analysis"
    }
    
    description = analysis_descriptions.get(analysis_type, "strategic analysis")
    
    return (
        f"🧠 Strategic Order activated for {ticker}\n\n"
        f"📊 Initiating {description} with 7 specialized agents:\n"
        f"- Trend Analyst (SMA patterns)\n"
        f"- Momentum Analyst (RSI, MACD)\n"
        f"- Volatility Analyst (ATR, StdDev)\n"
        f"- Risk Manager (Position sizing, SL/TP)\n"
        f"- Backtest Engineer (Historical validation)\n"
        f"- Portfolio Advisor (Allocation strategy)\n"
        f"- Explainability Agent (Human-readable insights)\n\n"
        f"⏳ Analysis in progress... Results will be delivered shortly.\n"
        f"🔗 Tracking ID: {correlation_id[:8]}..."
    )


# Optional: Response listener for crew.strategy.generated events
def crew_response_listener_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    PHASE 4.6: Enhanced response listener for crew.strategy.generated events.
    
    This node subscribes to Redis and waits for async CrewAI responses.
    Includes timeout handling and correlation ID matching.
    
    Args:
        state: LangGraph state with crew_correlation_id
        
    Returns:
        Updated state with crew_strategy_result or timeout status
    """
    
    start_time = time.time()
    
    logger.info("👂 Crew Response Listener activated")
    
    correlation_id = state.get("crew_correlation_id")
    trace_log = state.get("trace_log", [])
    timeout = state.get("crew_timeout", 30)  # Default 30 seconds
    
    # Initialize metrics
    listener_metrics = {
        "listen_duration_ms": 0,
        "response_received": False,
        "timeout": timeout,
        "node_start_time": datetime.now().isoformat()
    }
    
    if not correlation_id:
        logger.warning("⚠️ No correlation ID found for response listening")
        
        listen_duration_ms = (time.time() - start_time) * 1000
        listener_metrics["listen_duration_ms"] = round(listen_duration_ms, 2)
        
        trace_log = _update_graph_trace(
            trace_log=trace_log,
            node_name="crew_listener",
            status="no_correlation_id",
            correlation_id="",
            metrics=listener_metrics
        )
        
        return {
            **state,
            "crew_listener_metrics": listener_metrics,
            "trace_log": trace_log
        }
    
    # Subscribe to crew.strategy.generated channel
    try:
        redis_bus = get_redis_bus()
        
        if not redis_bus.is_connected():
            redis_bus.connect()
        
        pubsub = redis_bus.client.pubsub()
        pubsub.subscribe("crew.strategy.generated")
        
        logger.info(f"📡 Listening for crew.strategy.generated (correlation: {correlation_id[:8]}..., timeout: {timeout}s)")
        
        response_data = None
        listen_start = time.time()
        
        while (time.time() - listen_start) < timeout:
            message = pubsub.get_message(timeout=1.0)
            
            if message and message['type'] == 'message':
                try:
                    event_data = json.loads(message['data'])
                    
                    # Check correlation ID match
                    if event_data.get('correlation_id') == correlation_id:
                        logger.info(f"✅ Received matching response for {correlation_id[:8]}...")
                        response_data = event_data
                        listener_metrics["response_received"] = True
                        break
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to decode message: {e}")
        
        pubsub.unsubscribe("crew.strategy.generated")
        pubsub.close()
        
        listen_duration_ms = (time.time() - start_time) * 1000
        listener_metrics["listen_duration_ms"] = round(listen_duration_ms, 2)
        
        if response_data:
            # Update trace log - success
            trace_log = _update_graph_trace(
                trace_log=trace_log,
                node_name="crew_listener",
                status="response_received",
                correlation_id=correlation_id,
                metrics=listener_metrics
            )
            
            return {
                **state,
                "crew_strategy_result": response_data.get('payload', {}),
                "crew_status": "completed",
                "crew_listener_metrics": listener_metrics,
                "trace_log": trace_log,
                "route": "compose"
            }
        else:
            # Timeout
            logger.warning(f"⏱️ Timeout waiting for response (correlation: {correlation_id[:8]}...)")
            
            trace_log = _update_graph_trace(
                trace_log=trace_log,
                node_name="crew_listener",
                status="timeout",
                correlation_id=correlation_id,
                metrics=listener_metrics
            )
            
            return {
                **state,
                "crew_status": "timeout",
                "crew_listener_metrics": listener_metrics,
                "trace_log": trace_log,
                "route": "compose"
            }
            
    except Exception as e:
        logger.error(f"❌ Error in Crew Response Listener: {e}")
        
        listen_duration_ms = (time.time() - start_time) * 1000
        listener_metrics["listen_duration_ms"] = round(listen_duration_ms, 2)
        listener_metrics["error"] = str(e)
        
        trace_log = _update_graph_trace(
            trace_log=trace_log,
            node_name="crew_listener",
            status="error",
            correlation_id=correlation_id or "",
            metrics=listener_metrics
        )
        
        return {
            **state,
            "crew_status": "error",
            "crew_listener_metrics": listener_metrics,
            "trace_log": trace_log,
            "route": "compose"
        }


# Legacy response listener (kept for backwards compatibility)
def crew_response_listener_node_legacy(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy: Optional node to listen for crew.strategy.generated responses.
    
    This can be used in workflows where you want to wait for the
    async CrewAI response before continuing.
    
    Note: Currently not used in main flow (responses handled separately)
    Use crew_response_listener_node() for PHASE 4.6 enhanced version.
    """
    
    logger.info("👂 Crew Response Listener activated")
    
    correlation_id = state.get("crew_correlation_id")
    
    if not correlation_id:
        logger.warning("⚠️ No correlation ID found for response listening (legacy mode)")
        return state
    
    # TODO: Implement Redis subscription for specific correlation_id
    # This would wait for crew.strategy.generated event matching correlation_id
    
    return {
        **state,
        "response": "Awaiting CrewAI strategic analysis... (legacy listener)",
        "route": "compose"
    }


if __name__ == "__main__":
    """Test Crew Node"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 Testing Crew Node...")
    
    # Test state
    test_state = {
        "ticker": "AAPL",
        "intent": "strategy",
        "horizon": "medium",
        "capital": 10000.0,
        "user_id": "test_user",
        "user_query": "Analizza AAPL con strategia completa"
    }
    
    # Note: This will attempt to publish to Redis
    # Make sure Redis is running for full test
    
    print(f"Input state: {test_state}")
    
    result = crew_node(test_state)
    
    print(f"\n✅ Result state:")
    print(f"  - Response: {result.get('response')[:100]}...")
    print(f"  - Route: {result.get('route')}")
    print(f"  - Correlation ID: {result.get('crew_correlation_id')}")
    
    print("\n🗺️ PHASE 4.6 Crew Node: READY ✅")
