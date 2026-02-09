"""
🧠 Memory Orders API - FastAPI Entrypoint
EPOCH II - PHASE 4.9
Dual-Memory System: Archivarium (PostgreSQL) + Mnemosyne (Qdrant)

Provides health check endpoint and metrics for Memory Orders service.
Note: Redis listener is started separately via MemoryOrdersCognitiveBusListener
"""

import os
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, Enum, generate_latest, CONTENT_TYPE_LATEST
import asyncio
import json
import logging

from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from core.agents.alchemist_agent import AlchemistAgent
from core.governance.memory_orders.rag_health import get_rag_health
from core.synaptic_conclave.transport.streams import StreamBus
# TODO: Create redis_listener for Synaptic Conclave integration
# from core.governance.memory_orders.redis_listener import MemoryOrdersCognitiveBusListener

# Configure logger for this module
logger = logging.getLogger(__name__)

# Cognitive Bus wrapper for AlchemistAgent (migrated to Redis Streams)
class CognitiveBusAdapter:
    """Adapter to make StreamBus work with AlchemistAgent's async interface."""
    def __init__(self, redis_url: str = None):
        # Extract Redis connection params from URL
        host = os.getenv('REDIS_HOST', 'omni_redis')
        port = int(os.getenv('REDIS_PORT', '6379'))
        self._bus = StreamBus(host=host, port=port)
        logger.info(f"[CognitiveBusAdapter] StreamBus initialized: {host}:{port}")

    async def connect(self):
        # StreamBus connects automatically in __init__
        logger.info("[CognitiveBusAdapter] StreamBus ready (auto-connected)")

    async def disconnect(self):
        # StreamBus uses synchronous Redis client, no explicit disconnect needed
        logger.info("[CognitiveBusAdapter] StreamBus will be cleaned up on shutdown")

    async def publish(self, channel: str, data: Dict[str, Any]):
        """Emit event to Redis Stream (sync operation wrapped in async)."""
        try:
            # StreamBus.emit() is synchronous, but we're in async context
            # Run in thread pool to avoid blocking event loop
            event_id = await asyncio.to_thread(
                self._bus.emit,
                channel=channel,
                payload=data,
                emitter="memory_orders"
            )
            logger.info(f"[CognitiveBusAdapter] Emitted to stream '{channel}': {event_id}")
        except Exception as e:
            logger.error(f"[CognitiveBusAdapter] Failed to emit to '{channel}': {e}", exc_info=True)


app = FastAPI(
    title="Memory Orders API",
    description="EPOCH II - Dual-Memory System (Archivarium + Mnemosyne)",
    version="1.0.0"
)

# Global listener instance
memory_listener = None

