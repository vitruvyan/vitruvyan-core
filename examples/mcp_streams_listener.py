"""
🧩 MCP Listener - Model Context Protocol Streams Bridge (Phase 3 Migration)

ZERO-CODE-CHANGE wrapper for MCPListener using ListenerAdapter.

Sacred Order: TRUTH (Epistemic Governance Layer)

Sacred Channels (1 total):
  1. conclave.mcp.actions - MCP action requests

Purpose:
  Bridge Model Context Protocol requests to Vitruvyan's Sacred Orders architecture.
  Epistemic continuity through protocol neutrality.

Migration: Phase 3 (Listener #7 of 13)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready after 6 successful migrations
"""

import asyncio
import logging

# MCP has flat structure, PYTHONPATH=/app in docker-compose
from mcp_listener import MCPListener
from core.cognitive_bus.consumers.listener_adapter import wrap_legacy_listener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MCPStreamsWrapper")

async def main():
    """🧩 Start MCP Streams listener with zero-code-change adapter"""
    
    logger.info("🧩 MCP Listener Sacred Streams Bridge starting...")
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = MCPListener()
    
    # Step 2: Define sacred channels
    sacred_channels = [
        "conclave.mcp.actions"
    ]
    
    logger.info(f"🧩 MCP Listener subscribed to {len(sacred_channels)} streams")
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="mcp_listener",
        sacred_channels=sacred_channels
    )
    
    logger.info("🧩 MCP Listener adapter initialized, starting consumption...")
    
    # Step 4: Start adapter
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🧩 MCP Listener stopped by user")
    except Exception as e:
        logger.error(f"🧩 MCP Listener error: {e}", exc_info=True)
