#!/usr/bin/env python3
"""
⚖️ Orthodoxy Wardens — Streams Listener (No Pub/Sub)
"""

import asyncio
import logging
import sys
import os
import json
from typing import Any, Dict

sys.path.insert(0, '/app/api_orthodoxy_wardens')
sys.path.insert(0, '/app')

from core.synaptic_conclave.transport.streams import StreamBus
from api_orthodoxy_wardens.adapters.bus_adapter import OrthodoxyBusAdapter
from api_orthodoxy_wardens.adapters.persistence import PersistenceAdapter
from api_orthodoxy_wardens.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("OrthodoxyWardensStreamsListener")

def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


def _build_orthodoxy_input(channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Domain-agnostic: treat payload as text for validation
    return {
        "trigger_type": channel,
        "source": payload.get("source") or payload.get("emitter") or "synaptic_conclave",
        "scope": payload.get("scope") or "event",
        "text": payload.get("text") or json.dumps(payload, ensure_ascii=False),
        "code": payload.get("code") or "",
    }


async def _consume_one_stream(
    bus: StreamBus,
    adapter: OrthodoxyBusAdapter,
    persistence: PersistenceAdapter,
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
        correlation_id = getattr(event, "correlation_id", None) or payload.get("correlation_id") or event.event_id

        try:
            orthodoxy_input = _build_orthodoxy_input(observed_channel, payload)

            if observed_channel == "orthodoxy.audit.requested":
                result = adapter.handle_event(orthodoxy_input)
                persistence.save_verdict(result)
                persistence.save_chronicle(result)
                bus.emit(
                    channel="orthodoxy.audit.completed",
                    payload={"correlation_id": correlation_id, "result": result},
                    emitter="orthodoxy_wardens.listener",
                    correlation_id=correlation_id,
                )

            else:
                # All other observed channels are validated via quick validation.
                result = adapter.handle_quick_validation(orthodoxy_input)
                persistence.save_verdict(result)
                bus.emit(
                    channel="orthodoxy.validation.completed",
                    payload={
                        "correlation_id": correlation_id,
                        "validated_channel": observed_channel,
                        "result": result,
                    },
                    emitter="orthodoxy_wardens.listener",
                    correlation_id=correlation_id,
                )

            bus.ack(event, group=group)

        except Exception as exc:
            logger.error("Failed orthodoxy handling channel=%s event_id=%s: %s", observed_channel, event.event_id, exc, exc_info=True)
            # no ACK


async def main() -> None:
    logger.info("⚖️ Starting Orthodoxy Wardens listener (Streams-only)")

    bus = StreamBus(host=os.getenv("REDIS_HOST", "core_redis"), port=int(os.getenv("REDIS_PORT", "6379")))
    adapter = OrthodoxyBusAdapter()
    persistence = PersistenceAdapter()

    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "orthodoxy_wardens"))
    consumer = os.getenv("CONSUMER_NAME", "orthodoxy_wardens:worker")
    channels = list(settings.SACRED_CHANNELS)

    logger.info("⚖️ group=%s consumer=%s streams=%d", group, consumer, len(channels))
    await asyncio.gather(*[_consume_one_stream(bus, adapter, persistence, c, group, consumer) for c in channels])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚖️ Orthodoxy Wardens listener stopped by user")
    except Exception as e:
        logger.error(f"⚖️ Orthodoxy Wardens listener error: {e}", exc_info=True)
        raise
