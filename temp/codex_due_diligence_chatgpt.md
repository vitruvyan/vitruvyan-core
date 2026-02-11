**1. Domain Leakage Findings**
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:8` — Severity: **Critical** — Explicitly declares finance-specific logic (tickers/fundamentals) inside `core/` listener; this is live integration surface, not an archive.
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:55` — Severity: **Critical** — Hardcodes finance-technical taxonomy in channels (`codex.technical.momentum.requested`).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:59` — Severity: **Critical** — Hardcodes finance domain concept (`codex.fundamentals.refresh.requested`).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:161` — Severity: **Critical** — Payload schema assumes finance entities (`tickers`).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:162` — Severity: **Critical** — Defaults to finance-specific source (`['yfinance']`).
- `services/api_codex_hunters/streams_listener.py:11` — Severity: **Critical** — Streams wrapper subscribes to finance-technical channels (momentum/trend/volatility).
- `services/api_codex_hunters/streams_listener.py:15` — Severity: **Critical** — Streams wrapper includes “fundamentals extraction” channel.
- `services/api_codex_hunters/streams_listener.py:19` — Severity: **Critical** — Purpose statement frames output as “sacred market knowledge” (domain leakage in the Order’s operational description).
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py:76` — Severity: **Medium** — Core config includes a “Finance domain override” example (tickers/ticker_embeddings/`codex.finance`) inside the purportedly agnostic domain layer.
- `vitruvyan_core/core/governance/codex_hunters/philosophy/charter.md:70` — Severity: **Medium** — Sacred charter embeds finance deployment example (`tickers`, `ticker_embeddings`, `codex.finance`).
- `vitruvyan_core/core/governance/codex_hunters/README.md:33` — Severity: **Medium** — “Quick Start” uses `AAPL` as the canonical entity example (stock ticker leakage).
- `vitruvyan_core/core/governance/codex_hunters/examples/complete_workflow_example.py:41` — Severity: **Medium** — Example source is explicitly “financial_api” and described as “Financial data API”.

