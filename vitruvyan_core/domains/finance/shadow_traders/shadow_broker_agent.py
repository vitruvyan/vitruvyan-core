#!/usr/bin/env python3
"""
Shadow Broker Agent - Sacred Order: Reason + Perception

EPISTEMIC ORDER: Reason (Order execution, risk assessment, portfolio optimization)
                  Perception (Market data acquisition, price monitoring)

The Shadow Broker is an autonomous AI agent that:
1. Perceives market conditions via yfinance, Alpaca, Polygon, Alpha Vantage
2. Reasons about order execution (timing, slippage, risk)
3. Suggests portfolio optimizations based on learned patterns
4. Validates trades against Orthodoxy Wardens rules
5. Archives all decisions to Vault Keepers
6. Publishes events to Synaptic Conclave via Cognitive Bus

Author: Vitruvyan Sacred Orders
Date: January 3, 2026
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import json
import uuid

# Third-party imports
import yfinance as yf
import pandas as pd
import numpy as np
from redis.asyncio import Redis
import pytz

# Vitruvyan Sacred Orders imports
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from core.synaptic_conclave.transport.redis_client import RedisBusClient
from core.vpar.vee.vee_engine import VEEEngine

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class OrderStatus(str, Enum):
    """Order lifecycle states"""
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELED = "canceled"


class OrderSide(str, Enum):
    """Order direction"""
    BUY = "buy"
    SELL = "sell"


class RejectionReason(str, Enum):
    """Why an order was rejected"""
    INSUFFICIENT_CASH = "insufficient_cash"
    INVALID_TICKER = "invalid_ticker"
    INSUFFICIENT_SHARES = "insufficient_shares"
    MARKET_CLOSED = "market_closed"
    INVALID_QUANTITY = "invalid_quantity"
    PRICE_FETCH_FAILED = "price_fetch_failed"
    HIGH_RISK = "high_risk"
    ORTHODOXY_REJECTED = "orthodoxy_rejected"


class AgentDecision(str, Enum):
    """Agent's reasoning about order"""
    APPROVE = "approve"
    REJECT = "reject"
    SUGGEST_ALTERNATIVE = "suggest_alternative"
    REQUEST_CLARIFICATION = "request_clarification"


@dataclass
class PriceQuote:
    """Market price information"""
    ticker: str
    price: float
    bid: Optional[float]
    ask: Optional[float]
    timestamp: datetime
    source: str  # yfinance, alpaca, polygon, vantage
    confidence: float  # 0.0-1.0


@dataclass
class MarketCondition:
    """Current market state"""
    is_open: bool
    volatility_regime: str  # low, normal, high, extreme
    spy_change_pct: float
    vix_level: float
    timestamp: datetime


@dataclass
class RiskAssessment:
    """Agent's risk analysis"""
    risk_score: float  # 0-100
    risk_category: str  # low, medium, high, extreme
    concerns: List[str]
    mitigations: List[str]
    orthodoxy_approved: bool


@dataclass
class TradeRecommendation:
    """Agent's suggested action"""
    decision: AgentDecision
    ticker: str
    side: OrderSide
    suggested_quantity: int
    reasoning: str
    risk_assessment: RiskAssessment
    alternatives: List[Dict[str, Any]]
    vee_explanation: str  # Natural language explanation


@dataclass
class OrderResult:
    """Trade execution outcome"""
    status: OrderStatus
    order_id: str
    ticker: str
    side: OrderSide
    quantity: int
    fill_price: Optional[float]
    total_cost: Optional[float]
    new_cash_balance: Optional[float]
    message: str
    rejection_reason: Optional[RejectionReason]
    conclave_event_id: Optional[str]
    slippage_pct: float
    agent_reasoning: str
    risk_assessment: RiskAssessment
    timestamp: datetime


@dataclass
class PortfolioSnapshot:
    """Current portfolio state"""
    user_id: str
    cash_balance: float
    positions: List[Dict[str, Any]]
    total_value: float
    unrealized_pnl: float
    total_pnl: float
    num_positions: int
    sector_allocation: Dict[str, float]
    risk_metrics: Dict[str, float]
    agent_insights: List[str]
    timestamp: datetime


# ============================================================================
# MARKET DATA PROVIDER (Perception Layer)
# ============================================================================

