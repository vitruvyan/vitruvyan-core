#!/usr/bin/env python3
"""
Initialize Qdrant Collections for Mercator
===========================================

Creates required Qdrant collections if they don't exist.
Safe to run multiple times (won't delete existing data).

All collections use 384-dim vectors (MiniLM-L6-v2) with Cosine distance.

Migrated from vitruvyan production (27 collections, 1.87M vectors).

Usage:
    python scripts/init_qdrant_collections.py

Environment Variables:
    QDRANT_HOST, QDRANT_PORT, QDRANT_URL
"""

import sys
import os
from pathlib import Path

# Add vitruvyan_core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "vitruvyan_core"))

from core.agents.qdrant_agent import QdrantAgent
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Collection configurations — curated inventory for active runtime paths
# Grouped by Sacred Order / domain function
COLLECTIONS = [
    # === CORE: Semantic Engine ===
    {"name": "semantic_states",          "vector_size": 384, "distance": "Cosine", "description": "VSGS semantic grounding contexts"},
    {"name": "phrases_embeddings",       "vector_size": 384, "distance": "Cosine", "description": "NLP phrase embeddings (api_embedding)"},

    # === CORE: Pattern Weavers ===
    {"name": "patterns",                 "vector_size": 384, "distance": "Cosine", "description": "Pattern Weavers ontology taxonomy"},
    {"name": "weave_embeddings",         "vector_size": 384, "distance": "Cosine", "description": "Pattern weave result embeddings"},

    # === CORE: Babel Gardens ===
    {"name": "conversations_embeddings", "vector_size": 384, "distance": "Cosine", "description": "Conversation history embeddings"},
    {"name": "sentiment_embeddings",     "vector_size": 384, "distance": "Cosine", "description": "Sentiment analysis embeddings"},

    # === CORE: Orthodoxy / Audit ===
    {"name": "audit_embeddings",         "vector_size": 384, "distance": "Cosine", "description": "Audit trail embeddings"},

    # === CORE: Codex Hunters ===
    {"name": "entity_embeddings",        "vector_size": 384, "distance": "Cosine", "description": "Codex Hunters entity semantic embeddings"},

    # === CORE: Knowledge Base ===
    {"name": "vitruvyan_docs",           "vector_size": 384, "distance": "Cosine", "description": "System documentation embeddings"},
    {"name": "vitruvyan_notes",          "vector_size": 384, "distance": "Cosine", "description": "System notes embeddings"},
    {"name": "aegis_demo_kb",            "vector_size": 384, "distance": "Cosine", "description": "Demo knowledge base"},

    # === FINANCE: Market Data ===
    {"name": "financial_templates",      "vector_size": 384, "distance": "Cosine", "description": "Financial template embeddings (1.7M vectors)"},
    {"name": "market_data",              "vector_size": 384, "distance": "Cosine", "description": "Market data embeddings"},
    {"name": "ticker_embeddings",        "vector_size": 384, "distance": "Cosine", "description": "Ticker/entity embeddings"},

    # === FINANCE: Factor Analysis ===
    {"name": "momentum_vectors",         "vector_size": 384, "distance": "Cosine", "description": "Momentum factor vectors"},
    {"name": "volatility_vectors",       "vector_size": 384, "distance": "Cosine", "description": "Volatility factor vectors"},
    {"name": "trend_vectors",            "vector_size": 384, "distance": "Cosine", "description": "Trend factor vectors"},
    {"name": "vare_embeddings",          "vector_size": 384, "distance": "Cosine", "description": "VaRE risk embeddings"},
    {"name": "vhsw_embeddings",          "vector_size": 384, "distance": "Cosine", "description": "VHSW strength embeddings"},
    {"name": "vmfl_embeddings",          "vector_size": 384, "distance": "Cosine", "description": "VMFL factor embeddings"},

    # === DOMAIN: Tracking / Demo ===
    {"name": "ship_tracking_vectors",    "vector_size": 384, "distance": "Cosine", "description": "Ship tracking embeddings"},
    {"name": "ship_tracker_embeddings",  "vector_size": 384, "distance": "Cosine", "description": "Ship tracker embeddings"},
    {"name": "air_traffic_embeddings",   "vector_size": 384, "distance": "Cosine", "description": "Air traffic embeddings"},

    # === TEST ===
    {"name": "test_collection",          "vector_size": 384, "distance": "Cosine", "description": "Test/development collection"},
]


def main():
    """Initialize all required Qdrant collections."""
    logger.info("🚀 Starting Qdrant collection initialization")
    
    try:
        # Connect to Qdrant
        qdrant = QdrantAgent()
        
        # Health check
        health = qdrant.health()
        if health["status"] != "ok":
            logger.error(f"❌ Qdrant health check failed: {health.get('error')}")
            sys.exit(1)
        
        logger.info(f"✅ Connected to Qdrant (existing collections: {health['collections']})")
        
        # Create collections
        created = 0
        existing = 0
        errors = 0
        
        for config in COLLECTIONS:
            logger.info(f"\n📦 Processing collection: {config['name']}")
            logger.info(f"   Description: {config['description']}")
            logger.info(f"   Vector size: {config['vector_size']}")
            logger.info(f"   Distance: {config['distance']}")
            
            try:
                result = qdrant.ensure_collection(
                    name=config["name"],
                    vector_size=config["vector_size"],
                    distance=config["distance"],
                    force_recreate=False  # SAFE: Never delete data
                )
                
                if result["status"] == "created":
                    logger.info(f"   ✅ Collection '{config['name']}' created")
                    created += 1
                elif result["status"] == "exists":
                    logger.info(f"   ℹ️  Collection '{config['name']}' already exists ({result.get('points_count', 0)} points)")
                    existing += 1
                else:
                    logger.warning(f"   ⚠️  Unexpected status: {result}")
                    
            except Exception as e:
                logger.error(f"   ❌ Failed to create collection '{config['name']}': {e}")
                errors += 1
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Created:  {created}")
        logger.info(f"ℹ️  Existing: {existing}")
        logger.info(f"❌ Errors:   {errors}")
        logger.info("="*60)
        
        if errors > 0:
            logger.error("\n❌ Some collections failed to initialize")
            sys.exit(1)
        else:
            logger.info("\n✅ All collections initialized successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
