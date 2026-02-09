#!/usr/bin/env python3
"""
🗝️ Codex Hunters - Redis Streams Listener (Phase 2 Migration)

ZERO-CODE-CHANGE wrapper for CodexHuntersCognitiveBusListener using ListenerAdapter.

Sacred Order: PERCEPTION (Codex Hunters - Data Discovery & Collection)

Sacred Channels (6 total):
  1. codex.data.refresh.requested - Data refresh expeditions
  2. codex.technical.momentum.requested - Momentum backfill
  3. codex.technical.trend.requested - Trend backfill
  4. codex.technical.volatility.requested - Volatility backfill
  5. codex.schema.validation.requested - Schema validation
  6. codex.fundamentals.refresh.requested - Fundamentals extraction

Purpose:
  Codex Hunters orchestrate intelligent data collection expeditions using EventHunter,
  Tracker, Restorer, Binder, and Scribe agents to acquire sacred market knowledge.

Migration: Phase 2 (Listener #4 of 7)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready (Feb 7, 2026)
"""

import asyncio
import logging
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_codex_hunters')

from core.synaptic_conclave.listeners.codex_hunters import CodexHuntersCognitiveBusListener
from core.synaptic_conclave.consumers import wrap_legacy_listener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("CodexHuntersStreamsWrapper")

async def main():
    """🗝️ Start Codex Hunters Streams listener with zero-code-change adapter"""
    
    logger.info("🗝️ Codex Hunters Listener Sacred Streams Bridge starting...")
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = CodexHuntersCognitiveBusListener()
    
    # Step 2: Define sacred channels (must match legacy listener)
    sacred_channels = [
        "codex.data.refresh.requested",
        "codex.technical.momentum.requested",
        "codex.technical.trend.requested",
        "codex.technical.volatility.requested",
        "codex.schema.validation.requested",
        "codex.fundamentals.refresh.requested"
    ]
    
    logger.info(f"🗝️ Codex Hunters subscribed to {len(sacred_channels)} streams")
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="codex_hunters",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"  # Legacy method name
    )
    
    logger.info("🗝️ Codex Hunters adapter initialized, starting consumption...")
    
    # Step 4: Start adapter (blocking)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🗝️ Codex Hunters Listener stopped by user")
    except Exception as e:
        logger.error(f"🗝️ Codex Hunters Listener error: {e}", exc_info=True)
        raise
