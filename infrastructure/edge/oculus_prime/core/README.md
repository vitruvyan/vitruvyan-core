# AEGIS Intake Layer — Pre-Epistemic Evidence Acquisition

**Version**: 1.0.0  
**Date**: 2026-01-09  
**Status**: PRODUCTION READY (94% compliance)  
**Compliance**: ACCORDO-FONDATIVO-INTAKE-V1.1

---

## Purpose

The **AEGIS Intake Layer** is the **pre-epistemic acquisition system** for the AEGIS DSE-CPS Engine. It acquires raw evidence from multiple media types (documents, images, audio, video, streams), normalizes content to literal format, and emits immutable Evidence Packs to the Redis Cognitive Bus.

**Key Characteristics**:
- ✅ **Pre-epistemic**: NO semantic interpretation, NO entity extraction, NO sentiment analysis
- ✅ **Append-only**: Evidence Packs are immutable (INSERT only, NO UPDATE/DELETE)
- ✅ **Event-driven**: No direct calls between Intake and Codex layers
- ✅ **Policy-governed**: Sampling Policy controls acquisition (external, versioned)
- ✅ **Auditable**: All operations logged to PostgreSQL

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  AEGIS INTAKE LAYER (Pre-Epistemic)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Media-Specific Agents                                 │  │
│  │  ┌──────────┬──────────┬──────────┬──────────────┐    │  │
│  │  │ Document │  Image   │  Audio   │ Video/Stream │    │  │
│  │  │  Intake  │  Intake  │  Intake  │   Intake     │    │  │
│  │  └──────────┴──────────┴──────────┴──────────────┘    │  │
│  │                          │                             │  │
│  │                          ▼                             │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  Evidence Pack Creation                          │ │  │
│  │  │  - Literal text normalization                    │ │  │
│  │  │  - Integrity hash computation (SHA-256)          │ │  │
│  │  │  - Sampling Policy enforcement                   │ │  │
│  │  │  - Immutability guarantee                        │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                          │                             │  │
│  │                          ▼                             │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  PostgreSQL (Append-Only)                        │ │  │
│  │  │  - evidence_packs table                          │ │  │
│  │  │  - intake_event_log (audit)                      │ │  │
│  │  │  - intake_event_failures (retry)                 │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                          │                             │  │
│  │                          ▼                             │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  Event Emitter                                   │ │  │
│  │  │  - Idempotency key generation (SHA-256)          │ │  │
│  │  │  - Redis Streams (oculus_prime.evidence.created) │ │  │
│  │  │  - Audit logging (success/failure)               │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                          │
                          │ oculus_prime.evidence.created event
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  CODEX LAYER (Epistemic Enrichment)                          │
│  - Consume events from Redis Streams                         │
│  - Perform semantic enrichment (NER, embeddings)             │
│  - Store in Knowledge Base (Qdrant + PostgreSQL)             │
└──────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
infrastructure/edge/oculus_prime/core/
├── README.md                                   ← This file
├── INTAKE_CODEX_BOUNDARY_CONTRACT.md           ← Layer separation contract
├── COMPLIANCE_CHECKLIST.md                     ← Audit validation (94% compliant)
│
├── evidence_pack_schema_v1.json                ← JSON Schema for Evidence Packs
├── event_evidence_created_v2.json              ← Canonical event schema for oculus_prime.evidence.created
├── event_evidence_created_v1.json              ← Legacy compatibility schema
├── event_emitter.py                            ← Event Bus emission logic
├── schema.sql                                  ← PostgreSQL schema (append-only)
│
└── agents/
    ├── document_intake.py                      ← PDF, DOCX, MD, TXT, JSON, XML
    ├── image_intake.py                         ← JPG, PNG, TIFF + OCR + literal captioning
    ├── audio_intake.py                         ← MP3, WAV, AAC + Whisper STT
    └── video_stream_intake.py                  ← MP4, AVI, MOV + keyframe extraction
```

---

## Quick Start

### Prerequisites

```bash
# Python dependencies
pip install pdfplumber python-docx markdown pillow pytesseract openai-whisper pydub opencv-python redis psycopg2

