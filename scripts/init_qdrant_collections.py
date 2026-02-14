#!/usr/bin/env python3
"""
Initialize Qdrant Collections for Vitruvyan Core
================================================

Creates required Qdrant collections if they don't exist.
Safe to run multiple times (won't delete existing data).

Collections:
- semantic_states: VSGS semantic grounding (384-dim, MiniLM-L6-v2)
- patterns: Pattern Weavers ontology (384-dim, MiniLM-L6-v2)

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

# Collection configurations
COLLECTIONS = [
    {
        "name": "semantic_states",
        "vector_size": 384,  # MiniLM-L6-v2 embedding dimension
        "distance": "Cosine",
        "description": "VSGS semantic grounding contexts"
    },
    {
        "name": "patterns",
        "vector_size": 384,  # MiniLM-L6-v2 embedding dimension
        "distance": "Cosine",
        "description": "Pattern Weavers ontology taxonomy"
    },
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
