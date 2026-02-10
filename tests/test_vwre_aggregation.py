#!/usr/bin/env python3
"""
Test VWRE Engine with AggregationProvider
=========================================

Tests the refactored VWRE Engine to ensure it works with domain-agnostic providers.

⚠️ TEMPORARILY SKIPPED:
These tests require VWRE engine and Mercator providers that were not yet migrated
to vitruvyan-core. Re-enable when modules are available.

Author: Vitruvyan Core Team
Created: December 30, 2025
"""

import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mark entire module as skipped due to missing modules
pytestmark = pytest.mark.skip(reason="VWRE engine and Mercator providers not available in vitruvyan-core")


def test_vwre_with_provider():
    """Test VWRE Engine with MercatorAggregationProvider"""

    print("🧪 Testing VWRE Engine with AggregationProvider...")

    # Initialize components
    vwre = VWREEngine()
    provider = MercatorAggregationProvider()

    # Test data (finance domain)
    entity_id = "EXAMPLE_ENTITY_1"
    composite_score = 1.85
    factors = {
        "momentum_z": 2.1,
        "trend_z": 1.5,
        "vola_z": -0.3,
        "sentiment_z": 0.8,
        "fundamentals_z": 1.2,
        "technical_z": 0.9,
        "quality_z": 0.4,
        "size_z": -0.1
    }

    # Perform attribution analysis
    result = vwre.analyze_attribution(entity_id, composite_score, factors, provider)

    # Validate results
    assert result.entity_id == entity_id
    assert abs(result.composite_score - composite_score) < 0.001
    assert result.primary_driver is not None
    assert result.verification_status in ["verified", "warning", "error"]

    print("✅ Basic attribution analysis passed")
    print(f"   Entity: {result.entity_id}")
    print(f"   Composite Score: {result.composite_score:.3f}")
    print(f"   Profile: {result.profile}")
    print(f"   Primary Driver: {result.primary_driver}")
    print(f"   Verification: {result.verification_status}")
    print(f"   Rank Explanation: {result.rank_explanation}")

    # Test batch analysis
    batch_data = [
        {"entity_id": "EXAMPLE_ENTITY_1", "composite_score": 1.85, "factors": factors},
        {"entity_id": "EXAMPLE_ENTITY_3", "composite_score": 0.95, "factors": {
            "momentum_z": 1.8, "trend_z": 0.2, "vola_z": 1.1, "sentiment_z": -0.5,
            "fundamentals_z": 0.8, "technical_z": 0.3, "quality_z": 0.1, "size_z": 0.2
        }}
    ]

    batch_results = vwre.batch_analyze(batch_data, provider)
    assert len(batch_results) == 2

    print("✅ Batch analysis passed")
    for result in batch_results:
        print(f"   {result.entity_id}: {result.primary_driver} ({result.primary_contribution:.3f})")

    # Test convenience functions
    from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vwre_engine import explain_rank, compare_two

    explanation = explain_rank("EXAMPLE_ENTITY_1", 1.85, factors, provider)
    print(f"✅ Convenience function passed: {explanation}")

    comparison = compare_two("EXAMPLE_ENTITY_1", 1.85, factors, "EXAMPLE_ENTITY_3", 0.95, {
        "momentum_z": 1.8, "trend_z": 0.2, "vola_z": 1.1, "sentiment_z": -0.5,
        "fundamentals_z": 0.8, "technical_z": 0.3, "quality_z": 0.1, "size_z": 0.2
    }, provider)
    print(f"✅ Comparison function passed: {comparison}")

    print("🎉 All VWRE tests passed! VWRE is now domain-agnostic.")


if __name__ == "__main__":
    test_vwre_with_provider()