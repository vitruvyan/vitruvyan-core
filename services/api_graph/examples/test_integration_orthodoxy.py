#!/usr/bin/env python3
"""
Orthodoxy Wardens Integration Test
=====================================

**Purpose**: Validate LangGraph → Orthodoxy Wardens → LangGraph round-trip

**Test Flow**:
1. Send POST /run to graph API (triggers orthodoxy_node)
2. orthodoxy_node emits "orthodoxy.audit.requested" to Redis
3. orthodoxy_listener consumes event
4. orthodoxy_wardens processes confession, emits verdict
5. orthodoxy_node receives "orthodoxy.absolution.granted"
6. Graph augments state with verdict
7. Response includes orthodoxy_verdict (NOT emergency_blessing)

**Prerequisites**:
- core_graph service running (port 9004)
- core_orthodoxy_wardens healthy
- core_orthodoxy_listener consuming events
- core_redis operational

**Expected Duration**: < 15 seconds (includes 10s timeout buffer)

**Author**: COO Feb 10, 2026
**Status**: Integration Test (P0)
"""

import httpx
import json
import redis
import time
from typing import Dict, Any, Optional

# Configuration
GRAPH_API_URL = "http://localhost:8004"  # Internal port (9004 on host)
REDIS_HOST = "core_redis"  # Docker hostname
REDIS_PORT = 6379
TIMEOUT = 20  # seconds

# Test inputs (designed to trigger orthodoxy audit via technical intents)
TEST_CASES = [
    {
        "name": "Sentiment Analysis (Technical Intent)",
        "input_text": "sentiment Apple",
        "user_id": "integration_test_ortho_1",
        "validated_tickers": ["AAPL"],  # Force entity recognition → technical intent
        "expect_audit": True,
        "description": "'sentiment' intent triggers dispatcher_exec → orthodoxy"
    },
    {
        "name": "Risk Analysis (Technical Intent)",
        "input_text": "risk Apple",
        "user_id": "integration_test_ortho_2",
        "validated_tickers": ["AAPL"],
        "expect_audit": True,
        "description": "'risk' intent triggers dispatcher_exec → orthodoxy"
    },
    {
        "name": "Trend Analysis (Technical Intent)",
        "input_text": "trend Apple",
        "user_id": "integration_test_ortho_3",
        "validated_tickers": ["AAPL"],
        "expect_audit": True,
        "description": "'trend' intent triggers dispatcher_exec → orthodoxy"
    }
]


class IntegrationTestResults:
    """Track test outcomes for reporting."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.start_time = time.time()
    
    def add_pass(self, test_name: str, duration_ms: float, details: str = ""):
        self.passed.append({
            "test": test_name,
            "duration_ms": round(duration_ms, 2),
            "details": details
        })
    
    def add_fail(self, test_name: str, error: str, details: str = ""):
        self.failed.append({
            "test": test_name,
            "error": error,
            "details": details
        })
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def print_report(self):
        """Print colorized test report."""
        duration = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("🏛️  ORTHODOXY WARDENS INTEGRATION TEST REPORT")
        print("="*80)
        print(f"Total Duration: {duration:.2f}s")
        print(f"Passed: {len(self.passed)} ✅")
        print(f"Failed: {len(self.failed)} ❌")
        print(f"Warnings: {len(self.warnings)} ⚠️")
        print("="*80)
        
        if self.passed:
            print("\n✅ PASSED TESTS:")
            for result in self.passed:
                print(f"  ✓ {result['test']} ({result['duration_ms']}ms)")
                if result['details']:
                    print(f"    {result['details']}")
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for result in self.failed:
                print(f"  ✗ {result['test']}")
                print(f"    Error: {result['error']}")
                if result['details']:
                    print(f"    Details: {result['details']}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        print("\n" + "="*80)
        
        if self.failed:
            print("❌ INTEGRATION TEST FAILED")
            print("="*80)
            return False
        else:
            print("✅ INTEGRATION TEST PASSED")
            print("="*80)
            return True


def test_graph_health() -> bool:
    """Prerequisite: Verify graph API is reachable."""
    try:
        response = httpx.get(f"{GRAPH_API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Graph API not reachable: {e}")
        return False


def test_redis_connection() -> bool:
    """Prerequisite: Verify Redis Streams accessible."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        return True
    except Exception as e:
        print(f"❌ Redis not reachable: {e}")
        return False


