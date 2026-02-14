# Vault Keepers

> **Last Updated**: February 14, 2026

## What it does

- Integrity validation across Postgres/Qdrant
- Backup/recovery planning + archival directives
- Immutable audit trail generation (service executes I/O)

- **Epistemic Layer**: Truth (Memory & Archival)
- **Mandate**: integrity monitoring, backup/recovery planning, immutable audit trails
- **Outputs**: integrity reports, snapshots metadata, recovery plans (LIVELLO 1 is pure)

## Charter (Mandate + Non-goals)

### Mandate
Guard the sanctity of stored knowledge across PostgreSQL and Qdrant by producing deterministic integrity/audit decisions.

### Non-goals
- No direct persistence in LIVELLO 1 (no DB, no filesystem, no network).
- Not a governance tribunal (verdicts belong to Orthodoxy Wardens).

## Interfaces

### Event contract (Cognitive Bus)
Defined in `vitruvyan_core/core/governance/vault_keepers/events/vault_events.py` (selected):

- inbound: `vault.archive.requested`, `vault.restore.requested`, `vault.snapshot.requested`
- outbound: `vault.archive.completed`, `vault.snapshot.created`, `vault.integrity.validated`

### Service (LIVELLO 2)
- `services/api_vault_keepers/` — executes I/O (PostgreSQL/Qdrant backups, restores) and emits events

## Pipeline (happy path)

1. **Sentinel** validates integrity → `IntegrityReport`
2. **Archivist** produces snapshot metadata → `VaultSnapshot`
3. **Guardian** plans/validates recovery → `RecoveryResult`
4. **Chamberlain** emits immutable audit entries

## Code map

### LIVELLO 1 (pure)
- `vitruvyan_core/core/governance/vault_keepers/domain/vault_objects.py`
- `vitruvyan_core/core/governance/vault_keepers/consumers/sentinel.py`
- `vitruvyan_core/core/governance/vault_keepers/consumers/archivist.py`
- `vitruvyan_core/core/governance/vault_keepers/consumers/guardian.py`
- `vitruvyan_core/core/governance/vault_keepers/consumers/chamberlain.py`

### LIVELLO 2 (adapters)
- `services/api_vault_keepers/` — I/O boundary (backup/restore execution)

## Verticalization (finance pilot)

Finance plugs in by defining:

- retention policies (how long to keep snapshots/audit trails)
- critical tables/collections to validate (e.g. `finance.tickers`, `ticker_embeddings`)
- restore priority rules (what must be restored first in incidents)
