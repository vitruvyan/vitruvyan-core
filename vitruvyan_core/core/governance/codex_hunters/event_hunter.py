#!/usr/bin/env python3
"""
🗺️ CODEX HUNTERS - EVENT HUNTER
================================
The Synaptic Conclave Bridge

The EventHunter is the official bridge between Synaptic Conclave events and 
Codex Hunter expeditions. It listens for cognitive events and orchestrates
complete Track → Restore → Bind cycles automatically.

"Every signal deserves a hunt" - EventHunter's Creed

Architecture:
- Inherits from BaseHunter (official Codex Hunter status)
- Redis Cognitive Bus integration for real-time events
- Orchestrates full expeditions (Track → Restore → Bind)
- Database logging for expedition tracking
- Event-driven response publishing

Author: Vitruvyan Development Team  
Created: 2025-10-19 - PHASE 4.5 Integration
"""

import os
import sys
import asyncio
import logging
import json
import signal
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import time

# Core imports
from .base_hunter import BaseHunter
from .tracker import Tracker
from .restorer import Restorer
from .binder import Binder
from .inspector import Inspector
from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent
from core.foundation.cognitive_bus.event_schema import (
    create_codex_discovery_event, 
    CodexIntent, 
    EventSchemaValidator
)

logger = logging.getLogger(__name__)


