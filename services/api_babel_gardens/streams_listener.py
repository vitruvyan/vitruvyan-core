#!/usr/bin/env python3
"""
🌿 Babel Gardens — Streams Listener (No Pub/Sub)

This listener currently ACKs and logs inbound streams for the Discourse layer.
Processing is performed via HTTP APIs (Pattern Weavers / LangGraph integration).
"""

import asyncio
import logging
import sys
import os
from typing import Any

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_babel_gardens')

from core.synaptic_conclave.transport.streams import StreamBus
from api_babel_gardens.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("BabelGardensStreamsListener")

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
        logger.info("🌿 received=%s event_id=%s", observed_channel, event.event_id)
        logger.debug("🌿 payload=%s", str(payload)[:240])
        bus.ack(event, group=group)


async def main() -> None:
    config = get_config()
    bus = StreamBus(host=config.redis.host, port=config.redis.port)

    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "babel_gardens"))
    consumer = os.getenv("CONSUMER_NAME", "babel_gardens:worker")
    channels = [
        "codex.discovery.mapped",
        "babel.linguistic.synthesis",
        "babel.multilingual.bridge",
        "babel.knowledge.cultivation",
    ]

    logger.info("🌿 Starting Babel Gardens listener (Streams-only) group=%s streams=%d", group, len(channels))
    await asyncio.gather(*[_consume_one_stream(bus, c, group, consumer) for c in channels])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🌿 Babel Gardens listener stopped by user")
    except Exception as e:
        logger.error(f"🌿 Babel Gardens listener error: {e}", exc_info=True)
        raise
