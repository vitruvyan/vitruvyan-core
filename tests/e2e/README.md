# Test End-to-End (`tests/e2e/`)

## Scopo

I test end-to-end (E2E) verificano il funzionamento del sistema completo
con **infrastruttura reale**: PostgreSQL, Qdrant, Redis Streams, API HTTP.

## ⚠️ Prerequisiti

Questi test richiedono lo stack Docker operativo:

```bash
cd infrastructure/docker
docker compose up -d postgres qdrant redis embedding_api
```

Variabili d'ambiente necessarie:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `QDRANT_HOST`, `QDRANT_PORT`
- `REDIS_HOST`, `REDIS_PORT`
- `EMBEDDING_API_URL`

## Stato attuale

**Placeholder** — nessun test E2E implementato.

I test E2E saranno aggiunti dopo che lo stack Docker sia stabile e
i test unitari e di integrazione siano completi al 100%.

## Scenari futuri pianificati

| Scenario | Descrizione |
|----------|-------------|
| `test_graph_pipeline_e2e.py` | Input utente → LangGraph → risposta completa |
| `test_streaming_e2e.py` | Evento StreamBus → consumer → persistence |
| `test_sacred_order_e2e.py` | API Sacred Order → health check → risposta |
| `test_vpar_with_qdrant.py` | VSGS con embedding reale + Qdrant |

## Esecuzione

```bash
# Solo test E2E (richiede Docker stack attivo)
pytest tests/e2e/ -m e2e -v --tb=long

# Escludere E2E da run normali
pytest tests/ -m "not e2e" -v
```

## Marker

Tutti i test E2E devono usare:
```python
@pytest.mark.e2e
@pytest.mark.slow
```
