from fastapi import FastAPI, Request, HTTPException
from typing import Any, Dict
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# DOMAIN-NEUTRAL CREWAI API SERVICE
# =============================================================================
# This service provides a domain-neutral HTTP interface for CrewAI execution.
# Domain-specific crew configurations should be imported from domains/* modules.
#
# Example integration with finance domain:
#   from domains.trade.crewai.crew_config import build_base_crew
#   from domains.trade.crewai.cognitive_wrapper import CognitiveCrew
#
# For other domains, implement similar modules in vitruvyan_core/domains/<domain>/
# =============================================================================

app = FastAPI(
    title="Vitruvyan CrewAI API (Domain-Neutral)",
    version="2.0.0",
    description="Domain-neutral CrewAI orchestration service for Vitruvyan Core"
)

# Global CognitiveCrew instance for event-driven processing (domain-specific)
cognitive_crew = None
cognitive_crew_task = None

# ----------------------------
# Startup & Shutdown Events
# ----------------------------
@app.on_event("startup")
async def startup_event():
    """
    Startup: Test infrastructure connectivity
    
    Note: Domain-specific CognitiveCrew initialization is disabled by default.
    To enable event-driven CrewAI for a specific domain:
    1. Import the domain's CognitiveCrew implementation
    2. Initialize and start listener in this function
    
    Example:
        from domains.trade.crewai.cognitive_wrapper import CognitiveCrew
        global cognitive_crew
        cognitive_crew = CognitiveCrew()
        asyncio.create_task(cognitive_crew.start_service())
    """
    global cognitive_crew, cognitive_crew_task
    
    try:
        logger.info("🚀 CrewAI API Service (Domain-Neutral) starting up...")
        logger.info("=" * 60)
        
        # Test Redis connection
        try:
            from core.foundation.cognitive_bus.redis_client import get_redis_bus
            redis_bus = get_redis_bus()
            logger.info("✅ Redis Bus connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis Bus unavailable: {e}")
        
        # Test PostgreSQL connection
        try:
            from core.foundation.persistence.postgres_agent import PostgresAgent
            postgres = PostgresAgent()
            logger.info("✅ PostgreSQL connected")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL unavailable: {e}")
        
        logger.info("ℹ️  Domain-specific CognitiveCrew listener NOT initialized (domain-neutral mode)")
        logger.info("   To enable event-driven CrewAI, import and initialize domain crew wrapper")
        logger.info("✅ CrewAI API Service ready on port 8005")
        logger.info("   📍 Endpoints: /health, /run")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ [CREWAI] Startup error: {e}")
        # Don't fail startup - service can still operate

@app.on_event("shutdown")
async def shutdown_event():
    """
    Gracefully stop CognitiveCrew listener if initialized
    """
    global cognitive_crew, cognitive_crew_task
    
    try:
        logger.info("🛑 [CREWAI] Stopping service...")
        
        if cognitive_crew and hasattr(cognitive_crew, 'stop_service'):
            cognitive_crew.stop_service()
        
        if cognitive_crew_task:
            cognitive_crew_task.cancel()
            try:
                await cognitive_crew_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ [CREWAI] Service stopped")
        
    except Exception as e:
        logger.error(f"⚠️ [CREWAI] Error during shutdown: {e}")


# ----------------------------
# Utility Functions
# ----------------------------
def _serialize(obj: Any) -> Dict[str, Any]:
    """
    Serialize crew/pydantic/LLM output to dict
    Handles various object types from CrewAI execution
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "dict"):  # Pydantic model
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return vars(obj)
    return {"raw": str(obj)}


# ----------------------------
# HTTP Endpoints
# ----------------------------
@app.get("/health")
def health():
    """
    Health check endpoint
    
    Returns service status and connectivity information
    """
    status = {
        "status": "ok",
        "service": "crewai",
        "mode": "domain-neutral",
        "api": "running"
    }
    
    # Add Redis status
    try:
        from core.foundation.cognitive_bus.redis_client import get_redis_bus
        redis_bus = get_redis_bus()
        status["redis"] = "connected"
    except Exception:
        status["redis"] = "unavailable"
    
    # Add PostgreSQL status
    try:
        from core.foundation.persistence.postgres_agent import PostgresAgent
        postgres = PostgresAgent()
        status["postgres"] = "connected"
    except Exception:
        status["postgres"] = "unavailable"
    
    # Add CognitiveCrew status if initialized
    if cognitive_crew and hasattr(cognitive_crew, 'get_stats'):
        try:
            stats = cognitive_crew.get_stats()
            status["cognitive_crew"] = {
                "running": True,
                "strategies_executed": stats.get("strategies_executed", 0),
                "redis_connected": stats.get("bridge_stats", {}).get("redis_connected", False)
            }
        except Exception:
            status["cognitive_crew"] = {"running": False, "error": "stats unavailable"}
    else:
        status["cognitive_crew"] = {"running": False, "mode": "domain-neutral"}
    
    return status


@app.post("/run")
async def run_crew(request: Request):
    """
    Execute CrewAI crew with provided configuration
    
    This is a domain-neutral endpoint. The request payload should contain
    domain-specific crew configuration and execution parameters.
    
    Request Body (domain-specific example):
        {
            "domain": "finance",
            "crew_type": "strategy_analysis",
            "parameters": {
                "ticker": "AAPL",
                "horizon": "medium",
                "amount": 10000
            }
        }
    
    Returns:
        {
            "ok": true,
            "domain": "finance",
            "crew_type": "strategy_analysis",
            "result": {...},
            "execution_time_ms": 15234
        }
    
    Note: Domain-specific crew execution requires importing and configuring
    domain crew builders. Currently disabled in domain-neutral mode.
    """
    try:
        payload = await request.json()
        domain = payload.get("domain", "unknown")
        crew_type = payload.get("crew_type", "unknown")
        
        logger.info(f"🧠 [CREWAI /run] Request received: domain={domain}, type={crew_type}")
        
        # Domain-neutral mode: return placeholder response
        # To enable domain execution, implement domain-specific handlers:
        #
        # if domain == "finance":
        #     from domains.trade.crewai.crew_config import build_base_crew
        #     crew = build_base_crew(payload.get("parameters", {}))
        #     result = crew.kickoff(inputs=payload.get("parameters", {}))
        #     return {"ok": True, "domain": domain, "result": _serialize(result)}
        
        return {
            "ok": False,
            "error": "Domain-neutral mode: no crew execution configured",
            "hint": "Import and configure domain-specific crew builder in /run endpoint",
            "received": {
                "domain": domain,
                "crew_type": crew_type,
                "parameters": payload.get("parameters", {})
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [CREWAI /run] Execution failed: {e}")
        return {"ok": False, "error": str(e)}
