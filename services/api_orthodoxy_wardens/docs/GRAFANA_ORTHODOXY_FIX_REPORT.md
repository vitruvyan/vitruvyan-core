# Risoluzione Problemi Grafana & Orthodoxy Wardens — Feb 11, 2026

## ✅ Problemi Risolti

### 1. Accesso Grafana
**Problema**: Credenziali di default non funzionavano  
**Causa**: Password amministratore era stata modificata o corrotta  
**Soluzione**: Reset password usando `grafana cli admin reset-admin-password`

**Credenziali Aggiornate**:
- **URL**: http://localhost:3000
- **Username**: `admin`
- **Password**: `vitruvyan_admin`
- **Dashboard principale**: http://localhost:3000/d/synaptic-bus-eeg/synaptic-bus-eeg

### 2. Endpoint Metrics per Orthodoxy Wardens
**Problema**: Orthodoxy Wardens restituiva 404 su `/metrics`  
**Causa**: Endpoint Prometheus non implementato  
**Soluzione**: Aggiunto `/metrics` endpoint seguendo il pattern di Memory Orders

#### Modifiche Implementate

**File**: `services/api_orthodoxy_wardens/monitoring/health.py`
- Aggiunto import `prometheus_client` (Counter, Gauge, Histogram, generate_latest)
- Importate definizioni metriche da `core.governance.orthodoxy_wardens.monitoring.metrics`
- Creati collectors Prometheus:
  - `confessions_received_counter`
  - `examinations_total_counter`
  - `examinations_duration_histogram`
  - `findings_total_counter`
  - `verdicts_total_counter`
  - `surveillance_cycles_counter`
  - `orthodoxy_health_status` (Gauge)
- Aggiunta funzione `async def metrics_endpoint()`

**File**: `services/api_orthodoxy_wardens/main.py`
- Aggiunto import `metrics_endpoint` da monitoring.health
- Aggiunto endpoint FastAPI:
  ```python
  @app.get("/metrics")
  async def prometheus_metrics():
      return await metrics_endpoint()
  ```

#### Metriche Esposte

```bash
$ curl -s http://localhost:9006/metrics | grep "orthodoxy_"
```

**Output** (esempio):
```
# HELP orthodoxy_confessions_received_total Total confessions received by Orthodoxy Wardens
# TYPE orthodoxy_confessions_received_total counter
orthodoxy_confessions_received_total 0.0

# HELP orthodoxy_examinations_total Total examinations conducted
# TYPE orthodoxy_examinations_total counter
orthodoxy_examinations_total 0.0

# HELP orthodoxy_examinations_duration_seconds Duration of examinations in seconds
# TYPE orthodoxy_examinations_duration_seconds histogram
orthodoxy_examinations_duration_seconds_bucket{le="0.005"} 0.0
...

# HELP orthodoxy_findings_total Total findings discovered
# TYPE orthodoxy_findings_total counter
orthodoxy_findings_total 0.0

# HELP orthodoxy_verdicts_total Total verdicts issued
# TYPE orthodoxy_verdicts_total counter
orthodoxy_verdicts_total 0.0

# HELP orthodoxy_surveillance_cycles_total Total surveillance cycles executed
# TYPE orthodoxy_surveillance_cycles_total counter
orthodoxy_surveillance_cycles_total 0.0

# HELP orthodoxy_health_status Overall health status (0=down, 1=degraded, 2=healthy)
# TYPE orthodoxy_health_status gauge
orthodoxy_health_status 2.0
```

---

## 🎯 Stato Attuale del Sistema

### Prometheus Scraping Status
**Tutti i 6 Sacred Orders monitorati e OPERATIVI**:

```json
[
  {"job": "babel_gardens", "health": "up"},
  {"job": "codex_hunters", "health": "up"},
  {"job": "memory_orders", "health": "up"},
  {"job": "orthodoxy_wardens", "health": "up"},
  {"job": "pattern_weavers", "health": "up"},
  {"job": "vault_keepers", "health": "up"}
]
```

**Coverage**: 100% (6/6 Sacred Orders)

### Configurazione Prometheus
**File**: `infrastructure/docker/monitoring/prometheus.yml`

```yaml
- job_name: 'orthodoxy_wardens'
  static_configs:
    - targets: ['core_orthodoxy_wardens:8006']
  metrics_path: /metrics
```

