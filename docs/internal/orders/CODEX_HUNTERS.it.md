# Codex Hunters

<p class="kb-subtitle">Discovery, normalizzazione, deduplica e binding “storage-ready” di payload grezzi.</p>

## A cosa serve

- **Gestisce la discovery**: valida richieste e mappa payload grezzi in oggetti dominio
- **Normalizza e valuta qualità**: pulisce i dati e produce segnali di qualità
- **Prepara la persistenza**: dedupe keys + storage refs/payload (il service esegue l’I/O)
- **Ispeziona coerenza**: calcola report di allineamento cross-store da count/ID (solo planning)

Codex Hunters è l’ordine di **data acquisition e canonicalizzazione**: trasforma payload grezzi in **entità deterministiche, deduplicate e pronte per la persistenza**.

> Questa pagina documenta **l’implementazione attuale** (consumer LIVELLO 1 + ciò che il LIVELLO 2 orchestri attorno).

## Mappa del codice

- **LIVELLO 1 (dominio puro, niente I/O)**: `vitruvyan_core/core/governance/codex_hunters/`
  - Consumers: `consumers/tracker.py`, `consumers/restorer.py`, `consumers/binder.py`, `consumers/inspector.py`
  - Modello dominio: `domain/entities.py`, `domain/config.py`
  - Esempi: `examples/*_example.py`
- **LIVELLO 2 (service + adapters + bus + persistenza)**: `services/api_codex_hunters/`
  - Orchestrazione bus: `adapters/bus_adapter.py`
  - API: `api/routes.py`
  - Listener Streams: `streams_listener.py`

## Oggetti dominio (cosa passa nella pipeline)

- `DiscoveredEntity` → prodotto dal Tracker (`status=discovered`)
- `RestoredEntity` → prodotto dal Restorer (`status=restored`)
- `BoundEntity` → prodotto dal Binder (`status=bound`)

## Pipeline (concettuale)

1. **Tracker** valida la richiesta di discovery e costruisce un `DiscoveredEntity`
2. **Restorer** normalizza e calcola un quality score producendo un `RestoredEntity`
3. **Binder** “lega” l’entità a riferimenti di storage e produce un `BoundEntity`
4. **Inspector** *(opzionale)* ispeziona coerenza cross-store da count/ID e produce un `InspectionReport`

Il livello service esegue l’I/O (Postgres/Qdrant, emissione bus, rate limiting).

---

## Agenti / Consumers

### `TrackerConsumer` — discovery + validazione

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py`
- Funzioni:
  - valida input (`entity_id`, `source`)
  - valida che `source` esista in `CodexConfig.sources`
  - crea `DiscoveredEntity`
  - calcola una dedupe key **deterministica** basata su `entity_id + source + hash(raw_data)`
- Nota:
  - `prepare_discovery_config()` produce metadati di rate limit per l’adapter (il consumer non applica rate limiting)
  - `validate_entity_id()` è volutamente permissivo (il verticale può renderlo più restrittivo)

**Dettagli implementativi**:

- `dedupe_key`:
  - hash di `raw_data` via `json.dumps(sort_keys=True)` → `sha256` (prime 8 cifre)
  - poi hash di `f"{entity_id}:{source}:{data_hash}"` → `sha256` (prime 16 cifre)
- `DiscoveredEntity.metadata` include `record_count` e `has_data`

### `RestorerConsumer` — normalizzazione + quality scoring

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py`
- Funzioni:
  - normalizza i dati (default: “clean” delle chiavi + normalizzazione nested)
  - valida struttura (es. dati vuoti, ratio di null elevata)
  - calcola `quality_score` con penalità guidate da config
  - produce `RestoredEntity`
- Estendibilità:
  - normalizzatori per-source registrabili (verticalizzazione)

**Dettagli implementativi**:

- Normalizzazione di default:
  - normalizza le chiavi (`lower()`, spazi e `-` → `_`)
  - normalizza ricorsivamente dict/list annidati
  - aggiunge `_normalized_at` (timestamp ISO)
- Validazione (default):
  - payload normalizzato vuoto → errore
  - “high null ratio” (> 0.5) → errore
- Quality score:
  - parte da `1.0`
  - sottrae `len(errori) * config.quality.penalty_per_error`
  - sottrae `null_ratio * config.quality.penalty_null_ratio`
  - clamp su `[0.0, 1.0]`

### `BinderConsumer` — binding + payload (ancora puro)

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py`
- Funzioni:
  - genera `dedupe_key` deterministica sul payload normalizzato
  - prepara storage refs (tabella/collection da config)
  - genera `embedding_id` se è presente un embedding
  - produce `BoundEntity` + dati necessari al LIVELLO 2

**Output effettivo (process)**:

- `data["bound_entity"] = BoundEntity`
- `data["normalized_data"] = dict`
- `data["embedding"] = list[float] | None`
- `data["quality_score"] = float`
- `data["dedupe_key"] = str`

**Dettagli implementativi**:

- `dedupe_key` fa hash di `json.dumps(normalized_data, sort_keys=True)` (prime 32 cifre hex)
- `embedding_id` è **unico, non deterministico** (include un timestamp UTC)
- Esistono helper per payload provider (`_prepare_postgres_payload`, `_prepare_qdrant_payload`), ma `process()` non li ritorna oggi.

---

## Orchestrazione service (LIVELLO 2)

### `BusAdapter`

- File: `services/api_codex_hunters/adapters/bus_adapter.py`
- Funzioni:
  - lazy-load dei consumer LIVELLO 1
  - emissione eventi su `StreamBus` (se disponibile)
  - delega della persistenza all’adapter dedicato

## Verticalizzazione (finanza, pilota)

Codex Hunters è domain-agnostic. Il verticale finanza definisce:

- il significato di `entity_id` (es. ticker)
- sources/tables/namespaces stream
- normalizzatori opzionali (service layer)

Riferimento: `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

## Note implementative (caveat attuali)

- Il `_normalized_at` di default rende `normalized_data` **non deterministico**.
  - Se usi `dedupe_key` del Binder per dedup reale, conviene rimuovere `_normalized_at` (o spostarlo in metadata) nel service/verticale.

---

### `InspectorConsumer` — ispezione coerenza cross-store (puro)

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/inspector.py`
- Funzioni:
  - valuta la coerenza tra due store “specchiati” (es. Postgres ↔ Qdrant) **a partire da count/ID forniti**
  - rileva orfani (ID presenti in A ma non in B, e viceversa)
  - classifica lo stato (`excellent`/`good`/`poor`/`critical`) via soglie
  - produce `InspectionReport` con `overall_score`, score per-collection e hint `needs_healing`
- Input (atteso):
  - `collections: list[{collection_name, source_a_count, source_b_count, source_a_ids?, source_b_ids?}]`
- Output:
  - `data["report"] = InspectionReport`
  - `data["report_dict"] = dict` (JSON-friendly)

> Nota: oggi il service Codex Hunters (`services/api_codex_hunters/`) non espone ancora un endpoint HTTP per inspection. Gli adapter LIVELLO 2 dovrebbero chiamare InspectorConsumer quando serve governance di coerenza.
