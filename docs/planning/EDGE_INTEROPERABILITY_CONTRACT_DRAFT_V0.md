# EDGE INTEROPERABILITY CONTRACT — Draft v0

> **Date**: February 16, 2026
> **Status**: Draft (pre-implementation)
> **Scope**: First foundational block for Vitruvyan Edge
> **Placement**: `infrastructure/edge`

---

## 1. Purpose

Define the rules, boundaries, and implementation strategy for a default interoperability layer that allows Vitruvyan Core to ingest data from external environments.

The Edge layer must be:
- Multi-domain
- Secure by default
- Scalable in throughput and features
- Readable and maintainable
- Energy-efficient for constrained hardware
- Multi-platform (Linux, mini PCs, SBCs, VPS, mobile relays, edge gateways)

`Raspberry` is treated as one reference profile, not the target platform.

---

## 2. Architectural Positioning

The new module is introduced as:

- `services/api_edge_gateway` (default data plane for external ingest)
- Integrated with Core through event contracts and governance rules
- Domain-agnostic, plugin-extensible, and transport-agnostic

High-level path:

`External Source (H2M/M2M) -> Edge Gateway -> Local Policy + Local Outbox -> Core Bus -> Intake -> Governance (Orthodoxy) -> Downstream Orders`

---

## 3. Key Decisions (Draft)

### 3.1 MCP and Orthodoxy roles

Decision:
- Do not put MCP in the critical ingest data path.
- Use Orthodoxy validation as governance checkpoint for edge-originated evidence.
- Create dedicated MCP tools for control-plane operations only.

Rationale:
- MCP is optimized for tool orchestration and H2M workflows.
- Intake data path requires high-throughput, low-latency, deterministic behavior.
- Governance/invariant validation belongs to Orthodoxy responsibilities.

Control-plane MCP examples:
- `edge.device.register`
- `edge.policy.deploy`
- `edge.link.status`
- `edge.buffer.inspect`

### 3.2 Build vs Buy

Build from scratch:
- Edge evidence envelope contract
- Idempotency semantics
- Policy model and enforcement mapping
- Edge/Core sync protocol
- Governance ontology and invariants

Use OSS:
- MQTT broker (`Mosquitto` baseline, `EMQX` when scaling)
- Persistent local queue store (`SQLite` baseline)
- Transport security primitives (mTLS, JWT libs)
- Metrics/logging/tracing stack

Rule:
- Build only where Vitruvyan semantic contract is proprietary.
- Buy/reuse for transport and infrastructure commodities.

### 3.3 MCP suitability for Intake (based on current implementation audit)

Observed MCP characteristics in current codebase:
- Single request-response tool execution model (`/execute`), no high-throughput ingest channel
- Tool-centric payload (`tool`, `args`, `user_id`) rather than evidence envelope lifecycle
- Current executors are analytical/orchestration oriented (screen/compare/vee/semantic), not acquisition adapters
- Governance checks in MCP middleware are selective (tool-specific), not a full intake policy engine
- Runtime dependency chain on orchestration APIs (LangGraph/Pattern Weavers), which is not ideal for edge data-path autonomy

Decision update:
- MCP is **approved for control-plane and H2M orchestration**, not as default M2M ingest data-plane.
- Intake data-plane must remain in a dedicated Edge Gateway path with deterministic contracts and offline buffering.
- If needed, MCP can expose control tools that interact with edge runtime state (diagnostics, provisioning, policy push), but must not be the mandatory ingress path for external evidence.

Allowed MCP usage in Edge program:
- `edge.device.register`
- `edge.policy.deploy`
- `edge.buffer.inspect`
- `edge.link.status`

Disallowed MCP usage in Edge program:
- Direct ingestion of raw external telemetry/file streams as default path
- Mandatory dependency for core evidence delivery from edge devices

---

## 4. Design Principles

1. Domain-agnostic core, domain-specific metadata only via contract fields.
2. Strict separation between data plane and control plane.
3. Append-only and auditable event lifecycle.
4. Policy-driven behavior, not hardcoded flow branching.
5. Offline-first edge operation with deterministic replay.
6. Minimal runtime footprint for constrained devices.
7. Backward compatibility adapters for existing intake events.

---

## 5. Functional Scope

### 5.1 Human-to-Machine (H2M)

- Local ingest API for operator uploads and form-based evidence input
- Guided validation prompts for mandatory fields
- Manual sync trigger and status visibility

### 5.2 Machine-to-Machine (M2M)

- MQTT topic ingestion
- HTTP webhook ingestion with signatures
- File watcher ingestion (drop-folder)
- Optional sensor/serial adapter plugins

### 5.3 Autonomic behavior (no core connectivity)

When disconnected from core:
- Continue local intake and validation
- Persist outbox with priority and TTL
- Enforce local minimum policies
- Expose local status and health
- Replay queued evidence on reconnection with idempotency

---

## 6. Non-Functional Requirements

### 6.1 Security

