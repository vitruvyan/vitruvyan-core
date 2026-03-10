#!/usr/bin/env python3
"""
Codex Hunters - Tracker Example
===============================

Demonstrates entity discovery using the Tracker consumer.
Pure domain logic - no I/O, no infrastructure dependencies.

Usage:
    python3 examples/tracker_example.py

Author: Vitruvyan Core Team
Created: February 2026
"""

import sys
import os
from datetime import datetime

# Add the core module to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from core.governance.codex_hunters.domain.config import CodexConfig, SourceConfig
from core.governance.codex_hunters.consumers.tracker import TrackerConsumer


def main():
    """Demonstrate entity discovery with Tracker."""

    print("🔍 Codex Hunters - Tracker Example")
    print("=" * 40)

    # Configure data sources
    config = CodexConfig(
        sources={
            "api_source": SourceConfig(
                name="api_source",
                rate_limit_per_minute=60,
                timeout_seconds=30,
                description="External API data source"
            ),
            "file_source": SourceConfig(
                name="file_source",
                rate_limit_per_minute=100,
                timeout_seconds=10,
                description="Local file data source"
            ),
        }
    )

    # Initialize tracker
    tracker = TrackerConsumer()

    # Simulate discovery input (normally comes from LIVELLO 2 adapter)
    discovery_input = {
        "config": config,
        "entity_id": "ENTITY_A",
        "source": "primary",
        "raw_data": {
            "symbol": "ENTITY_A",
            "name": "Acme Corp.",
            "sector": "Technology",
            "price": 150.25,
            "revenue": 2500000000
        },
        "metadata": {
            "request_id": "req_12345",
            "timestamp": datetime.now().isoformat()
        }
    }

    # Process discovery
    result = tracker.process(discovery_input)

    print(f"Processing result: {result.success}")
    if result.success:
        entity = result.data.get("entity")
        print(f"Discovered 1 entity:")

        print(f"  📋 Entity: {entity.entity_id}")
        print(f"     Source: {entity.source}")
        print(f"     Status: {entity.status.value}")
        print(f"     Raw data keys: {list(entity.raw_data.keys())}")
        print(f"     Metadata keys: {list(entity.metadata.keys())}")
        print()
    else:
        print(f"❌ Processing failed: {result.errors}")
        for error in result.errors:
            print(f"   {error}")

    print("✅ Tracker example completed")


if __name__ == "__main__":
    main()