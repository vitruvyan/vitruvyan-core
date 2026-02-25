#!/usr/bin/env python3
"""
Memory Orders — Redis Streams Listener

Consumes events from Cognitive Bus (Redis Streams) and delegates to bus_adapter.

Pattern: ListenerAdapter wrapper (zero-code-change migration)

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — streams listener)
"""

import asyncio
import logging
import sys

# Add paths for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_memory_orders')

from core.synaptic_conclave.transport.streams import StreamBus
from core.governance.memory_orders.events import (
    MEMORY_COHERENCE_REQUESTED,
    MEMORY_HEALTH_REQUESTED,
    MEMORY_SYNC_REQUESTED,
)
from api_memory_orders.adapters import MemoryBusAdapter
from api_memory_orders.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MemoryStreamsListener")


class MemoryStreamsListener:
    """
    Redis Streams consumer for Memory Orders.
    
    Subscribes to:
    - memory.coherence.requested
    - memory.health.requested
    - memory.sync.requested
    
    Delegates handling to MemoryBusAdapter.
    """
    
    def __init__(self):
        self.bus = StreamBus()
        self.adapter = MemoryBusAdapter()
        
        # Consumer group + consumer ID
        self.group = "memory_orders_group"
        self.consumer_id = "memory_listener_1"
        
        # Channels to consume
        self.channels = [
            MEMORY_COHERENCE_REQUESTED,
            MEMORY_HEALTH_REQUESTED,
            MEMORY_SYNC_REQUESTED,
        ]
        
        logger.info(f"Initialized listener: group={self.group}, consumer={self.consumer_id}")
        logger.info(f"Subscribed channels: {self.channels}")
    
    async def start(self):
        """Start consuming events from Redis Streams."""
        logger.info("=" * 60)
        logger.info("Starting Memory Orders Streams Listener")
        logger.info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        logger.info("=" * 60)
        
        # Create consumer groups
        for channel in self.channels:
            try:
                self.bus.create_consumer_group(channel, self.group)
                logger.info(f"✅ Consumer group '{self.group}' ready for {channel}")
            except Exception as e:
                logger.warning(f"Consumer group may already exist for {channel}: {e}")
        
        # Start consuming with one task per stream.
        # `StreamBus.consume()` is an infinite generator for a single channel,
        # so multi-channel consumption must run in parallel tasks.
        logger.info(f"🎧 Listening on {len(self.channels)} channels...")
        tasks = [
            asyncio.create_task(self._consume_channel(channel))
            for channel in self.channels
        ]
        await asyncio.gather(*tasks)

    async def _consume_channel(self, channel: str) -> None:
        """Consume one channel forever and acknowledge processed events."""
        consumer_name = f"{self.consumer_id}_{channel.replace('.', '_')}"
        iterator = self.bus.consume(
            channel,
            self.group,
            consumer_name,
            count=1,
            block_ms=1000,
        )
        while True:
            try:
                event = await asyncio.to_thread(lambda: next(iterator, None))
                if event is None:
                    await asyncio.sleep(0.1)
                    continue

                await self.handle_event(event)
                self.bus.ack(event, group=self.group)
                logger.info(f"✅ ACK {event.event_id} from {event.stream}")
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop for {channel}: {e}")
                iterator = self.bus.consume(
                    channel,
                    self.group,
                    consumer_name,
                    count=1,
                    block_ms=1000,
                )
                await asyncio.sleep(1)
    
    async def handle_event(self, event):
        """
        Handle incoming event based on channel.
        
        Args:
            event: TransportEvent from StreamBus
        """
        logger.info(f"📨 Received event: {event.stream} (id={event.event_id})")
        
        try:
            # Parse payload
            payload = event.payload if isinstance(event.payload, dict) else {}
            channel = event.stream.replace("vitruvyan:", "", 1)
            
            # Route to appropriate handler
            if channel == MEMORY_COHERENCE_REQUESTED:
                await self.handle_coherence_request(payload)
            
            elif channel == MEMORY_HEALTH_REQUESTED:
                await self.handle_health_request(payload)
            
            elif channel == MEMORY_SYNC_REQUESTED:
                await self.handle_sync_request(payload)
            
            else:
                logger.warning(f"Unknown channel: {event.stream} (normalized={channel})")
        
        except Exception as e:
            logger.error(f"Failed to handle event {event.event_id}: {e}")
            raise
    
    async def handle_coherence_request(self, payload: dict):
        """Handle coherence check request."""
        table = payload.get("table", "entities")
        collection = payload.get("collection")
        embedded_column = payload.get("embedded_column", "embedded")
        reconcile_limit = payload.get("reconcile_limit", 1000)
        allow_mass_delete = bool(payload.get("allow_mass_delete", False))
        idempotency_key = payload.get("idempotency_key")

        try:
            reconcile_limit = int(reconcile_limit)
            if reconcile_limit <= 0:
                raise ValueError("reconcile_limit must be > 0")
        except (TypeError, ValueError):
            logger.warning("Invalid reconcile_limit=%r, fallback to 1000", reconcile_limit)
            reconcile_limit = 1000
        
        logger.info(f"Processing coherence check: {table} ↔ {collection}")
        
        report = await self.adapter.handle_coherence_check(
            table=table,
            collection=collection,
            embedded_column=embedded_column,
        )
        
        logger.info(f"Coherence check complete: status={report.status}, drift={report.drift_percentage:.2f}%")

        if not settings.ENABLE_AUTO_SYNC:
            return

        if report.status != "critical":
            logger.info(
                "Auto-sync enabled but coherence status is %s; skipping auto-reconciliation",
                report.status,
            )
            return

        if settings.MEMORY_RECONCILIATION_MODE == "dry_run":
            logger.warning(
                "Auto-sync skipped: MEMORY_RECONCILIATION_MODE=dry_run does not execute repairs"
            )
            return

        logger.warning(
            "Critical drift detected for %s ↔ %s; triggering auto-reconciliation "
            "(mode=%s, limit=%s, allow_mass_delete=%s)",
            table,
            collection,
            settings.MEMORY_RECONCILIATION_MODE,
            reconcile_limit,
            allow_mass_delete,
        )
        result = await self.adapter.handle_reconciliation(
            table=table,
            collection=collection,
            limit=reconcile_limit,
            execute=True,
            idempotency_key=idempotency_key,
            allow_mass_delete=allow_mass_delete,
        )
        logger.info(
            "Auto-reconciliation result: status=%s severity=%s operations=%s",
            result.get("status"),
            result.get("severity"),
            result.get("operations_count"),
        )
    
    async def handle_health_request(self, payload: dict):
        """Handle health check request."""
        logger.info("Processing health check")
        
        health = await self.adapter.handle_health_check()
        
        logger.info(f"Health check complete: status={health.overall_status}")
    
    async def handle_sync_request(self, payload: dict):
        """Handle sync planning request."""
        mode = payload.get("mode", "incremental")
        table = payload.get("table", "entities")
        collection = payload.get("collection")
        
        logger.info(f"Processing sync request: mode={mode}")
        
        plan = await self.adapter.handle_sync_request(
            mode=mode,
            table=table,
            collection=collection
        )
        
        logger.info(f"Sync plan complete: {plan.total_operations} operations")


async def main():
    """Main entry point."""
    listener = MemoryStreamsListener()
    
    try:
        await listener.start()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
