# Vitruvyan — Pipeline Walkthrough ("Il Giro del Fumo")

> **Audience**: Software engineer joining the project.  
> **Goal**: Understand exactly how data flows through Vitruvyan, end-to-end, step by step.

---

## Two Paths, One System

Vitruvyan has two concurrent data flows that run independently but feed each other:

| Path | Trigger | Nature | Purpose |
|------|---------|--------|---------|
| **Path A** — Data Ingestion | Scheduled / event-driven | Asynchronous (Cognitive Bus) | The system feeds itself — acquires, cleans, enriches, stores knowledge |
| **Path B** — User Query | User sends a message | Synchronous (LangGraph pipeline) | The system answers — uses accumulated knowledge to produce validated, explainable responses |

**The intersection**: Path B *reads* what Path A *wrote*. When a user asks a question, the answer comes from knowledge that the ingestion pipeline has been quietly accumulating in the background.

```mermaid
graph LR
    A["🔄 Path A<br/>Data Ingestion<br/><i>async, continuous</i>"]
    DB[("💾 PostgreSQL<br/>+ Qdrant")]
    B["💬 Path B<br/>User Query<br/><i>sync, on-demand</i>"]

    A -->|writes| DB
    DB -->|reads| B

    style A fill:#1a365d,stroke:#2b6cb0,color:#fff
    style B fill:#2f855a,stroke:#38a169,color:#fff
    style DB fill:#2d3748,stroke:#4a5568,color:#fff
```

---

## Path A — Data Ingestion (Asynchronous)

*"The system feeds itself."*

No user involved. Codex Hunters discover data, clean it, store it. Babel Gardens enriches it semantically. Vault Keepers archive the event. Everything communicates through the Cognitive Bus (Redis Streams).

```mermaid
sequenceDiagram
    autonumber
    participant SRC as 🌐 External Source<br/>(API, feed, scraper)
    participant TRK as 🔭 Tracker<br/>(Codex Hunters)
    participant RST as 🧹 Restorer<br/>(Codex Hunters)
    participant BND as 📦 Binder<br/>(Codex Hunters)
    participant PG as 💾 PostgreSQL<br/>(via PostgresAgent)
    participant QD as 🧠 Qdrant<br/>(via QdrantAgent)
    participant BUS as 🔴 Cognitive Bus<br/>(Redis Streams)
    participant BBL as 🌿 Babel Gardens
    participant VLT as 🏛️ Vault Keepers

    Note over SRC,VLT: PHASE 1 — Data Acquisition (Perception)
    
    TRK->>SRC: fetch raw data (rate-limited)
    SRC-->>TRK: raw records (text, numeric, metadata)
    
    TRK->>RST: pass raw records
    Note right of RST: • hash-based dedup<br/>• text cleaning (URLs, noise)<br/>• sentiment normalization<br/>• missing field imputation
    RST-->>RST: clean, deduplicated records

    RST->>BND: pass clean records
    Note right of BND: dual-write with embeddings
    BND->>PG: structured data (PostgresAgent)
    BND->>QD: vector embeddings (QdrantAgent)<br/>MiniLM-L6-v2, 384-dim

    Note over SRC,VLT: PHASE 2 — Semantic Enrichment (Discourse)

    BND->>BUS: publish "codex.discovery.mapped"
    BUS->>BBL: Babel listener consumes event
    
    Note right of BBL: HARVEST: extract raw text<br/>EXTRACT: run FinBERT (60%)<br/> + Gemma (40%)<br/>SYNTHESIZE: fuse vectors<br/> (4 strategies available)<br/>PLANT: store in seedbank
    
    BBL->>PG: save fused sentiment (PostgresAgent)
    BBL->>QD: save semantic vectors (QdrantAgent)
    BBL->>BUS: publish "babel.sentiment.fused"

    Note over SRC,VLT: PHASE 3 — Archival (Truth)

    BUS->>VLT: Vault listener consumes event
    VLT->>PG: immutable archive entry
```

### What happens at each step:

