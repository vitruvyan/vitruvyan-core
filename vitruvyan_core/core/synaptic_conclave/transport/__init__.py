"""Redis transport layer for Cognitive Bus"""
try:
    from .streams import StreamBus, get_stream_bus, emit, consume
except ImportError:  # redis / structlog not installed
    StreamBus = None  # type: ignore[assignment,misc]
    get_stream_bus = None  # type: ignore[assignment]
    emit = None  # type: ignore[assignment]
    consume = None  # type: ignore[assignment]

__all__ = ['StreamBus', 'get_stream_bus', 'emit', 'consume']