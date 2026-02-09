#!/usr/bin/env python3
"""
⚖️ Orthodoxy Wardens - Redis Streams Listener (Phase 2 Migration)

ZERO-CODE-CHANGE wrapper for OrthodoxyWardensCognitiveBusListener using ListenerAdapter.

Sacred Order: TRUTH (Orthodoxy Wardens - Epistemic Integrity)

Sacred Channels (7 total):
  1. orthodoxy.audit.requested - Audit initiation requests
  2. orthodoxy.validation.requested - Validation requests
  3. neural_engine.screening.completed - Validate screening results
  4. babel.sentiment.completed - Validate sentiment scores
  5. memory.write.completed - Audit memory writes
  6. vee.explanation.completed - Validate VEE outputs
  7. langgraph.response.completed - Audit final responses

Purpose:
  Ensure epistemic integrity and divine compliance.
  Sacred guardians of truth and validation.

Migration: Phase 2 (Listener #3 of 7)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready (Feb 6, 2026)
"""

import asyncio
import logging
import sys
import os

# Add parent directories to path for imports
# CRITICAL: /app MUST be first so global core/ (symlink → vitruvyan_core/core)
# takes priority over the local api_orthodoxy_wardens/core/ package.
sys.path.insert(0, '/app/api_orthodoxy_wardens')
sys.path.insert(0, '/app')

from redis_listener import OrthodoxyWardensCognitiveBusListener
from vitruvyan_core.core.synaptic_conclave.consumers import wrap_legacy_listener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("OrthodoxyWardensStreamsWrapper")

async def main():
    """⚖️ Start Orthodoxy Wardens Streams listener with zero-code-change adapter"""
    
    logger.info("⚖️ Orthodoxy Wardens Listener Sacred Streams Bridge starting...")
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = OrthodoxyWardensCognitiveBusListener()
    
    # Step 2: Define sacred channels (must match legacy listener)
    sacred_channels = [
        "orthodoxy.audit.requested",
        "orthodoxy.validation.requested",
        "neural_engine.screening.completed",
        "babel.sentiment.completed",
        "memory.write.completed",
        "vee.explanation.completed",
        "langgraph.response.completed"
    ]
    
    logger.info(f"⚖️ Orthodoxy Wardens subscribed to {len(sacred_channels)} streams")
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="orthodoxy_wardens",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"  # Legacy method name
    )
    
    logger.info("⚖️ Orthodoxy Wardens adapter initialized, starting consumption...")
    
    # Step 4: Start adapter (blocking)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚖️ Orthodoxy Wardens Listener stopped by user")
    except Exception as e:
        logger.error(f"⚖️ Orthodoxy Wardens Listener error: {e}", exc_info=True)
        raise
