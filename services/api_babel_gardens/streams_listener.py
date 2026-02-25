#!/usr/bin/env python3
"""
🌿 Babel Gardens — Streams Listener (Active Processing)

Consumes events from the Synaptic Conclave and dispatches
to Babel Gardens HTTP API for linguistic processing.

Channels consumed:
- codex.entity.bound       → POST /v1/emotion/detect    (emotion detection)
                           → POST /analyze               (sentiment analysis)
- codex.discovery.mapped   → POST /v1/emotion/detect    (discovery processing)
- babel.linguistic.synthesis → POST /v2/comprehend       (unified comprehension)
- babel.multilingual.bridge  → log only (future: translation pipeline)
- babel.knowledge.cultivation → log only (future: knowledge graph)
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_babel_gardens')

import httpx

from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_envelope import TransportEvent
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


def _extract_text_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract embeddable text from an event payload.

    Tries several common payload shapes produced by Codex (bind, discover).
    """
    # Direct text field
    if isinstance(payload.get("text"), str) and payload["text"].strip():
        return payload["text"]

    # Nested inside 'data' (Codex bind / discovery events)
    data = payload.get("data") or payload.get("normalized_data") or {}
    if isinstance(data, dict):
        for key in ("normalized_text", "title", "text", "description", "content"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val

    # Fall back to entity_id (at least something to log)
    entity_id = payload.get("entity_id")
    if entity_id:
        return f"Entity: {entity_id}"

    return None


async def _process_linguistic_event(
    client: httpx.AsyncClient,
    channel: str,
    payload: Dict[str, Any],
    bus: StreamBus,
) -> None:
    """
    Dispatch linguistic processing based on channel.

    For codex.entity.bound and codex.discovery.mapped:
    1. Call /v1/emotion/detect for emotion analysis
    2. Call /analyze for sentiment analysis
    3. Emit babel.linguistic.completed event with results
    """
    text = _extract_text_from_payload(payload)
    if not text:
        logger.debug("🌿 No text found in payload for %s, skipping", channel)
        return

    entity_id = payload.get("entity_id", "unknown")
    results: Dict[str, Any] = {"entity_id": entity_id, "channel": channel}

    # ── Emotion detection ──
    try:
        emotion_resp = await client.post(
            "/v1/emotion/detect",
            json={"text": text[:8000], "language": "auto"},
            timeout=15.0,
        )
        emotion_resp.raise_for_status()
        results["emotion"] = emotion_resp.json()
        logger.info(
            "🌿 emotion entity=%s emotion=%s confidence=%.2f",
            entity_id,
            results["emotion"].get("emotion", "?"),
            results["emotion"].get("confidence", 0.0),
        )
    except Exception as e:
        logger.warning("🌿 Emotion detection failed for %s: %s", entity_id, e)
        results["emotion_error"] = str(e)

    # ── Sentiment analysis ──
    try:
        sentiment_resp = await client.post(
            "/analyze",
            json={"text": text[:4000]},
            timeout=15.0,
        )
        sentiment_resp.raise_for_status()
        results["sentiment"] = sentiment_resp.json()
        logger.info(
            "🌿 sentiment entity=%s label=%s",
            entity_id,
            results["sentiment"].get("label", "?"),
        )
    except Exception as e:
        logger.warning("🌿 Sentiment analysis failed for %s: %s", entity_id, e)
        results["sentiment_error"] = str(e)

    # ── Emit completion event ──
    try:
        bus.emit(
            channel="babel.linguistic.completed",
            payload={
                "entity_id": entity_id,
                "source_channel": channel,
                "emotion": results.get("emotion"),
                "sentiment": results.get("sentiment"),
            },
            emitter="babel_gardens.listener",
        )
    except Exception as e:
        logger.warning("🌿 Failed to emit babel.linguistic.completed: %s", e)


async def _process_comprehension_event(
    client: httpx.AsyncClient,
    payload: Dict[str, Any],
) -> None:
    """Dispatch to /v2/comprehend for unified comprehension (if enabled)."""
    text = _extract_text_from_payload(payload)
    if not text:
        return

    try:
        resp = await client.post(
            "/v2/comprehend",
            json={"text": text[:8000]},
            timeout=20.0,
        )
        if resp.status_code == 404:
            logger.debug("🌿 Comprehension v3 not enabled (BABEL_COMPREHENSION_V3=0)")
            return
        resp.raise_for_status()
        logger.info("🌿 comprehension result: %s", str(resp.json())[:200])
    except Exception as e:
        logger.warning("🌿 Comprehension call failed: %s", e)


async def _process_event(
    bus: StreamBus,
    client: httpx.AsyncClient,
    event: TransportEvent,
    group: str,
) -> bool:
    """Process a single stream event."""
    observed_channel = _channel_from_stream(event.stream)
    payload_any: Any = event.payload
    payload: Dict[str, Any] = payload_any if isinstance(payload_any, dict) else {}

    try:
        if observed_channel in {"codex.entity.bound", "codex.discovery.mapped"}:
            await _process_linguistic_event(client, observed_channel, payload, bus)
        elif observed_channel == "babel.linguistic.synthesis":
            await _process_comprehension_event(client, payload)
        else:
            # Future channels: multilingual.bridge, knowledge.cultivation
            logger.debug("🌿 passthrough channel=%s event_id=%s", observed_channel, event.event_id)

        bus.ack(event, group=group)
        logger.info("🌿 processed=%s event_id=%s", observed_channel, event.event_id)
        return True
    except Exception as exc:
        logger.error("🌿 processing_failed=%s err=%s", observed_channel, exc, exc_info=True)
        # ACK to avoid infinite redelivery on persistent errors
        bus.ack(event, group=group)
        return False


async def _consume_one_stream(
    bus: StreamBus,
    client: httpx.AsyncClient,
    channel: str,
    group: str,
    consumer: str,
) -> None:
    """Consume events from a single stream channel."""
    bus.create_consumer_group(channel=channel, group=group, start_id="0")

    while True:
        try:
            stream = f"{bus.prefix}:{channel}"
            response = await asyncio.to_thread(
                bus.client.xreadgroup,
                groupname=group,
                consumername=consumer,
                streams={stream: ">"},
                count=10,
                block=1000,
            )
            if not response:
                continue

            for stream_name, events in response:
                stream_str = stream_name.decode() if isinstance(stream_name, bytes) else stream_name
                for event_id, data in events:
                    event_id_str = event_id.decode() if isinstance(event_id, bytes) else event_id
                    transport_event = TransportEvent.from_redis(stream_str, event_id_str, data)
                    await _process_event(bus, client, transport_event, group)
        except Exception as e:
            logger.error("🌿 stream_error channel=%s: %s", channel, e, exc_info=True)
            await asyncio.sleep(2)


async def main() -> None:
    config = get_config()
    bus = StreamBus(host=config.redis.host, port=config.redis.port)

    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "babel_gardens"))
    consumer = os.getenv("CONSUMER_NAME", "babel_gardens:worker")

    channels = [
        "codex.entity.bound",
        "codex.discovery.mapped",
        "babel.linguistic.synthesis",
        "babel.multilingual.bridge",
        "babel.knowledge.cultivation",
    ]

    base_url = os.getenv(
        "BABEL_API_URL",
        f"http://babel_gardens:{config.service.port}",
    )
    logger.info(
        "🌿 Starting Babel Gardens listener (Active) api=%s group=%s streams=%d",
        base_url, group, len(channels),
    )
    logger.info("🌿 listening_channels=%s", ",".join(channels))

    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Content-Type": "application/json"},
    ) as client:
        await asyncio.gather(
            *[_consume_one_stream(bus, client, c, group, consumer) for c in channels]
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🌿 Babel Gardens listener stopped by user")
    except Exception as e:
        logger.error(f"🌿 Babel Gardens listener error: {e}", exc_info=True)
        raise
