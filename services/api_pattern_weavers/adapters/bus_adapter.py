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
    
    def setup_consumer_group(self, stream: str, group: str) -> bool:
        """
        Create consumer group for a stream.
        
        Args:
            stream: Stream name
            group: Consumer group name
            
        Returns:
            bool: Success status
        """
        if not self.bus:
            return False
        
        try:
            self.bus.create_consumer_group(stream, group)
            logger.info(f"✅ Consumer group '{group}' ready on '{stream}'")
            return True
        except Exception as e:
            logger.warning(f"Consumer group setup: {e}")
            return True  # Group may already exist
    
    def process_and_emit(
        self,
        input_event: Dict[str, Any],
        output_stream: str,
    ) -> bool:
        """
        Process event through pure consumers and emit result.
        
        Flow:
        1. Validate request (WeaverConsumer.validate_request)
        2. Get embedding (via caller - adapter doesn't do HTTP)
        3. Get similarity results (via caller - adapter doesn't do Qdrant)
        4. Process results (WeaverConsumer.process_results)
        5. Emit to output stream
        
        Args:
            input_event: Raw event payload
            output_stream: Stream to emit results
            
        Returns:
            bool: Success status
        """
        # Validate the request
        validation = self.weaver_consumer.process({
            "mode": "validate_request",
            "payload": input_event,
        })
        
        if not validation.success:
            logger.warning(f"Validation failed: {validation.errors}")
            return False
        
        # Emit validation success - actual processing happens async
        # Result will be emitted by the orchestrator after embedding + Qdrant
        return True
    
    def emit_weave_result(
        self,
        stream: str,
        result: Dict[str, Any],
    ) -> bool:
        """
        Emit weave result to stream.
        
        Args:
            stream: Target stream
            result: Weave result dict
            
        Returns:
            bool: Success status
        """
        if not self.bus:
            return False
        
        try:
            self.bus.emit(stream, result)
            return True
        except Exception as e:
            logger.error(f"Failed to emit result: {e}")
            return False
    
    def acknowledge(self, stream: str, group: str, event_id: str) -> bool:
        """
        Acknowledge event processing.
        
        Args:
            stream: Stream name
            group: Consumer group
            event_id: Event ID to acknowledge
            
        Returns:
            bool: Success status
        """
        if not self.bus:
            return False
        
        try:
            self.bus.acknowledge(stream, group, event_id)
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge: {e}")
            return False
    
    def check_health(self) -> bool:
        """Check StreamBus connection health."""
        if not self.bus:
            return False
        try:
            return self.bus.ping()
        except Exception:
            return False
    
    def publish_semantic_search_results(
        self,
        query_text: str,
        matches: list,
        query_id: str = "unknown",
        top_k: int = 10
    ) -> bool:
        """
        Publish semantic search results to memory.vector.match.fulfilled.
        
        CONTRACT COMPLIANCE:
        - Pre-calculates all domain metrics (avg_similarity, max, min)
        - Consumer (mnemosyne_node) extracts, never computes
        
        Args:
            query_text: Original query
            matches: List of match dicts with similarity_score
            query_id: Request correlation ID
            top_k: Number of results requested
            
        Returns:
            bool: Success status
        """
        if not self.bus:
            return False
        
        try:
            # ✅ Pre-calculate all metrics (producer responsibility)
            similarity_scores = [m.get("similarity_score", 0.0) for m in matches]
            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            max_similarity = max(similarity_scores) if similarity_scores else 0.0
            min_similarity = min(similarity_scores) if similarity_scores else 0.0
            match_count = len(matches)
            
            # ✅ Pre-sort matches by similarity (consumer preserves order)
            sorted_matches = sorted(matches, key=lambda m: m.get("similarity_score", 0), reverse=True)
            
            payload = {
                "query_id": query_id,
                "query_text": query_text,
                "matches": sorted_matches,
                "top_k": top_k,
                "metrics": {
                    "avg_similarity": round(avg_similarity, 3),
                    "max_similarity": round(max_similarity, 3),
                    "min_similarity": round(min_similarity, 3),
                    "match_count": match_count,
                    "threshold_met": avg_similarity >= 0.7,
                },
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }
            
            self.bus.emit("memory.vector.match.fulfilled", payload)
            logger.info(f"✅ Published semantic search results: {match_count} matches, avg_sim={avg_similarity:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish semantic search: {e}")
            return False


# Singleton
_bus_adapter: Optional[BusAdapter] = None


def get_bus_adapter() -> BusAdapter:
    """Get or create bus adapter singleton."""
    global _bus_adapter
    if _bus_adapter is None:
        _bus_adapter = BusAdapter()
    return _bus_adapter
