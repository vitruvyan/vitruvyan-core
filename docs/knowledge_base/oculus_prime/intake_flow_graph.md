# Oculus Prime Flow Graph (Streams-Native)

> **Updated**: February 17, 2026  
> **Context**: Vitruvyan Core Oculus Prime refactor baseline  
> **Scope**: Pre-epistemic acquisition only (no semantic enrichment in Oculus Prime)

## Purpose

This document describes the canonical Oculus Prime flow after migration to Redis Streams.

Key constraints:
1. Oculus Prime is the single edge gateway for H2M/M2M ingestion.
2. Oculus Prime performs acquisition, normalization, and immutable persistence.
3. Oculus Prime emits `oculus_prime.evidence.created` via StreamBus (legacy alias supported).
4. Semantic enrichment starts downstream (Codex Hunters and beyond).

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

## Responsibility Boundary

Oculus Prime MUST:
1. Create immutable Evidence Packs.
2. Emit stream events and audit logs.
3. Stay media-agnostic and domain-agnostic in acquisition behavior.

Oculus Prime MUST NOT:
1. Run NER, embeddings, ontology mapping.
2. Decide semantic relevance.
3. Call downstream cognitive services directly.
4. Read downstream cognitive tables.
