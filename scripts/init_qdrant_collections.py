#!/usr/bin/env python3
"""
Initialize Qdrant Collections for Mercator
===========================================

Creates required Qdrant collections if they don't exist.
Safe to run multiple times (won't delete existing data).

All collections use 768-dim vectors (nomic-embed-text-v1.5) with Cosine distance.

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
# Governed by RAG_GOVERNANCE_CONTRACT_V1 (docs/contracts/rag/)
# Format: "TIER: Owner — Purpose"
#
# ONLY collections with active writer+reader in codebase are declared here.
# Domain/vertical collections are added when their owning code is implemented.
# See contract Section 6.1 for creation rules.
COLLECTIONS = [
    # ═══════════════════════════════════════════════════════════════════════
    # CORE: OS-level, domain-agnostic, permanent
    # ═══════════════════════════════════════════════════════════════════════
    {"name": "semantic_states",          "vector_size": 768, "distance": "Cosine",
     "description": "CORE: VSGS Engine \u2014 Semantic grounding contexts"},
    {"name": "phrases_embeddings",       "vector_size": 768, "distance": "Cosine",
     "description": "CORE: Embedding Service \u2014 NLP phrase embeddings (general-purpose RAG)"},
    {"name": "conversations_embeddings", "vector_size": 768, "distance": "Cosine",
     "description": "CORE: LangGraph — Conversational memory for RAG retrieval"},

    # ═══════════════════════════════════════════════════════════════════════
    # ORDER: Sacred Order operational data
    # ═══════════════════════════════════════════════════════════════════════
    {"name": "entity_embeddings",        "vector_size": 768, "distance": "Cosine",
     "description": "ORDER: Codex Hunters \u2014 Ingested entity semantic embeddings"},
    {"name": "weave_embeddings",         "vector_size": 768, "distance": "Cosine",
     "description": "ORDER: Pattern Weavers — Ontological pattern result embeddings"},
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
