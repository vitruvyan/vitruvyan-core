#!/usr/bin/env python3
"""
Codex Hunters - Binder Example
==============================

Demonstrates entity binding and deduplication preparation.
Pure domain logic - no I/O, no infrastructure dependencies.

Usage:
    python3 examples/binder_example.py

Author: Vitruvyan Core Team
Created: February 2026
"""

import sys
import os
from datetime import datetime

# Add the core module to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from vitruvyan_core.core.governance.codex_hunters.domain.entities import RestoredEntity, EntityStatus
from vitruvyan_core.core.governance.codex_hunters.domain.config import CodexConfig, SourceConfig, CollectionConfig, TableConfig
from vitruvyan_core.core.governance.codex_hunters.consumers.binder import BinderConsumer


def main():
    """Demonstrate entity binding with Binder."""

    print("🔗 Codex Hunters - Binder Example")
    print("=" * 40)

    # Configure storage targets
    config = CodexConfig(
        sources=(
            SourceConfig(
                name="api_source",
                rate_limit_per_minute=60,
                timeout_seconds=30,
                description="External API data source"
            ),
        ),
        collections=(
            CollectionConfig(
                name="entity_vectors",
                vector_size=768,
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

    # Initialize binder
    binder = BinderConsumer()

    # Create a restored entity (normally from Restorer)
    restored_entity = RestoredEntity(
        entity_id="ENTITY_A",
        source="api_source",
        normalized_data={
            "symbol": "ENTITY_A",
            "name": "Acme Corp.",
            "sector": "Technology",
            "price": 150.25,
            "revenue": 2500000000,
            "growth_rate": 28.5,
            "efficiency_score": 0.82,
            "country": "USA",
            "exchange": "PRIMARY"
        },
        quality_score=0.95,
        validation_errors=[],
        status=EntityStatus.RESTORED
    )

    # Process binding
    binding_input = {
        "config": config,
        "entity": restored_entity,
        "storage_targets": {
            "vector_collection": "entity_vectors",
            "table": "entities"
        },
        "dedupe_strategy": "content_hash",  # or "entity_id", "symbol"
        "embedding_fields": ["name", "sector", "symbol"]
    }

    result = binder.process(binding_input)

    print(f"Processing result: {result.success}")
    if result.success:
        bound_entity = result.data.get("entity")
        if bound_entity:
            print("✅ Entity bound successfully:")
            print(f"  📋 Entity ID: {bound_entity.entity_id}")
            print(f"     Source: {bound_entity.source}")
            print(f"     Status: {bound_entity.status.value}")
            print(f"     Dedupe Key: {bound_entity.dedupe_key}")
            print(f"     Storage Refs: {bound_entity.storage_refs}")
            print(f"     Embedding ID: {bound_entity.embedding_id}")
            print(f"     Ready for Storage: {bound_entity.ready_for_storage}")
        else:
            print("❌ No entity returned")
    else:
        print(f"❌ Processing failed: {result.error}")
        for error in result.errors:
            print(f"   {error}")

    print("\n✅ Binder example completed")


if __name__ == "__main__":
    main()