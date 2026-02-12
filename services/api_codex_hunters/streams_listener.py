#!/usr/bin/env python3
"""
🗝️ Codex Hunters — Streams Listener (No Pub/Sub)

Consumes request streams and dispatches to Codex Hunters API (HTTP) for execution.
"""

import asyncio
import logging
import sys
import os
from typing import Any, Dict, Optional

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_codex_hunters')

import httpx

from core.synaptic_conclave.transport.streams import StreamBus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("CodexHuntersStreamsListener")

def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


def _expedition_type_for_channel(channel: str) -> str:
    mapping = {
        "codex.data.refresh.requested": "data_refresh",
        "codex.technical.momentum.requested": "momentum_backfill",
        "codex.technical.trend.requested": "trend_backfill",
        "codex.technical.volatility.requested": "volatility_backfill",
        "codex.schema.validation.requested": "schema_validation",
        "codex.fundamentals.refresh.requested": "fundamentals_refresh",
    }
    return mapping.get(channel, "unknown")


async def _dispatch_to_api(client: httpx.AsyncClient, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    expedition_type = _expedition_type_for_channel(channel)
    resp = await client.post(
        "/expedition/run",
        json={"expedition_type": expedition_type, "parameters": payload},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


async def _consume_one_stream(
    bus: StreamBus,
    client: httpx.AsyncClient,
    channel: str,
    group: str,
    consumer: str,
) -> None:
    bus.create_consumer_group(channel=channel, group=group, start_id="0")
    gen = bus.consume(channel=channel, group=group, consumer=consumer, count=10, block_ms=1000)

    while True:
        event = await asyncio.to_thread(next, gen, None)
        if event is None:
            continue

        observed_channel = _channel_from_stream(event.stream)
        payload_any: Any = event.payload
        payload: Dict[str, Any] = payload_any if isinstance(payload_any, dict) else {}
        correlation_id: Optional[str] = getattr(event, "correlation_id", None) or payload.get("correlation_id") or event.event_id

        try:
            result = await _dispatch_to_api(client, observed_channel, payload)
            # Emit a lightweight completion event (dispatch acknowledgement)
            bus.emit(
                channel="codex.expedition.completed",
                payload={
                    "correlation_id": correlation_id,
                    "requested_channel": observed_channel,
                    "dispatch": "accepted",
                    "api_result": result,
                },
                emitter="codex_hunters.listener",
                correlation_id=correlation_id,
            )
            bus.ack(event, group=group)
            logger.info("🗝️ dispatched=%s event_id=%s", observed_channel, event.event_id)
        except Exception as exc:
            logger.error("🗝️ dispatch_failed=%s event_id=%s err=%s", observed_channel, event.event_id, exc, exc_info=True)
            # no ACK


async def main() -> None:
    bus = StreamBus(host=os.getenv("REDIS_HOST", "core_redis"), port=int(os.getenv("REDIS_PORT", "6379")))
    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "codex_hunters"))
    consumer = os.getenv("CONSUMER_NAME", "codex_hunters:worker")

    channels = [
        "codex.data.refresh.requested",
        "codex.technical.momentum.requested",
        "codex.technical.trend.requested",
        "codex.technical.volatility.requested",
        "codex.schema.validation.requested",
        "codex.fundamentals.refresh.requested",
    ]

    base_url = os.getenv("CODEX_API_URL", "http://codex_hunters:8008")
    logger.info("🗝️ Starting Codex Hunters listener (Streams-only) api=%s group=%s streams=%d", base_url, group, len(channels))

    async with httpx.AsyncClient(base_url=base_url, headers={"Content-Type": "application/json"}) as client:
        await asyncio.gather(*[_consume_one_stream(bus, client, c, group, consumer) for c in channels])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🗝️ Codex Hunters listener stopped by user")
    except Exception as e:
        logger.error(f"🗝️ Codex Hunters listener error: {e}", exc_info=True)
        raise
