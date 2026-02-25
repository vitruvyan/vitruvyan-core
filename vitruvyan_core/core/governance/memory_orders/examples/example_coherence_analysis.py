#!/usr/bin/env python3
"""
Memory Orders — Example: Coherence Analysis

Demonstrates the complete domain flow for memory coherence monitoring:
  Coherence Analysis → Health Aggregation → Sync Planning

Run standalone: python -m examples.example_coherence_analysis
Requires: NO infrastructure (no Redis, no PostgreSQL, no Docker)

Sacred Order: Memory & Persistence
Layer: Foundational (examples)
"""

import sys
import os

# Add vitruvyan_core to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from vitruvyan_core.core.governance.memory_orders.domain import CoherenceInput, CoherenceReport, ComponentHealth, SystemHealth, SyncInput
from vitruvyan_core.core.governance.memory_orders.consumers.coherence_analyzer import CoherenceAnalyzer
from vitruvyan_core.core.governance.memory_orders.consumers.health_aggregator import HealthAggregator
from vitruvyan_core.core.governance.memory_orders.consumers.sync_planner import SyncPlanner
from vitruvyan_core.core.governance.memory_orders.governance import DEFAULT_THRESHOLDS


def main():
    print("=" * 60)
    print("Memory Orders — Coherence Analysis & Health Monitoring")
    print("=" * 60)

    # ─────────────────────────────────────────────────────────────
    # 1. Coherence Analysis: Calculate drift between systems
    # ─────────────────────────────────────────────────────────────
    print("\n1. Running coherence analysis with CoherenceAnalyzer:")

    analyzer = CoherenceAnalyzer()

    # Healthy coherence scenario
    input_healthy = CoherenceInput(
        pg_count=1000,
        qdrant_count=980,
        thresholds=DEFAULT_THRESHOLDS.as_tuple()
    )

    report_healthy = analyzer.process(input_healthy)
    print(f"   Healthy scenario - Status: {report_healthy.status}")
    print(f"   Drift: {report_healthy.drift_percentage:.2f}%")
    print(f"   Recommendation: {report_healthy.recommendation}")

    # Warning coherence scenario
    input_warning = CoherenceInput(
        pg_count=1000,
        qdrant_count=850,
        thresholds=DEFAULT_THRESHOLDS.as_tuple()
    )

    report_warning = analyzer.process(input_warning)
    print(f"   Warning scenario - Status: {report_warning.status}")
    print(f"   Drift: {report_warning.drift_percentage:.2f}%")
    print(f"   Recommendation: {report_warning.recommendation}")

    # Critical coherence scenario
    input_critical = CoherenceInput(
        pg_count=1000,
        qdrant_count=500,
        thresholds=DEFAULT_THRESHOLDS.as_tuple()
    )

    report_critical = analyzer.process(input_critical)
    print(f"   Critical scenario - Status: {report_critical.status}")
    print(f"   Drift: {report_critical.drift_percentage:.2f}%")
    print(f"   Recommendation: {report_critical.recommendation}")

    # ─────────────────────────────────────────────────────────────
    # 2. Health Aggregation: Combine multiple system health reports
    # ─────────────────────────────────────────────────────────────
    print("\n2. Aggregating health with HealthAggregator:")

    aggregator = HealthAggregator()

    # Simulate health data from multiple components
    components = (
        ComponentHealth(
            component="postgresql",
            status="healthy",
            metrics=(("response_time", 50), ("connections", 10)),
            response_time_ms=50.0
        ),
        ComponentHealth(
            component="qdrant",
            status="healthy",
            metrics=(("response_time", 30), ("collections", 5)),
            response_time_ms=30.0
        ),
        ComponentHealth(
            component="embedding_api",
            status="degraded",
            metrics=(("response_time", 200), ("errors", 2)),
            response_time_ms=200.0
        ),
        ComponentHealth(
            component="redis",
            status="healthy",
            metrics=(("response_time", 10), ("memory_usage", 0.3)),
            response_time_ms=10.0
        )
    )

    health_input = {
        "components": components,
        "coherence_report": report_healthy
    }

    health_report = aggregator.process(health_input)
    print(f"   Overall health: {health_report.overall_status}")
    
    # Count components by status
    healthy_count = sum(1 for comp in health_report.components if comp.status == "healthy")
    degraded_count = sum(1 for comp in health_report.components if comp.status == "degraded")
    failed_count = sum(1 for comp in health_report.components if comp.status == "unhealthy")
    
    print(f"   Healthy components: {healthy_count}")
    print(f"   Degraded components: {degraded_count}")
    print(f"   Failed components: {failed_count}")

    # ─────────────────────────────────────────────────────────────
    # 3. Sync Planning: Generate synchronization recommendations
    # ─────────────────────────────────────────────────────────────
    print("\n3. Planning synchronization with SyncPlanner:")

    planner = SyncPlanner()

    # Create SyncInput for warning scenario
    sync_input = SyncInput(
        pg_data=(1000, "sample_data_1", "sample_data_2"),  # Simplified data
        qdrant_data=(850, "embedding_1", "embedding_2"),   # Simplified data
        mode="incremental",
        source_table="entities",
        target_collection="entity_embeddings"
    )

    sync_plan = planner.process(sync_input)
    print(f"   Sync mode: {sync_plan.mode}")
    print(f"   Estimated duration: {sync_plan.estimated_duration_s}s")
    print(f"   Total operations: {sync_plan.total_operations}")
    print(f"   Operations: {[op.operation_type for op in sync_plan.operations[:3]]}")  # Show first 3

    # ─────────────────────────────────────────────────────────────
    # 4. Decision Flow: Coherence → Health → Sync Plan
    # ─────────────────────────────────────────────────────────────
    print("\n4. Complete decision flow:")

    scenarios = [
        ("Healthy", input_healthy),
        ("Warning", input_warning),
        ("Critical", input_critical)
    ]

    for scenario_name, coherence_input in scenarios:
        # Step 1: Analyze coherence
        coh_report = analyzer.process(coherence_input)

        # Step 2: Aggregate health (simplified)
        health_status = "healthy" if coh_report.status == "healthy" else "degraded"

        # Step 3: Determine action based on coherence
        if coh_report.status != "healthy":
            action = f"Sync required ({coh_report.drift_percentage:.1f}% drift)"
        else:
            action = "No action needed"

        print(f"   {scenario_name}: {coh_report.status} → {health_status} → {action}")

    print("\n✅ Memory coherence analysis example completed!")
    print("\n💡 This demonstrates pure domain logic - no I/O, no databases, no network calls")
    print("   The service layer (api_memory_orders) handles persistence and event publishing")


if __name__ == "__main__":
    main()
