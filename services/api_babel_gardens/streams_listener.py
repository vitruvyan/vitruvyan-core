#!/usr/bin/env python3
"""
🌿 Babel Gardens - Redis Streams Listener (Phase 2 Migration)

ZERO-CODE-CHANGE wrapper for BabelGardensCognitiveBusListener using ListenerAdapter.

Sacred Order: DISCOURSE (Babel Gardens - Linguistic Unification)

Sacred Channels (4 total):
  1. codex.discovery.mapped - Process discovery events
  2. babel.linguistic.synthesis - Synthesize multilingual content
  3. babel.multilingual.bridge - Cross-language bridging
  4. babel.knowledge.cultivation - Knowledge garden cultivation

Purpose:
  Babel Gardens is the linguistic unification layer that processes multilingual content,
  synthesizes knowledge across languages, and cultivates the sacred gardens of understanding.

Migration: Phase 2 (Listener #3 of 7)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready (Feb 7, 2026)
"""

import asyncio
import logging
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_babel_gardens')

from core.synaptic_conclave.listeners.babel_gardens import BabelGardensCognitiveBusListener
from core.synaptic_conclave.consumers import wrap_legacy_listener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("BabelGardensStreamsWrapper")

async def main():
    """🌿 Start Babel Gardens Streams listener with zero-code-change adapter"""
    
    logger.info("🌿 Babel Gardens Listener Sacred Streams Bridge starting...")
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = BabelGardensCognitiveBusListener()
    
    # Step 2: Define sacred channels (must match legacy listener)
    sacred_channels = [
        "codex.discovery.mapped",
        "babel.linguistic.synthesis",
        "babel.multilingual.bridge",
        "babel.knowledge.cultivation"
    ]
    
    logger.info(f"🌿 Babel Gardens subscribed to {len(sacred_channels)} streams")
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="babel_gardens",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"  # Legacy method name
    )
    
    logger.info("🌿 Babel Gardens adapter initialized, starting consumption...")
    
    # Step 4: Start adapter (blocking)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🌿 Babel Gardens Listener stopped by user")
    except Exception as e:
        logger.error(f"🌿 Babel Gardens Listener error: {e}", exc_info=True)
        raise
