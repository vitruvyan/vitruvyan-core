# Codex Hunters (Perception / Data Collection)

I **Codex Hunters** sono il sottosistema di **raccolta dati**: un set di agenti (hunters) e un servizio API che coordinano “spedizioni” per **scoprire**, **normalizzare**, **archiviare** e **verificare** dati grezzi provenienti da sorgenti esterne.

## Scopo (domain-agnostic)

- **Expeditions**: eseguire job ripetibili (manuali o schedulati) su collezioni/insiemi di entità.
- **Dual-write opzionale**: persistenza strutturata (es. PostgreSQL) + memoria semantica (es. Qdrant) *quando richiesto dal vertical*.
- **Event-driven**: emettere e consumare eventi sul Cognitive Bus per coordinamento con orchestratori (es. LangGraph) e altri ordini.
- **Observability**: metriche e history delle spedizioni.

## Componenti

### 1) API Service (`api_codex_hunters`)

Servizio FastAPI per:

- trigger spedizioni in background,
- consultare stato e history,
- esporre health/stats/metrics,
- (opzionale) ascoltare eventi dal bus e trasformarli in spedizioni.

**Porta default**: `8008` (`CODEX_API_PORT`).

Endpoint principali (vedi `services/core/api_codex_hunters/main.py`):

- `POST /expedition/run`
- `POST /expedition/trigger/langgraph`
- `GET /expedition/status/{expedition_id}`
- `GET /expedition/history`
- `GET /health`
- `GET /stats`
- `GET /metrics`

Variabili d’ambiente utili:

- `CODEX_API_HOST`, `CODEX_API_PORT`
- `CODEX_API_BASE` (usato dal nodo LangGraph per chiamare l’API)

### 2) Hunters (agent modules)

Pattern consigliato (agnostico):

- `Tracker`: acquisizione da sorgenti esterne
- `Restorer`: normalizzazione/backfill/riparazione di lacune
- `Binder`: archiviazione e deduplica
- `Inspector`: controlli di qualità / integrità
- `Cartographer`: reportistica “mappa consistenza”
- `ExpeditionLeader`: coordinamento multi-agent

> Nota: in questo repo esistono implementazioni storiche nate in un vertical finance; la documentazione core descrive **il pattern**, non il dominio.

## Modello “Expedition”

Una spedizione ha:

- `expedition_type` (es. audit/healing/discovery — definito dal vertical o dall’orchestratore)
- `target_collections` (opzionale)
- `priority`
- `parameters` (payload opaco)
- `correlation_id` (tracing)

Il servizio mantiene uno stato in-memory con progress, agent deployati, risultati, errori.

## Cognitive Bus

Uso tipico:

- consumare eventi “requested” (trigger) e avviare una spedizione;
- emettere eventi “started/completed/failed” per aggiornare l’orchestratore.

Convenzione suggerita (agnostica): `codex.<namespace>.<intent>.<state>` con payload definito dal vertical.

Il servizio include anche un listener “bridge” (opzionale) che può sottoscrivere canali sul bus e tradurli in `expedition/run`.

## Observability

- **Prometheus**: contatori/gauge/istogrammi per numero spedizioni, durata, stato salute del servizio.
- **History**: `GET /expedition/history` per tracciare esecuzioni recenti.

## Stato e migrazione (importante)

La base Codex Hunters in vitruvyan-core è in fase di **de-financializzazione**:

- l’appendix storico (in `.github/`) è una fonte utile per il design, ma contiene contenuti vertical-specific;
- alcune implementazioni/code-path hanno ancora naming e dipendenze legacy.

Per rendere i Codex Hunters “core-grade”, l’obiettivo è:

1. definire un **contratto** minimale per Hunter (input/output/eventi),
2. spostare sorgenti e schema in un vertical/plugin,
3. mantenere nel core solo orchestrazione, tracciamento, bus, e primitive di persistenza generiche.
