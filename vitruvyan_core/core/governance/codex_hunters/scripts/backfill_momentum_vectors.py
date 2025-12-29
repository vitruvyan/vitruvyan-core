#!/usr/bin/env python3
"""
PHASE A3.2 Part 2: Backfill momentum_vectors Collection
Sacred Order: Memory (Archivarium → Mnemosyne)

Reads latest momentum data from PostgreSQL and populates Qdrant.
Target: 519 points (one per active ticker)

Usage:
    python scripts/backfill_momentum_vectors.py [--batch-size 100] [--dry-run]
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
COLLECTION_NAME = "momentum_vectors"
VECTOR_SIZE = 384

def generate_momentum_text(row: tuple) -> str:
    """Generate semantic text description from momentum data."""
    ticker, rsi, macd, macd_signal, roc, roc_trend, macd_trend, timestamp = row
    
    # RSI interpretation
    if rsi:
        if rsi >= 70:
            rsi_desc = f"RSI {rsi:.2f} overbought"
        elif rsi <= 30:
            rsi_desc = f"RSI {rsi:.2f} oversold"
        else:
            rsi_desc = f"RSI {rsi:.2f} neutral"
    else:
        rsi_desc = "RSI unavailable"
    
    # MACD interpretation
    if macd and macd_signal:
        histogram = macd - macd_signal
        if macd > macd_signal:
            macd_desc = f"MACD bullish above signal (histogram {histogram:.4f})"
        else:
            macd_desc = f"MACD bearish below signal (histogram {histogram:.4f})"
    else:
        macd_desc = "MACD unavailable"
    
    # ROC interpretation
    if roc and roc_trend:
        roc_desc = f"ROC {roc:.2f}% {roc_trend}"
    else:
        roc_desc = "ROC unavailable"
    
    return f"Ticker: {ticker}, {rsi_desc}, {macd_desc}, {roc_desc}, Trend: {macd_trend or 'unknown'}"

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

def backfill_momentum(batch_size: int = 100, dry_run: bool = False):
    """Backfill momentum_vectors from PostgreSQL."""
    pg = PostgresAgent()
    qdrant = QdrantAgent()
    
    print(f"🚀 Starting momentum_vectors backfill...")
    print(f"⚙️  Batch size: {batch_size}, Dry run: {dry_run}")
    
    # Fetch latest momentum for each active ticker
    query = """
        SELECT DISTINCT ON (ticker)
            ticker, rsi, macd, macd_signal,
            roc, roc_trend, macd_trend, timestamp
        FROM momentum_logs
        WHERE ticker IN (SELECT ticker FROM tickers WHERE active = true)
        ORDER BY ticker, timestamp DESC;
    """
    
    print("📊 Querying PostgreSQL for momentum data...")
    rows = pg.fetch_all(query)
    print(f"✅ Retrieved {len(rows)} tickers from PostgreSQL")
    
    if len(rows) == 0:
        print("⚠️  No momentum data found. Exiting.")
        return
    
    if dry_run:
        print("\n🔍 DRY RUN - Sample data (first 3 rows):")
        for i, row in enumerate(rows[:3]):
            text = generate_momentum_text(row)
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
            texts = [generate_momentum_text(row) for row in batch]
            
            # Generate embeddings
            print(f"  🧠 Generating embeddings...")
            embeddings = generate_embeddings(texts)
            
            # Prepare Qdrant points
            points = []
            for row, embedding in zip(batch, embeddings):
                ticker, rsi, macd, macd_signal, roc, roc_trend, macd_trend, timestamp = row
                
                # Calculate histogram
                macd_histogram = (macd - macd_signal) if (macd and macd_signal) else None
                
                point = {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "ticker": ticker,
                        "rsi": float(rsi) if rsi else None,
                        "macd": float(macd) if macd else None,
                        "macd_signal": float(macd_signal) if macd_signal else None,
                        "macd_histogram": float(macd_histogram) if macd_histogram else None,
                        "roc": float(roc) if roc else None,
                        "roc_trend": roc_trend,
                        "macd_trend": macd_trend,
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
    parser = argparse.ArgumentParser(description="Backfill momentum_vectors collection")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Preview data without writing")
    
    args = parser.parse_args()
    
    backfill_momentum(batch_size=args.batch_size, dry_run=args.dry_run)