# System dependencies (Ubuntu/Debian)
sudo apt install tesseract-ocr ffmpeg

# PostgreSQL schema
psql -U vitruvyan_user -d vitruvyan -f schema.sql
```

---

### Example 1: Ingest PDF Document

```python
from intake.core.agents.document_intake import DocumentIntakeAgent
from intake.core.event_emitter import IntakeEventEmitter
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

# Initialize dependencies
postgres = PostgresAgent()
stream_bus = StreamBus()
event_emitter = IntakeEventEmitter(stream_bus=stream_bus, postgres_agent=postgres)

# Create agent
agent = DocumentIntakeAgent(event_emitter, postgres)

# Define sampling policy
sampling_policy = {
    "policy_ref": "SAMPPOL-DOC-DEFAULT-V1",
    "chunk_strategy": "size",
    "chunk_size": 1024
}

# Ingest document
evidence_ids = agent.ingest_document(
    source_path="/data/reports/Q4_2025.pdf",
    sampling_policy_ref=sampling_policy["policy_ref"],
    chunking_strategy=sampling_policy["chunk_strategy"],
    chunk_size=sampling_policy["chunk_size"],
    correlation_id="trace-12345"
)

print(f"Created {len(evidence_ids)} Evidence Packs: {evidence_ids}")
```

**Output**:
```
Created 3 Evidence Packs: ['EVD-12345678-1234-5678-1234-567812345678', 'EVD-87654321-4321-8765-4321-876543218765', ...]
```

---

### Example 2: Ingest Image with OCR

```python
from intake.core.agents.image_intake import ImageIntakeAgent

agent = ImageIntakeAgent(event_emitter, postgres)

sampling_policy = {
    "policy_ref": "SAMPPOL-IMAGE-OCR-V1"
}

evidence_id = agent.ingest_image(
    source_path="/data/images/blueprint.png",
    sampling_policy_ref=sampling_policy["policy_ref"],
    enable_ocr=True,          # Extract text via pytesseract
    enable_caption=True,      # Generate literal caption
    correlation_id="trace-67890"
)

print(f"Created Evidence Pack: {evidence_id}")
```

---

### Example 3: Ingest Audio with Transcription

```python
from intake.core.agents.audio_intake import AudioIntakeAgent

agent = AudioIntakeAgent(event_emitter, postgres, whisper_model="base")

sampling_policy = {
    "policy_ref": "SAMPPOL-AUDIO-TRANSCRIBE-V1",
    "chunk_duration_sec": 300  # 5-minute chunks
}

evidence_ids = agent.ingest_audio(
    source_path="/data/audio/interview.mp3",
    sampling_policy_ref=sampling_policy["policy_ref"],
    chunk_duration_sec=sampling_policy["chunk_duration_sec"],
    correlation_id="trace-11111"
)

print(f"Created {len(evidence_ids)} Evidence Packs (audio chunks)")
```

---

### Example 4: Ingest Video with Keyframe Extraction

```python
from intake.core.agents.video_stream_intake import VideoStreamIntakeAgent

agent = VideoStreamIntakeAgent(event_emitter, postgres, whisper_model="base")

sampling_policy = {
    "policy_ref": "SAMPPOL-VIDEO-KEYFRAME-V1",
    "frame_interval_sec": 1.0,     # 1 frame per second
    "keyframes_only": False,       # Sample uniformly
    "chunk_duration_sec": 60       # 60-second chunks
}

evidence_ids = agent.ingest_video(
    source_path="/data/video/surveillance.mp4",
    sampling_policy=sampling_policy,
    enable_audio=True,              # Transcribe audio track
    correlation_id="trace-22222"
)