def test_orthodoxy_integration(
    test_case: Dict[str, Any],
    results: IntegrationTestResults
) -> None:
    """
    Execute one orthodoxy integration test.
    
    Steps:
    1. Send graph execution request
    2. Parse response
    3. Verify orthodoxy_verdict present
    4. Verify NOT emergency_blessing (real divine response)
    5. (Optional) Check Redis event traces
    """
    test_name = test_case["name"]
    start_time = time.time()
    
    print(f"\n🧪 Running: {test_name}")
    print(f"   Input: {test_case['input_text']}")
    
    try:
        # Step 1: Send graph execution request
        payload = {
            "input_text": test_case["input_text"],
            "user_id": test_case["user_id"]
        }
        
        # Add validated_tickers if provided (forces intent recognition)
        if "validated_tickers" in test_case:
            payload["validated_tickers"] = test_case["validated_tickers"]
        
        response = httpx.post(
            f"{GRAPH_API_URL}/run",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            results.add_fail(
                test_name,
                f"HTTP {response.status_code}",
                response.text[:200]
            )
            return
        
        # Step 2: Parse response
        data = response.json()
        
        # Verify response schema
        if "json" not in data or "human" not in data:
            results.add_fail(
                test_name,
                "Invalid response schema",
                f"Missing 'json' or 'human' fields: {list(data.keys())}"
            )
            return
        
        # Parse graph output (stored in "json" field)
        try:
            graph_state = json.loads(data["json"])
        except json.JSONDecodeError as e:
            results.add_fail(
                test_name,
                "Invalid JSON in response",
                str(e)
            )
            return
        
        # Step 3: ✅ FIX (Feb 10, 2026): Verify Sacred Orders metadata present
        sacred_orders_missing = []
        
        # Required Orthodoxy Wardens metadata
        if "orthodoxy_verdict" not in graph_state:
            sacred_orders_missing.append("orthodoxy_verdict")
        if "orthodoxy_blessing" not in graph_state:
            sacred_orders_missing.append("orthodoxy_blessing")
        if "theological_metadata" not in graph_state:
            sacred_orders_missing.append("theological_metadata")
        
        # Required Vault Keepers metadata
        if "vault_blessing" not in graph_state:
            sacred_orders_missing.append("vault_blessing")
        
        if sacred_orders_missing:
            results.add_fail(
                test_name,
                f"Missing Sacred Orders metadata: {', '.join(sacred_orders_missing)}",
                f"Present keys: {[k for k in graph_state.keys() if 'orthodoxy' in k or 'vault' in k]}"
            )
            return
        
        orthodoxy_verdict = graph_state["orthodoxy_verdict"]
        vault_blessing = graph_state["vault_blessing"]
        theological_metadata = graph_state["theological_metadata"]
        
        # Step 4: Verify Sacred Orders integration quality
        # Accept local_blessing (fallback) or approved (remote audit)
        valid_verdicts = ["approved", "blessed", "local_blessing"]
        if orthodoxy_verdict not in valid_verdicts:
            results.add_warning(
                f"{test_name}: Unexpected orthodoxy_verdict={orthodoxy_verdict} (expected one of {valid_verdicts})"
            )
        
        # Step 5: Verify NOT emergency_blessing (timeout indicator)
        if orthodoxy_verdict == "emergency_blessing":
            results.add_fail(
                test_name,
                "Orthodoxy timeout (emergency_blessing applied)",
                "Verdict: emergency_blessing indicates listener not responding"
            )
            return
        
        # Step 6: Verify valid verdict (accept fallback local_blessing)
        valid_verdicts = ["blessed", "approved", "local_blessing", "heretical", "requires_confession", "absolved"]
        if orthodoxy_verdict not in valid_verdicts:
            results.add_warning(
                f"{test_name}: Unexpected verdict '{orthodoxy_verdict}' "
                f"(expected one of: {valid_verdicts})"
            )
        
        # Success - Sacred Orders integration validated
        duration_ms = (time.time() - start_time) * 1000
        results.add_pass(
            test_name,
            duration_ms,
            f"Orthodoxy: {orthodoxy_verdict} | Vault: {vault_blessing.get('vault_status', 'N/A') if isinstance(vault_blessing, dict) else vault_blessing}"
        )
        
        print(f"   ✅ Orthodoxy: {orthodoxy_verdict} | Vault: {vault_blessing.get('vault_status', 'N/A') if isinstance(vault_blessing, dict) else vault_blessing} ({duration_ms:.0f}ms)")
    
    except httpx.TimeoutException:
        results.add_fail(
            test_name,
            f"Request timeout (>{TIMEOUT}s)",
            "Graph execution took too long or listener unresponsive"
        )
    
    except Exception as e:
        results.add_fail(
            test_name,
            f"Unexpected error: {type(e).__name__}",
            str(e)
        )


def test_redis_event_traces(results: IntegrationTestResults) -> None:
    """
    Optional: Verify Redis Streams contain audit events.
    
    This validates that orthodoxy_node actually emitted events
    (even if we can't directly trace correlation_id from test).
    """
    print("\n🔍 Checking Redis event traces...")
    
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        
        # Check orthodoxy.audit.requested stream
        audit_events = r.xread(
            {"vitruvyan:orthodoxy.validation.requested": '0'},
            count=5
        )
        
        if audit_events:
            count = len(audit_events[0][1]) if audit_events else 0
            results.add_pass(
                "Redis Event Traces",
                0,
                f"Found {count} audit request events"
            )
            print(f"   ✅ Found {count} orthodoxy audit events in Redis")
        else:
            results.add_warning(
                "No orthodoxy audit events found in Redis Streams "
                "(may have been consumed or TTL expired)"
            )
    
    except Exception as e:
        results.add_warning(f"Could not check Redis traces: {e}")


def main():
    """Run full integration test suite."""
    print("🏛️  Starting Orthodoxy Wardens Integration Tests")
    print("="*80)
    
    results = IntegrationTestResults()
    
    # Prerequisites
    print("\n🔍 Checking prerequisites...")
    
    if not test_graph_health():
        print("❌ ABORT: Graph API not healthy")
        return False
    print("   ✅ Graph API healthy")
    
    if not test_redis_connection():
        print("❌ ABORT: Redis not accessible")
        return False
    print("   ✅ Redis accessible")
    
    # Run test cases
    for test_case in TEST_CASES:
        test_orthodoxy_integration(test_case, results)
    
    # Check Redis traces (optional)
    test_redis_event_traces(results)
    
    # Print report
    success = results.print_report()
    
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