**2. Abstraction Violations**
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py:34` — Severity: **Medium** — LIVELLO 1 domain config encodes vendor semantics (“Qdrant/vector store”) instead of a storage-agnostic abstraction.
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py:43` — Severity: **Medium** — LIVELLO 1 config references a specific RDBMS (“PostgreSQL”) in the pure domain layer.
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py:127` — Severity: **Medium** — Embedding provider/model default is specific (`sentence-transformers/all-MiniLM-L6-v2`) in core config.
- `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py:186` — Severity: **Medium** — Binder encodes Postgres-specific storage semantics (“JSONB column”).
- `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py:208` — Severity: **Critical** — LIVELLO 1 returns Qdrant-specific “upsert” payload contract.
- `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py:215` — Severity: **Critical** — Payload shape is literally `{id, vector, payload}`, i.e., Qdrant point schema in core consumer output.
- `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py:126` — Severity: **Medium** — `storage_refs` keys are hardcoded as `"postgres"` / `"qdrant"` (provider coupling leaks into domain objects).
- `vitruvyan_core/core/governance/codex_hunters/monitoring/__init__.py:85` — Severity: **Low** — LIVELLO 1 health components enumerate infra (`POSTGRES`, `QDRANT`, `REDIS`), tightening conceptual coupling between “pure domain” and infrastructure inventory.

**3. Boundary Violations (Including Micelial Integration)**
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:60` — Severity: **Critical** — Codex Hunters listener subscribes to `codex.risk.refresh.requested` (risk scoring is explicitly outside Codex Hunters’ epistemic boundary).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:234` — Severity: **Critical** — Implements VARE/Cassandra risk analysis handling inside Codex Hunters listener codepath (overlap with risk engine / Order boundary breach).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:268` — Severity: **Critical** — Publishes `codex.risk.completed` from Codex Hunters listener (Codex Hunters becomes an adjudicator/signal emitter).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:215` — Severity: **Medium** — “Database schema validation” handler lives in Codex Hunters listener (drifts toward orthodoxy/integrity concerns, not ingestion normalization).
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:93` — Severity: **Critical** — Uses Redis Pub/Sub subscribe flow (not Streams), violating “Streams-only” micelial integration.
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:289` — Severity: **Critical** — Uses `redis_client.publish` (Pub/Sub) for expedition completion; even if consumption is bridged, emission is not Streams-native.
- `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py:213` — Severity: **Critical** — Direct HTTP cross-service call (`POST {CODEX_API_BASE}/expedition/run`) violates “inter-order comm via Redis Streams only”.
- `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py:301` — Severity: **Medium** — Hardcodes `target="audit_engine"` in emitted event payload, creating hidden coupling/decision-routing semantics at the integration boundary.

**4. Configuration Audit**
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py:10` — Severity: **Medium** — YAML/JSON injection is explicitly “future”; today the configuration story is not file-driven (fails “entirely YAML-driven” requirement as stated).
- `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py:129` — Severity: **Medium** — Quality threshold `0.5` is hardcoded into status assignment; no config override path in `CodexConfig`.
- `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py:240` — Severity: **Medium** — Quality scoring weight (`len(errors) * 0.1`) is hardcoded.
- `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py:244` — Severity: **Medium** — Null-penalty weight (`null_ratio * 0.3`) is hardcoded.
- `vitruvyan_core/core/governance/codex_hunters/philosophy/charter.md:36` — Severity: **Medium** — Charter invariant: dedupe key is deterministic based on entity_id + source + data hash.
- `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py:159` — Severity: **Critical** — Tracker dedupe key uses *current date* (not data hash), breaking the charter invariant and making dedupe non-deterministic across days.
- `services/api_codex_hunters/adapters/bus_adapter.py:113` — Severity: **Critical** — Service adapter sends `source_type`; LIVELLO 1 `TrackerConsumer` requires `source` (`vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py:64`), so the pipeline fails at the boundary.
- `services/api_codex_hunters/adapters/bus_adapter.py:129` — Severity: **Critical** — Emits `Channels.DISCOVERED`, but no such constant exists (see `vitruvyan_core/core/governance/codex_hunters/events/__init__.py:37`).
- `services/api_codex_hunters/adapters/bus_adapter.py:143` — Severity: **Critical** — Returns `result.message`, but LIVELLO 1 `ProcessResult` has no `message` field (`vitruvyan_core/core/governance/codex_hunters/consumers/base.py:23`).
- `services/api_codex_hunters/adapters/bus_adapter.py:246` — Severity: **Critical** — Uses nonexistent config shape (`codex_config.table.entities`), diverging from LIVELLO 1 config (`vitruvyan_core/core/governance/codex_hunters/domain/config.py:85`).
- `vitruvyan_core/core/governance/codex_hunters/examples/tracker_example.py:49` — Severity: **Low** — Examples/documentation reference config fields (`quality_threshold`, `dedupe_enabled`) that do not exist in current `CodexConfig` (drift undermines “config injection” claims and encourages hardcoded assumptions).

**5. Legacy Residue Analysis (Mercator/Finance-Era Comparison)**
- **Legacy finance-era constructs (Appendix evidence)**
  - `.github/Vitruvyan_Appendix_Codex_Hunters.md:26` — Codex Hunters described as specializing in “financial data”.
  - `.github/Vitruvyan_Appendix_Codex_Hunters.md:40` — “Dual-Memory” assumption (PostgreSQL + Qdrant).
  - `.github/Vitruvyan_Appendix_Codex_Hunters.md:67` — Cognitive Bus explicitly “Redis Pub/Sub”.
  - `.github/Vitruvyan_Appendix_Codex_Hunters.md:117` — Finance-specific data sources (r/wallstreetbets etc).
  - `.github/Vitruvyan_Appendix_Codex_Hunters.md:157` — Finance APIs (Alpha Vantage, Yahoo Finance).
