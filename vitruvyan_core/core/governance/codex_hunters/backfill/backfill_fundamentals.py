#!/usr/bin/env python3
"""
Vitruvyan Fundamentals Backfill Script
======================================

Standalone script to backfill fundamentals table with comprehensive financial data.
Uses yfinance API to fetch quarterly financial statements, balance sheets, and cash flow data.

Usage:
    python3 scripts/backfill_fundamentals.py [--limit N] [--tickers AAPL,MSFT] [--batch-size 50]

Author: GitHub Copilot + dbaldoni
Date: December 6, 2025
Status: ✅ PRODUCTION READY
"""

import sys
import os
import argparse
import logging
from datetime import datetime
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.foundation.persistence.postgres_agent import PostgresAgent
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def get_active_tickers(limit: int = None, tickers_filter: list = None) -> list:
    """
    Retrieve active tickers from PostgreSQL.
    
    Args:
        limit: Maximum number of tickers to return
        tickers_filter: Specific tickers to process (overrides DB query)
    
    Returns:
        List of ticker symbols
    """
    if tickers_filter:
        logger.info(f"Using manual ticker list: {tickers_filter}")
        return tickers_filter
    
    pg = PostgresAgent()
    with pg.connection.cursor() as cur:
        sql = "SELECT ticker FROM tickers WHERE active = true ORDER BY ticker ASC"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        cur.execute(sql)
        tickers = [row[0] for row in cur.fetchall()]
    
    logger.info(f"Loaded {len(tickers)} active tickers from PostgreSQL")
    return tickers


def fetch_yfinance_data(ticker: str) -> dict:
    """
    Fetch comprehensive data from yfinance for a single ticker.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with info, quarterly_financials, quarterly_balance_sheet, quarterly_cashflow
    """
    try:
        logger.info(f"📊 Fetching yfinance data for {ticker}...")
        stock = yf.Ticker(ticker)
        
        return {
            "ticker": ticker,
            "info": stock.info,
            "quarterly_financials": stock.quarterly_financials,
            "quarterly_balance_sheet": stock.quarterly_balance_sheet,
            "quarterly_cashflow": stock.quarterly_cashflow,
            "source": "yfinance"
        }
    except Exception as e:
        logger.error(f"❌ Failed to fetch {ticker}: {e}")
        return None


