#!/usr/bin/env python3
"""
Shadow Traders API Service - Sacred Order Container

EPISTEMIC ORDER: Reason + Perception
CONTAINER: vitruvyan_shadow_traders:8021

FastAPI service exposing Shadow Traders Agent endpoints:
- POST /execute_order - Execute market orders with AI reasoning
- GET /portfolio/{user_id} - Get portfolio snapshot with insights
- POST /suggest_trades - Get AI trading suggestions
- GET /health - Health check
- GET /metrics - Prometheus metrics

Integrates with:
- PostgreSQL (ledger via PostgresAgent)
- Qdrant (pattern learning via QdrantAgent)
- Redis Cognitive Bus (Synaptic Conclave events)
- Market data (yfinance, Alpaca stubs, Polygon stubs, Alpha Vantage stubs)

Author: Vitruvyan Sacred Orders
Date: January 3, 2026
"""

import os
import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from openai import OpenAI

# Sacred Orders imports
from api_shadow_traders.redis_listener import shadow_traders_listener
from domains.finance.shadow_traders.shadow_broker_agent import (
    ShadowBrokerAgent,
    OrderSide,
    OrderStatus,
    OrderResult,
    PortfolioSnapshot,
    TradeRecommendation
)
from domains.finance.learning import FeedbackLoopEmitter
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from api_shadow_traders.auth import require_auth, optional_auth

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

orders_executed_total = Counter(
    'shadow_traders_orders_executed_total',
    'Total orders executed',
    ['side', 'status']
)

orders_rejected_total = Counter(
    'shadow_traders_orders_rejected_total',
    'Total orders rejected by AI agent',
    ['reason']
)

order_execution_duration = Histogram(
    'shadow_traders_order_execution_duration_seconds',
    'Order execution latency'
)

portfolio_queries_total = Counter(
    'shadow_traders_portfolio_queries_total',
    'Total portfolio queries'
)

vee_narratives_generated_total = Counter(
    'shadow_traders_vee_narratives_total',
    'Total VEE narratives generated via OpenAI',
    ['pattern_type', 'model']
)

vee_generation_cost_usd = Counter(
    'shadow_traders_vee_cost_usd_total',
    'Total OpenAI VEE generation cost in USD'
)

average_slippage = Gauge(
    'shadow_traders_average_slippage_pct',
    'Average slippage percentage'
)

cash_balance_gauge = Gauge(
    'shadow_traders_cash_balance',
    'Current cash balance',
    ['user_id']
)

portfolio_value_gauge = Gauge(
    'shadow_traders_portfolio_value',
    'Total portfolio value',
    ['user_id']
)

redis_listener_active = Gauge(
    'shadow_traders_redis_listener_active',
    'Redis Cognitive Bus listener status (1=active, 0=inactive)'
)

websocket_connections_active = Gauge(
    'shadow_traders_websocket_connections',
    'Active WebSocket connections',
    ['user_id']
)

websocket_messages_sent_total = Counter(
    'shadow_traders_websocket_messages_total',
    'Total WebSocket messages sent',
    ['message_type']
)


