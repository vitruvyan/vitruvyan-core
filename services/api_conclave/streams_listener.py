#!/usr/bin/env python3
"""
🕯 Synaptic Conclave — Streams Listener (No Pub/Sub)

This is the Epistemic Observatory consumer.
It consumes Redis Streams directly via StreamBus and performs PASSIVE observation only.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict

# Ensure /app packages resolve in container
sys.path.insert(0, "/app")
sys.path.insert(0, "/app/api_conclave")

from core.synaptic_conclave.transport.streams import StreamBus
from api_conclave.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ConclaveStreamsListener")


def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


async def _consume_one_stream(bus: StreamBus, channel: str, group: str, consumer: str) -> None:
    bus.create_consumer_group(channel=channel, group=group, start_id="0")
    gen = bus.consume(channel=channel, group=group, consumer=consumer, count=10, block_ms=1000)

    while True:
        event = await asyncio.to_thread(next, gen, None)
        if event is None:
            continue

        observed_channel = _channel_from_stream(event.stream)
        payload: Any = event.payload
        if isinstance(payload, dict):
            preview = str(payload)[:180]
        else:
            preview = str(payload)[:180]

        logger.info("🕯 observed=%s event_id=%s payload=%s", observed_channel, event.event_id, preview)
        bus.ack(event, group=group)


async def main() -> None:
    logger.info("🕯 Starting Conclave Epistemic Observatory (Streams-only)")

    bus = StreamBus(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", settings.CONSUMER_GROUP))
    consumer = os.getenv("CONSUMER_NAME", settings.CONSUMER_NAME)
    channels = list(settings.SACRED_CHANNELS)

    logger.info("🕯 group=%s consumer=%s streams=%d", group, consumer, len(channels))

    await asyncio.gather(*[_consume_one_stream(bus, c, group, consumer) for c in channels])


if __name__ == "__main__":
    asyncio.run(main())
