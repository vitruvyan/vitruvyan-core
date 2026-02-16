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

# Import canonical event envelope
from ..events.event_envelope import CognitiveEvent, TransportEvent, EventAdapter

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
    events: List['CognitiveEvent'] = field(default_factory=list)
    confidence: float = 1.0
    reasoning: Optional[str] = None
    
    @classmethod
    def emit(cls, event: 'CognitiveEvent', confidence: float = 1.0) -> 'ProcessResult':
        return cls(action="emit", events=[event], confidence=confidence)
    
    @classmethod
    def emit_many(cls, events: List['CognitiveEvent'], confidence: float = 1.0) -> 'ProcessResult':
        return cls(action="emit", events=events, confidence=confidence)
    
    @classmethod
    def escalate(cls, reason: str, confidence: float = 0.0) -> 'ProcessResult':
        return cls(action="escalate", confidence=confidence, reasoning=reason)
    
    @classmethod
    def silence(cls) -> 'ProcessResult':
        return cls(action="silence")


# ============================================================================
# BACKWARD COMPATIBILITY (Removed - Use CognitiveEvent)
# ============================================================================
# StreamEvent class definition removed (Jan 24, 2026)
# Use CognitiveEvent from event_envelope.py instead
#
# Old StreamEvent is now split into:
# - TransportEvent (bus level) in event_envelope.py
# - CognitiveEvent (consumer level) in event_envelope.py
#
# This eliminates the ambiguity of having two incompatible StreamEvent classes.


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
        
        # Phase 6: Plasticity System (Jan 24, 2026)
        self.plasticity: Optional[Any] = None  # PlasticityManager (avoid circular import)
        self.outcome_tracker: Optional[Any] = None  # OutcomeTracker
        
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
    async def process(self, event: CognitiveEvent) -> ProcessResult:
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
    
    async def emit(self, event: CognitiveEvent) -> None:
        """
        Emit an event to the cognitive bus.
        
        The consumer sets:
        - source (automatically set to this consumer's name)
        - causation_id (if derived from another event)
        
        The bus handles:
        - Routing to subscribers (via Redis Streams)
        - Persistence (built-in to Redis Streams)
        - Delivery guarantees (at-least-once via consumer groups)
        
        NOTE: Herald deprecated and removed (Jan 24, 2026). Use StreamBus.
        """
        event.source = self.name
        
        if self._stream_bus:
            # TODO: Implement async publish in Phase 3
            # await self._stream_bus.publish(event)
            logger.warning(f"Consumer {self.name}: emit() not yet wired to StreamBus (Phase 3)")
        else:
            logger.error(f"Consumer {self.name}: No bus connection - cannot emit event")
        
        logger.debug(f"Consumer {self.name} emitted: {event.type}")
    
    async def escalate(self, event: CognitiveEvent, reason: str, confidence: float = 0.0) -> ProcessResult:
        """
        Escalate to governance (Orthodoxy Wardens).
        
        This is the "ask the brain" mechanism.
        Used when:
        - Confidence is below threshold
        - Ambiguity in input
        - Potential policy violation detected
        
        Returns a ProcessResult with escalation action.
        """
        escalation = CognitiveEvent(
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
        
        return ProcessResult.escalate(reason=reason, confidence=confidence)
    
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
        """
        Main consumption loop — reads from subscribed streams.
        
        PHASE 3 UPDATE (Jan 24, 2026):
        - Now uses real StreamBus.connect() and read_async()
        - Converts TransportEvent → CognitiveEvent via EventAdapter
        - Implements proper consumer group pattern
        """
        from ..transport.streams import StreamBus
        from ..events.event_envelope import EventAdapter
        
        bus = StreamBus()
        connected = await bus.connect()
        if not connected:
            logger.error(f"Consumer {self.name}: Failed to connect to bus")
            return
        
        self._stream_bus = bus
        
        # Create consumer group if specified
        group = self.config.consumer_group or f"cg_{self.name}"
        
        # Create consumer groups for all subscriptions
        for subscription in self.config.subscriptions:
            try:
                await asyncio.to_thread(bus.create_consumer_group, subscription, group)
            except Exception as e:
                logger.debug(f"Consumer group {group} already exists for {subscription}: {e}")
        
        logger.info(f"Consumer {self.name} starting consume loop (group={group})")
        
        while self._running:
            try:
                # Read events from all subscribed streams
                for subscription in self.config.subscriptions:
                    # Get TransportEvents from bus
                    transport_events = await bus.read_async(
                        stream_name=subscription,
                        group=group,
                        consumer=self.name,
                        count=10,
                        block_ms=1000
                    )
                    
                    # Convert to CognitiveEvents and process
                    for transport_event in transport_events:
                        cognitive_event = EventAdapter.transport_to_cognitive(transport_event)
                        await self._handle_event(cognitive_event)
                        
                        # ACK after successful handling
                        try:
                            await asyncio.to_thread(bus.ack, transport_event, group)
                        except Exception as e:
                            logger.warning(f"ACK failed for {transport_event.event_id}: {e}")
                        
            except asyncio.CancelledError:
                logger.info(f"Consumer {self.name} consume loop cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer {self.name} error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Backoff on error
    
    async def _handle_event(self, event: CognitiveEvent) -> None:
        """
        Handle a single event with timeout and result routing.
        
        Args:
            event: CognitiveEvent (already converted from TransportEvent)
        """
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
    
    async def _route_result(self, event: CognitiveEvent, result: ProcessResult) -> None:
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
    
    async def _handle_timeout(self, event: CognitiveEvent) -> None:
        """Handle processing timeout based on consumer type."""
        if self.consumer_type == ConsumerType.CRITICAL:
            # CRITICAL timeout is a system alert
            logger.error(f"CRITICAL consumer {self.name} TIMEOUT on {event.type}")
            await self._emit_alert(event, "timeout", "Critical consumer timed out")
        elif self.consumer_type == ConsumerType.ADVISORY:
            logger.warning(f"ADVISORY consumer {self.name} timeout on {event.type}")
        # AMBIENT timeout is normal
    
    async def _handle_error(self, event: CognitiveEvent, error: Exception) -> None:
        """Handle processing error."""
        logger.error(f"Consumer {self.name} error on {event.type}: {error}")
        
        if self.consumer_type == ConsumerType.CRITICAL:
            await self._emit_alert(event, "error", str(error))
    
    async def _emit_alert(self, event: CognitiveEvent, alert_type: str, message: str) -> None:
        """Emit system alert for critical failures."""
        alert = CognitiveEvent(
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
        status_dict = {
            "name": self.name,
            "type": self.consumer_type.value,
            "running": self._running,
            "subscriptions": self.config.subscriptions,
            "confidence_threshold": self.config.confidence_threshold,
            "timeout_ms": self.config.timeout_ms
        }
        
        # Add plasticity status if enabled
        if self.plasticity:
            status_dict["plasticity"] = self.plasticity.get_statistics()
        
        return status_dict
    
    # ─────────────────────────────────────────────────────────────
    # Phase 6: Plasticity System (Jan 24, 2026)
    # ─────────────────────────────────────────────────────────────
    
    def enable_plasticity(
        self,
        bounds: Dict[str, Any],  # Dict[str, ParameterBounds] - avoid import
        outcome_tracker: Any,  # OutcomeTracker - avoid circular import
        require_approval: bool = False
    ) -> None:
        """
        Enable plasticity with defined parameter bounds.
        
        Allows this consumer to adapt parameters based on outcomes.
        All adjustments are bounded, logged, and reversible.
        
        Args:
            bounds: Dict of parameter_name → ParameterBounds
            outcome_tracker: OutcomeTracker for learning feedback
            require_approval: If True, adjustments require governance approval
                             (recommended for CRITICAL consumers)
        
        Example:
            from vitruvyan_core.core.synaptic_conclave.plasticity import ParameterBounds, OutcomeTracker
            
            bounds = {
                "confidence_threshold": ParameterBounds(
                    name="confidence_threshold",
                    min_value=0.4,
                    max_value=0.9,
                    step_size=0.05,
                    default_value=0.6,
                    description="Minimum confidence for non-escalation"
                )
            }
            
            tracker = OutcomeTracker(postgres_agent)
            consumer.enable_plasticity(bounds, tracker, require_approval=False)
        """
        from vitruvyan_core.core.synaptic_conclave.plasticity.manager import PlasticityManager
        
        self.plasticity = PlasticityManager(
            consumer=self,
            bounds=bounds,
            outcome_tracker=outcome_tracker,
            require_approval=require_approval
        )
        self.outcome_tracker = outcome_tracker
        
        logger.info(
            f"✅ Plasticity enabled for {self.__class__.__name__} "
            f"({len(bounds)} adjustable parameters, approval={require_approval})"
        )
    
    async def record_outcome(self, outcome: Any) -> None:
        """
        Record outcome for learning (if tracker enabled).
        
        Links a decision (event) to its outcome for adaptive learning.
        
        Args:
            outcome: Outcome dataclass with decision details
        
        Example:
            from vitruvyan_core.core.synaptic_conclave.plasticity import Outcome
            
            outcome = Outcome(
                decision_event_id=event.id,
                outcome_type="escalation_resolved",
                outcome_value=1.0,  # 0.0-1.0 (success)
                consumer_name=self.name,
                parameter_name="confidence_threshold",
                parameter_value=self.confidence_threshold
            )
            
            await self.record_outcome(outcome)
        """
        if self.outcome_tracker:
            await self.outcome_tracker.record_outcome(outcome)
        else:
            logger.debug(
                f"No outcome tracker for {self.name}, outcome not recorded"
            )

    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name}, {self.consumer_type.value})>"
