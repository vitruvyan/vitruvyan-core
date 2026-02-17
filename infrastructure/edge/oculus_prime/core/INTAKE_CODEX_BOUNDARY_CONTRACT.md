# INTAKE ↔ CODEX Boundary Contract

**Version**: 1.0.0  
**Date**: 2026-01-09  
**Status**: CANONICAL  
**Compliance**: ACCORDO-FONDATIVO-INTAKE-V1.1

---

## Purpose

This document defines the **immutable boundary** between the **Intake Layer** (pre-epistemic acquisition) and the **Codex Layer** (epistemic enrichment) in the AEGIS DSE-CPS Engine.

The boundary ensures:
- **Separation of concerns**: Intake acquires, Codex enriches
- **Event-driven decoupling**: No direct function calls between layers
- **Immutability enforcement**: Evidence Packs are append-only
- **Auditability**: All interactions via event log

---

## Epistemic Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│  INTAKE LAYER (Pre-Epistemic)                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Evidence Acquisition                                │    │
│  │  - Document/Image/Audio/Video/Stream Intake Agents   │    │
│  │  - Literal text extraction                           │    │
│  │  - NO semantic interpretation                        │    │
│  │  - Sampling Policy enforcement                       │    │
│  │  - Evidence Pack creation (immutable)                │    │
│  └──────────────────────────────────────────────────────┘    │
│                          │                                    │
│                          │ emit event                         │
│                          │ "oculus_prime.evidence.created"    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Redis Cognitive Bus                                 │    │
│  │  - Event routing                                     │    │
│  │  - Idempotency enforcement                           │    │
│  │  - Audit logging                                     │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                          │
                          │ consume event
                          │ (async, eventual consistency)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  CODEX LAYER (Epistemic Enrichment)                          │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Semantic Enrichment                                 │    │
│  │  - NER (Named Entity Recognition)                    │    │
│  │  - Relationship extraction                           │    │
│  │  - Embedding generation                              │    │
│  │  - Ontology mapping                                  │    │
│  │  - Concept linking                                   │    │
│  └──────────────────────────────────────────────────────┘    │
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Knowledge Base (Qdrant, PostgreSQL)                 │    │
│  │  - Enriched entities                                 │    │
│  │  - Vector embeddings                                 │    │
│  │  - Ontology graph                                    │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### INTAKE Layer (Pre-Epistemic)

**MUST DO**:
✅ Acquire raw evidence from sources (documents, images, audio, video, streams)  
✅ Normalize text to literal, descriptive format (NO interpretation)  
✅ Apply external Sampling Policy (frame rate, chunk size, etc.)  
✅ Create immutable Evidence Packs with integrity hashes  
✅ Emit canonical `oculus_prime.evidence.created` events to Redis Cognitive Bus  
✅ Log event emission success/failure to PostgreSQL audit trail  
✅ Support idempotency (detect duplicate evidence via source_hash)  

**MUST NOT DO**:
❌ Perform semantic interpretation (NER, entity extraction, sentiment)  
❌ Call Codex Layer functions directly  
❌ Modify Evidence Packs after creation (append-only)  
❌ Filter evidence by relevance (Sampling Policy decides)  
❌ Store embeddings in Qdrant (Codex responsibility)  
❌ Make epistemic judgments ("this is important", "this contradicts X")  

---

### CODEX Layer (Epistemic Enrichment)

**MUST DO**:
✅ Consume canonical `oculus_prime.evidence.created` events from Redis Cognitive Bus  
✅ Retrieve Evidence Packs from PostgreSQL (read-only)  
✅ Perform semantic enrichment (NER, embeddings, ontology mapping)  
✅ Store enriched entities in Knowledge Base (Qdrant + PostgreSQL)  
✅ Link evidence to existing concepts/entities  
✅ Emit downstream events (e.g., `codex.entity.created`)  

**MUST NOT DO**:
❌ Modify Evidence Packs (immutable by design)  
❌ Call Intake Agents directly  
❌ Bypass event bus for upstream communication  
❌ Perform raw evidence acquisition (Intake responsibility)  
❌ Override Sampling Policy decisions  

---

## Event Contract: `oculus_prime.evidence.created` (canonical)

**Event Schema**: `aegis://oculus_prime/events/evidence_created/v2.0`  
**Channel**: `oculus_prime.evidence.created` (Redis Streams)  
**Legacy Alias**: `intake.evidence.created` (migration window only)  
**Direction**: INTAKE → CODEX (one-way)

### Event Structure

