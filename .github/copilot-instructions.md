# Copilot Instructions — Vitruvyan OS (`vitruvyan-core`)
*Domain-agnostic epistemic operating system. Finance/trading terms in this repo are legacy from an upstream implementation and should be treated as **examples**, not as the repo’s identity.*

---

## Purpose (keep this file small, but useful)
This file is the **high-signal, stable context** Copilot needs to work productively in this repo.

- Prefer **OS-agnostic naming** in new code (entities, signals, events), even if older docs/examples mention tickers/markets.
- If you need deep specs, use the **Appendix docs** in `.github/` (linked at the end) instead of expanding this file.

---

## Sacred Orders (Epistemic Hierarchy)
| Order | Domain | Responsibility |
|------:|--------|----------------|
| Perception | Ingestion | Acquire + normalize external inputs |
| Memory | Persistence | Store structured + semantic state |
| Reason | Computation | Produce deterministic / explainable outputs |
| Discourse | Orchestration | Turn system state into narratives / UX payloads |
| Truth | Governance | Validate outputs, audit, enforce invariants |

---

## Repo layout (what exists here)
- `vitruvyan_core/`: the reusable OS core (agents, bus, governance primitives, contracts)
- `services/`: reference microservices (examples of how to wire the core in a running system)
- `tests/`: unit/integration tests and helpers
- `docs/`: long-form system docs
- `.github/`: “appendix” architecture documents and contributor automation

---

## Import conventions (important)
Most runnable code in `services/` imports the core as `core.*` (e.g. `from core.agents.postgres_agent import PostgresAgent`).
That works because the runtime/container typically adds `vitruvyan_core/` to `PYTHONPATH` (or installs it).

- When adding new modules under `vitruvyan_core/core/`, prefer imports that match existing usage (`core.<...>`).
- Avoid mixing `vitruvyan_core.core.<...>` and `core.<...>` in the same service.

---

## Non‑negotiable invariants (do not violate)

### 1) Service boundaries
- Do **not** directly import implementation code across services; communicate via **REST** or the **event bus**.
- Keep “transport/orchestration” concerns separate from “domain logic” (verticals plug in; core stays generic).

### 2) Persistence access (PostgreSQL / Qdrant)
- Use the agents:
  - PostgreSQL: `core.agents.postgres_agent.PostgresAgent` (`vitruvyan_core/core/agents/postgres_agent.py`)
  - Qdrant: `core.agents.qdrant_agent.QdrantAgent` (`vitruvyan_core/core/agents/qdrant_agent.py`)
- Do **not** create raw clients directly in business logic (e.g. `psycopg2.connect(...)`, `qdrant_client.QdrantClient(...)`) unless the repo explicitly introduces a new agent.
- Never put secrets in docs/commands. Use environment variables (`POSTGRES_*`, `QDRANT_*`, etc.) and placeholders.

**Minimal patterns**
```python
from core.agents.postgres_agent import PostgresAgent

pg = PostgresAgent()
rows = pg.fetch("SELECT 1 AS ok")

with pg.transaction():
    pg.execute("INSERT INTO events (id, payload) VALUES (%s, %s)", ("evt_1", "{}"))
```

### 3) Synaptic Conclave (Cognitive Bus = Redis Streams)
- Streams are the canonical transport. Prefer `StreamBus`:
  - `core.synaptic_conclave.transport.streams.StreamBus` (`vitruvyan_core/core/synaptic_conclave/transport/streams.py`)
- Channel naming: dot notation `<service>.<domain>.<action>` (e.g. `codex.discovery.mapped`).
- Consumers must:
  - be **autonomous** (create consumer groups with `mkstream=True` where applicable)
  - **acknowledge** events after handling to avoid redelivery
  - consume via a generator pattern (don’t load unbounded events into memory)
- Sacred invariant: the bus is **payload-blind** (no semantic routing/correlation/synthesis in transport).

**Minimal consumer pattern**
```python
from core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.create_consumer_group("codex.discovery.mapped", "vault_keepers")  # mkstream=True by default

for event in bus.consume("codex.discovery.mapped", "vault_keepers", "vault_1"):
    handle(event)  # event is TransportEvent (payload is opaque to the bus)
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)
```

**Event envelope (single source of truth)**
- Transport layer (bus-level): `core.synaptic_conclave.events.event_envelope.TransportEvent`
- Cognitive layer (consumer-level): `core.synaptic_conclave.events.event_envelope.CognitiveEvent`
- Adapter boundary: `core.synaptic_conclave.events.event_envelope.EventAdapter`

Do not invent new “event shapes” in random services; use these types or wrap them explicitly.

### 4) Language + narrative rules (OS-agnostic interpretation)
- Treat language detection / multilingual preprocessing as a **Perception** responsibility.
- Treat narrative generation as a **Discourse** responsibility.
- Do **not** introduce backend language-switching logic in multiple nodes without an explicit product decision; keep prompts/templates centralized and consistent.

