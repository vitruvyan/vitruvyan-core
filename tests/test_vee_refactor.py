#!/usr/bin/env python3
"""
Test script for VEE domain-agnostic refactoring
"""

from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_engine import VEEEngine
from vitruvyan_core.verticals.mercator.providers import MercatorExplainabilityProvider

def test_vee_domain_agnostic():
    """Test the refactored VEE components with domain provider"""

    # Test data
    entity_id = "EXAMPLE_ENTITY_1"
    test_metrics = {
        'momentum_z': 0.8,
        'vola_z': -0.5,
        'sentiment_z': 0.3,
        'technical_score': 65,
        'risk_score': 45,
        'composite_score': 70
    }

    # Initialize components
    engine = VEEEngine()
    provider = MercatorExplainabilityProvider()

    # Test explain_entity
    try:
        result = engine.explain_entity(entity_id, test_metrics, provider)
        print("✅ VEE Engine explain_entity: SUCCESS")
        print(f"Entity: {entity_id}")
        print(f"Summary: {result['summary'][:100]}...")
        print(f"Technical: {result['technical'][:100]}...")
        print(f"Detailed: {result['detailed'][:100]}...")
    except Exception as e:
        print(f"❌ VEE Engine explain_entity: FAILED - {e}")
        return False

    # Test standalone functions
    try:
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_analyzer import analyze_kpi
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_generator import generate_explanation

        analysis = analyze_kpi(entity_id, test_metrics)
        print("✅ VEE Analyzer analyze_kpi: SUCCESS")

        explanation = generate_explanation(entity_id, analysis)
        print("✅ VEE Generator generate_explanation: SUCCESS")

    except Exception as e:
        print(f"❌ Standalone functions: FAILED - {e}")
        return False

    print("\n🎉 All VEE domain-agnostic tests PASSED!")
    return True

if __name__ == "__main__":
    test_vee_domain_agnostic()