#!/usr/bin/env python3
"""
🔍 Backfill Completeness Verification Tool

Verifies that all active tickers in the database are properly processed
by backfill operations and data is synchronized between PostgreSQL and Qdrant.

Usage:
    python3 scripts/verify_backfill_completeness.py

Checks:
1. Active tickers count in DB
2. Recent momentum_logs entries (last 48h)
3. Recent trend_logs entries (last 48h)
4. Recent sentiment_scores entries (last 48h)
5. Qdrant vector collections populated
6. Data coherence between PostgreSQL and Qdrant
"""

import sys
sys.path.insert(0, '/home/caravaggio/vitruvyan')

from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
from datetime import datetime, timedelta
import json

def check_active_tickers():
    """Check how many active tickers we have in the database"""
    print("=" * 80)
    print("📊 STEP 1: Active Tickers in Database")
    print("=" * 80)
    
    pg = PostgresAgent()
    
    try:
        # Total and active tickers
        result = pg.execute_query(
            "SELECT COUNT(*) as total, COUNT(CASE WHEN active = true THEN 1 END) as active FROM tickers",
            fetch=True
        )
        
        if result:
            total, active = result[0]
            print(f"✅ Total tickers in DB: {total}")
            print(f"✅ Active tickers in DB: {active}")
            
            # Sample tickers
            samples = pg.execute_query(
                "SELECT ticker FROM tickers WHERE active = true ORDER BY ticker LIMIT 10",
                fetch=True
            )
            print(f"\n📝 Sample active tickers:")
            for row in samples:
                print(f"   - {row[0]}")
            
            return active
        else:
            print("❌ Failed to query tickers table")
            return 0
            
    except Exception as e:
        print(f"❌ Error querying tickers: {e}")
        return 0


def check_momentum_logs(active_count):
    """Check momentum_logs table for recent entries"""
    print("\n" + "=" * 80)
    print("⚡ STEP 2: Momentum Logs (RSI, MACD, ROC)")
    print("=" * 80)
    
    pg = PostgresAgent()
    cutoff = datetime.now() - timedelta(hours=48)
    
    try:
        # Count recent entries
        result = pg.execute_query(
            "SELECT COUNT(DISTINCT ticker) FROM momentum_logs WHERE created_at > %s",
            (cutoff,),
            fetch=True
        )
        
        if result:
            count = result[0][0]
            coverage = (count / active_count * 100) if active_count > 0 else 0
            
            print(f"✅ Tickers with momentum data (last 48h): {count}/{active_count} ({coverage:.1f}%)")
            
            # Latest entries
            recent = pg.execute_query(
                """
                SELECT ticker, rsi, macd, created_at
                FROM momentum_logs
                WHERE created_at > %s
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (cutoff,),
                fetch=True
            )
            
            if recent:
                print(f"\n📝 Latest momentum entries:")
                for row in recent:
                    ticker, rsi, macd, created = row
                    print(f"   - {ticker}: RSI={rsi:.2f}, MACD={macd:.4f}, at {created}")
            
            return count
        else:
            print("⚠️ No momentum_logs found in last 48h")
            return 0
            
    except Exception as e:
        print(f"❌ Error querying momentum_logs: {e}")
        return 0


def check_trend_logs(active_count):
    """Check trend_logs table for recent entries"""
    print("\n" + "=" * 80)
    print("📈 STEP 3: Trend Logs (SMA20, SMA50, SMA200)")
    print("=" * 80)
    
    pg = PostgresAgent()
    cutoff = datetime.now() - timedelta(hours=48)
    
    try:
        # Count recent entries
        result = pg.execute_query(
            "SELECT COUNT(DISTINCT ticker) FROM trend_logs WHERE created_at > %s",
            (cutoff,),
            fetch=True
        )
        
        if result:
            count = result[0][0]
            coverage = (count / active_count * 100) if active_count > 0 else 0
            
            print(f"✅ Tickers with trend data (last 48h): {count}/{active_count} ({coverage:.1f}%)")
            
            # Latest entries
            recent = pg.execute_query(
                """
                SELECT ticker, sma_20, sma_50, sma_200, created_at
                FROM trend_logs
                WHERE created_at > %s
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (cutoff,),
                fetch=True
            )
            
            if recent:
                print(f"\n📝 Latest trend entries:")
                for row in recent:
                    ticker, sma20, sma50, sma200, created = row
                    print(f"   - {ticker}: SMA20={sma20:.2f}, SMA50={sma50:.2f}, SMA200={sma200:.2f}, at {created}")
            
            return count
        else:
            print("⚠️ No trend_logs found in last 48h")
            return 0
            
    except Exception as e:
        print(f"❌ Error querying trend_logs: {e}")
        return 0