class EventHunter(BaseHunter):
    """
    PHASE 4.5 EventHunter - Synaptic Conclave Bridge
    
    The official Codex Hunter responsible for listening to cognitive events
    and orchestrating automatic expeditions. Acts as the bridge between
    Synaptic Conclave and the Codex Hunter ecosystem.
    
    Capabilities:
    - Real-time Redis event listening
    - Full expedition orchestration (Track → Restore → Bind)
    - Event-driven response publishing
    - Database expedition logging
    - Background service operation
    """
    
    def __init__(self):
        super().__init__(agent_name="EventHunter")
        
        # Event processing
        self.validator = EventSchemaValidator()
        self.running = False
        self.expedition_count = 0
        
        # Hunter team initialization
        self.tracker = None
        self.restorer = None
        self.binder = None
        self.inspector = None
        
        logger.info("🎧 EventHunter initialized - Bridge to Synaptic Conclave active")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method (required by BaseHunter).
        
        For EventHunter, this starts the background listening service.
        
        Kwargs:
            service_mode: bool - Run as background service (default: True)
            duration: int - Service duration in seconds (default: continuous)
        """
        service_mode = kwargs.get("service_mode", True)
        duration = kwargs.get("duration", None)
        
        if service_mode:
            return self._run_as_service(duration)
        else:
            return self._run_single_cycle()
    
    def start_listening(self) -> bool:
        """Start the event listening service"""
        try:
            logger.info("🚀 Starting EventHunter - Synaptic Conclave Bridge...")
            
            # Connect to Redis Cognitive Bus
            if not self.redis_bus.connect():
                logger.error("❌ Failed to connect to Redis Cognitive Bus")
                return False
            
            # Initialize Hunter team
            self._initialize_hunter_team()
            
            # Subscribe to Conclave events
            self.redis_bus.subscribe("codex.data.refresh.requested", self._handle_data_refresh_event)
            self.redis_bus.subscribe("codex.data.discovery.requested", self._handle_discovery_event)
            
            # Start listening for events
            if not self.redis_bus.start_listening():
                logger.error("❌ Failed to start Redis event listener")
                return False
            
            self.running = True
            logger.info("✅ EventHunter active - Listening for Synaptic Conclave events")
            
            # Setup graceful shutdown (only if in main thread)
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
                logger.info("📡 Signal handlers registered for graceful shutdown")
            except ValueError as e:
                logger.info("📡 Signal handlers not available (not in main thread) - manual shutdown required")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ EventHunter startup failed: {e}")
            return False
    
    def stop_listening(self):
        """Stop the event listening service"""
        try:
            logger.info("🛑 Stopping EventHunter service...")
            
            self.running = False
            if self.redis_bus:
                self.redis_bus.stop_listening()
                self.redis_bus.disconnect()
            
            # Cleanup hunter team
            self._cleanup_hunter_team()
            
            logger.info("✅ EventHunter service stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping EventHunter: {e}")
    
    def _initialize_hunter_team(self):
        """Initialize the Hunter expedition team"""
        try:
            logger.info("⚙️ Assembling Hunter expedition team...")
            
            self.tracker = Tracker()
            self.restorer = Restorer()
            self.binder = Binder()
            self.inspector = Inspector()
            
            logger.info("✅ Hunter expedition team assembled and ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to assemble Hunter team: {e}")
            raise
    
    def _cleanup_hunter_team(self):
        """Cleanup hunter team resources"""
        hunters = [self.tracker, self.restorer, self.binder, self.inspector]
        for hunter in hunters:
            if hunter:
                try:
                    hunter.__exit__(None, None, None)
                except:
                    pass
    
    def _handle_data_refresh_event(self, event: CognitiveEvent):
        """Handle data refresh requests - orchestrate full expedition"""
        try:
            logger.info(f"🗺️ [EventHunter] Processing data refresh: {event.correlation_id}")
            
            # Validate event payload
            if not self.validator.validate_codex_data_refresh(event.payload):
                logger.error(f"❌ [EventHunter] Invalid refresh request payload")
                self._publish_failure_response(event, "Invalid request payload")
                return
            
            # Extract expedition parameters
            entity_id = event.payload.get("entity_id")
            entity_ids = event.payload.get("entity_ids", [])
            sources = event.payload.get("sources", ["yfinance", "reddit"])
            priority = event.payload.get("priority", "medium")
            
            target_entities = [entity_id] if entity_id else entity_ids
            if not target_entities:
                self._publish_failure_response(event, "No entity_ids specified for expedition")
                return
            
            logger.info(f"📋 [EventHunter] Expedition: {len(target_entities)} entity_ids, {len(sources)} sources")
            
            # Execute complete expedition cycle
            expedition_result = self._orchestrate_expedition(target_entities, sources, event.correlation_id)
            
            # Publish expedition response
            if expedition_result["success"]:
                self._publish_success_response(event, expedition_result)
                logger.info(f"✅ [EventHunter] Expedition successful: {expedition_result.get('total_records', 0)} records")
            else:
                self._publish_failure_response(event, expedition_result["error"])
                logger.error(f"❌ [EventHunter] Expedition failed: {expedition_result['error']}")
            
            self.expedition_count += 1
            
        except Exception as e:
            logger.error(f"❌ [EventHunter] Error handling data refresh: {e}")
            self._publish_failure_response(event, f"Processing error: {str(e)}")
    
    def _handle_discovery_event(self, event: CognitiveEvent):
        """Handle discovery requests - Inspector analysis"""
        try:
            logger.info(f"🔍 [EventHunter] Processing discovery request: {event.correlation_id}")
            
            # Use Inspector for discovery analysis
            inspection_result = self.inspector.execute(scope="all", healing=False, detailed=True)
            
            # Create response based on inspection results
            if inspection_result["overall_health"] > 0.9:
                self._publish_success_response(event, {
                    "sources_found": [f"inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"],
                    "collections_analyzed": list(inspection_result["collection_results"].keys()),
                    "total_records": sum(r.get("postgres_count", 0) for r in inspection_result["collection_results"].values()),
                    "consistency_score": inspection_result["overall_health"]
                })
            else:
                self._publish_failure_response(event, f"System health below threshold: {inspection_result['overall_health']:.2f}")
            
        except Exception as e:
            logger.error(f"❌ [EventHunter] Error handling discovery: {e}")
            self._publish_failure_response(event, f"Discovery error: {str(e)}")
    
    def _orchestrate_expedition(self, entity_ids: List[str], sources: List[str], correlation_id: str) -> Dict[str, Any]:
        """Orchestrate complete Codex Hunter expedition: Track → Restore → Bind"""
        try:
            logger.info(f"🚀 [EXPEDITION] Starting full cycle for {len(entity_ids)} entity_ids")
            
            # Step 1: Track (data gathering)
            track_result = self.tracker.execute(
                entity_ids=entity_ids,
                sources=sources,
                batch_size=10
            )
            
            if track_result["status"] != "completed" or track_result["total_records"] == 0:
                return {"success": False, "error": "No data retrieved during tracking phase"}
            
            logger.info(f"✅ [EXPEDITION] Tracking complete: {track_result['total_records']} records")
            
            # Step 2: Restore (data normalization)
            raw_data = []
            entity_results = track_result["entity_results"]
            
            # DEBUG: Log the actual structure to understand the data format
            logger.info(f"🔍 [DEBUG] entity_results type: {type(entity_results)}")
            logger.info(f"🔍 [DEBUG] entity_results length: {len(entity_results) if hasattr(entity_results, '__len__') else 'no length'}")
            if entity_results and len(entity_results) > 0:
                logger.info(f"🔍 [DEBUG] first element type: {type(entity_results[0])}")
                logger.info(f"🔍 [DEBUG] first element: {entity_results[0]}")
            
            # entity_results is expected to be a list of dicts, each dict has source keys
            if isinstance(entity_results, list):
                for i, entity_data in enumerate(entity_results):
                    logger.info(f"🔍 [DEBUG] Processing item {i}: type={type(entity_data)}")
                    if isinstance(entity_data, dict):
                        logger.info(f"🔍 [DEBUG] Dict keys: {list(entity_data.keys())}")
                        for source, source_data in entity_data.items():
                            logger.info(f"🔍 [DEBUG] Source '{source}': type={type(source_data)}, data={bool(source_data)}")
                            if source_data:
                                if isinstance(source_data, list):
                                    raw_data.extend(source_data)
                                    logger.info(f"✅ [DEBUG] Extended {len(source_data)} items from {source}")
                                elif isinstance(source_data, dict):
                                    raw_data.append(source_data)
                                    logger.info(f"✅ [DEBUG] Appended dict from {source}")
                                else:
                                    raw_data.append(source_data)
                                    logger.info(f"✅ [DEBUG] Appended {type(source_data)} from {source}")
                    else:
                        logger.error(f"❌ [DEBUG] Item {i} is not a dict: {type(entity_data)}")
            else:
                logger.error(f"❌ [EXPEDITION] entity_results is not a list: {type(entity_results)}")
                return {"success": False, "error": f"Unexpected entity_results type: {type(entity_results)}"}
            
            if not raw_data:
                return {"success": False, "error": "No raw data available for restoration"}
            
            restore_result = self.restorer.execute(raw_data=raw_data)
            
            if restore_result["status"] != "completed":
                return {"success": False, "error": "Data restoration phase failed"}
            
            logger.info(f"✅ [EXPEDITION] Restoration complete: {len(restore_result['normalized_results'])} normalized")
            
            # Step 3: Bind (data persistence)  
            bind_result = self.binder.execute(normalized_data=restore_result["normalized_results"])
            
            if bind_result["status"] != "completed":
                return {"success": False, "error": "Data binding phase failed"}
            
            logger.info(f"✅ [EXPEDITION] Binding complete: PostgreSQL + Qdrant updated")
            
            # Log complete expedition
            self._log_expedition(correlation_id, {
                "track_result": track_result,
                "restore_result": restore_result, 
                "bind_result": bind_result
            })
            
            return {
                "success": True,
                "sources_found": [f"{source}_{entity_id}" for entity_id in entity_ids for source in sources],
                "collections_updated": ["phrases", "sentiment_scores"],
                "total_records": track_result["total_records"],
                "normalized_records": len(restore_result["normalized_results"]),
                "bind_stats": bind_result.get("write_stats", {}),
                "expedition_summary": "Full Track→Restore→Bind cycle completed successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ [EXPEDITION] Full expedition failed: {e}")
            return {"success": False, "error": f"Expedition failed: {str(e)}"}
    
    def _publish_success_response(self, request_event: CognitiveEvent, expedition_result: Dict[str, Any]):
        """Publish successful expedition response"""
        try:
            response = create_codex_discovery_event(
                discovery_id=f"eventhunter_{request_event.correlation_id}",
                collections_mapped=expedition_result.get("collections_updated", ["phrases"]),
                consistency_scores={"expedition": 1.0},
                inconsistencies_found=0,
                recommendations=[f"Expedition successful: {expedition_result.get('total_records', 0)} records processed"],
                intent=CodexIntent.DISCOVERY_MAPPED,
                emitter="event_hunter",
                target="langgraph",
                sources_found=expedition_result.get("sources_found", []),
                expedition_type="automated_expedition",
                correlation_id=request_event.correlation_id
            )
            
            success = self.redis_bus.publish_event(CognitiveEvent.from_dict(response))
            
            if success:
                logger.info(f"📤 [EventHunter] Published success response: {len(expedition_result.get('sources_found', []))} sources")
            else:
                logger.error(f"❌ [EventHunter] Failed to publish success response")
                
        except Exception as e:
            logger.error(f"❌ [EventHunter] Error publishing success: {e}")
    
    def _publish_failure_response(self, request_event: CognitiveEvent, error_message: str):
        """Publish failed expedition response"""
        try:
            response = create_codex_discovery_event(
                discovery_id=f"eventhunter_failed_{request_event.correlation_id}",
                collections_mapped=[],
                consistency_scores={},
                inconsistencies_found=1,
                recommendations=[f"Expedition failed: {error_message}"],
                intent=CodexIntent.DISCOVERY_FAILED,
                emitter="event_hunter",
                target="langgraph",
                expedition_type="failed_expedition",
                correlation_id=request_event.correlation_id
            )
            
            success = self.redis_bus.publish_event(CognitiveEvent.from_dict(response))
            
            if success:
                logger.info(f"📤 [EventHunter] Published failure response: {error_message}")
            else:
                logger.error(f"❌ [EventHunter] Failed to publish failure response")
                
        except Exception as e:
            logger.error(f"❌ [EventHunter] Error publishing failure: {e}")
    
    def _log_expedition(self, correlation_id: str, expedition_data: Dict[str, Any]):
        """Log expedition to PostgreSQL for tracking and debugging"""
        try:
            if not self.tracker or not self.tracker.postgres_agent:
                return
            
            with self.tracker.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS expedition_log (
                        id SERIAL PRIMARY KEY,
                        service_name TEXT,
                        correlation_id TEXT,
                        expedition_data TEXT,
                        total_records INTEGER,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute("""
                    INSERT INTO expedition_log (service_name, correlation_id, expedition_data, total_records, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    "event_hunter",
                    correlation_id,
                    json.dumps(expedition_data, default=str),
                    expedition_data.get("track_result", {}).get("total_records", 0),
                    "completed"
                ))
            
            self.tracker.postgres_agent.connection.commit()
            logger.info(f"📝 [EventHunter] Expedition logged: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ [EventHunter] Failed to log expedition: {e}")
    
    def _run_as_service(self, duration: Optional[int] = None) -> Dict[str, Any]:
        """Run EventHunter as background service"""
        if not self.start_listening():
            return {"status": "failed", "error": "Failed to start listening service"}
        
        try:
            start_time = time.time()
            logger.info("🎯 EventHunter service running... Press Ctrl+C to stop")
            
            while self.running:
                time.sleep(1)
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    logger.info(f"⏰ Service duration reached: {duration}s")
                    break
                
                # Log stats periodically
                if self.expedition_count > 0 and self.expedition_count % 10 == 0:
                    logger.info(f"📊 EventHunter stats: {self.expedition_count} expeditions completed")
        
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        
        finally:
            self.stop_listening()
        
        return {
            "status": "completed",
            "expeditions_completed": self.expedition_count,
            "duration": time.time() - start_time if 'start_time' in locals() else 0
        }
    
    def _run_single_cycle(self) -> Dict[str, Any]:
        """Run a single test cycle (for testing/debugging)"""
        # This could be used for testing single expedition cycles
        return {"status": "completed", "message": "Single cycle mode - implement as needed"}
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 EventHunter received signal {signum}, shutting down gracefully...")
        self.running = False


# CLI Entry Point
def main():
    """Main EventHunter service entry point"""
    print("🗺️ CODEX HUNTERS - EVENT HUNTER")
    print("=" * 40)
    print("Synaptic Conclave Bridge Active")
    
    hunter = EventHunter()
    
    try:
        result = hunter.execute(service_mode=True)
        return 0 if result["status"] == "completed" else 1
        
    except Exception as e:
        logger.error(f"❌ EventHunter service failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)