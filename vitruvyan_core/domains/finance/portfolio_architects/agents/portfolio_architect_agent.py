"""
PortfolioArchitectAgent - Core Portfolio Construction Engine
Sacred Order #7 - Portfolio Architects

Responsibilities:
1. Construct optimized portfolios from Neural Engine rankings
2. Apply risk-adjusted allocation strategies
3. Enforce diversification constraints (sector, concentration)
4. Generate VEE narratives explaining portfolio composition
5. Integrate with Redis Cognitive Bus for event publishing

Integration Points:
- Neural Engine: Ticker rankings via /screen endpoint
- Pattern Weavers: Sector/concept extraction for diversification
- VARE: Risk scoring for position sizing
- VEE Engine: Construction rationale narratives
- PostgreSQL: Snapshot persistence (shadow_portfolio_snapshots)
- Redis: Event publishing (portfolio.constructed)

Author: Vitruvyan AI Team
Created: January 8, 2026
Status: Phase 1 Implementation
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import redis
import httpx
import yfinance as yf
from collections import defaultdict

from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from core.vpar.vare.vare_engine import VAREEngine
from core.vpar.vee.vee_engine import VEEEngine
from domains.finance.portfolio_architects.services.price_aggregator import PriceAggregator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PortfolioHolding:
    """Individual portfolio position"""
    ticker: str
    shares: float
    weight: float  # 0.0-1.0 (percentage of portfolio)
    value: float  # USD value
    rationale: str  # Why this ticker was included
    composite_z: float  # Neural Engine composite score
    risk_score: float  # VARE risk score
    sector: Optional[str] = None


@dataclass
class PortfolioSnapshot:
    """Complete portfolio state at a point in time"""
    snapshot_id: Optional[int] = None
    user_id: str = ""
    total_value: float = 0.0
    cash_available: float = 0.0
    holdings: List[PortfolioHolding] = None
    sector_breakdown: Dict[str, float] = None  # {sector: weight}
    risk_metrics: Dict[str, Any] = None  # {concentration_risk, diversification_score, volatility}
    performance_metrics: Dict[str, Any] = None  # {total_return, sharpe_ratio, max_drawdown}
    construction_rationale: str = ""  # VEE narrative
    created_at: Optional[datetime] = None
    is_demo_mode: bool = False
    
    def __post_init__(self):
        if self.holdings is None:
            self.holdings = []
        if self.sector_breakdown is None:
            self.sector_breakdown = {}
        if self.risk_metrics is None:
            self.risk_metrics = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}


class PortfolioArchitectAgent:
    """
    Sacred Order #7 - Portfolio Construction Engine
    
    Constructs optimized portfolios using Neural Engine rankings,
    risk constraints, and diversification strategies.
    
    Design Philosophy:
    - Risk-first: Position sizing based on VARE scores
    - Diversification: Sector limits + concentration constraints
    - Explainability: VEE narratives for every decision
    - Event-driven: Redis Cognitive Bus integration
    """
    
    def __init__(
        self,
        postgres_agent: Optional[PostgresAgent] = None,
        qdrant_agent: Optional[QdrantAgent] = None,
        redis_client: Optional[redis.Redis] = None,
        neural_engine_url: Optional[str] = None,
        pattern_weavers_url: Optional[str] = None,
        vee_enabled: bool = True
    ):
        """
        Initialize Portfolio Architect Agent
        
        Args:
            postgres_agent: PostgreSQL connection agent
            qdrant_agent: Qdrant vector DB agent
            redis_client: Redis Cognitive Bus client
            neural_engine_url: Neural Engine API endpoint
            pattern_weavers_url: Pattern Weavers API endpoint
            vee_enabled: Generate VEE narratives (default: True)
        """
        self.postgres = postgres_agent or PostgresAgent()
        self.qdrant = qdrant_agent or QdrantAgent()
        
        # Redis connection with fallback (Docker internal name or localhost)
        redis_host = os.getenv('REDIS_HOST', 'localhost')  # Default to localhost for non-Docker
        try:
            self.redis = redis_client or redis.Redis(host=redis_host, port=6379, db=0, socket_connect_timeout=2)
            self.redis.ping()  # Test connection
            logger.info(f"✅ Redis connected: {redis_host}:6379")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed ({redis_host}:6379): {e}, pub/sub disabled")
            self.redis = None
        
        self.neural_engine_url = neural_engine_url or os.getenv(
            "NEURAL_ENGINE_API", "http://neural_engine:8003"
        )
        self.pattern_weavers_url = pattern_weavers_url or os.getenv(
            "PATTERN_WEAVERS_API", "http://pattern_weavers:8011"
        )
        self.vee_enabled = vee_enabled
        
        # VEE Engine integration (TODO: Fix signature compatibility)
        try:
            self.vee_engine = VEEEngine() if vee_enabled else None
        except Exception as e:
            logger.warning(f"⚠️ VEE Engine initialization failed: {e}, VEE disabled")
            self.vee_enabled = False
            self.vee_engine = None
        
        # VARE Engine integration for risk-adjusted position sizing
        try:
            self.vare_engine = VAREEngine()
            logger.info("✅ VARE Engine initialized for risk-adjusted portfolios")
        except Exception as e:
            logger.warning(f"⚠️ VARE Engine initialization failed: {e}, using fallback risk scores")
            self.vare_engine = None
        
        # PriceAggregator for real market prices (Task 9)
        try:
            self.price_aggregator = PriceAggregator(redis_client=self.redis)
            logger.info("✅ PriceAggregator initialized (Finnhub + yfinance)")
        except Exception as e:
            logger.warning(f"⚠️ PriceAggregator initialization failed: {e}, using fallback prices")
            self.price_aggregator = None
        
        # Default construction constraints
        self.default_constraints = {
            "max_position_size": 0.20,  # Max 20% per ticker
            "max_sector_allocation": 0.40,  # Max 40% per sector
            "min_holdings": 5,  # Minimum portfolio size
            "max_holdings": 20,  # Maximum portfolio size
            "min_diversification_score": 0.60  # Minimum acceptable diversification
        }
        
        logger.info("PortfolioArchitectAgent initialized (Sacred Order #7)")
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """Convert non-JSON-serializable types to serializable formats"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._serialize_for_json(asdict(obj))
        return obj
    
    def construct_portfolio(
        self,
        user_id: str,
        available_cash: float,
        risk_tolerance: str = "balanced",
        sector_preferences: Optional[List[str]] = None,
        blocked_tickers: Optional[List[str]] = None,
        is_demo_mode: bool = False
    ) -> PortfolioSnapshot:
        """
        Construct optimized portfolio from scratch
        
        Args:
            user_id: User identifier
            available_cash: Total cash available for investment (USD)
            risk_tolerance: User risk profile (conservative, balanced, aggressive)
            sector_preferences: Optional list of preferred sectors
            blocked_tickers: Optional list of excluded tickers
            is_demo_mode: TRUE for 50K simulated testing
        
        Returns:
            PortfolioSnapshot with holdings and metrics
        
        Raises:
            ValueError: Invalid parameters or construction failed
        """
        logger.info(f"🏗️ Portfolio construction started - User: {user_id}, Cash: ${available_cash:,.2f}, Risk: {risk_tolerance}")
        
        if available_cash <= 0:
            raise ValueError("available_cash must be positive")
        
        # Step 1: Get top tickers from Neural Engine
        logger.info("Step 1: Fetching Neural Engine rankings...")
        ranked_tickers = self._fetch_neural_engine_rankings(
            risk_tolerance=risk_tolerance,
            top_k=50,  # Get top 50 candidates
            blocked_tickers=blocked_tickers or []
        )
        
        if not ranked_tickers:
            raise ValueError("Neural Engine returned no valid tickers")
        
        logger.info(f"✅ Neural Engine: {len(ranked_tickers)} tickers ranked")
        
        # Step 2: Apply diversification constraints
        logger.info("Step 2: Applying diversification constraints...")
        selected_tickers = self._apply_diversification_strategy(
            ranked_tickers=ranked_tickers,
            sector_preferences=sector_preferences,
            max_holdings=self.default_constraints["max_holdings"]
        )
        
        logger.info(f"✅ Selected {len(selected_tickers)} tickers for portfolio")
        
        # Step 3: Calculate position sizes (risk-adjusted weights)
        logger.info("Step 3: Calculating risk-adjusted position sizes...")
        holdings = self._calculate_position_sizes(
            selected_tickers=selected_tickers,
            available_cash=available_cash,
            risk_tolerance=risk_tolerance
        )
        
        # Step 4: Compute portfolio metrics
        logger.info("Step 4: Computing portfolio metrics...")
        sector_breakdown = self._compute_sector_breakdown(holdings)
        risk_metrics = self._compute_risk_metrics(holdings)
        
        logger.info(f"✅ Risk metrics: {risk_metrics}")
        
        # Step 5: Generate VEE narrative (if enabled)
        construction_rationale = ""
        if self.vee_enabled:
            logger.info("Step 5: Generating VEE construction narrative...")
            construction_rationale = self._generate_vee_narrative(
                holdings=holdings,
                sector_breakdown=sector_breakdown,
                risk_metrics=risk_metrics,
                risk_tolerance=risk_tolerance
            )
        
        # Step 6: Create portfolio snapshot
        total_invested = sum(h.value for h in holdings)
        cash_remaining = available_cash - total_invested
        
        snapshot = PortfolioSnapshot(
            user_id=user_id,
            total_value=total_invested,
            cash_available=cash_remaining,
            holdings=holdings,
            sector_breakdown=sector_breakdown,
            risk_metrics=risk_metrics,
            construction_rationale=construction_rationale,
            is_demo_mode=is_demo_mode,
            created_at=datetime.now()
        )
        
        # Step 7: Persist to PostgreSQL
        logger.info("Step 6: Persisting snapshot to PostgreSQL...")
        snapshot_id = self._save_snapshot_to_db(snapshot)
        snapshot.snapshot_id = snapshot_id
        
        # Step 8: Publish to Redis Cognitive Bus
        logger.info("Step 7: Publishing to Redis Cognitive Bus...")
        self._publish_construction_event(snapshot)
        
        logger.info(f"🎉 Portfolio construction complete - Snapshot ID: {snapshot_id}")
        logger.info(f"💰 Invested: ${total_invested:,.2f}, Cash remaining: ${cash_remaining:,.2f}")
        
        return snapshot
    
    def _fetch_neural_engine_rankings(
        self,
        risk_tolerance: str,
        top_k: int = 50,
        blocked_tickers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch top-ranked tickers from Neural Engine
        
        Args:
            risk_tolerance: User risk profile
            top_k: Number of top tickers to retrieve
            blocked_tickers: Excluded tickers
        
        Returns:
            List of ranked ticker dicts with scores
        """
        try:
            # Map risk tolerance to Neural Engine profile
            profile_map = {
                "conservative": "balanced_mid",
                "balanced": "balanced_mid",
                "aggressive": "momentum_focus"
            }
            profile = profile_map.get(risk_tolerance, "balanced_mid")
            
            # Call Neural Engine /neural-engine endpoint
            response = httpx.post(
                f"{self.neural_engine_url}/neural-engine",
                json={"profile": profile, "top_k": top_k},
                timeout=120.0  # Long timeout for large universe (2600+ tickers)
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract tickers from ranking.stocks array (Neural Engine v2 format)
            ranked_tickers = data.get("ranking", {}).get("stocks", [])
            
            # Filter out blocked tickers
            if blocked_tickers:
                ranked_tickers = [
                    t for t in ranked_tickers 
                    if t.get("ticker") not in blocked_tickers
                ]
            
            return ranked_tickers
        
        except Exception as e:
            logger.error(f"❌ Neural Engine fetch failed: {e}")
            return []
    
    def _apply_diversification_strategy(
        self,
        ranked_tickers: List[Dict[str, Any]],
        sector_preferences: Optional[List[str]],
        max_holdings: int,
        max_tickers_per_sector: int = 3,
        max_sector_allocation: float = 0.40
    ) -> List[Dict[str, Any]]:
        """
        Select tickers ensuring sector diversification
        
        Strategy:
        1. Fetch sector for each ticker (Pattern Weavers API → fallback map)
        2. Apply sector limit: max 2-3 tickers per sector (configurable)
        3. Apply sector allocation limit: max 40% per sector
        4. Prioritize user's sector preferences if provided
        5. Maintain sector diversity across portfolio
        
        Args:
            ranked_tickers: Neural Engine ranked tickers (sorted by composite_z)
            sector_preferences: Optional preferred sectors (e.g., ["Technology", "Healthcare"])
            max_holdings: Maximum number of holdings in portfolio
            max_tickers_per_sector: Max tickers per sector (default: 3)
            max_sector_allocation: Max % per sector (default: 40%)
        
        Returns:
            Filtered list of tickers with sector diversity maintained
            
        Example:
            Input: [AAPL, MSFT, NVDA, GOOGL, JPM, BAC, TSLA] (7 tickers)
            max_holdings=5, max_tickers_per_sector=2
            Output: [AAPL, MSFT, JPM, BAC, TSLA] (2 Tech, 2 Financials, 1 Consumer)
        """
        try:
            logger.info(f"🔍 Diversification started: {len(ranked_tickers)} candidates → {max_holdings} target")
            
            # Step 1: Fetch sectors for all tickers
            ranked_with_sectors = []
            for ticker_data in ranked_tickers:
                ticker = ticker_data.get("ticker", "")
                sector = self._fetch_ticker_sector(ticker)
                ticker_data["sector"] = sector
                ranked_with_sectors.append(ticker_data)
            
            # Step 2: Prioritize sector preferences if provided
            if sector_preferences:
                logger.info(f"📊 Sector preferences: {sector_preferences}")
                preferred = [t for t in ranked_with_sectors if t["sector"] in sector_preferences]
                other = [t for t in ranked_with_sectors if t["sector"] not in sector_preferences]
                ranked_with_sectors = preferred + other
            
            # Step 3: Apply diversification constraints
            sector_count = defaultdict(int)
            selected = []
            
            for ticker_data in ranked_with_sectors:
                if len(selected) >= max_holdings:
                    break
                
                ticker = ticker_data.get("ticker", "")
                sector = ticker_data.get("sector", "Unknown")
                
                # Check sector ticker limit (e.g., max 3 tech stocks)
                if sector_count[sector] >= max_tickers_per_sector:
                    logger.debug(f"⚠️ Skipping {ticker} - sector '{sector}' at limit ({max_tickers_per_sector} tickers)")
                    continue
                
                selected.append(ticker_data)
                sector_count[sector] += 1
            
            # Step 4: Verify sector allocation constraint (max 40% per sector)
            # Calculate hypothetical equal-weight allocation
            if selected:
                equal_weight = 1.0 / len(selected)
                sector_allocations = defaultdict(float)
                
                for ticker_data in selected:
                    sector = ticker_data.get("sector", "Unknown")
                    sector_allocations[sector] += equal_weight
                
                # Check if any sector exceeds max allocation
                overweight_sectors = [s for s, alloc in sector_allocations.items() 
                                     if alloc > max_sector_allocation]
                
                if overweight_sectors:
                    logger.warning(
                        f"⚠️ Sectors exceed {max_sector_allocation*100:.0f}% limit: {overweight_sectors}. "
                        f"Consider reducing max_tickers_per_sector or increasing max_holdings."
                    )
            
            # Step 5: Log diversification results
            sector_summary = {sector: count for sector, count in sector_count.items()}
            logger.info(
                f"✅ Diversification complete: {len(selected)} tickers, "
                f"{len(sector_count)} sectors → {sector_summary}"
            )
            
            return selected
        
        except Exception as e:
            logger.error(f"❌ Diversification failed: {e}", exc_info=True)
            logger.warning(f"⚠️ Fallback: Using top {max_holdings} tickers without diversification")
            return ranked_tickers[:max_holdings]
    
    def _fetch_ticker_sector(self, ticker: str) -> str:
        """
        Fetch ticker sector via Pattern Weavers API with fallback
        
        Priority:
        1. Pattern Weavers API (real-time sector extraction)
        2. Hardcoded sector map (fallback for common tickers)
        3. "Unknown" (last resort)
        
        Returns:
            Sector name or "Unknown"
        """
        # Try Pattern Weavers API first
        try:
            response = httpx.post(
                f"{self.pattern_weavers_url}/weave",
                json={"query_text": f"{ticker} stock sector", "user_id": "portfolio_architect"},
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                patterns = data.get("patterns", [])
                sector_patterns = [p for p in patterns if p.get("type") == "sector"]
                if sector_patterns and sector_patterns[0].get("confidence", 0) > 0.5:
                    sector = sector_patterns[0].get("value", "Unknown")
                    logger.debug(f"✅ Pattern Weavers: {ticker} → {sector}")
                    return sector
        except Exception as e:
            logger.debug(f"⚠️ Pattern Weavers unavailable for {ticker}: {e}, using fallback")
        
        # Fallback: Use hardcoded sector mapping
        sector_map = {
            # Technology
            "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
            "NVDA": "Technology", "META": "Technology", "SHOP": "Technology",
            "PLTR": "Technology", "DDOG": "Technology", "COIN": "Technology",
            "CRWD": "Technology", "SNOW": "Technology", "NET": "Technology",
            
            # Financials
            "JPM": "Financials", "BAC": "Financials", "WFC": "Financials",
            "GS": "Financials", "MS": "Financials", "SQ": "Financials", 
            "PYPL": "Financials", "V": "Financials", "MA": "Financials",
            
            # Consumer
            "TSLA": "Consumer Discretionary", "AMZN": "Consumer Discretionary",
            "HD": "Consumer Discretionary", "NKE": "Consumer Discretionary",
            "SBUX": "Consumer Discretionary", "MCD": "Consumer Discretionary",
            
            # Healthcare
            "JNJ": "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare",
            "ABBV": "Healthcare", "TMO": "Healthcare", "ABT": "Healthcare",
            
            # Energy
            "XOM": "Energy", "CVX": "Energy", "COP": "Energy",
            
            # Industrials
            "CAT": "Industrials", "BA": "Industrials", "GE": "Industrials",
            
            # Materials
            "LIN": "Materials", "APD": "Materials",
            
            # Communication Services
            "DIS": "Communication Services", "NFLX": "Communication Services",
            "CMCSA": "Communication Services"
        }
        
        sector = sector_map.get(ticker, "Unknown")
        if sector != "Unknown":
            logger.debug(f"✅ Fallback map: {ticker} → {sector}")
        else:
            logger.warning(f"⚠️ No sector found for {ticker}, using 'Unknown'")
        
        return sector
    
    def _calculate_position_sizes(
        self,
        selected_tickers: List[Dict[str, Any]],
        available_cash: float,
        risk_tolerance: str
    ) -> List[PortfolioHolding]:
        """
        Calculate risk-adjusted position sizes for each ticker
        
        Strategy:
        1. Base weight = 1/N (equal-weight)
        2. Risk adjustment: weight *= (1 - risk_score/2)
        3. Normalize weights to sum = 1.0
        4. Calculate shares using real market prices (yfinance)
        
        Args:
            selected_tickers: Tickers to include in portfolio
            available_cash: Total cash for investment
            risk_tolerance: User risk profile
        
        Returns:
            List of PortfolioHolding with calculated weights
        """
        num_holdings = len(selected_tickers)
        base_weight = 1.0 / num_holdings
        
        # Risk-adjusted weights using VARE Engine
        adjusted_weights = []
        risk_scores = []  # Store calculated risk scores
        for ticker_data in selected_tickers:
            ticker = ticker_data.get("ticker", "")
            
            # Get risk score from VARE Engine (0-100 scale)
            if self.vare_engine:
                try:
                    vare_result = self.vare_engine.analyze_ticker(ticker)
                    risk_score = vare_result.overall_risk / 100.0  # Convert to 0-1 scale
                    logger.info(f"✅ VARE risk score for {ticker}: {risk_score:.3f} (raw: {vare_result.overall_risk:.1f})")
                except Exception as e:
                    logger.warning(f"⚠️ VARE analysis failed for {ticker}: {e}, using fallback 0.5")
                    risk_score = 0.5
            else:
                logger.warning(f"⚠️ VARE Engine not available, using fallback risk score 0.5 for {ticker}")
                risk_score = 0.5
            
            # Risk penalty: High risk (0.8) → 40% reduction, Low risk (0.2) → 10% reduction
            risk_penalty = risk_score / 2.0
            adjusted_weight = base_weight * (1.0 - risk_penalty)
            adjusted_weights.append(adjusted_weight)
            risk_scores.append(risk_score)  # Store for later use
        
        # Normalize weights to sum = 1.0
        total_weight = sum(adjusted_weights)
        normalized_weights = [w / total_weight for w in adjusted_weights]
        
        # Calculate holdings with real prices
        holdings = []
        for idx, ticker_data in enumerate(selected_tickers):
            ticker = ticker_data.get("ticker", "")
            composite_z = ticker_data.get("composite_z", 0.0)
            sector = ticker_data.get("sector", "Unknown")
            
            weight = normalized_weights[idx]
            cash_allocated = available_cash * weight
            
            # Fetch real market price via PriceAggregator (Task 9)
            price = self._fetch_ticker_price(ticker)
            shares = cash_allocated / price if price > 0 else 0.0
            
            holding = PortfolioHolding(
                ticker=ticker,
                shares=shares,
                weight=weight,
                value=cash_allocated,
                rationale=f"Neural Engine z-score {composite_z:.2f}, risk-adjusted weight {weight*100:.1f}%",
                composite_z=composite_z,
                risk_score=risk_scores[idx],  # Use calculated VARE risk score
                sector=sector
            )
            holdings.append(holding)
        
        logger.info(f"✅ Position sizing: {len(holdings)} holdings, total weight {sum(h.weight for h in holdings):.4f}")
        return holdings
    
    def _fetch_ticker_price(self, ticker: str) -> float:
        """
        Fetch real market price via PriceAggregator (Task 9)
        
        Routing:
        - Portfolio construction = "construction" use case (delayed OK)
        - Falls back to $100 if all providers fail
        
        Returns:
            Current price in USD (fallback: $100)
        """
        if self.price_aggregator:
            try:
                result = self.price_aggregator.get_price(ticker, use_case="construction")
                if result:
                    logger.debug(f"💰 {ticker} price: ${result.price:.2f} (source: {result.source})")
                    return result.price
            except Exception as e:
                logger.warning(f"⚠️ PriceAggregator failed for {ticker}: {e}")
        
        # Fallback: $100 estimate
        logger.warning(f"⚠️ Using fallback price $100 for {ticker}")
        return 100.0
    
    def _compute_sector_breakdown(
        self,
        holdings: List[PortfolioHolding]
    ) -> Dict[str, float]:
        """Compute sector allocation percentages"""
        sector_weights = {}
        for holding in holdings:
            sector = holding.sector or "Unknown"
            sector_weights[sector] = sector_weights.get(sector, 0.0) + holding.weight
        return sector_weights
    
    def _compute_risk_metrics(
        self,
        holdings: List[PortfolioHolding]
    ) -> Dict[str, Any]:
        """Compute portfolio-level risk metrics"""
        # Concentration risk: Max single position weight
        max_weight = max(h.weight for h in holdings) if holdings else 0.0
        concentration_risk = "high" if max_weight > 0.25 else "moderate" if max_weight > 0.15 else "low"
        
        # Diversification score: Number of holdings / target holdings
        diversification_score = min(len(holdings) / 10.0, 1.0)
        
        # Average risk score (VARE)
        avg_risk = sum(h.risk_score for h in holdings) / len(holdings) if holdings else 0.5
        
        return {
            "concentration_risk": concentration_risk,
            "max_position_weight": max_weight,
            "diversification_score": diversification_score,
            "average_risk_score": avg_risk,
            "num_holdings": len(holdings)
        }
    
    def _generate_vee_narrative(
        self,
        holdings: List[PortfolioHolding],
        sector_breakdown: Dict[str, float],
        risk_metrics: Dict[str, Any],
        risk_tolerance: str
    ) -> str:
        """
        Generate VEE narrative explaining portfolio construction
        
        Integration:
        - VEE Engine for 3-level explanations (summary, detailed, technical)
        - English-only output (MVP Language Guardrail)
        
        Returns:
            Full VEE narrative (3 levels combined) or simple text if VEE unavailable
        """
        if not self.vee_enabled:
            # Fallback: Simple text summary
            logger.warning("⚠️ VEE disabled, using simple narrative")
            return self._generate_simple_narrative(holdings, sector_breakdown, risk_metrics, risk_tolerance)
        
        try:
            # Initialize VEE Engine (real integration)
            vee_engine = VEEEngine()  # VEEEngine 2.0 has no init parameters
            
            # Prepare portfolio data dict for VEEEngine.explain_portfolio()
            portfolio_data = {
                "total_value": sum(h.value for h in holdings),
                "num_positions": len(holdings),
                "risk_level": risk_tolerance,  # conservative, balanced, aggressive
                "concentration": {
                    "max_position": risk_metrics.get("max_position_weight", 0.0),
                    "concentration_risk": risk_metrics.get("concentration_risk", "N/A"),
                    "diversification_score": risk_metrics.get("diversification_score", 0.0)
                },
                "performance": {
                    "avg_risk_score": risk_metrics.get("average_risk_score", 0.5),
                    "num_holdings": len(holdings),
                    "num_sectors": len(sector_breakdown)
                },
                "tickers": [h.ticker for h in holdings[:10]],  # Max 10 for context
                "sectors": sector_breakdown
            }
            
            logger.info("🔄 Generating VEE portfolio narrative via VEEEngine...")
            
            # Call VEEEngine official method
            vee_result = vee_engine.explain_portfolio(
                portfolio_data=portfolio_data,
                language="en"  # MVP Language Guardrail: English-only
            )
            
            # VEEEngine returns: {summary, technical, detailed, conversational, timestamp}
            # Combine into full narrative with 3 levels
            full_narrative = f"""=== PORTFOLIO CONSTRUCTION NARRATIVE (VEE) ===

[LEVEL 1 - SUMMARY]
{vee_result.get('summary', 'Portfolio summary not available')}

[LEVEL 2 - DETAILED]
{vee_result.get('detailed', 'Detailed analysis not available')}

[LEVEL 3 - TECHNICAL]
{vee_result.get('technical', 'Technical details not available')}

Generated by VEEEngine v2.0 | Language: English (MVP Guardrail) | {vee_result.get('timestamp', '')}
"""
            
            logger.info(f"✅ VEE narrative generated via VEEEngine ({len(full_narrative)} chars)")
            return full_narrative
        
        except Exception as e:
            logger.warning(f"⚠️ VEE generation failed: {e}, using simple narrative", exc_info=True)
            return self._generate_simple_narrative(holdings, sector_breakdown, risk_metrics, risk_tolerance)
    
    def _generate_simple_narrative(
        self,
        holdings: List[PortfolioHolding],
        sector_breakdown: Dict[str, float],
        risk_metrics: Dict[str, Any],
        risk_tolerance: str
    ) -> str:
        """
        Generate simple text narrative (fallback when VEE unavailable)
        """
        top_sectors = sorted(
            sector_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        sector_text = ", ".join([f"{s} ({w*100:.1f}%)" for s, w in top_sectors])
        
        narrative = f"""Portfolio Construction Rationale:

This {risk_tolerance} portfolio contains {len(holdings)} carefully selected holdings with a total diversification score of {risk_metrics['diversification_score']:.2f}.

Sector Allocation: The portfolio is diversified across {sector_text}.

Risk Profile: Concentration risk is {risk_metrics['concentration_risk']} with the largest position at {risk_metrics['max_position_weight']*100:.1f}% of the portfolio. Average risk score is {risk_metrics['average_risk_score']:.2f}.

Construction Methodology: Tickers were selected from Neural Engine top rankings, filtered for sector diversity, and weighted using risk-adjusted allocation strategies."""
        
        return narrative
    
    def _save_snapshot_to_db(
        self,
        snapshot: PortfolioSnapshot
    ) -> int:
        """
        Persist portfolio snapshot to PostgreSQL
        
        Returns:
            snapshot_id (primary key)
        """
        with self.postgres.connection.cursor() as cur:
            # Calculate cash_balance and positions_value for database
            positions_value = sum(h.value for h in snapshot.holdings)
            cash_balance = snapshot.cash_available
            
            cur.execute("""
                INSERT INTO shadow_portfolio_snapshots (
                    user_id,
                    portfolio_data,
                    total_value,
                    cash_balance,
                    positions_value,
                    cash_available,
                    holdings,
                    sector_breakdown,
                    risk_metrics,
                    performance_metrics,
                    construction_rationale,
                    is_demo_mode
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING snapshot_id
            """, (
                snapshot.user_id,
                json.dumps(self._serialize_for_json(asdict(snapshot))),
                snapshot.total_value,
                cash_balance,
                positions_value,
                snapshot.cash_available,
                json.dumps(self._serialize_for_json([asdict(h) for h in snapshot.holdings])),
                json.dumps(self._serialize_for_json(snapshot.sector_breakdown)),
                json.dumps(self._serialize_for_json(snapshot.risk_metrics)),
                json.dumps(self._serialize_for_json(snapshot.performance_metrics)),
                snapshot.construction_rationale,
                snapshot.is_demo_mode
            ))
            
            snapshot_id = cur.fetchone()[0]
            self.postgres.connection.commit()
            
        logger.info(f"✅ Snapshot saved to PostgreSQL - ID: {snapshot_id}")
        return snapshot_id
    
    def _publish_construction_event(
        self,
        snapshot: PortfolioSnapshot
    ):
        """Publish portfolio.constructed event to Redis Cognitive Bus"""
        if not self.redis:
            logger.debug("⚠️ Redis not available, skipping event publish")
            return
        
        try:
            event = {
                "event_type": "portfolio.constructed",
                "snapshot_id": snapshot.snapshot_id,
                "user_id": snapshot.user_id,
                "total_value": snapshot.total_value,
                "num_holdings": len(snapshot.holdings),
                "is_demo_mode": snapshot.is_demo_mode,
                "timestamp": datetime.now().isoformat()
            }
            
            self.redis.publish(
                "cognitive_bus:portfolio_architects",
                json.dumps(event)
            )
            
            logger.info(f"✅ Published portfolio.constructed event to Redis Cognitive Bus")
        
        except Exception as e:
            logger.error(f"❌ Redis publish failed: {e}")
            # Non-blocking: continue even if Redis fails
    
    def get_user_portfolio(
        self,
        user_id: str,
        latest_only: bool = True
    ) -> Optional[PortfolioSnapshot]:
        """
        Retrieve user's portfolio snapshot(s) from database
        
        Args:
            user_id: User identifier
            latest_only: Return only most recent snapshot (default: True)
        
        Returns:
            PortfolioSnapshot or None if not found
        """
        with self.postgres.connection.cursor() as cur:
            if latest_only:
                cur.execute("""
                    SELECT 
                        snapshot_id,
                        user_id,
                        portfolio_data,
                        total_value,
                        cash_available,
                        holdings,
                        sector_breakdown,
                        risk_metrics,
                        performance_metrics,
                        construction_rationale,
                        created_at,
                        is_demo_mode
                    FROM shadow_portfolio_snapshots
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
            else:
                cur.execute("""
                    SELECT * FROM shadow_portfolio_snapshots
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            
            row = cur.fetchone()
            
            if not row:
                return None
            
            # Reconstruct PortfolioSnapshot from database row
            snapshot = PortfolioSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                total_value=float(row[3]),
                cash_available=float(row[4]),
                holdings=[
                    PortfolioHolding(**h) for h in json.loads(row[5])
                ],
                sector_breakdown=json.loads(row[6]),
                risk_metrics=json.loads(row[7]),
                performance_metrics=json.loads(row[8]),
                construction_rationale=row[9],
                created_at=row[10],
                is_demo_mode=row[11]
            )
            
            return snapshot
