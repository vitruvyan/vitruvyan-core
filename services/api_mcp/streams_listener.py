#!/usr/bin/env python3
"""
MCP Server - Redis Streams Listener (No Pub/Sub)

Consumes MCP action requests from Redis Streams and emits a normalized
"mcp.tool.executed" observation event for downstream Sacred Orders components.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Iterable, List

sys.path.insert(0, "/app")

from core.synaptic_conclave.transport.streams import StreamBus


logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("MCPStreamsListener")


REQUEST_CHANNELS_DEFAULT = "conclave.mcp.actions"
TOOL_EXECUTED_CHANNEL = "mcp.tool.executed"
ERROR_CHANNEL = "mcp.listener.error"


def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


def _as_channels(raw: str) -> List[str]:
    channels: Iterable[str] = (item.strip() for item in raw.split(","))
    return [channel for channel in dict.fromkeys(channels) if channel]


def _normalize_payload(raw_payload: Any) -> Dict[str, Any]:
    if not isinstance(raw_payload, dict):
        return {}

    payload: Dict[str, Any] = dict(raw_payload)
    nested = payload.get("payload")
    if isinstance(nested, dict):
        payload = {**payload, **nested}

    return payload


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _emit_tool_executed(
    bus: StreamBus,
    payload: Dict[str, Any],
    source_channel: str,
    correlation_id: str,
) -> None:
    conclave_id = str(payload.get("conclave_id") or correlation_id)
    tool = str(payload.get("tool") or payload.get("action") or "unknown")
    args = payload.get("args")
    if not isinstance(args, dict):
        args = {}

    bus.emit(
        TOOL_EXECUTED_CHANNEL,
        {
            "conclave_id": conclave_id,
            "tool": tool,
            "args": args,
            "user_id": payload.get("user_id"),
            "status": str(payload.get("status") or payload.get("orthodoxy_status") or "observed"),
            "execution_time_ms": _to_float(payload.get("execution_time_ms"), 0.0),
            "source_stream": source_channel,
            "observed_at": datetime.utcnow().isoformat(),
        },
        emitter="mcp.listener",
        correlation_id=correlation_id,
    )


def _emit_error(
    bus: StreamBus,
    source_channel: str,
    correlation_id: str,
    error: str,
) -> None:
    bus.emit(
        ERROR_CHANNEL,
        {
            "source_stream": source_channel,
            "error": error,
            "observed_at": datetime.utcnow().isoformat(),
        },
        emitter="mcp.listener",
        correlation_id=correlation_id,
    )


async def _consume_one_stream(bus: StreamBus, channel: str, group: str, consumer: str) -> None:
    start_id = os.getenv("MCP_LISTENER_START_ID", "0")
    bus.create_consumer_group(channel=channel, group=group, start_id=start_id)
    gen = bus.consume(channel=channel, group=group, consumer=consumer, count=10, block_ms=1000)

    while True:
        event = await asyncio.to_thread(next, gen, None)
        if event is None:
            continue

        source_channel = _channel_from_stream(event.stream)
        payload = _normalize_payload(event.payload)
        correlation_id = (
            getattr(event, "correlation_id", None)
            or payload.get("correlation_id")
            or payload.get("conclave_id")
            or event.event_id
        )

        try:
            _emit_tool_executed(
                bus=bus,
                payload=payload,
                source_channel=source_channel,
                correlation_id=str(correlation_id),
            )
            logger.info(
                "processed=%s conclave_id=%s tool=%s",
                source_channel,
                payload.get("conclave_id"),
                payload.get("tool"),
            )
        except Exception as exc:
            _emit_error(
                bus=bus,
                source_channel=source_channel,
                correlation_id=str(correlation_id),
                error=str(exc),
            )
            logger.error(
                "processing error stream=%s event_id=%s: %s",
                source_channel,
                event.event_id,
                exc,
            )
        finally:
            bus.ack(event, group=group)


async def main() -> None:
    bus = StreamBus(
        host=os.getenv("REDIS_HOST", "mercator_redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )

    raw_channels = os.getenv("MCP_LISTENER_CHANNELS", REQUEST_CHANNELS_DEFAULT)
    channels = _as_channels(raw_channels)
    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "mcp_listeners"))
    consumer = os.getenv("CONSUMER_NAME", "mcp_listener:worker")

    logger.info("Starting MCP listener group=%s streams=%d", group, len(channels))
    await asyncio.gather(*[_consume_one_stream(bus, channel, group, consumer) for channel in channels])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP listener stopped by user")
    except Exception as exc:
        logger.error("MCP listener error: %s", exc, exc_info=True)
        raise