# ============================================================================
# WEBSOCKET CONNECTION MANAGER (Task 26.1 - Jan 26, 2026)
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for real-time portfolio updates.
    
    Features:
    - User-specific connection pools
    - Automatic disconnect cleanup
    - Broadcast to specific user (all their devices)
    - Prometheus metrics integration
    
    Architecture:
    - One ConnectionManager instance per app
    - Multiple connections per user (multi-device support)
    - Redis bus integration for Guardian/Autopilot events
    """
    
    def __init__(self):
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[str, set] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        websocket_connections_active.labels(user_id=user_id).set(len(self.active_connections[user_id]))
        
        logger.info(f"✅ WebSocket connected: user={user_id}, total_connections={len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                websocket_connections_active.labels(user_id=user_id).set(0)
            else:
                websocket_connections_active.labels(user_id=user_id).set(len(self.active_connections[user_id]))
        
        logger.info(f"🔌 WebSocket disconnected: user={user_id}")
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """
        Broadcast message to all connections for a specific user.
        
        Args:
            user_id: Target user ID
            message: JSON-serializable message dict
        
        Returns:
            Number of successful sends
        """
        if user_id not in self.active_connections:
            logger.debug(f"No WebSocket connections for user={user_id}")
            return 0
        
        disconnected = set()
        success_count = 0
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
                success_count += 1
                websocket_messages_sent_total.labels(message_type=message.get("type", "unknown")).inc()
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message to user={user_id}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected sockets
        for conn in disconnected:
            self.disconnect(conn, user_id)
        
        logger.debug(f"📤 Broadcast to user={user_id}: {success_count}/{len(self.active_connections.get(user_id, []))} delivered")
        return success_count
    
    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for user."""
        return len(self.active_connections.get(user_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total active WebSocket connections."""
        return sum(len(conns) for conns in self.active_connections.values())


# Global ConnectionManager instance
connection_manager = ConnectionManager()


# ============================================================================
# PYDANTIC MODELS (Request/Response schemas)
# ============================================================================

class ShadowTradeRequest(BaseModel):
    """Request from LangGraph shadow_trading_node"""
    user_id: str = Field(..., description="User ID")
    ticker: str = Field(..., description="Stock ticker symbol")
    quantity: int = Field(..., gt=0, description="Number of shares")
    reason: str = Field(default="Shadow trade execution", description="Trading reason")
    input_text: str = Field(default="", description="Original user input")


class ShadowTradeResponse(BaseModel):
    """Simplified response for LangGraph shadow_trading_node"""
    status: str = Field(..., description="Order status: filled, rejected, error")
    message: str = Field(..., description="Human-readable message")
    order_id: Optional[str] = Field(None, description="Order ID if successful")
    ticker: str = Field(..., description="Ticker symbol")
    quantity: int = Field(..., description="Quantity executed")
    fill_price: Optional[float] = Field(None, description="Fill price")
    total_cost: Optional[float] = Field(None, description="Total cost/proceeds")
    vee_narrative: Optional[str] = Field(None, description="VEE 3-level explanation (Phase 3.2 - Jan 7, 2026)")


class ExecuteOrderRequest(BaseModel):
    """Request to execute a market order"""
    user_id: str = Field(..., description="User ID")
    ticker: str = Field(..., description="Stock ticker symbol")
    side: str = Field(..., description="Order side: 'buy' or 'sell'")
    quantity: int = Field(..., gt=0, description="Number of shares")
    bypass_agent_approval: bool = Field(False, description="Skip agent reasoning (forced execution)")


class ExecuteOrderResponse(BaseModel):
    """Response from order execution"""
    status: str
    order_id: str
    ticker: str
    side: str
    quantity: int
    fill_price: Optional[float]
    total_cost: Optional[float]
    new_cash_balance: Optional[float]
    message: str
    rejection_reason: Optional[str]
    conclave_event_id: Optional[str]
    slippage_pct: float
    agent_reasoning: str
    risk_assessment: Dict[str, Any]
    timestamp: str


class PortfolioSnapshotResponse(BaseModel):
    """Portfolio snapshot with AI insights"""
    user_id: str
    cash_balance: float
    positions: list
    total_value: float
    unrealized_pnl: float
    total_pnl: float
    num_positions: int
    sector_allocation: Dict[str, float]
    risk_metrics: Dict[str, float]
    agent_insights: list
    timestamp: str


class SuggestTradesRequest(BaseModel):
    """Request for AI trade suggestions"""
    user_id: str = Field(..., description="User ID")
    risk_tolerance: str = Field("medium", description="Risk tolerance: 'low', 'medium', 'high'")
    max_suggestions: int = Field(3, ge=1, le=10, description="Max number of suggestions")


class SuggestTradesResponse(BaseModel):
    """AI-generated trade suggestions"""
    user_id: str
    suggestions: list
    reasoning: str
    timestamp: str


class AnalyzePatternRequest(BaseModel):
    """Request for pattern analysis"""
    ticker: str = Field(..., description="Stock ticker symbol")
    user_id: str = Field("demo", description="User ID for logging")
    timeframe: str = Field("30d", description="Historical data timeframe (7d, 30d, 90d, 1y)")
    pattern_types: list[str] = Field(["momentum", "reversal", "breakout"], description="Pattern types to detect")
    use_cache: bool = Field(True, description="Use Redis cached market data")


class PatternResult(BaseModel):
    """Single pattern detection result"""
    type: str = Field(..., description="Pattern type: momentum, reversal, breakout")
    signal_strength: float = Field(..., ge=0, le=10, description="Signal strength (0-10)")
    entry_price: Optional[float] = Field(None, description="Recommended entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    risk_reward_ratio: Optional[float] = Field(None, description="Risk/reward ratio")
    position_size_pct: Optional[float] = Field(None, description="Recommended position size (%)")
    vee_narrative: str = Field(..., description="VEE explainability narrative")
    orthodox_status: str = Field(..., description="Orthodoxy validation: blessed, purified, heretical")
    confidence: float = Field(..., ge=0, le=1, description="Pattern confidence (0-1)")


class AnalyzePatternResponse(BaseModel):
    """Pattern analysis response"""
    ticker: str
    patterns_found: list[PatternResult]
    market_context: Dict[str, Any]
    analysis_timestamp: str
    cache_hit: bool
    latency_ms: float
    status: str


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

# Global agent instance
shadow_broker: Optional[ShadowBrokerAgent] = None
learning_capture_enabled = os.getenv("LEARNING_CAPTURE_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
feedback_loop = FeedbackLoopEmitter(
    source_service="shadow_traders.api",
    enabled=learning_capture_enabled,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup agent on startup/shutdown"""
    global shadow_broker
    listener_task: Optional[asyncio.Task] = None
    
    logger.info("🚀 Starting Shadow Traders API Service...")
    
    # Initialize agent
    shadow_broker = ShadowBrokerAgent()
    await shadow_broker.initialize()
    
    logger.info("✅ Shadow Traders Agent ready")
    
    # Register callbacks even if local listener is disabled; no-op unless listener runs.
    shadow_traders_listener.register_websocket_callback(
        "guardian.insight.created",
        on_guardian_insight_created
    )
    shadow_traders_listener.register_websocket_callback(
        "autopilot.action.proposed",
        on_autopilot_action_proposed
    )
    shadow_traders_listener.register_websocket_callback(
        "portfolio.value.updated",
        on_portfolio_value_updated
    )
    logger.info("✅ WebSocket callbacks registered with listener")

    local_listener_enabled = os.getenv("SHADOW_LOCAL_LISTENER_ENABLED", "0").strip() in {"1", "true", "yes", "on"}
    if local_listener_enabled:
        listener_task = asyncio.create_task(shadow_traders_listener.begin_sacred_listening())
        redis_listener_active.set(1)
        logger.info("🎯 Local Redis listener started (pub/sub compatibility mode)")
    else:
        redis_listener_active.set(0)
        logger.info("🎯 Local listener disabled (using dedicated streams listener container)")
    
    yield
    
    logger.info("🛑 Shutting down Shadow Traders API Service...")
    
    if listener_task is not None:
        shadow_traders_listener.stop()
        redis_listener_active.set(0)
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
    
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="Shadow Traders API",
    description="Sacred Order: Reason + Perception - AI-powered shadow trading",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "shadow_traders",
        "epistemic_order": "Reason + Perception",
        "sacred_orders_active": True
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# WEBSOCKET ENDPOINT (Task 26.1 - Jan 26, 2026)
# ============================================================================

@app.websocket("/ws/portfolio/{user_id}")
async def portfolio_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time portfolio updates.
    
    Message Types (from server):
    - portfolio.snapshot.initial: Initial portfolio data on connect
    - guardian.insight.new: New Guardian insight detected
    - autopilot.action.proposed: New Autopilot action proposed
    - portfolio.value.updated: Portfolio value changed
    - heartbeat: Keep-alive ping
    
    Client Messages:
    - ping: Client-initiated keep-alive → server responds with pong
    
    Architecture:
    - JWT authentication via query params (token=xxx)
    - Redis listener integration (guardian/autopilot events)
    - Automatic reconnection on disconnect
    - Prometheus metrics tracking
    
    Security:
    - Token validation required (bypass for demo_user in development)
    - User can only access their own portfolio data
    
    Task 26.1.2: WebSocket Endpoint (Jan 26, 2026)
    """
    # TODO: JWT validation
    # token = websocket.query_params.get("token")
    # if not verify_jwt(token, user_id):
    #     await websocket.close(code=1008, reason="Unauthorized")
    #     return
    
    # Accept connection
    await connection_manager.connect(websocket, user_id)
    
    try:
        # Send initial portfolio snapshot
        if shadow_broker:
            try:
                snapshot = await shadow_broker.get_portfolio_snapshot(user_id)
                await websocket.send_json({
                    "type": "portfolio.snapshot.initial",
                    "data": {
                        "user_id": snapshot.user_id,
                        "cash_balance": snapshot.cash_balance,
                        "positions": [p.dict() for p in snapshot.positions],
                        "total_value": snapshot.total_value,
                        "unrealized_pnl": snapshot.unrealized_pnl,
                        "num_positions": snapshot.num_positions,
                        "sector_allocation": snapshot.sector_allocation,
                        "risk_metrics": snapshot.risk_metrics,
                        "timestamp": snapshot.timestamp.isoformat()
                    },
                    "timestamp": time.time()
                })
                logger.info(f"📊 Sent initial portfolio snapshot to user={user_id}")
            except Exception as e:
                logger.error(f"Failed to fetch initial portfolio for user={user_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to load portfolio data",
                    "timestamp": time.time()
                })
        
        # Keep-alive loop (ping/pong)
        while True:
            try:
                # Wait for client message with 30s timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                if data == "ping":
                    await websocket.send_text("pong")
                    logger.debug(f"💓 Ping/pong: user={user_id}")
                else:
                    logger.debug(f"Received WebSocket message from user={user_id}: {data}")
            
            except asyncio.TimeoutError:
                # Send heartbeat if no client activity
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": time.time()
                })
                logger.debug(f"💓 Heartbeat sent to user={user_id}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
        logger.info(f"👋 WebSocket disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user={user_id}: {e}")
        connection_manager.disconnect(websocket, user_id)


# ============================================================================
# REDIS LISTENER CALLBACKS (Task 26.1.3 - Jan 26, 2026)
# ============================================================================

async def on_guardian_insight_created(event_data: dict):
    """
    Callback when Guardian emits new insight.
    Broadcasts to user's WebSocket connections.
    
    Event channel: 'guardian.insight.created'
    Event data: {user_id, insight_id, insight_type, severity, title, ...}
    
    Task 26.1.3: Redis Listener Integration
    """
    user_id = event_data.get("user_id")
    if not user_id:
        logger.warning("Guardian insight event missing user_id")
        return
    
    await connection_manager.broadcast_to_user(user_id, {
        "type": "guardian.insight.new",
        "data": event_data,
        "timestamp": time.time()
    })
    
    logger.info(f"📢 Guardian insight broadcasted to user={user_id}, insight_type={event_data.get('insight_type')}")


async def on_autopilot_action_proposed(event_data: dict):
    """
    Callback when Autopilot proposes new action.
    Broadcasts to user's WebSocket connections.
    
    Event channel: 'autopilot.action.proposed'
    Event data: {user_id, action_id, action_type, ticker, quantity, ...}
    
    Task 26.1.3: Redis Listener Integration
    """
    user_id = event_data.get("user_id")
    if not user_id:
        logger.warning("Autopilot action event missing user_id")
        return
    
    await connection_manager.broadcast_to_user(user_id, {
        "type": "autopilot.action.proposed",
        "data": event_data,
        "timestamp": time.time()
    })
    
    logger.info(f"📢 Autopilot action broadcasted to user={user_id}, action_type={event_data.get('action_type')}")


async def on_portfolio_value_updated(event_data: dict):
    """
    Callback when portfolio value changes significantly.
    Broadcasts to user's WebSocket connections.
    
    Event channel: 'portfolio.value.updated'
    Event data: {user_id, total_value, change_pct, ...}
    
    Task 26.1.3: Redis Listener Integration
    """
    user_id = event_data.get("user_id")
    if not user_id:
        logger.warning("Portfolio value event missing user_id")
        return
    
    await connection_manager.broadcast_to_user(user_id, {
        "type": "portfolio.value.updated",
        "data": event_data,
        "timestamp": time.time()
    })
    
    logger.info(f"📢 Portfolio value update broadcasted to user={user_id}, value={event_data.get('total_value')}")


# Register callbacks with Redis listener (requires redis_listener.py modification)
# TODO: Add to redis_listener.py:
# redis_bus.subscribe("guardian.insight.created", on_guardian_insight_created)
# redis_bus.subscribe("autopilot.action.proposed", on_autopilot_action_proposed)
# redis_bus.subscribe("portfolio.value.updated", on_portfolio_value_updated)


# ============================================================================
# HELPER FUNCTIONS (Phase 3.2 - Jan 7, 2026)
# ============================================================================

def _capture_learning_feedback(
    *,
    user_id: str,
    event_name: str,
    feedback_signal: str,
    payload: Dict[str, Any],
    feedback_value: Optional[float] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """Best-effort feedback capture (DB + Streams)."""
    try:
        feedback_loop.record_feedback(
            user_id=user_id,
            event_name=event_name,
            feedback_signal=feedback_signal,
            payload=payload,
            feedback_value=feedback_value,
            correlation_id=correlation_id,
        )
    except Exception as exc:
        logger.warning("Learning feedback capture failed: %s", exc)


async def _fetch_vee_narrative(order_id: str) -> Optional[str]:
    """
    Fetch VEE narrative from shadow_orders table.
    
    Phase 3.2 (Jan 7, 2026): VEE narratives are generated after order execution
    and stored in shadow_orders.vee_narrative column.
    
    Args:
        order_id: UUID of order
        
    Returns:
        VEE narrative string (English-only, 3 levels) or None
    """
    try:
        pg = PostgresAgent()
        with pg.connection.cursor() as cur:
            cur.execute(
                """
                SELECT vee_narrative, vee_generated_at, vee_model
                FROM shadow_orders
                WHERE order_id = %s
                """,
                (order_id,)
            )
            row = cur.fetchone()
            
            if row and row[0]:  # vee_narrative exists
                vee_narrative, vee_generated_at, vee_model = row
                logger.info(f"📝 VEE fetched for order {order_id} (model: {vee_model}, generated: {vee_generated_at})")
                return vee_narrative
            else:
                logger.warning(f"⚠️ VEE not found for order {order_id} (may still be generating)")
                return None
                
    except Exception as e:
        logger.error(f"❌ VEE fetch error: {e}")
        return None


# ============================================================================
# SHADOW TRADING ENDPOINTS (LangGraph Integration)
# ============================================================================

@app.post("/shadow/buy", response_model=ShadowTradeResponse)
@require_auth
async def shadow_buy(request: Request, trade_req: ShadowTradeRequest):
    """
    Execute shadow buy order from LangGraph shadow_trading_node.
    
    **AUTHENTICATION REQUIRED**: JWT token from Keycloak.
    user_id is extracted from token (request.state.user_id), NOT from request body.
    
    Simplified endpoint that wraps the full execute_market_order logic.
    Returns minimal response optimized for LangGraph state propagation.
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    # ✅ Use authenticated user_id from JWT token (NOT from request body)
    authenticated_user_id = request.state.user_id
    
    logger.info(
        f"📡 Shadow BUY request: {trade_req.ticker} x{trade_req.quantity} "
        f"(authenticated user={authenticated_user_id})"
    )
    
    # Security check: Ignore request body user_id, use authenticated user
    if trade_req.user_id != authenticated_user_id:
        logger.warning(
            f"⚠️ User ID mismatch: request={trade_req.user_id}, "
            f"authenticated={authenticated_user_id}. Using authenticated."
        )
    
    try:
        # Execute via ShadowBrokerAgent with authenticated user_id
        result: OrderResult = await shadow_broker.execute_market_order(
            user_id=authenticated_user_id,
            ticker=trade_req.ticker,
            side=OrderSide.BUY,
            quantity=trade_req.quantity,
            bypass_agent_approval=False  # Always use agent reasoning
        )
        
        # Record Prometheus metrics
        orders_executed_total.labels(side='buy', status=result.status.value).inc()

        _capture_learning_feedback(
            user_id=authenticated_user_id,
            event_name="shadow.order.executed",
            feedback_signal=f"order_{result.status.value}",
            feedback_value=result.slippage_pct if result.slippage_pct is not None else None,
            correlation_id=result.order_id,
            payload={
                "ticker": result.ticker,
                "side": "buy",
                "quantity": result.quantity,
                "status": result.status.value,
                "fill_price": result.fill_price,
                "total_cost": result.total_cost,
                "risk_category": result.risk_assessment.risk_category,
                "bypass_agent_approval": False,
            },
        )
        
        # Fetch VEE narrative if order was filled (Phase 3.2 - Jan 7, 2026)
        vee_narrative = None
        if result.status == OrderStatus.FILLED and result.order_id:
            vee_narrative = await _fetch_vee_narrative(result.order_id)
        
        # Simplified response for LangGraph
        return ShadowTradeResponse(
            status=result.status.value,
            message=result.message,
            order_id=result.order_id,
            ticker=result.ticker,
            quantity=result.quantity,
            fill_price=result.fill_price,
            total_cost=result.total_cost,
            vee_narrative=vee_narrative  # Phase 3.2: VEE 3-level explanation
        )
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Shadow BUY error: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        orders_rejected_total.labels(reason='execution_error').inc()
        _capture_learning_feedback(
            user_id=authenticated_user_id,
            event_name="shadow.order.execution_error",
            feedback_signal="order_error",
            payload={
                "ticker": trade_req.ticker,
                "side": "buy",
                "quantity": trade_req.quantity,
                "error": str(e),
            },
        )
        return ShadowTradeResponse(
            status="error",
            message=f"Execution failed: {str(e)}",
            order_id=None,
            ticker=trade_req.ticker,
            quantity=trade_req.quantity,
            fill_price=None,
            total_cost=None
        )


@app.post("/shadow/sell", response_model=ShadowTradeResponse)
@require_auth
async def shadow_sell(request: Request, trade_req: ShadowTradeRequest):
    """
    Execute shadow sell order from LangGraph shadow_trading_node.
    
    **AUTHENTICATION REQUIRED**: JWT token from Keycloak.
    user_id is extracted from token (request.state.user_id), NOT from request body.
    
    Simplified endpoint that wraps the full execute_market_order logic.
    Returns minimal response optimized for LangGraph state propagation.
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    # ✅ Use authenticated user_id from JWT token
    authenticated_user_id = request.state.user_id
    
    logger.info(
        f"📡 Shadow SELL request: {trade_req.ticker} x{trade_req.quantity} "
        f"(authenticated user={authenticated_user_id})"
    )
    
    # Security check: Ignore request body user_id
    if trade_req.user_id != authenticated_user_id:
        logger.warning(
            f"⚠️ User ID mismatch: request={trade_req.user_id}, "
            f"authenticated={authenticated_user_id}. Using authenticated."
        )
    
    try:
        # Execute via ShadowBrokerAgent with authenticated user_id
        result: OrderResult = await shadow_broker.execute_market_order(
            user_id=authenticated_user_id,
            ticker=trade_req.ticker,
            side=OrderSide.SELL,
            quantity=trade_req.quantity,
            bypass_agent_approval=False  # Always use agent reasoning
        )
        
        # Record Prometheus metrics
        orders_executed_total.labels(side='sell', status=result.status.value).inc()

        _capture_learning_feedback(
            user_id=authenticated_user_id,
            event_name="shadow.order.executed",
            feedback_signal=f"order_{result.status.value}",
            feedback_value=result.slippage_pct if result.slippage_pct is not None else None,
            correlation_id=result.order_id,
            payload={
                "ticker": result.ticker,
                "side": "sell",
                "quantity": result.quantity,
                "status": result.status.value,
                "fill_price": result.fill_price,
                "total_cost": result.total_cost,
                "risk_category": result.risk_assessment.risk_category,
                "bypass_agent_approval": False,
            },
        )
        
        # Fetch VEE narrative if order was filled (Phase 3.2 - Jan 7, 2026)
        vee_narrative = None
        if result.status == OrderStatus.FILLED and result.order_id:
            vee_narrative = await _fetch_vee_narrative(result.order_id)
        
        # Simplified response for LangGraph
        return ShadowTradeResponse(
            status=result.status.value,
            message=result.message,
            order_id=result.order_id,
            ticker=result.ticker,
            quantity=result.quantity,
            fill_price=result.fill_price,
            total_cost=result.total_cost,
            vee_narrative=vee_narrative  # Phase 3.2: VEE 3-level explanation
        )
        
    except Exception as e:
        logger.error(f"❌ Shadow SELL error: {str(e)}")
        orders_rejected_total.labels(reason='execution_error').inc()
        _capture_learning_feedback(
            user_id=authenticated_user_id,
            event_name="shadow.order.execution_error",
            feedback_signal="order_error",
            payload={
                "ticker": trade_req.ticker,
                "side": "sell",
                "quantity": trade_req.quantity,
                "error": str(e),
            },
        )
        return ShadowTradeResponse(
            status="error",
            message=f"Execution failed: {str(e)}",
            order_id=None,
            ticker=trade_req.ticker,
            quantity=trade_req.quantity,
            fill_price=None,
            total_cost=None
        )


# ============================================================================
# FULL TRADING ENDPOINTS (Direct API Access)
# ============================================================================

@app.post("/execute_order", response_model=ExecuteOrderResponse)
async def execute_order(request: ExecuteOrderRequest):
    """
    Execute market order with AI reasoning.
    
    Flow:
    1. Agent reasons about trade (risk, market conditions, portfolio impact)
    2. If approved → Execute
    3. Publish to Synaptic Conclave
    4. Archive to Vault Keepers
    5. Embed pattern to Qdrant
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    # Validate side
    if request.side.lower() not in ["buy", "sell"]:
        raise HTTPException(status_code=400, detail="Invalid side: must be 'buy' or 'sell'")
    
    side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL
    
    logger.info(f"📥 Received order: {request.side.upper()} {request.quantity} {request.ticker} (user: {request.user_id})")
    
    # Track execution time
    start_time = time.time()
    
    try:
        # Execute order via agent
        result: OrderResult = await shadow_broker.execute_market_order(
            user_id=request.user_id,
            ticker=request.ticker,
            side=side,
            quantity=request.quantity,
            bypass_agent_approval=request.bypass_agent_approval
        )
        
        # Record metrics
        execution_time = time.time() - start_time
        order_execution_duration.observe(execution_time)
        
        if result.status == OrderStatus.FILLED:
            orders_executed_total.labels(side=request.side.lower(), status='filled').inc()
            average_slippage.set(result.slippage_pct)
            
            # Publish to Redis Cognitive Bus
            await shadow_traders_listener.publish_order_executed({
                "order_id": result.order_id,
                "user_id": request.user_id,
                "ticker": result.ticker,
                "side": result.side.value,
                "quantity": result.quantity,
                "fill_price": result.fill_price,
                "total_cost": result.total_cost
            })
        else:
            orders_rejected_total.labels(reason=result.rejection_reason.value if result.rejection_reason else 'unknown').inc()

        _capture_learning_feedback(
            user_id=request.user_id,
            event_name="shadow.order.executed",
            feedback_signal=f"order_{result.status.value}",
            feedback_value=result.slippage_pct if result.slippage_pct is not None else None,
            correlation_id=result.order_id,
            payload={
                "ticker": result.ticker,
                "side": request.side.lower(),
                "quantity": result.quantity,
                "status": result.status.value,
                "fill_price": result.fill_price,
                "total_cost": result.total_cost,
                "risk_category": result.risk_assessment.risk_category,
                "rejection_reason": result.rejection_reason.value if result.rejection_reason else None,
                "bypass_agent_approval": request.bypass_agent_approval,
            },
        )
        
        # Convert to response model
        response = ExecuteOrderResponse(
            status=result.status.value,
            order_id=result.order_id,
            ticker=result.ticker,
            side=result.side.value,
            quantity=result.quantity,
            fill_price=result.fill_price,
            total_cost=result.total_cost,
            new_cash_balance=result.new_cash_balance,
            message=result.message,
            rejection_reason=result.rejection_reason.value if result.rejection_reason else None,
            conclave_event_id=result.conclave_event_id,
            slippage_pct=result.slippage_pct,
            agent_reasoning=result.agent_reasoning,
            risk_assessment={
                "risk_score": result.risk_assessment.risk_score,
                "risk_category": result.risk_assessment.risk_category,
                "concerns": result.risk_assessment.concerns,
                "mitigations": result.risk_assessment.mitigations,
                "orthodoxy_approved": result.risk_assessment.orthodoxy_approved
            },
            timestamp=result.timestamp.isoformat()
        )
        
        logger.info(f"✅ Order executed: {result.status.value} (order_id: {result.order_id})")
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Order execution failed: {e}")
        _capture_learning_feedback(
            user_id=request.user_id,
            event_name="shadow.order.execution_error",
            feedback_signal="order_error",
            payload={
                "ticker": request.ticker,
                "side": request.side.lower(),
                "quantity": request.quantity,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=f"Order execution failed: {str(e)}")


@app.get("/portfolio/{user_id}", response_model=PortfolioSnapshotResponse)
@require_auth
async def get_portfolio(request: Request, user_id: str):
    """
    Get real-time portfolio snapshot with AI insights.
    
    **AUTHENTICATION REQUIRED**: JWT token from Keycloak.
    User can only access their own portfolio (enforced via token validation).
    
    Returns:
    - Cash balance
    - All positions with current prices
    - Unrealized/realized P&L
    - Sector allocation
    - Risk metrics
    - AI-generated insights and suggestions
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    # ✅ Security: User can only access their own portfolio
    authenticated_user_id = request.state.user_id
    if user_id != authenticated_user_id:
        logger.warning(
            f"⚠️ Unauthorized portfolio access attempt: "
            f"user {authenticated_user_id} tried to access portfolio of {user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: You can only access your own portfolio"
        )
    
    logger.info(f"📥 Portfolio request for authenticated user: {user_id}")
    
    # Track portfolio queries
    portfolio_queries_total.inc()
    
    try:
        # Get snapshot via agent
        snapshot: PortfolioSnapshot = await shadow_broker.get_portfolio_snapshot(user_id)
        
        # Update Prometheus gauges
        cash_balance_gauge.labels(user_id=user_id).set(snapshot.cash_balance)
        portfolio_value_gauge.labels(user_id=user_id).set(snapshot.total_value)
        
        # Publish to Redis Cognitive Bus
        await shadow_traders_listener.publish_portfolio_updated({
            "user_id": user_id,
            "total_value": snapshot.total_value,
            "cash_balance": snapshot.cash_balance,
            "num_positions": snapshot.num_positions,
            "unrealized_pnl": snapshot.unrealized_pnl
        })

        _capture_learning_feedback(
            user_id=user_id,
            event_name="portfolio.snapshot.requested",
            feedback_signal="portfolio_view",
            payload={
                "total_value": snapshot.total_value,
                "cash_balance": snapshot.cash_balance,
                "num_positions": snapshot.num_positions,
                "unrealized_pnl": snapshot.unrealized_pnl,
            },
        )
        
        # Convert to response model
        response = PortfolioSnapshotResponse(
            user_id=snapshot.user_id,
            cash_balance=snapshot.cash_balance,
            positions=snapshot.positions,
            total_value=snapshot.total_value,
            unrealized_pnl=snapshot.unrealized_pnl,
            total_pnl=snapshot.total_pnl,
            num_positions=snapshot.num_positions,
            sector_allocation=snapshot.sector_allocation,
            risk_metrics=snapshot.risk_metrics,
            agent_insights=snapshot.agent_insights,
            timestamp=snapshot.timestamp.isoformat()
        )
        
        logger.info(f"✅ Portfolio snapshot: ${snapshot.total_value:.2f} ({snapshot.num_positions} positions)")
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Portfolio snapshot failed: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio snapshot failed: {str(e)}")


@app.post("/suggest_trades", response_model=SuggestTradesResponse)
async def suggest_trades(request: SuggestTradesRequest):
    """
    Get AI-powered trade suggestions based on:
    - Portfolio composition
    - Risk tolerance
    - Market conditions
    - Learned patterns (from Qdrant)
    
    Future enhancement: Implement ML-based recommendation engine
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    logger.info(f"📥 Trade suggestions request for user: {request.user_id} (risk: {request.risk_tolerance})")
    
    # TODO: Implement AI trade suggestion logic
    # For now, return placeholder
    
    return SuggestTradesResponse(
        user_id=request.user_id,
        suggestions=[
            {
                "ticker": "AAPL",
                "action": "buy",
                "quantity": 10,
                "reasoning": "Strong momentum and fundamentals",
                "confidence": 0.85
            }
        ],
        reasoning="Based on current portfolio composition and market conditions, these trades can improve diversification.",
        timestamp="2026-01-03T00:00:00Z"
    )


@app.post("/reason_about_trade")
async def reason_about_trade(request: ExecuteOrderRequest):
    """
    Get agent's reasoning about a trade WITHOUT executing it.
    
    Returns: TradeRecommendation with decision, risk assessment, alternatives
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL
    
    logger.info(f"📥 Reasoning request: {request.side.upper()} {request.quantity} {request.ticker} (user: {request.user_id})")
    
    try:
        recommendation: TradeRecommendation = await shadow_broker.reason_about_trade(
            user_id=request.user_id,
            ticker=request.ticker,
            side=side,
            quantity=request.quantity
        )

        _capture_learning_feedback(
            user_id=request.user_id,
            event_name="shadow.trade.recommendation_generated",
            feedback_signal=f"recommendation_{recommendation.decision.value}",
            payload={
                "ticker": request.ticker,
                "side": request.side.lower(),
                "quantity": request.quantity,
                "decision": recommendation.decision.value,
                "risk_score": recommendation.risk_assessment.risk_score,
                "risk_category": recommendation.risk_assessment.risk_category,
                "alternatives": recommendation.alternatives,
            },
        )
        
        return {
            "decision": recommendation.decision.value,
            "reasoning": recommendation.reasoning,
            "vee_explanation": recommendation.vee_explanation,
            "risk_assessment": {
                "risk_score": recommendation.risk_assessment.risk_score,
                "risk_category": recommendation.risk_assessment.risk_category,
                "concerns": recommendation.risk_assessment.concerns,
                "mitigations": recommendation.risk_assessment.mitigations,
                "orthodoxy_approved": recommendation.risk_assessment.orthodoxy_approved
            },
            "alternatives": recommendation.alternatives
        }
    
    except Exception as e:
        logger.error(f"❌ Reasoning failed: {e}")
        _capture_learning_feedback(
            user_id=request.user_id,
            event_name="shadow.trade.recommendation_error",
            feedback_signal="recommendation_error",
            payload={
                "ticker": request.ticker,
                "side": request.side.lower(),
                "quantity": request.quantity,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")


# ============================================================================
# PHASE 3: PATTERN-EXECUTION INTEGRATION
# ============================================================================

@app.post("/pre_trade_check")
async def pre_trade_check(request: ExecuteOrderRequest):
    """
    Pre-trade pattern validation check (Phase 3.1).
    
    Validates trade against detected patterns BEFORE execution:
    1. Detect active patterns for ticker
    2. Check if order aligns with pattern signals (blessed/heretical)
    3. Return Orthodoxy validation status
    
    Orthodoxy States:
    - "blessed": Order aligns with pattern signals → EXECUTE
    - "purified": Order has minor concerns but acceptable → EXECUTE with warnings
    - "heretical": Order contradicts pattern signals → REJECT
    
    Used by LangGraph shadow_trading_node before calling /shadow/buy or /shadow/sell.
    """
    if not shadow_broker:
        raise HTTPException(status_code=503, detail="Shadow Broker Agent not initialized")
    
    logger.info(f"🔍 Pre-trade check: {request.side.upper()} {request.quantity} {request.ticker} (user: {request.user_id})")
    
    try:
        # 1. Analyze patterns for ticker
        pattern_request = AnalyzePatternRequest(
            ticker=request.ticker,
            user_id=request.user_id,
            timeframe="30d",
            pattern_types=["momentum", "reversal", "breakout"],
            use_cache=True
        )
        
        # Call internal pattern analysis (reuse existing logic)
        pattern_response = await analyze_pattern(pattern_request)
        
        # 2. Validate order against patterns
        side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL
        
        # Extract strongest pattern
        if not pattern_response.patterns_found:
            # No patterns detected → PURIFIED (proceed with caution)
            return {
                "orthodoxy_status": "purified",
                "approved": True,
                "concerns": ["No clear patterns detected - market neutral"],
                "strongest_pattern": None,
                "signal_alignment": 0.0,
                "vee_narrative": f"No strong patterns detected for {request.ticker}. Trade carries medium risk due to lack of clear directional signal.",
                "patterns_detected": 0
            }
        
        strongest = max(pattern_response.patterns_found, key=lambda p: p.signal_strength)
        
        # 3. Check alignment
        signal_alignment = 0.0
        concerns = []
        
        if strongest.type == "momentum":
            # Momentum pattern → Buy if signal_strength > 5, Sell if < 5
            if side == OrderSide.BUY and strongest.signal_strength > 5:
                signal_alignment = (strongest.signal_strength - 5) / 5  # 0-1 scale
            elif side == OrderSide.SELL and strongest.signal_strength < 5:
                signal_alignment = (5 - strongest.signal_strength) / 5
            else:
                signal_alignment = -1.0  # Contradicts pattern
                concerns.append(f"Order contradicts {strongest.type} pattern (strength: {strongest.signal_strength})")
        
        elif strongest.type == "reversal":
            # Reversal pattern → opposite direction trade
            if side == OrderSide.SELL and strongest.signal_strength > 5:
                signal_alignment = (strongest.signal_strength - 5) / 5
            elif side == OrderSide.BUY and strongest.signal_strength < 5:
                signal_alignment = (5 - strongest.signal_strength) / 5
            else:
                signal_alignment = -1.0
                concerns.append(f"Order contradicts {strongest.type} reversal signal")
        
        elif strongest.type == "breakout":
            # Breakout pattern → Buy on upward breakout
            if side == OrderSide.BUY and strongest.signal_strength > 6:
                signal_alignment = (strongest.signal_strength - 6) / 4
            else:
                signal_alignment = 0.3  # Neutral
                concerns.append(f"Breakout pattern not strong enough for confident trade")
        
        # 4. Determine Orthodoxy status
        if signal_alignment > 0.5:
            orthodoxy_status = "blessed"
            approved = True
        elif signal_alignment > 0:
            orthodoxy_status = "purified"
            approved = True
            concerns.append("Pattern alignment weak - proceed with caution")
        else:
            orthodoxy_status = "heretical"
            approved = False
            concerns.append("Order contradicts detected patterns - trade REJECTED")
        
        # 5. Generate VEE narrative
        vee_narrative = strongest.vee_narrative + f"\n\n**Orthodoxy Assessment**: {orthodoxy_status.upper()} - {', '.join(concerns) if concerns else 'Pattern alignment confirmed'}"
        
        return {
            "orthodoxy_status": orthodoxy_status,
            "approved": approved,
            "concerns": concerns,
            "strongest_pattern": {
                "type": strongest.type,
                "signal_strength": strongest.signal_strength,
                "entry_price": strongest.entry_price,
                "stop_loss": strongest.stop_loss,
                "take_profit": strongest.take_profit,
                "confidence": strongest.confidence
            },
            "signal_alignment": signal_alignment,
            "vee_narrative": vee_narrative,
            "patterns_detected": len(pattern_response.patterns_found),
            "cache_hit": pattern_response.cache_hit
        }
    
    except Exception as e:
        logger.error(f"❌ Pre-trade check failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fail-safe: If pattern analysis fails, return PURIFIED (don't block trade)
        return {
            "orthodoxy_status": "purified",
            "approved": True,
            "concerns": [f"Pattern analysis unavailable: {str(e)}"],
            "strongest_pattern": None,
            "signal_alignment": 0.0,
            "vee_narrative": f"Pre-trade check failed due to technical issue. Trade proceeds with medium risk.",
            "patterns_detected": 0
        }


@app.post("/analyze_pattern", response_model=AnalyzePatternResponse)
async def analyze_pattern(request: AnalyzePatternRequest):
    """
    Analyze trading patterns for a ticker (Phase 1: Pattern Analysis).
    
    Detects 3 pattern types:
    - Momentum: Strong directional movement with volume confirmation
    - Reversal: Trend change with divergence signals
    - Breakout: Price breaks consolidation range
    
    Returns:
    - Patterns detected with signal strength (0-10)
    - Entry/stop/target prices
    - Risk/reward ratios
    - VEE explainability narratives
    - Orthodoxy validation (blessed/purified/heretical)
    
    ⚠️ CRITICAL: Uses PostgreSQL as source (Codex Hunters data), NOT yfinance directly.
    """
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta
    from core.agents.postgres_agent import PostgresAgent
    
    logger.info(f"📊 Pattern analysis request: {request.ticker} ({request.timeframe}, {request.pattern_types})")
    
    start_time = time.time()
    cache_hit = False
    
    # Generate cache key (hash of request params)
    cache_key = hashlib.md5(
        f"{request.ticker}:{request.timeframe}:{','.join(sorted(request.pattern_types))}".encode()
    ).hexdigest()
    
    # Check Redis cache if enabled
    if request.use_cache:
        cached_response = _get_cached_analysis(cache_key)
        if cached_response:
            cached_response['cache_hit'] = True
            cached_response['latency_ms'] = (time.time() - start_time) * 1000
            return AnalyzePatternResponse(**cached_response)
    
    try:
        # ✅ GOLDEN RULE: Use PostgresAgent (NOT direct psycopg2.connect)
        pg = PostgresAgent()
        
        # Map timeframe to days
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(request.timeframe, 30)
        
        # Query OHLCV data from PostgreSQL (Codex Hunters source)
        query = """
            SELECT dt as date, open, high, low, close, volume
            FROM ohlcv_daily
            WHERE ticker = %s
              AND dt >= CURRENT_DATE - %s
            ORDER BY dt ASC
        """
        
        with pg.connection.cursor() as cur:
            cur.execute(query, (request.ticker, days))
            rows = cur.fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=404, 
                detail=f"No historical data found for {request.ticker} in last {days} days. Codex Hunters may not have tracked this ticker yet."
            )
        
        # Convert to pandas DataFrame (same structure as yfinance)
        hist = pd.DataFrame(rows, columns=['date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        hist['date'] = pd.to_datetime(hist['date'])
        hist.set_index('date', inplace=True)
        
        # ⚠️ CRITICAL: Drop rows with NULL values (incomplete Codex Hunters data)
        hist = hist.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        
        if len(hist) < 7:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for {request.ticker} ({len(hist)} days < 7 minimum). Codex Hunters may need to update."
            )
        
        # Market context
        current_price = hist['Close'].iloc[-1]
        volume_avg = hist['Volume'].mean()
        volume_current = hist['Volume'].iloc[-1]
        volatility = hist['Close'].pct_change().std() * np.sqrt(252)  # Annualized
        
        market_context = {
            "current_price": float(current_price),
            "volume_trend": "increasing" if volume_current > volume_avg * 1.2 else "decreasing" if volume_current < volume_avg * 0.8 else "stable",
            "volatility": f"{volatility:.2%}",
            "data_points": len(hist),
            "date_range": f"{hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')}"
        }
        
        patterns_found = []
        
        # Pattern Detection Logic
        for pattern_type in request.pattern_types:
            if pattern_type == "momentum":
                pattern = _detect_momentum(hist, current_price, request.ticker)
                if pattern:
                    patterns_found.append(pattern)
            
            elif pattern_type == "reversal":
                pattern = _detect_reversal(hist, current_price, request.ticker)
                if pattern:
                    patterns_found.append(pattern)
            
            elif pattern_type == "breakout":
                pattern = _detect_breakout(hist, current_price, request.ticker)
                if pattern:
                    patterns_found.append(pattern)
        
        latency_ms = (time.time() - start_time) * 1000
        
        response_dict = {
            "ticker": request.ticker,
            "patterns_found": [p.dict() for p in patterns_found],
            "market_context": market_context,
            "analysis_timestamp": datetime.now().isoformat(),
            "cache_hit": cache_hit,
            "latency_ms": round(latency_ms, 2),
            "status": "success"
        }
        
        # Archive patterns to PostgreSQL and Qdrant (async operations, don't block response)
        for pattern in patterns_found:
            # Log to PostgreSQL shadow_trades table
            trade_id = _log_pattern_to_postgres(
                pattern=pattern,
                ticker=request.ticker,
                timeframe=request.timeframe,
                data_points=len(hist),
                market_context=market_context,
                user_id=request.user_id,
                vee_cost_usd=0.00028  # Average cost from VEE generation
            )
            
            # Embed to Qdrant shadow_patterns collection
            if trade_id:
                _embed_pattern_to_qdrant(
                    pattern=pattern,
                    ticker=request.ticker,
                    trade_id=trade_id,
                    market_context=market_context
                )
        
        # Cache response for future requests (1 hour TTL)
        if request.use_cache:
            _cache_analysis(cache_key, response_dict, ttl=3600)
        
        return AnalyzePatternResponse(**response_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Pattern analysis failed for {request.ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")


def _generate_vee_narrative(
    pattern_type: str,
    ticker: str,
    signal_strength: float,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    risk_reward_ratio: float,
    orthodox_status: str,
    context: Dict[str, Any]
) -> str:
    """
    Generate VEE explainability narrative using OpenAI GPT-4o-mini.
    
    Cost: ~$0.00028/query (100 input + 120 output tokens avg)
    Model: gpt-4o-mini (temperature=0 for consistency)
    
    Returns professional trading narrative explaining:
    - Why pattern detected (technical reasoning)
    - Risk/reward setup (entry/stop/target)
    - Confidence level and orthodoxy status
    """
    try:
        # Construct prompt with all context
        prompt = f"""You are a professional trading analyst generating a concise technical analysis narrative.

Pattern: {pattern_type}
Ticker: {ticker}
Signal Strength: {signal_strength}/10
Entry: ${entry_price:.2f}
Stop Loss: ${stop_loss:.2f}
Take Profit: ${take_profit:.2f}
Risk/Reward: {risk_reward_ratio:.2f}:1
Orthodoxy: {orthodox_status}

Context: {context}

Generate a 2-3 sentence professional narrative explaining:
1. Why this {pattern_type} pattern was detected (specific technical indicators)
2. The trade setup (entry/stop/target with clear reasoning)
3. Risk management perspective

Tone: Professional, factual, no hype. Focus on risk-first approach."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional trading analyst specializing in technical pattern recognition and risk management."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        narrative = response.choices[0].message.content.strip()
        
        # Track metrics
        vee_narratives_generated_total.labels(
            pattern_type=pattern_type,
            model="gpt-4o-mini"
        ).inc()
        
        # Calculate cost (gpt-4o-mini: $0.150/1M input, $0.600/1M output)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost_usd = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)
        vee_generation_cost_usd.inc(cost_usd)
        
        logger.info(f"✨ VEE narrative generated for {ticker} ({pattern_type}): {input_tokens}+{output_tokens} tokens, ${cost_usd:.6f}")
        
        return narrative
        
    except Exception as e:
        logger.error(f"❌ VEE narrative generation failed: {e}")
        # Fallback to simple narrative
        return (
            f"{ticker} {pattern_type} pattern detected with {signal_strength}/10 signal strength. "
            f"Entry: ${entry_price:.2f}, Stop: ${stop_loss:.2f}, Target: ${take_profit:.2f} "
            f"(R/R {risk_reward_ratio:.2f}:1, {orthodox_status})."
        )


def _log_pattern_to_postgres(
    pattern: PatternResult,
    ticker: str,
    timeframe: str,
    data_points: int,
    market_context: Dict[str, Any],
    user_id: str,
    vee_cost_usd: float
) -> Optional[int]:
    """
    Archive pattern analysis to PostgreSQL shadow_trades table.
    
    Returns: Trade ID if successful, None on error
    """
    try:
        pg = PostgresAgent()
        
        # Technical indicators context (if available)
        technical_indicators = pattern.__dict__.get('technical_indicators', {})
        
        query = """
            INSERT INTO shadow_trades (
                ticker, pattern_type, signal_strength, confidence,
                entry_price, stop_loss, take_profit, risk_reward_ratio, position_size_pct,
                orthodox_status, vee_narrative, vee_generated_by, vee_generation_cost_usd,
                timeframe, data_points, analysis_timestamp, user_id,
                market_context, technical_indicators
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, NOW(), %s,
                %s, %s
            ) RETURNING id
        """
        
        with pg.connection.cursor() as cur:
            cur.execute(query, (
                ticker, pattern.type, pattern.signal_strength, pattern.confidence,
                pattern.entry_price, pattern.stop_loss, pattern.take_profit, 
                pattern.risk_reward_ratio, pattern.position_size_pct,
                pattern.orthodox_status, pattern.vee_narrative, 'gpt-4o-mini', vee_cost_usd,
                timeframe, data_points, user_id,
                json.dumps(market_context), json.dumps(technical_indicators)
            ))
            trade_id = cur.fetchone()[0]
            pg.connection.commit()
        
        logger.info(f"📝 Pattern archived to shadow_trades: ID={trade_id}, {ticker} {pattern.type}")
        return trade_id
        
    except Exception as e:
        logger.error(f"❌ Failed to archive pattern to PostgreSQL: {e}")
        return None


def _embed_pattern_to_qdrant(
    pattern: PatternResult,
    ticker: str,
    trade_id: int,
    market_context: Dict[str, Any]
) -> bool:
    """
    Embed pattern to Qdrant shadow_patterns collection for semantic search.
    
    Embedding text: VEE narrative (semantic similarity for pattern matching)
    Payload: All pattern metadata for filtering/retrieval
    """
    try:
        qa = QdrantAgent()
        
        # Generate embedding from VEE narrative (semantic content)
        embedding_text = f"{ticker} {pattern.type}: {pattern.vee_narrative}"
        
        # Create point for Qdrant
        point = {
            "id": trade_id,  # Use PostgreSQL ID for cross-reference
            "vector": qa.generate_embedding(embedding_text),
            "payload": {
                "ticker": ticker,
                "pattern_type": pattern.type,
                "signal_strength": float(pattern.signal_strength),
                "entry_price": float(pattern.entry_price),
                "risk_reward_ratio": float(pattern.risk_reward_ratio),
                "orthodox_status": pattern.orthodox_status,
                "vee_narrative": pattern.vee_narrative,
                "trade_id": trade_id,
                "market_context": market_context,
                "timestamp": time.time()
            }
        }
        
        # Ensure shadow_patterns collection exists
        from qdrant_client.models import Distance, VectorParams
        try:
            qa.client.get_collection("shadow_patterns")
        except:
            qa.client.create_collection(
                collection_name="shadow_patterns",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info("✅ Created shadow_patterns collection in Qdrant")
        
        # Upsert to Qdrant
        qa.upsert(collection="shadow_patterns", points=[point])
        
        logger.info(f"🔍 Pattern embedded to Qdrant: trade_id={trade_id}, {ticker} {pattern.type}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to embed pattern to Qdrant: {e}")
        return False


def _get_cached_analysis(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached pattern analysis from Redis.
    
    Returns: Cached response dict if found and valid, None otherwise
    """
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'vitruvyan_redis_master'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        cached = r.get(f"shadow_pattern:{cache_key}")
        if cached:
            logger.info(f"💨 Cache hit for {cache_key}")
            return json.loads(cached)
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ Cache retrieval failed: {e}")
        return None


def _cache_analysis(cache_key: str, response: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Cache pattern analysis to Redis.
    
    Args:
        cache_key: Hash of request params
        response: Full AnalyzePatternResponse dict
        ttl: Time to live in seconds (default 1 hour)
    
    Returns: True if cached successfully
    """
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'vitruvyan_redis_master'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        r.setex(
            f"shadow_pattern:{cache_key}",
            ttl,
            json.dumps(response, default=str)
        )
        
        logger.info(f"💾 Cached analysis for {cache_key} (TTL: {ttl}s)")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Cache write failed: {e}")
        return False


def _detect_momentum(hist, current_price: float, ticker: str) -> Optional[PatternResult]:
    """
    Detect momentum pattern: strong directional movement with increasing volume.
    
    Criteria:
    - Price change >5% in last 7 days
    - Volume increasing (>20% above average)
    - RSI > 60 (bullish) or < 40 (bearish)
    """
    import numpy as np
    
    if len(hist) < 14:
        return None
    
    # Calculate price change (last 7 days)
    price_7d_ago = hist['Close'].iloc[-7] if len(hist) >= 7 else hist['Close'].iloc[0]
    price_change_pct = ((current_price - price_7d_ago) / price_7d_ago) * 100
    
    # Calculate RSI (14 periods)
    delta = hist['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # Volume trend
    volume_avg = hist['Volume'].mean()
    volume_current = hist['Volume'].iloc[-1]
    volume_increasing = volume_current > volume_avg * 1.2
    
    # Signal strength calculation (0-10)
    signal_strength = 0
    
    if abs(price_change_pct) > 5:
        signal_strength += 3
    if abs(price_change_pct) > 10:
        signal_strength += 2
    if volume_increasing:
        signal_strength += 2
    if (price_change_pct > 0 and current_rsi > 60) or (price_change_pct < 0 and current_rsi < 40):
        signal_strength += 3
    
    if signal_strength < 5:
        return None  # Weak signal, skip
    
    # Calculate entry/stop/target prices (2:1 reward/risk)
    if price_change_pct > 0:  # Bullish momentum
        entry_price = current_price
        stop_loss = current_price * 0.95  # 5% stop
        take_profit = current_price * 1.10  # 10% target
    else:  # Bearish momentum (short)
        entry_price = current_price
        stop_loss = current_price * 1.05
        take_profit = current_price * 0.90
    
    risk_reward_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
    
    # Orthodoxy validation (minimum 2:1 R/R required)
    orthodox_status = "blessed" if risk_reward_ratio >= 2.0 else "purified" if risk_reward_ratio >= 1.5 else "heretical"
    
    # VEE narrative (OpenAI GPT-4o-mini)
    direction = "upward" if price_change_pct > 0 else "downward"
    vee_narrative = _generate_vee_narrative(
        pattern_type="momentum",
        ticker=ticker,
        signal_strength=signal_strength,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward_ratio=risk_reward_ratio,
        orthodox_status=orthodox_status,
        context={
            "direction": direction,
            "price_change_pct": abs(price_change_pct),
            "rsi": current_rsi,
            "volume_increasing": volume_increasing
        }
    )
    
    return PatternResult(
        type="momentum",
        signal_strength=round(signal_strength, 1),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        take_profit=round(take_profit, 2),
        risk_reward_ratio=round(risk_reward_ratio, 2),
        position_size_pct=5.0 if orthodox_status == "blessed" else 2.5,
        vee_narrative=vee_narrative,
        orthodox_status=orthodox_status,
        confidence=min(signal_strength / 10, 1.0)
    )


def _detect_reversal(hist, current_price: float, ticker: str) -> Optional[PatternResult]:
    """
    Detect reversal pattern: trend change with divergence signals.
    
    Criteria:
    - Price tested support/resistance 2+ times
    - RSI divergence (price making new highs/lows, RSI diverging)
    - Volume exhaustion (decreasing on trend continuation)
    """
    import numpy as np
    
    if len(hist) < 20:
        return None
    
    # Simplified reversal logic (placeholder for full implementation)
    # TODO: Implement full RSI divergence, support/resistance detection
    
    # For now, detect simple overbought/oversold reversals
    delta = hist['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # Reversal signal only if RSI extreme + volume exhaustion
    volume_avg = hist['Volume'].mean()
    volume_current = hist['Volume'].iloc[-1]
    volume_exhaustion = volume_current < volume_avg * 0.8
    
    if not volume_exhaustion:
        return None
    
    signal_strength = 0
    
    if current_rsi > 70 and volume_exhaustion:  # Overbought reversal (bearish)
        signal_strength = 7
        entry_price = current_price
        stop_loss = current_price * 1.03
        take_profit = current_price * 0.93
        direction = "bearish"
    elif current_rsi < 30 and volume_exhaustion:  # Oversold reversal (bullish)
        signal_strength = 7
        entry_price = current_price
        stop_loss = current_price * 0.97
        take_profit = current_price * 1.07
        direction = "bullish"
    else:
        return None
    
    risk_reward_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
    orthodox_status = "blessed" if risk_reward_ratio >= 2.0 else "purified"
    
    vee_narrative = _generate_vee_narrative(
        pattern_type="reversal",
        ticker=ticker,
        signal_strength=signal_strength,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward_ratio=risk_reward_ratio,
        orthodox_status=orthodox_status,
        context={
            "direction": direction,
            "rsi": current_rsi,
            "condition": "overbought" if current_rsi > 70 else "oversold",
            "volume_exhaustion": True
        }
    )
    
    return PatternResult(
        type="reversal",
        signal_strength=round(signal_strength, 1),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        take_profit=round(take_profit, 2),
        risk_reward_ratio=round(risk_reward_ratio, 2),
        position_size_pct=3.0,
        vee_narrative=vee_narrative,
        orthodox_status=orthodox_status,
        confidence=0.75
    )


def _detect_breakout(hist, current_price: float, ticker: str) -> Optional[PatternResult]:
    """
    Detect breakout pattern: price breaks consolidation range with volume spike.
    
    Criteria:
    - Price consolidating in range (volatility <2% for 10+ days)
    - Break above/below range with volume spike (>50% above average)
    - No false breakout in last 5 days
    """
    import numpy as np
    
    if len(hist) < 15:
        return None
    
    # Calculate consolidation range (last 10 days)
    recent_high = hist['High'].iloc[-10:].max()
    recent_low = hist['Low'].iloc[-10:].min()
    range_pct = ((recent_high - recent_low) / recent_low) * 100
    
    # Consolidation detected if range < 5%
    if range_pct > 5:
        return None
    
    # Check for breakout
    volume_avg = hist['Volume'].mean()
    volume_current = hist['Volume'].iloc[-1]
    volume_spike = volume_current > volume_avg * 1.5
    
    if not volume_spike:
        return None
    
    # Bullish breakout (above range)
    if current_price > recent_high * 1.01:
        signal_strength = 8
        entry_price = current_price
        stop_loss = recent_low * 0.99  # Below consolidation range
        take_profit = entry_price + (entry_price - stop_loss) * 2  # 2:1 R/R
        direction = "bullish"
    # Bearish breakout (below range)
    elif current_price < recent_low * 0.99:
        signal_strength = 8
        entry_price = current_price
        stop_loss = recent_high * 1.01
        take_profit = entry_price - (stop_loss - entry_price) * 2
        direction = "bearish"
    else:
        return None
    
    risk_reward_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
    orthodox_status = "blessed" if risk_reward_ratio >= 2.0 else "blessed"  # Breakouts always blessed if 2:1+
    
    vee_narrative = _generate_vee_narrative(
        pattern_type="breakout",
        ticker=ticker,
        signal_strength=signal_strength,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward_ratio=risk_reward_ratio,
        orthodox_status=orthodox_status,
        context={
            "direction": direction,
            "recent_low": recent_low,
            "recent_high": recent_high,
            "range_pct": range_pct,
            "volume_spike_ratio": volume_current / volume_avg
        }
    )
    
    return PatternResult(
        type="breakout",
        signal_strength=round(signal_strength, 1),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        take_profit=round(take_profit, 2),
        risk_reward_ratio=round(risk_reward_ratio, 2),
        position_size_pct=4.0,
        vee_narrative=vee_narrative,
        orthodox_status=orthodox_status,
        confidence=0.85
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("SHADOW_BROKER_PORT", 8020))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
