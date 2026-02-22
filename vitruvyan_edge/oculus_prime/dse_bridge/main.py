"""
Vitruvyan Intake → DSE Bridge Service

FastAPI service that bridges Codex Hunters (semantic enrichment) and DSE Epistemic Chain (Pattern Weavers).

ARCHITECTURAL CONTEXT:
- Listens to: codex.evidence.indexed (Redis event)
- Creates: dse_intake_evidence records (PostgreSQL)
- Emits: langgraph.intake.ready (triggers Pattern Weavers node)

SERVICE ENDPOINTS:
- GET /health → Health check
- GET /metrics → Prometheus metrics
- GET /status → Bridge statistics

Author: Vitruvyan Development Team
Created: 2026-01-11
Port: 8021
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import os

# Vitruvyan imports
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

try:
    from vitruvyan_core.core.orchestration.bridges.intake_dse_bridge import IntakeDSEBridge
except Exception:
    class IntakeDSEBridge:  # type: ignore[no-redef]
        """
        Transitional local bridge fallback.
        Keeps service bootable when core bridge module is not available yet.
        """

        def __init__(self):
            self.stream_bus = StreamBus(
                host=os.getenv("REDIS_HOST", "core_redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            )

        async def start(self):
            logger.warning(
                "IntakeDSEBridge core module missing; running fallback no-op listener."
            )
            while True:
                await asyncio.sleep(60)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Vitruvyan Intake → DSE Bridge",
    description="Bridge service between Codex Hunters and DSE Epistemic Chain",
    version="1.0.0"
)

# Global bridge instance
bridge: IntakeDSEBridge = None  # type: ignore[assignment]


@app.on_event("startup")
async def startup_event():
    """Initialize bridge and start event listener on startup"""
    global bridge
    
    logger.info("🚀 Starting Vitruvyan Intake → DSE Bridge Service...")
    
    # Initialize bridge
    bridge = IntakeDSEBridge()
    
    # Start bridge listener in background
    asyncio.create_task(bridge.start())
    
    logger.info("✅ Bridge Service started successfully")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        200 OK: Service is healthy
        503 Service Unavailable: Service is unhealthy
    """
    try:
        # Check PostgreSQL connection
        pg = PostgresAgent()
        with pg.connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        
        # Check Redis Streams connection
        if bridge and getattr(bridge, "stream_bus", None):
            bridge.stream_bus.client.ping()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "intake_dse_bridge",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/metrics")
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint
    
    Metrics:
    - bridge_operations_total: Total bridge operations
    - bridge_operations_success: Successful operations
    - bridge_operations_failed: Failed operations
    - bridge_events_processed: Total events processed
    """
    try:
        pg = PostgresAgent()
        
        # Query metrics from bridge_operations_log
        with pg.connection.cursor() as cur:
            # Total operations
            cur.execute("SELECT COUNT(*) FROM bridge_operations_log")
            total_operations = cur.fetchone()[0]
            
            # Success count
            cur.execute("SELECT COUNT(*) FROM bridge_operations_log WHERE status = 'success'")
            success_count = cur.fetchone()[0]
            
            # Failed count
            cur.execute("SELECT COUNT(*) FROM bridge_operations_log WHERE status = 'failed'")
            failed_count = cur.fetchone()[0]
            
            # Last 24 hours
            cur.execute("""
                SELECT COUNT(*) FROM bridge_operations_log
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            last_24h = cur.fetchone()[0]
        
        # Format as Prometheus metrics
        metrics = f"""
# HELP bridge_operations_total Total bridge operations
# TYPE bridge_operations_total counter
bridge_operations_total {total_operations}

# HELP bridge_operations_success Successful bridge operations
# TYPE bridge_operations_success counter
bridge_operations_success {success_count}

# HELP bridge_operations_failed Failed bridge operations
# TYPE bridge_operations_failed counter
bridge_operations_failed {failed_count}

# HELP bridge_operations_24h Bridge operations in last 24 hours
# TYPE bridge_operations_24h gauge
bridge_operations_24h {last_24h}
"""
        
        return JSONResponse(
            status_code=200,
            content={"metrics": metrics.strip()}
        )
    
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """
    Get bridge status and statistics
    
    Returns:
        JSON with bridge statistics and recent operations
    """
    try:
        pg = PostgresAgent()
        
        # Query bridge statistics
        with pg.connection.cursor() as cur:
            # Total operations by status
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM bridge_operations_log
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cur.fetchall()}
            
            # Recent operations (last 10)
            cur.execute("""
                SELECT 
                    operation_id,
                    evidence_id,
                    operation_type,
                    status,
                    created_at
                FROM bridge_operations_log
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            recent_ops = []
            for row in cur.fetchall():
                recent_ops.append({
                    "operation_id": str(row[0]),
                    "evidence_id": row[1],
                    "operation_type": row[2],
                    "status": row[3],
                    "created_at": row[4].isoformat()
                })
        
        return {
            "service": "intake_dse_bridge",
            "version": "1.0.0",
            "subscribe_channel": "codex.evidence.indexed",
            "publish_channel": "langgraph.intake.ready",
            "statistics": {
                "total_operations": sum(status_counts.values()),
                "status_breakdown": status_counts,
                "success_rate": (
                    status_counts.get('success', 0) / sum(status_counts.values()) * 100
                    if sum(status_counts.values()) > 0 else 0
                )
            },
            "recent_operations": recent_ops,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Vitruvyan Intake → DSE Bridge",
        "version": "1.0.0",
        "description": "Bridge between Codex Hunters (semantic enrichment) and DSE Epistemic Chain (Pattern Weavers)",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "status": "/status"
        },
        "architecture": {
            "subscribes_to": "codex.evidence.indexed",
            "creates": "dse_intake_evidence (PostgreSQL)",
            "emits": "langgraph.intake.ready"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("BRIDGE_PORT", "8021"))
    host = os.getenv("BRIDGE_HOST", "0.0.0.0")
    
    logger.info(f"🌉 Starting Bridge Service on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
