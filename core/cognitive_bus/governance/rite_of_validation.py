"""
    Sacred Rite of Validation - Synaptic Conclave Testing
Sacred ceremony to validate the cognitive organism's communication

This module provides comprehensive testing for the Synaptic Conclave
to ensure all Sacred Orders can communicate properly.
"""
    
import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, Any, List
import httpx
import json
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.cognitive_bus import (
    get_heart, get_herald, get_pulse, get_scribe, get_lexicon,
    publish_event, subscribe_to_domain
)


class RiteOfValidation:
    """
    Sacred ceremony to validate Conclave functionality.
    """
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def perform_rite(self) -> bool:
        """
        Perform the complete Rite of Validation.
        """
        print("Sacred Beginning the Rite of Validation...")
        print("=" * 60)
        
        try:
            # Test 1: Heart Awakening
            await self._test_heart_awakening()
            
            # Test 2: Sacred Language Validation
            await self._test_sacred_language()
            
            # Test 3: Event Publication
            await self._test_event_publication()
            
            # Test 4: Event Subscription
            await self._test_event_subscription()
            
            # Test 5: Herald Routing
            await self._test_herald_routing()
            
            # Test 6: Pulse Vitality
            await self._test_pulse_vitality()
            
            # Test 7: Scribe Chronicles
            await self._test_scribe_chronicles()
            
            # Test 8: API Endpoints
            await self._test_api_endpoints()
            
            # Test 9: End-to-End Flow
            await self._test_end_to_end_flow()
            
            # Final Results
            return await self._present_results()
            
        except Exception as e:
            print(f"💔 Rite of Validation failed catastrophically: {e}")
            return False
    
    async def _test_heart_awakening(self):
        """
        Test 1: Validate Heart can awaken and connect to Redis.
        """
        print("\n🧪 Test 1: Heart Awakening")
        print("-" * 30)
        
        try:
            heart = await get_heart()
            
            if heart.is_beating:
                vitals = await heart.get_vital_signs()
                
                if vitals["redis_connected"]:
                    await self._record_success("Heart Awakening", {
                        "redis_connected": True,
                        "active_subscriptions": vitals["active_subscriptions"]
                    })
                    print("✅ Heart is beating and connected to Redis")
                else:
                    await self._record_failure("Heart Awakening", "Redis not connected")
                    print("❌ Heart awakened but Redis not connected")
            else:
                await self._record_failure("Heart Awakening", "Heart not beating")
                print("❌ Heart failed to awaken")
                
        except Exception as e:
            await self._record_failure("Heart Awakening", str(e))
            print(f"❌ Heart awakening failed: {e}")
    
    async def _test_sacred_language(self):
        """
        Test 2: Validate Sacred Language schema.
        """
        print("\n🧪 Test 2: Sacred Language Validation")
        print("-" * 30)
        
        try:
            lexicon = get_lexicon()
            
            # Test domain retrieval
            domains = lexicon.get_all_domains()
            
            if len(domains) >= 6:  # babel, orthodoxy, conclave, codex, vault, crew, system
                print(f"✅ Found {len(domains)} domains: {domains}")
                
                # Test intent validation
                babel_intents = lexicon.get_domain_intents("babel")
                if "fusion.completed" in babel_intents:
                    print("✅ Babel Gardens intents validated")
                    
                    # Test event validation
                    is_valid = lexicon.validate_event("babel", "fusion.completed", {
                        "phrase_id": 12345,
                        "language": "arabic"
                    })
                    
                    if is_valid:
                        await self._record_success("Sacred Language", {
                            "total_domains": len(domains),
                            "babel_intents": len(babel_intents),
                            "validation_working": True
                        })
                        print("✅ Event validation working")
                    else:
                        await self._record_failure("Sacred Language", "Event validation failed")
                        print("❌ Event validation failed")
                else:
                    await self._record_failure("Sacred Language", "Babel intents missing")
                    print("❌ Babel Gardens intents not found")
            else:
                await self._record_failure("Sacred Language", f"Only {len(domains)} domains found")
                print(f"❌ Expected at least 6 domains, found {len(domains)}")
                
        except Exception as e:
            await self._record_failure("Sacred Language", str(e))
            print(f"❌ Sacred Language test failed: {e}")
    
    async def _test_event_publication(self):
        """
        Test 3: Validate event publication.
        """
        print("\n🧪 Test 3: Event Publication")
        print("-" * 30)
        
        try:
            # Test event publication
            test_payload = {
                "phrase_id": 99999,
                "language": "test",
                "processing_time_ms": 1.0,
                "test_timestamp": datetime.utcnow().isoformat()
            }
            
            success = await publish_event("babel", "fusion.completed", test_payload)
            
            if success:
                await self._record_success("Event Publication", {
                    "event_published": True,
                    "domain": "babel",
                    "intent": "fusion.completed"
                })
                print("✅ Event published successfully")
            else:
                await self._record_failure("Event Publication", "Publication returned False")
                print("❌ Event publication failed")
                
        except Exception as e:
            await self._record_failure("Event Publication", str(e))
            print(f"❌ Event publication test failed: {e}")
    
    async def _test_event_subscription(self):
        """
        Test 4: Validate event subscription and reception.
        """
        print("\n🧪 Test 4: Event Subscription")
        print("-" * 30)
        
        try:
            received_events = []
            
            # Define callback
            async def test_callback(event_data):
                received_events.append(event_data)
                print(f"📨 Received test event: {event_data.get('domain')}.{event_data.get('intent')}")
            
            # Subscribe to test events
            success = await subscribe_to_domain("test", test_callback)
            
            if success:
                # Give subscription time to register
                await asyncio.sleep(1)
                
                # Publish test event
                test_payload = {"test_data": "subscription_validation"}
                await publish_event("test", "validation.check", test_payload)
                
                # Wait for event processing
                await asyncio.sleep(2)
                
                if received_events:
                    await self._record_success("Event Subscription", {
                        "subscription_successful": True,
                        "events_received": len(received_events),
                        "last_event": received_events[-1] if received_events else None
                    })
                    print("✅ Event subscription and reception working")
                else:
                    await self._record_failure("Event Subscription", "No events received")
                    print("❌ Subscribed but no events received")
            else:
                await self._record_failure("Event Subscription", "Subscription failed")
                print("❌ Event subscription failed")
                
        except Exception as e:
            await self._record_failure("Event Subscription", str(e))
            print(f"❌ Event subscription test failed: {e}")
    
    async def _test_herald_routing(self):
        """
        Test 5: Validate Herald routing logic.
        """
        print("\n🧪 Test 5: Herald Routing")
        print("-" * 30)
        
        try:
            herald = get_herald()
            
            # Test routing map retrieval
            routing_map = await herald.get_routing_map()
            
            if routing_map["total_rules"] > 0:
                print(f"✅ Found {routing_map['total_rules']} routing rules")
                
                # Test Order health check
                order_health = await herald.check_order_health()
                
                total_orders = len(order_health)
                print(f"📊 Checked {total_orders} Orders")
                
                # Test event routing (dry run)
                routing_result = await herald.route_event("babel", "fusion.completed", {
                    "test": "routing_validation"
                })
                
                if routing_result["routed"]:
                    await self._record_success("Herald Routing", {
                        "routing_rules": routing_map["total_rules"],
                        "total_orders": total_orders,
                        "test_routing_successful": True,
                        "target_orders": routing_result["target_orders"]
                    })
                    print(f"✅ Routing working - targeted {len(routing_result['target_orders'])} Orders")
                else:
                    await self._record_failure("Herald Routing", "Test routing failed")
                    print("❌ Test event routing failed")
            else:
                await self._record_failure("Herald Routing", "No routing rules found")
                print("❌ No routing rules configured")
                
        except Exception as e:
            await self._record_failure("Herald Routing", str(e))
            print(f"❌ Herald routing test failed: {e}")
    
    async def _test_pulse_vitality(self):
        """
        Test 6: Validate Pulse heartbeat system.
        """
        print("\n🧪 Test 6: Pulse Vitality")
        print("-" * 30)
        
        try:
            pulse = await get_pulse()
            
            # Start pulse if not already beating
            if not pulse.is_beating:
                await pulse.start_beating()
                await asyncio.sleep(2)  # Give it time to start
            
            pulse_status = await pulse.get_pulse_status()
            
            if pulse_status["is_beating"]:
                # Force a heartbeat
                heartbeat_success = await pulse.force_heartbeat()
                
                if heartbeat_success:
                    await self._record_success("Pulse Vitality", {
                        "pulse_beating": True,
                        "heartbeat_count": pulse_status["heartbeat_count"],
                        "pulse_interval": pulse_status["pulse_interval"],
                        "forced_heartbeat": True
                    })
                    print("✅ Pulse vitality system operational")
                else:
                    await self._record_failure("Pulse Vitality", "Forced heartbeat failed")
                    print("❌ Pulse beating but forced heartbeat failed")
            else:
                await self._record_failure("Pulse Vitality", "Pulse not beating")
                print("❌ Pulse not beating")
                
        except Exception as e:
            await self._record_failure("Pulse Vitality", str(e))
            print(f"❌ Pulse vitality test failed: {e}")
    
    async def _test_scribe_chronicles(self):
        """
        Test 7: Validate Scribe chronicling system.
        """
        print("\n🧪 Test 7: Scribe Chronicles")
        print("-" * 30)
        
        try:
            scribe = get_scribe()
            
            # Chronicle a test event
            await scribe.chronicle_event(
                domain="test",
                intent="validation.chronicle",
                payload={"test_data": "scribe_validation"},
                timestamp=datetime.utcnow().isoformat(),
                source="rite_of_validation"
            )
            
            # Get recent events
            recent_events = scribe.get_recent_events(limit=10)
            
            # Get statistics
            stats = scribe.get_event_statistics()
            
            # Check health
            health = await scribe.get_chronicle_health()
            
            if health["log_directory_exists"] and len(recent_events) > 0:
                await self._record_success("Scribe Chronicles", {
                    "log_directory_exists": True,
                    "recent_events_count": len(recent_events),
                    "daily_events": stats["daily_events_count"],
                    "total_domains": stats["total_domains"]
                })
                print(f"✅ Scribe chronicling {stats['daily_events_count']} events today")
            else:
                await self._record_failure("Scribe Chronicles", "Chronicle system not working")
                print("❌ Scribe chronicle system not working")
                
        except Exception as e:
            await self._record_failure("Scribe Chronicles", str(e))
            print(f"❌ Scribe chronicles test failed: {e}")
    
    async def _test_api_endpoints(self):
        """
        Test 8: Validate API endpoints.
        """
        print("\n🧪 Test 8: API Endpoints")
        print("-" * 30)
        
        try:
            from config.api_config import get_embedding_url
            base_url = get_embedding_url()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test health endpoint
                try:
                    response = await client.get(f"{base_url}/health/conclave")
                    if response.status_code == 200:
                        health_data = response.json()
                        print(f"✅ Health endpoint: {health_data['status']}")
                        
                        # Test other endpoints
                        endpoints_to_test = [
                            "/events/recent",
                            "/events/statistics", 
                            "/orders/health",
                            "/routing/map",
                            "/lexicon/domains",
                            "/pulse/status"
                        ]
                        
                        successful_endpoints = 0
                        
                        for endpoint in endpoints_to_test:
                            try:
                                resp = await client.get(f"{base_url}{endpoint}")
                                if resp.status_code == 200:
                                    successful_endpoints += 1
                                    print(f"✅ {endpoint}")
                                else:
                                    print(f"❌ {endpoint} - Status: {resp.status_code}")
                            except Exception as e:
                                print(f"❌ {endpoint} - Error: {e}")
                        
                        if successful_endpoints >= len(endpoints_to_test) * 0.8:  # 80% success rate
                            await self._record_success("API Endpoints", {
                                "health_endpoint": True,
                                "successful_endpoints": successful_endpoints,
                                "total_endpoints": len(endpoints_to_test),
                                "success_rate": successful_endpoints / len(endpoints_to_test)
                            })
                            print(f"✅ API endpoints operational ({successful_endpoints}/{len(endpoints_to_test)})")
                        else:
                            await self._record_failure("API Endpoints", f"Only {successful_endpoints}/{len(endpoints_to_test)} endpoints working")
                    else:
                        await self._record_failure("API Endpoints", f"Health endpoint returned {response.status_code}")
                        print(f"❌ Health endpoint returned {response.status_code}")
                        
                except httpx.RequestError as e:
                    await self._record_failure("API Endpoints", f"Cannot connect to API: {e}")
                    print(f"❌ Cannot connect to Conclave API: {e}")
                    
        except Exception as e:
            await self._record_failure("API Endpoints", str(e))
            print(f"❌ API endpoints test failed: {e}")
    
    async def _test_end_to_end_flow(self):
        """
        Test 9: Complete end-to-end communication flow.
        """
        print("\n🧪 Test 9: End-to-End Flow")
        print("-" * 30)
        
        try:
            # This tests the complete flow:
            # Event -> Heart -> Herald -> Routing -> Scribe
            
            start_time = time.time()
            
            # Publish a comprehensive test event
            test_event = {
                "test_id": "end_to_end_validation",
                "timestamp": datetime.utcnow().isoformat(),
                "data": "complete_flow_test"
            }
            
            success = await publish_event("babel", "fusion.completed", test_event)
            
            if success:
                # Wait for processing
                await asyncio.sleep(3)
                
                # Check if event was chronicled
                scribe = get_scribe()
                recent_events = scribe.get_recent_events(limit=50)
                
                # Look for our test event
                test_event_found = any(
                    event.get("payload", {}).get("test_id") == "end_to_end_validation"
                    for event in recent_events
                )
                
                processing_time = (time.time() - start_time) * 1000  # ms
                
                if test_event_found:
                    await self._record_success("End-to-End Flow", {
                        "event_published": True,
                        "event_chronicled": True,
                        "processing_time_ms": processing_time,
                        "complete_flow": True
                    })
                    print(f"✅ End-to-end flow completed in {processing_time:.1f}ms")
                else:
                    await self._record_failure("End-to-End Flow", "Event not found in chronicles")
                    print("❌ Event was published but not found in chronicles")
            else:
                await self._record_failure("End-to-End Flow", "Initial event publication failed")
                print("❌ End-to-end flow failed at publication stage")
                
        except Exception as e:
            await self._record_failure("End-to-End Flow", str(e))
            print(f"❌ End-to-end flow test failed: {e}")
    
    async def _record_success(self, test_name: str, details: Dict[str, Any]):
        """
        Record a successful test.
        """
        self.test_results.append({
            "test": test_name,
            "status": "PASSED",
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        })
        self.passed_tests += 1
    
    async def _record_failure(self, test_name: str, error: str):
        """
        Record a failed test.
        """
        self.test_results.append({
            "test": test_name,
            "status": "FAILED",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        })
        self.failed_tests += 1
    
    async def _present_results(self) -> bool:
        """
        Present final test results.
        """
        print("\n" + "=" * 60)
        print("Sacred RITE OF VALIDATION RESULTS")
        print("=" * 60)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"   • {result['test']}: {result.get('error', 'Unknown error')}")
        
        # Save results to file
        results_file = Path("logs/conclave/validation_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "validation_timestamp": datetime.utcnow().isoformat(),
                "total_tests": total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": success_rate,
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Determine overall success
        is_successful = success_rate >= 80.0  # 80% pass rate required
        
        if is_successful:
            print("\n🎉 RITE OF VALIDATION SUCCESSFUL!")
            print("   The Synaptic Conclave is ready for sacred communion.")
        else:
            print("\n💔 RITE OF VALIDATION FAILED!")
            print("   The Conclave requires healing before achieving full consciousness.")
        
        print("=" * 60)
        
        return is_successful


async def main():
    """
    Execute the Rite of Validation.
    """
    rite = RiteOfValidation()
    success = await rite.perform_rite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())