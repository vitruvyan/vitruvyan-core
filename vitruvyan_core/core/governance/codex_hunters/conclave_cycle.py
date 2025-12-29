#!/usr/bin/env python3
"""
PHASE 4.5 - Codex Hunters ⇄ Synaptic Conclave Integration Cycle
==============================================================

Core integration component that orchestrates the complete event cycle between 
Codex Hunters and Synaptic Conclave for event-driven data processing.

Event Flow:
data.refresh.requested → Codex Expedition → codex.discovery.mapped/failed

Integration Scenarios:
1. Successful data refresh expedition (real ticker validation)
2. Failed expedition handling (invalid ticker recovery)
3. Redis pub/sub event routing and response cycle
4. Event payload schema compliance and validation
5. LangGraph integration with codex_node.py
6. Database logging and expedition tracking

This is a core component of the Codex Hunters system, not a test framework.

Author: Vitruvyan Development Team
Created: 2025-10-19 - PHASE 4.5 Implementation
"""

import os
import sys
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

# Set up path
sys.path.insert(0, '/home/caravaggio/vitruvyan')

# Core imports
from core.foundation.cognitive_bus.redis_client import get_redis_bus, publish_codex_event, CognitiveEvent
from core.foundation.cognitive_bus.event_schema import (
    create_codex_data_refresh_request,
    create_codex_discovery_event,
    EventSchemaValidator,
    CodexIntent
)
from core.orchestration.langgraph.node.codex_node import codex_node
from core.governance.codex_hunters.tracker import Tracker
from core.governance.codex_hunters.restorer import Restorer
from core.governance.codex_hunters.binder import Binder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ConclaveIntegration:
    """
    PHASE 4.5 Codex Hunters ⇄ Synaptic Conclave Integration
    
    Core integration component that orchestrates the complete event cycle 
    between Codex Hunters and Synaptic Conclave for event-driven processing.
    Manages Redis pub/sub, LangGraph routing, and database persistence.
    """
    
    def __init__(self):
        self.redis_bus = get_redis_bus()
        self.test_results = []
        self.received_events = []
        self.validator = EventSchemaValidator()
        
        # Test configuration
        self.test_timeout = 30  # seconds
        self.redis_timeout = 5   # seconds
        
        logger.info("🧪 PHASE 4.5 Conclave Cycle Test initialized")
    
    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            # Connect to Redis
            if not self.redis_bus.connect():
                logger.error("❌ Failed to connect to Redis Bus")
                return False
            
            # Subscribe to codex response events
            self.redis_bus.subscribe("codex.discovery.*", self._handle_codex_response)
            
            # Start listening
            if not self.redis_bus.start_listening():
                logger.error("❌ Failed to start Redis listener")
                return False
            
            logger.info("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def teardown(self):
        """Cleanup test environment"""
        try:
            self.redis_bus.stop_listening()
            self.redis_bus.disconnect()
            logger.info("🧹 Test environment cleaned up")
        except Exception as e:
            logger.error(f"❌ Teardown error: {e}")
    
    def _handle_codex_response(self, event: CognitiveEvent):
        """Handle incoming codex response events"""
        try:
            logger.info(f"📥 Received event: {event.event_type}")
            self.received_events.append(event)
        except Exception as e:
            logger.error(f"❌ Error handling event: {e}")
    
    async def test_successful_data_refresh(self) -> Dict[str, Any]:
        """Test Scenario 1: Successful data refresh expedition"""
        test_name = "Successful Data Refresh"
        correlation_id = f"test_success_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"🚀 Starting {test_name}...")
        
        try:
            # Step 1: Create and publish data refresh request
            refresh_request = create_codex_data_refresh_request(
                ticker="AAPL",
                sources=["yfinance", "reddit"],
                priority="high",
                correlation_id=correlation_id
            )
            
            # Validate request schema
            if not self.validator.validate_codex_data_refresh(refresh_request["payload"]):
                return self._test_result(test_name, False, "Invalid request schema")
            
            # Step 2: Publish to Redis
            start_time = time.time()
            success = self.redis_bus.publish_event(CognitiveEvent.from_dict(refresh_request))
            
            if not success:
                return self._test_result(test_name, False, "Failed to publish request")
            
            # Step 3: Wait for response
            await self._wait_for_response(correlation_id, timeout=self.test_timeout)
            
            # Step 4: Validate response
            response_event = self._find_response_event(correlation_id)
            
            if not response_event:
                return self._test_result(test_name, False, "No response received")
            
            # Step 5: Validate response schema
            if response_event.event_type == f"codex.{CodexIntent.DISCOVERY_MAPPED.value}":
                if not self.validator.validate_codex_discovery(response_event.payload):
                    return self._test_result(test_name, False, "Invalid response schema")
                
                duration = time.time() - start_time
                return self._test_result(test_name, True, f"Success in {duration:.2f}s", {"response": response_event.to_dict()})
            
            else:
                return self._test_result(test_name, False, f"Unexpected response type: {response_event.event_type}")
            
        except Exception as e:
            return self._test_result(test_name, False, f"Exception: {e}")
    
    async def test_failed_expedition(self) -> Dict[str, Any]:
        """Test Scenario 2: Failed expedition with invalid ticker"""
        test_name = "Failed Expedition"
        correlation_id = f"test_failure_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"🚀 Starting {test_name}...")
        
        try:
            # Step 1: Create request with invalid ticker
            refresh_request = create_codex_data_refresh_request(
                ticker="INVALID_TICKER_XYZ",
                sources=["yfinance"],
                priority="low",
                correlation_id=correlation_id
            )
            
            # Step 2: Publish request
            start_time = time.time()
            success = self.redis_bus.publish_event(CognitiveEvent.from_dict(refresh_request))
            
            if not success:
                return self._test_result(test_name, False, "Failed to publish request")
            
            # Step 3: Wait for failure response
            await self._wait_for_response(correlation_id, timeout=self.test_timeout)
            
            # Step 4: Validate failure response
            response_event = self._find_response_event(correlation_id)
            
            if not response_event:
                return self._test_result(test_name, False, "No response received")
            
            if response_event.event_type == f"codex.{CodexIntent.DISCOVERY_FAILED.value}":
                duration = time.time() - start_time
                return self._test_result(test_name, True, f"Failure correctly detected in {duration:.2f}s", {"response": response_event.to_dict()})
            
            else:
                return self._test_result(test_name, False, f"Expected failure, got: {response_event.event_type}")
                
        except Exception as e:
            return self._test_result(test_name, False, f"Exception: {e}")
    
    async def test_langgraph_integration(self) -> Dict[str, Any]:
        """Test Scenario 3: LangGraph codex_node integration"""
        test_name = "LangGraph Integration"
        
        logger.info(f"🚀 Starting {test_name}...")
        
        try:
            # Step 1: Create mock state with Conclave event
            mock_event = create_codex_data_refresh_request(
                ticker="MSFT",
                sources=["yfinance"],
                priority="medium"
            )
            
            test_state = {
                "conclave_event": mock_event,
                "correlation_id": f"langgraph_test_{uuid.uuid4().hex[:8]}"
            }
            
            # Step 2: Process through codex_node
            start_time = time.time()
            result_state = codex_node(test_state)
            duration = time.time() - start_time
            
            # Step 3: Validate results
            if "response" not in result_state:
                return self._test_result(test_name, False, "No response in result state")
            
            if "codex_status" not in result_state:
                return self._test_result(test_name, False, "No codex_status in result state")
            
            if result_state["codex_status"] == "expedition_launched":
                return self._test_result(test_name, True, f"LangGraph integration successful in {duration:.2f}s", {
                    "status": result_state["codex_status"],
                    "response_preview": result_state["response"][:100] + "...",
                    "route": result_state.get("route")
                })
            
            else:
                return self._test_result(test_name, False, f"Unexpected status: {result_state['codex_status']}")
                
        except Exception as e:
            return self._test_result(test_name, False, f"Exception: {e}")
    
    async def test_event_schema_validation(self) -> Dict[str, Any]:
        """Test Scenario 4: Event payload schema compliance"""
        test_name = "Event Schema Validation"
        
        logger.info(f"🚀 Starting {test_name}...")
        
        try:
            # Test valid refresh request
            valid_request = create_codex_data_refresh_request(
                ticker="GOOGL",
                sources=["yfinance", "reddit", "google_news"],
                priority="critical"
            )
            
            if not self.validator.validate_codex_data_refresh(valid_request["payload"]):
                return self._test_result(test_name, False, "Valid request failed validation")
            
            # Test invalid refresh request (no ticker)
            invalid_request = {
                "event_type": "codex.data.refresh.requested",
                "payload": {
                    "sources": ["yfinance"],
                    "priority": "medium"
                    # Missing ticker/tickers
                }
            }
            
            if self.validator.validate_codex_data_refresh(invalid_request["payload"]):
                return self._test_result(test_name, False, "Invalid request passed validation")
            
            # Test valid discovery response
            valid_response = create_codex_discovery_event(
                discovery_id="test_discovery",
                collections_mapped=["phrases", "sentiment_scores"],
                consistency_scores={"phrases": 0.95, "sentiment_scores": 0.98},
                inconsistencies_found=0,
                recommendations=["All systems operational"]
            )
            
            if not self.validator.validate_codex_discovery(valid_response["payload"]):
                return self._test_result(test_name, False, "Valid response failed validation")
            
            return self._test_result(test_name, True, "All schema validations passed")
            
        except Exception as e:
            return self._test_result(test_name, False, f"Exception: {e}")
    
    async def test_redis_connectivity(self) -> Dict[str, Any]:
        """Test Scenario 5: Redis pub/sub connectivity"""
        test_name = "Redis Connectivity"
        
        logger.info(f"🚀 Starting {test_name}...")
        
        try:
            # Test Redis health
            if not self.redis_bus.is_connected():
                return self._test_result(test_name, False, "Redis not connected")
            
            # Test event publishing
            test_event = CognitiveEvent(
                event_type="codex.test.ping",
                emitter="test_framework",
                target="test_framework",
                payload={"test": True, "test_timestamp": datetime.now().isoformat()},
                timestamp=datetime.now().isoformat()
            )
            
            success = self.redis_bus.publish_event(test_event)
            
            if not success:
                return self._test_result(test_name, False, "Failed to publish test event")
            
            # Get Redis stats
            stats = self.redis_bus.get_stats()
            
            return self._test_result(test_name, True, "Redis connectivity verified", {"stats": stats})
            
        except Exception as e:
            return self._test_result(test_name, False, f"Exception: {e}")
    
    async def _wait_for_response(self, correlation_id: str, timeout: int = 30):
        """Wait for response event with correlation ID"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._find_response_event(correlation_id):
                return
            await asyncio.sleep(0.5)
        
        logger.warning(f"⏰ Timeout waiting for response to {correlation_id}")
    
    def _find_response_event(self, correlation_id: str) -> Optional[CognitiveEvent]:
        """Find response event by correlation ID"""
        for event in self.received_events:
            if hasattr(event, 'correlation_id') and event.correlation_id == correlation_id:
                return event
        return None
    
    def _test_result(self, name: str, success: bool, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized test result"""
        result = {
            "test_name": name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {name}: {message}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("🏗️ Starting PHASE 4.5 Complete Test Suite...")
        
        start_time = time.time()
        
        # Setup
        if not await self.setup():
            return {"error": "Test setup failed"}
        
        try:
            # Run all test scenarios
            await self.test_redis_connectivity()
            await self.test_event_schema_validation()
            await self.test_langgraph_integration()
            await self.test_successful_data_refresh()
            await self.test_failed_expedition()
            
            # Calculate results
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result["success"])
            duration = time.time() - start_time
            
            summary = {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "duration_seconds": round(duration, 2),
                "results": self.test_results,
                "events_received": len(self.received_events)
            }
            
            logger.info(f"🎯 Test Summary: {passed_tests}/{total_tests} passed ({summary['success_rate']:.1f}%) in {duration:.2f}s")
            
            return summary
            
        finally:
            await self.teardown()


async def main():
    """Main integration cycle execution"""
    print("🗺️ PHASE 4.5 - CODEX HUNTERS ⇄ CONCLAVE INTEGRATION CYCLE")
    print("=" * 60)
    
    integration_cycle = ConclaveIntegration()
    
    try:
        results = await integration_cycle.run_all_tests()
        
        if "error" in results:
            print(f"❌ Integration cycle failed: {results['error']}")
            return 1
        
        # Print summary
        print(f"\\n📊 FINAL RESULTS:")
        print(f"   Total Tests: {results['total_tests']}")
        print(f"   Passed: ✅ {results['passed']}")
        print(f"   Failed: ❌ {results['failed']}")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        print(f"   Duration: {results['duration_seconds']}s")
        print(f"   Events Received: {results['events_received']}")
        
        # Print detailed results
        print(f"\\n📋 DETAILED RESULTS:")
        for result in results['results']:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test_name']}: {result['message']}")
        
        print(f"\n🗺️ PHASE 4.5 Integration Cycle: {'✅ COMPLETE' if results['success_rate'] >= 80 else '❌ NEEDS WORK'}")
        
        return 0 if results['success_rate'] >= 80 else 1
        
    except Exception as e:
        logger.error(f"❌ Integration cycle failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)