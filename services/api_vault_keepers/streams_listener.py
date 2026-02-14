#!/usr/bin/env python3
"""
🔐 Vault Keepers — Streams Listener (No Pub/Sub)
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_vault_keepers')

from core.synaptic_conclave.transport.streams import StreamBus
from api_vault_keepers.adapters.bus_adapter import VaultBusAdapter
from api_vault_keepers.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("VaultKeepersStreamsListener")

def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


async def _handle_event(adapter: VaultBusAdapter, channel: str, payload: Dict[str, Any], correlation_id: str | None):
    if channel == "audit.vault.requested":
        adapter.ingest_external_audit(payload=payload, correlation_id=correlation_id)
        return

    if channel == "vault.archive.requested":
        content_type = payload.get("content_type") or payload.get("entity_type") or "generic"
        source_order = payload.get("source_order") or payload.get("source") or "unknown"
        adapter.handle_archive(content=payload, content_type=content_type, source_order=source_order, correlation_id=correlation_id)
        return

    if channel == "vault.restore.requested":
        snapshot_id = payload.get("snapshot_id") or payload.get("version_id") or payload.get("archive_id")
        if snapshot_id:
            adapter.handle_restore(snapshot_id=snapshot_id, dry_run=bool(payload.get("dry_run", True)), correlation_id=correlation_id)
        else:
            logger.warning("restore.requested missing snapshot_id/version_id/archive_id")
        return

    if channel == "vault.snapshot.requested":
        mode = payload.get("mode", "full")
        include_vectors = bool(payload.get("include_vectors", True))
        adapter.handle_backup(mode=mode, include_vectors=include_vectors, correlation_id=correlation_id)
        return

    # Cross-order archival (store results as archives)
    if channel in {"orthodoxy.audit.completed", "neural_engine.screening.completed"}:
        source_order = channel.split(".", 1)[0]
        adapter.handle_archive(content=payload, content_type=channel, source_order=source_order, correlation_id=correlation_id)
        return

    logger.info("Ignoring unhandled channel=%s", channel)


async def _consume_one_stream(bus: StreamBus, adapter: VaultBusAdapter, channel: str, group: str, consumer: str) -> None:
    bus.create_consumer_group(channel=channel, group=group, start_id="0")
    gen = bus.consume(channel=channel, group=group, consumer=consumer, count=10, block_ms=1000)

    while True:
        event = await asyncio.to_thread(next, gen, None)
        if event is None:
            continue

        observed_channel = _channel_from_stream(event.stream)
        payload_any: Any = event.payload
        payload: Dict[str, Any] = payload_any if isinstance(payload_any, dict) else {}
        correlation_id = getattr(event, "correlation_id", None) or payload.get("correlation_id")

        try:
            await _handle_event(adapter, observed_channel, payload, correlation_id)
            bus.ack(event, group=group)
        except Exception as exc:
            logger.error("Failed handling channel=%s event_id=%s: %s", observed_channel, event.event_id, exc, exc_info=True)
            # no ACK -> retry via PEL


async def main() -> None:
    logger.info("🔐 Starting Vault Keepers listener (Streams-only)")

    adapter = VaultBusAdapter()
    bus = adapter.bus

    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "vault_keepers"))
    consumer = os.getenv("CONSUMER_NAME", "vault_keepers:worker")
    channels = list(settings.SACRED_CHANNELS)

    logger.info("🔐 group=%s consumer=%s streams=%d", group, consumer, len(channels))
    await asyncio.gather(*[_consume_one_stream(bus, adapter, c, group, consumer) for c in channels])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🔐 Vault Keepers listener stopped by user")
    except Exception as e:
        logger.error(f"🔐 Vault Keepers listener error: {e}", exc_info=True)
        raise