- Device identity per edge node
- mTLS for edge-core channel
- Signed payload + nonce/timestamp anti-replay
- Least privilege per adapter/channel
- Secrets rotation policy
- Audit log integrity checks

### 6.2 Scalability

- Backpressure and bounded queues
- Retry with exponential backoff + jitter
- Partition by device/domain/topic
- Horizontal scale on VPS; profile scale on constrained edge nodes

### 6.3 Efficiency

- Async I/O first, avoid active polling by default
- Batching and compression thresholds configurable
- Runtime profiles: `eco`, `balanced`, `performance`
- Resource caps (CPU/memory/network) configurable per deployment

### 6.4 Readability and maintainability

- Clear module boundaries
- Contract-first API design
- Short services, explicit adapters, typed payloads
- Integration tests per adapter + offline scenarios

---

## 7. Canonical Contracts (to formalize)

### 7.1 `EdgeEvidenceEnvelope v1`

Mandatory fields (draft):
- `envelope_id`
- `event_type`
- `event_version`
- `created_utc`
- `device_id`
- `source_type`
- `domain_family`
- `payload_ref` or `payload_inline`
- `integrity.hash`
- `idempotency_key`
- `policy_ref`
- `connectivity_mode` (`online` or `offline_buffered`)

### 7.2 `EdgePolicy v1`

- Input constraints and schema refs
- Allowed source types and max payload sizes
- Local retention and replay windows
- Security requirements by channel
- Fallback mode behavior in offline state

### 7.3 `EdgeCapability v1`

- Declared platform and architecture
- Supported adapters
- Max throughput class
- Power profile class
- Security posture level

---

## 8. Ontology Seeds (Draft)

Event taxonomy candidates:
- `edge.ingest.received`
- `edge.ingest.validated`
- `edge.ingest.rejected`
- `edge.buffer.stored`
- `edge.buffer.replayed`
- `edge.forward.sent`
- `edge.forward.failed`
- `edge.health.degraded`
- `edge.policy.applied`

State terms:
- `connectivity_state`: `online`, `degraded`, `offline`
- `governance_state`: `pending`, `validated`, `rejected`
- `delivery_state`: `queued`, `forwarded`, `acked`, `dead_letter`

---

## 9. Proposed Repository Layout (Draft)

```text
infrastructure/edge/
├── gateway/
│   ├── app/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── adapters/
│   │   │   ├── ingress_http/
│   │   │   ├── ingress_mqtt/
│   │   │   ├── ingress_files/
│   │   │   └── egress_core_bus/
│   │   ├── policy/
│   │   ├── outbox/
│   │   └── observability/
│   ├── tests/
│   ├── Dockerfile
│   └── README.md
├── contracts/
│   ├── edge_evidence_envelope_v1.json
│   ├── edge_policy_v1.json
│   └── edge_capability_v1.json
└── docs/
    ├── deployment_profiles.md
    ├── security_model.md
    └── offline_behavior.md
```

---

## 10. Implementation Roadmap

### Phase 0 — Contract and threat model
- Define envelope/policy/capability schemas
- Define invariants for Orthodoxy integration
- Produce ADRs for transport and security decisions

### Phase 1 — MVP edge gateway
- HTTP + MQTT ingest adapters
- Local SQLite outbox + replay worker
- Core bus publisher adapter
- Basic health and metrics endpoints

### Phase 2 — Governance and hardening
- Orthodoxy validation flow for edge-origin events
- Signature verification and mTLS
- Dead-letter handling and replay controls

### Phase 3 — Multi-platform packaging
- Docker profile (server/VPS)
- systemd profile (mini PC/SBC)
- lightweight runtime profile (constrained edge)
- mobile relay profile (forward-only)

### Phase 4 — Performance and energy certification
- Benchmark matrix by device class
- `eco/balanced/performance` tuning
- Acceptance thresholds and regression guardrails

---

## 11. Acceptance Criteria for “First Block”

1. External data can be ingested on an edge node and forwarded to core through the canonical contract.
2. Offline mode stores data safely and replays without duplicates after reconnection.
3. Governance validation is enforceable via Orthodoxy rules.
4. At least two transports (HTTP + MQTT) are production-ready.
5. Runtime profile `eco` is validated on one constrained device class.
6. Documentation is sufficient for independent deployment by platform.

---

## 12. Open Questions Before Freezing v1

1. Which bus is canonical for edge-core forwarding in V1: Redis Streams only or abstracted bus interface from day one?
2. Is smartphone support native or relay-only in V1?
3. Which Orthodoxy invariants are hard-fail vs soft-fail in degraded/offline mode?
4. Should payload encryption at rest be mandatory for all edge profiles or only regulated profiles?
5. Which KPI thresholds are mandatory for V1 certification by platform class?

---

## 13. Next Step

After review, produce:
- `EDGE_INTEROPERABILITY_CONTRACT_V1.md` (frozen)
- JSON schemas for v1 contracts
- ADR set for transport, security, and offline semantics
