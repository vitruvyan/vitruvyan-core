# Template — Sacred Order Component (Public/Internal)

Use this template to document a **Sacred Order** (domain-agnostic core component) in a way that is:

- consistent across Orders,
- easy to scan by engineers,
- explicit about **boundaries** (what the Order does / does not do),
- clear on how **vertical domains** (finance, energy, healthcare, …) plug in without contaminating the core.

> Keep “public” pages high-level and “internal” pages deep. If you need both, split into two pages with the same structure.

---

## 0) One-paragraph Summary

- **Order**: `<NAME>`
- **Epistemic Layer**: `<PERCEPTION | MEMORY | REASON | DISCOURSE | TRUTH | GOVERNANCE>`
- **Mandate** (1 sentence): `<what problem this Order solves>`
- **Outputs**: `<what it emits/returns>`
- **Key invariants**: `<3 bullets>`

---

## 1) Charter (Mandate + Non-Goals)

### Mandate
Explain “why it exists” and what it guarantees.

### Non-Goals (hard boundaries)
List what is explicitly out-of-scope (e.g., risk scoring, business decisions, UI, persistence).

---

## 2) Interfaces (How to Integrate)

### Event Contract (Cognitive Bus)
- **Request channels**: `<prefix>.<…>.requested`
- **Response channels**: `<prefix>.<…>.completed | failed`
- **Envelope**: include required fields (`correlation_id`, `emitter`, `timestamp`, …)

### API (if any)
- Base URL + ports
- Key endpoints
- Required headers / auth assumptions

### Inputs/Outputs (schemas)
Table with: `name`, `type`, `required`, `meaning`.

---

## 3) Pipeline (Happy Path)

Describe the default pipeline as steps and what each step produces.

Example:

1. `Track` → `DiscoveredEntity`
2. `Restore` → `RestoredEntity` (+ quality score)
3. `Bind` → `BoundEntity` (storage-ready metadata)

---

## 4) Code Map (Where to Read)

### LIVELLO 1 (Pure Domain)
- `core/<order>/domain/...` — entities + config
- `core/<order>/consumers/...` — pure processing stages
- `core/<order>/events/...` — channel names + envelope

### LIVELLO 2 (Service / Adapters)
- `services/api_<order>/...` — API surface + adapters
- `.../adapters/...` — I/O boundary (DB, vector DB, HTTP, files, vendors)
- `.../streams_listener.py` — Streams bridge (if used)

Add a bullet list “file → responsibility” (must be precise).

---

## 5) Operational Notes (How it Runs)

- Docker services involved
- Health checks
- Env vars (only the ones that matter)
- Observability: metrics names, logs, dashboards
- Failure modes and how to debug

---

## 6) Verticalization (Domain Implementation Guide)

This section is mandatory for domain-agnostic Orders.

### 6.1 Domain Pack: what a vertical must provide

- **Domain config**: tables/collections/stream prefix/sources (YAML or code)
- **Normalizers/validators**: per-source data shape normalization
- **Source adapters (LIVELLO 2)**: fetching, rate limiting, caching, retries
- **Orchestration hooks**: routing rules to trigger this Order (graph/plugin)

### 6.2 Vocabulary mapping (avoid confusion)

| Core primitive | Finance example | Energy example |
|---|---|---|
| `entity_id` | `ticker` | `plant_id` / `meter_id` |
| `source` | `yfinance` | `scada_api` / `iso_feed` |
| `normalized_data` | fundamentals/metrics | telemetry/forecasts |

### 6.3 Minimal “Domain Pack” skeleton

Describe *where* the domain lives (e.g., `domains/<domain>_plugin.py`, `examples/verticals/<domain>/...`) and the minimal artifacts:

- `domains/<domain>_plugin.py` (routing + intent integration)
- `config/<order>_<domain>.yaml` (sources + streams prefix)
- `services/api_<order>/adapters/<domain>_source.py` (I/O boundary)

---

## 7) Known Issues / Roadmap

- Link to refactor plan(s)
- List current “violations” (domain leakage, provider coupling, contract drift)
- Define target state

