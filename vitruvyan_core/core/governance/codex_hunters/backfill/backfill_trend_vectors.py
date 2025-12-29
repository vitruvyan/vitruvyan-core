#!/usr/bin/env python3
"""
PHASE A3.2 Part 2: Backfill trend_vectors Collection
Sacred Order: Memory (Archivarium → Mnemosyne)

Reads latest trend data from PostgreSQL and populates Qdrant.
Target: 519 points (one per active ticker)

Usage:
    python scripts/backfill_trend_vectors.py [--batch-size 100] [--dry-run]
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx
import uuid
from datetime import datetime
from typing import List, Dict, Any
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
import argparse
import time

EMBEDDING_API_URL = "http://localhost:8010"
COLLECTION_NAME = "trend_vectors"
VECTOR_SIZE = 384

def generate_trend_text(row: tuple) -> str:
    """Generate semantic text description from trend data."""
    ticker, sma_short, sma_medium, sma_long, short_trend, medium_trend, long_trend, timestamp = row
    
    # Detect cross patterns
    cross_desc = ""
    if sma_short and sma_medium and sma_long:
        if sma_short > sma_medium and sma_medium > sma_long:
            cross_desc = "Golden cross formation, all SMAs aligned bullish"
        elif sma_short < sma_medium and sma_medium < sma_long:
            cross_desc = "Death cross formation, all SMAs aligned bearish"
        elif sma_short > sma_medium > sma_long:
            cross_desc = "Strong uptrend, golden cross"
        elif sma_short < sma_medium < sma_long:
            cross_desc = "Strong downtrend, death cross"
        else:
            cross_desc = "Mixed trend signals, consolidation"
    
    # Trend strength
    if short_trend and medium_trend and long_trend:
        if "up" in short_trend.lower() and "up" in medium_trend.lower() and "up" in long_trend.lower():
            strength = "Very strong uptrend"
        elif "down" in short_trend.lower() and "down" in medium_trend.lower() and "down" in long_trend.lower():
            strength = "Very strong downtrend"
        else:
            strength = f"Short: {short_trend}, Medium: {medium_trend}, Long: {long_trend}"
    else:
        strength = "Trend data incomplete"
    
    sma_text = ""
    if sma_short and sma_medium and sma_long:
        sma_text = f", SMA Short: {sma_short:.2f}, Medium: {sma_medium:.2f}, Long: {sma_long:.2f}"
    
    return f"Ticker: {ticker}, {strength}, {cross_desc}{sma_text}"

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings via cooperative API."""
    try:
        response = httpx.post(
            f"{EMBEDDING_API_URL}/v1/embeddings/batch",
            json={"texts": texts},
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()["embeddings"]
    except Exception as e:
        print(f"❌ Embedding API error: {e}")
        raise

def backfill_trend(batch_size: int = 100, dry_run: bool = False):
    """Backfill trend_vectors from PostgreSQL."""
    pg = PostgresAgent()
    qdrant = QdrantAgent()
    
    print(f"🚀 Starting trend_vectors backfill...")
    print(f"⚙️  Batch size: {batch_size}, Dry run: {dry_run}")
    
    # Fetch latest trend for each active ticker
    query = """
        SELECT DISTINCT ON (ticker)
            ticker, sma_short, sma_medium, sma_long,
            short_trend, medium_trend, long_trend, timestamp
        FROM trend_logs
        WHERE ticker IN (SELECT ticker FROM tickers WHERE active = true)
        ORDER BY ticker, timestamp DESC;
    """
    
    print("📊 Querying PostgreSQL for trend data...")
    rows = pg.fetch_all(query)
    print(f"✅ Retrieved {len(rows)} tickers from PostgreSQL")
    
    if len(rows) == 0:
        print("⚠️  No trend data found. Exiting.")
        return
    
    if dry_run:
        print("\n🔍 DRY RUN - Sample data (first 3 rows):")
        for i, row in enumerate(rows[:3]):
            text = generate_trend_text(row)
            print(f"  {i+1}. {text}")
        print(f"\n✅ Dry run complete. Would process {len(rows)} tickers.")
        return
    
    # Ensure collection exists
    print(f"🔧 Ensuring {COLLECTION_NAME} collection exists...")
    qdrant.ensure_collection(COLLECTION_NAME, VECTOR_SIZE)
    
    # Process in batches
    total_processed = 0
    total_errors = 0
    start_time = time.time()
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(rows) + batch_size - 1) // batch_size
        
        print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} tickers)...")
        
        try:
            # Generate text descriptions
            texts = [generate_trend_text(row) for row in batch]
            
            # Generate embeddings
            print(f"  🧠 Generating embeddings...")
            embeddings = generate_embeddings(texts)
            
            # Prepare Qdrant points
            points = []
            for row, embedding in zip(batch, embeddings):
                ticker, sma_short, sma_medium, sma_long, short_trend, medium_trend, long_trend, timestamp = row
                
                # Calculate trend alignment
                trend_alignment = None
                if short_trend and medium_trend and long_trend:
                    if all("up" in t.lower() for t in [short_trend, medium_trend, long_trend]):
                        trend_alignment = "all_up"
                    elif all("down" in t.lower() for t in [short_trend, medium_trend, long_trend]):
                        trend_alignment = "all_down"
                    else:
                        trend_alignment = "mixed"
                
                point = {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "ticker": ticker,
                        "sma_short": float(sma_short) if sma_short else None,
                        "sma_medium": float(sma_medium) if sma_medium else None,
                        "sma_long": float(sma_long) if sma_long else None,
                        "short_trend": short_trend,
                        "medium_trend": medium_trend,
                        "long_trend": long_trend,
                        "trend_alignment": trend_alignment,
                        "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        "backfill": True,
                        "backfill_date": datetime.now().isoformat()
                    }
                }
                points.append(point)
            
            # Upsert to Qdrant
            print(f"  💾 Upserting to Qdrant...")
            qdrant.upsert(COLLECTION_NAME, points)
            
            total_processed += len(batch)
            print(f"  ✅ Batch {batch_num} complete ({total_processed}/{len(rows)} total)")
            
        except Exception as e:
            print(f"  ❌ Error in batch {batch_num}: {e}")
            total_errors += len(batch)
            continue
    
    elapsed = time.time() - start_time
    
    # Final verification
    print(f"\n🔍 Verifying collection...")
    try:
        collection_info = qdrant.client.get_collection(COLLECTION_NAME)
        final_count = collection_info.points_count
        print(f"✅ Final count in {COLLECTION_NAME}: {final_count} points")
    except Exception as e:
        print(f"⚠️  Could not verify collection: {e}")
        final_count = "unknown"
    
    print(f"\n{'='*60}")
    print(f"📊 BACKFILL SUMMARY")
    print(f"{'='*60}")
    print(f"Total tickers processed: {total_processed}")
    print(f"Total errors: {total_errors}")
    print(f"Success rate: {(total_processed-total_errors)/total_processed*100:.1f}%")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print(f"Speed: {total_processed/elapsed:.2f} tickers/sec")
    print(f"Final Qdrant count: {final_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill trend_vectors collection")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Preview data without writing")
    
    args = parser.parse_args()
    
    backfill_trend(batch_size=args.batch_size, dry_run=args.dry_run)