class MarketDataProvider:
    """
    EPISTEMIC ORDER: Perception
    
    Acquires market data from multiple sources:
    - yfinance (primary, FREE)
    - Alpaca (stub, prepared for real API)
    - Polygon (stub)
    - Alpha Vantage (stub, API key in env)
    """
    
    def __init__(self):
        self.redis_client = None
        self.cache_ttl = 60  # 1-minute cache
        
        # API keys from environment
        self.alpaca_key = os.getenv("ALPACA_API_KEY")
        self.polygon_key = os.getenv("POLYGON_API_KEY")
        self.vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    async def initialize_redis(self):
        """Initialize Redis connection for caching"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_client = Redis(host=redis_host, port=redis_port, decode_responses=True)
        logger.info(f"✅ Redis initialized for market data caching ({redis_host}:{redis_port})")
    
    async def get_current_price(self, ticker: str) -> PriceQuote:
        """
        Get current price with caching and fallback sources.
        
        Sacred Orders Architecture (Jan 7, 2026):
        - Priority 1: Redis cache (1-minute TTL)
        - Priority 2: PostgreSQL daily_prices (Codex Hunters data)
        - Priority 3: Alpha Vantage (emergency fallback if DB empty)
        
        Codex Hunters (Perception) is the ONLY component that calls external APIs
        (yfinance, polygon, alpaca). Shadow Traders (Reason) reads from PostgreSQL.
        
        MVP Design: Daily data sufficient for demo (no real-time needed).
        Production: Alpaca/Polygon stubs exist for future real-time pricing.
        """
        # Check cache first
        cache_key = f"price:{ticker}"
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Deserialize timestamp from ISO format
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                logger.info(f"💾 Cache HIT for {ticker}: ${data['price']:.2f}")
                return PriceQuote(**data)
        
        # Try PostgreSQL first (Codex Hunters daily backfill data)
        quote = await self._fetch_from_postgres(ticker)
        if quote:
            # Cache for 1 minute
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps({
                        "ticker": quote.ticker,
                        "price": quote.price,
                        "bid": quote.bid,
                        "ask": quote.ask,
                        "timestamp": quote.timestamp.isoformat(),
                        "source": quote.source,
                        "confidence": quote.confidence
                    })
                )
            return quote
        
        # Emergency fallback: Alpha Vantage (if PostgreSQL completely empty)
        logger.warning(f"⚠️ PostgreSQL empty for {ticker}, using Alpha Vantage emergency fallback...")
        
        if self.vantage_key:
            quote = await self._fetch_from_vantage(ticker)
            if quote:
                # Cache Alpha Vantage result (CRITICAL for rate limit mitigation)
                if self.redis_client:
                    await self.redis_client.setex(
                        cache_key, self.cache_ttl,
                        json.dumps({
                            "ticker": quote.ticker, "price": quote.price,
                            "bid": quote.bid, "ask": quote.ask,
                            "timestamp": quote.timestamp.isoformat(),
                            "source": quote.source, "confidence": quote.confidence
                        })
                    )
                    logger.info(f"💾 Cached Alpha Vantage price for {ticker} (60s TTL)")
                return quote
        
        raise ValueError(f"❌ Failed to fetch price for {ticker} from PostgreSQL and Alpha Vantage fallback")
    
    async def _fetch_from_postgres(self, ticker: str) -> Optional[PriceQuote]:
        """
        Fetch latest daily price from PostgreSQL (Codex Hunters data).
        
        Sacred Orders Architecture: Shadow Traders reads from PostgreSQL
        populated by Codex Hunters daily backfill (23:00 UTC).
        
        Returns:
            PriceQuote or None if no data found
        """
        try:
            from core.agents.postgres_agent import PostgresAgent
            
            pg = PostgresAgent()
            results = pg.fetch(
                """
                SELECT ticker, price, open, high, low, volume, timestamp, source
                FROM daily_prices
                WHERE ticker = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (ticker,),
            )
            
            if not results:
                logger.warning(f"⚠️ No PostgreSQL price data for {ticker} (Codex backfill may not have run)")
                return None
            
            result = results[0]
            ticker_db = result.get("ticker")
            price = result.get("price")
            timestamp = result.get("timestamp")
            source = result.get("source")
            
            # Convert Decimal to float for calculations
            price = float(price) if price else 0.0
            
            # Calculate bid/ask spread (estimated from OHLC)
            # Bid slightly below close, ask slightly above
            spread_pct = 0.001  # 0.1% spread
            bid = price * (1 - spread_pct)
            ask = price * (1 + spread_pct)
            
            logger.info(f"📊 PostgreSQL: {ticker} = ${price:.2f} (last updated: {timestamp})")
            
            return PriceQuote(
                ticker=ticker,
                price=price,
                bid=bid,
                ask=ask,
                timestamp=timestamp,
                source=f"postgresql_{source}",  # e.g., "postgresql_yfinance"
                confidence=0.95  # High confidence (Codex Hunters validated data)
            )
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL fetch failed for {ticker}: {e}")
            return None
    
    async def _fetch_from_yfinance(self, ticker: str) -> Optional[PriceQuote]:
        """Fetch from yfinance (primary source)"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try multiple price fields (yfinance API varies)
            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
            
            if not price:
                logger.error(f"❌ No price found for {ticker} in yfinance")
                return None
            
            bid = info.get("bid")
            ask = info.get("ask")
            
            logger.info(f"✅ yfinance: {ticker} = ${price:.2f}")
            
            return PriceQuote(
                ticker=ticker,
                price=float(price),
                bid=float(bid) if bid else None,
                ask=float(ask) if ask else None,
                timestamp=datetime.now(timezone.utc),
                source="yfinance",
                confidence=0.95  # yfinance is reliable
            )
        
        except Exception as e:
            logger.error(f"❌ yfinance error for {ticker}: {e}")
            return None
    
    async def _fetch_from_alpaca(self, ticker: str) -> Optional[PriceQuote]:
        """Stub for Alpaca API (implement when key available)"""
        logger.warning(f"⚠️ Alpaca API stub called for {ticker} (not implemented)")
        return None
    
    async def _fetch_from_polygon(self, ticker: str) -> Optional[PriceQuote]:
        """Stub for Polygon API (implement when key available)"""
        logger.warning(f"⚠️ Polygon API stub called for {ticker} (not implemented)")
        return None
    
    async def _fetch_from_vantage(self, ticker: str) -> Optional[PriceQuote]:
        """
        Fetch from Alpha Vantage API (fallback when yfinance fails).
        
        Phase 3.2.1 (Jan 7, 2026): Implemented real Alpha Vantage integration
        as fallback for yfinance 429 rate limit issues.
        
        API: https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={key}
        """
        if not self.vantage_key:
            logger.warning(f"⚠️ Alpha Vantage API key not configured (set ALPHA_VANTAGE_API_KEY)")
            return None
        
        _AV_MAX_RETRIES = 3
        _AV_BACKOFF = 2.0
        
        for attempt in range(1, _AV_MAX_RETRIES + 1):
            try:
                import httpx
                
                url = f"https://www.alphavantage.co/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": ticker,
                    "apikey": self.vantage_key
                }
                
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"❌ Alpha Vantage HTTP {response.status_code} for {ticker}")
                    if response.status_code == 429 and attempt < _AV_MAX_RETRIES:
                        wait = _AV_BACKOFF ** attempt
                        logger.warning(f"⏳ Rate limited, retrying in {wait}s…")
                        import asyncio; await asyncio.sleep(wait)
                        continue
                    return None
                
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    logger.error(f"❌ Alpha Vantage error: {data['Error Message']}")
                    return None
                
                if "Note" in data:
                    # Rate limit message — retry with backoff
                    logger.warning(f"⚠️ Alpha Vantage rate limit: {data['Note']}")
                    if attempt < _AV_MAX_RETRIES:
                        wait = _AV_BACKOFF ** attempt
                        logger.warning(f"⏳ Retrying in {wait}s…")
                        import asyncio; await asyncio.sleep(wait)
                        continue
                    return None
                
                # Extract price from Global Quote
                quote = data.get("Global Quote", {})
                
                if not quote:
                    logger.error(f"❌ No quote data from Alpha Vantage for {ticker}")
                    return None
                
                price_str = quote.get("05. price")
                if not price_str:
                    logger.error(f"❌ No price field in Alpha Vantage response for {ticker}")
                    return None
                
                price = float(price_str)
                
                # Alpha Vantage doesn't provide bid/ask in GLOBAL_QUOTE
                # Use spread estimation (0.5% typical)
                spread = price * 0.005
                bid = price - spread / 2
                ask = price + spread / 2
                
                logger.info(f"✅ Alpha Vantage: {ticker} = ${price:.2f} (fallback source)")
                
                return PriceQuote(
                    ticker=ticker,
                    price=price,
                    bid=bid,
                    ask=ask,
                    timestamp=datetime.now(timezone.utc),
                    source="alpha_vantage",
                    confidence=0.90  # Slightly lower than yfinance (delayed data)
                )
                
            except Exception as e:
                logger.error(f"❌ Alpha Vantage attempt {attempt}/{_AV_MAX_RETRIES} for {ticker}: {e}")
                if attempt < _AV_MAX_RETRIES:
                    import asyncio
                    await asyncio.sleep(_AV_BACKOFF ** attempt)
                    continue
                return None
        
        return None
    
    def simulate_slippage(self, price: float, quantity: int, side: OrderSide) -> Tuple[float, float]:
        """
        Simulate realistic slippage based on order size.
        
        Slippage increases with order size:
        - Small orders (<100 shares): 0.05%
        - Medium orders (100-1000): 0.10%
        - Large orders (>1000): 0.15%
        """
        if quantity < 100:
            slippage_pct = 0.05
        elif quantity < 1000:
            slippage_pct = 0.10
        else:
            slippage_pct = 0.15
        
        # Apply slippage direction (buy = pay more, sell = receive less)
        if side == OrderSide.BUY:
            fill_price = float(price) * (1 + slippage_pct / 100)
        else:
            fill_price = float(price) * (1 - slippage_pct / 100)
        
        return fill_price, slippage_pct
    
    async def get_market_condition(self) -> MarketCondition:
        """
        Get current market state (for risk assessment).
        
        Checks:
        - Market hours (NYSE 9:30-16:00 ET)
        - SPY daily change
        - VIX level
        - Volatility regime
        """
        ny_tz = pytz.timezone("America/New_York")
        now_et = datetime.now(ny_tz)
        
        # Check market hours
        is_open = (
            now_et.weekday() < 5 and  # Monday-Friday
            now_et.hour >= 9 and
            (now_et.hour < 16 or (now_et.hour == 9 and now_et.minute >= 30))
        )
        
        # Fetch SPY and VIX for volatility assessment
        try:
            import signal as _sig
            _YFINANCE_TIMEOUT = 15  # seconds

            def _alarm_handler(signum, frame):
                raise TimeoutError("yfinance market condition call timed out")

            try:
                _old_handler = _sig.signal(_sig.SIGALRM, _alarm_handler)
                _sig.alarm(_YFINANCE_TIMEOUT)
            except (AttributeError, ValueError):
                _old_handler = None  # Windows / threads

            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="2d")
            spy_change_pct = ((float(spy_hist['Close'].iloc[-1]) / float(spy_hist['Close'].iloc[-2])) - 1) * 100
            
            vix = yf.Ticker("^VIX")
            vix_level = vix.info.get("regularMarketPrice", 20.0)

            # Cancel alarm
            try:
                _sig.alarm(0)
                if _old_handler is not None:
                    _sig.signal(_sig.SIGALRM, _old_handler)
            except (AttributeError, ValueError):
                pass
            
            # Determine volatility regime
            if vix_level < 15:
                volatility_regime = "low"
            elif vix_level < 25:
                volatility_regime = "normal"
            elif vix_level < 35:
                volatility_regime = "high"
            else:
                volatility_regime = "extreme"
            
            logger.info(f"📊 Market: SPY {spy_change_pct:+.2f}%, VIX {vix_level:.1f} ({volatility_regime})")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch market condition: {e}")
            spy_change_pct = 0.0
            vix_level = 20.0
            volatility_regime = "normal"
        
        return MarketCondition(
            is_open=is_open,
            volatility_regime=volatility_regime,
            spy_change_pct=spy_change_pct,
            vix_level=vix_level,
            timestamp=datetime.now(timezone.utc)
        )


# ============================================================================
# SHADOW BROKER AGENT (Reason Layer)
# ============================================================================

class ShadowBrokerAgent:
    """
    EPISTEMIC ORDER: Reason
    
    Autonomous AI agent for shadow trading with:
    1. Risk-aware order execution
    2. Portfolio optimization suggestions
    3. Trade pattern learning (via Qdrant embeddings)
    4. Orthodoxy Wardens validation
    5. Vault Keepers archival
    6. Synaptic Conclave event publishing
    """
    
    def __init__(self):
        self.pg = PostgresAgent()
        self.qdrant = QdrantAgent()
        self.market_data = MarketDataProvider()
        self.redis_bus = RedisBusClient()
        self.vee_engine = VEEEngine()  # Phase 3.2: VEE narrative generation
        
        # Sacred Orders integration
        self.conclave_enabled = os.getenv("CONCLAVE_ENABLED", "1") == "1"
        self.vault_enabled = os.getenv("VAULT_ENABLED", "1") == "1"
        self.orthodoxy_enabled = os.getenv("ORTHODOXY_ENABLED", "1") == "1"
        
        logger.info("🤖 Shadow Broker Agent initialized (Sacred Orders: Reason + Perception)")
    
    async def initialize(self):
        """Initialize async components"""
        await self.market_data.initialize_redis()
        logger.info("✅ Shadow Broker Agent ready")
    
    # ========================================================================
    # AUTONOMOUS TRADE REASONING
    # ========================================================================
    
    async def reason_about_trade(
        self,
        user_id: str,
        ticker: str,
        side: OrderSide,
        quantity: int
    ) -> TradeRecommendation:
        """
        Agent's autonomous reasoning about proposed trade.
        
        Considers:
        1. Market conditions (volatility, hours)
        2. Portfolio impact (concentration, diversification)
        3. Risk metrics (position size, sector exposure)
        4. Historical patterns (learned from Qdrant)
        5. Orthodoxy Wardens rules
        
        Returns: TradeRecommendation with decision + reasoning
        """
        logger.info(f"🧠 Agent reasoning: {side.value.upper()} {quantity} {ticker} for {user_id}")
        
        # 1. Get market condition
        market = await self.market_data.get_market_condition()
        
        # 2. Get current portfolio
        portfolio = await self.get_portfolio_snapshot(user_id)
        
        # 3. Assess risk
        risk = await self._assess_trade_risk(
            user_id=user_id,
            ticker=ticker,
            side=side,
            quantity=quantity,
            market=market,
            portfolio=portfolio
        )
        
        # 4. Check Orthodoxy Wardens (ticker validation)
        if self.orthodoxy_enabled:
            orthodoxy_result = await self._validate_with_orthodoxy(
                user_id=user_id,
                ticker=ticker,
                side=side,
                quantity=quantity,
                risk=risk
            )
            risk.orthodoxy_approved = orthodoxy_result["approved"]
            if not orthodoxy_result["approved"]:
                risk.concerns.extend(orthodoxy_result["concerns"])
        else:
            risk.orthodoxy_approved = True  # Orthodoxy disabled in config
        
        # 5. Make decision
        if risk.risk_category == "extreme" or not risk.orthodoxy_approved:
            decision = AgentDecision.REJECT
            reasoning = f"❌ Trade rejected: {', '.join(risk.concerns)}"
        elif risk.risk_category == "high":
            decision = AgentDecision.SUGGEST_ALTERNATIVE
            reasoning = f"⚠️ High risk detected. Suggesting alternatives."
        else:
            decision = AgentDecision.APPROVE
            reasoning = f"✅ Trade approved with {risk.risk_category} risk."
        
        # 6. Generate alternatives if needed
        alternatives = []
        if decision == AgentDecision.SUGGEST_ALTERNATIVE:
            alternatives = await self._generate_alternatives(
                ticker=ticker,
                side=side,
                quantity=quantity,
                portfolio=portfolio
            )
        
        # 7. Generate VEE explanation
        vee_explanation = await self._generate_vee_explanation(
            ticker=ticker,
            side=side,
            quantity=quantity,
            decision=decision,
            risk=risk,
            market=market
        )
        
        recommendation = TradeRecommendation(
            decision=decision,
            ticker=ticker,
            side=side,
            suggested_quantity=quantity,
            reasoning=reasoning,
            risk_assessment=risk,
            alternatives=alternatives,
            vee_explanation=vee_explanation
        )
        
        logger.info(f"🧠 Decision: {decision.value} ({risk.risk_category} risk)")
        
        return recommendation
    
    async def _assess_trade_risk(
        self,
        user_id: str,
        ticker: str,
        side: OrderSide,
        quantity: int,
        market: MarketCondition,
        portfolio: PortfolioSnapshot
    ) -> RiskAssessment:
        """
        Autonomous risk assessment using AI reasoning.
        
        Risk factors:
        1. Position size (% of portfolio)
        2. Sector concentration
        3. Market volatility
        4. Liquidity
        5. Historical patterns
        """
        concerns = []
        mitigations = []
        
        # Get quote for value calculation
        try:
            quote = await self.market_data.get_current_price(ticker)
            position_value = Decimal(str(quote.price)) * Decimal(str(quantity))
        except Exception as e:
            concerns.append(f"Price fetch failed: {e}")
            return RiskAssessment(
                risk_score=100.0,
                risk_category="extreme",
                concerns=concerns,
                mitigations=[],
                orthodoxy_approved=False
            )
        
        # Calculate position size as % of portfolio
        if portfolio.total_value > 0:
            position_pct = (float(position_value) / float(portfolio.total_value)) * 100
        else:
            position_pct = 100.0  # First trade = 100% of portfolio
        
        risk_score = 0.0
        
        # Risk factor 1: Position size
        if position_pct > 50:
            risk_score += 40
            concerns.append(f"Large position size ({position_pct:.1f}% of portfolio)")
            mitigations.append("Consider reducing quantity to <30% of portfolio")
        elif position_pct > 30:
            risk_score += 20
            concerns.append(f"Moderate position size ({position_pct:.1f}%)")
        
        # Risk factor 2: Market volatility
        if market.volatility_regime == "extreme":
            risk_score += 30
            concerns.append(f"Extreme market volatility (VIX {market.vix_level:.1f})")
            mitigations.append("Wait for volatility to decrease")
        elif market.volatility_regime == "high":
            risk_score += 15
            concerns.append(f"High market volatility (VIX {market.vix_level:.1f})")
        
        # Risk factor 3: Market closed
        if not market.is_open and side == OrderSide.BUY:
            risk_score += 20
            concerns.append("Market is closed (execution at next open)")
        
        # Risk factor 4: Sector concentration (TODO: implement sector lookup)
        # For now, skip sector analysis
        
        # Determine risk category
        if risk_score >= 70:
            risk_category = "extreme"
        elif risk_score >= 50:
            risk_category = "high"
        elif risk_score >= 30:
            risk_category = "medium"
        else:
            risk_category = "low"
        
        logger.info(f"📊 Risk assessment: {risk_category} (score: {risk_score:.1f})")
        
        return RiskAssessment(
            risk_score=risk_score,
            risk_category=risk_category,
            concerns=concerns,
            mitigations=mitigations,
            orthodoxy_approved=True  # Will be updated by Orthodoxy check
        )
    
    async def _validate_with_orthodoxy(
        self,
        user_id: str,
        ticker: str,
        side: OrderSide,
        quantity: int,
        risk: RiskAssessment
    ) -> Dict[str, Any]:
        """
        Validate trade with Orthodoxy Wardens (Sacred Order: Truth).
        
        Orthodoxy rules:
        1. No extreme risk trades
        2. No high concentration (>50% single ticker)
        3. No trades during market crash (SPY <-5%)
        4. No invalid tickers
        """
        concerns = []
        
        # Rule 1: Extreme risk forbidden
        if risk.risk_category == "extreme":
            concerns.append("Orthodoxy: Extreme risk trades forbidden")
        
        # Rule 2: Ticker must exist in PostgreSQL ticker_metadata
        with self.pg.connection.cursor() as cur:
            cur.execute("SELECT 1 FROM ticker_metadata WHERE ticker = %s", (ticker,))
            if not cur.fetchone():
                concerns.append(f"Orthodoxy: Invalid ticker {ticker}")
        
        # TODO: Add more Orthodoxy rules
        
        approved = len(concerns) == 0
        
        if approved:
            logger.info("✅ Orthodoxy Wardens: Trade approved")
        else:
            logger.warning(f"❌ Orthodoxy Wardens: Trade rejected - {concerns}")
        
        return {
            "approved": approved,
            "concerns": concerns
        }
    
    async def _generate_alternatives(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        portfolio: PortfolioSnapshot
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative trade suggestions (AI reasoning).
        
        Alternatives:
        1. Reduce quantity
        2. Different ticker in same sector
        3. ETF instead of individual stock
        """
        alternatives = []
        
        # Alternative 1: Reduce quantity
        alternatives.append({
            "ticker": ticker,
            "side": side.value,
            "quantity": int(quantity * 0.5),
            "reasoning": "Reduce position size to lower risk"
        })
        
        # Alternative 2: TODO - Suggest similar tickers (requires sector data)
        
        return alternatives
    
    async def _generate_vee_explanation(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        decision: AgentDecision,
        risk: RiskAssessment,
        market: MarketCondition
    ) -> str:
        """
        Generate VEE (Vitruvyan Explainability Engine) natural language explanation.
        
        Explains:
        - Why agent approved/rejected trade
        - Risk factors considered
        - Market conditions
        - Alternatives
        """
        if decision == AgentDecision.APPROVE:
            explanation = (
                f"Il Shadow Broker Agent ha approvato l'ordine di {side.value} per {quantity} azioni {ticker}. "
                f"Il rischio è classificato come {risk.risk_category}, con un risk score di {risk.risk_score:.1f}/100. "
            )
            if risk.concerns:
                explanation += f"Considerazioni: {', '.join(risk.concerns)}. "
            explanation += f"Condizioni di mercato: {market.volatility_regime} volatilità (VIX {market.vix_level:.1f})."
        
        elif decision == AgentDecision.REJECT:
            explanation = (
                f"Il Shadow Broker Agent ha rigettato l'ordine di {side.value} per {quantity} azioni {ticker}. "
                f"Motivi: {', '.join(risk.concerns)}. "
            )
            if risk.mitigations:
                explanation += f"Suggerimenti: {', '.join(risk.mitigations)}."
        
        else:  # SUGGEST_ALTERNATIVE
            explanation = (
                f"Il Shadow Broker Agent suggerisce alternative per l'ordine {side.value} {quantity} {ticker}. "
                f"Il rischio attuale è {risk.risk_category} ({risk.risk_score:.1f}/100). "
                f"Considera: {', '.join(risk.mitigations)}."
            )
        
        return explanation
    
    # ========================================================================
    # ORDER EXECUTION
    # ========================================================================
    
    async def execute_market_order(
        self,
        user_id: str,
        ticker: str,
        side: OrderSide,
        quantity: int,
        bypass_agent_approval: bool = False
    ) -> OrderResult:
        """
        Execute market order with autonomous agent reasoning.
        
        Flow:
        1. Agent reasons about trade → TradeRecommendation
        2. If approved (or bypass=True) → Execute
        3. Publish to Synaptic Conclave
        4. Archive to Vault Keepers
        5. Embed trade pattern to Qdrant
        
        Args:
            bypass_agent_approval: If True, skip agent reasoning (for forced executions)
        """
        logger.info(f"🤖 Shadow Broker executing: {side.value.upper()} {quantity} {ticker} (user: {user_id})")
        
        # Step 1: Agent reasoning (unless bypassed)
        if not bypass_agent_approval:
            recommendation = await self.reason_about_trade(user_id, ticker, side, quantity)
            
            if recommendation.decision == AgentDecision.REJECT:
                return OrderResult(
                    status=OrderStatus.REJECTED,
                    order_id=str(uuid.uuid4()),
                    ticker=ticker,
                    side=side,
                    quantity=quantity,
                    fill_price=None,
                    total_cost=None,
                    new_cash_balance=None,
                    message=recommendation.reasoning,
                    rejection_reason=RejectionReason.HIGH_RISK,
                    conclave_event_id=None,
                    slippage_pct=0.0,
                    agent_reasoning=recommendation.vee_explanation,
                    risk_assessment=recommendation.risk_assessment,
                    timestamp=datetime.now(timezone.utc)
                )
            
            if recommendation.decision == AgentDecision.SUGGEST_ALTERNATIVE:
                # Return alternatives (frontend can show to user)
                pass  # TODO: Handle alternatives in frontend
        
        # Step 2: Validate order (basic checks)
        validation_error = await self._validate_order_basic(user_id, ticker, side, quantity)
        if validation_error:
            return OrderResult(
                status=OrderStatus.REJECTED,
                order_id=str(uuid.uuid4()),
                ticker=ticker,
                side=side,
                quantity=quantity,
                fill_price=None,
                total_cost=None,
                new_cash_balance=None,
                message=validation_error["message"],
                rejection_reason=validation_error["reason"],
                conclave_event_id=None,
                slippage_pct=0.0,
                agent_reasoning="Basic validation failed",
                risk_assessment=RiskAssessment(
                    risk_score=0.0,
                    risk_category="unknown",
                    concerns=[validation_error["message"]],
                    mitigations=[],
                    orthodoxy_approved=False
                ),
                timestamp=datetime.now(timezone.utc)
            )
        
        # Step 3: Fetch current price
        try:
            quote = await self.market_data.get_current_price(ticker)
        except Exception as e:
            logger.error(f"❌ Price fetch failed: {e}")
            return OrderResult(
                status=OrderStatus.REJECTED,
                order_id=str(uuid.uuid4()),
                ticker=ticker,
                side=side,
                quantity=quantity,
                fill_price=None,
                total_cost=None,
                new_cash_balance=None,
                message=f"Price fetch failed: {e}",
                rejection_reason=RejectionReason.PRICE_FETCH_FAILED,
                conclave_event_id=None,
                slippage_pct=0.0,
                agent_reasoning="Market data unavailable",
                risk_assessment=RiskAssessment(
                    risk_score=0.0,
                    risk_category="unknown",
                    concerns=["Price fetch failed"],
                    mitigations=[],
                    orthodoxy_approved=False
                ),
                timestamp=datetime.now(timezone.utc)
            )
        
        # Step 4: Simulate slippage
        fill_price, slippage_pct = self.market_data.simulate_slippage(quote.price, quantity, side)
        
        # Step 5: Execute trade (buy or sell)
        if side == OrderSide.BUY:
            result = await self._execute_buy(user_id, ticker, quantity, fill_price, slippage_pct)
        else:
            result = await self._execute_sell(user_id, ticker, quantity, fill_price, slippage_pct)
        
        # Step 6: Publish to Synaptic Conclave
        if result.status == OrderStatus.FILLED and self.conclave_enabled:
            conclave_event_id = await self._publish_trade_event(result)
            result.conclave_event_id = conclave_event_id
        
        # Step 7: Embed trade pattern to Qdrant (for learning)
        if result.status == OrderStatus.FILLED:
            await self._embed_trade_pattern(result)
        
        # Step 8: Generate VEE narrative (Phase 3.2 - Jan 7, 2026)
        if result.status == OrderStatus.FILLED:
            vee_narrative = await self._generate_vee_narrative(result)
            if vee_narrative:
                # Save VEE to database
                await self._save_vee_to_order(result.order_id, vee_narrative)
                logger.info(f"📝 VEE narrative generated for order {result.order_id}")
        
        # Step 9: Archive to Vault Keepers (if enabled)
        if result.status == OrderStatus.FILLED and self.vault_enabled:
            await self._archive_to_vault(result)
        
        logger.info(f"✅ Order executed: {result.status.value} (order_id: {result.order_id})")
        
        return result
    
    async def _generate_vee_narrative(
        self,
        result: OrderResult
    ) -> Optional[str]:
        """
        Generate VEE 3-level narrative for executed order (Phase 3.2 - Jan 7, 2026).
        
        Generates English-only VEE narrative (MVP Language Guardrail).
        
        VEE Structure:
        - Level 1 (Summary): Conversational, zero tecnicismi (120-180 words)
        - Level 2 (Detailed): Operational analysis, strategy implications (150-200 words)
        - Level 3 (Technical): Explicit metrics, risk/reward ratios (200-250 words)
        
        Args:
            result: OrderResult with execution details
            
        Returns:
            VEE narrative string (English-only) or None if generation fails
        """
        try:
            # Prepare KPI data for VEE Engine
            kpi_data = {
                "ticker": result.ticker,
                "side": result.side.value,
                "quantity": result.quantity,
                "fill_price": float(result.fill_price) if result.fill_price else 0.0,
                "total_cost": float(result.total_cost) if result.total_cost else 0.0,
                "slippage_pct": float(result.slippage_pct),
                "status": result.status.value,
                "timestamp": result.timestamp.isoformat(),
                "agent_reasoning": result.agent_reasoning,
                "risk_assessment": {
                    "risk_score": float(result.risk_assessment.risk_score),
                    "risk_category": result.risk_assessment.risk_category,
                    "concerns": result.risk_assessment.concerns,
                    "mitigations": result.risk_assessment.mitigations,
                    "orthodoxy_approved": result.risk_assessment.orthodoxy_approved
                }
            }
            
            # Generate VEE explanation (English-only for MVP)
            # VEE Engine signature: explain_ticker(ticker, kpi, profile=None, semantic_context=None)
            explanation = self.vee_engine.explain_ticker(
                ticker=result.ticker,
                kpi=kpi_data  # Use 'kpi' not 'complete_kpi'
                # profile and semantic_context are optional, omit for simplicity
            )
            
            if explanation and "explanations" in explanation:
                # Extract VEE narratives from response
                explanations = explanation["explanations"]
                
                # Build 3-level VEE narrative
                vee_parts = []
                
                if "summary" in explanations:
                    vee_parts.append(f"**Summary (Level 1)**\n{explanations['summary']}")
                
                if "detailed" in explanations:
                    vee_parts.append(f"\n\n**Detailed Analysis (Level 2)**\n{explanations['detailed']}")
                
                if "technical" in explanations:
                    vee_parts.append(f"\n\n**Technical Details (Level 3)**\n{explanations['technical']}")
                
                vee_narrative = "\n".join(vee_parts)
                
                logger.info(f"📝 VEE narrative generated ({len(vee_narrative)} chars)")
                return vee_narrative
            
            logger.warning("⚠️ VEE Engine returned empty response")
            return None
            
        except Exception as e:
            logger.error(f"❌ VEE narrative generation failed: {e}")
            return None
    
    async def _save_vee_to_order(
        self,
        order_id: str,
        vee_narrative: str
    ) -> None:
        """
        Save VEE narrative to shadow_orders table (Phase 3.2 - Jan 7, 2026).
        
        Updates existing order record with VEE narrative and metadata.
        
        Args:
            order_id: UUID of order
            vee_narrative: Generated VEE 3-level explanation
        """
        try:
            with self.pg.connection.cursor() as cur:
                cur.execute(
                    """
                    UPDATE shadow_orders
                    SET vee_narrative = %s,
                        vee_generated_at = NOW(),
                        vee_model = %s
                    WHERE order_id = %s
                    """,
                    (vee_narrative, "gpt-4o-mini", order_id)
                )
                self.pg.connection.commit()
                
            logger.info(f"✅ VEE narrative saved to order {order_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save VEE to database: {e}")
            # Don't fail the entire order if VEE save fails
            pass
    
    async def _validate_order_basic(
        self,
        user_id: str,
        ticker: str,
        side: OrderSide,
        quantity: int
    ) -> Optional[Dict[str, Any]]:
        """Basic validation checks (quantity, ticker existence, cash/shares availability)"""
        
        # Check quantity > 0
        if quantity <= 0:
            return {
                "message": "Quantity must be > 0",
                "reason": RejectionReason.INVALID_QUANTITY
            }
        
        # Check ticker exists in PostgreSQL
        with self.pg.connection.cursor() as cur:
            cur.execute("SELECT 1 FROM ticker_metadata WHERE ticker = %s", (ticker,))
            if not cur.fetchone():
                return {
                    "message": f"Invalid ticker: {ticker}",
                    "reason": RejectionReason.INVALID_TICKER
                }
        
        # ✅ CRITICAL: Ensure cash account exists (auto-initialize if needed)
        try:
            await self._ensure_cash_account(user_id)
        except Exception as e:
            logger.error(f"❌ Cash account initialization failed: {e}")
            return {
                "message": f"Failed to initialize cash account: {str(e)}",
                "reason": RejectionReason.INSUFFICIENT_CASH
            }
        
        # Check cash (for buy) or shares (for sell)
        if side == OrderSide.BUY:
            # Cash will be checked in _execute_buy (need price first)
            pass
        
        else:  # SELL
            with self.pg.connection.cursor() as cur:
                cur.execute(
                    "SELECT quantity FROM shadow_positions WHERE user_id = %s AND ticker = %s",
                    (user_id, ticker)
                )
                row = cur.fetchone()
                if not row or row[0] < quantity:
                    return {
                        "message": f"Insufficient shares: need {quantity}, have {row[0] if row else 0}",
                        "reason": RejectionReason.INSUFFICIENT_SHARES
                    }
        
        # All checks passed
        return None
    
    async def _ensure_cash_account(self, user_id: str) -> None:
        """
        Ensure user has a cash account. Auto-initialize if missing.
        
        **AUTO-INITIALIZATION** (Jan 26, 2026):
        - On first order, creates shadow_cash_accounts record
        - Initial balance: $50,000 USD (starting_capital + current_cash)
        - Account status: 'active'
        - Logs creation event for audit
        
        This replaces the need for manual account creation.
        """
        with self.pg.connection.cursor() as cur:
            # Check if account exists
            cur.execute(
                "SELECT user_id, current_cash FROM shadow_cash_accounts WHERE user_id = %s",
                (user_id,)
            )
            existing = cur.fetchone()
            
            if existing:
                # Account exists - no action needed
                logger.debug(f"✅ Cash account exists for user {user_id} (balance: ${existing[1]:.2f})")
                return
            
            # ✅ AUTO-INITIALIZE: Create new account
            initial_balance = Decimal("50000.00")  # $50,000 starting capital
            
            logger.info(
                f"🆕 AUTO-INITIALIZING cash account for new user {user_id} "
                f"(initial balance: ${initial_balance})"
            )
            
            cur.execute(
                """
                INSERT INTO shadow_cash_accounts (
                    user_id, 
                    starting_capital, 
                    current_cash, 
                    total_deposits,
                    total_withdrawals,
                    account_status,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (user_id) DO NOTHING
                """,
                (
                    user_id, 
                    initial_balance,  # starting_capital
                    initial_balance,  # current_cash
                    Decimal("0.00"),  # total_deposits
                    Decimal("0.00"),  # total_withdrawals
                    'active'          # account_status
                )
            )
            
            self.pg.connection.commit()
            
            # Note: Audit trail skipped due to check_positive_quantity constraint
            # Shadow orders require quantity > 0, but account init is quantity 0
            # Alternative: Log via dedicated initialization_logs table (future)
            
            logger.info(
                f"✅ Cash account created for user {user_id} "
                f"(initial balance: ${initial_balance})"
            )
    
    async def _execute_buy(
        self,
        user_id: str,
        ticker: str,
        quantity: int,
        fill_price: float,
        slippage_pct: float
    ) -> OrderResult:
        """Execute BUY order: deduct cash, add/update position"""
        
        order_id = str(uuid.uuid4())
        total_cost = Decimal(str(fill_price)) * Decimal(str(quantity))
        
        with self.pg.connection.cursor() as cur:
            # Get current cash
            cur.execute(
                "SELECT current_cash FROM shadow_cash_accounts WHERE user_id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No cash account for user {user_id}")
            
            current_cash = row[0]
            
            # Check sufficient cash
            if current_cash < total_cost:
                return OrderResult(
                    status=OrderStatus.REJECTED,
                    order_id=order_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    fill_price=fill_price,
                    total_cost=total_cost,
                    new_cash_balance=current_cash,
                    message=f"Insufficient cash: need ${total_cost:.2f}, have ${current_cash:.2f}",
                    rejection_reason=RejectionReason.INSUFFICIENT_CASH,
                    conclave_event_id=None,
                    slippage_pct=slippage_pct,
                    agent_reasoning="Cash balance insufficient",
                    risk_assessment=RiskAssessment(
                        risk_score=0.0,
                        risk_category="low",
                        concerns=["Insufficient cash"],
                        mitigations=[],
                        orthodoxy_approved=True
                    ),
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Deduct cash
            new_cash = current_cash - total_cost
            cur.execute(
                "UPDATE shadow_cash_accounts SET current_cash = %s WHERE user_id = %s",
                (new_cash, user_id)
            )
            
            # Update or insert position (FIFO cost basis)
            cur.execute(
                "SELECT quantity, cost_basis FROM shadow_positions WHERE user_id = %s AND ticker = %s",
                (user_id, ticker)
            )
            existing = cur.fetchone()
            
            if existing:
                # Update existing position (weighted average cost basis)
                old_qty, old_cost_basis = existing
                new_qty = old_qty + quantity
                new_cost_basis = ((old_cost_basis * Decimal(str(old_qty))) + (Decimal(str(fill_price)) * Decimal(str(quantity)))) / Decimal(str(new_qty))
                
                cur.execute(
                    """
                    UPDATE shadow_positions
                    SET quantity = %s, cost_basis = %s, last_updated = NOW()
                    WHERE user_id = %s AND ticker = %s
                    """,
                    (new_qty, new_cost_basis, user_id, ticker)
                )
            else:
                # Insert new position
                cur.execute(
                    """
                    INSERT INTO shadow_positions (user_id, ticker, quantity, cost_basis, total_cost, unrealized_pnl, first_purchase_date)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (user_id, ticker, quantity, fill_price, total_cost, 0.0)
                )
            
            # Log transaction
            cur.execute(
                """
                INSERT INTO shadow_transactions (transaction_id, user_id, ticker, transaction_type, quantity, price, total_value, realized_pnl)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), user_id, ticker, "buy", quantity, fill_price, total_cost, 0.0)
            )
            
            # Insert order record
            cur.execute(
                """
                INSERT INTO shadow_orders (order_id, user_id, ticker, side, quantity, status, fill_price, slippage, commission, market_hours)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (order_id, user_id, ticker, "buy", quantity, "filled", fill_price, slippage_pct, 0.0, True)
            )
            
            self.pg.connection.commit()
        
        logger.info(f"✅ BUY executed: {quantity} {ticker} @ ${fill_price:.2f} (total: ${total_cost:.2f})")
        
        return OrderResult(
            status=OrderStatus.FILLED,
            order_id=order_id,
            ticker=ticker,
            side=OrderSide.BUY,
            quantity=quantity,
            fill_price=fill_price,
            total_cost=total_cost,
            new_cash_balance=new_cash,
            message=f"Successfully bought {quantity} shares of {ticker} at ${fill_price:.2f}",
            rejection_reason=None,
            conclave_event_id=None,
            slippage_pct=slippage_pct,
            agent_reasoning="Buy order approved and executed",
            risk_assessment=RiskAssessment(
                risk_score=0.0,
                risk_category="low",
                concerns=[],
                mitigations=[],
                orthodoxy_approved=True
            ),
            timestamp=datetime.now(timezone.utc)
        )
    
    async def _execute_sell(
        self,
        user_id: str,
        ticker: str,
        quantity: int,
        fill_price: float,
        slippage_pct: float
    ) -> OrderResult:
        """Execute SELL order: add cash, reduce/remove position, calculate realized P&L (FIFO)"""
        
        order_id = str(uuid.uuid4())
        total_proceeds = Decimal(str(fill_price)) * Decimal(str(quantity))
        
        with self.pg.connection.cursor() as cur:
            # Get current position
            cur.execute(
                "SELECT quantity, cost_basis FROM shadow_positions WHERE user_id = %s AND ticker = %s",
                (user_id, ticker)
            )
            row = cur.fetchone()
            if not row:
                return OrderResult(
                    status=OrderStatus.REJECTED,
                    order_id=order_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    quantity=quantity,
                    fill_price=fill_price,
                    total_cost=None,
                    new_cash_balance=None,
                    message=f"No position found for {ticker}",
                    rejection_reason=RejectionReason.INSUFFICIENT_SHARES,
                    conclave_event_id=None,
                    slippage_pct=slippage_pct,
                    agent_reasoning="Position not found",
                    risk_assessment=RiskAssessment(
                        risk_score=0.0,
                        risk_category="low",
                        concerns=["No position"],
                        mitigations=[],
                        orthodoxy_approved=True
                    ),
                    timestamp=datetime.now(timezone.utc)
                )
            
            current_qty, cost_basis = row
            
            if current_qty < quantity:
                return OrderResult(
                    status=OrderStatus.REJECTED,
                    order_id=order_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    quantity=quantity,
                    fill_price=fill_price,
                    total_cost=None,
                    new_cash_balance=None,
                    message=f"Insufficient shares: need {quantity}, have {current_qty}",
                    rejection_reason=RejectionReason.INSUFFICIENT_SHARES,
                    conclave_event_id=None,
                    slippage_pct=slippage_pct,
                    agent_reasoning="Insufficient shares",
                    risk_assessment=RiskAssessment(
                        risk_score=0.0,
                        risk_category="low",
                        concerns=["Insufficient shares"],
                        mitigations=[],
                        orthodoxy_approved=True
                    ),
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Calculate realized P&L (FIFO)
            realized_pnl = (Decimal(str(fill_price)) - cost_basis) * Decimal(str(quantity))
            
            # Update position
            new_qty = current_qty - quantity
            
            if new_qty == 0:
                # Remove position
                cur.execute(
                    "DELETE FROM shadow_positions WHERE user_id = %s AND ticker = %s",
                    (user_id, ticker)
                )
            else:
                # Reduce quantity (cost basis stays same under FIFO)
                cur.execute(
                    """
                    UPDATE shadow_positions
                    SET quantity = %s, last_updated = NOW()
                    WHERE user_id = %s AND ticker = %s
                    """,
                    (new_qty, user_id, ticker)
                )
            
            # Add cash
            cur.execute(
                "SELECT current_cash FROM shadow_cash_accounts WHERE user_id = %s",
                (user_id,)
            )
            current_cash = cur.fetchone()[0]
            new_cash = current_cash + total_proceeds
            
            cur.execute(
                "UPDATE shadow_cash_accounts SET current_cash = %s WHERE user_id = %s",
                (new_cash, user_id)
            )
            
            # Log transaction
            cur.execute(
                """
                INSERT INTO shadow_transactions (transaction_id, user_id, ticker, transaction_type, quantity, price, total_value, realized_pnl)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), user_id, ticker, "sell", quantity, fill_price, total_proceeds, realized_pnl)
            )
            
            # Insert order record
            cur.execute(
                """
                INSERT INTO shadow_orders (order_id, user_id, ticker, side, quantity, status, fill_price, slippage, commission, market_hours)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (order_id, user_id, ticker, "sell", quantity, "filled", fill_price, slippage_pct, 0.0, True)
            )
            
            self.pg.connection.commit()
        
        logger.info(f"✅ SELL executed: {quantity} {ticker} @ ${fill_price:.2f} (P&L: ${realized_pnl:+.2f})")
        
        return OrderResult(
            status=OrderStatus.FILLED,
            order_id=order_id,
            ticker=ticker,
            side=OrderSide.SELL,
            quantity=quantity,
            fill_price=fill_price,
            total_cost=None,
            new_cash_balance=new_cash,
            message=f"Successfully sold {quantity} shares of {ticker} at ${fill_price:.2f} (P&L: ${realized_pnl:+.2f})",
            rejection_reason=None,
            conclave_event_id=None,
            slippage_pct=slippage_pct,
            agent_reasoning=f"Sell order approved and executed (realized P&L: ${realized_pnl:+.2f})",
            risk_assessment=RiskAssessment(
                risk_score=0.0,
                risk_category="low",
                concerns=[],
                mitigations=[],
                orthodoxy_approved=True
            ),
            timestamp=datetime.now(timezone.utc)
        )
    
    async def _publish_trade_event(self, result: OrderResult) -> str:
        """
        Publish trade event to Synaptic Conclave (Sacred Order: Truth).
        
        Event type: shadow_trade_executed
        Channel: cognitive_bus:events
        """
        event_id = str(uuid.uuid4())
        
        event = {
            "event_id": event_id,
            "event_type": "shadow_trade_executed",
            "source": "shadow_broker_agent",
            "timestamp": result.timestamp.isoformat(),
            "data": {
                "order_id": result.order_id,
                "ticker": result.ticker,
                "side": result.side.value,
                "quantity": result.quantity,
                "fill_price": float(result.fill_price),  # Convert Decimal to float
                "total_cost": float(result.total_cost),  # Convert Decimal to float
                "slippage_pct": result.slippage_pct,
                "agent_reasoning": result.agent_reasoning,
                "risk_score": result.risk_assessment.risk_score,
                "risk_category": result.risk_assessment.risk_category
            }
        }
        
        # Publish to Redis cognitive_bus:events (synchronous)
        self.redis_bus.publish("cognitive_bus:events", event)
        
        logger.info(f"📡 Published to Synaptic Conclave: {event_id}")
        
        return event_id
    
    async def _embed_trade_pattern(self, result: OrderResult):
        """
        Embed trade pattern to Qdrant for learning (Sacred Order: Memory).
        
        Collection: shadow_trade_patterns
        Embedding: [ticker, side, quantity, fill_price, risk_score, ...]
        """
        # TODO: Implement Qdrant embedding
        # This will enable the agent to learn from past trades and improve reasoning
        pass
    
    async def _archive_to_vault(self, result: OrderResult):
        """
        Archive trade to Vault Keepers (Sacred Order: Truth).
        
        All trades are versioned and immutable.
        """
        # TODO: Implement Vault Keepers archival
        pass
    
    # ========================================================================
    # PORTFOLIO SNAPSHOT
    # ========================================================================
    
    async def get_portfolio_snapshot(self, user_id: str) -> PortfolioSnapshot:
        """
        Get real-time portfolio snapshot with P&L calculation.
        
        Includes:
        - Cash balance
        - All positions with current prices
        - Unrealized P&L
        - Total P&L
        - Sector allocation
        - Risk metrics
        - Agent insights (AI-generated suggestions)
        """
        with self.pg.connection.cursor() as cur:
            # Get cash balance
            cur.execute(
                "SELECT current_cash FROM shadow_cash_accounts WHERE user_id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            cash_balance = float(row[0]) if row else 0.0
            
            # Get all positions
            cur.execute(
                """
                SELECT ticker, quantity, cost_basis, unrealized_pnl, first_purchase_date
                FROM shadow_positions
                WHERE user_id = %s
                ORDER BY ticker
                """,
                (user_id,)
            )
            positions_raw = cur.fetchall()
        
        positions = []
        total_unrealized_pnl = 0.0
        
        # Enrich positions with current prices
        for ticker, quantity, cost_basis, _, first_purchase_date in positions_raw:
            try:
                quote = await self.market_data.get_current_price(ticker)
                current_price = quote.price
                market_value = float(current_price) * float(quantity)
                unrealized_pnl = (float(current_price) - float(cost_basis)) * float(quantity)
                
                positions.append({
                    "ticker": ticker,
                    "quantity": float(quantity),
                    "cost_basis": float(cost_basis),
                    "current_price": current_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_pct": (unrealized_pnl / (float(cost_basis) * float(quantity))) * 100,
                    "first_purchase_date": first_purchase_date.isoformat()
                })
                
                total_unrealized_pnl += unrealized_pnl
                
            except Exception as e:
                logger.error(f"❌ Failed to fetch price for {ticker}: {e}")
                # Use cost basis as fallback
                market_value = float(cost_basis) * float(quantity)
                positions.append({
                    "ticker": ticker,
                    "quantity": float(quantity),
                    "cost_basis": float(cost_basis),
                    "current_price": float(cost_basis),
                    "market_value": market_value,
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_pct": 0.0,
                    "first_purchase_date": first_purchase_date.isoformat()
                })
        
        # Calculate total value
        total_positions_value = sum(float(p["market_value"]) for p in positions)
        total_value = float(cash_balance) + total_positions_value
        
        # Get realized P&L from transactions
        with self.pg.connection.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(SUM(realized_pnl), 0) FROM shadow_transactions WHERE user_id = %s",
                (user_id,)
            )
            total_realized_pnl = float(cur.fetchone()[0])
        
        total_pnl = total_realized_pnl + total_unrealized_pnl
        
        # TODO: Calculate sector allocation (requires ticker metadata)
        sector_allocation = {}
        
        # TODO: Calculate risk metrics (Sharpe, beta, VaR)
        risk_metrics = {}
        
        # Generate agent insights (AI-powered suggestions)
        agent_insights = await self._generate_portfolio_insights(positions, total_value, cash_balance)
        
        snapshot = PortfolioSnapshot(
            user_id=user_id,
            cash_balance=cash_balance,
            positions=positions,
            total_value=total_value,
            unrealized_pnl=total_unrealized_pnl,
            total_pnl=total_pnl,
            num_positions=len(positions),
            sector_allocation=sector_allocation,
            risk_metrics=risk_metrics,
            agent_insights=agent_insights,
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(f"📊 Portfolio snapshot: ${total_value:.2f} ({len(positions)} positions, P&L: ${total_pnl:+.2f})")
        
        return snapshot
    
    async def _generate_portfolio_insights(
        self,
        positions: List[Dict[str, Any]],
        total_value: float,
        cash_balance: float
    ) -> List[str]:
        """
        Generate AI-powered portfolio insights and suggestions.
        
        Insights:
        - Concentration risk
        - Underperforming positions
        - Cash allocation suggestions
        - Diversification recommendations
        """
        insights = []
        
        if not positions:
            insights.append("Portfolio vuoto. Considera di iniziare con 2-3 posizioni diversificate.")
            return insights
        
        # Check concentration risk
        for pos in positions:
            weight_pct = (float(pos["market_value"]) / float(total_value)) * 100
            if weight_pct > 40:
                insights.append(f"⚠️ Alta concentrazione in {pos['ticker']} ({weight_pct:.1f}%). Considera di diversificare.")
        
        # Check underperformers
        for pos in positions:
            if pos["unrealized_pnl_pct"] < -20:
                insights.append(f"⚠️ {pos['ticker']} in perdita del {pos['unrealized_pnl_pct']:.1f}%. Valuta stop loss.")
        
        # Check cash allocation
        cash_pct = (float(cash_balance) / float(total_value)) * 100
        if cash_pct > 50:
            insights.append(f"💰 Cash elevato ({cash_pct:.1f}%). Considera nuove opportunità di investimento.")
        elif cash_pct < 5:
            insights.append(f"⚠️ Cash basso ({cash_pct:.1f}%). Mantieni almeno 10-15% di liquidità.")
        
        # Check diversification
        if len(positions) < 3:
            insights.append("📊 Portafoglio poco diversificato. Target: 5-10 posizioni.")
        
        return insights


# ============================================================================
# MAIN (for testing)
# ============================================================================

async def main():
    """Test the Shadow Broker Agent"""
    agent = ShadowBrokerAgent()
    await agent.initialize()
    
    # Test: Get portfolio snapshot
    snapshot = await agent.get_portfolio_snapshot("test_user")
    print(f"\n📊 Portfolio: ${snapshot.total_value:.2f}")
    print(f"Positions: {snapshot.num_positions}")
    print(f"P&L: ${snapshot.total_pnl:+.2f}")
    
    if snapshot.agent_insights:
        print("\n🤖 Agent Insights:")
        for insight in snapshot.agent_insights:
            print(f"  - {insight}")
    
    # Test: Buy order
    print("\n🤖 Executing BUY order...")
    result = await agent.execute_market_order(
        user_id="test_user",
        ticker="AAPL",
        side=OrderSide.BUY,
        quantity=10
    )
    print(f"Status: {result.status.value}")
    print(f"Message: {result.message}")
    if result.agent_reasoning:
        print(f"Agent Reasoning: {result.agent_reasoning}")


if __name__ == "__main__":
    asyncio.run(main())
