"""
🕯 Synaptic Conclave API - Main Application
Sacred Communication Hub for the Vitruvyan Cognitive Organism

This is the central nervous system that enables semantic communication
between all Sacred Orders through Redis-based event distribution.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import structlog

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Import cognitive bus components
from vitruvyan_core.core.foundation.cognitive_bus import (
    get_heart, get_herald, get_pulse, get_scribe, get_lexicon,
    publish_event, subscribe_to_domain, start_system_pulse
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("conclave.api")


# ============================================================
# PROMETHEUS METRICS
# ============================================================

# HTTP Request metrics
http_requests_total = Counter(
    'conclave_http_requests_total',
    'Total HTTP requests received by Conclave',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'conclave_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# Cognitive Bus metrics
cognitive_events_published = Counter(
    'conclave_cognitive_events_published_total',
    'Total cognitive events published to Redis',
    ['domain', 'intent']
)

cognitive_events_subscribed = Counter(
    'conclave_cognitive_events_subscribed_total',
    'Total cognitive events subscribed to',
    ['domain']
)

cognitive_event_processing_duration = Histogram(
    'conclave_cognitive_event_processing_seconds',
    'Time to process and publish cognitive events',
    ['domain']
)

# System health metrics
active_orders_gauge = Gauge(
    'conclave_active_orders',
    'Number of active orchestration orders'
)

redis_connection_status = Gauge(
    'conclave_redis_connected',
    'Redis connection status (1=connected, 0=disconnected)'
)

pulse_active_status = Gauge(
    'conclave_pulse_active',
    'System pulse status (1=active, 0=inactive)'
)

# ============================================================
# SYNAPTIC CONCLAVE — REDIS EVENT LISTENER (Audit Q4 2025)
# ============================================================

async def conclave_event_listener(heart):
    """
    Dedicated Redis event listener for Synaptic Conclave.
    Subscribes to all epistemic channels and processes incoming events.
    
    Restored during Q4 2025 audit - ensures Conclave actively listens
    to Sacred Orders communication, not just serves HTTP endpoints.
    """
    import redis.asyncio as redis
    import json
    
    # Use print() for guaranteed output (bypasses logging config issues)
    print("[CONCLAVE LISTENER] Starting initialization...")
    
    redis_host = os.getenv("REDIS_HOST", "vitruvyan_redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    throttle_interval = int(os.getenv("CONCLAVE_THROTTLE_INTERVAL", 5))
    
    # Channels to subscribe to
    channels = [
        "conclave_events",
        "epistemic_drift", 
        "memory_orders",
        "perception.codex",
        "reason.neural",
        "discourse.babel",
        "truth.orthodoxy",
        "truth.vault"
    ]
    
    print(f"[CONCLAVE LISTENER] Redis: {redis_host}:{redis_port}, Channels: {len(channels)}")
    logger.info(f"🔊 [Conclave] Starting Redis listener on {redis_host}:{redis_port}")
    
    try:
        # Create dedicated Redis connection for pub/sub
        print("[CONCLAVE LISTENER] Creating Redis connection...")
        r = await redis.from_url(f"redis://{redis_host}:{redis_port}")
        pubsub = r.pubsub()
        
        # Subscribe to all channels
        print("[CONCLAVE LISTENER] Subscribing to channels...")
        await pubsub.subscribe(*channels)
        print(f"[CONCLAVE LISTENER] ✅ Subscribed to {len(channels)} channels!")
        logger.info(f"🔊 [Conclave] Subscribed to {len(channels)} channels: {', '.join(channels)}")
        
        # Event listener loop
        print("[CONCLAVE LISTENER] Entering event listener loop...")
        async for message in pubsub.listen():
            try:
                if message and message["type"] == "message":
                    channel = message["channel"].decode("utf-8") if isinstance(message["channel"], bytes) else message["channel"]
                    payload = message["data"].decode("utf-8") if isinstance(message["data"], bytes) else message["data"]
                    
                    print(f"[CONCLAVE LISTENER] 🔊 Received on '{channel}': {payload[:100]}")
                    logger.info(f"🔊 [Conclave] Received event on channel '{channel}': {payload[:100]}...")
                    
                    # Log to structured log (PostgreSQL integration deferred - core.leo not in container)
                    try:
                        logger.info(
                            "conclave_event_received",
                            channel=channel,
                            payload_preview=payload[:200],
                            event_size=len(payload)
                        )
                    except Exception as log_err:
                        print(f"[CONCLAVE LISTENER] ⚠️  Logging error: {log_err}")
                    
                    # Throttle to prevent tight loops
                    await asyncio.sleep(throttle_interval)
                    
            except asyncio.CancelledError:
                # Graceful shutdown - break the loop immediately
                print("[CONCLAVE LISTENER] 🛑 Shutdown signal received")
                break
            except Exception as msg_err:
                print(f"[CONCLAVE LISTENER] ❌ Message error: {msg_err}")
                logger.error(f"❌ [Conclave] Error processing message: {msg_err}")
                await asyncio.sleep(throttle_interval)
        
    except asyncio.CancelledError:
        print("[CONCLAVE LISTENER] 🛑 Cancelled (graceful shutdown)")
        logger.info("🛑 [Conclave] Redis listener cancelled (graceful shutdown)")
        try:
            # Unsubscribe from channels
            await pubsub.unsubscribe()
            # Note: Do NOT call pubsub.aclose() here - it causes "aclose() already running" error
            # The async generator will be closed automatically when the function exits
            # Close Redis connection
            await r.aclose()
        except Exception as cleanup_err:
            print(f"[CONCLAVE LISTENER] ⚠️  Cleanup error: {cleanup_err}")
        raise  # Re-raise to allow proper task cancellation
    except Exception as e:
        print(f"[CONCLAVE LISTENER] ❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"❌ [Conclave] Redis listener crashed: {e}")
        # Auto-restart after error (resilience)
        await asyncio.sleep(10)
        asyncio.create_task(conclave_event_listener(heart))
        print("[CONCLAVE LISTENER] 🔄 Restarting after crash...")

# ============================================================
# PYDANTIC MODELS
# ============================================================
class EventEmission(BaseModel):
    domain: str
    intent: str
    payload: Dict[str, Any]


class EventSubscription(BaseModel):
    domain: str
    callback_url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    conclave_version: str
    heart_beating: bool
    pulse_active: bool
    redis_connected: bool
    active_orders: int


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown.
    """
    logger.info("🕯 Synaptic Conclave awakening...")
    
    try:
        # Awaken the Heart (Redis connection)
        heart = await get_heart()
        if not heart.is_beating:
            logger.error("💔 Failed to awaken Conclave Heart")
            raise RuntimeError("Conclave Heart failed to awaken")
        
        # Start the system pulse (reduced from 30s to 120s for CPU optimization)
        await start_system_pulse(interval=120)
        
        # Start background tasks
        pulse = await get_pulse()
        
        # Synaptic Conclave — Redis Listener Restored (Audit Q4 2025)
        # Start dedicated event listener for Sacred Orders communication
        listener_task = asyncio.create_task(conclave_event_listener(heart))
        logger.info("🔊 Conclave Redis listener task started")
        
        # Emit awakening event
        await publish_event("conclave", "awakened", {
            "conclave_version": "1.0.0",
            "startup_time": datetime.utcnow().isoformat(),
            "components_initialized": ["heart", "herald", "pulse", "scribe", "lexicon"]
        })
        
        logger.info("✅ Synaptic Conclave fully awakened and operational")
        
        yield  # Application runs here
        
    except Exception as e:
        logger.error("💔 Failed to awaken Conclave", error=str(e))
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("😴 Synaptic Conclave entering rest...")
        
        try:
            # Cancel and await the listener task
            if 'listener_task' in locals() and not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    logger.info("🛑 Listener task cancelled successfully")
            
            # Stop pulse
            pulse = await get_pulse()
            await pulse.stop_beating()
            await pulse.stop_beating()
            
            # Silence the heart
            heart = await get_heart()
            await heart.silence()
            
            logger.info("😴 Synaptic Conclave at rest")
            
        except Exception as e:
            logger.error("💔 Error during Conclave shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="🕯 Synaptic Conclave Core",
    description="The Sacred Heart of all Orders - Redis Pub/Sub nervous system on port 8012",
    version="1.0.0",
    lifespan=lifespan  # ⚠️  CRITICAL: Enable lifespan context manager for Redis listener
)


