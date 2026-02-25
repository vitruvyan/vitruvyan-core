"""
Portfolio Architects API Service — FastAPI Application

Epistemic Order: REASON (Portfolio Construction)
Port: 8021

Provides REST API for Portfolio Architect construction services.

Endpoints:
- POST /construct: Construct portfolio for user
- GET /portfolios/{user_id}: Get user's portfolios
- GET /health: Health check
- GET /metrics: Prometheus metrics

Author: Sacred Orders
Created: January 8, 2026
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Import Portfolio Architect agent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domains.finance.portfolio_architects.agents.portfolio_architect_agent import PortfolioArchitectAgent
from domains.finance.learning import FeedbackLoopEmitter
from core.agents.postgres_agent import PostgresAgent

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

learning_capture_enabled = os.getenv("LEARNING_CAPTURE_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
feedback_loop = FeedbackLoopEmitter(
    source_service="portfolio_architects.api",
    enabled=learning_capture_enabled,
)

# Initialize FastAPI app
app = FastAPI(
    title="Portfolio Architects API",
    description="Portfolio Construction & Management Service",
    version="1.0.0"
)

# Prometheus metrics
portfolio_constructions_total = Counter(
    'portfolio_constructions_total',
    'Total portfolio constructions',
    ['status', 'risk_level']
)

portfolio_construction_latency = Histogram(
    'portfolio_construction_duration_seconds',
    'Portfolio construction latency',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

portfolio_tickers_count = Histogram(
    'portfolio_tickers_count',
    'Number of tickers in constructed portfolios',
    buckets=[2, 5, 10, 15, 20, 25, 30]
)

portfolio_diversification_score = Histogram(
    'portfolio_diversification_score',
    'Portfolio diversification scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)


# Request/Response models
class ConstructPortfolioRequest(BaseModel):
    """Request to construct a portfolio."""
    user_id: str = Field(..., description="User identifier")
    risk_tolerance: str = Field("balanced", description="Risk tolerance: conservative, balanced, aggressive")
    available_cash: float = Field(..., description="Total cash available for investment (USD)", gt=0)
    sector_preferences: Optional[List[str]] = Field(None, description="Preferred sectors (optional)")
    blocked_tickers: Optional[List[str]] = Field(None, description="Tickers to exclude")
    is_demo_mode: bool = Field(False, description="Demo mode flag (50K simulated)")


class PortfolioHolding(BaseModel):
    """Single holding in a portfolio."""
    ticker: str
    shares: int
    price: float
    value: float
    weight: float
    sector: str
    composite_z: Optional[float] = None


class PortfolioResponse(BaseModel):
    """Constructed portfolio response."""
    user_id: str
    risk_tolerance: str
    available_cash: float
    total_value: float
    holdings: List[PortfolioHolding]
    num_holdings: int
    diversification_score: float
    concentration_risk: str
    sectors: Dict[str, float]
    construction_time: float
    created_at: str


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


@app.post("/construct", response_model=PortfolioResponse)
async def construct_portfolio(request: ConstructPortfolioRequest):
    """
    Construct a diversified portfolio for user.
    
    Flow:
        1. Initialize Portfolio Architect Agent
        2. Construct portfolio based on risk level and budget
        3. Calculate diversification metrics
        4. Persist to PostgreSQL
        5. Return portfolio details
    
    Args:
        request: ConstructPortfolioRequest with user_id, risk_level, budget
        
    Returns:
        PortfolioResponse with holdings, diversification, sectors
    """
    start_time = time.time()
    
    try:
        logger.info(f"🏗️ Constructing portfolio for user={request.user_id}, risk={request.risk_tolerance}, cash=${request.available_cash:,.2f}")
        
        # Initialize Portfolio Architect
        architect = PortfolioArchitectAgent()
        
        # Construct portfolio
        portfolio_result = architect.construct_portfolio(
            user_id=request.user_id,
            risk_tolerance=request.risk_tolerance,
            available_cash=request.available_cash,
            sector_preferences=request.sector_preferences,
            blocked_tickers=request.blocked_tickers,
            is_demo_mode=request.is_demo_mode
        )
        
        if not portfolio_result or "holdings" not in portfolio_result:
            raise ValueError("Portfolio construction failed: No holdings returned")
        
        # Calculate construction time
        construction_time = time.time() - start_time
        
        # Extract metrics from PortfolioSnapshot object
        holdings = [
            PortfolioHolding(
                ticker=h.ticker,
                shares=h.shares,
                price=h.value / h.shares if h.shares > 0 else 0.0,  # Calculate price from value/shares
                value=h.value,
                weight=h.weight,
                sector=h.sector or "Unknown",
                composite_z=h.composite_z
            )
            for h in portfolio_result.holdings
        ]
        
        num_holdings = len(holdings)
        diversification_score = portfolio_result.risk_metrics.get("diversification_score", 0.0)
        concentration_risk = portfolio_result.risk_metrics.get("concentration_risk", "unknown")
        sectors = portfolio_result.sector_breakdown
        total_value = portfolio_result.total_value
        
        # Record Prometheus metrics
        portfolio_construction_latency.observe(construction_time)
        portfolio_constructions_total.labels(status="success", risk_level=request.risk_tolerance).inc()
        portfolio_tickers_count.observe(num_holdings)
        portfolio_diversification_score.observe(diversification_score)

        _capture_learning_feedback(
            user_id=request.user_id,
            event_name="portfolio.constructed",
            feedback_signal="portfolio_created",
            feedback_value=diversification_score,
            correlation_id=str(portfolio_result.snapshot_id) if portfolio_result.snapshot_id is not None else None,
            payload={
                "risk_tolerance": request.risk_tolerance,
                "available_cash": request.available_cash,
                "num_holdings": num_holdings,
                "total_value": total_value,
                "concentration_risk": concentration_risk,
                "is_demo_mode": request.is_demo_mode,
                "blocked_tickers_count": len(request.blocked_tickers or []),
                "sector_preferences_count": len(request.sector_preferences or []),
            },
        )
        
        logger.info(
            f"✅ Portfolio constructed: {num_holdings} holdings, "
            f"diversification={diversification_score:.2f}, "
            f"risk={concentration_risk}, time={construction_time:.2f}s"
        )
        
        return PortfolioResponse(
            user_id=request.user_id,
            risk_tolerance=request.risk_tolerance,
            available_cash=request.available_cash,
            total_value=total_value,
            holdings=holdings,
            num_holdings=num_holdings,
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            sectors=sectors,
            construction_time=construction_time,
            created_at=portfolio_result.created_at.isoformat() if portfolio_result.created_at else ""
        )
    
    except Exception as e:
        logger.error(f"❌ Portfolio construction error: {e}", exc_info=True)
        portfolio_constructions_total.labels(status="error", risk_level=request.risk_tolerance).inc()
        _capture_learning_feedback(
            user_id=request.user_id,
            event_name="portfolio.construction_error",
            feedback_signal="portfolio_error",
            payload={
                "risk_tolerance": request.risk_tolerance,
                "available_cash": request.available_cash,
                "is_demo_mode": request.is_demo_mode,
                "error": str(e),
            },
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio construction failed: {str(e)}"
        )


@app.get("/portfolios/{user_id}")
async def get_user_portfolios(user_id: str, limit: int = 10):
    """
    Get user's portfolio history.
    
    Args:
        user_id: User identifier
        limit: Max portfolios to return (default 10)
        
    Returns:
        List of user's portfolios with holdings
    """
    try:
        pg = PostgresAgent()
        
        with pg.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    portfolio_id, user_id, risk_tolerance, available_cash, total_value,
                    num_holdings, diversification_score, concentration_risk,
                    sectors, created_at
                FROM portfolios
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            portfolios = []
            for row in cur.fetchall():
                portfolio = {
                    "portfolio_id": row[0],
                    "user_id": row[1],
                    "risk_tolerance": row[2],
                    "available_cash": float(row[3]),
                    "total_value": float(row[4]),
                    "num_holdings": row[5],
                    "diversification_score": float(row[6]),
                    "concentration_risk": row[7],
                    "sectors": row[8],
                    "created_at": row[9].isoformat()
                }
                
                # Fetch holdings
                cur.execute("""
                    SELECT ticker, shares, price, value, weight, sector, composite_z
                    FROM portfolio_holdings
                    WHERE portfolio_id = %s
                    ORDER BY weight DESC
                """, (row[0],))
                
                holdings = []
                for h_row in cur.fetchall():
                    holdings.append({
                        "ticker": h_row[0],
                        "shares": h_row[1],
                        "price": float(h_row[2]),
                        "value": float(h_row[3]),
                        "weight": float(h_row[4]),
                        "sector": h_row[5],
                        "composite_z": float(h_row[6]) if h_row[6] else None
                    })
                
                portfolio["holdings"] = holdings
                portfolios.append(portfolio)
        
        logger.info(f"📊 Retrieved {len(portfolios)} portfolios for user={user_id}")
        _capture_learning_feedback(
            user_id=user_id,
            event_name="portfolio.history.requested",
            feedback_signal="portfolio_history_view",
            payload={
                "limit": limit,
                "returned_count": len(portfolios),
            },
        )
        return {"user_id": user_id, "portfolios": portfolios, "count": len(portfolios)}
    
    except Exception as e:
        logger.error(f"❌ Portfolio retrieval error: {e}", exc_info=True)
        _capture_learning_feedback(
            user_id=user_id,
            event_name="portfolio.history_error",
            feedback_signal="portfolio_history_error",
            payload={
                "limit": limit,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=f"Portfolio retrieval failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test PostgreSQL connection
        pg = PostgresAgent()
        with pg.connection.cursor() as cur:
            cur.execute("SELECT 1")
        
        # Test Redis connection (if available)
        redis_status = "unknown"
        try:
            from redis import Redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            r = Redis(host=redis_host, port=6379, socket_connect_timeout=2)
            r.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "unavailable"
        
        return {
            "status": "healthy",
            "service": "portfolio_architects",
            "port": 8021,
            "postgresql": "connected",
            "redis": redis_status
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "portfolio_architects",
            "error": str(e)
        }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8021)
