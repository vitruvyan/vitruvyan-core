"""
DSE Service — Redis Streams Listener (LIVELLO 2)
=================================================

Background process that consumes events from the Synaptic Conclave
and delegates to DSEBusAdapter.

Migration from aegis:
  OLD: redis.asyncio PubSub (fire-and-forget, no acknowledgment)
  NEW: StreamBus (Redis Streams, consumer groups, explicit acknowledgment)

Consumer group: dse_edge
Consumer ID:    dse_1 (configurable via DSE_CONSUMER_ID env var)

Last updated: Feb 26, 2026
"""

import asyncio
import json
import logging
from typing import Any, Dict

from core.synaptic_conclave.transport.streams import StreamBus

from infrastructure.edge.dse.events.channels import DSEChannels

from .adapters.bus_adapter import DSEBusAdapter
from .config import config

logger = logging.getLogger(__name__)


class DSEStreamsListener:
    """
    Consumes DSE events from Redis Streams.

    Pattern: generator-based consumption with explicit acknowledgment.
    """

    def __init__(self, adapter: DSEBusAdapter, bus: StreamBus) -> None:
        self.adapter = adapter
        self.bus = bus

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def setup_consumer_groups(self) -> None:
        """Create consumer groups for all subscribed streams (idempotent)."""
        for channel in DSEChannels.SUBSCRIBED:
            try:
                self.bus.create_consumer_group(
                    channel,
                    config.CONSUMER_GROUP,
                    mkstream=True,
                )
                logger.info("Consumer group ready: stream=%s group=%s", channel, config.CONSUMER_GROUP)
            except Exception as exc:
                logger.debug("Consumer group already exists (%s): %s", channel, exc)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Start consuming events. Runs until cancelled."""
        self.setup_consumer_groups()
        logger.info(
            "DSEStreamsListener started — group=%s consumer=%s streams=%d",
            config.CONSUMER_GROUP, config.CONSUMER_ID, len(DSEChannels.SUBSCRIBED),
        )

        heartbeat_task = asyncio.create_task(self._heartbeat())
        try:
            await self._consume_loop()
        except asyncio.CancelledError:
            logger.info("DSEStreamsListener cancelled — shutting down")
        finally:
            heartbeat_task.cancel()

    async def _consume_loop(self) -> None:
        """Generator-based multi-stream consumption."""
        while True:
            try:
                for channel in DSEChannels.SUBSCRIBED:
                    events = self.bus.consume(
                        channel,
                        config.CONSUMER_GROUP,
                        config.CONSUMER_ID,
                        count=10,
                        block_ms=100,
                    )
                    for event in events:
                        await self._handle(event)
                        self.bus.acknowledge(channel, config.CONSUMER_GROUP, event.event_id)
            except Exception as exc:
                logger.error("DSEStreamsListener._consume_loop error: %s", exc)
            await asyncio.sleep(0.05)  # yield to event loop

    async def _handle(self, event: Any) -> None:
        """Route event to the appropriate adapter method."""
        stream: str = event.stream
        try:
            payload: Dict[str, Any] = (
                json.loads(event.payload) if isinstance(event.payload, (str, bytes)) else {}
            )
        except Exception:
            payload = {}

        try:
            if stream == DSEChannels.WEAVE_COMPLETED:
                self.adapter.prepare(
                    weaver_context=payload.get("weaver_context", {}),
                    user_id=payload.get("user_id", "system"),
                    trace_id=payload.get("trace_id", "unknown"),
                    trigger="weave.completed",
                )
                # After prepare, request Conclave governance
                self.adapter.request_governance(
                    trace_id=payload.get("trace_id", "unknown"),
                    design_points_count=payload.get("design_points_count", 0),
                    strategy=payload.get("strategy", "unknown"),
                )

            elif stream == DSEChannels.GOVERNANCE_APPROVED:
                # Trigger actual DSE run (simplified: use cached design points from trace)
                # In production: retrieve design points from a session store / Vault
                trace_id = payload.get("trace_id", "unknown")
                logger.info("Governance approved — DSE run would execute for trace_id=%s", trace_id)

            elif stream == DSEChannels.GOVERNANCE_REJECTED:
                self.adapter.log_rejection(
                    trace_id=payload.get("trace_id", "unknown"),
                    reason=payload.get("reason", "conclave_rejected"),
                    rejected_by=payload.get("rejected_by"),
                )

            else:
                logger.debug("DSEStreamsListener: unhandled stream %s", stream)

        except Exception as exc:
            logger.error("DSEStreamsListener._handle error on stream %s: %s", stream, exc)

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat(self) -> None:
        while True:
            try:
                await asyncio.sleep(60)
                logger.info(
                    "DSEStreamsListener heartbeat — group=%s consumer=%s",
                    config.CONSUMER_GROUP, config.CONSUMER_ID,
                )
            except asyncio.CancelledError:
                break
