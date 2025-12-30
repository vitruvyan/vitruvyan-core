"""
Phase 3D: Integration Tests

Tests for the complete Neural Engine → VWRE → VARE → VEE pipeline
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# Import the demo orchestrator
from vertical_integration_demo import MercatorLiteOrchestrator


class TestVerticalIntegration:
    """Test complete vertical integration pipeline"""

    @pytest.fixture
    def orchestrator(self):
        """Create test orchestrator"""
        return MercatorLiteOrchestrator()

    @pytest.fixture
    def sample_entity_data(self):
        """Sample entity data for testing"""
        return {
            "entity_id": "TEST_STOCK",
            "current_price": 100.0,
            "previous_price": 95.0,
            "volume": 1000000,
            "market_cap": 1000000000
        }

    def test_pipeline_execution(self, orchestrator, sample_entity_data):
        """Test complete pipeline executes without errors"""
        entity_id = sample_entity_data["entity_id"]

        # Execute pipeline
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        # Verify result structure
        assert result['entity_id'] == entity_id
        assert 'timestamp' in result
        assert 'neural_evaluation' in result
        assert 'attribution_analysis' in result
        assert 'risk_assessment' in result
        assert 'explanation' in result

    def test_neural_engine_integration(self, orchestrator, sample_entity_data):
        """Test Neural Engine produces expected outputs"""
        entity_id = sample_entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        ne_result = result['neural_evaluation']
        assert 'composite_score' in ne_result
        assert 'factor_contributions' in ne_result
        assert 'rank' in ne_result

        # Score should be a float
        assert isinstance(ne_result['composite_score'], (int, float))

    def test_vwre_integration(self, orchestrator, sample_entity_data):
        """Test VWRE attribution analysis"""
        entity_id = sample_entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        vwre_result = result['attribution_analysis']
        assert 'profile' in vwre_result
        assert 'primary_driver' in vwre_result
        assert 'factor_contributions' in vwre_result
        assert 'factor_percentages' in vwre_result

    def test_vare_integration(self, orchestrator, sample_entity_data):
        """Test VARE risk assessment"""
        entity_id = sample_entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        vare_result = result['risk_assessment']
        assert 'overall_risk' in vare_result
        assert 'risk_category' in vare_result
        assert 'market_risk' in vare_result
        assert 'volatility_risk' in vare_result
        assert 'liquidity_risk' in vare_result
        assert 'correlation_risk' in vare_result

        # Risk scores should be 0-100
        assert 0 <= vare_result['overall_risk'] <= 100
        assert vare_result['risk_category'] in ['LOW', 'MODERATE', 'HIGH', 'EXTREME']

    def test_vee_integration(self, orchestrator, sample_entity_data):
        """Test VEE explainability generation"""
        entity_id = sample_entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        vee_result = result['explanation']
        assert 'summary' in vee_result
        assert 'technical' in vee_result
        assert 'detailed' in vee_result

        # Explanations should be non-empty strings
        assert len(vee_result['summary']) > 0
        assert len(vee_result['technical']) > 0
        assert len(vee_result['detailed']) > 0

    def test_data_flow_integrity(self, orchestrator, sample_entity_data):
        """Test data flows correctly between components"""
        entity_id = sample_entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        # All components should reference the same entity
        assert result['entity_id'] == entity_id
        assert result['attribution_analysis']['entity_id'] == entity_id
        assert result['risk_assessment']['entity_id'] == entity_id
        assert result['explanation']['entity_id'] == entity_id

    def test_batch_processing(self, orchestrator):
        """Test processing multiple entities"""
        entities = [
            {"entity_id": "STOCK_A", "current_price": 100, "previous_price": 95, "volume": 1000000},
            {"entity_id": "STOCK_B", "current_price": 200, "previous_price": 205, "volume": 500000},
            {"entity_id": "STOCK_C", "current_price": 50, "previous_price": 48, "volume": 2000000}
        ]

        results = []
        for entity_data in entities:
            entity_id = entity_data["entity_id"]
            result = orchestrator.process_entity(entity_id, entity_data)
            results.append(result)

        # Should have results for all entities
        assert len(results) == 3

        # All should be successful
        for result in results:
            assert 'neural_evaluation' in result
            assert 'attribution_analysis' in result
            assert 'risk_assessment' in result
            assert 'explanation' in result

    def test_error_handling(self, orchestrator):
        """Test error handling for invalid data"""
        # Test with missing required fields
        invalid_data = {"entity_id": "INVALID"}

        result = orchestrator.process_entity("INVALID", invalid_data)

        # Should still return a result structure (even if with errors)
        assert result['entity_id'] == "INVALID"
        assert 'timestamp' in result

    def test_boundary_maintenance(self, orchestrator, sample_entity_data):
        """Test that core boundaries are maintained"""
        entity_id = sample_entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, sample_entity_data)

        # Neural evaluation should not contain domain-specific explanations
        ne_result = result['neural_evaluation']
        assert 'explanation' not in ne_result
        assert 'risk' not in str(ne_result).lower()

        # Attribution should not contain business recommendations
        attr_result = result['attribution_analysis']
        assert 'buy' not in str(attr_result).lower()
        assert 'sell' not in str(attr_result).lower()


if __name__ == "__main__":
    # Run tests manually if pytest not available
    import sys

    orchestrator = MercatorLiteOrchestrator()
    sample_data = {
        "entity_id": "TEST_STOCK",
        "current_price": 100.0,
        "previous_price": 95.0,
        "volume": 1000000,
        "market_cap": 1000000000
    }

    print("🧪 Running Phase 3D Integration Tests...")

    try:
        # Test basic pipeline
        result = orchestrator.process_entity("TEST_STOCK", sample_data)
        assert 'neural_evaluation' in result
        assert 'attribution_analysis' in result
        assert 'risk_assessment' in result
        assert 'explanation' in result
        print("✅ Pipeline execution test passed")

        # Test data flow
        assert result['entity_id'] == "TEST_STOCK"
        assert result['attribution_analysis']['entity_id'] == "TEST_STOCK"
        print("✅ Data flow integrity test passed")

        # Test risk categories
        risk_cat = result['risk_assessment']['risk_category']
        assert risk_cat in ['LOW', 'MODERATE', 'HIGH', 'EXTREME']
        print("✅ Risk assessment test passed")

        print("\n🎉 All integration tests passed!")
        print("🏛️ Phase 3D Neural Engine integration verified")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)