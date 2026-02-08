#!/usr/bin/env python3
"""
🔐 Vault Keepers - Redis Streams Listener (Phase 2 Migration)

ZERO-CODE-CHANGE wrapper for VaultKeepersCognitiveBusListener using ListenerAdapter.

Sacred Order: TRUTH (Vault Keepers - Knowledge Preservation)

Sacred Channels (5 total):
  1. vault.archive.requested - Archive creation requests
  2. vault.restore.requested - Version restoration requests
  3. vault.snapshot.requested - System snapshot requests
  4. orthodoxy.audit.completed - Store audit results
  5. neural_engine.screening.completed - Archive screening results

Purpose:
  Preserve and version Vitruvyan's sacred knowledge.
  Divine custodians of the memory vaults.

Migration: Phase 2 (Listener #2 of 7)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready (Feb 6, 2026)
"""

import asyncio
import logging
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_vault_keepers')

from redis_listener import VaultKeepersCognitiveBusListener
from core.synaptic_conclave.consumers import wrap_legacy_listener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("VaultKeepersStreamsWrapper")

async def main():
    """🔐 Start Vault Keepers Streams listener with zero-code-change adapter"""
    
    logger.info("🔐 Vault Keepers Listener Sacred Streams Bridge starting...")
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = VaultKeepersCognitiveBusListener()
    
    # Step 2: Define sacred channels (must match legacy listener)
    sacred_channels = [
        "vault.archive.requested",
        "vault.restore.requested",
        "vault.snapshot.requested",
        "orthodoxy.audit.completed",
        "neural_engine.screening.completed"
    ]
    
    logger.info(f"🔐 Vault Keepers subscribed to {len(sacred_channels)} streams")
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="vault_keepers",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"  # Legacy method name
    )
    
    logger.info("🔐 Vault Keepers adapter initialized, starting consumption...")
    
    # Step 4: Start adapter (blocking)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🔐 Vault Keepers Listener stopped by user")
    except Exception as e:
        logger.error(f"🔐 Vault Keepers Listener error: {e}", exc_info=True)
        raise
