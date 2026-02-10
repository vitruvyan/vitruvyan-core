#!/usr/bin/env python3
"""
🗝️ Codex Hunters - Sacred Cognitive Bus Listener
Divine event subscription for data collection expeditions
Listens to discovery events in the sacred cognitive realm

⚠️ DOMAIN MIGRATION NOTICE:
This module contains FINANCE-SPECIFIC logic (ticker data collection, fundamentals)
and should be migrated to: vitruvyan_core/domains/finance/listeners/codex_hunters.py

Core infrastructure (StreamBus, TransportEvent) remains in core/.
Only domain-specific listeners should move to domains/<vertical>/.

See: docs/TECH_DEBT_DOMAIN_MIGRATION.md

ARCHITETTURA:
USA AGENTI INTELLIGENTI, NON SCRIPT.
EventHunter orchestra Tracker→Restorer→Binder→Scribe per raccolta dati.
"""

import asyncio
import json
import logging
from typing import Dict, Any
import redis.asyncio as redis
from datetime import datetime
import os
import sys

# Aggiungere core/codex_hunters al path per importare agenti
sys.path.insert(0, '/app/core')

# Import AGENTI INTELLIGENTI from core (refactored Feb 5, 2026)
from core.codex_hunters.event_hunter import EventHunter
from core.codex_hunters.tracker import Tracker
from core.codex_hunters.restorer import Restorer
from core.codex_hunters.binder import Binder
from core.leo.postgres_agent import PostgresAgent
from core.leo.qdrant_agent import QdrantAgent

logger = logging.getLogger("CodexHuntersListener")

