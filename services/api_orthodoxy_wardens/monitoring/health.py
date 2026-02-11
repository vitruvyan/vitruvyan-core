"""
🏛️ ORTHODOXY WARDENS - Synaptic Conclave Integration & Health Monitoring
Utility functions for Synaptic Conclave listener setup and health checks.

This module contains non-global utility functions that can be reused
without touching main.py global state.
"""

import logging
import os
import asyncio
import threading
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Synaptic Conclave integration
from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_envelope import CognitiveEvent

# Prometheus metrics
from core.governance.orthodoxy_wardens.monitoring.metrics import (
    CONFESSIONS_RECEIVED_TOTAL,
    EXAMINATIONS_TOTAL,
    EXAMINATIONS_DURATION_SECONDS,
    FINDINGS_TOTAL,
    VERDICTS_TOTAL,
    SURVEILLANCE_CYCLES_TOTAL,
)

# Import event handlers
from api_orthodoxy_wardens._legacy.core.event_handlers import (
    handle_audit_request,
    handle_system_events
)

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS COLLECTORS
# =============================================================================

confessions_received_counter = Counter(
    CONFESSIONS_RECEIVED_TOTAL,
    "Total confessions received by Orthodoxy Wardens"
)

examinations_total_counter = Counter(
    EXAMINATIONS_TOTAL,
    "Total examinations conducted"
)

examinations_duration_histogram = Histogram(
    EXAMINATIONS_DURATION_SECONDS,
    "Duration of examinations in seconds"
)

findings_total_counter = Counter(
    FINDINGS_TOTAL,
    "Total findings discovered"
)

verdicts_total_counter = Counter(
    VERDICTS_TOTAL,
    "Total verdicts issued"
)

surveillance_cycles_counter = Counter(
    SURVEILLANCE_CYCLES_TOTAL,
    "Total surveillance cycles executed"
)

# Health status gauge
orthodoxy_health_status = Gauge(
    "orthodoxy_health_status",
    "Overall health status (0=down, 1=degraded, 2=healthy)"
)

# =============================================================================
# SYNAPTIC CONCLAVE LISTENER SETUP
# =============================================================================

async def setup_synaptic_conclave_listeners():
    """🕯️ Setup Redis Streams listeners for Orthodoxy Wardens (Feb 8, 2026 - FASE 1 COMPLETE)"""
    try:
        redis_host = os.getenv('REDIS_HOST', 'omni_redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        bus = StreamBus(host=redis_host, port=redis_port)
        
        # Sacred channels configuration - maps streams to handlers
        sacred_channels = {
            "orthodoxy.audit.requested": handle_audit_request,
            "orthodoxy.validation.requested": handle_audit_request,  # Reuse audit handler
            "neural_engine.screening.completed": handle_system_events,
            "babel.sentiment.completed": handle_system_events,
            "memory.write.completed": handle_system_events,
            "vee.explanation.completed": handle_system_events,
            "langgraph.response.completed": handle_system_events
        }
        
        # Create consumer group for Orthodoxy Wardens
        group_name = "group:orthodoxy_main"
        consumer_id = "orthodoxy_main:worker_1"
        
        # First pass: Create all consumer groups (non-blocking)
        for channel, handler in sacred_channels.items():
            try:
                bus.create_consumer_group(channel, group_name)
                logger.info(f"⚖️ Created consumer group '{group_name}' on {channel}")
            except Exception as e:
                # Consumer group may already exist (idempotent operation)
                logger.debug(f"Consumer group '{group_name}' on {channel}: {e}")
        
        logger.info(f"🕯️ Synaptic Conclave listeners activated for {len(sacred_channels)} sacred channels")
        
        # Second pass: Launch background consumption tasks in separate thread (non-blocking)
        # This ensures the startup event completes immediately
        def start_listeners_thread():
            """Launch all consumption loops in a background thread"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            tasks = []
            for channel, handler in sacred_channels.items():
                task = loop.create_task(_consume_channel(bus, channel, group_name, consumer_id, handler))
                tasks.append(task)
            
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                logger.info("Shutting down Synaptic Conclave listeners")
            finally:
                for task in tasks:
                    task.cancel()
                loop.close()
        
        # Start in daemon thread (won't block shutdown)
        listener_thread = threading.Thread(target=start_listeners_thread, daemon=True, name="OrthodoxyListenerThread")
        listener_thread.start()
        logger.info("🔥 Synaptic Conclave listeners thread started (background processing active)")
        
    except Exception as e:
        logger.error(f"⚖️ Error setting up Synaptic Conclave listeners: {e}")

async def _consume_channel(bus: StreamBus, channel: str, group: str, consumer: str, handler):
    """Background task to consume events from a sacred channel"""
    logger.info(f"👂 Starting consumption: {channel} (group: {group}, consumer: {consumer})")
    
    try:
        for event in bus.consume(channel, group, consumer, block_ms=5000):
            try:
                # Convert TransportEvent to CognitiveEvent for backward compatibility
                cognitive_event = CognitiveEvent(
                    event_id=event.event_id,
                    event_type=event.data.get("event_type", "system.event"),
                    payload=event.data,
                    correlation_id=event.data.get("correlation_id"),
                    timestamp=event.timestamp
                )
                
                # Call handler
                await handler(cognitive_event)
                
                # Acknowledge event
                bus.acknowledge(event.stream, group, event.event_id)
                logger.debug(f"✅ Processed and acknowledged event {event.event_id} from {channel}")
                
            except Exception as e:
                logger.error(f"❌ Error processing event from {channel}: {e}")
                # Don't acknowledge on error - event will be retried
                
    except Exception as e:
        logger.error(f"💀 Fatal error in consumption loop for {channel}: {e}")
        # TODO: Implement reconnection logic


# =============================================================================
# METRICS ENDPOINT
# =============================================================================

async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    orthodoxy_health_status.set(2)  # Mark as healthy when metrics are accessible
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