def store_fundamentals(pg: PostgresAgent, ticker: str, fundamentals: dict) -> bool:
    """Store fundamentals in PostgreSQL using UPSERT."""
    try:
        with pg.connection.cursor() as cur:
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
                    peg_ratio = EXCLUDED.peg_ratio
            """, (
                ticker, fundamentals['date'],
                fundamentals['revenue'], fundamentals['revenue_growth_yoy'], fundamentals['revenue_growth_qoq'],
                fundamentals['eps'], fundamentals['eps_growth_yoy'], fundamentals['eps_growth_qoq'],
                fundamentals['gross_margin'], fundamentals['operating_margin'], fundamentals['net_margin'], fundamentals['ebitda_margin'],
                fundamentals['debt_to_equity'], fundamentals['current_ratio'], fundamentals['free_cash_flow'],
                fundamentals['dividend_yield'], fundamentals['dividend_rate'], fundamentals['payout_ratio'],
                fundamentals['pe_ratio'], fundamentals['pb_ratio'], fundamentals['peg_ratio']
            ))
        pg.connection.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Failed to store {ticker}: {e}")
        pg.connection.rollback()
        return False


def extract_fundamentals(ticker: str, data: dict) -> dict:
    """Extract fundamentals from yfinance data."""
    from decimal import Decimal
    
    info = data.get('info', {})
    qf = data.get('quarterly_financials')
    qbs = data.get('quarterly_balance_sheet')
    qcf = data.get('quarterly_cashflow')
    
    # Get latest quarter date
    report_date = datetime.now().date()
    if qf is not None and not qf.empty:
        report_date = qf.columns[0].date()
    
    # Extract metrics (simplified version - add full logic if needed)
    revenue = Decimal(str(info['totalRevenue'])) if info.get('totalRevenue') else None
    eps = Decimal(str(info['trailingEps'])) if info.get('trailingEps') else None
    pe_ratio = Decimal(str(info['trailingPE'])) if info.get('trailingPE') else None
    
    # FIX: yfinance sometimes returns dividend_yield as percentage (0-100) instead of decimal (0-1)
    # Normalize to decimal format for database storage
    dividend_yield_raw = Decimal(str(info['dividendYield'])) if info.get('dividendYield') else None
    dividend_yield = dividend_yield_raw / 100 if dividend_yield_raw and dividend_yield_raw > 1.0 else dividend_yield_raw
    dividend_rate = Decimal(str(info['dividendRate'])) if info.get('dividendRate') else None
    payout_ratio = Decimal(str(info['payoutRatio'])) if info.get('payoutRatio') else None
    pb_ratio = Decimal(str(info['priceToBook'])) if info.get('priceToBook') else None
    peg_ratio = Decimal(str(info['pegRatio'])) if info.get('pegRatio') else None
    
    # Margins
    gross_margin = Decimal(str(info['grossMargins'])) if info.get('grossMargins') else None
    operating_margin = Decimal(str(info['operatingMargins'])) if info.get('operatingMargins') else None
    net_margin = Decimal(str(info['profitMargins'])) if info.get('profitMargins') else None
    ebitda_margin = Decimal(str(info['ebitdaMargins'])) if info.get('ebitdaMargins') else None
    
    # Balance sheet
    debt_to_equity = Decimal(str(info['debtToEquity'])) if info.get('debtToEquity') else None
    current_ratio = Decimal(str(info['currentRatio'])) if info.get('currentRatio') else None
    
    # Cash flow
    free_cash_flow = Decimal(str(info['freeCashflow'])) if info.get('freeCashflow') else None
    
    # Growth metrics (FIXED Dec 7, 2025: use yfinance info fields)
    revenue_growth_yoy = Decimal(str(info['revenueGrowth'])) if info.get('revenueGrowth') is not None else None
    eps_growth_yoy = Decimal(str(info['earningsGrowth'])) if info.get('earningsGrowth') is not None else None
    
    return {
        "date": report_date,
        "revenue": revenue,
        "revenue_growth_yoy": revenue_growth_yoy,
        "revenue_growth_qoq": None,  # Not available from yfinance info
        "eps": eps,
        "eps_growth_yoy": eps_growth_yoy,
        "eps_growth_qoq": None,  # Not available from yfinance info
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


def backfill_fundamentals(
    tickers: list,
    batch_size: int = 50,
    sleep_between_batches: int = 5
) -> dict:
    """
    Backfill fundamentals table for list of tickers.
    
    Args:
        tickers: List of ticker symbols
        batch_size: Number of tickers to process before checkpointing
        sleep_between_batches: Seconds to sleep between batches (rate limiting)
    
    Returns:
        Dictionary with summary statistics
    """
    start_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("💰 FUNDAMENTALS BACKFILL STARTED")
    logger.info("=" * 80)
    logger.info(f"Total tickers: {len(tickers)}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Sleep between batches: {sleep_between_batches}s")
    logger.info("")
    
    pg = PostgresAgent()
    
    total_processed = 0
    total_successful = 0
    total_failed = 0
    all_errors = []
    
    # Process in batches
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(tickers) + batch_size - 1) // batch_size
        
        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH {batch_num}/{total_batches}: Processing {len(batch)} tickers")
        logger.info(f"{'='*80}")
        
        # Process each ticker
        for ticker in batch:
            try:
                data = fetch_yfinance_data(ticker)
                if not data:
                    total_failed += 1
                    all_errors.append(f"{ticker}: No data")
                    continue
                
                fundamentals = extract_fundamentals(ticker, data)
                if store_fundamentals(pg, ticker, fundamentals):
                    total_successful += 1
                    logger.info(f"✅ {ticker}")
                else:
                    total_failed += 1
                    all_errors.append(f"{ticker}: Store failed")
                
                total_processed += 1
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                total_failed += 1
                all_errors.append(f"{ticker}: {str(e)}")
                logger.error(f"❌ {ticker}: {e}")
                total_processed += 1
        
        # Batch summary
        batch_success = total_successful - (total_processed - len(batch))
        logger.info(f"\n✅ Batch {batch_num} complete:")
        logger.info(f"   - Successful: {batch_success}/{len(batch)}")
        logger.info(f"   - Failed: {len(batch) - batch_success}")
        
        # Sleep between batches (except last one)
        if i + batch_size < len(tickers):
            logger.info(f"\n😴 Sleeping {sleep_between_batches}s before next batch...")
            time.sleep(sleep_between_batches)
    
    # Calculate summary
    duration = (datetime.now() - start_time).total_seconds()
    success_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
    
    logger.info("\n" + "=" * 80)
    logger.info("💰 FUNDAMENTALS BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Successful: {total_successful} ({success_rate:.1f}%)")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Duration: {duration:.2f}s ({duration/60:.1f} minutes)")
    logger.info(f"Throughput: {total_processed/duration:.2f} tickers/second")
    
    if all_errors:
        logger.warning(f"\n⚠️ Failed tickers ({len(all_errors)}):")
        for error in all_errors[:10]:  # Show first 10 errors
            logger.warning(f"   - {error}")
        if len(all_errors) > 10:
            logger.warning(f"   ... and {len(all_errors) - 10} more")
    
    logger.info("\n" + "=" * 80)
    
    return {
        "total_processed": total_processed,
        "successful": total_successful,
        "failed": total_failed,
        "success_rate": success_rate,
        "duration_seconds": duration,
        "errors": all_errors
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Backfill fundamentals table with comprehensive financial data"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tickers to process (for testing)"
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default="",
        help="Comma-separated list of specific tickers to process (e.g., AAPL,MSFT,TSLA)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of tickers per batch (default: 50)"
    )
    parser.add_argument(
        "--sleep",
        type=int,
        default=5,
        help="Seconds to sleep between batches (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Get tickers
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',') if t.strip()]
    else:
        tickers = get_active_tickers(limit=args.limit)
    
    if not tickers:
        logger.error("❌ No tickers to process!")
        sys.exit(1)
    
    # Run backfill
    try:
        result = backfill_fundamentals(
            tickers=tickers,
            batch_size=args.batch_size,
            sleep_between_batches=args.sleep
        )
        
        # Exit with appropriate code
        if result["failed"] == 0:
            sys.exit(0)
        elif result["successful"] > 0:
            sys.exit(2)  # Partial success
        else:
            sys.exit(1)  # Complete failure
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Backfill interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Backfill failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