```json
{
  "event_id": "EVT-12345678-1234-5678-1234-567812345678",
  "event_version": "2.0.0",
  "schema_ref": "aegis://oculus_prime/events/evidence_created/v2.0",
  "timestamp_utc": "2026-01-09T14:30:00Z",
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

### Event Processing Rules

**Idempotency**:
- `idempotency_key` = SHA-256(evidence_id + chunk_id + source_hash)
- Codex MUST check for duplicate idempotency keys before processing
- If duplicate detected, ignore event (already processed)

**Ordering**:
- Events are NOT guaranteed to arrive in order (eventual consistency)
- Codex MUST handle out-of-order chunks (use `chunk_id` to sequence)

**Retry Logic**:
- If Codex processing fails, emit `codex.enrichment.failed` event
- Intake Layer DOES NOT retry event emission (event log is append-only)
- Retry logic belongs to Codex Layer (exponential backoff)

**Error Handling**:
- Malformed events → log to `intake_event_failures` table
- Schema validation errors → reject event, log error
- Redis unavailability → retry emission with exponential backoff

---

## Data Flow Examples

### Example 1: Document Ingestion (PDF Report)

```
1. [INTAKE] User uploads Q4_2025.pdf
2. [INTAKE] DocumentIntakeAgent.ingest_document(path="/data/reports/Q4_2025.pdf")
3. [INTAKE] Extract text via pdfplumber → normalized_text = "Q4 2025 Financial Report..."
4. [INTAKE] Compute source_hash = sha256(file_bytes)
5. [INTAKE] Create Evidence Pack (evidence_id = EVD-12345678...)
6. [INTAKE] Persist to PostgreSQL evidence_packs table (append-only INSERT)
7. [INTAKE] Emit event to Redis: oculus_prime.evidence.created
8. [INTAKE] Log emission to intake_event_log table
9. [CODEX] Consume event from Redis channel
10. [CODEX] Retrieve Evidence Pack from PostgreSQL (SELECT by evidence_id)
11. [CODEX] Perform NER → extract entities: "Q4", "2025", "Financial Report"
12. [CODEX] Generate embedding via SentenceTransformer
13. [CODEX] Store enriched entity in Qdrant + PostgreSQL
14. [CODEX] Emit codex.entity.created event (downstream processing)
```

**Key Observation**: No direct function calls between INTAKE and CODEX. All communication via Redis events.

---

### Example 2: Real-Time Video Stream (Surveillance Feed)

```
1. [INTAKE] VideoStreamIntakeAgent.ingest_stream(url="rtsp://camera1", duration=60)
2. [INTAKE] Extract keyframes every 1 second (Sampling Policy: frame_interval_sec=1.0)
3. [INTAKE] Chunk frames into 10-second windows
4. [INTAKE] For each chunk:
   - Create Evidence Pack (evidence_id = EVD-chunk1...)
   - Emit oculus_prime.evidence.created event
5. [CODEX] Consume events (chunk-by-chunk, eventual consistency)
6. [CODEX] Perform object detection (not in Intake scope)
7. [CODEX] Store detected objects in Knowledge Base
8. [CODEX] Emit codex.anomaly.detected if threshold exceeded
```

**Key Observation**: INTAKE does NOT filter frames by relevance. Sampling Policy defines what to acquire. CODEX performs semantic filtering.

---

## Forbidden Interactions

### ❌ WRONG: Direct Function Call

```python
# INTAKE Layer (BAD EXAMPLE)
def ingest_document(source_path):
    text = extract_text(source_path)
    evidence_pack = create_evidence_pack(text)
    
    # ❌ FORBIDDEN: Direct call to Codex
    codex_enrichment_service.enrich(evidence_pack)  # WRONG!
```

**Why Wrong**: Tight coupling, violates event-driven architecture, bypasses audit trail.

---

### ✅ CORRECT: Event-Driven Decoupling

```python
# INTAKE Layer (CORRECT)
def ingest_document(source_path):
    text = extract_text(source_path)
    evidence_pack = create_evidence_pack(text)
    persist_evidence_pack(evidence_pack)
    
    # ✅ CORRECT: Emit event, let Codex consume
    event_emitter.emit_evidence_created(evidence_pack)
```

```python
# CODEX Layer (CORRECT)
def on_evidence_created_event(event):
    evidence_id = event['evidence_id']
    evidence_pack = retrieve_from_postgres(evidence_id)
    
    # ✅ CORRECT: Perform enrichment independently
    enriched = enrich_with_ner(evidence_pack)
    store_in_knowledge_base(enriched)
```

---

## Qdrant RBAC Enforcement

**Requirement**: Intake Agents have **read+index** permissions only on Qdrant.

**Rationale**: Intake does NOT store embeddings (Codex responsibility).

**Implementation**:
```python
# INTAKE Layer (Allowed)
qdrant_client.search(collection="documents", query_vector=[...], limit=10)  # ✅ READ

