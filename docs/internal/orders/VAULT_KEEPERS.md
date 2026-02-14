# Vault Keepers

> **Last Updated**: February 14, 2026

<p class="kb-subtitle">Backup and recovery planning, integrity checks, and immutable audit trails.</p>

## What it does

- **Integrity validation**: judges health/coherence signals and outputs integrity reports
- **Backup & recovery planning**: produces snapshot/restore plans (service executes operations)
- **Audit trail**: emits immutable audit records and archival directives

Vault Keepers is the **archival + integrity + backup/restore planning** order. It produces pure decisions and plans; the service layer executes I/O.

## Code map

- **LIVELLO 1 (pure vault roles, no I/O)**: `vitruvyan_core/core/governance/vault_keepers/`
  - Consumers: `consumers/guardian.py`, `consumers/sentinel.py`, `consumers/archivist.py`, `consumers/chamberlain.py`, `consumers/signal_archivist.py`
  - Domain objects: `domain/vault_objects.py`, `domain/signal_archive.py`
  - Events schema: `events/vault_events.py`
  - Examples: `examples/*`
- **LIVELLO 2 (service + adapters)**: `services/api_vault_keepers/`

## Roles and responsibilities

Vault Keepers follows the “pure role” model:

- Every consumer implements `VaultRole` (`consumers/base.py`)
- `process()` must not perform I/O (service layer executes the plan)

> Note: several roles generate IDs/timestamps (`*_id = f"...{utcnow()}"`) for traceability. That makes outputs **unique**, not strictly deterministic byte-for-byte.

---

## Agents / Consumers

### `Guardian` — operations orchestrator (routing plan)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/guardian.py`
- Purpose:
  - given `event_type` / `operation` + priority
  - decides which roles to invoke (`sentinel`, `archivist`, `chamberlain`, …)
  - decides sequence (`single`, `parallel`, `sequential`)
  - flags `requires_approval` for critical operations

**How it works (important details)**:

- Plans based on keywords:
  - integrity → `roles_to_invoke=["sentinel"]`, `sequence="single"`
  - backup → optionally runs `sentinel` first for `high|critical`, then `archivist` + `chamberlain`
  - restore → `sentinel` + `chamberlain`, and requires approval when `dry_run=false`
  - archive → `archivist` + `chamberlain`
- Output is a routing plan dict with `operation`, `roles_to_invoke`, `sequence`, `requires_approval`, `correlation_id`, `timestamp`

### `Sentinel` — integrity validator (health → integrity report)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/sentinel.py`
- Purpose:
  - judges health of Postgres/Qdrant + coherence signals (provided by service layer)
  - outputs `IntegrityReport` with `overall_status`:
    - `sacred`
    - `blessed_with_concerns`
    - `corruption_detected`

**How it works (important details)**:

- Input expects:
  - `postgresql.status` and `qdrant.status` (`healthy|degraded|corrupted|unreachable`)
  - `coherence.status` (`coherent|drift_detected|critical`)
- Overall judgment:
  - any corrupted/unreachable datastore or `coherence=critical` → `corruption_detected`
  - all healthy + coherent → `sacred`
  - otherwise → `blessed_with_concerns`
- Findings include human-readable hints (e.g., degraded tables, drift ratio)

### `Archivist` — backup planner + archive validator (plan only)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/archivist.py`
- Purpose:
  - plans backup operations (`VaultSnapshot`)
  - plans archival operations (`ArchiveMetadata`)
  - sets retention horizons and destination paths (service layer executes)

**How it works (important details)**:

- `operation="backup"`:
  - decides `scope` from `mode` + `include_vectors`
  - returns `VaultSnapshot` with planned file paths under `/var/vitruvyan/vaults/`
- `operation="archive"`:
  - returns `ArchiveMetadata` with planned path under `/var/vitruvyan/vaults/archives/`
  - default retention is 30 days

### `Chamberlain` — audit trail recorder (record only)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/chamberlain.py`
- Purpose:
  - builds immutable `AuditRecord` objects for vault operations
  - includes correlation ID + metadata tuples
  - no persistence; service layer stores it

**How it works (important details)**:

- Builds `record_id` as `audit_<timestamp>`
- Normalizes metadata to `tuple((k, str(v)), ...)` and prepends standard tuples:
  - `("warden", "vault_keepers")`, `("priority", ...)`, `("scope", ...)`

### `SignalArchivist` — Babel signal timeseries archival (domain-agnostic)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/signal_archivist.py`
- Purpose:
  - converts Babel Gardens signal extraction results into a `SignalTimeseries`
  - keeps traceability via `extraction_method` and `source_text_hash`
  - supports any vertical (`finance`, `cybersecurity`, `healthcare`, …)

**How it works (important details)**:

- Validates:
  - `entity_id` must be present
  - `signal_results` must be non-empty
  - all `signal_results` should share a single `signal_name`
- Builds `SignalDataPoint` objects:
  - `timestamp` from `extraction_trace.timestamp` (or `utcnow()` fallback)
  - `source_text_hash = sha256(source_text)[:16]` (optional)
- Sorts points chronologically before returning
