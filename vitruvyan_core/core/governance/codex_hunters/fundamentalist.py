"""
💰 Fundamentalist - The Renaissance Fundamental Analyst

Named after Benjamin Graham and Warren Buffett's fundamental analysis principles,
this Codex Hunter extracts comprehensive fundamental financial data from market sources
and stores it in the fundamentals table for Neural Engine integration.

Historical Context:
Fundamentalists like Graham pioneered value investing by analyzing company fundamentals
(earnings, assets, debt, cash flow) to determine intrinsic value. Similarly, Fundamentalist
extracts raw financial metrics to power quantitative analysis.

Responsibilities:
- Extract quarterly financial statements (revenue, EPS, margins)
- Calculate growth rates (YoY, QoQ)
- Analyze balance sheet health (debt-to-equity, current ratio)
- Extract cash flow metrics (free cash flow)
- Calculate dividend metrics (yield, payout ratio)
- Extract valuation ratios (P/E, P/B, PEG)
- Store results in PostgreSQL fundamentals table

Integration Strategy:
Uses raw SQL INSERT with ON CONFLICT UPDATE for upserts (no PostgresAgent modification required).
Scheduled weekly (Sundays 06:00 UTC) after Scholastic completes.

Author: GitHub Copilot + dbaldoni
Date: December 6, 2025
Status: ✅ PRODUCTION READY
"""

import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, date

