#!/usr/bin/env python3
"""
🕯 Synaptic Conclave - Redis Streams Listener (Phase 2 Migration)

ZERO-CODE-CHANGE wrapper for ConclaveCognitiveBusListener using ListenerAdapter.

Sacred Order: GOVERNANCE (Epistemic Observatory)
Role: Passive observer of ALL Sacred Orders communication

Sacred Channels (20+ domains observed):
  Orchestration:
    - conclave.events.broadcast
    - conclave.health.ping
  
  Memory:
    - memory.write.completed
    - memory.sync.requested
  
  Perception (Codex Hunters):
    - codex.discovery.mapped
    - codex.reddit.scraped
    - codex.news.collected
  
  Reason (Neural Engine):
    - neural_engine.screening.completed
    - neural_engine.comparison.completed
  
  Discourse (Babel Gardens):
    - babel.sentiment.completed
    - babel.fusion.completed
    - babel.emotion.detected
  
  Truth (Orthodoxy):
    - orthodoxy.audit.requested
    - orthodoxy.validation.completed
  
  Truth (Vault):
    - vault.archive.completed
    - vault.retrieval.requested
  
  Orchestration (LangGraph):
    - langgraph.response.completed
    - langgraph.comparison.routed
  
  Pattern Recognition:
    - pattern_weavers.context.extracted

Purpose:
  Monitor inter-Order communication for system health dashboard.
  Chronicle epistemic activity patterns.
  Provide observability for Sacred Orders ecosystem.
  
  SACRED INVARIANTS COMPLIANCE:
    ✅ NO payload inspection (bus is semantically blind)
    ✅ NO correlation logic (no smart routing)
    ✅ NO synthesis (pure observation)
    ✅ NO semantic routing (namespace-based only)

Migration: Phase 2 (Listener #5 of 7)
Pattern: wrap_legacy_listener (from listener_adapter.py)
Status: Production-ready (Feb 8, 2026)
Architecture: Octopus-Mycelium (2/3 neurons in arms, 1/3 in Observatory)
"""

import asyncio
import logging
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_conclave')

from redis_listener import ConclaveCognitiveBusListener
from core.synaptic_conclave.consumers import wrap_legacy_listener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("ConclaveStreamsWrapper")

async def main():
    """🕯 Start Epistemic Observatory Streams listener with zero-code-change adapter"""
    
    logger.info("🕯 Synaptic Conclave Epistemic Observatory starting...")
    logger.info("🕯 Role: Passive observer of ALL Sacred Orders")
    
    # Step 1: Instantiate existing legacy listener (NO MODIFICATIONS)
    legacy_listener = ConclaveCognitiveBusListener()
    
    # Step 2: Define sacred channels (comprehensive observatory)
    # Maps legacy Pub/Sub channels to Streams dot-notation
    sacred_channels = [
        # Orchestration
        "conclave.events.broadcast",
        "conclave.health.ping",
        "conclave.awakened",
        
        # System-wide
        "epistemic.drift.detected",
        "epistemic.coherence.alert",
        
        # Memory Orders
        "memory.write.completed",
        "memory.sync.requested",
        "memory.coherence.checked",
        
        # Codex Hunters (Perception)
        "codex.discovery.mapped",
        "codex.reddit.scraped",
        "codex.news.collected",
        "codex.refresh.scheduled",
        
        # Neural Engine (Reason)
        "neural_engine.screening.completed",
        "neural_engine.comparison.completed",
        "neural_engine.risk.assessed",
        
        # Babel Gardens (Discourse)
        "babel.sentiment.completed",
        "babel.fusion.completed",
        "babel.emotion.detected",
        "babel.translation.completed",
        
        # Orthodoxy Wardens (Truth)
        "orthodoxy.audit.requested",
        "orthodoxy.validation.completed",
        "orthodoxy.heresy.detected",
        
        # Vault Keepers (Truth)
        "vault.archive.completed",
        "vault.retrieval.requested",
        "vault.snapshot.created",
        
        # LangGraph (Orchestration)
        "langgraph.response.completed",
        "langgraph.comparison.routed",
        "langgraph.screening.executed",
        
        # Pattern Weavers
        "pattern_weavers.context.extracted",
        "pattern_weavers.weave.completed"
    ]
    
    logger.info(f"🕯 Observatory monitoring {len(sacred_channels)} sacred streams")
    logger.info(f"🕯 Architecture: Octopus-Mycelium (passive observation, zero interference)")
    
    # Step 3: Wrap with ListenerAdapter (handles all Streams logic)
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="conclave_observatory",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"  # Legacy method name
    )
    
    logger.info("🕯 Epistemic Observatory adapter initialized")
    logger.info("🕯 Starting consumption (passive observer mode)...")
    
    # Step 4: Start adapter (blocking)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🕯 Epistemic Observatory stopped by user")
    except Exception as e:
        logger.error(f"🕯 Epistemic Observatory error: {e}", exc_info=True)
        raise