| # | Who | What enters | What happens | What exits |
|---|-----|-------------|--------------|------------|
| 1 | **Tracker** | Nothing (scheduled or event-triggered) | Fetches from external sources with rate limiting | Raw records (text, numbers, metadata, timestamps) |
| 2-3 | **Restorer** | Raw records | Dedup by content hash, strips URLs/noise, normalizes sentiment scores (tanh clipping), fills missing fields | Clean, unique records |
| 4-5 | **Binder** | Clean records | Generates 384-dim embeddings (MiniLM-L6-v2), writes to PostgreSQL (structured) AND Qdrant (vectors) | Persisted knowledge with dual index |
| 6-7 | **Babel Gardens** | Bus event with record reference | Runs sentiment models (FinBERT 60% + Gemma 40%), applies linguistic fusion, synthesizes unified representation | Fused sentiment + semantic vectors in seedbank |
| 8 | **Vault Keepers** | Bus event chain | Archives immutably | Audit trail with causal chain |

### Resilience pattern
If Babel Gardens fails during enrichment, it **still publishes** `babel.sentiment.fused` with `score=None`. Downstream consumers handle the absence — the pipeline never blocks.

---

## Path B — User Query (Synchronous)

*"The system answers."*

A user sends a message. LangGraph orchestrates 23 nodes in sequence. Each node reads from or writes to the shared `state` dict (~80 typed fields). The final response is validated, archived, and explainable.

```mermaid
sequenceDiagram
    autonumber
    participant USR as 👤 User
    participant API as 🎯 API Gateway<br/>(api_graph :8004)
    participant PRS as 📝 Parse
    participant INT as 🧭 Intent Detection
    participant WVR as 🕸️ Pattern Weavers
    participant ENT as 🔍 Entity Resolver
    participant EMO as 💭 Babel Emotion
    participant SEM as 🔗 Semantic Grounding<br/>(VSGS)
    participant PRM as 📐 Params Extraction
    participant DEC as ⚡ Decide
    participant EXE as ⚙️ Execution Node<br/>(domain-specific)
    participant NRM as 📊 Output Normalizer
    participant ORT as 🛡️ Orthodoxy Wardens
    participant VLT as 🏛️ Vault Keepers
    participant CMP as 📖 Compose (VEE)
    participant CAN as 💬 CAN Node
    participant PRO as 💡 Proactive Suggestions
    participant PG as 💾 PostgreSQL
    participant QD as 🧠 Qdrant

    USR->>API: "analyze European banks"
    API->>PRS: raw input text

    Note over PRS,PRM: STAGE 1 — Understanding (7 nodes)

    PRS->>INT: structured tokens
    Note right of INT: LLM classifies intent<br/>+ detects language<br/>(parallel with Babel)
    
    INT->>WVR: intent + language + text
    Note right of WVR: vector search on Qdrant<br/>→ {concepts: ["Banking"],<br/>  regions: ["Europe"],<br/>  countries: [IT,FR,DE...]}
    WVR->>QD: search "weave_embeddings"
    QD-->>WVR: matching patterns
    
    WVR->>ENT: enriched context
    Note right of ENT: resolves abstract concepts<br/>to concrete entities<br/>(in Mercator: tickers)
    ENT->>PG: validate entities exist
    PG-->>ENT: confirmed entities
    
    ENT->>EMO: validated entities + context
    Note right of EMO: detects user emotional state<br/>(confident / uncertain /<br/>frustrated / excited)
    
    EMO->>SEM: state + emotion
    Note right of SEM: VSGS retrieves prior<br/>conversations from Qdrant<br/>→ multi-turn coherence
    SEM->>QD: search conversation history
    QD-->>SEM: semantic matches
    
    SEM->>PRM: full context
    Note right of PRM: extracts parameters<br/>(timeframe, budget,<br/>risk tolerance)

    Note over DEC,EXE: STAGE 2 — Execution (domain-specific)

    PRM->>DEC: complete understanding
    Note right of DEC: conditional routing:<br/>analysis → execution<br/>conversation → CAN<br/>codex → hunters<br/>sentinel → monitoring
    
    DEC->>EXE: route to appropriate executor
    Note right of EXE: domain logic runs here<br/>(Neural Engine in Mercator)<br/>reads from PostgreSQL + Qdrant<br/>← this is where Path A<br/>  and Path B meet
    EXE->>PG: read accumulated knowledge
    PG-->>EXE: stored data
    EXE->>QD: read semantic vectors
    QD-->>EXE: embeddings + similarities

    Note over NRM,VLT: STAGE 3 — Sacred Flow (governance)

    EXE->>NRM: raw execution results
    Note right of NRM: uniform format,<br/>fill missing fields
    
    NRM->>ORT: normalized output
    Note right of ORT: epistemic validation<br/>→ blessed ✅<br/>→ purified ⚠️ (fixed)<br/>→ heretical ❌ (rejected)
    
    ORT->>VLT: validated output
    Note right of VLT: immutable archive<br/>with causal chain

    Note over CMP,PRO: STAGE 4 — Response Generation (discourse)

    VLT->>CMP: archived + validated output
    Note right of CMP: VEE generates 3 levels:<br/>1. Summary (plain language)<br/>2. Detailed (operational)<br/>3. Technical (raw scores)<br/>+ VWRE attribution analysis
    
    CMP->>CAN: structured narrative
    Note right of CAN: LLM generates natural<br/>conversational response<br/>+ anti-hallucination<br/>  validation (MCP)
    
    CAN->>PRO: response ready
    Note right of PRO: injects unsolicited insights<br/>(earnings warnings,<br/>concentration alerts,<br/>pattern detections)

    PRO->>API: final response
    API->>USR: validated, archived, explainable answer
```

