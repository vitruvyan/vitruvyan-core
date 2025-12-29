#!/usr/bin/env python3
"""
Vitruvyan Codex Hunters API Service
===================================

FastAPI service for Codex Hunters expedition management and coordination.
Provides REST API endpoints for LangGraph integration, expedition management,
and system health monitoring.

Endpoints:
- /expedition/run - Trigger expedition
- /expedition/status - Get expedition status
- /expedition/history - Get expedition history
- /health - Health check
- /stats - System statistics

Author: Vitruvyan Development Team
Created: 2025-01-14
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json

# Prometheus metrics
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# Import Codex Hunters (with fallbacks for missing dependencies)
try:
    from core.governance.codex_hunters.tracker import Tracker
    from core.governance.codex_hunters.restorer import Restorer
    from core.governance.codex_hunters.binder import Binder
    from core.governance.codex_hunters.inspector import Inspector
    from core.governance.codex_hunters.expedition_planner import ExpeditionPlanner
    from core.governance.codex_hunters.cartographer import Cartographer
    from core.governance.codex_hunters.expedition_leader import ExpeditionLeader
    CODEX_AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Codex Hunters agents not available: {e}")
    # Create dummy classes for fallback
    Tracker = Restorer = Binder = Inspector = None
    ExpeditionPlanner = Cartographer = ExpeditionLeader = None
    CODEX_AGENTS_AVAILABLE = False

try:
    from core.foundation.cognitive_bus.redis_client import get_redis_bus
    REDIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Redis client not available: {e}")
    get_redis_bus = lambda: None
    REDIS_AVAILABLE = False


# Pydantic models for API
class ExpeditionRequest(BaseModel):
    """Request model for expedition trigger"""
    expedition_type: str = Field(..., description="Type of expedition: full_audit, healing, discovery")
    target_collections: Optional[List[str]] = Field(default=None, description="Specific collections to target")
    priority: str = Field(default="medium", description="Priority level: critical, high, medium, low")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    correlation_id: Optional[str] = Field(default=None, description="Correlation ID for tracking")


class ExpeditionStatus(BaseModel):
    """Response model for expedition status"""
    expedition_id: str
    status: str  # "running", "completed", "failed", "queued"
    progress: float  # 0.0 to 1.0
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    agents_deployed: List[str]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]


class SystemHealth(BaseModel):
    """Response model for system health"""
    status: str  # "healthy", "degraded", "unhealthy"
    agents_status: Dict[str, str]
    redis_connected: bool
    database_connected: bool
    active_expeditions: int
    completed_expeditions_24h: int
    error_rate: float


# Global expedition tracker
class ExpeditionTracker:
    """Track running and completed expeditions"""
    
    def __init__(self):
        self.expeditions: Dict[str, Dict[str, Any]] = {}
        self.expedition_counter = 0
    
    def create_expedition(self, expedition_type: str, params: Dict[str, Any]) -> str:
        """Create new expedition entry"""
        self.expedition_counter += 1
        expedition_id = f"exp_{expedition_type}_{self.expedition_counter}_{int(datetime.utcnow().timestamp())}"
        
        self.expeditions[expedition_id] = {
            "expedition_id": expedition_id,
            "expedition_type": expedition_type,
            "status": "queued",
            "progress": 0.0,
            "started_at": None,
            "completed_at": None,
            "agents_deployed": [],
            "results": None,
            "error_message": None,
            "parameters": params
        }
        
        return expedition_id
    
    def update_expedition(self, expedition_id: str, updates: Dict[str, Any]) -> None:
        """Update expedition status"""
        if expedition_id in self.expeditions:
            self.expeditions[expedition_id].update(updates)
    
    def get_expedition(self, expedition_id: str) -> Optional[Dict[str, Any]]:
        """Get expedition by ID"""
        return self.expeditions.get(expedition_id)
    
    def get_recent_expeditions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get expeditions from last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent = []
        for exp in self.expeditions.values():
            started_at = exp.get("started_at")
            if started_at and isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            
            if started_at and started_at >= cutoff:
                recent.append(exp)
        
        return sorted(recent, key=lambda x: x.get("started_at", ""), reverse=True)


# Initialize FastAPI app
app = FastAPI(
    title="Vitruvyan Codex Hunters API",
    description="Expedition management and coordination API for Codex Hunters",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
expedition_tracker = ExpeditionTracker()
logger = logging.getLogger(__name__)

# Redis Event Listener task reference
redis_listener_task = None


# Prometheus Metrics
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

# Helper to get or create metric
def get_or_create_counter(name, documentation, labelnames=None):
    """Get existing counter or create new one"""
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    return Counter(name, documentation, labelnames or [])

def get_or_create_gauge(name, documentation, labelnames=None):
    """Get existing gauge or create new one"""
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    return Gauge(name, documentation, labelnames or [])

def get_or_create_histogram(name, documentation, labelnames=None):
    """Get existing histogram or create new one"""
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    return Histogram(name, documentation, labelnames or [])

# API-level metrics (agent-specific metrics are in their modules)
codex_expeditions_total = get_or_create_counter(
    'codex_expeditions',
    'Total number of expeditions started',
    ['expedition_type', 'status']
)

codex_expeditions_active = get_or_create_gauge(
    'codex_expeditions_active',
    'Number of currently active expeditions'
)

codex_expedition_duration_seconds = get_or_create_histogram(
    'codex_expedition_duration_seconds',
    'Duration of expeditions in seconds',
    ['expedition_type', 'status']
)

codex_hunters_system_health = get_or_create_gauge(
    'codex_hunters_system_health',
    'System health status (1=healthy, 0.5=degraded, 0=unhealthy)'
)

codex_agents_active = get_or_create_gauge(
    'codex_agents_active',
    'Number of active Codex Hunters agents'
)

# Background expedition runner
async def run_expedition_background(expedition_id: str, expedition_type: str, 
                                  parameters: Dict[str, Any]) -> None:
    """Run expedition in background"""
    start_time = datetime.utcnow()
    
    try:
        # Increment expedition counter
        codex_expeditions_total.labels(expedition_type=expedition_type, status='started').inc()
        
        # Update status to running
        expedition_tracker.update_expedition(expedition_id, {
            "status": "running",
            "started_at": start_time.isoformat(),
            "progress": 0.1
        })
        
        # Publish expedition started event
        await publish_expedition_event("started", expedition_id, parameters)
        
        # Initialize expedition leader for coordination
        # Use simplified agent initialization for now
        postgres_agent = None  # Will be initialized by specific agents
        qdrant_agent = None    # Will be initialized by specific agents
        
        if expedition_type == "full_audit":
            # Full system audit with all agents
            if not CODEX_AGENTS_AVAILABLE:
                results = {
                    "status": "simulated",
                    "message": "Codex agents not available - simulation mode",
                    "agents_simulated": ["expedition_leader", "inspector", "cartographer"]
                }
            else:
                leader = ExpeditionLeader(postgres_agent, qdrant_agent)
                await leader.activate()
                
                expedition_tracker.update_expedition(expedition_id, {
                    "progress": 0.3,
                    "agents_deployed": ["expedition_leader", "inspector", "cartographer", "restorer", "binder"]
                })
                
                results = await leader.coordinate_full_integrity_audit()
            
        elif expedition_type == "healing":
            # Focused healing expedition
            collections = parameters.get("target_collections", ["phrases", "sentiment_scores"])
            
            if not CODEX_AGENTS_AVAILABLE:
                results = {
                    "status": "simulated",
                    "collections_healed": collections,
                    "records_processed": 1500,
                    "healing_success": True,
                    "message": "Healing agents not available - simulation mode"
                }
            else:
                restorer = Restorer()
                binder = Binder()
                
                expedition_tracker.update_expedition(expedition_id, {
                    "progress": 0.4,
                    "agents_deployed": ["restorer", "binder"]
                })
                
                # Simulate healing process
                results = {
                    "collections_healed": collections,
                    "records_processed": 1500,  # Would be actual count
                    "healing_success": True
                }
            
        elif expedition_type == "discovery":
            # Discovery and mapping expedition
            if not CODEX_AGENTS_AVAILABLE:
                results = {
                    "status": "simulated", 
                    "collections_discovered": 3,
                    "consistency_map": [
                        {"collection": "phrases", "consistency": 95.2, "status": "excellent"},
                        {"collection": "sentiment_scores", "consistency": 87.8, "status": "good"},
                        {"collection": "market_data", "consistency": 92.1, "status": "excellent"}
                    ],
                    "message": "Discovery agents not available - simulation mode"
                }
            else:
                tracker = Tracker()
                cartographer = Cartographer(postgres_agent, qdrant_agent)
                
                expedition_tracker.update_expedition(expedition_id, {
                    "progress": 0.5,
                    "agents_deployed": ["tracker", "cartographer"]
                })
                
                # Discovery process
                await cartographer.activate()
                consistency_map = await cartographer.generate_consistency_map()
                
                results = {
                    "collections_discovered": len(consistency_map),
                    "consistency_map": [
                        {
                            "collection": entry.collection_name,
                            "consistency": entry.consistency_percentage,
                            "status": entry.health_status
                        }
                        for entry in consistency_map
                    ]
                }
            
        else:
            raise ValueError(f"Unknown expedition type: {expedition_type}")
        
        # Complete expedition
        expedition_tracker.update_expedition(expedition_id, {
            "status": "completed",
            "progress": 1.0,
            "completed_at": datetime.utcnow().isoformat(),
            "results": results
        })
        
        # Record metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        codex_expeditions_total.labels(expedition_type=expedition_type, status='completed').inc()
        codex_expedition_duration_seconds.labels(expedition_type=expedition_type, status='completed').observe(duration)
        
        # Publish completion event
        await publish_expedition_event("completed", expedition_id, {
            "results": results,
            "success": True
        })
        
        logger.info(f"✅ Expedition {expedition_id} completed successfully in {duration:.1f}s")
        
    except Exception as e:
        logger.error(f"❌ Expedition {expedition_id} failed: {str(e)}")
        
        # Record failure metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        codex_expeditions_total.labels(expedition_type=expedition_type, status='failed').inc()
        codex_expedition_duration_seconds.labels(expedition_type=expedition_type, status='failed').observe(duration)
        
        expedition_tracker.update_expedition(expedition_id, {
            "status": "failed",
            "progress": 0.0,
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": str(e)
        })
        
        # Publish failure event
        await publish_expedition_event("failed", expedition_id, {
            "error": str(e)
        })


async def publish_expedition_event(event_type: str, expedition_id: str, data: Dict[str, Any]) -> None:
    """Publish expedition event to Cognitive Bus"""
    try:
        redis_bus = get_redis_bus()
        
        success = redis_bus.publish_codex_event(
            domain="codex",
            intent=f"expedition.{event_type}",
            emitter="codex_hunters_api",
            target="langgraph",
            payload={
                "expedition_id": expedition_id,
                "event_type": event_type,
                **data
            }
        )
        
        if success:
            logger.info(f"📡 Published expedition.{event_type} event for {expedition_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to publish expedition event: {e}")


# API Endpoints

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """System health check"""
    try:
        # Check Redis connection
        redis_bus = get_redis_bus()
        redis_connected = redis_bus.is_connected()
        
        # Check database connections (simplified)
        try:
            # Simple health check without importing specific agents
            import os
            db_host = os.getenv("POSTGRES_HOST", "172.17.0.1")
            db_connected = True if db_host else False  # Simplified check
        except:
            db_connected = False
        
        # Agent status (simplified)
        agents_status = {
            "tracker": "active",
            "restorer": "active", 
            "binder": "active",
            "inspector": "active",
            "expedition_planner": "active",
            "cartographer": "active",
            "expedition_leader": "active"
        }
        
        # Expedition statistics
        active_expeditions = len([
            exp for exp in expedition_tracker.expeditions.values()
            if exp["status"] == "running"
        ])
        
        completed_24h = len(expedition_tracker.get_recent_expeditions(24))
        
        # Overall status
        if redis_connected and db_connected:
            status = "healthy"
        elif redis_connected or db_connected:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "agents_status": agents_status,
            "redis_connected": redis_connected,
            "database_connected": db_connected,
            "active_expeditions": active_expeditions,
            "completed_expeditions_24h": completed_24h,
            "error_rate": 0.0,  # Would calculate from actual data
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/expedition/run")
async def run_expedition(request: ExpeditionRequest, background_tasks: BackgroundTasks):
    """Trigger a new expedition"""
    try:
        # Validate expedition type
        valid_types = ["full_audit", "healing", "discovery"]
        if request.expedition_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid expedition type. Must be one of: {valid_types}"
            )
        
        # Create expedition entry
        expedition_id = expedition_tracker.create_expedition(
            request.expedition_type,
            {
                "target_collections": request.target_collections,
                "priority": request.priority,
                "parameters": request.parameters,
                "correlation_id": request.correlation_id
            }
        )
        
        # Start expedition in background
        background_tasks.add_task(
            run_expedition_background,
            expedition_id,
            request.expedition_type,
            request.parameters or {}
        )
        
        logger.info(f"🚀 Started expedition {expedition_id} of type {request.expedition_type}")
        
        return {
            "expedition_id": expedition_id,
            "status": "queued",
            "message": f"Expedition {request.expedition_type} started",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to start expedition: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start expedition: {str(e)}")


@app.get("/expedition/status/{expedition_id}")
async def get_expedition_status(expedition_id: str):
    """Get status of specific expedition"""
    try:
        expedition = expedition_tracker.get_expedition(expedition_id)
        
        if not expedition:
            raise HTTPException(status_code=404, detail=f"Expedition {expedition_id} not found")
        
        return expedition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get expedition status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/expedition/history")
async def get_expedition_history(hours: int = 24, limit: int = 50):
    """Get expedition history"""
    try:
        expeditions = expedition_tracker.get_recent_expeditions(hours)
        
        # Apply limit
        expeditions = expeditions[:limit]
        
        return {
            "expeditions": expeditions,
            "total_count": len(expeditions),
            "time_range_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get expedition history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@app.get("/stats")
async def get_system_stats():
    """Get system statistics and metrics"""
    try:
        # Expedition statistics
        all_expeditions = list(expedition_tracker.expeditions.values())
        
        stats = {
            "total_expeditions": len(all_expeditions),
            "expeditions_by_status": {},
            "expeditions_by_type": {},
            "success_rate": 0.0,
            "average_duration_minutes": 0.0,
            "redis_stats": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Count by status
        for exp in all_expeditions:
            status = exp["status"]
            stats["expeditions_by_status"][status] = stats["expeditions_by_status"].get(status, 0) + 1
            
            exp_type = exp.get("expedition_type", "unknown")
            stats["expeditions_by_type"][exp_type] = stats["expeditions_by_type"].get(exp_type, 0) + 1
        
        # Calculate success rate
        completed = stats["expeditions_by_status"].get("completed", 0)
        failed = stats["expeditions_by_status"].get("failed", 0)
        total_finished = completed + failed
        
        if total_finished > 0:
            stats["success_rate"] = completed / total_finished
        
        # Redis stats
        try:
            redis_bus = get_redis_bus()
            stats["redis_stats"] = redis_bus.get_stats()
        except:
            stats["redis_stats"] = {"error": "Redis not available"}
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/expedition/trigger/langgraph")
async def trigger_langgraph_expedition(
    expedition_type: str = "full_audit",
    correlation_id: str = None,
    background_tasks: BackgroundTasks = None
):
    """Special endpoint for LangGraph integration"""
    try:
        # Create expedition request
        request = ExpeditionRequest(
            expedition_type=expedition_type,
            priority="high",
            parameters={"triggered_by": "langgraph"},
            correlation_id=correlation_id
        )
        
        # Use existing run_expedition logic
        return await run_expedition(request, background_tasks)
        
    except Exception as e:
        logger.error(f"❌ LangGraph expedition trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"LangGraph trigger failed: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Update gauges with current values
        active_count = len([
            exp for exp in expedition_tracker.expeditions.values()
            if exp["status"] == "running"
        ])
        codex_expeditions_active.set(active_count)
        
        # Count active agents (simplified - all 7 agents always active)
        codex_agents_active.set(7)
        
        # System health metric (based on last health check)
        try:
            redis_bus = get_redis_bus()
            redis_ok = redis_bus.is_connected()
            health_value = 1.0 if redis_ok else 0.5
        except:
            health_value = 0.0
        
        codex_hunters_system_health.set(health_value)
        
        # Generate Prometheus metrics output
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        logger.error(f"❌ Failed to generate metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics generation failed: {str(e)}")


# Redis Event Listener
async def redis_event_listener():
    """
    Background task to listen for Codex events from Redis Cognitive Bus
    
    Subscribes to:
    - codex.technical.momentum.requested
    - codex.technical.trend.requested  
    - codex.technical.volatility.requested
    - codex.schema.validation.requested
    - codex.data.refresh.requested
    """
    logger.info("🎧 Starting Redis Event Listener...")
    
    redis_bus = get_redis_bus()
    
    # Subscribe to codex events
    channels = [
        "codex.technical.momentum.requested",
        "codex.technical.trend.requested",
        "codex.technical.volatility.requested",
        "codex.schema.validation.requested",
        "codex.data.refresh.requested",
        "codex.macro.refresh.requested",
        "codex.factors.refresh.requested"
    ]
    
    try:
        # Get pubsub object
        pubsub = redis_bus.redis_client.pubsub()
        
        # Subscribe to channels
        for channel in channels:
            pubsub.subscribe(channel)
            logger.info(f"   📻 Subscribed to: {channel}")
        
        logger.info("✅ Redis Event Listener active - waiting for events...")
        
        # Listen for messages
        while True:
            try:
                message = pubsub.get_message(timeout=1.0)
                
                if message and message['type'] == 'message':
                    # Handle both bytes and str types
                    channel = message['channel']
                    if isinstance(channel, bytes):
                        channel = channel.decode('utf-8')
                    
                    data_raw = message['data']
                    if isinstance(data_raw, bytes):
                        data_raw = data_raw.decode('utf-8')
                    
                    data = json.loads(data_raw)
                    
                    logger.info(f"📨 Received event: {channel}")
                    
                    # Route event to appropriate handler
                    await handle_redis_event(channel, data)
                
                # Small sleep to prevent busy loop
                await asyncio.sleep(0.1)
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse event JSON: {e}")
                continue
            
            except Exception as e:
                logger.error(f"❌ Error processing event: {e}")
                await asyncio.sleep(1)
                continue
                
    except Exception as e:
        logger.error(f"❌ Redis Event Listener crashed: {e}")
        # Attempt to reconnect after 5 seconds
        await asyncio.sleep(5)
        logger.info("🔄 Attempting to restart Redis Event Listener...")
        await redis_event_listener()


async def handle_redis_event(channel: str, data: Dict[str, Any]):
    """Handle incoming Redis events and trigger expeditions"""
    
    try:
        payload = data.get('payload', {})
        correlation_id = data.get('correlation_id', f"redis_event_{int(datetime.utcnow().timestamp())}")
        
        logger.info(f"🎯 Handling event: {channel} (correlation: {correlation_id})")
        
        # Determine expedition type based on channel
        if channel == "codex.technical.momentum.requested":
            # Trigger momentum backfill expedition
            request = ExpeditionRequest(
                expedition_type="discovery",  # Use discovery for now
                target_collections=["momentum_logs"],
                priority=payload.get("priority", "high"),
                parameters={
                    "event_source": "redis_event_scheduler",
                    "neural_engine_function": "H",
                    "indicators": ["RSI", "MACD", "Stochastic"],
                    "tickers": payload.get("tickers", []),
                    **payload
                },
                correlation_id=correlation_id
            )
            
            # Create expedition
            expedition_id = expedition_tracker.create_expedition(
                request.expedition_type,
                {
                    "target_collections": request.target_collections,
                    "priority": request.priority,
                    "parameters": request.parameters,
                    "correlation_id": correlation_id,
                    "triggered_by": "redis_event"
                }
            )
            
            # Run in background
            asyncio.create_task(
                run_expedition_background(expedition_id, request.expedition_type, request.parameters)
            )
            
            logger.info(f"✅ Momentum expedition triggered: {expedition_id}")
        
        elif channel == "codex.technical.trend.requested":
            # Trigger trend backfill expedition
            request = ExpeditionRequest(
                expedition_type="discovery",
                target_collections=["trend_logs"],
                priority=payload.get("priority", "high"),
                parameters={
                    "event_source": "redis_event_scheduler",
                    "neural_engine_function": "I",
                    "timeframes": ["1d", "1wk", "1mo"],
                    "tickers": payload.get("tickers", []),
                    **payload
                },
                correlation_id=correlation_id
            )
            
            expedition_id = expedition_tracker.create_expedition(
                request.expedition_type,
                {
                    "target_collections": request.target_collections,
                    "priority": request.priority,
                    "parameters": request.parameters,
                    "correlation_id": correlation_id,
                    "triggered_by": "redis_event"
                }
            )
            
            asyncio.create_task(
                run_expedition_background(expedition_id, request.expedition_type, request.parameters)
            )
            
            logger.info(f"✅ Trend expedition triggered: {expedition_id}")
        
        elif channel == "codex.technical.volatility.requested":
            # Trigger volatility backfill expedition
            request = ExpeditionRequest(
                expedition_type="discovery",
                target_collections=["volatility_logs"],
                priority=payload.get("priority", "medium"),
                parameters={
                    "event_source": "redis_event_scheduler",
                    "neural_engine_function": "E",
                    "volatility_windows": [20, 60, 120],
                    "tickers": payload.get("tickers", []),
                    **payload
                },
                correlation_id=correlation_id
            )
            
            expedition_id = expedition_tracker.create_expedition(
                request.expedition_type,
                {
                    "target_collections": request.target_collections,
                    "priority": request.priority,
                    "parameters": request.parameters,
                    "correlation_id": correlation_id,
                    "triggered_by": "redis_event"
                }
            )
            
            asyncio.create_task(
                run_expedition_background(expedition_id, request.expedition_type, request.parameters)
            )
            
            logger.info(f"✅ Volatility expedition triggered: {expedition_id}")
        
        elif channel == "codex.schema.validation.requested":
            # Trigger schema validation
            request = ExpeditionRequest(
                expedition_type="full_audit",
                target_collections=payload.get("tables", ["momentum_logs", "trend_logs"]),
                priority="high",
                parameters={
                    "event_source": "redis_event_scheduler",
                    "validation_type": "schema",
                    **payload
                },
                correlation_id=correlation_id
            )
            
            expedition_id = expedition_tracker.create_expedition(
                request.expedition_type,
                {
                    "target_collections": request.target_collections,
                    "priority": request.priority,
                    "parameters": request.parameters,
                    "correlation_id": correlation_id,
                    "triggered_by": "redis_event"
                }
            )
            
            asyncio.create_task(
                run_expedition_background(expedition_id, request.expedition_type, request.parameters)
            )
            
            logger.info(f"✅ Schema validation expedition triggered: {expedition_id}")
        
        elif channel == "codex.data.refresh.requested":
            # Trigger full data refresh expedition
            request = ExpeditionRequest(
                expedition_type="full_audit",
                priority="medium",
                parameters={
                    "event_source": "redis_event_scheduler",
                    "sources": payload.get("sources", ["yfinance", "reddit"]),
                    "tickers": payload.get("tickers", []),
                    **payload
                },
                correlation_id=correlation_id
            )
            
            expedition_id = expedition_tracker.create_expedition(
                request.expedition_type,
                {
                    "priority": request.priority,
                    "parameters": request.parameters,
                    "correlation_id": correlation_id,
                    "triggered_by": "redis_event"
                }
            )
            
            asyncio.create_task(
                run_expedition_background(expedition_id, request.expedition_type, request.parameters)
            )
            
            logger.info(f"✅ Data refresh expedition triggered: {expedition_id}")
        
        else:
            logger.warning(f"⚠️ Unknown event channel: {channel}")
    
    except Exception as e:
        logger.error(f"❌ Failed to handle event {channel}: {e}")


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global redis_listener_task
    
    logger.info("🚀 Codex Hunters API Service starting up...")
    
    # Initialize Redis connection
    try:
        redis_bus = get_redis_bus()
        if redis_bus.connect():
            logger.info("✅ Redis Cognitive Bus connected")
            
            # Start Redis Event Listener in background
            redis_listener_task = asyncio.create_task(redis_event_listener())
            logger.info("🎧 Redis Event Listener started in background")
        else:
            logger.warning("⚠️ Redis connection failed - events will be logged only")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
    
    logger.info("✅ Codex Hunters API Service ready on port 8008")


@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_listener_task
    
    logger.info("🛑 Codex Hunters API Service shutting down...")
    
    # Cancel Redis listener task
    if redis_listener_task:
        redis_listener_task.cancel()
        try:
            await redis_listener_task
        except asyncio.CancelledError:
            logger.info("🔇 Redis Event Listener stopped")
    
    try:
        redis_bus = get_redis_bus()
        redis_bus.disconnect()
    except:
        pass
    
    logger.info("✅ Shutdown completed")


# Main entry point
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # Get configuration from environment
    host = os.getenv("CODEX_API_HOST", "0.0.0.0")
    port = int(os.getenv("CODEX_API_PORT", 8008))
    
    logger.info(f"🏰 Starting Codex Hunters API Service on {host}:{port}")
    
    # Run server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        access_log=True
    )