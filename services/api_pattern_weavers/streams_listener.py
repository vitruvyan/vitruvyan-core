#!/usr/bin/env python3
"""
Pattern Weavers — Streams Listener (No Pub/Sub)

Consumes weave requests from Redis Streams and emits completion/error events.
This is the bus bridge for the Pattern Weavers service.
"""

import asyncio
import logging
import os
import sys
import uuid
from typing import Any, Dict, Iterable, List

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/api_pattern_weavers")

from core.synaptic_conclave.transport.streams import StreamBus
from core.cognitive.pattern_weavers.domain import PatternConfig, set_config as set_domain_config
from api_pattern_weavers.api.routes import run_weave_pipeline
from api_pattern_weavers.models import WeaveRequest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("PatternWeaversStreamsListener")


REQUEST_CHANNELS_DEFAULT = (
    "pattern.weave.request,"
    "pattern_weavers.weave.request,"
    "pattern_weavers.weave_request"
)
RESPONSE_CHANNEL = "pattern_weavers.weave.completed"
CONTEXT_CHANNEL = "pattern_weavers.context.extracted"
ERROR_CHANNEL = "pattern_weavers.weave.error"


def _ensure_group_prefix(group: str) -> str:
    return group if group.startswith("group:") else f"group:{group}"


def _channel_from_stream(stream: str) -> str:
    return stream.replace("vitruvyan:", "", 1)


def _as_channels(raw: str) -> List[str]:
    channels: Iterable[str] = (item.strip() for item in raw.split(","))
    return [channel for channel in dict.fromkeys(channels) if channel]


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_payload(raw_payload: Any) -> Dict[str, Any]:
    if not isinstance(raw_payload, dict):
        return {}

    payload: Dict[str, Any] = dict(raw_payload)
    nested = payload.get("payload")
    if isinstance(nested, dict):
        payload = {**payload, **nested}

    return payload


def _build_weave_request(payload: Dict[str, Any]) -> WeaveRequest:
    query = payload.get("query") or payload.get("query_text") or payload.get("text")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("missing query/query_text/text in payload")

    context = payload.get("context")
    if not isinstance(context, dict):
        context = {}

    categories = payload.get("categories")
    if not isinstance(categories, list):
        categories = None

    return WeaveRequest(
        query=query.strip(),
        user_id=payload.get("user_id"),
        language=str(payload.get("language", "auto")),
        context=context,
        categories=categories,
        limit=_to_int(payload.get("limit", 10), 10),
        threshold=_to_float(payload.get("threshold", 0.4), 0.4),
    )


def _emit_success(
    bus: StreamBus,
    source_channel: str,
    request_id: str,
    correlation_id: str,
    request: WeaveRequest,
    result: Dict[str, Any],
) -> None:
    response_payload = dict(result)
    response_payload["request_id"] = request_id

    # Ensure matches are plain dicts (PatternMatch → dict)
    raw_matches = response_payload.get("matches", [])
    response_payload["matches"] = [
        m.model_dump() if hasattr(m, "model_dump") else (m.dict() if hasattr(m, "dict") else m)
        for m in raw_matches
    ]

    metadata = response_payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.update(
        {
            "source_stream": source_channel,
            "listener": "pattern_weavers",
        }
    )
    response_payload["metadata"] = metadata

    bus.emit(
        RESPONSE_CHANNEL,
        response_payload,
        emitter="pattern_weavers.listener",
        correlation_id=correlation_id,
    )

    concepts = metadata.get("extracted_concepts", [])
    if not isinstance(concepts, list):
        concepts = []

    bus.emit(
        CONTEXT_CHANNEL,
        {
            "request_id": request_id,
            "query": request.query,
            "concepts": concepts,
            "match_count": len(response_payload.get("matches", [])),
            "categories": request.categories or [],
            "processing_time_ms": response_payload.get("processing_time_ms", 0.0),
        },
        emitter="pattern_weavers.listener",
        correlation_id=correlation_id,
    )


def _emit_error(
    bus: StreamBus,
    source_channel: str,
    request_id: str,
    correlation_id: str,
    error: str,
) -> None:
    bus.emit(
        ERROR_CHANNEL,
        {
            "request_id": request_id,
            "source_stream": source_channel,
            "error": error,
        },
        emitter="pattern_weavers.listener",
        correlation_id=correlation_id,
    )


async def _consume_one_stream(bus: StreamBus, channel: str, group: str, consumer: str) -> None:
    start_id = os.getenv("PATTERN_LISTENER_START_ID", "0")
    bus.create_consumer_group(channel=channel, group=group, start_id=start_id)
    gen = bus.consume(channel=channel, group=group, consumer=consumer, count=10, block_ms=1000)

    while True:
        event = await asyncio.to_thread(next, gen, None)
        if event is None:
            continue

        source_channel = _channel_from_stream(event.stream)
        payload = _normalize_payload(event.payload)
        request_id = str(payload.get("request_id") or uuid.uuid4())
        correlation_id = str(payload.get("correlation_id") or request_id)

        try:
            request = _build_weave_request(payload)
            result = await asyncio.to_thread(run_weave_pipeline, request)
            _emit_success(
                bus=bus,
                source_channel=source_channel,
                request_id=request_id,
                correlation_id=correlation_id,
                request=request,
                result=result,
            )
            logger.info(
                "🕸️ processed=%s request_id=%s matches=%d",
                source_channel,
                request_id,
                len(result.get("matches", [])),
            )
        except Exception as exc:
            _emit_error(
                bus=bus,
                source_channel=source_channel,
                request_id=request_id,
                correlation_id=correlation_id,
                error=str(exc),
            )
            logger.error("🕸️ processing error stream=%s request_id=%s: %s", source_channel, request_id, exc)
        finally:
            bus.ack(event, group=group)


async def main() -> None:
    # Listener process has no FastAPI lifespan, so we bootstrap domain config here.
    set_domain_config(PatternConfig.from_env())

    bus = StreamBus(
        host=os.getenv("REDIS_HOST", "mercator_redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )

    raw_channels = os.getenv("PATTERN_LISTENER_CHANNELS", REQUEST_CHANNELS_DEFAULT)
    channels = _as_channels(raw_channels)
    group = _ensure_group_prefix(os.getenv("CONSUMER_GROUP", "pattern_weavers"))
    consumer = os.getenv("CONSUMER_NAME", "pattern_weavers:worker")

    logger.info("🕸️ Starting Pattern Weavers listener group=%s streams=%d", group, len(channels))
    await asyncio.gather(*[_consume_one_stream(bus, channel, group, consumer) for channel in channels])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🕸️ Pattern Weavers listener stopped by user")
    except Exception as exc:
        logger.error("🕸️ Pattern Weavers listener error: %s", exc, exc_info=True)
        raise
