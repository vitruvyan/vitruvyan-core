#!/usr/bin/env python3
"""
PHASE A3.2 Part 2: Backfill sentiment_embeddings Collection
Sacred Order: Memory (Archivarium → Mnemosyne)

Reads latest sentiment data from PostgreSQL and populates Qdrant.
Target: 519 points (one per active ticker)

NOTE: This backfills sentiment_embeddings only. 
phrases_fused requires actual user text from phrases table (separate backfill).

Usage:
    python scripts/backfill_sentiment_vectors.py [--batch-size 50] [--dry-run]
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
COLLECTION_NAME = "sentiment_embeddings"
VECTOR_SIZE = 384

def generate_sentiment_text(row: tuple) -> str:
    """Generate semantic text description from sentiment data."""
    ticker, combined_score, sentiment_tag, timestamp = row
    
    # Score interpretation
    if combined_score >= 0.6:
        intensity = "strongly positive"
    elif combined_score >= 0.3:
        intensity = "moderately positive"
    elif combined_score > -0.3:
        intensity = "neutral"
    elif combined_score > -0.6:
        intensity = "moderately negative"
    else:
        intensity = "strongly negative"
    
    return f"Ticker: {ticker}, Sentiment: {intensity} ({combined_score:.2f}), Tag: {sentiment_tag}"

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

def backfill_sentiment(batch_size: int = 50, dry_run: bool = False):
    """Backfill sentiment_embeddings from PostgreSQL."""
    pg = PostgresAgent()
    qdrant = QdrantAgent()
    
    print(f"🚀 Starting sentiment_embeddings backfill...")
    print(f"⚙️  Batch size: {batch_size}, Dry run: {dry_run}")
    
    # Fetch latest sentiment for each active ticker
    query = """
        SELECT DISTINCT ON (ticker)
            ticker, combined_score, sentiment_tag, created_at
        FROM sentiment_scores
        WHERE ticker IN (SELECT ticker FROM tickers WHERE active = true)
        ORDER BY ticker, created_at DESC;
    """
    
    print("📊 Querying PostgreSQL for sentiment data...")
    rows = pg.fetch_all(query)
    print(f"✅ Retrieved {len(rows)} tickers from PostgreSQL")
    
    if len(rows) == 0:
        print("⚠️  No sentiment data found. Exiting.")
        return
    
    if dry_run:
        print("\n🔍 DRY RUN - Sample data (first 3 rows):")
        for i, row in enumerate(rows[:3]):
            text = generate_sentiment_text(row)
            print(f"  {i+1}. {text}")
        print(f"\n✅ Dry run complete. Would process {len(rows)} tickers.")
        return
    
    # Ensure collection exists
    print(f"🔧 Ensuring {COLLECTION_NAME} collection exists...")
    qdrant.ensure_collection(COLLECTION_NAME, VECTOR_SIZE)
    
    # Process in batches (smaller due to sentiment processing)
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
            texts = [generate_sentiment_text(row) for row in batch]
            
            # Generate embeddings
            print(f"  🧠 Generating embeddings...")
            embeddings = generate_embeddings(texts)
            
            # Prepare Qdrant points
            points = []
            for row, embedding in zip(batch, embeddings):
                ticker, combined_score, sentiment_tag, timestamp = row
                
                point = {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "ticker": ticker,
                        "combined_score": float(combined_score) if combined_score else 0.0,
                        "sentiment_tag": sentiment_tag,
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
    
    print("\n⚠️  NOTE: phrases_fused collection requires separate backfill from phrases table")
    print("   Run: python scripts/backfill_phrases_fused.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill sentiment_embeddings collection")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Preview data without writing")
    
    args = parser.parse_args()
    
    backfill_sentiment(batch_size=args.batch_size, dry_run=args.dry_run)
