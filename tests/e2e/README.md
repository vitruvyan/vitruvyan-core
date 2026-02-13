# Test End-to-End (`tests/e2e/`)

## Scopo

I test end-to-end (E2E) verificano il funzionamento del **sistema completo**
con infrastruttura reale: PostgreSQL, Qdrant, Redis Streams, API HTTP e tutti
i microservizi Docker. Coprono l'intero percorso dati — dall'input utente
fino alla risposta finale — inclusi bus eventi, persistence e Sacred Orders.

## Stato attuale

**143 test — 100% pass** (Feb 13, 2026)

| Modulo | Test | Copertura |
|--------|-----:|-----------|
| `test_conversational_pipeline.py` | 25 | LangGraph `/run`, intent detection, routing, Orthodoxy, Vault, CAN, VSGS |
| `test_postgres_logging.py` | 16 | Tabelle, schemi, graph-writes, isolamento connessioni |
| `test_qdrant_upsert_search.py` | 12 | Collezioni, embedding, upsert/search, delete |
| `test_bus_event_flow.py` | 14 | Redis Streams, consumer groups, ACK, TransportEvent, CognitiveEvent |
| `test_pattern_weavers_ontology.py` | 16 | `/keyword-match` API, LIVELLO 1 KeywordMatcherConsumer |
| `test_babel_gardens_agnostic.py` | 22 | SynthesisConsumer, TopicClassifierConsumer, LanguageDetectorConsumer |
| `test_neural_engine_computation.py` | 23 | `/screen`, `/rank`, `/profiles`, edge cases, metriche |
| `conftest.py` | — | Fixture condivise (httpx, pg, redis, qdrant, `graph_run`) |

## ⚠️ Prerequisiti

L'intero stack Docker deve essere operativo:

```bash
cd infrastructure/docker
docker compose up -d
```

Servizi richiesti (porte esterne):
- **Graph API** (LangGraph): `localhost:9004`
- **Neural Engine**: `localhost:9003`
- **Babel Gardens**: `localhost:9009`
- **Embedding API**: `localhost:9010`
- **Pattern Weavers**: `localhost:9017`
- **Orthodoxy Wardens**: `localhost:9006`
- **Vault Keepers**: `localhost:9007`
- **PostgreSQL**: `localhost:9432`
- **Redis**: `localhost:9379`
- **Qdrant**: `localhost:9333` (REST) / `localhost:9334` (gRPC)

I test saltano automaticamente (`pytest.skip`) se un servizio non è raggiungibile.

## Esecuzione

```bash
# Intera suite E2E (richiede Docker stack attivo)
PYTHONPATH=vitruvyan_core:$PYTHONPATH pytest tests/e2e/ -m e2e -v --tb=short

# Singolo modulo
PYTHONPATH=vitruvyan_core:$PYTHONPATH pytest tests/e2e/test_conversational_pipeline.py -m e2e -v

# Escludere E2E dai run normali
pytest tests/ -m "not e2e" -v
```

## Architettura dei test

```
conftest.py                         ← Fixture condivise per tutti i moduli
├── http_client                     ← httpx.Client (timeout 30s)
├── graph_api / neural_api / ...    ← URL + skip-se-irraggiungibile
├── pg_conn                         ← psycopg2 (autocommit)
├── redis_client                    ← redis.Redis (decode_responses=True)
├── qdrant_http                     ← Base URL per REST API
├── graph_run(prompt, ...)          ← Helper: chiama /run e parsa JSON annidato
└── e2e_run_id                      ← UUID per isolamento tra run
```

### Principi di design

- **Domain-agnostic**: tutti i test verificano funzionalità OS-level, non finance-specific
- **Skip graceful**: se un servizio è down, il test è skippato (non fallisce)
- **Isolamento**: ogni test usa UUID/nomi univoci per evitare collisioni
- **LIVELLO 1 puro**: i consumer test (Babel, Pattern Weavers) importano Python puro, zero I/O
- **Cleanup**: stream Redis e collection Qdrant vengono rimossi dopo il test

## Marker

Tutti i test E2E devono usare:
```python
@pytest.mark.e2e
@pytest.mark.slow
```