# INTAKE Layer (Forbidden)
qdrant_client.upsert(collection="documents", points=[...])  # ❌ WRITE (Codex only)
```

**Enforcement**: Use Qdrant API keys with scoped permissions:
- Intake API key: `read`, `index` (NO `upsert`, `delete`)
- Codex API key: `read`, `upsert`, `delete` (full access)

---

## Sampling Policy Contract

**Requirement**: Sampling Policy is **external, versioned, non-modifiable at runtime**.

**Storage**: 
- Policy definitions in Git repository (version-controlled)
- Policy references in Evidence Packs (e.g., `SAMPPOL-VIDEO-KEYFRAME-V1`)

**Example Policy**:
```yaml
# samppol_video_keyframe_v1.yaml
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

**Intake Behavior**:
- Load policy from Git at startup
- Apply policy during acquisition
- Reference policy ID in Evidence Pack
- NEVER modify policy at runtime

**Codex Behavior**:
- Read policy reference from Evidence Pack
- Use policy metadata for context (e.g., "this video was sampled at 1 fps")
- NEVER override policy decisions

---

## Immutability Guarantees

### Evidence Pack Immutability

**Enforced By**:
1. **PostgreSQL RBAC**: Application user has INSERT+SELECT only (NO UPDATE/DELETE)
2. **Integrity Hash**: `evidence_hash` computed over (evidence_id + chunk_id + normalized_text + source_hash)
3. **Audit Trail**: All modifications logged (if attempted, triggers alarm)

**Verification**:
```python
def verify_evidence_pack_integrity(evidence_pack):
    computed_hash = sha256(
        evidence_pack['evidence_id'] +
        evidence_pack['chunk_id'] +
        evidence_pack['normalized_text'] +
        evidence_pack['source_ref']['source_hash']
    )
    stored_hash = evidence_pack['integrity']['evidence_hash']
    
    if computed_hash != stored_hash:
        raise IntegrityError("Evidence Pack tampered!")
```

---

## Compliance Checklist

### INTAKE Layer Compliance

- [ ] Evidence Packs are append-only (INSERT only, NO UPDATE/DELETE)
- [ ] `normalized_text` is literal/descriptive (NO semantic interpretation)
- [ ] Sampling Policy is external, versioned, referenced (not embedded)
- [ ] Events have `schema_ref` = `aegis://oculus_prime/events/evidence_created/v2.0`
- [ ] Idempotency key prevents duplicate processing
- [ ] Event emission logged to `intake_event_log` (success) or `intake_event_failures` (failure)
- [ ] No direct calls to Codex Layer functions
- [ ] Qdrant access is read+index only (NO upsert/delete)

### CODEX Layer Compliance

- [ ] Consumes events from Redis Cognitive Bus (NO direct Intake calls)
- [ ] Reads Evidence Packs from PostgreSQL (read-only, NO modifications)
- [ ] Performs semantic enrichment (NER, embeddings, ontology mapping)
- [ ] Stores enriched data in Knowledge Base (Qdrant + PostgreSQL)
- [ ] Does NOT modify Evidence Packs (immutable by contract)
- [ ] Does NOT override Sampling Policy decisions
- [ ] Emits downstream events (e.g., `codex.entity.created`)

---

## Monitoring & Observability

### Key Metrics

**INTAKE Layer**:
- `intake_evidence_packs_created_total` (counter)
- `intake_events_emitted_total` (counter)
- `intake_events_failed_total` (counter)
- `intake_event_emission_duration_seconds` (histogram)

**CODEX Layer**:
- `codex_events_consumed_total` (counter)
- `codex_enrichment_duration_seconds` (histogram)
- `codex_enrichment_failures_total` (counter)
- `codex_entities_stored_total` (counter)

**Alerts**:
- `intake_event_emission_failure_rate > 5%` → trigger Synaptic Conclave
- `codex_enrichment_latency_p95 > 10s` → scale Codex workers
- `evidence_pack_integrity_violations > 0` → critical alarm (potential tampering)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-09 | Lead Orchestrator | Initial boundary contract |

---

## References

- [ACCORDO-FONDATIVO-INTAKE-V1.1](ACCORDO-FONDATIVO-INTAKE-V1.1.md)
- [Evidence Pack Schema v1.0](evidence_pack_schema_v1.json)
- [Event Schema: oculus_prime.evidence.created v2.0](event_evidence_created_v2.json)
- [Legacy Event Schema: intake.evidence.created v1.0](event_evidence_created_v1.json)
- [PostgreSQL Schema (append-only)](schema.sql)

---

**END OF BOUNDARY CONTRACT**