class CodexHuntersCognitiveBusListener:
    """🗝️ Sacred listener for expedition events in Codex Hunters"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://vitruvyan_redis:6379')
        self.redis_client = None
        self.pubsub = None
        self.running = False
        
        # Sacred codex channels - Divine expedition subscriptions
        self.sacred_channels = [
            "codex.data.refresh.requested",      # Data refresh expeditions
            "codex.technical.momentum.requested", # Momentum backfill
            "codex.technical.trend.requested",    # Trend backfill
            "codex.technical.volatility.requested", # Volatility backfill
            "codex.schema.validation.requested",  # Schema validation
            "codex.fundamentals.refresh.requested", # Fundamentals extraction
            "codex.risk.refresh.requested"       # VARE risk analysis (Sacred Order #7 - Dec 2025)
        ]
        
        # ✨ Inizializza AGENTI INTELLIGENTI (non HTTP endpoints)
        logger.info("🗝️ Initializing Codex Hunters agents...")
        try:
            self.postgres_agent = PostgresAgent()
            self.qdrant_agent = QdrantAgent()
            
            # EventHunter orchestra tutti gli agenti (No parameters, inherits from BaseHunter)
            self.event_hunter = EventHunter()
            
            # CRITICAL: Inizializza hunter team (Tracker, Restorer, Binder, Inspector)
            self.event_hunter._initialize_hunter_team()
            
            # Riferimenti per compatibility
            self.tracker = self.event_hunter.tracker
            self.restorer = self.event_hunter.restorer
            self.binder = self.event_hunter.binder
            
            logger.info("✅ Codex Hunters agents initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}", exc_info=True)
            raise
        
    async def initialize_sacred_connection(self):
        """🗝️ Initialize divine Redis connection to sacred cognitive realm"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to all sacred channels
            for channel in self.sacred_channels:
                await self.pubsub.subscribe(channel)
                logger.info(f"🗝️ Subscribed to sacred channel: {channel}")
            
            logger.info("🗝️ Codex Hunters connected to divine cognitive bus")
            return True
            
        except Exception as e:
            logger.error(f"🗝️ Sacred connection failed: {e}")
            return False
    
    async def begin_sacred_listening(self):
        """🗝️ Begin sacred listening for divine expedition events"""
        if not await self.initialize_sacred_connection():
            return
            
        self.running = True
        logger.info("🗝️ Codex Hunters listener activated - Embarking on sacred expeditions...")
        
        # Heartbeat task for health monitoring
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self.handle_sacred_message(message)
        except Exception as e:
            logger.error(f"🗝️ Sacred listener error: {e}")
        finally:
            heartbeat_task.cancel()
            await self.sacred_cleanup()
    
    async def _heartbeat_loop(self):
        """💓 Heartbeat logger - confirms listener is alive every 60s"""
        while self.running:
            try:
                await asyncio.sleep(60)
                logger.info("💓 Codex Hunters listener heartbeat - Redis connection active, listening on channels: " + 
                           ", ".join(self.sacred_channels))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💓 Heartbeat error: {e}")
    
    async def handle_sacred_message(self, message):
        """🗝️ Handle sacred messages from divine cognitive channels"""
        channel = message['channel'].decode('utf-8')
        
        if channel == "codex.data.refresh.requested":
            await self.handle_data_refresh(message['data'])
        elif channel == "codex.technical.momentum.requested":
            await self.handle_momentum_backfill(message['data'])
        elif channel == "codex.technical.trend.requested":
            await self.handle_trend_backfill(message['data'])
        elif channel == "codex.technical.volatility.requested":
            await self.handle_volatility_backfill(message['data'])
        elif channel == "codex.schema.validation.requested":
            await self.handle_schema_validation(message['data'])
        elif channel == "codex.fundamentals.refresh.requested":
            await self.handle_fundamentals_extraction(message['data'])
        elif channel == "codex.risk.refresh.requested":
            await self.handle_vare_risk_analysis(message['data'])
        else:
            logger.warning(f"🗝️ Unknown sacred channel: {channel}")
    
    async def handle_data_refresh(self, data: bytes):
        """🗝️ Handle full data refresh expedition using INTELLIGENT AGENTS"""
        try:
            payload = json.loads(data.decode('utf-8'))
            tickers = payload.get('tickers', [])
            sources = payload.get('sources', ['yfinance'])
            
            logger.info(f"🗝️ Data refresh expedition started: {len(tickers)} tickers")
            
            # ✨ USA AGENTI INTELLIGENTI: Tracker → Restorer → Binder
            # EventHunter orchestra l'intera expedition
            correlation_id = f"expedition_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Orchestrazione intelligente via EventHunter (metodo diretto, no CognitiveEvent)
            result = self.event_hunter._orchestrate_expedition(
                tickers=tickers,
                sources=sources,
                correlation_id=correlation_id
            )
            
            if result.get("success"):
                logger.info(f"✅ Expedition completed: {result.get('total_records', 0)} records processed")
                await self.publish_expedition_completed(payload, result)
            else:
                logger.error(f"❌ Expedition failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Data refresh error: {e}", exc_info=True)
    
    async def handle_momentum_backfill(self, data: bytes):
        """🗝️ Handle momentum indicator backfill"""
        try:
            payload = json.loads(data.decode('utf-8'))
            tickers = payload.get('tickers', [])
            logger.info(f"🗝️ Momentum backfill started: {len(tickers)} tickers")
            # Call appropriate backfill endpoint
        except Exception as e:
            logger.error(f"🗝️ Momentum backfill error: {e}")
    
    async def handle_trend_backfill(self, data: bytes):
        """🗝️ Handle trend indicator backfill"""
        try:
            payload = json.loads(data.decode('utf-8'))
            tickers = payload.get('tickers', [])
            logger.info(f"🗝️ Trend backfill started: {len(tickers)} tickers")
            # Call appropriate backfill endpoint
        except Exception as e:
            logger.error(f"🗝️ Trend backfill error: {e}")
    
    async def handle_volatility_backfill(self, data: bytes):
        """🗝️ Handle volatility indicator backfill"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🗝️ Volatility backfill started")
            # Call appropriate backfill endpoint
        except Exception as e:
            logger.error(f"🗝️ Volatility backfill error: {e}")
    
    async def handle_schema_validation(self, data: bytes):
        """🗝️ Handle database schema validation"""
        try:
            payload = json.loads(data.decode('utf-8'))
            tables = payload.get('tables', [])
            logger.info(f"🗝️ Schema validation started: {tables}")
            # Call schema validation endpoint
        except Exception as e:
            logger.error(f"🗝️ Schema validation error: {e}")
    
    async def handle_fundamentals_extraction(self, data: bytes):
        """🗝️ Handle fundamentals data extraction"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🗝️ Fundamentals extraction started")
            # Call fundamentals backfill
        except Exception as e:
            logger.error(f"🗝️ Fundamentals extraction error: {e}")
    
    async def handle_vare_risk_analysis(self, data: bytes):
        """🗝️ Handle VARE risk analysis (Sacred Order #7 - Cassandra - Dec 2025)"""
        try:
            payload = json.loads(data.decode('utf-8'))
            tickers = payload.get('tickers', [])
            
            logger.info(f"🛡️ Cassandra awakens... prophecy for {len(tickers)} tickers requested")
            
            # Import and execute Cassandra (The Risk Prophet)
            from core.codex_hunters.cassandra import Cassandra
            
            cassandra = Cassandra()
            result = cassandra.execute(tickers=tickers)
            
            logger.info(f"🛡️ Cassandra's prophecy delivered: {result.get('status')}")
            
            # Publish completion event
            await self.publish_vare_completed(result)
            
        except Exception as e:
            logger.error(f"🛡️ VARE risk analysis error: {e}")
    
    async def publish_vare_completed(self, result: Dict):
        """🗝️ Publish VARE risk analysis completion event"""
        try:
            event = {
                "event_type": "codex.risk.completed",
                "tickers_analyzed": result.get('tickers_analyzed', 0),
                "tickers_persisted": result.get('tickers_persisted', 0),
                "statistics": result.get('statistics', {}),
                "status": result.get('status', 'unknown'),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(
                "codex.risk.completed",
                json.dumps(event)
            )
            
            logger.info(f"🛡️ Published codex.risk.completed")
            
        except Exception as e:
            logger.error(f"🛡️ Event publishing error: {e}")
    
    async def publish_expedition_completed(self, request: Dict, result: Dict):
        """🗝️ Publish expedition completion event"""
        try:
            event = {
                "event_type": "codex.expedition.completed",
                "tickers_processed": result.get('processed'),
                "sources": request.get('sources'),
                "status": result.get('status'),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(
                "codex.expedition.completed",
                json.dumps(event)
            )
            
            logger.info(f"🗝️ Published codex.expedition.completed")
            
        except Exception as e:
            logger.error(f"🗝️ Event publishing error: {e}")
    
    async def sacred_cleanup(self):
        """🗝️ Sacred cleanup of divine Redis connections"""
        try:
            if self.pubsub:
                for channel in self.sacred_channels:
                    await self.pubsub.unsubscribe(channel)
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("🗝️ Sacred connections to divine realm cleaned up")
        except Exception as e:
            logger.error(f"🗝️ Sacred cleanup error: {e}")


def main():
    """Start Codex Hunters listener"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    listener = CodexHuntersCognitiveBusListener()
    
    try:
        asyncio.run(listener.begin_sacred_listening())
    except KeyboardInterrupt:
        logger.info("🗝️ Codex Hunters listener stopped by user")


if __name__ == "__main__":
    main()