### 5) “Client validation” contract (generalized from upstream UI)
If a client sends an explicit, validated list (e.g. `validated_entities`, `validated_tickers`):
- Backend must **respect it** and must **not re-extract** entities from raw text.
- An **explicit empty list** means “conversational / no entities selected”; do not silently override it with extraction.

This rule generalizes beyond finance. Replace “ticker” with any domain entity:
- `validated_entities is None` → server may attempt extraction (CLI calls, low-trust clients)
- `validated_entities == []` → user explicitly chose “no entities”
- `validated_entities == [...]` → user explicitly chose entities; trust the list

### 6) Testing bias guardrail
- Avoid biased, repetitive fixtures (e.g., the same few “top entities” in every test).
- Prefer generating diverse test inputs when possible (see `tests/` helpers and guidelines).

---

## Golden Rules (must stay true)
Use these as the “quick mental checklist” while coding. If a change violates one of these, stop and redesign.

- **Core stays generic**: put domain logic in verticals/services, not in `vitruvyan_core/core/`.
- **No cross-service imports**: services talk via **REST** or **StreamBus** events.
- **Agents only for persistence**: use `PostgresAgent` / `QdrantAgent`; no raw DB/vector clients in business logic.
- **No secrets in repo text**: commands/docs must use env vars/placeholders (never real passwords/hosts/tokens).
- **Streams, not Pub/Sub**: Redis Streams is the canonical transport; acknowledge after handling; generator consumption.
- **Bus is payload-blind**: transport never inspects/correlates/routes semantically/synthesizes events.
- **Validated lists are authoritative**: if a client provides `validated_*`, respect it (including explicit `[]`).
- **Bias-aware tests**: avoid tiny repetitive fixtures that overfit (prefer diversity/generators).

---

## Where new code should go (rule of thumb)
- OS primitives / reusable infrastructure → `vitruvyan_core/core/`
  - agents, bus, contracts, governance, orchestration helpers
- Domain contracts / interfaces → `vitruvyan_core/domains/`
  - keep them generic (schema-free), focused on inputs/outputs and invariants
- Domain/vertical implementations → prefer `services/` (reference implementations) or a dedicated domain package
  - avoid baking a single vertical’s assumptions into `core/`

If you’re tempted to add finance-specific rules into `core/`, stop and ask:
“Can this be expressed as a domain contract + a vertical implementation instead?”

---

## Quick workflow (safe defaults)
- Search code: `rg "<pattern>"`
- Run tests: `pytest`
- If using reference services: prefer `docker compose up -d --build <service>` (no hardcoded hostnames/passwords in docs)

---

## Legacy vocabulary (upstream artifacts → OS terms)
You will see finance-heavy names in historical docs and a few helpers. Map them mentally:
- “ticker/entity” → “entity”
- “screening/ranking” → “batch scoring”
- “sentiment” → “text signal”
- “portfolio” → “collection/working set”

Prefer OS terms in new code unless you are working inside an explicitly finance vertical.

---

## References (deep docs; do not duplicate here)
- Neural Engine example vertical: `.github/Vitruvyan_Appendix_A_Neural_engine.md`
- Proprietary algorithms (historical context): `.github/Vitruvyan_Appendix_B_Proprietary_Algorithms.md`
- Roadmap: `.github/Vitruvyan_Appendix_C_Epistemic_Roadmap_2026.md`
- Truth & integrity layer: `.github/Vitruvyan_Appendix_D_Truth_and_Integrity_Layer.md`
- RAG system (example): `.github/Vitruvyan_Appendix_E_RAG_System.md`
- Conversational layer: `.github/Vitruvyan_Appendix_F_Conversational_Layer.md`
- Conversational architecture V1: `.github/Vitruvyan_Appendix_G_ Conversational_Architecture_V1.md`
- Ledger system (example): `.github/Vitruvyan_Appendix_H_Blockchain_Ledger.md`
- Pattern Weavers (example): `.github/Vitruvyan_Appendix_I_Pattern_Weavers.md`
- LangGraph exec summary: `.github/Vitruvyan_Appendix_J_LangGraph_Executive_Summary.md`
- Babel Gardens (example vertical): `.github/Vitruvyan_Appendix_K_Babel_Gardens.md`
- MCP integration: `.github/Vitruvyan_Appendix_K_MCP_Integration.md`
- Synaptic Conclave (bus): `.github/Vitruvyan_Appendix_L_Synaptic_Conclave.md`
- UI architecture (example client): `.github/Vitruvyan_Appendix_L_UI_Architecture.md`
- Shadow trading (example vertical): `.github/Vitruvyan_Appendix_M_Shadow_Trading.md`
- Portfolio architects (example vertical): `.github/Vitruvyan_Appendix_N_Portfolio_Architects.md`
