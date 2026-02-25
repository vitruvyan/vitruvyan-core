#!/usr/bin/env python3
"""
⚖️ Orthodoxy Wardens — Streams Listener (No Pub/Sub)
"""

import asyncio
import logging
import sys
import os
import json
from urllib.parse import urlparse
from typing import Any, Dict

sys.path.insert(0, '/app/api_orthodoxy_wardens')
sys.path.insert(0, '/app')

from core.synaptic_conclave.transport.streams import StreamBus
from api_orthodoxy_wardens.adapters.bus_adapter import OrthodoxyBusAdapter
from api_orthodoxy_wardens.adapters.finance_adapter import (
    get_finance_adapter,
    is_finance_enabled,
)
from api_orthodoxy_wardens.adapters.persistence import PersistenceAdapter
from api_orthodoxy_wardens.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("OrthodoxyWardensStreamsListener")

_VALID_TRIGGER_TYPES = {"code_commit", "scheduled", "manual", "output_validation", "event"}
_VALID_SCOPES = {"complete_realm", "single_service", "single_output", "single_event"}
_CHANNEL_TRIGGER_MAP = {
    "langgraph.response.completed": "output_validation",
}
_CHANNEL_SCOPE_MAP = {
    "langgraph.response.completed": "single_output",
}

def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


def _redis_endpoint() -> tuple[str, int]:
    """Resolve redis host/port from env and settings."""
    redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
    parsed = urlparse(redis_url)
    host = os.getenv("REDIS_HOST") or parsed.hostname or "mercator_redis"
    port = int(os.getenv("REDIS_PORT") or parsed.port or 6379)
    return host, port


def _build_orthodoxy_input(
    channel: str,
    payload: Dict[str, Any],
    finance_adapter: Any | None = None,
) -> Dict[str, Any]:
    """Build normalized input payload for orthodoxy audit pipeline."""
    text = payload.get("text") or json.dumps(payload, ensure_ascii=False)
    code = payload.get("code") or ""
    trigger_type = payload.get("trigger_type")
    if trigger_type not in _VALID_TRIGGER_TYPES:
        trigger_type = _CHANNEL_TRIGGER_MAP.get(channel, "event")

    scope = payload.get("scope")
    if scope not in _VALID_SCOPES:
        scope = _CHANNEL_SCOPE_MAP.get(channel, "single_event")

    source = payload.get("source") or payload.get("emitter") or "synaptic_conclave"

    if finance_adapter is not None:
        return finance_adapter.build_event(
            text=text,
            code=code,
            trigger_type=trigger_type,
            scope=scope,
            source=source,
        )

    return {
        "trigger_type": trigger_type,
        "source": source,
        "scope": scope,
        "text": text,
        "code": code,
    }


async def _consume_one_stream(
    bus: StreamBus,
    adapter: OrthodoxyBusAdapter,
    persistence: PersistenceAdapter,
    channel: str,
    group: str,
    consumer: str,
    finance_adapter: Any | None = None,
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
            orthodoxy_input = _build_orthodoxy_input(
                observed_channel,
                payload,
                finance_adapter=finance_adapter,
            )

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

    redis_host, redis_port = _redis_endpoint()
    bus = StreamBus(host=redis_host, port=redis_port)

    finance_adapter = get_finance_adapter() if is_finance_enabled() else None
    ruleset = finance_adapter.build_ruleset() if finance_adapter else None
    if finance_adapter:
        rules = finance_adapter.get_rules_stats()
        logger.info(
            "⚖️ Finance mode enabled ruleset=%s active_rules=%d",
            rules["ruleset_version"],
            rules["active_rules"],
        )

    adapter = OrthodoxyBusAdapter(ruleset=ruleset)
    persistence = PersistenceAdapter()

    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "orthodoxy_wardens"))
    consumer = os.getenv("CONSUMER_NAME", "orthodoxy_wardens:worker")
    channels = list(settings.SACRED_CHANNELS)

    logger.info("⚖️ group=%s consumer=%s streams=%d", group, consumer, len(channels))
    await asyncio.gather(
        *[
            _consume_one_stream(
                bus=bus,
                adapter=adapter,
                persistence=persistence,
                channel=c,
                group=group,
                consumer=consumer,
                finance_adapter=finance_adapter,
            )
            for c in channels
        ]
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚖️ Orthodoxy Wardens listener stopped by user")
    except Exception as e:
        logger.error(f"⚖️ Orthodoxy Wardens listener error: {e}", exc_info=True)
        raise
