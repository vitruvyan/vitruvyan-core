#!/usr/bin/env python3
"""
BaseConsumer — The Tentacle Pattern
====================================

Core abstraction for all Vitruvyan consumers.

Biological Model: Octopus arm
- Processes locally without central coordination
- Maintains own working memory (proprioception)
- Escalates to brain only when uncertain

Three consumer types:
1. CRITICAL - Must respond (even "non_liquet")
2. ADVISORY - Should respond, may timeout
3. AMBIENT  - May respond, no expectations (mycelium nodes)

Architectural Invariants Enforced:
- I2: Consumer Autonomy (process without waiting)
- I4: Epistemic Honesty (escalate when uncertain)
- I6: Graceful Degradation (failure isolated to this consumer)

Author: Vitruvyan Cognitive Architecture
Date: January 18, 2026
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConsumerType(Enum):
    """
    Consumer types inspired by biological response requirements.
    
    CRITICAL: Like octopus central brain neurons — must always respond.
              Used for: Orthodoxy Wardens, Sentinel Guardian
              
    ADVISORY: Like octopus arm ganglia — should respond, but system
              continues if timeout. Used for: Analysis consumers
              
    AMBIENT:  Like mycelium nodes — may respond, no expectations.
              Used for: Metrics, monitoring, logging
    """
    CRITICAL = "critical"
    ADVISORY = "advisory"
    AMBIENT = "ambient"


@dataclass
class ConsumerConfig:
    """Configuration for a consumer instance."""
    name: str
    consumer_type: ConsumerType
    subscriptions: List[str]  # Event types to subscribe to (supports wildcards)
    
    # Confidence threshold for escalation
    # Below this → escalate to Orthodoxy
    confidence_threshold: float = 0.6
    
    # Timeout in milliseconds
    # CRITICAL: timeout = error (system alert)
    # ADVISORY: timeout = skip this consumer
    # AMBIENT:  timeout = normal (no response expected)
    timeout_ms: int = 5000
    
    # Working memory TTL (seconds)
    memory_ttl: int = 3600
    
    # Optional consumer group for load balancing
    consumer_group: Optional[str] = None


@dataclass
class ProcessResult:
    """
    Result of processing an event.
    
    Every consumer must produce a result that can be:
    - emit: Produce new event(s)
    - escalate: Request governance intervention
    - silence: No output (valid for AMBIENT, error for CRITICAL)
    """
    action: str  # "emit", "escalate", "silence"
    events: List['StreamEvent'] = field(default_factory=list)
    confidence: float = 1.0
    reasoning: Optional[str] = None
    
    @classmethod
    def emit(cls, event: 'StreamEvent', confidence: float = 1.0) -> 'ProcessResult':
        return cls(action="emit", events=[event], confidence=confidence)
    
    @classmethod
    def emit_many(cls, events: List['StreamEvent'], confidence: float = 1.0) -> 'ProcessResult':
        return cls(action="emit", events=events, confidence=confidence)
    
    @classmethod
    def escalate(cls, reason: str, confidence: float = 0.0) -> 'ProcessResult':
        return cls(action="escalate", confidence=confidence, reasoning=reason)
    
    @classmethod
    def silence(cls) -> 'ProcessResult':
        return cls(action="silence")


@dataclass
class StreamEvent:
    """
    Event envelope for the cognitive bus.
    
    The bus validates envelope structure but NEVER inspects payload.
    This is architectural law (I1: Bus Humility).
    """
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # e.g., "analysis.complete", "escalation.request"
    
    # Causal chain (for temporal coherence & auditability)
    correlation_id: str = ""      # Groups related events (e.g., user session)
    causation_id: Optional[str] = None  # Immediate parent event
    trace_id: str = ""            # Root of entire causal tree
    
    # Temporal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Routing (declared by producer, not inferred by bus!)
    source: str = ""              # Which consumer emitted this
    targets: List[str] = field(default_factory=list)  # Suggested targets (hints only)
    
    # Payload (OPAQUE to bus — this is the actual content)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata (for observability, not routing)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def child(self, event_type: str, payload: Dict[str, Any], source: str) -> 'StreamEvent':
        """Create a child event in the causal chain."""
        return StreamEvent(
            type=event_type,
            correlation_id=self.correlation_id,
            causation_id=self.id,  # This event is the cause
            trace_id=self.trace_id or self.id,  # Preserve root
            source=source,
            payload=payload
        )


class BaseConsumer(ABC):
    """
    Abstract base class for all Vitruvyan consumers.
    
    The Tentacle Pattern:
    - Each consumer is autonomous (can process without coordination)
    - Each consumer has working memory (local state)
    - Each consumer can escalate (ask the brain)
    - Each consumer is typed (CRITICAL/ADVISORY/AMBIENT)
    
    Subclass and implement `process()` to create a consumer.
    """
    
    def __init__(self, config: ConsumerConfig):
        self.config = config
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Lazy-loaded dependencies
        self._working_memory = None
        self._stream_bus = None
        
        logger.info(
            f"Consumer initialized: {config.name} "
            f"[{config.consumer_type.value}] "
            f"subscriptions={config.subscriptions}"
        )
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def consumer_type(self) -> ConsumerType:
        return self.config.consumer_type
    
    # ─────────────────────────────────────────────────────────────
    # Abstract method — subclasses MUST implement
    # ─────────────────────────────────────────────────────────────
    
    @abstractmethod
    async def process(self, event: StreamEvent) -> ProcessResult:
        """
        Process an incoming event.
        
        This is the core cognitive function of the consumer.
        Implement domain-specific logic here.
        
        MUST return a ProcessResult:
        - ProcessResult.emit(event) — output to bus
        - ProcessResult.escalate(reason) — ask governance
        - ProcessResult.silence() — no output (AMBIENT only)
        
        For CRITICAL consumers:
        - MUST return emit or escalate (never silence)
        - Silence will trigger system alert
        
        For ADVISORY consumers:
        - Should return emit or escalate
        - Silence is allowed but logged
        
        For AMBIENT consumers:
        - All responses are valid
        - Silence is normal
        """
        pass
    
    # ─────────────────────────────────────────────────────────────
    # Lifecycle methods
    # ─────────────────────────────────────────────────────────────
    
    async def start(self) -> None:
        """Start consuming events from subscribed streams."""
        if self._running:
            logger.warning(f"Consumer {self.name} already running")
            return
        
        self._running = True
        logger.info(f"Consumer {self.name} starting...")
        
        # Initialize working memory
        from .working_memory import WorkingMemory
        self._working_memory = WorkingMemory(
            consumer_name=self.name,
            ttl_seconds=self.config.memory_ttl
        )
        await self._working_memory.connect()
        
        # Start consumption loop
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"Consumer {self.name} started")
    
    async def stop(self) -> None:
        """Gracefully stop the consumer."""
        if not self._running:
            return
        
        self._running = False
        logger.info(f"Consumer {self.name} stopping...")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._working_memory:
            await self._working_memory.close()
        
        logger.info(f"Consumer {self.name} stopped")
    
    # ─────────────────────────────────────────────────────────────
    # Communication methods
    # ─────────────────────────────────────────────────────────────
    
    async def emit(self, event: StreamEvent) -> None:
        """
        Emit an event to the cognitive bus.
        
        The consumer sets:
        - source (automatically set to this consumer's name)
        - causation_id (if derived from another event)
        
        The bus handles:
        - Routing to subscribers
        - Persistence (via Scribe)
        - Delivery guarantees
        """
        event.source = self.name
        
        if self._stream_bus:
            await self._stream_bus.publish(event)
        else:
            # Fallback: use Herald directly
            from ..herald import Herald
            herald = Herald()
            await herald.announce(
                event_type=event.type,
                payload=event.payload,
                correlation_id=event.correlation_id,
                metadata=event.metadata
            )
        
        logger.debug(f"Consumer {self.name} emitted: {event.type}")
    
    async def escalate(self, event: StreamEvent, reason: str, confidence: float = 0.0) -> StreamEvent:
        """
        Escalate to governance (Orthodoxy Wardens).
        
        This is the "ask the brain" mechanism.
        Used when:
        - Confidence is below threshold
        - Ambiguity in input
        - Potential policy violation detected
        
        Returns an escalation event that will be sent to Orthodoxy.
        """
        escalation = StreamEvent(
            type="escalation.request",
            correlation_id=event.correlation_id,
            causation_id=event.id,
            trace_id=event.trace_id,
            source=self.name,
            payload={
                "original_event": event.payload,
                "original_type": event.type,
                "reason": reason,
                "confidence": confidence,
                "consumer_type": self.config.consumer_type.value
            },
            metadata={
                "escalated_by": self.name,
                "escalation_time": datetime.utcnow().isoformat()
            }
        )
        
        await self.emit(escalation)
        logger.info(f"Consumer {self.name} escalated: {reason} (confidence={confidence})")
        
        return escalation
    
    # ─────────────────────────────────────────────────────────────
    # Working memory access
    # ─────────────────────────────────────────────────────────────
    
    async def remember(self, key: str, value: Any) -> None:
        """Store a value in working memory."""
        if self._working_memory:
            await self._working_memory.remember(key, value)
    
    async def recall(self, key: str) -> Optional[Any]:
        """Retrieve a value from working memory."""
        if self._working_memory:
            return await self._working_memory.recall(key)
        return None
    
    async def forget(self, key: str) -> None:
        """Remove a value from working memory."""
        if self._working_memory:
            await self._working_memory.forget(key)
    
    # ─────────────────────────────────────────────────────────────
    # Internal methods
    # ─────────────────────────────────────────────────────────────
    
    async def _consume_loop(self) -> None:
        """Main consumption loop — reads from subscribed streams."""
        from ..streams import StreamBus
        
        bus = StreamBus()
        await bus.connect()
        self._stream_bus = bus
        
        # Create consumer group if specified
        group = self.config.consumer_group or f"cg_{self.name}"
        
        while self._running:
            try:
                # Read events from all subscribed streams
                for subscription in self.config.subscriptions:
                    events = await bus.read(
                        stream_name=subscription,
                        group=group,
                        consumer=self.name,
                        count=10,
                        block_ms=1000
                    )
                    
                    for event_data in events:
                        await self._handle_event(event_data)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer {self.name} error: {e}")
                await asyncio.sleep(1)  # Backoff on error
    
    async def _handle_event(self, event_data: Dict[str, Any]) -> None:
        """Handle a single event with timeout and result routing."""
        # Parse event
        event = StreamEvent(
            id=event_data.get("id", str(uuid.uuid4())),
            type=event_data.get("type", "unknown"),
            correlation_id=event_data.get("correlation_id", ""),
            causation_id=event_data.get("causation_id"),
            trace_id=event_data.get("trace_id", ""),
            source=event_data.get("source", "unknown"),
            payload=event_data.get("payload", {}),
            metadata=event_data.get("metadata", {})
        )
        
        try:
            # Process with timeout
            result = await asyncio.wait_for(
                self.process(event),
                timeout=self.config.timeout_ms / 1000
            )
            
            # Handle result based on consumer type
            await self._route_result(event, result)
            
        except asyncio.TimeoutError:
            await self._handle_timeout(event)
        except Exception as e:
            await self._handle_error(event, e)
    
    async def _route_result(self, event: StreamEvent, result: ProcessResult) -> None:
        """Route the processing result appropriately."""
        if result.action == "emit":
            for output_event in result.events:
                await self.emit(output_event)
                
        elif result.action == "escalate":
            await self.escalate(event, result.reasoning or "unknown", result.confidence)
            
        elif result.action == "silence":
            if self.consumer_type == ConsumerType.CRITICAL:
                # CRITICAL consumers MUST respond — silence is an error
                logger.error(f"CRITICAL consumer {self.name} returned silence — escalating")
                await self.escalate(
                    event, 
                    f"Critical consumer {self.name} had no response",
                    confidence=0.0
                )
            elif self.consumer_type == ConsumerType.ADVISORY:
                logger.debug(f"ADVISORY consumer {self.name} silent on {event.type}")
            # AMBIENT silence is normal — no logging needed
    
    async def _handle_timeout(self, event: StreamEvent) -> None:
        """Handle processing timeout based on consumer type."""
        if self.consumer_type == ConsumerType.CRITICAL:
            # CRITICAL timeout is a system alert
            logger.error(f"CRITICAL consumer {self.name} TIMEOUT on {event.type}")
            await self._emit_alert(event, "timeout", "Critical consumer timed out")
        elif self.consumer_type == ConsumerType.ADVISORY:
            logger.warning(f"ADVISORY consumer {self.name} timeout on {event.type}")
        # AMBIENT timeout is normal
    
    async def _handle_error(self, event: StreamEvent, error: Exception) -> None:
        """Handle processing error."""
        logger.error(f"Consumer {self.name} error on {event.type}: {error}")
        
        if self.consumer_type == ConsumerType.CRITICAL:
            await self._emit_alert(event, "error", str(error))
    
    async def _emit_alert(self, event: StreamEvent, alert_type: str, message: str) -> None:
        """Emit system alert for critical failures."""
        alert = StreamEvent(
            type="system.alert",
            correlation_id=event.correlation_id,
            causation_id=event.id,
            trace_id=event.trace_id,
            source=self.name,
            payload={
                "alert_type": alert_type,
                "message": message,
                "consumer": self.name,
                "consumer_type": self.consumer_type.value,
                "original_event_type": event.type
            }
        )
        await self.emit(alert)
    
    # ─────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────
    
    def status(self) -> Dict[str, Any]:
        """Return current status of this consumer."""
        return {
            "name": self.name,
            "type": self.consumer_type.value,
            "running": self._running,
            "subscriptions": self.config.subscriptions,
            "confidence_threshold": self.config.confidence_threshold,
            "timeout_ms": self.config.timeout_ms
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name}, {self.consumer_type.value})>"
