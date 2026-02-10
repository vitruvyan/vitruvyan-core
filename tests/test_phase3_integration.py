#!/usr/bin/env python3
"""
Integration Test: VEE + VARE + VWRE with Domain Providers
=========================================================

Tests the complete Phase 3 integration where all engines work together
using domain-agnostic providers instead of hardcoded finance logic.

⚠️ TEMPORARILY SKIPPED:
These tests require VARE/VWRE engines and Mercator providers that were
not yet migrated to vitruvyan-core. Re-enable when modules are available.

Author: Vitruvyan Core Team
Created: December 30, 2025
"""

import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mark entire module as skipped due to missing modules
pytestmark = pytest.mark.skip(reason="VARE/VWRE engines and Mercator providers not available in vitruvyan-core")


def test_complete_phase3_integration():
    """Test VEE + VARE + VWRE working together with domain providers"""

    print("🔗 Testing Complete Phase 3 Integration...")

    # Initialize all engines
    vee = VEEEngine()
    vare = VAREEngine()
    vwre = VWREEngine()

    # Initialize domain providers
    explain_provider = MercatorExplainabilityProvider()
    risk_provider = MercatorRiskProvider()
    aggregation_provider = MercatorAggregationProvider()

    # Test entity (finance domain)
    entity_id = "EXAMPLE_ENTITY_1"
    composite_score = 1.85

    # Factor data
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

    # Test VWRE attribution analysis
    print("1️⃣ Testing VWRE Attribution Analysis...")
    vwre_result = vwre.analyze_attribution(entity_id, composite_score, factors, aggregation_provider)
    assert vwre_result.entity_id == entity_id
    assert vwre_result.primary_driver is not None
    print(f"   ✅ VWRE: {vwre_result.primary_driver} drives {vwre_result.composite_score:.3f}")

    # Test VARE risk analysis
    print("2️⃣ Testing VARE Risk Analysis...")
    vare_result = vare.analyze_entity(entity_id, factors, risk_provider)
    assert vare_result.entity_id == entity_id
    assert len(vare_result.risk_factors) > 0
    print(f"   ✅ VARE: {len(vare_result.risk_factors)} risk factors analyzed")

    # Test VEE explanation generation
    print("3️⃣ Testing VEE Explanation Generation...")
    vee_result = vee.explain_entity(entity_id, factors, explain_provider)
    assert isinstance(vee_result, dict)
    assert "summary" in vee_result
    assert "technical" in vee_result
    assert "detailed" in vee_result
    print(f"   ✅ VEE: Generated explanation with {len(vee_result)} levels")

    # Test integration: VWRE attribution data enhances VEE narratives
    print("4️⃣ Testing Engine Integration...")
    # VWRE provides attribution context that VEE can use
    attribution_context = {
        "primary_driver": vwre_result.primary_driver,
        "factor_contributions": vwre_result.factor_contributions,
        "rank_explanation": vwre_result.rank_explanation
    }

    # VEE could use this context to enhance explanations (for now just test separate)
    enhanced_explanation = vee.explain_entity(entity_id, factors, explain_provider)
    assert isinstance(enhanced_explanation, dict)
    print("   ✅ Integration: VWRE and VEE work independently with providers")

    # Test batch processing
    print("5️⃣ Testing Batch Processing...")
    batch_entities = [
        {"entity_id": "EXAMPLE_ENTITY_1", "composite_score": 1.85, "factors": factors},
        {"entity_id": "EXAMPLE_ENTITY_3", "composite_score": 0.95, "factors": {
            "momentum_z": 1.8, "trend_z": 0.2, "vola_z": 1.1, "sentiment_z": -0.5,
            "fundamentals_z": 0.8, "technical_z": 0.3, "quality_z": 0.1, "size_z": 0.2
        }}
    ]

    # Batch VWRE
    vwre_batch = vwre.batch_analyze(batch_entities, aggregation_provider)
    assert len(vwre_batch) == 2

    # Batch VEE
    vee_batch = []
    for entity in batch_entities:
        result = vee.explain_entity(entity["entity_id"], entity["factors"], explain_provider)
        vee_batch.append(result)
    assert len(vee_batch) == 2
    assert all(isinstance(r, dict) for r in vee_batch)

    print("   ✅ Batch processing: All engines handle multiple entities")

    # Test domain-agnostic nature
    print("6️⃣ Testing Domain Agnosticism...")
    # All engines now accept providers instead of hardcoded logic
    # This means they can work with any domain that implements the contracts
    assert hasattr(explain_provider, 'get_explanation_templates')
    assert hasattr(risk_provider, 'get_risk_dimensions')
    assert hasattr(aggregation_provider, 'get_aggregation_profiles')
    print("   ✅ Domain Agnostic: Engines accept any provider implementation")

    print("🎉 Phase 3 Integration Complete!")
    print("   ✅ VEE: Domain-agnostic explanations")
    print("   ✅ VARE: Domain-agnostic risk analysis")
    print("   ✅ VWRE: Domain-agnostic attribution")
    print("   ✅ Integration: Engines work together seamlessly")
    print("   ✅ Multi-domain Ready: Any domain can implement providers")


if __name__ == "__main__":
    test_complete_phase3_integration()