### What happens at each stage:

#### Stage 1 — Understanding (7 nodes)
The system builds a complete picture of *what the user wants*.

| Node | Input | Processing | Output |
|------|-------|------------|--------|
| **Parse** | Raw text | Tokenizes, extracts structure | Parsed tokens |
| **Intent Detection** | Tokens | LLM classifies intent (analysis, conversation, risk...) + language detection | `intent`, `language`, `confidence` |
| **Pattern Weavers** | Intent + text | Vector search → maps vague concepts to structured context | `weaver_context: {concepts, regions, sectors, risk_profile}` |
| **Entity Resolver** | Enriched context | Resolves abstract → concrete (validates existence in PostgreSQL) | `validated_entities[]` |
| **Babel Emotion** | Full state | Detects user emotional state | `emotion: "confident" / "uncertain" / "frustrated"` |
| **Semantic Grounding** | State + emotion | VSGS searches conversation history in Qdrant | `semantic_matches[]` (prior context) |
| **Params Extraction** | Full context | Extracts operational parameters | `horizon`, `budget`, `risk_tolerance` |

#### Stage 2 — Execution (1 node, domain-specific)
**This is where the vertical lives.** In Mercator, this is where the Neural Engine evaluates entities across multiple factors, normalizes cross-entity, and aggregates into composite scores. In a different vertical, this could be anything.

**This is also where Path A meets Path B**: the execution node reads knowledge that the ingestion pipeline accumulated asynchronously.

#### Stage 3 — Sacred Flow (3 nodes, governance)
Every output passes through governance before reaching the user. This is non-negotiable.

| Node | Role | Verdicts |
|------|------|----------|
| **Output Normalizer** | Uniform format, fill gaps | (passthrough) |
| **Orthodoxy Wardens** | Epistemic validation | `blessed` ✅ / `purified` ⚠️ / `heretical` ❌ |
| **Vault Keepers** | Immutable archival with causal chain | (passthrough, side-effect: archive) |

#### Stage 4 — Response Generation (3 nodes, discourse)

| Node | Role | Output |
|------|------|--------|
| **Compose (VEE)** | 3-level explainability engine | `summary` + `detailed` + `technical` narratives |
| **CAN** | Conversational response with anti-hallucination | Natural language answer |
| **Proactive Suggestions** | Inject unsolicited insights | Warnings, alerts, recommendations |

---

## Where the Two Paths Meet

