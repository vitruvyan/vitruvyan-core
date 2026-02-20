# 🌉 Edge Gateway Flow (Offline-First)

> **Updated**: February 16, 2026  
> **Scope**: `services/api_edge_gateway` MVP

## 🎯 Purpose

Describe how edge runtimes ingest local data, buffer offline, and relay to Core Oculus Prime.

## 🔄 Flow Graph

```mermaid
flowchart TD
    A[Edge Source<br/>H2M or M2M] --> B[Edge Gateway API<br/>POST /api/edge/oculus-prime]
    B --> C[(SQLite Outbox<br/>status=pending)]
    C --> D{Core Reachable?}
    D -- Yes --> E[Relay to Core Oculus Prime<br/>/api/oculus-prime/{type}]
    E --> F[(Core PostgreSQL<br/>evidence_packs)]
    E --> G[[Redis Streams<br/>oculus_prime.evidence.created]]
    D -- No --> H[Keep Pending]
    H --> I[POST /api/edge/replay]
    I --> D
```

## Operational Endpoints

- `GET /health`
- `GET /status`
- `GET /metrics`
- `POST /api/edge/replay`

## Design Constraints

1. Data-plane only: MCP is not used for evidence transport.
2. Semantic neutrality preserved: edge relays payloads, does not enrich.
3. Deterministic replay order: FIFO by outbox record id.