- **Legacy residue still present in current (non-archive) wiring**
  - `services/api_codex_hunters/streams_listener.py:11` — Technical indicator channel taxonomy persists (momentum/trend/volatility).
  - `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:161` — “tickers” payload persists.
  - `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:162` — yfinance default persists.
  - `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:234` — Risk-analysis path persists (VARE/Cassandra).
  - `vitruvyan_core/core/governance/codex_hunters/domain/config.py:76` — “Finance domain override” is still promoted inside core config.
- **Finance terms still present (representative)**
  - `tickers`, `ticker_embeddings`, `codex.finance`: `vitruvyan_core/core/governance/codex_hunters/domain/config.py:78`
  - `AAPL` / stock-shaped fields (price, market_cap, pe_ratio): `vitruvyan_core/core/governance/codex_hunters/examples/complete_workflow_example.py:80`
  - “fundamentals”, “technical.momentum/trend/volatility”: `services/api_codex_hunters/streams_listener.py:15`
- **Finance-era logic patterns still present**
  - Technical-indicator backfill taxonomy: `services/api_codex_hunters/streams_listener.py:11`
  - Fundamentals extraction taxonomy: `services/api_codex_hunters/streams_listener.py:15`
  - Risk analysis execution + completion event: `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:234`
  - Dual-write mental model preserved in “postgres_payload/qdrant_payload”: `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py:62`
- **Suspicious naming conventions / implicit assumptions**
  - Prefixing streams with finance namespace: `vitruvyan_core/core/governance/codex_hunters/philosophy/charter.md:74`
  - Entity identity implicitly treated as ticker in examples/docs: `vitruvyan_core/core/governance/codex_hunters/README.md:33`
- **What is safe to keep (as legacy reference)**
  - `vitruvyan_core/core/governance/codex_hunters/_legacy/__init__.py:8` — Legacy archive is clearly labeled as finance-specific and “DO NOT import”; acceptable if truly dead-code.
- **What must be removed/relocated for “core-grade agnostic”**
  - Finance-specific Synaptic Conclave listener in core: `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:8` (also explicitly tracked for migration: `docs/TECH_DEBT_DOMAIN_MIGRATION.md:25`).
  - Finance-specific channel taxonomy in the service listener wrapper: `services/api_codex_hunters/streams_listener.py:11`.
  - Finance-coded examples/charter/config examples that normalize tickers/market fields as the “default” mental model: `vitruvyan_core/core/governance/codex_hunters/philosophy/charter.md:70`.

**6. Agnosticization Score (0–100)**
- **Score: 24 / 100**
  - Domain Purity: **4/20** (active tickers/yfinance/fundamentals/technical channels remain in live listener+wrapper: `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:161`, `services/api_codex_hunters/streams_listener.py:11`)
  - Abstraction Purity: **6/20** (LIVELLO 1 still speaks Qdrant/Postgres and returns Qdrant-shaped payloads: `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py:215`)
  - Epistemic Boundary: **4/20** (risk analysis path exists under Codex Hunters: `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:234`)
  - Config Injection: **6/20** (hardcoded thresholds/weights + charter invariant violation: `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py:159`)
  - Micelial Integration: **4/20** (Pub/Sub still used + direct HTTP orchestration: `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:93`, `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py:213`)
- **3 highest-priority improvements (non-redesign, compliance-driven)**
  - Migrate/contain finance-specific listener and channel taxonomy out of core + out of the default service wrapper path: `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:8`, `services/api_codex_hunters/streams_listener.py:11`.
  - Reconcile LIVELLO 2 ↔ LIVELLO 1 contracts (field names + channel constants + result schema) to eliminate silent failures: `services/api_codex_hunters/adapters/bus_adapter.py:113`, `services/api_codex_hunters/adapters/bus_adapter.py:143`.
  - Make quality threshold/scoring and dedupe strategy truly config-driven and align with charter invariants (remove date-based dedupe key): `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py:129`, `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py:159`.