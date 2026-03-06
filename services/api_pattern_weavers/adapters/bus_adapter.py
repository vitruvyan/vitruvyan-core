"""
Bus Adapter for Pattern Weavers
===============================

Orchestrates LIVELLO 1 pure consumers with StreamBus I/O.
ALL Redis Streams operations are centralized here.
"""

import logging
from typing import Any, Dict, Optional

from ..config import get_config

logger = logging.getLogger(__name__)


class BusAdapter:
    """
    Orchestrates pure consumers with StreamBus.
    
    This adapter:
    1. Receives events from StreamBus
    2. Passes payloads to LIVELLO 1 consumers (pure processing)
    3. Emits results back to StreamBus
    
    LIVELLO 1 consumers never touch StreamBus directly.
    """
    
    def __init__(self):
        """Initialize with lazy StreamBus loading."""
        self._bus = None
        self._config = get_config()
        self._weaver_consumer = None
        self._keyword_consumer = None
    
    @property
    def bus(self):
        """Lazy-load StreamBus."""
        if self._bus is None:
            try:
                from core.synaptic_conclave.transport.streams import StreamBus
                self._bus = StreamBus()
                logger.info("✅ StreamBus initialized")
            except ImportError as e:
                logger.warning(f"⚠️ StreamBus not available: {e}")
        return self._bus
    
    @property
    def weaver_consumer(self):
        """Lazy-load WeaverConsumer."""
        if self._weaver_consumer is None:
            from core.cognitive.pattern_weavers.consumers import WeaverConsumer
            from core.cognitive.pattern_weavers.domain import get_config as get_domain_config
            self._weaver_consumer = WeaverConsumer(config=get_domain_config())
        return self._weaver_consumer
    
    @property
    def keyword_consumer(self):
        """Lazy-load KeywordMatcherConsumer."""
        if self._keyword_consumer is None:
            from core.cognitive.pattern_weavers.consumers import KeywordMatcherConsumer
            from core.cognitive.pattern_weavers.domain import get_config as get_domain_config
            self._keyword_consumer = KeywordMatcherConsumer(config=get_domain_config())
        return self._keyword_consumer
    
    def check_health(self) -> bool:
        """Check StreamBus connection health."""
        if not self.bus:
            return False
        try:
            return self.bus.ping()
        except Exception:
            return False


# Singleton
_bus_adapter: Optional[BusAdapter] = None


def get_bus_adapter() -> BusAdapter:
    """Get or create bus adapter singleton."""
    global _bus_adapter
    if _bus_adapter is None:
        _bus_adapter = BusAdapter()
    return _bus_adapter
