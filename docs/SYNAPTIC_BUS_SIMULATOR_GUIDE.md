# 🧠 Synaptic Bus Dashboard Simulator — User Guide

## Overview
Il **Synaptic Bus Simulator** genera traffico realistico di eventi attraverso tutti i Sacred Orders per popolare la Grafana dashboard con dati live e vivaci.

---

## Quick Start

### Modalità 1: Script Bash (Raccomandato)
```bash
# 5 minuti, media intensità (default)
./scripts/run_dashboard_simulator.sh

# 10 minuti, alta intensità
./scripts/run_dashboard_simulator.sh -d 600 -i high

# Continuo, intensità estrema (Ctrl+C per fermare)
./scripts/run_dashboard_simulator.sh -c -i extreme
```

### Modalità 2: Direttamente in Docker
```bash
# Test veloce 1 minuto
docker exec core_memory_orders python3 /tmp/synaptic_bus_simulator.py \
  --redis-host core_redis \
  --redis-port 6379 \
  --duration 60 \
  --intensity medium

# Background continuo (attualmente in esecuzione!)
docker exec core_memory_orders sh -c "nohup python3 /tmp/synaptic_bus_simulator.py \
  --redis-host core_redis \
  --redis-port 6379 \
  --continuous \
  --intensity high > /tmp/simulator.log 2>&1 &"
```

---

## Profili di Intensità

| Intensità | Eventi/Min | Burst | Descrizione |
|-----------|-----------|-------|-------------|
| **low**   | 10        | 10% chance, 2x | Traffico leggero, ideale per test |
| **medium** | 60       | 20% chance, 3x | Traffico normale, bilanciato |
| **high**  | 200       | 30% chance, 5x | **Attualmente attivo**: Alta densità, burst frequenti |
| **extreme** | 500     | 50% chance, 10x | Stress test, massimo carico |

---

## Verifiche Live

### 1. Verifica Simulator Attivo
```bash
# Controlla log (dovresti vedere 💥 BURST messages)
docker exec core_memory_orders tail -f /tmp/simulator.log

# Controlla processi
docker exec core_memory_orders ps aux | grep python
```

### 2. Verifica Stream Redis
```bash
# Stream lengths (dovrebbero crescere rapidamente)
curl -s "http://localhost:15000/api/v1/query?query=stream_length" | \
  jq -r '.data.result[] | "\(.metric.stream): \(.value[1])"' | \
  sort -t: -k2 -nr | head -10

# Output atteso (numeri in crescita):
# memory.coherence.requested: 68
# codex.discovery.mapped: 64
# neural_engine.screening.completed: 63
```

### 3. Dashboard Grafana
**URL**: http://localhost:3000/d/synaptic-bus-eeg  
**Login**: admin / vitruvyan_admin

**Pannelli popolati** (refresh automatico ogni 10s):
- ⚡ **Cognitive EEG**: Grafico time series con picchi e burst
- 🕸️ **Micelial Network**: Node graph con connessioni attive
- 📊 **Polypo Matrix**: Tabella lag/pending per consumer group
- 🔋 **Stability Index**: Gauge con metriche aggregate
- 📈 **Stream Integrity**: Stat counters in crescita
- 🎯 **Capacity**: Bar gauge per stream lengths
- 🏆 **Top Streams**: Classifica eventi pubblicati
- 🐌 **Slowest Consumers**: Consumer lag ranking

---

## Fermata Simulatore

### Opzione 1: Graceful Stop (se lanciato con script bash)
```bash
# Premi Ctrl+C nel terminale dove hai lanciato run_dashboard_simulator.sh
```

### Opzione 2: Kill processo Docker
```bash
# Trova PID del simulatore
docker exec core_memory_orders ps aux | grep synaptic_bus_simulator

# Kill processo (sostituisci <PID> con il numero del processo)
docker exec core_memory_orders kill <PID>

# Oppure killa tutti i processi Python (attenzione!)
docker exec core_memory_orders pkill -f synaptic_bus_simulator
```

### Opzione 3: Restart container
```bash
cd infrastructure/docker
docker compose restart memory_orders
```

---

## Metriche Esportate

Il **Redis Streams Exporter** (`core_redis_streams_exporter`) espone:

