# Oculus Prime Flow Graph (Streams-Native)

> **Updated**: February 17, 2026  
> **Context**: Vitruvyan Core Oculus Prime refactor baseline  
> **Scope**: Pre-epistemic acquisition only (no semantic enrichment in Oculus Prime)

---

## Purpose

This document describes the canonical Oculus Prime flow after migration to Redis Streams.

Key constraints:
1. Oculus Prime is the single edge gateway for H2M/M2M ingestion.
2. Oculus Prime performs acquisition, normalization, and immutable persistence.
3. Oculus Prime emits `oculus_prime.evidence.created` via StreamBus (legacy alias supported).
4. Semantic enrichment starts downstream (Codex Hunters and beyond).

---

## End-to-End Flow

```mermaid
flowchart TD
    A[External Source<br/>H2M / M2M] --> B[Oculus Prime API<br/>upload + ingest endpoint]
    B --> C[Media Oculus Prime Agent<br/>document/image/audio/video/geo/cad]
    C --> D[Evidence Pack Builder<br/>literal normalized_text]
    D --> E[(PostgreSQL<br/>evidence_packs append-only)]
    D --> F[IntakeEventEmitter]
    F --> G[[Redis Streams<br/>vitruvyan:oculus_prime.evidence.created]]
    F --> H[(PostgreSQL<br/>intake_event_log / intake_event_failures)]

    G --> I[Codex Hunters Consumer Group]
    I --> J[Pattern Weavers]
    J --> K[Memory Orders]
    K --> L[Vault Keepers]
```

---

## Runtime Sequence

```mermaid
sequenceDiagram
    participant SRC as Source
    participant API as Oculus Prime API
    participant AG as Oculus Prime Agent
    participant PG as PostgreSQL
    participant EM as IntakeEventEmitter
    participant SB as StreamBus
    participant CX as Codex Hunters

    SRC->>API: POST /api/oculus-prime/{type} (file + metadata)
    API->>AG: ingest(file_path, source_type, metadata)
    AG->>AG: compute source_hash + literal extraction + chunking
    AG->>PG: INSERT evidence_packs (append-only)
    AG->>EM: emit_evidence_created(...)
    EM->>SB: emit("oculus_prime.evidence.created", event_payload)
    EM->>PG: INSERT intake_event_log
    SB-->>CX: consume via consumer group + ack
```

---

## Event Contract (Operational View)

Channel name:
- canonical: `oculus_prime.evidence.created` (stored as stream `vitruvyan:oculus_prime.evidence.created`)
- legacy alias: `intake.evidence.created` (optional for migration window)

Required event keys:
1. `event_id`
2. `event_version`
3. `schema_ref`
4. `timestamp_utc`
5. `evidence_id`
6. `chunk_id`
7. `idempotency_key`
8. `payload`

Idempotency:
- `idempotency_key = sha256(evidence_id + chunk_id + source_hash)`

---

## Responsibility Boundary

Oculus Prime MUST:
1. Create immutable Evidence Packs.
2. Emit stream events and audit logs.
3. Stay media-agnostic and domain-agnostic in acquisition behavior.

Oculus Prime MUST NOT:
1. Run NER, embeddings, ontology mapping.
2. Decide semantic relevance.
3. Call downstream cognitive services directly.
4. Read downstream cognitive tables (for example `cognitive_entities`).

---

## Control Plane Note (MCP)

MCP is not part of this data-plane flow.

Allowed MCP usage:
1. Device registration
2. Policy deployment
3. Link/buffer diagnostics

MCP is control-plane only; Oculus Prime evidence ingestion remains on dedicated edge data path.