# Health endpoint
@app.get("/health/conclave", response_model=HealthResponse)
async def health_check():
    """
    Check the vital signs of the Synaptic Conclave.
    Lightweight check - does NOT probe all Orders (use /orders/health for that).
    """
    try:
        heart = await get_heart()
        pulse = await get_pulse()
        
        # Get heart vitals
        heart_vitals = await heart.get_vitals()
        
        # Get pulse status
        pulse_status = await pulse.get_pulse_status()
        
        # OPTIMIZATION: Don't check all Orders on every healthcheck (too expensive)
        # Use /orders/health endpoint for detailed Order status
        
        return HealthResponse(
            status="alive",
            timestamp=datetime.utcnow().isoformat(),
            conclave_version="1.0.0",
            heart_beating=heart_vitals["is_beating"],
            pulse_active=pulse_status["is_beating"],
            redis_connected=heart_vitals["redis_connected"],
            active_orders=0  # Placeholder - use /orders/health for accurate count
        )
        
    except Exception as e:
        logger.error("💔 Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ============================================================
# PROMETHEUS METRICS ENDPOINT
# ============================================================

@app.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics for monitoring.
    
    Metrics include:
    - HTTP request counts and latencies
    - Cognitive event processing stats
    - System health indicators (Redis, pulse, active orders)
    """
    try:
        # Update gauge metrics with current values
        heart = await get_heart()
        pulse = await get_pulse()
        herald = await get_herald()
        
        # Update Redis connection status
        heart_vitals = await heart.get_vitals()
        redis_connection_status.set(1 if heart_vitals["redis_connected"] else 0)
        
        # Update pulse status
        pulse_status = await pulse.get_pulse_status()
        pulse_active_status.set(1 if pulse_status["is_beating"] else 0)
        
        # Update active orders count
        order_health = await herald.check_order_health()
        active_count = sum(1 for status in order_health.values() 
                          if status.get("status") == "alive")
        active_orders_gauge.set(active_count)
        
        # Generate and return metrics in Prometheus format
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        logger.error("📊 Metrics generation failed", error=str(e))
        # Return empty metrics on error (better than failing the scrape)
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================
# EVENT EMISSION ENDPOINT
# ============================================================

@app.post("/emit/{event_type}")
async def emit_event(event_type: str, emission: EventEmission, background_tasks: BackgroundTasks):
    """
    Emit a semantic event through the Conclave.
    
    Event type format: domain.intent (e.g., "babel.fusion.completed")
    """
    # Start timing for metrics
    start_time = datetime.utcnow()
    
    try:
        # Validate event format
        if '.' not in event_type:
            http_requests_total.labels(method='POST', endpoint='/emit', status='400').inc()
            raise HTTPException(
                status_code=400, 
                detail="Event type must be in format 'domain.intent'"
            )
        
        domain, intent = event_type.split('.', 1)
        
        # Override domain/intent if provided in body (body takes precedence)
        final_domain = emission.domain if emission.domain else domain
        final_intent = emission.intent if emission.intent else intent
        
        # Validate with lexicon (temporarily bypassed for Sacred Orders Event Bus testing)
        try:
            lexicon = await get_lexicon()
            if not lexicon.validate_event(final_domain, final_intent, emission.payload):
                logger.warning(
                    "📯 Event validation failed (continuing anyway)",
                    domain=final_domain,
                    intent=final_intent
                )
        except Exception as e:
            logger.warning(
                "📯 Event validation bypassed due to lexicon error",
                domain=final_domain,
                intent=final_intent,
                error=str(e)
            )
            # Continue without validation for testing
        
        # Emit the event
        success = await publish_event(final_domain, final_intent, emission.payload)
        
        if not success:
            http_requests_total.labels(method='POST', endpoint='/emit', status='500').inc()
            raise HTTPException(status_code=500, detail="Failed to emit event")
        
        # Track metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        cognitive_events_published.labels(domain=final_domain, intent=final_intent).inc()
        cognitive_event_processing_duration.labels(domain=final_domain).observe(duration)
        http_requests_total.labels(method='POST', endpoint='/emit', status='200').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/emit').observe(duration)
        
        # Route to appropriate Orders in background
        herald = await get_herald()
        background_tasks.add_task(
            herald.route_event, 
            final_domain, 
            final_intent, 
            emission.payload
        )
        
        # Chronicle the event
        scribe = await get_scribe()
        background_tasks.add_task(
            scribe.chronicle_event,
            final_domain,
            final_intent, 
            emission.payload,
            datetime.utcnow().isoformat(),
            "conclave.api.emit"
        )
        
        return {
            "emitted": True,
            "event_type": f"{final_domain}.{final_intent}",
            "timestamp": datetime.utcnow().isoformat(),
            "will_route_to_orders": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("💔 Failed to emit event", event_type=event_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Emission failed: {str(e)}")


# Recent events endpoint
@app.get("/events/recent")
async def get_recent_events(limit: int = 100, domain: str = None):
    """
    Get recent semantic events from the Scribe's chronicles.
    """
    try:
        scribe = await get_scribe()
        events = scribe.get_recent_events(limit=limit, domain_filter=domain)
        
        return {
            "events": events,
            "total_returned": len(events),
            "limit": limit,
            "domain_filter": domain,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to get recent events", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve events: {str(e)}")


# Event statistics endpoint
@app.get("/events/statistics")
async def get_event_statistics():
    """
    Get event statistics from the Scribe.
    """
    try:
        scribe = await get_scribe()
        stats = scribe.get_event_statistics()
        
        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to get event statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


# Orders health endpoint
@app.get("/orders/health")
async def get_orders_health():
    """
    Check health status of all Sacred Orders.
    """
    try:
        herald = await get_herald()
        order_health = await herald.check_order_health()
        
        # Add summary
        total_orders = len(order_health)
        alive_orders = sum(1 for status in order_health.values() 
                          if status.get("status") == "alive")
        
        return {
            "orders": order_health,
            "summary": {
                "total_orders": total_orders,
                "alive_orders": alive_orders,
                "health_percentage": (alive_orders / total_orders * 100) if total_orders > 0 else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to check Orders health", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Routing map endpoint
@app.get("/routing/map")
async def get_routing_map():
    """
    Get the complete event routing map.
    """
    try:
        herald = await get_herald()
        routing_map = await herald.get_routing_map()
        
        return {
            "routing_map": routing_map,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to get routing map", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routing map: {str(e)}")


# Sacred lexicon endpoint
@app.get("/lexicon/domains")
async def get_lexicon_domains():
    """
    Get all available domains and their schemas.
    """
    try:
        lexicon = await get_lexicon()
        schema_export = lexicon.export_schema()
        
        return {
            "lexicon": schema_export,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to get lexicon", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve lexicon: {str(e)}")


# Pulse status endpoint
@app.get("/pulse/status")
async def get_pulse_status():
    """
    Get system pulse status and vitals.
    """
    try:
        pulse = await get_pulse()
        pulse_status = await pulse.get_pulse_status()
        
        return {
            "pulse": pulse_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to get pulse status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pulse status: {str(e)}")


# Force heartbeat endpoint
@app.post("/pulse/heartbeat")
async def force_heartbeat():
    """
    Force an immediate system heartbeat.
    """
    try:
        pulse = await get_pulse()
        success = await pulse.force_heartbeat()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to force heartbeat")
        
        return {
            "heartbeat_forced": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("💔 Failed to force heartbeat", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to force heartbeat: {str(e)}")


# Event reception endpoint (for Orders to receive events)
@app.post("/events/receive")
async def receive_event(event_data: Dict[str, Any]):
    """
    Receive events from other Orders (webhook endpoint).
    This is primarily for testing and inter-Order communication.
    """
    try:
        logger.info(
            "📨 Event received via webhook",
            domain=event_data.get("domain"),
            intent=event_data.get("intent"),
            source=event_data.get("source")
        )
        
        # Chronicle the received event
        scribe = await get_scribe()
        await scribe.chronicle_event(
            event_data.get("domain", "unknown"),
            event_data.get("intent", "unknown"),
            event_data.get("payload", {}),
            event_data.get("timestamp", datetime.utcnow().isoformat()),
            f"webhook.{event_data.get('source', 'unknown')}"
        )
        
        return {
            "received": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("💔 Failed to receive event", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to receive event: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    port = int(os.getenv("CONCLAVE_PORT", 8012))
    host = os.getenv("CONCLAVE_HOST", "0.0.0.0")
    
    logger.info(f"🕯 Starting Synaptic Conclave on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )