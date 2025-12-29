#!/usr/bin/env python3
"""
Ensures momentum_logs table exists with all required columns.
Auto-creates table/columns if missing. Safe to run multiple times (idempotent).
"""
import sys
from core.foundation.persistence.postgres_agent import PostgresAgent


def ensure_momentum_logs_schema():
    """Create momentum_logs table and columns if they don't exist."""
    
    agent = PostgresAgent()
    
    # 1. Create table if not exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS momentum_logs (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        ticker TEXT NOT NULL,
        horizon TEXT,
        rsi NUMERIC,
        signal TEXT,
        roc NUMERIC,
        macd NUMERIC,
        macd_signal NUMERIC,
        roc_trend TEXT,
        macd_trend TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        raw_output JSONB
    );
    """
    
    with agent.connection.cursor() as cur:
        cur.execute(create_table_sql)
        agent.connection.commit()
        print("✅ momentum_logs table ensured")
    
    # 2. Ensure indexes exist for performance
    indexes = [
        ("momentum_logs_ticker_idx", "CREATE INDEX IF NOT EXISTS momentum_logs_ticker_idx ON momentum_logs(ticker);"),
        ("momentum_logs_timestamp_idx", "CREATE INDEX IF NOT EXISTS momentum_logs_timestamp_idx ON momentum_logs(timestamp DESC);"),
        ("momentum_logs_ticker_timestamp_idx", "CREATE INDEX IF NOT EXISTS momentum_logs_ticker_timestamp_idx ON momentum_logs(ticker, timestamp DESC);"),
    ]
    
    with agent.connection.cursor() as cur:
        for idx_name, idx_sql in indexes:
            cur.execute(idx_sql)
            print(f"✅ Index {idx_name} ensured")
        agent.connection.commit()
    
    # 3. Verify column existence (PostgreSQL auto-adds missing columns if needed in future)
    required_columns = [
        "id", "user_id", "ticker", "horizon", 
        "rsi", "signal", "roc", "macd", "macd_signal", 
        "roc_trend", "macd_trend", "timestamp", "raw_output"
    ]
    
    with agent.connection.cursor() as cur:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'momentum_logs' 
            AND table_schema = 'public'
        """)
        existing_columns = {row[0] for row in cur.fetchall()}
        
        missing = set(required_columns) - existing_columns
        if missing:
            print(f"⚠️ Missing columns: {missing}")
            print("   (These will be auto-created on next INSERT)")
        else:
            print(f"✅ All {len(required_columns)} required columns exist")
    
    # 4. Check data freshness (alert if no recent data)
    with agent.connection.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(DISTINCT ticker) as tickers,
                MAX(timestamp) as latest_record,
                EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) / 3600 as hours_old
            FROM momentum_logs
        """)
        row = cur.fetchone()
        if row:
            tickers, latest, hours_old = row
            print(f"\n📊 Data Status:")
            print(f"   - Tickers with data: {tickers}")
            print(f"   - Latest record: {latest}")
            print(f"   - Age: {hours_old:.1f} hours")
            
            if hours_old and hours_old > 48:
                print(f"\n⚠️ WARNING: Data is {hours_old:.1f} hours old!")
                print("   Backfill should run daily to populate fresh momentum data.")
                return False
            else:
                print("✅ Data freshness acceptable")
                return True
        else:
            print("\n⚠️ WARNING: No data in momentum_logs!")
            print("   Run: python3 scripts/backfill_technical_logs.py --only momentum --only-us")
            return False


if __name__ == "__main__":
    try:
        print("🔧 Ensuring momentum_logs schema...")
        is_fresh = ensure_momentum_logs_schema()
        sys.exit(0 if is_fresh else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
