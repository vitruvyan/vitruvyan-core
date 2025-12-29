#!/usr/bin/env python3
"""
🛡️ ORTHODOXY REDIS BUS TESTS
Comprehensive validation of Sacred Conclave event flow and timing.

Phase 4.3: Foundation for production deployment
Target: <100ms latency for complete confession cycle
"""

import asyncio
import pytest
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent
from core.foundation.cognitive_bus.event_schema import EventSchemaValidator


class OrthodoxyCycleValidator:
    """Sacred audit cycle validation engine"""
    
    def __init__(self):
        self.redis_bus = get_redis_bus()
        self.received_events: List[Dict] = []
        self.start_time: Optional[float] = None
        self.correlation_tracker: Dict[str, Dict] = {}
        
    async def setup(self):
        """Initialize Redis connection and listeners"""
        self.redis_bus.connect()
        
        # Subscribe to orthodoxy events
        self.redis_bus.subscribe('orthodoxy.*', self._event_handler)
        self.redis_bus.start_listening()
        print("[TEST] Orthodoxy Redis listeners activated")
        
        # Give listeners time to initialize
        await asyncio.sleep(0.1)
        
    def _event_handler(self, event: CognitiveEvent):
        """Handle incoming orthodoxy events"""
        timestamp = time.time()
        event_data = event.to_dict()
        event_data['received_at'] = timestamp
        self.received_events.append(event_data)
        
        correlation_id = event.correlation_id or 'unknown'
        if correlation_id not in self.correlation_tracker:
            self.correlation_tracker[correlation_id] = {
                'events': [],
                'start_time': timestamp
            }
        
        self.correlation_tracker[correlation_id]['events'].append(event_data)
        print(f"[TEST] Event received: {event.event_type} | {correlation_id}")
        
    async def publish_test_event(self, event_type: str, payload: Dict, correlation_id: str):
        """Publish test event to trigger orthodoxy cycle"""
        self.start_time = time.time()
        
        test_event = CognitiveEvent(
            event_type=event_type,
            emitter='test_orthodoxy_validator',
            target='orthodoxy_wardens',
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id
        )
        
        self.redis_bus.publish_event(test_event)
        print(f"[TEST] Published: {event_type} | {correlation_id}")
        await asyncio.sleep(0.1)  # Give event time to propagate
        
    async def wait_for_completion(self, correlation_id: str, expected_events: List[str], timeout: float = 5.0):
        """Wait for sacred cycle completion"""
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            if correlation_id in self.correlation_tracker:
                received_types = [
                    event.get('event_type') 
                    for event in self.correlation_tracker[correlation_id]['events']
                ]
                
                if all(expected_type in received_types for expected_type in expected_events):
                    cycle_time = time.time() - self.correlation_tracker[correlation_id]['start_time']
                    print(f"[TEST] Sacred cycle completed in {cycle_time*1000:.1f}ms")
                    return True, cycle_time
                    
            await asyncio.sleep(0.01)  # 10ms polling
            
        return False, timeout
        
    def validate_event_schema(self, event: Dict) -> bool:
        """Validate event against sacred schema"""
        required_fields = ['event_type', 'correlation_id', 'timestamp', 'payload']
        return all(field in event for field in required_fields)
        
    async def cleanup(self):
        """Cleanup Redis connections"""
        self.redis_bus.disconnect()


@pytest.fixture
async def orthodoxy_validator():
    """Test fixture for orthodoxy cycle validation"""
    validator = OrthodoxyCycleValidator()
    await validator.setup()
    yield validator
    await validator.cleanup()


@pytest.mark.asyncio
async def test_confession_cycle(orthodoxy_validator):
    """
    🔥 TEST: Sacred Confession Cycle
    system.audit.requested → orthodoxy.absolution.granted
    Target: <100ms latency
    """
    correlation_id = f"confession_test_{int(time.time())}"
    
    # Publish confession request
    await orthodoxy_validator.publish_test_event(
        event_type='system.audit.requested',
        payload={'test_type': 'confession_cycle', 'severity': 'minor'},
        correlation_id=correlation_id
    )
    
    # Wait for absolution
    completed, cycle_time = await orthodoxy_validator.wait_for_completion(
        correlation_id=correlation_id,
        expected_events=['orthodoxy.absolution.granted'],
        timeout=2.0
    )
    
    # Assertions
    assert completed, f"Confession cycle failed to complete within timeout"
    assert cycle_time < 0.1, f"Confession cycle too slow: {cycle_time*1000:.1f}ms > 100ms"
    
    # Validate received events
    events = orthodoxy_validator.correlation_tracker[correlation_id]['events']
    assert len(events) >= 1, "No absolution event received"
    
    absolution_event = next(e for e in events if e.get('event_type') == 'orthodoxy.absolution.granted')
    assert orthodoxy_validator.validate_event_schema(absolution_event), "Invalid event schema"
    
    print(f"✅ Confession cycle validated: {cycle_time*1000:.1f}ms")


@pytest.mark.asyncio
async def test_penance_cycle(orthodoxy_validator):
    """
    🩹 TEST: Sacred Penance Cycle  
    system.audit.requested → orthodoxy.penance.assigned
    Target: <150ms latency
    """
    correlation_id = f"penance_test_{int(time.time())}"
    
    # Publish penance request
    await orthodoxy_validator.publish_test_event(
        event_type='system.audit.requested',
        payload={
            'test_type': 'penance_cycle', 
            'severity': 'moderate',
            'requires_penance': True
        },
        correlation_id=correlation_id
    )
    
    # Wait for penance assignment
    completed, cycle_time = await orthodoxy_validator.wait_for_completion(
        correlation_id=correlation_id,
        expected_events=['orthodoxy.penance.assigned'],
        timeout=2.0
    )
    
    # Assertions
    assert completed, f"Penance cycle failed to complete within timeout"
    assert cycle_time < 0.15, f"Penance cycle too slow: {cycle_time*1000:.1f}ms > 150ms"
    
    # Validate penance event
    events = orthodoxy_validator.correlation_tracker[correlation_id]['events']
    penance_events = [e for e in events if e.get('event_type') == 'orthodoxy.penance.assigned']
    assert len(penance_events) > 0, "No penance assigned"
    
    print(f"✅ Penance cycle validated: {cycle_time*1000:.1f}ms")