def check_sentiment_scores(active_count):
    """Check sentiment_scores table for recent entries"""
    print("\n" + "=" * 80)
    print("🎭 STEP 4: Sentiment Scores (Babel Gardens)")
    print("=" * 80)
    
    pg = PostgresAgent()
    cutoff = datetime.now() - timedelta(hours=48)
    
    try:
        # Count recent entries
        result = pg.execute_query(
            "SELECT COUNT(DISTINCT ticker) FROM sentiment_scores WHERE created_at > %s",
            (cutoff,),
            fetch=True
        )
        
        if result:
            count = result[0][0]
            coverage = (count / active_count * 100) if active_count > 0 else 0
            
            print(f"✅ Tickers with sentiment data (last 48h): {count}/{active_count} ({coverage:.1f}%)")
            
            # Latest entries
            recent = pg.execute_query(
                """
                SELECT ticker, combined_score, sentiment_tag, created_at
                FROM sentiment_scores
                WHERE created_at > %s
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (cutoff,),
                fetch=True
            )
            
            if recent:
                print(f"\n📝 Latest sentiment entries:")
                for row in recent:
                    ticker, score, tag, created = row
                    print(f"   - {ticker}: score={score:.3f}, tag={tag}, at {created}")
            
            return count
        else:
            print("⚠️ No sentiment_scores found in last 48h")
            return 0
            
    except Exception as e:
        print(f"❌ Error querying sentiment_scores: {e}")
        return 0


def check_qdrant_collections():
    """Check Qdrant vector collections"""
    print("\n" + "=" * 80)
    print("🗄️ STEP 5: Qdrant Vector Collections")
    print("=" * 80)
    
    try:
        qdrant = QdrantAgent()
        
        # Check each collection
        collections = ["momentum_vectors", "trend_vectors", "sentiment_embeddings"]
        results = {}
        
        for collection_name in collections:
            try:
                info = qdrant.client.get_collection(collection_name=collection_name)
                count = info.points_count
                results[collection_name] = count
                print(f"✅ {collection_name}: {count} vectors")
            except Exception as e:
                print(f"⚠️ {collection_name}: Collection not found or error - {e}")
                results[collection_name] = 0
        
        return results
        
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        return {}


def check_data_coherence(pg_counts, qdrant_counts):
    """Check if PostgreSQL and Qdrant have similar data counts"""
    print("\n" + "=" * 80)
    print("🔗 STEP 6: Data Coherence (PostgreSQL ↔ Qdrant)")
    print("=" * 80)
    
    mappings = {
        "momentum": ("momentum_logs", "momentum_vectors"),
        "trend": ("trend_logs", "trend_vectors"),
        "sentiment": ("sentiment_scores", "sentiment_embeddings")
    }
    
    for data_type, (pg_key, qdrant_key) in mappings.items():
        pg_count = pg_counts.get(pg_key, 0)
        qdrant_count = qdrant_counts.get(qdrant_key, 0)
        
        if pg_count > 0 and qdrant_count > 0:
            ratio = (qdrant_count / pg_count * 100)
            status = "✅" if ratio >= 80 else "⚠️"
            print(f"{status} {data_type.capitalize()}: PG={pg_count}, Qdrant={qdrant_count} ({ratio:.1f}% sync)")
        elif pg_count > 0:
            print(f"⚠️ {data_type.capitalize()}: PG has data ({pg_count}) but Qdrant is empty")
        elif qdrant_count > 0:
            print(f"⚠️ {data_type.capitalize()}: Qdrant has data ({qdrant_count}) but PG is empty")
        else:
            print(f"❌ {data_type.capitalize()}: Both PostgreSQL and Qdrant are empty")


def generate_recommendations(active_count, momentum_count, trend_count, sentiment_count):
    """Generate recommendations based on coverage"""
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    # Check momentum coverage
    momentum_coverage = (momentum_count / active_count * 100) if active_count > 0 else 0
    if momentum_coverage < 50:
        recommendations.append(
            f"⚠️ Momentum coverage is LOW ({momentum_coverage:.1f}%). "
            "Consider triggering manual backfill:\n"
            "   docker exec vitruvyan_redis redis-cli PUBLISH codex.technical.momentum.requested "
            "'{\"tickers\": [\"AAPL\"], \"priority\": \"high\"}'"
        )
    
    # Check trend coverage
    trend_coverage = (trend_count / active_count * 100) if active_count > 0 else 0
    if trend_coverage < 50:
        recommendations.append(
            f"⚠️ Trend coverage is LOW ({trend_coverage:.1f}%). "
            "Consider triggering manual backfill:\n"
            "   docker exec vitruvyan_redis redis-cli PUBLISH codex.technical.trend.requested "
            "'{\"tickers\": [\"AAPL\"], \"priority\": \"high\"}'"
        )
    
    # Check sentiment coverage
    sentiment_coverage = (sentiment_count / active_count * 100) if active_count > 0 else 0
    if sentiment_coverage < 20:
        recommendations.append(
            f"⚠️ Sentiment coverage is LOW ({sentiment_coverage:.1f}%). "
            "Sentiment is populated on-demand via LangGraph queries. "
            "To populate, run queries like:\n"
            "   curl -X POST http://localhost:8004/run -d '{\"input_text\": \"analizza sentiment AAPL\"}'"
        )
    
    # Check scheduler
    recommendations.append(
        "✅ Verify Codex Event Scheduler is running:\n"
        "   systemctl status vitruvyan_codex_scheduler\n"
        "   (Should show daily jobs at 18:00, 18:30 UTC)"
    )
    
    if recommendations:
        for rec in recommendations:
            print(f"\n{rec}")
    else:
        print("\n✅ All systems operational! Coverage is good across all data types.")


def main():
    print("\n" + "🔍" * 40)
    print("🔍 VITRUVYAN BACKFILL COMPLETENESS VERIFICATION")
    print("🔍" * 40 + "\n")
    
    # Step 1: Check active tickers
    active_count = check_active_tickers()
    
    if active_count == 0:
        print("\n❌ CRITICAL: No active tickers found in database!")
        print("   Please verify tickers table exists and has data.")
        return 1
    
    # Step 2-4: Check PostgreSQL tables
    momentum_count = check_momentum_logs(active_count)
    trend_count = check_trend_logs(active_count)
    sentiment_count = check_sentiment_scores(active_count)
    
    pg_counts = {
        "momentum_logs": momentum_count,
        "trend_logs": trend_count,
        "sentiment_scores": sentiment_count
    }
    
    # Step 5: Check Qdrant
    qdrant_counts = check_qdrant_collections()
    
    # Step 6: Check coherence
    check_data_coherence(pg_counts, qdrant_counts)
    
    # Step 7: Generate recommendations
    generate_recommendations(active_count, momentum_count, trend_count, sentiment_count)
    
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
