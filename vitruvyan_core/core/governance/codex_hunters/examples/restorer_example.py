#!/usr/bin/env python3
"""
Codex Hunters - Restorer Example
=================================

Demonstrates entity restoration and quality validation.
Pure domain logic - no I/O, no infrastructure dependencies.

Usage:
    python3 examples/restorer_example.py

Author: Vitruvyan Core Team
Created: February 2026
"""

import sys
import os
from datetime import datetime

# Add the core module to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from core.governance.codex_hunters.domain.entities import DiscoveredEntity, EntityStatus
from core.governance.codex_hunters.domain.config import CodexConfig, SourceConfig
from core.governance.codex_hunters.consumers.restorer import RestorerConsumer


def main():
    """Demonstrate entity restoration with Restorer."""

    print("🔧 Codex Hunters - Restorer Example")
    print("=" * 40)

    # Configure data sources
    config = CodexConfig(
        sources=(
            SourceConfig(
                name="api_source",
                rate_limit_per_minute=60,
                timeout_seconds=30,
                description="External API data source"
            ),
        ),
        quality_threshold=0.7,
        dedupe_enabled=True
    )

    # Initialize restorer
    restorer = RestorerConsumer()

    # Create a discovered entity (normally from Tracker)
    discovered_entity = DiscoveredEntity(
        entity_id="ENTITY_A",
        source="api_source",
        raw_data={
            "symbol": "ENTITY_A",
            "name": "Acme Corp.",
            "sector": "Technology",
            "price": 150.25,
            "revenue": 2500000000,
            "growth_rate": 28.5,
            "efficiency_score": 0.82
        },
        metadata={
            "request_id": "req_12345",
            "fetched_at": datetime.utcnow().isoformat(),
            "source_version": "v2.1"
        },
        status=EntityStatus.DISCOVERED
    )

    # Process restoration
    restoration_input = {
        "config": config,
        "entity": discovered_entity,
        "validation_rules": {
            "required_fields": ["symbol", "name", "price"],
            "numeric_fields": ["price", "revenue", "growth_rate"],
            "price_range": {"min": 0, "max": 10000},
            "name_format": "entity_name"
        }
    }

    result = restorer.process(restoration_input)

    print(f"Processing result: {result.success}")
    if result.success:
        restored_entity = result.data.get("entity")
        if restored_entity:
            print("✅ Entity restored successfully:")
            print(f"  📋 Entity ID: {restored_entity.entity_id}")
            print(f"     Source: {restored_entity.source}")
            print(f"     Status: {restored_entity.status.value}")
            print(f"     Quality Score: {restored_entity.quality_score:.2f}")
            print(f"     Validation Errors: {len(restored_entity.validation_errors)}")
            print(f"     Normalized Data Keys: {list(restored_entity.normalized_data.keys())}")

            if restored_entity.validation_errors:
                print("  ⚠️  Validation Issues:")
                for error in restored_entity.validation_errors:
                    print(f"     - {error}")
        else:
            print("❌ No entity returned")
    else:
        print(f"❌ Processing failed: {result.error}")
        for error in result.errors:
            print(f"   {error}")

    print("\n✅ Restorer example completed")


if __name__ == "__main__":
    main()