```mermaid
graph TB
    subgraph PATH_A["🔄 Path A — Ingestion (async)"]
        direction LR
        T[Tracker] --> R[Restorer] --> B[Binder] --> BG[Babel Gardens]
    end

    subgraph STORE["💾 Shared Knowledge"]
        PG[(PostgreSQL)]
        QD[(Qdrant)]
    end

    subgraph PATH_B["💬 Path B — Query (sync)"]
        direction LR
        U[User] --> UND[Understanding<br/>7 nodes] --> EXE[Execution] --> GOV[Sacred Flow<br/>3 nodes] --> RESP[Response<br/>3 nodes] --> OUT[Answer]
    end

    B -->|"write (PostgresAgent)"| PG
    B -->|"write (QdrantAgent)"| QD
    BG -->|"write (PostgresAgent)"| PG
    BG -->|"write (QdrantAgent)"| QD

    PG -->|"read (PostgresAgent)"| EXE
    QD -->|"read (QdrantAgent)"| EXE
    QD -->|"read (VSGS)"| UND

    style PATH_A fill:#1a365d,stroke:#2b6cb0,color:#fff
    style PATH_B fill:#2f855a,stroke:#38a169,color:#fff
    style STORE fill:#2d3748,stroke:#4a5568,color:#fff
```

**Key insight**: Path A and Path B never call each other. They share state exclusively through the canonical data stores (PostgreSQL and Qdrant), accessed only through `PostgresAgent` and `QdrantAgent`. This is what makes the two paths independently scalable and testable.

---

## Communication Channels Summary

| Between | Channel | Example |
|---------|---------|---------|
| Codex → Babel → Vault (Path A) | **Redis Streams** (async events) | `codex.discovery.mapped` → Babel consumes |
| LangGraph nodes (Path B) | **State dict** (in-process) | `state["weaver_context"]` flows node to node |
| LangGraph → external services | **REST API** (httpx) | LangGraph calls Neural Engine at `:8003` |
| Both paths → storage | **Canonical agents** (PostgresAgent, QdrantAgent) | Never direct connections |

---

## The Complete Picture

```
                    ┌─────────────────────────────────────────────┐
                    │              COGNITIVE BUS                   │
                    │         (Redis Streams, async)               │
                    │                                             │
                    │  codex.discovery.mapped ──────────────►     │
                    │  babel.sentiment.fused  ──────────────►     │
                    │  vault.archive.stored   ──────────────►     │
                    └────┬──────────┬──────────┬──────────────────┘
                         │          │          │
            ┌────────────┘     ┌────┘     ┌────┘
            ▼                  ▼          ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Codex Hunters│  │Babel Gardens │  │ Vault Keepers│
    │  (Perception)│  │  (Discourse) │  │   (Truth)    │
    └──────┬───────┘  └──────┬───────┘  └──────────────┘
           │                 │
           │    WRITE        │    WRITE
           ▼                 ▼
    ┌─────────────────────────────────┐
    │     PostgreSQL    +    Qdrant   │◄──── Canonical Access Only
    │  (PostgresAgent)  (QdrantAgent) │      (no direct connections)
    └──────────────┬──────────────────┘
                   │
                   │    READ
                   ▼
    ┌─────────────────────────────────────────────────────┐
    │                 LANGGRAPH PIPELINE                    │
    │                                                      │
    │  parse → intent → weavers → entities → emotion →     │
    │  grounding → params → decide → EXECUTE → normalize → │
    │  orthodoxy → vault → compose(VEE) → CAN → suggest    │
    │                                                      │
    │  (23 nodes, ~80 state fields, sync)                  │
    └──────────────────────────┬───────────────────────────┘
                               │
                               ▼
                        👤 User gets a
                     validated, archived,
                    explainable response
```

---

## FAQ for New Engineers

**Q: Where do I add domain logic?**  
A: In the execution node (Stage 2 of Path B) and in Codex Hunters data sources (Path A). The core pipeline stays untouched.

**Q: Can I query the database directly?**  
A: No. `PostgresAgent` and `QdrantAgent` are the only interfaces. This is a hard rule, not a suggestion.

**Q: What if my node fails?**  
A: Follow the graceful degradation pattern. Return empty/default state — never block the pipeline. See Pattern Weavers for a reference implementation.

**Q: How do I test my changes?**  
A: Path A and Path B are independently testable because they share state only through the data stores. Mock `PostgresAgent`/`QdrantAgent` for unit tests.

**Q: Where does my new service get its events?**  
A: Subscribe to a Redis Streams channel via `StreamBus.consume()`. Use consumer groups. Always acknowledge after processing. Never inspect other consumers' payloads.