**Note**: Tutti i target usano `container_name` (core_*) invece di service name per la risoluzione DNS corretta in Docker.

### Verifiche Eseguite

1. **Endpoint accessibile**:
   ```bash
   $ curl -s http://localhost:9006/metrics | head -5
   # HELP python_gc_objects_collected_total Objects collected during gc
   # TYPE python_gc_objects_collected_total counter
   python_gc_objects_collected_total{generation="0"} 25072.0
   ...
   ```

2. **Prometheus target UP**:
   ```bash
   $ curl -s 'http://localhost:15000/api/v1/targets' | jq '.data.activeTargets[] | select(.labels.job == "orthodoxy_wardens")'
   {
     "health": "up",
     "lastError": ""
   }
   ```

3. **Metriche in Prometheus**:
   ```bash
   $ curl -s 'http://localhost:15000/api/v1/query' --data-urlencode 'query=orthodoxy_health_status'
   {
     "metric": "orthodoxy_health_status",
     "value": "2"
   }
   ```

4. **Grafana accessibile**:
   ```bash
   $ curl -s -u admin:vitruvyan_admin 'http://localhost:3000/api/dashboards/uid/synaptic-bus-eeg'
   {
     "dashboard": {
       "title": "Synaptic Bus EEG",
       ...
     }
   }
   ```

---

## 📊 Dashboard Grafana — Synaptic Bus EEG

**URL**: http://localhost:3000/d/synaptic-bus-eeg/synaptic-bus-eeg  
**Credenziali**: `admin` / `vitruvyan_admin`

**Panels aggiornati** per includere Orthodoxy Wardens:
- ⚡ Cognitive EEG: Visualizza eventi publish/consume (include orthodoxy_wardens)
- 🧠 Polypo Matrix: Mostra lag consumer group (include group:orthodoxy_wardens)
- 🕸️ Micelial Network: Topologia Sacred Orders (include nodo Orthodoxy)
- ⚖️ Cognitive Stability Index: Ratio globale consume/publish
- 📊 Stream Integrity: Pending messages
- 📈 Stream Capacity: Fill levels
- 🔥 Top 10 Hottest Streams
- ⏳ Slowest Consumer Groups

**Alert Rules**: 8 regole attive (synaptic_bus_alerts.yml)

---

## 🔧 Comandi Utili

### Reset Password Grafana
```bash
docker exec core_grafana grafana cli admin reset-admin-password <nuova_password>
```

### Verificare Metriche Orthodoxy
```bash
curl -s http://localhost:9006/metrics | grep "orthodoxy_"
```

### Verificare Scraping Prometheus
```bash
curl -s 'http://localhost:15000/api/v1/targets' | jq '.data.activeTargets[] | select(.labels.job == "orthodoxy_wardens")'
```

### Query Metriche in Prometheus
```bash
curl -s 'http://localhost:15000/api/v1/query' --data-urlencode 'query=orthodoxy_health_status'
```

### Riavviare Orthodoxy Wardens
```bash
cd infrastructure/docker
docker compose restart orthodoxy_wardens
```

### Ricredere Container (forza reload)
```bash
cd infrastructure/docker
docker compose stop orthodoxy_wardens
docker compose rm -f orthodoxy_wardens
docker compose up -d orthodoxy_wardens
```

---

## 📚 Riferimenti

- [GRAFANA_DASHBOARD_VALIDATION_REPORT.md](GRAFANA_DASHBOARD_VALIDATION_REPORT.md) — Deployment & troubleshooting
- [SYNAPTIC_BUS_DASHBOARD_GUIDE.md](SYNAPTIC_BUS_DASHBOARD_GUIDE.md) — User guide per dashboard
- [services/api_orthodoxy_wardens/monitoring/health.py](services/api_orthodoxy_wardens/monitoring/health.py) — Metrics implementation
- [vitruvyan_core/core/governance/orthodoxy_wardens/monitoring/metrics.py](vitruvyan_core/core/governance/orthodoxy_wardens/monitoring/metrics.py) — Metric definitions

---

**Risolto da**: GitHub Copilot (Claude Sonnet 4.5)  
**Data**: Febbraio 11, 2026  
**Status**: ✅ Tutti i problemi risolti, monitoring al 100%
