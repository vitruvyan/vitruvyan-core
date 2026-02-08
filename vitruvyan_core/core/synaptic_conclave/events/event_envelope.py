#!/usr/bin/env python3
"""
Canonical Event Envelope — Single Source of Truth
==================================================

This module defines the ONLY event structures used in Vitruvyan Cognitive Bus.

ARCHITECTURAL DECISION (Jan 24, 2026):
- TWO event layers (transport vs cognitive)
- Explicit adapter between layers
- Eliminates ambiguity from 4 incompatible event models

Layer 1 (Transport): TransportEvent
- Redis Streams level
- Minimal, immutable
- Bus never inspects payload

Layer 2 (Cognitive): CognitiveEvent  
- Consumer level
- Adds causal chain (trace_id, causation_id)
- Adds metadata for reasoning

Author: Vitruvyan Core Team
Created: 2026-01-24
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field


# ============================================================================
# LAYER 1: TRANSPORT EVENT (Bus Level)
# ============================================================================

@dataclass(frozen=True)
class TransportEvent:
    """
    Immutable transport-level event for Redis Streams.
    
    This is what the bus sees. The bus does NOT interpret these fields —
    they are opaque containers for routing and persistence.
    
    Invariants:
    - Immutable (frozen=True)
    - No business logic
    - No semantic interpretation by bus
    
    Fields match Redis Streams XADD structure:
    - stream: Redis stream name (e.g., "vitruvyan:codex:entity_updated")
    - event_id: Redis-assigned ID (e.g., "1705123456789-0")
    - emitter: Source service identifier
    - payload: Opaque JSON data (bus doesn't look inside)
    - timestamp: ISO 8601 timestamp
    - correlation_id: Optional chain tracking
    """
    stream: str                    # Stream name (domain:intent)
    event_id: str                  # Redis-assigned ID
    emitter: str                   # Source service name
    payload: Dict[str, Any]        # Opaque data — bus NEVER inspects
    timestamp: str                 # ISO 8601
    correlation_id: Optional[str] = None  # Optional chain tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_redis_fields(self) -> Dict[str, str]:
        """
        Convert to Redis Streams field-value pairs.
        
        Used by StreamBus.emit() when writing to XADD.
        """
        fields = {
            'emitter': self.emitter,
            'payload': json.dumps(self.payload),
            'timestamp': self.timestamp,
        }
        if self.correlation_id:
            fields['correlation_id'] = self.correlation_id
        return fields
    
    @classmethod
    def from_redis(cls, stream: str, event_id: str, data: Dict[bytes, bytes]) -> 'TransportEvent':
        """
        Reconstruct event from Redis XREADGROUP response.
        
        Args:
            stream: Stream name from XREADGROUP
            event_id: Event ID from Redis
            data: Field-value dict from Redis (bytes → bytes)
        
        Returns:
            TransportEvent instance
        """
        # Decode bytes to strings
        decoded = {k.decode(): v.decode() for k, v in data.items()}
        
        # Parse JSON payload
        payload = json.loads(decoded.get('payload', '{}'))
        
        return cls(
            stream=stream,
            event_id=event_id,
            emitter=decoded.get('emitter', 'unknown'),
            payload=payload,
            timestamp=decoded.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            correlation_id=decoded.get('correlation_id')
        )


# ============================================================================
# LAYER 2: COGNITIVE EVENT (Consumer Level)
# ============================================================================

@dataclass
class CognitiveEvent:
    """
    Consumer-level event with causal chain and metadata.
    
    This is what consumers use for reasoning. It adds:
    - Causal chain (trace_id, causation_id)
    - Event type (for consumer routing)
    - Metadata (for observability)
    - Mutable (consumers can enrich)
    
    Consumers receive CognitiveEvent, process, and emit new CognitiveEvent.
    Adapter converts between CognitiveEvent ↔ TransportEvent at bus boundary.
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
    
    # Source (who emitted this)
    source: str = ""              # Which consumer emitted this
    
    # Payload (OPAQUE to bus — actual content)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata (for observability, not routing)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime to ISO string
        if isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat() + 'Z'
        return data
    
    def child(self, event_type: str, payload: Dict[str, Any], source: str) -> 'CognitiveEvent':
        """
        Create a child event in the causal chain.
        
        Preserves:
        - correlation_id (same session)
        - trace_id (same root cause)
        
        Sets:
        - causation_id = this event's ID (causal parent)
        - new ID for child
        """
        return CognitiveEvent(
            type=event_type,
            correlation_id=self.correlation_id,
            causation_id=self.id,  # This event is the cause
            trace_id=self.trace_id or self.id,  # Preserve root
            source=source,
            payload=payload,
            metadata={
                'parent_type': self.type,
                'parent_source': self.source
            }
        )


# ============================================================================
# LAYER ADAPTER (Bidirectional Conversion)
# ============================================================================

class EventAdapter:
    """
    Adapter between TransportEvent (bus) and CognitiveEvent (consumer).
    
    This is the ONLY place where conversion happens.
    """
    
    @staticmethod
    def transport_to_cognitive(transport: TransportEvent) -> CognitiveEvent:
        """
        Convert TransportEvent (from bus) to CognitiveEvent (for consumer).
        
        Mapping:
        - transport.stream → cognitive.type (convert "domain:intent" to "domain.intent")
        - transport.event_id → cognitive.id
        - transport.emitter → cognitive.source
        - transport.payload → cognitive.payload
        - transport.timestamp → cognitive.timestamp
        - transport.correlation_id → cognitive.correlation_id
        
        Adds:
        - trace_id = correlation_id (if not present in payload)
        - causation_id = None (unless in payload)
        """
        # Extract causal fields from payload (if present)
        trace_id = transport.payload.get('trace_id', transport.correlation_id or transport.event_id)
        causation_id = transport.payload.get('causation_id')
        
        # Convert stream name "domain:intent" → "domain.intent"
        event_type = transport.stream.replace('vitruvyan:', '').replace(':', '.')
        
        return CognitiveEvent(
            id=transport.event_id,
            type=event_type,
            correlation_id=transport.correlation_id or transport.event_id,
            causation_id=causation_id,
            trace_id=trace_id,
            timestamp=datetime.fromisoformat(transport.timestamp.replace('Z', '+00:00')),
            source=transport.emitter,
            payload=transport.payload,
            metadata={
                'transport_stream': transport.stream,
                'transport_event_id': transport.event_id
            }
        )
    
    @staticmethod
    def cognitive_to_transport(cognitive: CognitiveEvent, stream_prefix: str = "vitruvyan") -> TransportEvent:
        """
        Convert CognitiveEvent (from consumer) to TransportEvent (for bus).
        
        Mapping:
        - cognitive.type → transport.stream (convert "domain.intent" to "vitruvyan:domain:intent")
        - cognitive.id → transport.event_id (will be overwritten by Redis)
        - cognitive.source → transport.emitter
        - cognitive.payload → transport.payload (enriched with causal fields)
        - cognitive.timestamp → transport.timestamp
        - cognitive.correlation_id → transport.correlation_id
        
        Enriches payload with:
        - trace_id
        - causation_id (if present)
        """
        # Convert type "domain.intent" → stream "vitruvyan:domain:intent"
        stream_parts = cognitive.type.split('.')
        stream = f"{stream_prefix}:{':'.join(stream_parts)}"
        
        # Enrich payload with causal chain
        enriched_payload = cognitive.payload.copy()
        enriched_payload['trace_id'] = cognitive.trace_id
        if cognitive.causation_id:
            enriched_payload['causation_id'] = cognitive.causation_id
        
        # Generate event_id (will be replaced by Redis XADD)
        event_id = cognitive.id if cognitive.id else f"{int(datetime.utcnow().timestamp() * 1000)}-0"
        
        return TransportEvent(
            stream=stream,
            event_id=event_id,
            emitter=cognitive.source,
            payload=enriched_payload,
            timestamp=cognitive.timestamp.isoformat() + 'Z' if isinstance(cognitive.timestamp, datetime) else cognitive.timestamp,
            correlation_id=cognitive.correlation_id
        )


# ============================================================================
# LEGACY COMPATIBILITY (Temporary - Remove after Phase 5)
# ============================================================================

# Alias for backward compatibility during migration
StreamEvent = TransportEvent

__all__ = [
    'TransportEvent',
    'CognitiveEvent',
    'EventAdapter',
    'StreamEvent',  # Temporary alias
]