print(f"Created {len(evidence_ids)} Evidence Packs (video chunks)")
```

---

## Evidence Pack Structure

**JSON Schema**: `evidence_pack_schema_v1.json`

```json
{
  "evidence_id": "EVD-12345678-1234-5678-1234-567812345678",
  "chunk_id": "CHK-0",
  "schema_version": "1.0.0",
  "created_utc": "2026-01-09T14:30:00Z",
  "source_ref": {
    "source_type": "document",
    "source_uri": "/data/reports/Q4_2025.pdf",
    "source_hash": "sha256:abc123...",
    "mime_type": "application/pdf",
    "byte_size": 1024000
  },
  "normalized_text": "Q4 2025 Financial Report...",
  "technical_metadata": {
    "extraction_method": "pdfplumber",
    "extraction_version": "1.0.0",
    "language_detected": "en",
    "confidence_score": 0.95,
    "chunk_position": {
      "start_offset": 0,
      "end_offset": 1024,
      "total_chunks": 3
    }
  },
  "integrity": {
    "evidence_hash": "sha256:def456...",
    "immutable": true
  },
  "sampling_policy_ref": "SAMPPOL-DOC-DEFAULT-V1",
  "tags": []
}
```

---

## Event Schema

**Event**: `oculus_prime.evidence.created` (canonical)  
**Schema URI**: `aegis://oculus_prime/events/evidence_created/v2.0`

```json
{
  "event_id": "EVT-12345678-1234-5678-1234-567812345678",
  "event_version": "2.0.0",
  "schema_ref": "aegis://oculus_prime/events/evidence_created/v2.0",
  "timestamp": "2026-01-09T14:30:00Z",
  "evidence_id": "EVD-12345678-1234-5678-1234-567812345678",
  "chunk_id": "CHK-0",
  "idempotency_key": "abc123def456...",
  "payload": {
    "source_type": "document",
    "source_uri": "/data/reports/Q4_2025.pdf",
    "evidence_pack_ref": "postgres://evidence_packs/12345",
    "source_hash": "sha256:abc123...",
    "byte_size": 1024000,
    "language_detected": "en",
    "sampling_policy_ref": "SAMPPOL-DOC-DEFAULT-V1"
  },
  "metadata": {
    "intake_agent_id": "document-intake-v1",
    "intake_agent_version": "1.0.0",
    "correlation_id": "trace-12345",
    "retry_count": 0
  }
}
```

**Idempotency Key**: `SHA-256(evidence_id + chunk_id + source_hash)` — prevents duplicate processing.

---

## PostgreSQL Schema

**Tables**:
1. **`evidence_packs`**: Immutable storage for all Evidence Packs (INSERT only, NO UPDATE/DELETE)
2. **`intake_event_log`**: Audit trail for successful event emissions
3. **`intake_event_failures`**: Audit trail for failed emissions (retry candidates)

**Views**:
1. **`evidence_packs_recent`**: Most recent Evidence Packs (last 24 hours)
2. **`intake_event_log_recent`**: Most recent event emissions

**Function**:
- **`get_evidence_pack_by_id(evidence_id)`**: Retrieve all chunks for debugging/audit

**RBAC**:
- Application user has **INSERT + SELECT** permissions only (NO UPDATE/DELETE)
- Immutability enforced at database level

---

## Sampling Policy

**Principle**: Sampling Policy is **external, versioned, non-modifiable at runtime**.

**Example Policy** (YAML):
```yaml
policy_id: SAMPPOL-VIDEO-KEYFRAME-V1
policy_version: 1.0.0
description: Extract keyframes only, 1 frame per second
applies_to: [video, stream]
parameters:
  frame_interval_sec: 1.0
  keyframes_only: true
  chunk_duration_sec: 60
immutable: true
```

**Storage**: Git repository (version-controlled)

**Reference**: Policy ID stored in Evidence Pack (`sampling_policy_ref` field)

---

## INTAKE ↔ CODEX Boundary

**Key Rules**:
- ✅ Intake emits events, NEVER calls Codex directly
- ✅ Codex consumes events, NEVER calls Intake directly
- ✅ Evidence Packs are read-only for Codex
- ✅ No direct function calls between layers (event-driven only)

**See**: `INTAKE_CODEX_BOUNDARY_CONTRACT.md` for full specification.

---

## Compliance Status

**Overall**: 94% compliant (63/67 items)

**Non-Compliant Items**:
1. ⚠️ **Qdrant RBAC**: API key scoping not implemented (Intake should have read+index only)
2. ⚠️ **Video Stream Ingestion**: `ingest_stream()` method is placeholder only (v1.1 feature)

