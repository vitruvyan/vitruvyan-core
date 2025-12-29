"""
📚 Scholastic - The Renaissance Academic Analyst

Named after medieval scholastics who synthesized knowledge from multiple sources,
this Codex Hunter calculates academic factors (Fama-French style) from fundamental data.

Historical Context:
Scholastics like Thomas Aquinas integrated philosophy, theology, and empirical observation
to create comprehensive knowledge systems. Similarly, Scholastic integrates multiple
fundamental metrics to create factor scores.

Responsibilities:
- Calculate Value factor (Earnings Yield = 1/PE)
- Calculate Growth factor (EPS growth YoY)
- Calculate Size factor (log market cap)
- Calculate Quality factor (ROE)
- Calculate Momentum factor (12-month return)
- Store results in PostgreSQL factor_scores table

Integration Strategy:
Uses raw SQL for INSERT (no PostgresAgent modification required).
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime, date

from core.foundation.persistence.postgres_agent import PostgresAgent

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
    
    scholastic_factors_calculated = Counter(
        'scholastic_factors_calculated_total',
        'Total factors calculated',
        ['status']
    )
    scholastic_batch_duration = Histogram(
        'scholastic_batch_duration_seconds',
        'Factor calculation batch duration'
    )
    scholastic_tickers_processed = Gauge(
        'scholastic_tickers_processed',
        'Number of tickers processed in last batch'
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

logger = logging.getLogger(__name__)


class Scholastic:
    """
    Academic factor calculation engine for Codex Hunters.
    
    Calculates Fama-French style factors from yfinance fundamental data.
    Stores results directly to factor_scores table using raw SQL.
    """
    
    def __init__(self, user_id: str = "scholastic"):
        """
        Initialize Scholastic hunter.
        
        Args:
            user_id: Identifier for logging attribution
        """
        self.user_id = user_id
        self.name = "Scholastic"
        self.postgres_agent = PostgresAgent()
        logger.info(f"📚 {self.name} initialized (user_id={user_id})")
    
    def execute(
        self,
        normalized_data: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate academic factors for normalized market data.
        
        Args:
            normalized_data: List of ticker dictionaries from Restorer
                Expected structure:
                {
                    "ticker": "AAPL",
                    "info": {
                        "trailingPE": 25.5,
                        "earningsGrowth": 0.15,
                        "marketCap": 2500000000000,
                        "returnOnEquity": 0.35,
                        ...
                    },
                    "history": [...],  # For momentum calculation
                    "source": "yfinance"
                }
            batch_size: Number of tickers to process before checkpointing
        
        Returns:
            {
                "processed": int,
                "successful": int,
                "failed": int,
                "errors": List[Dict],
                "duration_seconds": float
            }
        """
        start_time = datetime.now()
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "tickers_processed": []
        }
        
        logger.info(f"📚 Scholastic starting expedition on {len(normalized_data)} tickers")
        
        for idx, ticker_data in enumerate(normalized_data):
            ticker = ticker_data.get("ticker", "UNKNOWN")
            
            try:
                # Validate required data
                if "info" not in ticker_data:
                    raise ValueError(f"No info data for {ticker}")
                
                # Calculate all factors
                factors = self._calculate_factors(ticker_data)
                
                if factors:
                    # Store using raw SQL
                    self._store_factors(ticker, factors)
                    
                    results["successful"] += 1
                    results["tickers_processed"].append(ticker)
                    logger.info(f"✅ {ticker} factors calculated and stored")
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "ticker": ticker,
                        "error": "Insufficient data for factor calculation"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "ticker": ticker,
                    "error": str(e)
                })
                logger.error(f"❌ Error processing {ticker}: {e}")
            
            results["processed"] += 1
            
            # Checkpoint progress
            if (idx + 1) % batch_size == 0:
                logger.info(f"📊 Checkpoint: {idx + 1}/{len(normalized_data)} tickers processed")
        
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration
        
        # Update Prometheus metrics
        if METRICS_ENABLED:
            scholastic_factors_calculated.labels(status="success").inc(results["successful"])
            scholastic_factors_calculated.labels(status="failed").inc(results["failed"])
            scholastic_batch_duration.observe(duration)
            scholastic_tickers_processed.set(results["processed"])
        
        logger.info(
            f"📚 Scholastic expedition complete: "
            f"{results['successful']}/{results['processed']} successful "
            f"in {duration:.2f}s"
        )
        
        return results
    
    def _calculate_factors(self, ticker_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Calculate all academic factors.
        
        Args:
            ticker_data: Normalized ticker data from Restorer
        
        Returns:
            Dictionary with value, growth, size, quality, momentum scores or None
        """
        ticker = ticker_data.get("ticker", "UNKNOWN")
        info = ticker_data.get("info", {})
        history = ticker_data.get("history", [])
        
        try:
            # 1. VALUE FACTOR: Earnings Yield (1/PE ratio)
            pe = info.get('trailingPE', 0)
            if pe and pe > 0:
                value_score = (1.0 / pe) * 100  # Convert to percentage
            else:
                value_score = 0.0
            
            # 2. GROWTH FACTOR: EPS growth YoY (already in percentage)
            earnings_growth = info.get('earningsGrowth')
            if earnings_growth is not None:
                growth_score = earnings_growth * 100  # Convert to percentage
            else:
                growth_score = 0.0
            
            # 3. SIZE FACTOR: log(market cap)
            market_cap = info.get('marketCap', 0)
            if market_cap and market_cap > 0:
                size_score = np.log10(market_cap)  # log10 for better scale
            else:
                size_score = 0.0
            
            # 4. QUALITY FACTOR: Return on Equity (ROE)
            roe = info.get('returnOnEquity')
            if roe is not None:
                quality_score = roe * 100  # Convert to percentage
            else:
                quality_score = 0.0
            
            # 5. MOMENTUM FACTOR: 12-month return
            momentum_score = 0.0
            if history and len(history) >= 252:  # Need at least 252 trading days (1 year)
                try:
                    # Sort by date to ensure correct order
                    sorted_history = sorted(history, key=lambda x: x.get('date', ''))
                    
                    current_price = float(sorted_history[-1].get('close', 0))
                    year_ago_price = float(sorted_history[-252].get('close', 0))
                    
                    if year_ago_price > 0:
                        momentum_score = ((current_price / year_ago_price) - 1) * 100  # Percentage return
                except (ValueError, KeyError, IndexError) as e:
                    logger.warning(f"⚠️  {ticker}: Could not calculate momentum - {e}")
                    momentum_score = 0.0
            
            # Validate at least some factors are available
            if all(score == 0.0 for score in [value_score, growth_score, size_score, quality_score, momentum_score]):
                logger.warning(f"⚠️  {ticker}: All factors are zero")
                return None
            
            return {
                "value": value_score,
                "growth": growth_score,
                "size": size_score,
                "quality": quality_score,
                "momentum": momentum_score
            }
            
        except Exception as e:
            logger.error(f"❌ Factor calculation error for {ticker}: {e}")
            return None
    
    def _store_factors(self, ticker: str, factors: Dict[str, float]) -> None:
        """
        Store factors in factor_scores table using raw SQL.
        
        Args:
            ticker: Stock ticker symbol
            factors: Dictionary with value, growth, size, quality, momentum scores
        """
        try:
            today = date.today()
            
            with self.postgres_agent.connection.cursor() as cur:
                # UPSERT into factor_scores (respects unique constraint on ticker, date)
                cur.execute("""
                    INSERT INTO factor_scores 
                    (ticker, date, value, growth, size, quality, momentum)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        value = EXCLUDED.value,
                        growth = EXCLUDED.growth,
                        size = EXCLUDED.size,
                        quality = EXCLUDED.quality,
                        momentum = EXCLUDED.momentum,
                        created_at = CURRENT_TIMESTAMP
                """, (
                    ticker,
                    today,
                    factors["value"],
                    factors["growth"],
                    factors["size"],
                    factors["quality"],
                    factors["momentum"]
                ))
            
            self.postgres_agent.connection.commit()
            logger.debug(f"📊 Factors stored for {ticker}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store factors for {ticker}: {e}")
            # Rollback on error
            self.postgres_agent.connection.rollback()
            raise


if __name__ == "__main__":
    # Example usage (for testing)
    logging.basicConfig(level=logging.INFO)
    
    # Mock normalized data
    mock_data = [{
        "ticker": "AAPL",
        "info": {
            "trailingPE": 25.5,
            "earningsGrowth": 0.15,
            "marketCap": 2500000000000,
            "returnOnEquity": 0.35
        },
        "history": [
            {"date": f"2024-{i//30+1:02d}-{i%30+1:02d}", "close": 150+i*0.1}
            for i in range(260)  # 260 days
        ],
        "source": "yfinance"
    }]
    
    scholastic = Scholastic()
    result = scholastic.execute(mock_data)
    print(f"\n📚 Scholastic Test Result:\n{result}")
