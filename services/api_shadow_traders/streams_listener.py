"""
🎯 Shadow Traders - Sacred Trading Streams Listener (Phase 2 Migration)

ZERO-CODE-CHANGE wrapper for ShadowTradersCognitiveBusListener using ListenerAdapter.

Sacred Order: Reason + Perception (#6)

Sacred Channels (3 subscribe total):
  1. codex.discovery.mapped - React to new ticker discoveries
  2. neural_engine.screen.completed - Trading opportunities from Neural Engine  
  3. synaptic.conclave.broadcast - Global epistemic events

Publish Channels (4 total):
  - shadow_traders.order.executed
  - shadow_traders.portfolio.updated
  - shadow_traders.risk.alert
  - shadow_traders.suggestion.generated

Migration: Phase 2 (Listener #6 of 13)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready after 5 successful migrations
"""

import asyncio
import logging

# BUSINESS LOGIC IMPORT (from cognitive_bus/listeners/ - Feb 5, 2026)
from api_shadow_traders.redis_listener import ShadowTradersCognitiveBusListener
from core.synaptic_conclave.consumers.listener_adapter import wrap_legacy_listener
from core.synaptic_conclave.monitoring.metrics_server import start_metrics_server

logger = logging.getLogger("ShadowTradersStreamsWrapper")

async def main():
    """🎯 Start Shadow Traders Streams listener with zero-code-change adapter"""
    
    logger.info("🎯 Shadow Traders Sacred Trading Streams Listener starting...")
    
    # Start Prometheus metrics server (non-blocking)
    start_metrics_server(port=8023)
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = ShadowTradersCognitiveBusListener()
    
    # Step 2: Use subscribe_channels from legacy listener
    sacred_channels = legacy_listener.subscribe_channels
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="shadow_traders",
        sacred_channels=sacred_channels  # 3 channels
    )
    
    # Step 4: Start adapter
    await adapter.start()

if __name__ == "__main__":
    asyncio.run(main())