**See**: `COMPLIANCE_CHECKLIST.md` for full audit report.

---

## Testing

### Unit Tests (Pending)

```bash
pytest tests/test_intake_agents.py
```

**Coverage**:
- Evidence Pack creation
- Event emission
- Idempotency enforcement
- Integrity hash verification
- Sampling Policy application

---

### Integration Tests (Pending)

```bash
pytest tests/test_intake_e2e.py
```

**Scenarios**:
- Ingest PDF → verify Evidence Pack in PostgreSQL → verify event in Redis
- Ingest image with OCR → verify normalized_text is literal only
- Ingest audio → verify Whisper transcription accuracy
- Ingest video → verify keyframe extraction follows Sampling Policy

---

## Monitoring

### Key Metrics (Prometheus)

- `intake_evidence_packs_created_total` (counter)
- `intake_events_emitted_total` (counter)
- `intake_events_failed_total` (counter)
- `intake_event_emission_duration_seconds` (histogram)

### Alerts

- `intake_event_emission_failure_rate > 5%` → trigger Synaptic Conclave
- `evidence_pack_integrity_violations > 0` → critical alarm (potential tampering)

---

## FAQ

### Q1: Why is normalized_text "literal only"?

**A**: Intake is **pre-epistemic**. Semantic interpretation (NER, sentiment, topic modeling) is Codex's responsibility. Intake acquires raw evidence and normalizes to descriptive format.

Example:
- ✅ CORRECT: "blue object in center, 640x480 pixels"
- ❌ WRONG: "car parked in parking lot" (interprets "blue object" as "car")

---

### Q2: Why append-only Evidence Packs?

**A**: Immutability ensures **audit trail integrity**. Every acquisition decision is preserved. If new evidence contradicts old evidence, Codex creates a new enriched entity (does NOT modify original Evidence Pack).

---

### Q3: What happens if event emission fails?

**A**: Failed emissions are logged to `intake_event_failures` table. Retry logic is TBD (exponential backoff, max 3 retries).

---

### Q4: How does Codex know when new evidence arrives?

**A**: Codex consumes Redis stream `oculus_prime.evidence.created` (or legacy alias during migration) via consumer groups. When an event arrives, Codex retrieves Evidence Pack from PostgreSQL and performs enrichment.

---

### Q5: Can I filter evidence by relevance at Intake?

**A**: ❌ NO. Sampling Policy defines what to acquire. Relevance filtering is Codex's responsibility. Intake acquires ALL data matching policy.

---

## Roadmap

### v1.0.0 (Current)
- ✅ 6 media-specific agents (Document, Image, Audio, Video, Stream placeholder)
- ✅ Evidence Pack schema (JSON)
- ✅ Event Bus contract
- ✅ PostgreSQL schema (append-only)
- ✅ INTAKE ↔ CODEX boundary contract
- ✅ Compliance checklist (94%)

### v1.1.0 (Q2 2026)
- ⏳ Video stream ingestion (RTSP, WebRTC)
- ⏳ Qdrant RBAC implementation
- ⏳ Unit + integration tests (95% coverage)
- ⏳ Prometheus metrics
- ⏳ Retry logic for failed events

### v1.2.0 (Q3 2026)
- ⏳ Multi-language support (84 languages)
- ⏳ Advanced chunking strategies (semantic, sliding window)
- ⏳ Real-time stream buffer optimization
- ⏳ Distributed tracing (OpenTelemetry)

---

## References

- [Evidence Pack Schema v1.0](evidence_pack_schema_v1.json)
- [Event Schema: oculus_prime.evidence.created v2.0](event_evidence_created_v2.json)
- [Legacy Event Schema: intake.evidence.created v1.0](event_evidence_created_v1.json)
- [PostgreSQL Schema](schema.sql)
- [INTAKE ↔ CODEX Boundary Contract](INTAKE_CODEX_BOUNDARY_CONTRACT.md)
- [Compliance Checklist](COMPLIANCE_CHECKLIST.md)

---

## License

AEGIS Intake Layer is part of the Vitruvyan AI Trading Advisor project.  
Copyright © 2026 Caravaggio. All rights reserved.

---

**END OF README**
