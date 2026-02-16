"""
AEGIS INTAKE — Event Bus Emission Contract

This module defines the emission contract for intake.evidence.created events.
MUST be used by all Intake Agents (Document, Image, Audio, Video, Stream).

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Events are idempotent (via idempotency_key)
- Events reference immutable Evidence Packs
- schema_ref enforces versioned validation
- No direct calls to Codex (event-driven only)
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class EvidenceCreatedEvent:
    """
    Event payload for intake.evidence.created
    
    Immutable event representing successful Evidence Pack creation.
    """
    
    event_id: str
    event_version: str = "1.0.0"
    schema_ref: str = "aegis://intake/events/evidence_created/v1.0"
    timestamp_utc: str = None
    evidence_id: str = None
    chunk_id: str = None
    idempotency_key: str = None
    payload: Dict[str, Any] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Auto-populate timestamp if not provided"""
        if self.timestamp_utc is None:
            self.timestamp_utc = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary (for serialization)"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class IntakeEventEmitter:
    """
    Event Bus emitter for Intake Layer
    
    Responsibilities:
    - Generate idempotency keys
    - Validate event schema compliance
    - Emit events to Redis Cognitive Bus
    - Log event emission for audit
    
    DOES NOT:
    - Call Codex directly
    - Modify Evidence Packs
    - Apply semantic interpretation
    """
    
    def __init__(self, redis_client=None, postgres_agent=None):
        """
        Args:
            redis_client: Redis connection for event emission
            postgres_agent: PostgresAgent for audit logging
        """
        self.redis_client = redis_client
        self.postgres_agent = postgres_agent
        self.channel = "intake.evidence.created"
    
    def generate_idempotency_key(self, evidence_id: str, chunk_id: str, source_hash: str) -> str:
        """
        Generate SHA-256 idempotency key for event deduplication
        
        Formula: sha256(evidence_id + chunk_id + source_hash)
        
        Args:
            evidence_id: Evidence Pack ID
            chunk_id: Chunk identifier
            source_hash: SHA-256 hash of source file
        
        Returns:
            64-char hex string
        """
        composite = f"{evidence_id}{chunk_id}{source_hash}"
        return hashlib.sha256(composite.encode('utf-8')).hexdigest()
    
    def emit_evidence_created(
        self,
        evidence_id: str,
        chunk_id: str,
        source_type: str,
        source_uri: str,
        evidence_pack_ref: str,
        source_hash: str,
        intake_agent_id: str,
        intake_agent_version: str,
        byte_size: int = None,
        language_detected: str = None,
        sampling_policy_ref: str = None,
        correlation_id: str = None
    ) -> EvidenceCreatedEvent:
        """
        Emit intake.evidence.created event to Redis Cognitive Bus
        
        This is the ONLY way Intake communicates with downstream layers (Codex).
        
        Args:
            evidence_id: Evidence Pack ID
            chunk_id: Chunk identifier
            source_type: Media type (document/image/audio/video/stream/sensor)
            source_uri: Original source location
            evidence_pack_ref: Reference to persisted Evidence Pack
            source_hash: SHA-256 of source file
            intake_agent_id: Identifier of emitting agent
            intake_agent_version: Version of emitting agent
            byte_size: Size in bytes (optional)
            language_detected: ISO 639-1 language code (optional)
            sampling_policy_ref: Sampling Policy reference (optional)
            correlation_id: Distributed tracing ID (optional)
        
        Returns:
            EvidenceCreatedEvent object
        
        Raises:
            ValueError: If required fields missing or invalid
        """
        # Validate source_type
        valid_types = ["document", "image", "audio", "video", "stream", "sensor"]
        if source_type not in valid_types:
            raise ValueError(f"Invalid source_type: {source_type}. Must be one of {valid_types}")
        
        # Generate event ID
        event_id = f"EVT-{uuid.uuid4().hex.upper()[:8]}-{uuid.uuid4().hex.upper()[8:12]}-{uuid.uuid4().hex.upper()[12:16]}-{uuid.uuid4().hex.upper()[16:20]}-{uuid.uuid4().hex.upper()[20:32]}"
        
        # Generate idempotency key
        idempotency_key = self.generate_idempotency_key(evidence_id, chunk_id, source_hash)
        
        # Build event
        event = EvidenceCreatedEvent(
            event_id=event_id,
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            idempotency_key=idempotency_key,
            payload={
                "source_type": source_type,
                "source_uri": source_uri,
                "evidence_pack_ref": evidence_pack_ref,
                "byte_size": byte_size,
                "language_detected": language_detected,
                "sampling_policy_ref": sampling_policy_ref
            },
            metadata={
                "intake_agent_id": intake_agent_id,
                "intake_agent_version": intake_agent_version,
                "correlation_id": correlation_id,
                "retry_count": 0
            }
        )
        
        # Emit to Redis (if connected)
        if self.redis_client:
            try:
                self.redis_client.publish(self.channel, event.to_json())
            except Exception as e:
                # Log error but don't fail (Evidence Pack already persisted)
                if self.postgres_agent:
                    self._log_emission_failure(event, str(e))
        
        # Audit log to PostgreSQL
        if self.postgres_agent:
            self._log_event_emission(event)
        
        return event
    
    def _log_event_emission(self, event: EvidenceCreatedEvent):
        """Log event emission to PostgreSQL for audit trail"""
        if not self.postgres_agent:
            return
        
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO intake_event_log (
                        event_id, event_version, schema_ref, timestamp_utc,
                        evidence_id, chunk_id, idempotency_key, payload, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    event.event_id,
                    event.event_version,
                    event.schema_ref,
                    event.timestamp_utc,
                    event.evidence_id,
                    event.chunk_id,
                    event.idempotency_key,
                    json.dumps(event.payload),
                    json.dumps(event.metadata)
                ))
            self.postgres_agent.connection.commit()
        except Exception as e:
            # Log error but don't fail
            print(f"[INTAKE] Failed to audit log event: {e}")
    
    def _log_emission_failure(self, event: EvidenceCreatedEvent, error: str):
        """Log event emission failure to PostgreSQL"""
        if not self.postgres_agent:
            return
        
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO intake_event_failures (
                        event_id, evidence_id, chunk_id, error, timestamp_utc
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    event.event_id,
                    event.evidence_id,
                    event.chunk_id,
                    error,
                    datetime.now(timezone.utc).isoformat()
                ))
            self.postgres_agent.connection.commit()
        except Exception as e:
            print(f"[INTAKE] Failed to log emission failure: {e}")


# Example usage (for reference, not executed)
if __name__ == "__main__":
    emitter = IntakeEventEmitter()
    
    # Emit event after Evidence Pack creation
    event = emitter.emit_evidence_created(
        evidence_id="EVD-12345678-1234-1234-1234-123456789ABC",
        chunk_id="CHK-0",
        source_type="document",
        source_uri="/data/intake/docs/report_2026.pdf",
        evidence_pack_ref="postgres://evidence_packs/12345",
        source_hash="sha256:abcd1234...",
        intake_agent_id="doc-intake-v1",
        intake_agent_version="1.0.0",
        byte_size=1024000,
        language_detected="en"
    )
    
    print(event.to_json())
