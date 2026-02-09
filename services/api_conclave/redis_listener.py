#!/usr/bin/env python3
"""
🕯 Synaptic Conclave - Redis Pub/Sub Listener (Legacy)

Epistemic Observatory que observa TODOS os canais dos Sacred Orders.

Sacred Order: GOVERNANCE (Epistemic Observatory)
Role: Passive observer, event chronicler, system health monitoring

Sacred Domains Observed (8 total):
  1. conclave.* - Own orchestration events
  2. epistemic.drift - System-wide coherence alerts
  3. memory.* - Archivarium + Mnemosyne operations
  4. codex.* - Perception (data gathering)
  5. neural_engine.* - Reason (quantitative analysis)
  6. babel.* - Discourse (linguistic processing)
  7. orthodoxy.* - Truth (validation)
  8. vault.* - Truth (archival)

Purpose:
  Monitor system-wide epistemic activity for observatory dashboard.
  Chronicle inter-Order communication patterns.
  NO processing, NO routing, PURE observation (Sacred Invariant compliance).

Pattern: Legacy Pub/Sub (to be wrapped by ListenerAdapter)
Status: Backward compatibility layer (post-rewrite Feb 8, 2026)
Migration: Phase 2 (Listener #5 of 7)
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any
import redis.asyncio as redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

class ConclaveCognitiveBusListener:
    """
    🕯 Legacy Pub/Sub listener for Epistemic Observatory.
    
    BACKWARD COMPATIBILITY: Wraps legacy Pub/Sub logic for zero-code-change migration.
    Will be wrapped by ListenerAdapter (Streams-native).
    """
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "omni_redis")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.logger = logging.getLogger("ConclavePubSubListener")
        
        # Legacy Pub/Sub channels (will be mapped to Streams by adapter)
        self.legacy_channels = [
            "conclave_events",      # Orchestration events
            "epistemic_drift",      # System coherence alerts
            "memory_orders",        # Memory operations
            "perception.codex",     # Data gathering
            "reason.neural",        # Quantitative analysis
            "discourse.babel",      # Linguistic processing
            "truth.orthodoxy",      # Validation
            "truth.vault"           # Archival
        ]
        
        self.logger.info(f"🕯 Conclave Observer initialized for {len(self.legacy_channels)} domains")
    
    async def handle_sacred_message(self, message: Dict[str, Any]):
        """
        Handle incoming Pub/Sub message (legacy interface).
        
        ListenerAdapter will call this method with Streams events transformed to Pub/Sub format.
        
        Args:
            message: Redis Pub/Sub message dict with keys: type, channel, data
        """
        if message.get("type") != "message":
            return
        
        channel = message.get("channel", "unknown")
        if isinstance(channel, bytes):
            channel = channel.decode("utf-8")
        
        data = message.get("data", "")
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        
        # ==============================
        # EPISTEMIC OBSERVATORY LOGIC
        # ==============================
        # Passive observation only (Sacred Invariant compliance)
        # NO processing, NO routing, NO correlation
        
        try:
            # Parse payload
            payload = json.loads(data) if isinstance(data, str) else data
            
            # Log observation (pure chronicler)
            self.logger.info(
                f"🕯 Observatory: {channel} | "
                f"Payload: {str(payload)[:100]}... | "
                f"Size: {len(str(payload))} bytes"
            )
            
            # Optional: Increment Prometheus counter (passive metric)
            # conclave_events_observed_total.labels(domain=channel.split('.')[0]).inc()
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"🕯 Observatory: Non-JSON payload on {channel}: {data[:50]}")
        except Exception as e:
            self.logger.error(f"🕯 Observatory error on {channel}: {e}", exc_info=True)
    
    async def start(self):
        """
        Start legacy Pub/Sub listener (DEPRECATED pattern).
        
        NOTE: This method is for backward compatibility only.
        Production uses streams_listener.py (ListenerAdapter wrapper).
        """
        self.logger.info(f"🕯 Starting legacy Pub/Sub listener (DEPRECATED)")
        self.logger.info(f"🕯 Connecting to Redis: {self.redis_host}:{self.redis_port}")
        
        r = await redis.from_url(f"redis://{self.redis_host}:{self.redis_port}")
        pubsub = r.pubsub()
        
        await pubsub.subscribe(*self.legacy_channels)
        self.logger.info(f"🕯 Subscribed to {len(self.legacy_channels)} Pub/Sub channels")
        
        try:
            async for message in pubsub.listen():
                await self.handle_sacred_message(message)
        except asyncio.CancelledError:
            self.logger.info("🕯 Listener cancelled (graceful shutdown)")
            await pubsub.unsubscribe()
            await r.aclose()
            raise
        except Exception as e:
            self.logger.error(f"🕯 Listener crashed: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    """Direct execution for testing (not for production)"""
    listener = ConclaveCognitiveBusListener()
    
    try:
        asyncio.run(listener.start())
    except KeyboardInterrupt:
        print("🕯 Listener stopped by user")
