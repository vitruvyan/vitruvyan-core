#!/usr/bin/env python3
"""
🗝️ Codex Hunters — Streams Listener (No Pub/Sub)

Consumes request streams and dispatches to Codex Hunters API (HTTP) for execution.
"""

import os
import sys
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_codex_hunters')

import httpx

from core.synaptic_conclave.events.event_envelope import TransportEvent
from core.synaptic_conclave.transport.streams import StreamBus
from core.governance.codex_hunters.events.codex_events import (
    CODEX_REQUEST_CHANNELS as _CODEX_CHANNELS,
    CHANNEL_TO_EXPEDITION_TYPE,
    OCULUS_EVIDENCE_CREATED,
    OCULUS_EVIDENCE_CREATED_LEGACY,
    EXPEDITION_COMPLETED,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("CodexHuntersStreamsListener")

CODEX_REQUEST_CHANNELS = list(_CODEX_CHANNELS)

OCULUS_CANONICAL_CHANNEL = OCULUS_EVIDENCE_CREATED
OCULUS_LEGACY_ALIAS_CHANNEL = OCULUS_EVIDENCE_CREATED_LEGACY


def _is_true(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


def _expedition_type_for_channel(channel: str) -> str:
    return CHANNEL_TO_EXPEDITION_TYPE.get(channel, "unknown")


def _resolve_oculus_channels() -> List[str]:
    mode = str(
        os.getenv("OCULUS_PRIME_EVENT_MIGRATION_MODE")
        or os.getenv("INTAKE_EVENT_MIGRATION_MODE")
        or "dual_write"
    ).strip().lower()
    include_legacy = _is_true(os.getenv("CODEX_OCULUS_CONSUME_LEGACY_ALIAS", "false"))

    if mode == "v1_only":
        channels = [OCULUS_LEGACY_ALIAS_CHANNEL]
    elif mode in {"dual_write", "v2_only"}:
        channels = [OCULUS_CANONICAL_CHANNEL]
    else:
        logger.warning("Unknown migration mode '%s'; fallback to canonical channel", mode)
        channels = [OCULUS_CANONICAL_CHANNEL]

    if include_legacy and OCULUS_LEGACY_ALIAS_CHANNEL not in channels:
        channels.append(OCULUS_LEGACY_ALIAS_CHANNEL)

    return channels


def _build_discovery_request(
    payload: Dict[str, Any],
    channel: str,
    correlation_id: str,
    fallback_event_id: str,
    transport_emitter: str,
) -> Dict[str, Any]:
    source = str(os.getenv("CODEX_OCULUS_SOURCE", "")).strip()

    event_payload_any: Any = payload.get("payload")
    event_payload: Dict[str, Any] = event_payload_any if isinstance(event_payload_any, dict) else {}

    metadata_any: Any = payload.get("metadata")
    metadata: Dict[str, Any] = metadata_any if isinstance(metadata_any, dict) else {}

    evidence_id = str(payload.get("evidence_id") or fallback_event_id)
    raw_data: Dict[str, Any] = {
        "event_channel": channel,
        "event_id": payload.get("event_id") or fallback_event_id,
        "event_version": payload.get("event_version"),
        "schema_ref": payload.get("schema_ref"),
        "timestamp_utc": payload.get("timestamp_utc") or payload.get("timestamp"),
        "evidence_id": payload.get("evidence_id"),
        "chunk_id": payload.get("chunk_id"),
        "idempotency_key": payload.get("idempotency_key"),
        "payload": event_payload,
        "metadata": metadata,
        "transport_emitter": transport_emitter,
    }

    request: Dict[str, Any] = {
        "entity_id": evidence_id,
        "raw_data": raw_data,
        "metadata": {
            "correlation_id": correlation_id,
            "stream_channel": channel,
        },
    }
    if source:
        request["source_type"] = source
    return request


def _dispatch_spec_for_channel(
    channel: str,
    payload: Dict[str, Any],
    correlation_id: str,
    event_id: str,
    transport_emitter: str,
) -> Tuple[str, Dict[str, Any]]:
    if channel in {OCULUS_CANONICAL_CHANNEL, OCULUS_LEGACY_ALIAS_CHANNEL}:
        return (
            "/discover",
            _build_discovery_request(
                payload=payload,
                channel=channel,
                correlation_id=correlation_id,
                fallback_event_id=event_id,
                transport_emitter=transport_emitter,
            ),
        )
    expedition_type = _expedition_type_for_channel(channel)
    return (
        "/expedition/run",
        {"expedition_type": expedition_type, "parameters": payload},
    )


async def _dispatch_to_api(
    client: httpx.AsyncClient,
    channel: str,
    payload: Dict[str, Any],
    correlation_id: str,
    event_id: str,
    transport_emitter: str,
) -> Dict[str, Any]:
    endpoint, body = _dispatch_spec_for_channel(
        channel=channel,
        payload=payload,
        correlation_id=correlation_id,
        event_id=event_id,
        transport_emitter=transport_emitter,
    )
    resp = await client.post(endpoint, json=body, timeout=30.0)
    resp.raise_for_status()
    data: Dict[str, Any] = resp.json() if resp.content else {}
    data["dispatch_endpoint"] = endpoint
    return data


def _resolve_correlation_id(event: TransportEvent, payload: Dict[str, Any]) -> str:
    payload_metadata_any: Any = payload.get("metadata")
    payload_metadata: Dict[str, Any] = payload_metadata_any if isinstance(payload_metadata_any, dict) else {}
    return (
        getattr(event, "correlation_id", None)
        or payload_metadata.get("correlation_id")
        or payload.get("correlation_id")
        or payload.get("event_id")
        or event.event_id
    )


def _stream_name(bus: StreamBus, channel: str) -> str:
    return f"{bus.prefix}:{channel}"


async def _process_event(
    bus: StreamBus,
    client: httpx.AsyncClient,
    event: TransportEvent,
    group: str,
) -> bool:
    observed_channel = _channel_from_stream(event.stream)
    payload_any: Any = event.payload
    payload: Dict[str, Any] = payload_any if isinstance(payload_any, dict) else {}
    correlation_id = _resolve_correlation_id(event, payload)

    try:
        result = await _dispatch_to_api(
            client=client,
            channel=observed_channel,
            payload=payload,
            correlation_id=correlation_id,
            event_id=event.event_id,
            transport_emitter=event.emitter,
        )
        # Emit a lightweight completion event (dispatch acknowledgement)
        bus.emit(
            channel="codex.expedition.completed",
            payload={
                "correlation_id": correlation_id,
                "requested_channel": observed_channel,
                "dispatched_endpoint": result.get("dispatch_endpoint"),
                "dispatch": "accepted",
                "api_result": result,
            },
            emitter="codex_hunters.listener",
            correlation_id=correlation_id,
        )
        bus.ack(event, group=group)
        logger.info("🗝️ dispatched=%s event_id=%s", observed_channel, event.event_id)
        return True
    except Exception as exc:
        logger.error(
            "🗝️ dispatch_failed=%s event_id=%s err=%s",
            observed_channel,
            event.event_id,
            exc,
            exc_info=True,
        )
        # no ACK
        return False


async def _drain_pending_for_channel(
    bus: StreamBus,
    client: httpx.AsyncClient,
    channel: str,
    group: str,
    consumer: str,
    max_rounds: int,
    batch_size: int,
) -> int:
    stream = _stream_name(bus, channel)
    total_recovered = 0

    for _ in range(max_rounds):
        response = await asyncio.to_thread(
            bus.client.xreadgroup,
            groupname=group,
            consumername=consumer,
            streams={stream: "0"},
            count=batch_size,
            block=1,
        )
        if not response:
            break

        recovered_this_round = 0
        for stream_name, events in response:
            stream_str = stream_name.decode() if isinstance(stream_name, bytes) else stream_name
            for event_id, data in events:
                event_id_str = event_id.decode() if isinstance(event_id, bytes) else event_id
                transport_event = TransportEvent.from_redis(stream_str, event_id_str, data)
                ok = await _process_event(bus=bus, client=client, event=transport_event, group=group)
                if ok:
                    recovered_this_round += 1
                    total_recovered += 1

        # Prevent tight infinite loops when all pending items keep failing.
        if recovered_this_round == 0:
            break

    return total_recovered


async def _read_new_events(
    bus: StreamBus,
    channel: str,
    group: str,
    consumer: str,
    count: int = 10,
    block_ms: int = 1000,
) -> List[TransportEvent]:
    stream = _stream_name(bus, channel)
    response = await asyncio.to_thread(
        bus.client.xreadgroup,
        groupname=group,
        consumername=consumer,
        streams={stream: ">"},
        count=count,
        block=block_ms,
    )
    if not response:
        return []

    parsed: List[TransportEvent] = []
    for stream_name, events in response:
        stream_str = stream_name.decode() if isinstance(stream_name, bytes) else stream_name
        for event_id, data in events:
            event_id_str = event_id.decode() if isinstance(event_id, bytes) else event_id
            parsed.append(TransportEvent.from_redis(stream_str, event_id_str, data))
    return parsed


async def _consume_one_stream(
    bus: StreamBus,
    client: httpx.AsyncClient,
    channel: str,
    group: str,
    consumer: str,
) -> None:
    bus.create_consumer_group(channel=channel, group=group, start_id="0")
    pending_recovery_enabled = _is_true(os.getenv("CODEX_PENDING_RECOVERY_ENABLED", "true"))
    pending_recovery_interval_sec = int(os.getenv("CODEX_PENDING_RECOVERY_INTERVAL_SEC", "30"))
    pending_recovery_max_rounds = int(os.getenv("CODEX_PENDING_RECOVERY_MAX_ROUNDS", "10"))
    pending_recovery_batch_size = int(os.getenv("CODEX_PENDING_RECOVERY_BATCH", "20"))
    next_pending_recovery_at = 0.0

    while True:
        if pending_recovery_enabled and time.monotonic() >= next_pending_recovery_at:
            recovered = await _drain_pending_for_channel(
                bus=bus,
                client=client,
                channel=channel,
                group=group,
                consumer=consumer,
                max_rounds=pending_recovery_max_rounds,
                batch_size=pending_recovery_batch_size,
            )
            if recovered > 0:
                logger.info(
                    "🗝️ pending_recovered channel=%s group=%s count=%d",
                    channel,
                    group,
                    recovered,
                )
            next_pending_recovery_at = time.monotonic() + pending_recovery_interval_sec

        events = await _read_new_events(
            bus=bus,
            channel=channel,
            group=group,
            consumer=consumer,
            count=10,
            block_ms=1000,
        )
        if not events:
            continue
        for event in events:
            await _process_event(bus=bus, client=client, event=event, group=group)


async def main() -> None:
    bus = StreamBus(host=os.getenv("REDIS_HOST", "core_redis"), port=int(os.getenv("REDIS_PORT", "6379")))
    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "codex_hunters"))
    consumer = os.getenv("CONSUMER_NAME", "codex_hunters:worker")

    channels = list(dict.fromkeys(CODEX_REQUEST_CHANNELS + _resolve_oculus_channels()))

    base_url = os.getenv("CODEX_API_URL", "http://codex_hunters:8008")
    logger.info(
        "🗝️ Starting Codex Hunters listener (Streams-only) api=%s group=%s streams=%d",
        base_url,
        group,
        len(channels),
    )
    logger.info("🗝️ listening_channels=%s", ",".join(channels))

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
