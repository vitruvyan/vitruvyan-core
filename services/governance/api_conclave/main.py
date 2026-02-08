"""
🕯 Synaptic Conclave API - Main Application
Sacred Communication Hub for the Vitruvyan Cognitive Organism

REWRITTEN Feb 8, 2026: 100% Redis Streams, zero Pub/Sub.
Epistemic Observatory pattern: HTTP bridge > Streams (passive observer).
Sacred Orders autonomy: consumers create streams (mkstream=True).
"""

import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import structlog

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Import Streams architecture (Redis Streams canonical since Jan 24, 2026)
from core.synaptic_conclave.transport.streams import StreamBus


# Configure structured logging
logger = structlog.get_logger("conclave.api")

# ============================================================
# PROMETHEUS METRICS (PRESERVED)
# ============================================================
streams_events_emitted_total = Counter(
    'conclave_streams_events_emitted_total',
    'Total events emitted to Redis Streams',
    ['channel']
)

http_requests_total = Counter(
    'conclave_http_requests_total',
    'Total HTTP requests received',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'conclave_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

redis_connection_status = Gauge(
    'conclave_redis_connected',
    'Redis connection status (1=connected, 0=disconnected)'
)


# ============================================================
# GLOBAL STATE
# ============================================================
# Initialize StreamBus on module load (thread-safe singleton pattern)
redis_host = os.getenv("REDIS_HOST", "omni_redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))

try:
    stream_bus = StreamBus(host=redis_host, port=redis_port)
    logger.info(f"✅ StreamBus initialized: {redis_host}:{redis_port}")
    redis_connection_status.set(1)
except Exception as e:
    logger.error(f"❌ StreamBus initialization failed: {e}")
    stream_bus = None
    redis_connection_status.set(0)

# ============================================================
# PYDANTIC MODELS
# ============================================================
class EventPayload(BaseModel):
    """Event payload for emission"""
    data: Dict[str, Any]
    emitter: str = "conclave.api"

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    redis_connected: bool
    service: str
    version: str

# ============================================================
# FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title="🕯 Synaptic Conclave - Epistemic Observatory",
    description="HTTP-to-Streams bridge (Streams-native since Jan 24, 2026)",
    version="2.0.0"
)

@app.get("/", tags=["info"])
async def root():
    """Service information"""
    return {
        "service": "synaptic_conclave",
        "role": "epistemic_observatory",
        "architecture": "redis_streams",
        "version": "2.0.0",
        "philosophy": "octopus_mycelium",
        "sacred_invariants": [
            "no_payload_inspection",
            "no_correlation",
            "no_semantic_routing",
            "no_synthesis"
        ]
    }

@app.post("/emit/{emission_channel}", tags=["streams"])
async def emit_event(emission_channel: str, payload: EventPayload):
    """
    Emit event to Redis Streams.
    
    Channel format: domain.action (e.g., 'codex.discovery.mapped')
    Payload: arbitrary JSON data
    
    Returns: event_id from Redis (e.g., '1770569658797-0')
    """
    start_time = datetime.utcnow()
    
    if not stream_bus:
        http_requests_total.labels(method='POST', endpoint='/emit', status='503').inc()
        raise HTTPException(status_code=503, detail="StreamBus not initialized")
    
    try:
        # Emit to Redis Streams
        event_id = stream_bus.emit(
            channel=emission_channel,
            payload=payload.data,
            emitter=payload.emitter
        )
        
        # Metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        streams_events_emitted_total.labels(channel=emission_channel).inc()
        http_requests_total.labels(method='POST', endpoint='/emit', status='200').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/emit').observe(duration)
        
        logger.info(f"📯 Event emitted: {emission_channel} -> {event_id}")
        
        return {
            "emitted": True,
            "channel": emission_channel,
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        http_requests_total.labels(method='POST', endpoint='/emit', status='500').inc()
        logger.error(f"❌ Emission failed: {emission_channel} - {e}")
        raise HTTPException(status_code=500, detail=f"Emission failed: {str(e)}")

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check: verify Redis connection.
    
    Returns: service status, Redis connection state
    """
    try:
        if not stream_bus:
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                redis_connected=False,
                service="api_conclave",
                version="2.0.0"
            )
        
        # Test Redis connection with PING
        import redis
        r = redis.Redis(host=redis_host, port=redis_port)
        r.ping()
        
        redis_connection_status.set(1)
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            redis_connected=True,
            service="api_conclave",
            version="2.0.0"
        )
        
    except Exception as e:
        redis_connection_status.set(0)
        logger.error(f"💔 Health check failed: {e}")
        
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            redis_connected=False,
            service="api_conclave",
            version="2.0.0"
        )

@app.get("/metrics", tags=["metrics"])
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Exposes:
    - conclave_streams_events_emitted_total (counter)
    - conclave_http_requests_total (counter)
    - conclave_http_request_duration_seconds (histogram)
    - conclave_redis_connected (gauge)
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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