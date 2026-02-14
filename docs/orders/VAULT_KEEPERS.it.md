# Vault Keepers

## A cosa serve

- Validazione integrità Postgres/Qdrant
- Pianificazione backup/recovery + direttive di archiviazione
- Generazione audit trail immutabile (il service esegue l’I/O)

- **Livello epistemico**: Truth (Memoria & Archival)
- **Mandato**: integrità, backup/recovery, audit trail immutabile
- **Output**: report integrità, snapshot metadata, piani recovery (LIVELLO 1 è pure)

## Charter (Mandato + Non-goals)

### Mandato
Proteggere la conoscenza persistita (PostgreSQL/Qdrant) con decisioni deterministiche su integrità e audit.

### Non-goals
- Nessun I/O in LIVELLO 1 (no DB, filesystem, network).
- Non è un tribunale (verdetti → Orthodoxy Wardens).

## Interfacce

### Contratto eventi (Cognitive Bus)
Definiti in `vitruvyan_core/core/governance/vault_keepers/events/vault_events.py` (estratto):

- inbound: `vault.archive.requested`, `vault.restore.requested`, `vault.snapshot.requested`
- outbound: `vault.archive.completed`, `vault.snapshot.created`, `vault.integrity.validated`

### Servizio (LIVELLO 2)
- `services/api_vault_keepers/` — esegue I/O (backup/restore) ed emette eventi

## Pipeline (happy path)

1. **Sentinel** → `IntegrityReport`
2. **Archivist** → `VaultSnapshot`
3. **Guardian** → `RecoveryResult`
4. **Chamberlain** → audit entries

## Mappa codice

### LIVELLO 1 (pure)
- `vitruvyan_core/core/governance/vault_keepers/domain/vault_objects.py`
- `vitruvyan_core/core/governance/vault_keepers/consumers/…`

### LIVELLO 2 (adapters)
- `services/api_vault_keepers/`

## Verticalizzazione (pilota finanza)

Il dominio definisce retention, target critici (`finance.tickers`, `ticker_embeddings`) e priorità di restore.
