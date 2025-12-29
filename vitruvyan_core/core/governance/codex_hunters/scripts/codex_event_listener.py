#!/usr/bin/env python3
"""
PHASE 4.5 - Codex Hunters Event Listener Service
=================================================

Background service that listens for Redis events and triggers Codex Hunter expeditions.
This service bridges the gap between Synaptic Conclave events and Codex Hunter operations.

Events Handled:
- codex.data.refresh.requested → Tracker expedition
- codex.data.discovery.requested → Inspector + Cartographer analysis

Author: Vitruvyan Development Team
Created: 2025-10-19 - PHASE 4.5 Implementation
"""

import os
import sys
import asyncio
import logging
import json
import signal
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import time

# Set up path
sys.path.insert(0, '/home/caravaggio/vitruvyan')

# Core imports
from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent
from core.foundation.cognitive_bus.event_schema import (
    create_codex_discovery_event, 
    CodexIntent, 
    EventSchemaValidator
)
from core.agents.codex_hunters.tracker import Tracker
from core.agents.codex_hunters.restorer import Restorer
from core.agents.codex_hunters.binder import Binder
from core.agents.codex_hunters.scribe import Scribe  # ✅ NEW: Technical indicators
from core.agents.codex_hunters.inspector import Inspector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class CodexEventListener:
    """
    PHASE 4.5 Event Listener Service
    
    Listens for Synaptic Conclave events and orchestrates Codex Hunter responses.
    Runs as background service to provide real-time event-driven data processing.
    """
    
    def __init__(self):
        self.redis_bus = get_redis_bus()
        self.validator = EventSchemaValidator()
        self.running = False
        self.expedition_count = 0
        
        # Initialize Codex Hunters
        self.tracker = None
        self.restorer = None
        self.binder = None
        self.scribe = None  # ✅ NEW: Technical indicator hunter
        self.inspector = None
        
        logger.info("🎧 Codex Event Listener initialized")
    
    def start(self):
        """Start the event listener service"""
        try:
            logger.info("🚀 Starting PHASE 4.5 Codex Event Listener Service...")
            
            # Connect to Redis
            if not self.redis_bus.connect():
                logger.error("❌ Failed to connect to Redis Bus")
                return False
            
            # Initialize Codex Hunters
            self._initialize_hunters()
            
            # Subscribe to events
            self.redis_bus.subscribe("codex.data.refresh.requested", self._handle_data_refresh_event)
            self.redis_bus.subscribe("codex.data.discovery.requested", self._handle_discovery_event)
            
            # Start listening
            if not self.redis_bus.start_listening():
                logger.error("❌ Failed to start Redis listener")
                return False
            
            self.running = True
            logger.info("✅ Codex Event Listener Service started successfully")
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start event listener: {e}")
            return False
    
    def stop(self):
        """Stop the event listener service"""
        try:
            logger.info("🛑 Stopping Codex Event Listener Service...")
            
            self.running = False
            self.redis_bus.stop_listening()
            self.redis_bus.disconnect()
            
            # Cleanup hunters
            if self.tracker:
                self.tracker.__exit__(None, None, None)
            if self.restorer:
                self.restorer.__exit__(None, None, None)
            if self.binder:
                self.binder.__exit__(None, None, None)
            if self.scribe:  # ✅ NEW
                pass  # Scribe has no __exit__ context manager
            if self.inspector:
                self.inspector.__exit__(None, None, None)
            
            logger.info("✅ Codex Event Listener Service stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping service: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _initialize_hunters(self):
        """Initialize Codex Hunter agents"""
        try:
            logger.info("⚙️ Initializing Codex Hunter agents...")
            
            self.tracker = Tracker()
            self.restorer = Restorer()  
            self.binder = Binder()
            self.scribe = Scribe(user_id="codex_listener")  # ✅ NEW
            self.inspector = Inspector()
            
            logger.info("✅ All Codex Hunter agents initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize hunters: {e}")
            raise
    
    def _handle_data_refresh_event(self, event: CognitiveEvent):
        """Handle data refresh requests - complete Track → Restore → Bind cycle"""
        try:
            logger.info(f"🗺️ [LISTENER] Processing data refresh request: {event.correlation_id}")
            
            # Validate event
            if not self.validator.validate_codex_data_refresh(event.payload):
                logger.error(f"❌ [LISTENER] Invalid refresh request payload")
                self._publish_failure_response(event, "Invalid request payload")
                return
            
            # Extract parameters
            ticker = event.payload.get("ticker")
            tickers = event.payload.get("tickers", [])
            sources = event.payload.get("sources", ["yfinance", "reddit"])
            priority = event.payload.get("priority", "medium")
            
            target_tickers = [ticker] if ticker else tickers
            if not target_tickers:
                self._publish_failure_response(event, "No tickers specified")
                return
            
            logger.info(f"📋 [LISTENER] Expedition: {len(target_tickers)} tickers, {len(sources)} sources")
            
            # Execute complete expedition cycle
            expedition_result = self._execute_full_expedition(target_tickers, sources, event.correlation_id)
            
            # Publish response
            if expedition_result["success"]:
                self._publish_success_response(event, expedition_result)
            else:
                self._publish_failure_response(event, expedition_result["error"])
            
            self.expedition_count += 1
            
        except Exception as e:
            logger.error(f"❌ [LISTENER] Error handling data refresh: {e}")
            self._publish_failure_response(event, f"Processing error: {str(e)}")
    
    def _handle_discovery_event(self, event: CognitiveEvent):
        """Handle discovery requests - Inspector analysis"""
        try:
            logger.info(f"🔍 [LISTENER] Processing discovery request: {event.correlation_id}")
            
            # Use Inspector for discovery analysis
            inspection_result = self.inspector.execute(scope="all", healing=False, detailed=True)
            
            # Create response based on inspection
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
            logger.error(f"❌ [LISTENER] Error handling discovery: {e}")
            self._publish_failure_response(event, f"Discovery error: {str(e)}")
    
    def _execute_full_expedition(self, tickers: list, sources: list, correlation_id: str) -> Dict[str, Any]:
        """
        Execute complete Codex Hunter expedition: Track → Restore → Bind → Scribe
        
        NEW in Scribe integration:
        - After Bind persists raw data, Scribe calculates technical indicators
        - Trend indicators (SMA20, SMA50, SMA200) → trend_logs
        - Momentum indicators (RSI, ROC, MACD) → momentum_logs  
        - Volatility indicators (ATR, StdDev) → volatility_logs
        """
        try:
            logger.info(f"🚀 [EXPEDITION] Starting full cycle for {len(tickers)} tickers")
            
            # Step 1: Track (data gathering)
            track_result = self.tracker.execute(
                tickers=tickers,
                sources=sources,
                batch_size=10
            )
            
            if track_result["status"] != "completed" or track_result["total_records"] == 0:
                return {"success": False, "error": "No data retrieved during tracking"}
            
            logger.info(f"✅ [EXPEDITION] Tracking complete: {track_result['total_records']} records")
            
            # DEBUG: Log the actual structure 
            logger.info(f"🔍 [DEBUG] ticker_results type: {type(track_result['ticker_results'])}")
            logger.info(f"🔍 [DEBUG] ticker_results content: {track_result['ticker_results'][:1] if track_result['ticker_results'] else 'empty'}")
            
            # Step 2: Restore (data normalization)
            raw_data = []
            # ticker_results is expected to be a list of dicts, each dict has source keys
            ticker_results = track_result["ticker_results"]
            
            if isinstance(ticker_results, list):
                for ticker_data in ticker_results:
                    if isinstance(ticker_data, dict):
                        for source, source_data in ticker_data.items():
                            if source_data:
                                if isinstance(source_data, list):
                                    raw_data.extend(source_data)
                                else:
                                    raw_data.append(source_data)
            else:
                logger.error(f"❌ [DEBUG] Unexpected ticker_results type: {type(ticker_results)}")
                return {"success": False, "error": f"Unexpected ticker_results type: {type(ticker_results)}"}
            
            if not raw_data:
                return {"success": False, "error": "No raw data to restore"}
            
            restore_result = self.restorer.execute(raw_data=raw_data)
            
            if restore_result["status"] != "completed":
                return {"success": False, "error": "Data restoration failed"}
            
            logger.info(f"✅ [EXPEDITION] Restoration complete: {len(restore_result['normalized_results'])} normalized")
            
            # Step 3: Bind (data persistence)
            bind_result = self.binder.execute(normalized_data=restore_result["normalized_results"])
            
            if bind_result["status"] != "completed":
                return {"success": False, "error": "Data binding failed"}
            
            logger.info(f"✅ [EXPEDITION] Binding complete: PostgreSQL + Qdrant updated")
            
            # ✅ Step 4: Scribe (technical indicator calculation) - NEW!
            scribe_result = None
            try:
                logger.info(f"🔬 [EXPEDITION] Starting Scribe analysis...")
                scribe_result = self.scribe.execute(
                    normalized_data=restore_result["normalized_results"],
                    batch_size=50
                )
                
                if scribe_result["successful"] > 0:
                    logger.info(
                        f"✅ [EXPEDITION] Scribe complete: {scribe_result['successful']}/{scribe_result['processed']} "
                        f"indicators calculated in {scribe_result['duration_seconds']:.2f}s"
                    )
                else:
                    logger.warning(f"⚠️  [EXPEDITION] Scribe processed 0 tickers successfully")
                    
            except Exception as e:
                logger.error(f"❌ [EXPEDITION] Scribe failed: {e}")
                # Don't fail entire expedition if Scribe fails - continue
                scribe_result = {"successful": 0, "failed": len(restore_result["normalized_results"]), "error": str(e)}
            
            # Log complete expedition
            self._log_expedition(correlation_id, {
                "track_result": track_result,
                "restore_result": restore_result, 
                "bind_result": bind_result,
                "scribe_result": scribe_result  # ✅ NEW
            })
            
            return {
                "success": True,
                "sources_found": [f"{source}_{ticker}" for ticker in tickers for source in sources],
                "collections_updated": ["phrases", "sentiment_scores", "trend_logs", "momentum_logs", "volatility_logs"],  # ✅ Extended
                "total_records": track_result["total_records"],
                "normalized_records": len(restore_result["normalized_results"]),
                "bind_stats": bind_result.get("write_stats", {}),
                "scribe_stats": {  # ✅ NEW
                    "processed": scribe_result.get("processed", 0) if scribe_result else 0,
                    "successful": scribe_result.get("successful", 0) if scribe_result else 0,
                    "failed": scribe_result.get("failed", 0) if scribe_result else 0,
                    "duration": scribe_result.get("duration_seconds", 0) if scribe_result else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ [EXPEDITION] Full expedition failed: {e}")
            return {"success": False, "error": f"Expedition failed: {str(e)}"}
    
    def _publish_success_response(self, request_event: CognitiveEvent, expedition_result: Dict[str, Any]):
        """Publish successful expedition response"""
        try:
            response = create_codex_discovery_event(
                discovery_id=f"listener_{request_event.correlation_id}",
                collections_mapped=expedition_result.get("collections_updated", ["phrases"]),
                consistency_scores={"expedition": 1.0},
                inconsistencies_found=0,
                recommendations=[f"Expedition successful: {expedition_result.get('total_records', 0)} records processed"],
                intent=CodexIntent.DISCOVERY_MAPPED,
                emitter="codex_listener",
                target="langgraph",
                sources_found=expedition_result.get("sources_found", []),
                expedition_type="full_expedition",
                correlation_id=request_event.correlation_id
            )
            
            success = self.redis_bus.publish_event(CognitiveEvent.from_dict(response))
            
            if success:
                logger.info(f"📤 [LISTENER] Published success response: {len(expedition_result.get('sources_found', []))} sources")
            else:
                logger.error(f"❌ [LISTENER] Failed to publish success response")
                
        except Exception as e:
            logger.error(f"❌ [LISTENER] Error publishing success: {e}")
    
    def _publish_failure_response(self, request_event: CognitiveEvent, error_message: str):
        """Publish failed expedition response"""
        try:
            response = create_codex_discovery_event(
                discovery_id=f"listener_failed_{request_event.correlation_id}",
                collections_mapped=[],
                consistency_scores={},
                inconsistencies_found=1,
                recommendations=[f"Expedition failed: {error_message}"],
                intent=CodexIntent.DISCOVERY_FAILED,
                emitter="codex_listener",
                target="langgraph",
                expedition_type="failed_expedition",
                correlation_id=request_event.correlation_id
            )
            
            success = self.redis_bus.publish_event(CognitiveEvent.from_dict(response))
            
            if success:
                logger.info(f"📤 [LISTENER] Published failure response: {error_message}")
            else:
                logger.error(f"❌ [LISTENER] Failed to publish failure response")
                
        except Exception as e:
            logger.error(f"❌ [LISTENER] Error publishing failure: {e}")
    
    def _log_expedition(self, correlation_id: str, expedition_data: Dict[str, Any]):
        """Log expedition to PostgreSQL"""
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
                    "codex_listener",
                    correlation_id,
                    json.dumps(expedition_data, default=str),
                    expedition_data.get("track_result", {}).get("total_records", 0),
                    "completed"
                ))
            
            self.tracker.postgres_agent.connection.commit()
            logger.info(f"📝 [LISTENER] Expedition logged: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ [LISTENER] Failed to log expedition: {e}")
    
    def run_forever(self):
        """Run the service in foreground (blocking)"""
        if not self.start():
            return 1
        
        try:
            logger.info("🎯 Codex Event Listener running... Press Ctrl+C to stop")
            
            while self.running:
                time.sleep(1)
                
                # Log stats every 5 minutes
                if self.expedition_count > 0 and self.expedition_count % 10 == 0:
                    logger.info(f"📊 Service stats: {self.expedition_count} expeditions processed")
        
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        
        finally:
            self.stop()
        
        return 0


def main():
    """Main service entry point"""
    print("🗺️ PHASE 4.5 - CODEX HUNTERS EVENT LISTENER SERVICE")
    print("=" * 60)
    
    service = CodexEventListener()
    
    try:
        exit_code = service.run_forever()
        return exit_code
        
    except Exception as e:
        logger.error(f"❌ Service failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)