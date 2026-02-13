# Vault Keepers

<p class="kb-subtitle">Pianificazione backup e recovery, integrity checks e audit trail immutabile.</p>

Vault Keepers è l’ordine di **archiviazione + integrità + pianificazione backup/restore**. Produce decisioni e piani puri; il service layer esegue l’I/O.

## Mappa del codice

- **LIVELLO 1 (ruoli puri, niente I/O)**: `vitruvyan_core/core/governance/vault_keepers/`
  - Consumers: `consumers/guardian.py`, `consumers/sentinel.py`, `consumers/archivist.py`, `consumers/chamberlain.py`, `consumers/signal_archivist.py`
  - Oggetti dominio: `domain/vault_objects.py`, `domain/signal_archive.py`
  - Schema eventi: `events/vault_events.py`
  - Esempi: `examples/*`
- **LIVELLO 2 (service + adapters)**: `services/api_vault_keepers/`

## Ruoli e responsabilità

- Ogni consumer implementa `VaultRole` (`consumers/base.py`)
- `process()` non deve fare I/O (il service layer esegue il piano)

> Nota: alcuni ruoli generano ID/timestamp (`*_id = f"...{utcnow()}"`) per tracciabilità. L’output è quindi **unico**, non strettamente deterministico byte-per-byte.

---

## Agenti / Consumers

### `Guardian` — orchestratore operazioni (piano di routing)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/guardian.py`
- Funzioni:
  - decide quali ruoli invocare in base a `event_type`/`operation` e priorità
  - decide sequenza e se serve approvazione (`requires_approval`)

**Dettagli implementativi**:

- Pianifica in base a keyword:
  - integrity → `roles_to_invoke=["sentinel"]`, `sequence="single"`
  - backup → opzionalmente `sentinel` prima per `high|critical`, poi `archivist` + `chamberlain`
  - restore → `sentinel` + `chamberlain`, approvazione quando `dry_run=false`
  - archive → `archivist` + `chamberlain`
- Output: dict con `operation`, `roles_to_invoke`, `sequence`, `requires_approval`, `correlation_id`, `timestamp`

### `Sentinel` — validatore integrità (health → report)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/sentinel.py`
- Funzioni:
  - giudica stato Postgres/Qdrant + coerenza (dati forniti dal service)
  - produce `IntegrityReport` con `overall_status` (`sacred`, `blessed_with_concerns`, `corruption_detected`)

**Dettagli implementativi**:

- Input atteso:
  - `postgresql.status` e `qdrant.status` (`healthy|degraded|corrupted|unreachable`)
  - `coherence.status` (`coherent|drift_detected|critical`)
- Giudizio:
  - datastore corrotto/non raggiungibile o `coherence=critical` → `corruption_detected`
  - tutti healthy + coherent → `sacred`
  - altrimenti → `blessed_with_concerns`

### `Archivist` — pianificazione backup + archivio (solo plan)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/archivist.py`
- Funzioni:
  - pianifica backup (`VaultSnapshot`)
  - pianifica archiviazione (`ArchiveMetadata`)

**Dettagli implementativi**:

- `operation="backup"`:
  - decide `scope` da `mode` + `include_vectors`
  - ritorna `VaultSnapshot` con path pianificati sotto `/var/vitruvyan/vaults/`
- `operation="archive"`:
  - ritorna `ArchiveMetadata` con path sotto `/var/vitruvyan/vaults/archives/`
  - retention di default: 30 giorni

### `Chamberlain` — audit trail (solo record)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/chamberlain.py`
- Funzioni:
  - costruisce `AuditRecord` immutabili per operazioni di vault
  - niente persistenza: scrive il service layer

**Dettagli implementativi**:

- `record_id`: `audit_<timestamp>`
- metadata normalizzato in `tuple((k, str(v)), ...)` + tuple standard:
  - `("warden", "vault_keepers")`, `("priority", ...)`, `("scope", ...)`

### `SignalArchivist` — archiviazione timeseries segnali Babel (domain-agnostic)

- File: `vitruvyan_core/core/governance/vault_keepers/consumers/signal_archivist.py`
- Funzioni:
  - converte risultati di estrazione segnali in `SignalTimeseries`
  - tracciabilità tramite `extraction_method` e `source_text_hash`
  - supporta verticali (`finance`, `cybersecurity`, `healthcare`, …)

**Dettagli implementativi**:

- Valida:
  - `entity_id` obbligatorio
  - `signal_results` non vuoto
  - tutti i `signal_results` dovrebbero condividere un solo `signal_name`
- Costruisce `SignalDataPoint`:
  - `timestamp` da `extraction_trace.timestamp` (fallback `utcnow()`)
  - `source_text_hash = sha256(source_text)[:16]` (opzionale)
- Ordina i punti per timestamp prima di ritornare