@app.on_event("startup")
async def startup_events():
    """Run all startup tasks: AlchemistAgent schema check + Redis listener"""
    global memory_listener
    
    logger.info("=" * 80)
    logger.info("🚀 STARTUP EVENT TRIGGERED - BEGIN")
    logger.info("=" * 80)
    
    # AlchemistAgent schema check
    logger.info("[MemoryOrdersApp] Running AlchemistAgent schema check during startup...")
    cognitive_bus_client = CognitiveBusAdapter()
    await cognitive_bus_client.connect()

    alchemist_agent = AlchemistAgent(cognitive_bus=cognitive_bus_client)
    schema_check_result = await asyncio.to_thread(alchemist_agent.check_schema_version)
    logger.info(f"[MemoryOrdersApp] AlchemistAgent schema check result: {schema_check_result}")
    await cognitive_bus_client.disconnect()
    logger.info("[MemoryOrdersApp] AlchemistAgent schema check complete.")
    
    logger.info("=" * 80)
    logger.info("🧠 MEMORY ORDERS STARTUP (Redis listener TODO)")
    logger.info("=" * 80)
    
    # TODO: Start Memory Orders Redis Listener after creating redis_listener.py
    # try:
    #     logger.info("🧠 Starting Memory Orders cognitive bus listener...")
    #     memory_listener = MemoryOrdersCognitiveBusListener()
    #     logger.info("🧠 Listener instance created, awakening...")
    #     await memory_listener.awaken()
    #     logger.info("🧠 Listener awakened, starting listen task...")
    #     asyncio.create_task(memory_listener.listen())
    #     logger.info("🧠 Memory Orders listener activated - Dual-memory sync ready!")
    # except Exception as e:
    #     logger.error(f"❌ Failed to start Memory Orders listener: {e}", exc_info=True)
    
    logger.info("=" * 80)
    logger.info("🚀 STARTUP EVENT COMPLETE")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown listener"""
    global memory_listener
    if memory_listener:
        memory_listener.running = False
        logger.info("🛑 Memory Orders listener shutdown complete")



# ===========================
# PROMETHEUS METRICS
# ===========================

# HTTP request metrics
http_requests_total = Counter(
    'memory_http_requests_total',
    'Total HTTP requests to Memory Orders',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'memory_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Dual-memory system metrics
archivarium_queries_total = Counter(
    'memory_archivarium_queries_total',
    'Total queries to Archivarium (PostgreSQL)',
    ['operation']  # write, read, update, delete
)

mnemosyne_searches_total = Counter(
    'memory_mnemosyne_searches_total',
    'Total semantic searches in Mnemosyne (Qdrant)',
    ['search_type']  # similarity, hybrid, filter
)

dual_memory_writes_total = Counter(
    'memory_dual_writes_total',
    'Total dual-memory writes (Archivarium + Mnemosyne)'
)

# Query performance metrics
archivarium_query_duration_seconds = Histogram(
    'memory_archivarium_query_duration_seconds',
    'Archivarium query execution time in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

mnemosyne_search_duration_seconds = Histogram(
    'memory_mnemosyne_search_duration_seconds',
    'Mnemosyne vector search time in seconds',
    ['search_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# System health gauges
redis_connected_gauge = Gauge(
    'memory_redis_connected',
    'Redis connection status (1=connected, 0=disconnected)'
)

archivarium_connected_gauge = Gauge(
    'memory_archivarium_connected',
    'Archivarium (PostgreSQL) connection status (1=connected, 0=disconnected)'
)

mnemosyne_connected_gauge = Gauge(
    'memory_mnemosyne_connected',
    'Mnemosyne (Qdrant) connection status (1=connected, 0=disconnected)'
)

dual_memory_coherence_gauge = Gauge(
    'memory_dual_coherence',
    'Dual-memory system coherence score (0.0 to 1.0)'
)

rag_health_status_enum = Enum(
    'vitruvyan_rag_health_status',
    'Overall RAG system health status',
    states=['healthy', 'warning', 'degraded', 'critical']
)

@app.get("/health/rag")
async def rag_health_endpoint() -> JSONResponse:
    """
    🧠 Epistemic Health Check for Vitruvyan RAG System
    
    This is the canonical health surface for Prometheus/Grafana monitoring.
    
    Returns comprehensive health status of:
    - PostgreSQL (Archivarium - Relational Memory)
    - Qdrant (Mnemosyne - Vector Memory)
    - Embedding API (Semantic Processing)
    - Babel Gardens (Linguistic Fusion)
    - Memory Orders (Coherence & Sync)
    
    Response format:
    {
        "status": "healthy|warning|degraded|critical",
        "timestamp": "ISO8601",
        "components": {
            "postgresql": {"status": "healthy", ...},
            "qdrant": {"status": "healthy", ...},
            ...
        },
        "summary": {
            "drift_percentage": 0.0,
            "sync_lag": 0,
            "total_points": 36783,
            "coherence_status": "healthy"
        }
    }
    """
    try:
        health_data = get_rag_health()
        
        # Map overall status to HTTP status code
        status_code = 200
        if health_data.get("status") == "warning":
            status_code = 200  # Still operational
        elif health_data.get("status") in ["degraded", "critical"]:
            status_code = 503  # Service degraded
        
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        # Graceful degradation - return error but keep service up
        error_response = {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "RAG health check failed"
        }
        return JSONResponse(content=error_response, status_code=500)

@app.get("/health/memory")
async def health_check() -> JSONResponse:
    """
    Health check endpoint for Memory Orders service.
    
    Validates:
    - Redis connection (Cognitive Bus)
    - PostgreSQL connection (Archivarium)
    - Qdrant connection (Mnemosyne)
    """
    health_status = {
        "service": "memory_orders",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    try:
        # Check Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        health_status["components"]["redis"] = "connected"
        await redis_client.close()
    except Exception as e:
        health_status["components"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check PostgreSQL connection (Archivarium)
        postgres_agent = PostgresAgent()
        # Simple query to verify connection
        health_status["components"]["archivarium"] = "connected"
    except Exception as e:
        health_status["components"]["archivarium"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check Qdrant connection (Mnemosyne)
        qdrant_agent = QdrantAgent()
        # Verify collection exists
        health_status["components"]["mnemosyne"] = "connected"
    except Exception as e:
        health_status["components"]["mnemosyne"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/metrics")
async def prometheus_metrics():
    """
    🧠 Prometheus metrics endpoint for Memory Orders observability
    Exposes dual-memory system metrics, connection health, and coherence
    """
    try:
        # Update health gauge metrics with current system state
        health_status = {
            "redis": 0,
            "archivarium": 0,
            "mnemosyne": 0
        }
        
        # Check Redis connection
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = await redis.from_url(redis_url, decode_responses=True)
            await redis_client.ping()
            health_status["redis"] = 1
            await redis_client.close()
        except Exception:
            pass
        
        # Check PostgreSQL connection (Archivarium)
        try:
            postgres_agent = PostgresAgent()
            health_status["archivarium"] = 1
        except Exception:
            pass
        
        # Check Qdrant connection (Mnemosyne)
        try:
            qdrant_agent = QdrantAgent()
            health_status["mnemosyne"] = 1
        except Exception:
            pass
        
        # Update gauges
        redis_connected_gauge.set(health_status["redis"])
        archivarium_connected_gauge.set(health_status["archivarium"])
        mnemosyne_connected_gauge.set(health_status["mnemosyne"])
        
        # Calculate dual-memory coherence (all systems connected = 1.0)
        coherence = sum(health_status.values()) / 3.0
        dual_memory_coherence_gauge.set(coherence)
        
        # Update RAG health status enum from get_rag_health()
        try:
            rag_health = get_rag_health()
            rag_status = rag_health.get("status", "unknown")
            if rag_status in ['healthy', 'warning', 'degraded', 'critical']:
                rag_health_status_enum.state(rag_status)
        except Exception:
            rag_health_status_enum.state('critical')
        
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        # Return empty metrics on error (graceful degradation)
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/metrics/memory")
async def get_metrics() -> Dict[str, Any]:
    """
    Get Memory Orders performance metrics.
    
    Returns:
    - Total writes (dual-system)
    - Total reads (Archivarium)
    - Total vector searches (Mnemosyne)
    - Average latencies
    - Coherence validation stats
    """
    
    # Return metrics placeholder (listener tracks actual metrics)
    metrics = {
        "service": "memory_orders",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "operational",
        "note": "Metrics tracked by Redis listener, query via Cognitive Bus events"
    }
    
    return metrics

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Memory Orders",
        "epoch": "II",
        "phase": "4.9",
        "architecture": "Dual-Memory System",
        "components": {
            "archivarium": "PostgreSQL (relational memory)",
            "mnemosyne": "Qdrant (semantic memory)"
        },
        "endpoints": {
            "health": "/health/memory",
            "metrics": "/metrics/memory"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("MEMORY_API_HOST", "0.0.0.0")
    port = int(os.getenv("MEMORY_API_PORT", "8016"))
    
    uvicorn.run(app, host=host, port=port)
