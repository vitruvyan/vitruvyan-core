#!/usr/bin/env python3
"""
Codex Hunters - Complete Workflow Example
==========================================

Demonstrates the complete Codex Hunters workflow:
Discovery → Restoration → Binding

Pure domain logic - no I/O, no infrastructure dependencies.

Usage:
    python3 examples/complete_workflow_example.py

Author: Vitruvyan Core Team
Created: February 2026
"""

import sys
import os
from datetime import datetime

# Add the core module to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from vitruvyan_core.core.governance.codex_hunters.domain.config import CodexConfig, SourceConfig, CollectionConfig, TableConfig
from vitruvyan_core.core.governance.codex_hunters.consumers.tracker import TrackerConsumer
from vitruvyan_core.core.governance.codex_hunters.consumers.restorer import RestorerConsumer
from vitruvyan_core.core.governance.codex_hunters.consumers.binder import BinderConsumer


def main():
    """Demonstrate complete Codex Hunters workflow."""

    print("🏛️  Codex Hunters - Complete Workflow Example")
    print("=" * 50)

    # Configure the system
    config = CodexConfig(
        sources=(
            SourceConfig(
                name="financial_api",
                rate_limit_per_minute=60,
                timeout_seconds=30,
                description="Financial data API"
            ),
            SourceConfig(
                name="news_feed",
                rate_limit_per_minute=100,
                timeout_seconds=10,
                description="News and press releases"
            ),
        ),
        collections=(
            CollectionConfig(
                name="entity_vectors",
                vector_size=384,
                distance_metric="Cosine",
                description="Vector embeddings for entity search"
            ),
        ),
        tables=(
            TableConfig(
                name="entities",
                schema="public",
                primary_key="entity_id",
                description="Entity metadata and relationships"
            ),
        ),
        quality_threshold=0.7,
        dedupe_enabled=True
    )

    # Sample raw data (normally fetched by LIVELLO 2 adapters)
    raw_entities_data = {
        "AAPL": {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "price": 150.25,
            "market_cap": 2500000000000,
            "pe_ratio": 28.5,
            "dividend_yield": 0.82,
            "country": "USA",
            "exchange": "NASDAQ",
            "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
        },
        "MSFT": {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "sector": "Technology",
            "industry": "Software",
            "price": 305.50,
            "market_cap": 2280000000000,
            "pe_ratio": 32.1,
            "dividend_yield": 0.95,
            "country": "USA",
            "exchange": "NASDAQ",
            "description": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide."
        }
    }

    # Initialize consumers
    tracker = TrackerConsumer()
    restorer = RestorerConsumer()
    binder = BinderConsumer()

    processed_entities = []

    # Process each entity through the complete pipeline
    for entity_id, raw_data in raw_entities_data.items():
        print(f"\n🔍 Processing entity: {entity_id}")
        print("-" * 30)

        # PHASE 1: Discovery (Tracker)
        discovery_input = {
            "config": config,
            "entity_ids": [entity_id],
            "source_name": "financial_api",
            "raw_data": {entity_id: raw_data},
            "metadata": {
                "request_id": f"req_{entity_id.lower()}",
                "timestamp": datetime.utcnow().isoformat(),
                "source_version": "v2.1"
            }
        }

        discovery_result = tracker.process(discovery_input)
        if not discovery_result.success:
            print(f"❌ Discovery failed for {entity_id}: {discovery_result.error}")
            continue

        discovered_entity = discovery_result.data["entities"][0]
        print(f"✅ Discovered: {discovered_entity.entity_id} from {discovered_entity.source}")

        # PHASE 2: Restoration (Restorer)
        restoration_input = {
            "config": config,
            "entity": discovered_entity,
            "validation_rules": {
                "required_fields": ["symbol", "name", "price", "sector"],
                "numeric_fields": ["price", "market_cap", "pe_ratio", "dividend_yield"],
                "price_range": {"min": 0, "max": 10000},
                "text_fields": ["name", "description"],
                "enum_fields": {"sector": ["Technology", "Healthcare", "Finance", "Energy"]},
                "name_format": "company_name"
            }
        }

        restoration_result = restorer.process(restoration_input)
        if not restoration_result.success:
            print(f"❌ Restoration failed for {entity_id}: {restoration_result.error}")
            continue

        restored_entity = restoration_result.data["entity"]
        print(f"✅ Restored: Quality Score {restored_entity.quality_score:.2f}")

        if restored_entity.quality_score < config.quality_threshold:
            print(f"⚠️  Low quality entity discarded (threshold: {config.quality_threshold})")
            continue

        # PHASE 3: Binding (Binder)
        binding_input = {
            "config": config,
            "entity": restored_entity,
            "storage_targets": {
                "vector_collection": "entity_vectors",
                "table": "entities"
            },
            "dedupe_strategy": "content_hash",
            "embedding_fields": ["name", "description", "sector", "industry"]
        }

        binding_result = binder.process(binding_input)
        if not binding_result.success:
            print(f"❌ Binding failed for {entity_id}: {binding_result.error}")
            continue

        bound_entity = binding_result.data["entity"]
        print(f"✅ Bound: Dedupe Key {bound_entity.dedupe_key[:16]}...")
        print(f"   Storage Ready: {bound_entity.ready_for_storage}")

        processed_entities.append(bound_entity)

    # Summary
    print(f"\n🏁 Workflow Complete")
    print("=" * 30)
    print(f"Total entities processed: {len(processed_entities)}")
    print(f"Successfully bound: {len(processed_entities)}")

    for entity in processed_entities:
        print(f"  📋 {entity.entity_id}: {entity.dedupe_key[:16]}... (Quality: {entity.quality_score:.2f})")

    print("\n✅ Complete workflow example finished")


if __name__ == "__main__":
    main()