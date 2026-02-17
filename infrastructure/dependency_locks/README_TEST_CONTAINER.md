# LangGraph 1.x Isolated Test Container

> **Last updated**: 16 Febbraio 2026

Questo directory contiene il setup per testare **LangGraph 1.0.8** in un container isolato, senza impattare la produzione (LangGraph 0.5.4).

## Purpose
- Testare LangGraph 1.x compatibility e behavior in modo sicuro
- Comparare con produzione (0.5.4) in ambiente controllato
- Rollback immediato se si riscontrano problemi

## Status Attuale

✅ **BUILD COMPLETATO** - Container pronto per testing

| Componente | Status | Note |
|------------|--------|------|
| **Immagine Docker** | ✅ Creata | 8.12 GB (include PyTorch) |
| **LangGraph** | ✅ 1.0.8 | Upgrade da 0.5.4 |
| **Dipendenze** | ✅ Risolte | alembic, checkpoint 4.0.0, prebuilt 1.0.7, sdk 0.3.6 |
| **Porta** | ✅ 9099 | Fix conflitto con embedding (era 9010) |

## Files
- `Dockerfile.api_graph_test`: Dockerfile per test container (LangGraph 1.0.8 + alembic)
- `requirements_graph_0_5_4_freeze.txt`: Freeze dipendenze produzione (rollback anchor)
- `test_langgraph_1_0_8.sh`: **Script automatico di validazione completa**
- `README_TEST_CONTAINER.md`: Questa documentazione

## Modifiche Applicate (16 Feb 2026)

### 1. Fix Conflitto Porta
```yaml
# docker-compose.yml - PRIMA
ports:
  - "9010:8010"  # ❌ Conflitto con core_embedding

# docker-compose.yml - DOPO
ports:
  - "9099:8010"  # ✅ Porta dedicata per test
```

### 2. Fix Dipendenza Mancante
```dockerfile
# Dockerfile.api_graph_test - PRIMA
RUN pip install -r requirements-graph-freeze.txt && \
    pip install langgraph==1.0.8

# Dockerfile.api_graph_test - DOPO
RUN pip install -r requirements-graph-freeze.txt && \
    pip install langgraph==1.0.8 && \
    pip install alembic>=1.13.0  # ✅ Fix ModuleNotFoundError
```

## Usage

### Metodo 1: Script Automatico (RACCOMANDATO)

```bash
cd /home/vitruvyan/vitruvyan-core
./infrastructure/dependency_locks/test_langgraph_1_0_8.sh
```

Lo script esegue automaticamente:
1. ✅ Verifica immagine Docker
2. ✅ Rimuove container precedente
3. ✅ Avvia container di test
4. ✅ Attende startup (15 secondi)
5. ✅ Verifica logs
6. ✅ Test health endpoint (`http://localhost:9099/health`)
7. ✅ Verifica versione LangGraph (1.0.8)
8. ✅ Test dispatch endpoint (opzionale)
9. ✅ Riepilogo risultati

### Metodo 2: Comandi Manuali

#### 1. Build Test Container (se non già fatto)
```bash
cd /home/vitruvyan/vitruvyan-core
docker compose -f infrastructure/docker/docker-compose.yml build vitruvyan_api_graph_test
```

#### 2. Avvia Test Container
```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d vitruvyan_api_graph_test
```

Il test container:
- Porta: **9010** (vs produzione 9005) - **AGGIORNATO A 9099**
- Nome: `core_graph_test`
- Network: `core-net` (condiviso con produzione)
- Dipendenze: Redis, PostgreSQL, Qdrant (stessa infra)

#### 3. Verifica Logs
```bash
docker logs core_graph_test --tail=50 -f
```

#### 4. Test Health Endpoint
```bash
curl http://localhost:9099/health
```

**Risposta attesa**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-16T22:XX:XX",
  "components": {
    "postgres": "healthy",
    "redis": "healthy",
    "langgraph": "1.0.8"
  }
}
```

#### 5. Test Dispatch (Opzionale)
```bash
curl -X POST http://localhost:9099/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test langgraph upgrade",
    "validated_entities": []
  }'
```

#### 6. Verifica Versione LangGraph
```bash
docker exec core_graph_test pip list | grep langgraph
```

**Output atteso**:
```
langgraph                1.0.8
langgraph-checkpoint     4.0.0
langgraph-prebuilt       1.0.7
langgraph-sdk            0.3.6
```

### 4. Comparazione con Produzione

| Aspetto | Produzione (9005) | Test (9099) |
|---------|------------------|------------|
| **LangGraph** | 0.5.4 | **1.0.8** |
| **checkpoint** | 2.1.2 | **4.0.0** |
| **prebuilt** | 0.5.2 | **1.0.7** |
| **sdk** | 0.1.74 | **0.3.6** |
| **Porta** | 9005 | 9099 |
| **Container** | core_graph | core_graph_test |

### 5. Rollback
Se test fallisce o comportamento inatteso:

```bash
# Stop test container
docker compose -f infrastructure/docker/docker-compose.yml down vitruvyan_api_graph_test

# (Produzione rimane inalterata su porta 9005 con LangGraph 0.5.4)
```

## Troubleshooting

### Problema: Container non si avvia
**Sintomo**: `docker ps` mostra status "Exited" o "Restarting"

**Soluzione**:
```bash
# Verifica logs errore
docker logs core_graph_test --tail=100

# Verifica dipendenze mancanti
docker exec core_graph_test pip check
```

### Problema: ModuleNotFoundError
**Sintomo**: Errore import modulo Python nei logs

**Soluzione**: Rebuild immagine (dipendenze aggiornate nel Dockerfile)
```bash
docker compose build --no-cache vitruvyan_api_graph_test
docker compose up -d vitruvyan_api_graph_test
```

### Problema: Conflitto porta 9099
**Sintomo**: "port is already allocated"

**Soluzione**: Verifica servizio occupante porta
```bash
# Identifica processo su porta 9099
sudo lsof -i :9099

# O cambia porta in docker-compose.yml
ports:
  - "9100:8010"  # Usa porta alternativa
```

### Problema: Health check fallisce
**Sintomo**: `curl http://localhost:9099/health` → timeout o 503

**Diagnosi**:
```bash
# 1. Verifica container in running
docker ps | grep graph_test

# 2. Verifica logs startup
docker logs core_graph_test --tail=50

# 3. Verifica connessione PostgreSQL/Redis
docker exec core_graph_test env | grep -E "(POSTGRES|REDIS)"

# 4. Test interno container
docker exec core_graph_test curl -f http://localhost:8010/health
```

## Notes
- **Non modificare** container produzione durante testing
- Tutti i cambiamenti sono isolati nel test container
- Produzione (core_graph, porta 9005) **non è impattata**
- Per documentazione completa: `docs/LANGGRAPH_UPGRADE_REPORT_FEB16_2026.md`

## Next Steps After Validation

Se test OK:
1. Leggere changelog LangGraph 0.5.4 → 1.0.8
2. Eseguire test suite completa (`pytest tests/test_orchestration*.py`)
3. Decidere timeline upgrade produzione
4. Aggiornare `requirements-graph.txt` e freeze file
5. Deploy graduale (canary/blue-green)

## References
- **LangGraph Release Notes**: https://github.com/langchain-ai/langgraph/releases
- **Full Technical Report**: `docs/LANGGRAPH_UPGRADE_REPORT_FEB16_2026.md`
- **Copilot Instructions**: `.github/copilot-instructions.md`
