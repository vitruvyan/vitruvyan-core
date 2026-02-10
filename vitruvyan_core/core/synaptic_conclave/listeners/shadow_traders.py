#!/usr/bin/env python3
"""
🎯 Shadow Traders - Synaptic Conclave Bus Listener
===================================================

⚠️ DOMAIN MIGRATION NOTICE:
This module contains FINANCE-SPECIFIC logic (trading events, portfolio updates)
and should be migrated to: vitruvyan_core/domains/finance/listeners/shadow_traders.py

Core infrastructure (StreamBus, TransportEvent) remains in core/.
Only domain-specific listeners should move to domains/<vertical>/.

See: docs/TECH_DEBT_DOMAIN_MIGRATION.md

Sacred Order: Reason + Perception

Listens to trading events on the Cognitive Bus and publishes
Shadow Traders insights to the Synaptic Conclave.

Channels:
- shadow_traders.order.executed (publish)
- shadow_traders.portfolio.updated (publish)
- shadow_traders.risk.alert (publish)
- codex.discovery.mapped (subscribe - react to new ticker data)
- neural_engine.screen.completed (subscribe - trading opportunities)

Author: Vitruvyan Sacred Orders
Date: January 3, 2026
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import redis.asyncio as redis

from core.leo.postgres_agent import PostgresAgent
from core.leo.qdrant_agent import QdrantAgent

logger = logging.getLogger("ShadowTradersListener")


class ShadowTradersCognitiveBusListener:
    """🎯 Sacred listener for shadow trading events"""
    
    def __init__(self, redis_url: str = None):
        # Use env var first, then parameter, then default to Docker network
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://vitruvyan_redis:6379')
        self.redis_client = None
        self.pubsub = None
        
        # WebSocket callback handlers (Task 26.1.3 - Jan 26, 2026)
        self.websocket_callbacks = {
            "guardian.insight.created": None,
            "autopilot.action.proposed": None,
            "portfolio.value.updated": None
        }
        
        # Sacred Test Mode Protection
        self.test_mode = os.getenv('VITRUVYAN_TEST_MODE', 'false').lower() == 'true'
        
        if self.test_mode:
            logger.info("🛡️ Sacred Test Mode: Bypassing PostgreSQL/Qdrant initialization")
            self.pg = None
            self.qdrant = None
        else:
            self.pg = PostgresAgent()
            self.qdrant = QdrantAgent()
            
        self.running = False
        
        # Sacred channels - Subscribe to relevant trading events
        self.subscribe_channels = [
            "codex.discovery.mapped",           # React to new ticker discoveries
            "neural_engine.screen.completed",   # Trading opportunities from Neural Engine
            "synaptic.conclave.broadcast",      # Global epistemic events
            "guardian.insight.created",         # Guardian Portfolio insights (Task 26.1.3)
            "autopilot.action.proposed",        # Autopilot proposed actions (Task 26.1.3)
            "portfolio.value.updated",          # Portfolio value changes (Task 26.1.3)
        ]
        
        # Publish channels
        self.publish_channels = {
            "order_executed": "shadow_traders.order.executed",
            "portfolio_updated": "shadow_traders.portfolio.updated",
            "risk_alert": "shadow_traders.risk.alert",
            "trade_suggestion": "shadow_traders.suggestion.generated"
        }
        
    async def initialize_sacred_connection(self):
        """🎯 Initialize divine Redis connection to Synaptic Conclave"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to all sacred channels
            for channel in self.subscribe_channels:
                await self.pubsub.subscribe(channel)
                logger.info(f"🎯 Subscribed to channel: {channel}")
            
            logger.info("🎯 Shadow Traders connected to Synaptic Conclave (Cognitive Bus)")
            return True
            
        except Exception as e:
            logger.error(f"🎯 Sacred connection failed: {e}")
            return False
    
    async def begin_sacred_listening(self):
        """🎯 Begin sacred listening for trading events"""
        if not await self.initialize_sacred_connection():
            logger.error("🎯 Failed to initialize Redis connection, listener not started")
            return
            
        self.running = True
        logger.info("🎯 Shadow Traders listener activated - Monitoring trading signals...")
        
        # Heartbeat task for health monitoring
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self.handle_sacred_message(message)
        except Exception as e:
            logger.error(f"🎯 Sacred listener error: {e}")
        finally:
            heartbeat_task.cancel()
            await self.sacred_cleanup()
    
    async def _heartbeat_loop(self):
        """💓 Heartbeat logger - confirms listener is alive every 60s"""
        while self.running:
            try:
                await asyncio.sleep(60)
                logger.info("💓 Shadow Traders listener heartbeat - Redis connection active, listening on channels: " + 
                           ", ".join(self.subscribe_channels))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💓 Heartbeat error: {e}")
    
    async def handle_sacred_message(self, message):
        """🎯 Handle sacred messages from Synaptic Conclave"""
        try:
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            
            logger.info(f"🎯 Received event on {channel}: {data.get('event_type', 'unknown')}")
            
            if channel == "codex.discovery.mapped":
                await self.handle_codex_discovery(data)
            elif channel == "neural_engine.screen.completed":
                await self.handle_screening_completed(data)
            elif channel == "synaptic.conclave.broadcast":
                await self.handle_conclave_broadcast(data)
            elif channel == "guardian.insight.created":
                await self.handle_guardian_insight(data)
            elif channel == "autopilot.action.proposed":
                await self.handle_autopilot_action(data)
            elif channel == "portfolio.value.updated":
                await self.handle_portfolio_value_update(data)
                
        except Exception as e:
            logger.error(f"🎯 Error handling message: {e}")
    
    async def handle_codex_discovery(self, data: Dict[str, Any]):
        """
        React to new ticker discoveries from Codex Hunters.
        Could trigger portfolio rebalancing suggestions.
        """
        ticker = data.get('ticker')
        logger.info(f"🎯 New ticker discovered: {ticker}")
        
        # Log to PostgreSQL (shadow_traders could track new opportunities)
        if not self.test_mode and self.pg:
            try:
                with self.pg.connection.cursor() as cur:
                    cur.execute("""
                        INSERT INTO shadow_discovery_log (ticker, discovery_data, created_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (ticker) DO NOTHING
                    """, (ticker, json.dumps(data)))
                    self.pg.connection.commit()
            except Exception as e:
                logger.warning(f"Failed to log discovery: {e}")
    
    async def handle_screening_completed(self, data: Dict[str, Any]):
        """
        React to Neural Engine screening results.
        Could trigger automated trade suggestions.
        """
        tickers = data.get('tickers', [])
        profile = data.get('profile', 'unknown')
        
        logger.info(f"🎯 Screening completed: {len(tickers)} tickers, profile: {profile}")
        
        # Could publish trade suggestions based on screening results
        # await self.publish_trade_suggestion({...})
    
    async def handle_conclave_broadcast(self, data: Dict[str, Any]):
        """
        React to global epistemic events from Synaptic Conclave.
        Could trigger risk alerts or portfolio adjustments.
        """
        event_type = data.get('event_type')
        logger.info(f"🎯 Conclave broadcast received: {event_type}")
    
    async def handle_guardian_insight(self, data: Dict[str, Any]):
        """
        Handle Guardian Portfolio insight events (Task 26.1.3).
        Calls registered WebSocket callback to broadcast to user.
        
        Event data: {user_id, insight_id, insight_type, severity, title, ...}
        """
        logger.info(f"🎯 Guardian insight received: {data.get('insight_type')}")
        
        # Call WebSocket callback if registered
        callback = self.websocket_callbacks.get("guardian.insight.created")
        if callback:
            await callback(data)
        else:
            logger.debug("No WebSocket callback registered for guardian.insight.created")
    
    async def handle_autopilot_action(self, data: Dict[str, Any]):
        """
        Handle Autopilot proposed action events (Task 26.1.3).
        Calls registered WebSocket callback to broadcast to user.
        
        Event data: {user_id, action_id, action_type, ticker, quantity, ...}
        """
        logger.info(f"🎯 Autopilot action proposed: {data.get('action_type')}")
        
        # Call WebSocket callback if registered
        callback = self.websocket_callbacks.get("autopilot.action.proposed")
        if callback:
            await callback(data)
        else:
            logger.debug("No WebSocket callback registered for autopilot.action.proposed")
    
    async def handle_portfolio_value_update(self, data: Dict[str, Any]):
        """
        Handle portfolio value update events (Task 26.1.3).
        Calls registered WebSocket callback to broadcast to user.
        
        Event data: {user_id, total_value, change_pct, ...}
        """
        logger.info(f"🎯 Portfolio value updated: {data.get('total_value')}")
        
        # Call WebSocket callback if registered
        callback = self.websocket_callbacks.get("portfolio.value.updated")
        if callback:
            await callback(data)
        else:
            logger.debug("No WebSocket callback registered for portfolio.value.updated")
    
    def register_websocket_callback(self, channel: str, callback):
        """
        Register WebSocket callback for specific channel (Task 26.1.3).
        
        Args:
            channel: One of 'guardian.insight.created', 'autopilot.action.proposed', 'portfolio.value.updated'
            callback: Async function to call when event received
        """
        if channel in self.websocket_callbacks:
            self.websocket_callbacks[channel] = callback
            logger.info(f"🎯 Registered WebSocket callback for {channel}")
        else:
            logger.warning(f"Unknown channel for WebSocket callback: {channel}")
    
    async def publish_order_executed(self, order_data: Dict[str, Any]):
        """Publish order execution event to Synaptic Conclave"""
        if not self.redis_client:
            return
            
        try:
            event = {
                "event_type": "shadow_order_executed",
                "timestamp": datetime.utcnow().isoformat(),
                "data": order_data
            }
            
            channel = self.publish_channels["order_executed"]
            await self.redis_client.publish(channel, json.dumps(event))
            logger.info(f"🎯 Published order execution to {channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish order event: {e}")
    
    async def publish_portfolio_updated(self, portfolio_data: Dict[str, Any]):
        """Publish portfolio update event"""
        if not self.redis_client:
            return
            
        try:
            event = {
                "event_type": "shadow_portfolio_updated",
                "timestamp": datetime.utcnow().isoformat(),
                "data": portfolio_data
            }
            
            channel = self.publish_channels["portfolio_updated"]
            await self.redis_client.publish(channel, json.dumps(event))
            logger.info(f"🎯 Published portfolio update to {channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish portfolio event: {e}")
    
    async def publish_risk_alert(self, risk_data: Dict[str, Any]):
        """Publish risk alert event"""
        if not self.redis_client:
            return
            
        try:
            event = {
                "event_type": "shadow_risk_alert",
                "timestamp": datetime.utcnow().isoformat(),
                "data": risk_data
            }
            
            channel = self.publish_channels["risk_alert"]
            await self.redis_client.publish(channel, json.dumps(event))
            logger.warning(f"🎯 Published risk alert to {channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish risk alert: {e}")
    
    async def sacred_cleanup(self):
        """🎯 Cleanup Redis connections gracefully"""
        self.running = False
        
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(*self.subscribe_channels)
                await self.pubsub.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("🎯 Shadow Traders listener disconnected from Synaptic Conclave")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def stop(self):
        """Stop the listener"""
        self.running = False
        logger.info("🎯 Shadow Traders listener stopping...")


# Global listener instance
shadow_traders_listener = ShadowTradersCognitiveBusListener()


async def start_listener():
    """Start the Redis listener in background"""
    await shadow_traders_listener.begin_sacred_listening()


def run_listener():
    """Run the listener (for standalone execution)"""
    asyncio.run(start_listener())


if __name__ == "__main__":
    run_listener()
