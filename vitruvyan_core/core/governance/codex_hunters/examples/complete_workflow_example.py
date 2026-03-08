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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from vitruvyan_core.core.governance.codex_hunters.domain.config import CodexConfig, SourceConfig, CollectionConfig, TableConfig
from vitruvyan_core.core.governance.codex_hunters.consumers.tracker import TrackerConsumer
from vitruvyan_core.core.governance.codex_hunters.consumers.restorer import RestorerConsumer
from vitruvyan_core.core.governance.codex_hunters.consumers.binder import BinderConsumer


def main():
    """Demonstrate complete Codex Hunters workflow."""

    print("🏛️  Codex Hunters - Complete Workflow Example")
    print("=" * 50)

    # Configure the system (domain-agnostic)
    config = CodexConfig(
        sources={
            "primary_api": SourceConfig(
                name="primary_api",
                rate_limit_per_minute=60,
                timeout_seconds=30,
                description="Primary data source API"
            ),
            "secondary_feed": SourceConfig(
                name="secondary_feed",
                rate_limit_per_minute=100,
                timeout_seconds=10,
                description="Secondary data feed"
            ),
        },
        collections={
            "entity_vectors": CollectionConfig(
                name="entity_vectors",
                vector_size=384,
                distance_metric="Cosine",
                description="Vector embeddings for entity search"
            ),
        },
        tables={
            "entities": TableConfig(
                name="entities",
                schema="public",
                primary_key="entity_id",
                description="Entity metadata and relationships"
            ),
        }
    )

    # Sample raw data (normally fetched by LIVELLO 2 adapters)
    # Domain-agnostic examples: products, research papers, medical records, etc.
    raw_entities_data = {
        "PROD_001": {
            "product_id": "PROD_001",
            "name": "Widget Alpha",
            "category": "Electronics",
            "subcategory": "Smart Devices",
            "price": 299.99,
            "stock_quantity": 1500,
            "rating": 4.5,
            "reviews_count": 287,
            "manufacturer": "TechCorp Inc.",
            "country_of_origin": "USA",
            "description": "Advanced smart device with AI capabilities and IoT integration."
        },
        "PROD_002": {
            "product_id": "PROD_002",
            "name": "Widget Beta",
            "category": "Electronics",
            "subcategory": "Home Automation",
            "price": 199.99,
            "stock_quantity": 3200,
            "rating": 4.8,
            "reviews_count": 512,
            "manufacturer": "SmartHome Solutions",
            "country_of_origin": "Germany",
            "description": "Energy-efficient home automation hub with voice control."
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
            "entity_id": entity_id,
            "source": "primary_api",
            "raw_data": raw_data,
            "metadata": {
                "request_id": f"req_{entity_id.lower()}",
                "timestamp": datetime.now().isoformat(),
                "source_version": "v2.1"
            }
        }

        discovery_result = tracker.process(discovery_input)
        if not discovery_result.success:
            print(f"❌ Discovery failed for {entity_id}: {discovery_result.errors}")
            continue

        discovered_entity = discovery_result.data["entity"]
        print(f"✅ Discovered: {discovered_entity.entity_id} from {discovered_entity.source}")

        # PHASE 2: Restoration (Restorer)
        restoration_input = {
            "entity": discovered_entity,
            "validation_rules": {
                "required_fields": ["symbol", "name", "price", "sector"],
                "numeric_fields": ["price", "revenue", "growth_rate", "efficiency_score"],
                "price_range": {"min": 0, "max": 10000},
                "text_fields": ["name", "description"],
                "enum_fields": {"sector": ["Technology", "Healthcare", "Finance", "Energy"]},
                "name_format": "entity_name"
            }
        }

        restoration_result = restorer.process(restoration_input)
        if not restoration_result.success:
            print(f"❌ Restoration failed for {entity_id}: {restoration_result.errors}")
            continue

        restored_entity = restoration_result.data["entity"]
        print(f"✅ Restored: Quality Score {restored_entity.quality_score:.2f}")

        if restored_entity.quality_score < config.quality.threshold_valid:
            print(f"⚠️  Low quality entity discarded (threshold: {config.quality.threshold_valid})")
            continue

        # PHASE 3: Binding (Binder)
        binding_input = {
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
            print(f"❌ Binding failed for {entity_id}: {binding_result.errors}")
            continue

        bound_entity = binding_result.data["bound_entity"]
        print(f"✅ Bound: Dedupe Key {bound_entity.dedupe_key[:16]}...")
        print(f"   Storage Refs: {bound_entity.storage_refs}")

        processed_entities.append(bound_entity)

    # Summary
    print(f"\n🏁 Workflow Complete")
    print("=" * 30)
    print(f"Total entities processed: {len(processed_entities)}")
    print(f"Successfully bound: {len(processed_entities)}")

    for entity in processed_entities:
        print(f"  📋 {entity.entity_id}: {entity.dedupe_key[:16]}... (Status: {entity.status.value})")

    print("\n✅ Complete workflow example finished")


if __name__ == "__main__":
    main()