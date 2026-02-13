"""Embedding API — Bus Adapter (StreamBus integration stub)."""

import logging
from core.synaptic_conclave.transport.streams import StreamBus

logger = logging.getLogger(__name__)


class EmbeddingBusAdapter:
    """Emit embedding events to Synaptic Conclave."""

    def __init__(self):
        try:
            self.bus = StreamBus()
            logger.info("StreamBus connected for Embedding service")
        except Exception as e:
            logger.warning(f"StreamBus not available: {e}")
            self.bus = None

    def emit_embedding_created(self, text_hash: str, dimension: int, collection: str):
        """Notify bus that an embedding was created."""
        if not self.bus:
            return
        self.bus.emit("embedding.created", {
            "text_hash": text_hash,
            "dimension": dimension,
            "collection": collection,
        })
