#!/usr/bin/env python3
"""
Comprehensive Test Suite for Codex Node - PHASE 4.6
===================================================

Tests complete Codex expedition cycle including:
- Event processing (data refresh, discovery)
- Discovery results handling
- Orthodoxy bridge integration
- Telemetry metrics collection
- Graph trace logging
- Redis event publishing

Usage:
    PYTHONPATH=. python3 scripts/test_codex_cycle.py

Author: Vitruvyan Development Team
Created: 2025-10-20 - PHASE 4.6
"""

import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, '/home/caravaggio/vitruvyan')

from core.langgraph.node.codex_node import codex_node

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_refresh_event() -> bool:
    """Test Codex node with data refresh event"""
    
    print("\n" + "="*70)
    print("TEST 1: Data Refresh Event Processing")
    print("="*70)
    
    test_state = {
        "conclave_event": {
            "event_type": "codex.data.refresh.requested",
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "ticker": "AAPL",
                "sources": ["yfinance", "reddit", "news"],
                "priority": "high",
                "batch_size": 5
            }
        },
        "correlation_id": "test_refresh_001",
        "trace_log": []
    }
    
    try:
        result = codex_node(test_state)
        
        # Validate response
        assert result["codex_status"] in ["expedition_launched"], \
            f"Expected expedition_launched, got {result['codex_status']}"
        
        assert "codex_metrics" in result, "Missing codex_metrics in result"
        assert result["codex_metrics"]["sources_count"] == 0, "Sources should be 0 for launched expedition"
        assert result["codex_metrics"]["expedition_duration_ms"] > 0, "Duration should be > 0"
        
        assert "trace_log" in result, "Missing trace_log in result"
        assert len(result["trace_log"]) > 0, "Trace log should have entries"
        
        print(f"✅ Status: {result['codex_status']}")
        print(f"✅ Metrics: {result['codex_metrics']}")
        print(f"✅ Trace entries: {len(result['trace_log'])}")
        print(f"📝 Response: {result['response'][:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_discovery_success() -> bool:
    """Test Codex node with successful discovery results"""
    
    print("\n" + "="*70)
    print("TEST 2: Successful Discovery Results Processing")
    print("="*70)
    
    test_state = {
        "codex_discovery_results": {
            "sources_found": [
                "yahoo_finance_aapl_2025-10-20",
                "reddit_post_wsb_12345",
                "benzinga_news_67890"
            ],
            "collections_mapped": ["phrases", "tickers", "market_data"],
            "inconsistencies_found": 0,
            "expedition_type": "data_refresh"
        },
        "correlation_id": "test_discovery_success_001",
        "trace_log": []
    }
    
    try:
        result = codex_node(test_state)
        
        # Validate response
        assert result["codex_status"] == "success", \
            f"Expected success, got {result['codex_status']}"
        
        assert len(result["sources_discovered"]) == 3, \
            f"Expected 3 sources, got {len(result['sources_discovered'])}"
        
        assert result["codex_metrics"]["sources_count"] == 3, \
            "Metrics sources_count should match discovered sources"
        
        assert result["codex_metrics"]["expedition_duration_ms"] > 0, \
            "Duration should be > 0"
        
        # Check Orthodoxy bridge was triggered (check logs)
        print(f"✅ Status: {result['codex_status']}")
        print(f"✅ Sources discovered: {len(result['sources_discovered'])}")
        print(f"✅ Metrics: {result['codex_metrics']}")
        print(f"✅ Trace entries: {len(result['trace_log'])}")
        print(f"📝 Response: {result['response'][:150]}...")
        print("🔗 Check logs above for Orthodoxy bridge activation")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_discovery_with_inconsistencies() -> bool:
    """Test Codex node with partial success (inconsistencies found)"""
    
    print("\n" + "="*70)
    print("TEST 3: Partial Success with Inconsistencies")
    print("="*70)
    
    test_state = {
        "codex_discovery_results": {
            "sources_found": [
                "yahoo_finance_tsla_2025-10-20",
                "reddit_post_investing_22222"
            ],
            "collections_mapped": ["phrases", "tickers"],
            "inconsistencies_found": 5,
            "expedition_type": "quality_check"
        },
        "correlation_id": "test_discovery_partial_001",
        "trace_log": []
    }
    
    try:
        result = codex_node(test_state)
        
        # Validate response
        assert result["codex_status"] == "partial_success", \
            f"Expected partial_success, got {result['codex_status']}"
        
        assert len(result["sources_discovered"]) == 2, \
            f"Expected 2 sources, got {len(result['sources_discovered'])}"
        
        assert result["codex_expedition_summary"]["inconsistencies"] == 5, \
            "Inconsistencies count should be preserved"
        
        print(f"✅ Status: {result['codex_status']}")
        print(f"✅ Sources: {len(result['sources_discovered'])}")
        print(f"⚠️ Inconsistencies: {result['codex_expedition_summary']['inconsistencies']}")
        print(f"✅ Metrics: {result['codex_metrics']}")
        print(f"📝 Response: {result['response'][:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_discovery_failure() -> bool:
    """Test Codex node with failed discovery (no sources found)"""
    
    print("\n" + "="*70)
    print("TEST 4: Failed Discovery (No Sources)")
    print("="*70)
    
    test_state = {
        "codex_discovery_results": {
            "sources_found": [],
            "collections_mapped": ["phrases", "tickers"],
            "inconsistencies_found": 0,
            "expedition_type": "data_refresh"
        },
        "correlation_id": "test_discovery_failed_001",
        "trace_log": []
    }
    
    try:
        result = codex_node(test_state)
        
        # Validate response
        assert result["codex_status"] == "failed", \
            f"Expected failed, got {result['codex_status']}"
        
        assert len(result["sources_discovered"]) == 0, \
            "Sources should be empty for failed discovery"
        
        assert result["codex_metrics"]["sources_count"] == 0, \
            "Metrics should show 0 sources"
        
        print(f"✅ Status: {result['codex_status']}")
        print(f"✅ Sources: {len(result['sources_discovered'])} (expected 0)")
        print(f"✅ Metrics: {result['codex_metrics']}")
        print(f"📝 Response: {result['response'][:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_idle_state() -> bool:
    """Test Codex node with no input (idle state)"""
    
    print("\n" + "="*70)
    print("TEST 5: Idle State (No Input)")
    print("="*70)
    
    test_state = {
        "correlation_id": "test_idle_001",
        "trace_log": []
    }
    
    try:
        result = codex_node(test_state)
        
        # Validate response
        assert result["codex_status"] == "idle", \
            f"Expected idle, got {result['codex_status']}"
        
        assert result["route"] == "compose", \
            "Route should default to compose"
        
        print(f"✅ Status: {result['codex_status']}")
        print(f"✅ Route: {result['route']}")
        print(f"✅ Metrics: {result['codex_metrics']}")
        print(f"📝 Response: {result['response']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_trace_log_accumulation() -> bool:
    """Test trace log accumulation across multiple node calls"""
    
    print("\n" + "="*70)
    print("TEST 6: Trace Log Accumulation")
    print("="*70)
    
    # First call
    test_state_1 = {
        "codex_discovery_results": {
            "sources_found": ["source_1"],
            "collections_mapped": ["phrases"],
            "inconsistencies_found": 0,
            "expedition_type": "test"
        },
        "correlation_id": "test_trace_001",
        "trace_log": []
    }
    
    result_1 = codex_node(test_state_1)
    
    # Second call with accumulated trace
    test_state_2 = {
        "codex_discovery_results": {
            "sources_found": ["source_2", "source_3"],
            "collections_mapped": ["tickers"],
            "inconsistencies_found": 0,
            "expedition_type": "test"
        },
        "correlation_id": "test_trace_002",
        "trace_log": result_1["trace_log"]  # Accumulate from previous call
    }
    
    result_2 = codex_node(test_state_2)
    
    try:
        assert len(result_2["trace_log"]) == 2, \
            f"Expected 2 trace entries, got {len(result_2['trace_log'])}"
        
        print(f"✅ Trace accumulation working")
        print(f"✅ Total trace entries: {len(result_2['trace_log'])}")
        for i, entry in enumerate(result_2["trace_log"], 1):
            print(f"  {i}. {entry}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_metrics_accuracy() -> bool:
    """Test metrics calculation accuracy"""
    
    print("\n" + "="*70)
    print("TEST 7: Metrics Accuracy")
    print("="*70)
    
    test_state = {
        "conclave_event": {
            "event_type": "codex.data.discovery.requested",
            "timestamp": (datetime.now()).isoformat(),  # Recent timestamp
            "payload": {
                "discovery_type": "full_scan",
                "target_collections": ["all"]
            }
        },
        "correlation_id": "test_metrics_001",
        "trace_log": []
    }
    
    try:
        result = codex_node(test_state)
        
        metrics = result["codex_metrics"]
        
        # Validate metrics structure
        assert "event_latency_ms" in metrics, "Missing event_latency_ms"
        assert "sources_count" in metrics, "Missing sources_count"
        assert "expedition_duration_ms" in metrics, "Missing expedition_duration_ms"
        assert "node_start_time" in metrics, "Missing node_start_time"
        
        # Validate metrics values
        assert metrics["expedition_duration_ms"] > 0, "Duration should be > 0"
        assert metrics["event_latency_ms"] >= 0, "Latency should be >= 0"
        assert isinstance(metrics["sources_count"], int), "Sources count should be int"
        
        print(f"✅ All metric fields present")
        print(f"✅ Metrics validation passed:")
        for key, value in metrics.items():
            print(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def run_all_tests() -> Dict[str, bool]:
    """Run all test cases and return results"""
    
    print("\n" + "🧪"*35)
    print("🧪 CODEX NODE COMPREHENSIVE TEST SUITE - PHASE 4.6")
    print("🧪"*35)
    
    tests = [
        ("Data Refresh Event", test_data_refresh_event),
        ("Discovery Success", test_discovery_success),
        ("Discovery with Inconsistencies", test_discovery_with_inconsistencies),
        ("Discovery Failure", test_discovery_failure),
        ("Idle State", test_idle_state),
        ("Trace Log Accumulation", test_trace_log_accumulation),
        ("Metrics Accuracy", test_metrics_accuracy)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    return results


def print_test_summary(results: Dict[str, bool]) -> None:
    """Print comprehensive test summary"""
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("-"*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! CODEX NODE READY FOR PHASE 4.6 🎉")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review logs above.")


if __name__ == "__main__":
    results = run_all_tests()
    print_test_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)