| Metrica | Tipo | Descrizione |
|---------|------|-------------|
| `stream_length` | Gauge | Numero totale messaggi in stream |
| `stream_consumer_lag` | Gauge | Lag tra stream head e consumer read position |
| `stream_pending_messages` | Gauge | Messaggi unacknowledged (PEL size) |
| `cognitive_bus_events_total` | Counter | Eventi pubblicati per channel |
| `listener_consumed_total` | Counter | Eventi consumati per consumer group |

**Endpoint**: http://localhost:9122/metrics  
**Health**: http://localhost:9122/health

---

## Troubleshooting

### Dashboard mostra ancora "No data"
1. **Verifica Prometheus scraping**:
   ```bash
   curl -s "http://localhost:15000/api/v1/targets" | \
     jq -r '.data.activeTargets[] | select(.job=="redis_streams") | .health'
   # Output atteso: "up"
   ```

2. **Verifica exporter metriche**:
   ```bash
   curl -s http://localhost:9122/metrics | grep stream_length | head -5
   # Dovrebbe mostrare stream_length{stream="..."} X.0
   ```

3. **Restart Grafana** per ricaricare le query:
   ```bash
   cd infrastructure/docker
   docker compose restart grafana
   ```

### Simulator non genera eventi
1. **Controlla Redis connection**:
   ```bash
   docker exec core_redis redis-cli PING
   # Output atteso: PONG
   ```

2. **Controlli dipendenze** nel container:
   ```bash
   docker exec core_memory_orders python3 -c "import redis; print('OK')"
   # Output atteso: OK
   ```

3. **Riesegui simulator** con verbose mode:
   ```bash
   docker exec core_memory_orders python3 /tmp/synaptic_bus_simulator.py \
     --redis-host core_redis \
     --redis-port 6379 \
     --duration 30 \
     --intensity low \
     --verbose
   ```

### Stream lengths non crescono
1. **Verifica maxlen policy**: Gli stream hanno `maxlen=10000` (automatic eviction)
2. **Controlla consumer groups**: Se i consumer processano velocemente, i messaggi vengono ACKnowledged e rimossi
3. **Aumenta intensità**: Usa `--intensity extreme` per saturare il sistema

---

## Stato Corrente (Feb 11, 2026 - 10:38 UTC)

✅ **Simulator attivo**: HIGH intensity (200 events/min, burst 5x)  
✅ **Redis Streams Exporter**: Deployed on port 9122  
✅ **Prometheus scraping**: 15s interval, redis_streams job active  
✅ **Grafana dashboard**: Synaptic Bus EEG (uid: synaptic-bus-eeg)  
✅ **Stream counts**: 60+ eventi per stream (crescita continua)

**Per visualizzare la dashboard**: http://localhost:3000/d/synaptic-bus-eeg

---

## Architettura

```
┌─────────────────────┐
│  Simulator Script   │ (synaptic_bus_simulator.py)
│  in Memory Orders   │
│  Container          │
└──────────┬──────────┘
           │ XADD events
           ▼
┌─────────────────────┐
│   Redis Streams     │ (52+ streams)
│   (core_redis)      │
└──────────┬──────────┘
           │ XINFO STREAM
           ▼
┌─────────────────────┐
│ Redis Streams       │ (port 9122)
│ Exporter            │
└──────────┬──────────┘
           │ /metrics endpoint
           ▼
┌─────────────────────┐
│   Prometheus        │ (scrape every 15s)
│   (port 15000)      │
└──────────┬──────────┘
           │ PromQL queries
           ▼
┌─────────────────────┐
│  Grafana Dashboard  │ (refresh every 10s)
│  (port 3000)        │
└─────────────────────┘
```

---

## Next Steps

1. **Personalizza burst patterns**: Modifica `ALL_EVENT_TEMPLATES` in `synaptic_bus_simulator.py`
2. **Aggiungi consumer simulation**: Crea consumer che processano eventi per simulare `listener_consumed_total`
3. **Custom dashboards**: Clona `synaptic_bus_eeg.json` e crea visualizzazioni custom
4. **Alert testing**: Triggera alert modificando intensità (e.g., `extreme` per SynapticBusPendingOverflow)

**Happy monitoring!** 🚀
