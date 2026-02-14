# Vitruvyan Pipeline Walkthrough (Target + Runtime)

> This page intentionally shows both:
> 1) the **target architecture** (design intent), and  
> 2) the **current runtime snapshot** (what is active today).

> Snapshot date: **February 14, 2026**

---

## 1) Target Architecture (Design Intent)

Vitruvyan is designed around two intersecting paths:

- **Path A (async ingestion):** Codex Hunters → Babel Gardens → Vault Keepers
- **Path B (sync query):** LangGraph orchestration with Sacred Flow governance

### Path A — Target Flow (Async)

```mermaid
sequenceDiagram
    autonumber
    participant SRC as External Source
    participant TRK as Tracker (Codex Hunters)
    participant RST as Restorer (Codex Hunters)
    participant BND as Binder (Codex Hunters)
    participant PG as PostgreSQL (PostgresAgent)
    participant QD as Qdrant (QdrantAgent)
    participant BUS as Cognitive Bus (Redis Streams)
    participant BBL as Babel Gardens
    participant VLT as Vault Keepers

    TRK->>SRC: fetch raw data
    SRC-->>TRK: raw records
    TRK->>RST: pass raw records
    RST-->>BND: cleaned + normalized records
    BND->>PG: write structured data
    BND->>QD: write embeddings
    BND->>BUS: publish codex.discovery.mapped
    BUS->>BBL: consume codex.discovery.mapped
    BBL->>PG: write semantic/sentiment enrichment
    BBL->>QD: write semantic vectors
    BBL->>BUS: publish babel.sentiment.fused
    BUS->>VLT: consume enrichment event
    VLT->>PG: immutable archive entry
```

### Path B — Target Flow (Sync)

```mermaid
sequenceDiagram
    autonumber
    participant USR as User
    participant API as API Graph (/run)
    participant PRS as Parse
    participant INT as Intent Detection
    participant WVR as Pattern Weavers
    participant ENT as Entity Resolver
    participant EMO as Babel Emotion
    participant SEM as Semantic Grounding (VSGS)
    participant PRM as Params Extraction
    participant DEC as Decide
    participant EXE as Execution Node
    participant NRM as Output Normalizer
    participant ORT as Orthodoxy Wardens
    participant VLT as Vault Keepers
    participant CMP as Compose (VEE)
    participant CAN as CAN Node
    participant RESP as Final Response

    USR->>API: query
    API->>PRS: input_text
    PRS->>INT: parsed state
    INT->>WVR: intent + language + context
    WVR->>ENT: semantic context
    ENT->>EMO: resolved entities/context
    EMO->>SEM: emotional/context signals
    SEM->>PRM: grounded context
    PRM->>DEC: execution-ready state
    DEC->>EXE: route execution
    EXE->>NRM: raw output
    NRM->>ORT: normalized output
    ORT->>VLT: validated output
    VLT->>CMP: archived + validated output
    CMP->>CAN: narrative payload
    CAN->>RESP: user-facing answer
```

### Unified Block View — Target (High-Level)

```mermaid
graph TB
    subgraph A["Path A — Async Ingestion"]
        TRK[Tracker]
        RST[Restorer]
        BND[Binder]
        BBL[Babel Gardens]
        VLT_A[Vault Keepers]
        TRK --> RST --> BND --> BBL --> VLT_A
    end

    subgraph STORE["Shared Knowledge Layer"]
        PG[(PostgreSQL via PostgresAgent)]
        QD[(Qdrant via QdrantAgent)]
    end

    subgraph B["Path B — Sync Query"]
        API[API Graph /run]
        UND[Understanding Nodes]
        EXE[Execution Node]
        GOV[Sacred Flow]
        CMP[Compose + CAN]
        API --> UND --> EXE --> GOV --> CMP
    end

    BND --> PG
    BND --> QD
    BBL --> PG
    BBL --> QD
    VLT_A --> PG

    PG --> EXE
    QD --> UND
    QD --> EXE
```

---

## 2) Current Runtime Snapshot (as of 2026-02-14)

### Path A — Runtime Status

| Item | Status | Note |
|---|---|---|
| Codex stream listeners + dispatch | IMPLEMENTED | `codex.*.requested` consumed and dispatched |
| Tracker/Restorer/Binder domain consumers | IMPLEMENTED | Present in core |
| Full auto chain from listener to discover/restore/bind | PARTIAL | Listener path focuses on expedition dispatch |
| Babel listener on `codex.discovery.mapped` | IMPLEMENTED | Consume/ACK path present |
| Babel full enrich + dual-write triggered from stream | PARTIAL | Not fully guaranteed end-to-end in current listener wiring |
| Vault archive via dedicated channels | IMPLEMENTED | Vault listener active on configured sacred channels |

### Path B — Runtime Status

| Item | Status | Note |
|---|---|---|
| Parse → Intent → Weavers → Resolver → Emotion → Grounding → Params → Decide | IMPLEMENTED | Present in compiled graph |
| Execution node domain logic | PARTIAL | `exec_node` currently domain-neutral stub |
| Entity resolver full validation | PARTIAL | Current resolver is stub passthrough |
| Sacred Flow (`output_normalizer -> orthodoxy -> vault -> compose -> can`) | IMPLEMENTED | Wired and active |
| Proactive Suggestions node | REMOVED | Removed from active graph |

---

## 3) Interpretation Rule

Use this page as follows:

- **Target sections** = intended end-state architecture (kept explicit on purpose).
- **Runtime status tables** = operational truth for current deployment.

This keeps vision and implementation aligned without losing roadmap context.

---

## 4) Quick Verification Commands

```bash
# Path B check
curl -sS -X POST http://127.0.0.1:9004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"analyze european banks","user_id":"audit_user"}'

# Path A example event
docker exec core_redis redis-cli XADD vitruvyan:codex.discovery.mapped '*' payload '{"entity_id":"E_AUDIT_1"}'

# Logs
docker logs --since 2m core_graph
docker logs --since 2m core_babel_listener
docker logs --since 2m core_vault_listener
```