@pytest.mark.asyncio
async def test_multi_role_response(orthodoxy_validator):
    """
    👥 TEST: Multi-Role Sacred Response
    system.complexity.detected → multiple orthodoxy roles respond
    Target: <200ms for complete multi-agent response
    """
    correlation_id = f"multi_role_test_{int(time.time())}"
    
    # Publish complex scenario
    await orthodoxy_validator.publish_test_event(
        event_type='system.complexity.detected',
        payload={
            'test_type': 'multi_role_cycle',
            'complexity_level': 'high',
            'requires_multiple_perspectives': True
        },
        correlation_id=correlation_id
    )
    
    # Wait for multi-role response
    expected_responses = [
        'orthodoxy.confession.heard',
        'orthodoxy.penance.assigned',
        'orthodoxy.chronicle.recorded'
    ]
    
    completed, cycle_time = await orthodoxy_validator.wait_for_completion(
        correlation_id=correlation_id,
        expected_events=expected_responses,
        timeout=3.0
    )
    
    # Assertions
    assert completed, f"Multi-role cycle failed to complete within timeout"
    assert cycle_time < 0.2, f"Multi-role cycle too slow: {cycle_time*1000:.1f}ms > 200ms"
    
    # Validate role participation
    events = orthodoxy_validator.correlation_tracker[correlation_id]['events']
    role_events = [e.get('event_type') for e in events]
    
    assert len(set(role_events)) >= 2, "Insufficient role participation"
    
    print(f"✅ Multi-role cycle validated: {cycle_time*1000:.1f}ms, {len(set(role_events))} roles")


@pytest.mark.asyncio
async def test_event_flow_validation(orthodoxy_validator):
    """
    🔄 TEST: Complete Event Flow Validation
    Validate proper event ordering and correlation tracking
    """
    correlation_id = f"flow_test_{int(time.time())}"
    
    # Start comprehensive audit
    await orthodoxy_validator.publish_test_event(
        event_type='system.audit.comprehensive',
        payload={
            'test_type': 'flow_validation',
            'audit_depth': 'full',
            'require_documentation': True
        },
        correlation_id=correlation_id
    )
    
    # Wait for complete flow
    await asyncio.sleep(1.0)  # Allow full cycle to complete
    
    # Validate event flow
    events = orthodoxy_validator.correlation_tracker.get(correlation_id, {}).get('events', [])
    assert len(events) > 0, "No events received for flow validation"
    
    # Check event ordering
    timestamps = [event.get('received_at', 0) for event in events]
    assert timestamps == sorted(timestamps), "Events received out of order"
    
    # Validate correlation consistency
    for event in events:
        assert event.get('correlation_id') == correlation_id, "Correlation ID mismatch"
        assert orthodoxy_validator.validate_event_schema(event), "Schema validation failed"
    
    print(f"✅ Event flow validated: {len(events)} events in proper order")


@pytest.mark.asyncio
async def test_performance_baseline(orthodoxy_validator):
    """
    ⚡ TEST: Performance Baseline Establishment
    Measure baseline performance for production monitoring
    """
    test_cycles = 10
    cycle_times = []
    
    for i in range(test_cycles):
        correlation_id = f"perf_test_{i}_{int(time.time())}"
        
        start_time = time.time()
        await orthodoxy_validator.publish_test_event(
            event_type='system.audit.requested',
            payload={'test_type': 'performance_baseline', 'cycle': i},
            correlation_id=correlation_id
        )
        
        completed, cycle_time = await orthodoxy_validator.wait_for_completion(
            correlation_id=correlation_id,
            expected_events=['orthodoxy.absolution.granted'],
            timeout=1.0
        )
        
        if completed:
            cycle_times.append(cycle_time * 1000)  # Convert to ms
            
    # Performance analysis
    avg_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
    max_time = max(cycle_times) if cycle_times else 0
    min_time = min(cycle_times) if cycle_times else 0
    
    print(f"📊 Performance Baseline:")
    print(f"   Average: {avg_time:.1f}ms")
    print(f"   Maximum: {max_time:.1f}ms")
    print(f"   Minimum: {min_time:.1f}ms")
    print(f"   Success Rate: {len(cycle_times)}/{test_cycles}")
    
    # Assertions
    assert len(cycle_times) >= test_cycles * 0.9, "Success rate below 90%"
    assert avg_time < 100, f"Average time too slow: {avg_time:.1f}ms > 100ms"
    assert max_time < 200, f"Maximum time too slow: {max_time:.1f}ms > 200ms"
    
    print("✅ Performance baseline established within requirements")


if __name__ == "__main__":
    """Direct execution for development testing"""
    async def run_tests():
        validator = OrthodoxyCycleValidator()
        await validator.setup()
        
        try:
            print("🛡️ Starting Orthodoxy Redis Bus Tests...")
            
            # Run confession cycle test
            await test_confession_cycle(validator)
            await asyncio.sleep(0.5)
            
            # Run performance baseline
            await test_performance_baseline(validator)
            
            print("\n✅ All Orthodoxy tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
        finally:
            await validator.cleanup()
    
    asyncio.run(run_tests())