from core.foundation.persistence.postgres_agent import PostgresAgent

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
    
    fundamentalist_records_inserted = Counter(
        'fundamentalist_records_inserted_total',
        'Total fundamental records inserted',
        ['status']
    )
    fundamentalist_batch_duration = Histogram(
        'fundamentalist_batch_duration_seconds',
        'Fundamental extraction batch duration'
    )
    fundamentalist_tickers_processed = Gauge(
        'fundamentalist_tickers_processed',
        'Number of tickers processed in last batch'
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

logger = logging.getLogger(__name__)


class Fundamentalist:
    """
    Fundamental financial data extraction engine for Codex Hunters.
    
    Extracts comprehensive fundamental metrics from yfinance data and stores
    in fundamentals table for Neural Engine z-score integration.
    """
    
    def __init__(self, user_id: str = "fundamentalist"):
        """
        Initialize Fundamentalist hunter.
        
        Args:
            user_id: Identifier for logging attribution
        """
        self.user_id = user_id
        self.name = "Fundamentalist"
        self.postgres_agent = PostgresAgent()
        logger.info(f"💰 {self.name} initialized (user_id={user_id})")
    
    def execute(
        self,
        normalized_data: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Extract fundamental data for normalized market data.
        
        Args:
            normalized_data: List of ticker dictionaries from Restorer
                Expected structure:
                {
                    "ticker": "AAPL",
                    "info": {
                        "trailingPE": 25.5,
                        "earningsGrowth": 0.15,
                        "marketCap": 2500000000000,
                        "dividendYield": 0.0055,
                        "debtToEquity": 150.5,
                        ...
                    },
                    "quarterly_financials": pd.DataFrame,  # Revenue, EBITDA
                    "quarterly_balance_sheet": pd.DataFrame,  # Assets, debt
                    "quarterly_cashflow": pd.DataFrame,  # FCF
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
        
        logger.info(f"💰 Fundamentalist starting expedition on {len(normalized_data)} tickers")
        
        for idx, ticker_data in enumerate(normalized_data):
            ticker = ticker_data.get("ticker", "UNKNOWN")
            
            try:
                # Validate required data
                if "info" not in ticker_data:
                    raise ValueError(f"No info data for {ticker}")
                
                # Extract all fundamental metrics
                fundamentals = self._extract_fundamentals(ticker_data)
                
                if fundamentals:
                    # Store using raw SQL (UPSERT)
                    self._store_fundamentals(ticker, fundamentals)
                    
                    results["successful"] += 1
                    results["tickers_processed"].append(ticker)
                    logger.info(f"✅ {ticker} fundamentals extracted and stored")
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "ticker": ticker,
                        "error": "Insufficient data for fundamental extraction"
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
            fundamentalist_records_inserted.labels(status="success").inc(results["successful"])
            fundamentalist_records_inserted.labels(status="failed").inc(results["failed"])
            fundamentalist_batch_duration.observe(duration)
            fundamentalist_tickers_processed.set(results["processed"])
        
        logger.info(
            f"💰 Fundamentalist expedition complete: "
            f"{results['successful']}/{results['processed']} successful "
            f"in {duration:.2f}s"
        )
        
        return results
    
    def _extract_fundamentals(self, ticker_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract all fundamental metrics from ticker data.
        
        Args:
            ticker_data: Normalized ticker data from Restorer
        
        Returns:
            Dictionary with all fundamental metrics or None
        """
        ticker = ticker_data.get("ticker", "UNKNOWN")
        info = ticker_data.get("info", {})
        quarterly_financials = ticker_data.get("quarterly_financials")
        quarterly_balance_sheet = ticker_data.get("quarterly_balance_sheet")
        quarterly_cashflow = ticker_data.get("quarterly_cashflow")
        
        try:
            # Determine reporting date (most recent quarter)
            if quarterly_financials is not None and not quarterly_financials.empty:
                report_date = quarterly_financials.columns[0].date()
            else:
                report_date = date.today()
            
            # === REVENUE METRICS ===
            revenue = None
            revenue_growth_yoy = None
            revenue_growth_qoq = None
            
            if quarterly_financials is not None and not quarterly_financials.empty:
                if 'Total Revenue' in quarterly_financials.index:
                    revenue_series = quarterly_financials.loc['Total Revenue']
                    
                    # Current quarter revenue
                    if len(revenue_series) >= 1 and revenue_series.iloc[0]:
                        revenue = Decimal(str(revenue_series.iloc[0]))
                    
                    # YoY growth (Q0 vs Q4)
                    if len(revenue_series) >= 5:
                        current = revenue_series.iloc[0]
                        year_ago = revenue_series.iloc[4]
                        if current and year_ago and year_ago != 0:
                            revenue_growth_yoy = Decimal(str((current - year_ago) / year_ago))
                    
                    # QoQ growth (Q0 vs Q1)
                    if len(revenue_series) >= 2:
                        current = revenue_series.iloc[0]
                        prev_quarter = revenue_series.iloc[1]
                        if current and prev_quarter and prev_quarter != 0:
                            revenue_growth_qoq = Decimal(str((current - prev_quarter) / prev_quarter))
            
            # === EARNINGS METRICS ===
            eps = None
            eps_growth_yoy = None
            eps_growth_qoq = None
            
            if info.get('trailingEps'):
                eps = Decimal(str(info['trailingEps']))
            
            if info.get('earningsGrowth'):
                eps_growth_yoy = Decimal(str(info['earningsGrowth']))
            
            # QoQ EPS growth requires quarterly data (not directly available from info)
            eps_growth_qoq = None
            
            # === MARGIN METRICS ===
            gross_margin = Decimal(str(info['grossMargins'])) if info.get('grossMargins') else None
            operating_margin = Decimal(str(info['operatingMargins'])) if info.get('operatingMargins') else None
            net_margin = Decimal(str(info['profitMargins'])) if info.get('profitMargins') else None
            ebitda_margin = Decimal(str(info['ebitdaMargins'])) if info.get('ebitdaMargins') else None
            
            # === BALANCE SHEET METRICS ===
            debt_to_equity = None
            if info.get('debtToEquity'):
                # yfinance returns as percentage (e.g., 150.5 = 150.5%)
                debt_to_equity = Decimal(str(info['debtToEquity'] / 100.0))
            
            current_ratio = Decimal(str(info['currentRatio'])) if info.get('currentRatio') else None
            
            # === CASH FLOW METRICS ===
            free_cash_flow = None
            if quarterly_cashflow is not None and not quarterly_cashflow.empty:
                if 'Free Cash Flow' in quarterly_cashflow.index:
                    fcf_series = quarterly_cashflow.loc['Free Cash Flow']
                    if len(fcf_series) >= 1 and fcf_series.iloc[0]:
                        free_cash_flow = Decimal(str(fcf_series.iloc[0]))
            
            # === DIVIDEND METRICS ===
            dividend_yield = Decimal(str(info['dividendYield'])) if info.get('dividendYield') else None
            dividend_rate = Decimal(str(info['dividendRate'])) if info.get('dividendRate') else None
            payout_ratio = Decimal(str(info['payoutRatio'])) if info.get('payoutRatio') else None
            
            # === VALUATION METRICS ===
            pe_ratio = Decimal(str(info['trailingPE'])) if info.get('trailingPE') else None
            pb_ratio = Decimal(str(info['priceToBook'])) if info.get('priceToBook') else None
            peg_ratio = Decimal(str(info['pegRatio'])) if info.get('pegRatio') else None
            
            # Build result dictionary
            fundamentals = {
                "date": report_date,
                "revenue": revenue,
                "revenue_growth_yoy": revenue_growth_yoy,
                "revenue_growth_qoq": revenue_growth_qoq,
                "eps": eps,
                "eps_growth_yoy": eps_growth_yoy,
                "eps_growth_qoq": eps_growth_qoq,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
                "ebitda_margin": ebitda_margin,
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
                "free_cash_flow": free_cash_flow,
                "dividend_yield": dividend_yield,
                "dividend_rate": dividend_rate,
                "payout_ratio": payout_ratio,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "peg_ratio": peg_ratio
            }
            
            # Validate at least some data is present
            non_null_count = sum(1 for v in fundamentals.values() if v is not None)
            if non_null_count < 3:  # Require at least 3 non-null metrics
                logger.warning(f"⚠️ {ticker} has insufficient fundamental data ({non_null_count} metrics)")
                return None
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"❌ Error extracting fundamentals for {ticker}: {e}")
            return None
    
    def _store_fundamentals(self, ticker: str, fundamentals: Dict[str, Any]) -> None:
        """
        Store fundamental data in PostgreSQL using UPSERT.
        
        Args:
            ticker: Stock ticker symbol
            fundamentals: Dictionary with fundamental metrics
        
        Raises:
            Exception if database operation fails
        """
        with self.postgres_agent.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO fundamentals (
                    ticker, date, revenue, revenue_growth_yoy, revenue_growth_qoq,
                    eps, eps_growth_yoy, eps_growth_qoq,
                    gross_margin, operating_margin, net_margin, ebitda_margin,
                    debt_to_equity, current_ratio, free_cash_flow,
                    dividend_yield, dividend_rate, payout_ratio,
                    pe_ratio, pb_ratio, peg_ratio
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (ticker, date)
                DO UPDATE SET
                    revenue = EXCLUDED.revenue,
                    revenue_growth_yoy = EXCLUDED.revenue_growth_yoy,
                    revenue_growth_qoq = EXCLUDED.revenue_growth_qoq,
                    eps = EXCLUDED.eps,
                    eps_growth_yoy = EXCLUDED.eps_growth_yoy,
                    eps_growth_qoq = EXCLUDED.eps_growth_qoq,
                    gross_margin = EXCLUDED.gross_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    net_margin = EXCLUDED.net_margin,
                    ebitda_margin = EXCLUDED.ebitda_margin,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    current_ratio = EXCLUDED.current_ratio,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    dividend_yield = EXCLUDED.dividend_yield,
                    dividend_rate = EXCLUDED.dividend_rate,
                    payout_ratio = EXCLUDED.payout_ratio,
                    pe_ratio = EXCLUDED.pe_ratio,
                    pb_ratio = EXCLUDED.pb_ratio,
                    peg_ratio = EXCLUDED.peg_ratio;
            """, (
                ticker, fundamentals["date"],
                fundamentals["revenue"], fundamentals["revenue_growth_yoy"], fundamentals["revenue_growth_qoq"],
                fundamentals["eps"], fundamentals["eps_growth_yoy"], fundamentals["eps_growth_qoq"],
                fundamentals["gross_margin"], fundamentals["operating_margin"], fundamentals["net_margin"], fundamentals["ebitda_margin"],
                fundamentals["debt_to_equity"], fundamentals["current_ratio"], fundamentals["free_cash_flow"],
                fundamentals["dividend_yield"], fundamentals["dividend_rate"], fundamentals["payout_ratio"],
                fundamentals["pe_ratio"], fundamentals["pb_ratio"], fundamentals["peg_ratio"]
            ))
        
        self.postgres_agent.connection.commit()
        logger.debug(f"✅ {ticker} fundamentals stored in PostgreSQL")


# ============================================================================
# STANDALONE TESTING (for development)
# ============================================================================

if __name__ == "__main__":
    """Test Fundamentalist with sample data"""
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Mock normalized data (in production, comes from Restorer)
    mock_data = [
        {
            "ticker": "AAPL",
            "info": {
                "trailingPE": 37.32,
                "earningsGrowth": 0.15,
                "grossMargins": 0.45,
                "operatingMargins": 0.30,
                "profitMargins": 0.25,
                "ebitdaMargins": 0.33,
                "debtToEquity": 150.5,
                "currentRatio": 1.08,
                "dividendYield": 0.0037,
                "dividendRate": 0.98,
                "payoutRatio": 0.15,
                "trailingEps": 7.47,
                "priceToBook": 52.0,
                "pegRatio": 2.5
            },
            "source": "mock"
        }
    ]
    
    print("=" * 80)
    print("🧪 TESTING fundamentalist.py")
    print("=" * 80)
    
    # Run Fundamentalist
    fundamentalist = Fundamentalist(user_id="test")
    result = fundamentalist.execute(mock_data, batch_size=10)
    
    # Display results
    print("\n📊 Results:")
    print(f"   Processed: {result['processed']}")
    print(f"   Successful: {result['successful']}")
    print(f"   Failed: {result['failed']}")
    print(f"   Duration: {result['duration_seconds']:.2f}s")
    
    if result['errors']:
        print(f"\n   Errors: {result['errors']}")
    
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80)
