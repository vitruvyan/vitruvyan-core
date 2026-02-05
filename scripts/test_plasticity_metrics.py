#!/usr/bin/env python3
"""
Test Plasticity Metrics Integration
====================================

Quick test to verify metrics are properly integrated and exposed.

Usage:
    python3 scripts/test_plasticity_metrics.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vitruvyan_core.core.foundation.cognitive_bus.plasticity import metrics as plasticity_metrics

def test_metrics_import():
    """Test that metrics module imports correctly."""
    print("✅ Metrics module imported successfully")
    
    # Check that all metrics are defined
    metrics_to_check = [
        'plasticity_adjustment_total',
        'plasticity_adjustment_rejected_total',
        'plasticity_adjustment_delta',
        'plasticity_rollback_total',
        'plasticity_success_rate',
        'plasticity_outcome_recorded_total',
        'plasticity_learning_cycle_duration_seconds',
        'plasticity_learning_cycles_total',
        'plasticity_learning_cycle_adjustments',
        'plasticity_parameters_adjustable',
        'plasticity_parameters_disabled',
        'plasticity_parameter_value',
        'plasticity_parameter_bounds',
        'plasticity_errors_total'
    ]
    
    for metric_name in metrics_to_check:
        if hasattr(plasticity_metrics, metric_name):
            print(f"  ✓ {metric_name}")
        else:
            print(f"  ✗ {metric_name} NOT FOUND")
            return False
    
    return True

def test_helper_functions():
    """Test that helper functions are available."""
    print("\n✅ Testing helper functions...")
    
    functions_to_check = [
        'record_adjustment',
        'record_rollback',
        'record_outcome',
        'update_success_rate',
        'update_parameter_state',
        'update_consumer_parameters',
        'record_learning_cycle',
        'record_error'
    ]
    
    for func_name in functions_to_check:
        if hasattr(plasticity_metrics, func_name):
            print(f"  ✓ {func_name}()")
        else:
            print(f"  ✗ {func_name}() NOT FOUND")
            return False
    
    return True

def test_metrics_recording():
    """Test that metrics can be recorded without errors."""
    print("\n✅ Testing metrics recording...")
    
    try:
        # Test adjustment recording
        plasticity_metrics.record_adjustment(
            consumer="TestConsumer",
            parameter="test_param",
            delta=0.05,
            reason="test",
            applied=True
        )
        print("  ✓ record_adjustment()")
        
        # Test success rate update
        plasticity_metrics.update_success_rate(
            consumer="TestConsumer",
            parameter="test_param",
            success_rate=0.85
        )
        print("  ✓ update_success_rate()")
        
        # Test parameter state update
        plasticity_metrics.update_parameter_state(
            consumer="TestConsumer",
            parameter="test_param",
            value=0.75,
            min_value=0.0,
            max_value=1.0,
            disabled=False
        )
        print("  ✓ update_parameter_state()")
        
        # Test consumer parameters update
        plasticity_metrics.update_consumer_parameters(
            consumer="TestConsumer",
            adjustable_count=5,
            disabled_count=0
        )
        print("  ✓ update_consumer_parameters()")
        
        # Test learning cycle recording
        plasticity_metrics.record_learning_cycle(
            duration_seconds=1.5,
            adjustments_proposed=3,
            adjustments_applied=2,
            adjustments_rejected=1
        )
        print("  ✓ record_learning_cycle()")
        
        # Test outcome recording
        plasticity_metrics.record_outcome(
            consumer="TestConsumer",
            parameter="test_param",
            outcome_type="success",
            outcome_value=1.0
        )
        print("  ✓ record_outcome()")
        
        return True
    
    except Exception as e:
        print(f"  ✗ Error recording metrics: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Plasticity Metrics Integration Test")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Import
    if not test_metrics_import():
        all_passed = False
    
    # Test 2: Helper functions
    if not test_helper_functions():
        all_passed = False
    
    # Test 3: Recording
    if not test_metrics_recording():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nNext steps:")
        print("1. Start vitruvyan API: docker compose up -d vitruvyan_api_graph")
        print("2. Check metrics endpoint: curl http://localhost:8004/metrics | grep plasticity")
        print("3. Verify all 15 metrics are exposed")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
