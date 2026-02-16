# Fix: Mycelial Network Panel Error
**Date**: February 16, 2026  
**Error**: `id field is required for nodes data frame`  
**Panel**: Mycelial Network — Sacred Orders Topology

---

## 🔴 Problema

Il pannello "Mycelial Network" usa una visualizzazione **Node Graph** che richiede:
- Campo `id` per ogni nodo
- Campi `source` e `target` per le connessioni

Le metriche Prometheus (`stream_connection`, `stream_consumer_lag`) non hanno questa struttura.

---

## ✅ Soluzione Immediata (Raccomandato)

### Opzione 1: Cambiare a Table Visualization

**Passi in Grafana**:

1. **Apri il pannello in Edit**:
   - Click sul titolo "Mycelial Network"
   - Click su "Edit" (icona matita)

2. **Cambia Tipo Visualizzazione**:
   - In alto a destra, clicca sul menu a tendina (attualmente: "Node Graph")
   - Seleziona **"Table"**

3. **Aggiorna Query**:
   ```promql
   # Query 1: Consumer Groups e Stream Associati
   count by (consumer_group, stream) (stream_consumer_lag >= 0)
   ```

4. **Configura Table**:
   - **Columns**: consumer_group, stream, Value
   - **Sort**: By Value (descending)
   - **Filter**: Hide rows where Value = 0

5. **Salva**:
   - Click "Apply" in alto a destra

**Risultato**: Tabella che mostra quali consumer groups consumano da quali stream.

---

### Opzione 2: Stat Panel con Sacred Orders

Se preferisci una visualizzazione grafica, usa **Stat** panels:

1. **Cambia a Stat Visualization**

2. **Query**:
   ```promql
   # Mostra connessioni Sacred Orders -> Sacred Orders
   stream_connection
   ```

3. **Configurazione**:
   - **Graph Mode**: None
   - **Color Mode**: Background
   - **Value**: Last (not null)
   - **Orientation**: Horizontal

**Risultato**: Boxes colorati che mostrano le connessioni tra ordini.

---

### Opzione 3: Bar Chart (Relazioni Visuali)

1. **Cambia a Bar Chart**

2. **Query**:
   ```promql
   # Consumer groups per stream
   count(stream_consumer_lag) by (stream)
   ```

3. **Configurazione**:
   - **Orientation**: Horizontal
   - **Show values**: Always
   - **Stacking**: None

**Risultato**: Bar chart che mostra quanti consumer groups per stream.

---

## 🔬 Opzione Avanzata: Node Graph con Trasformazioni (Complesso)

Se vuoi **mantenere Node Graph**, serve una trasformazione custom:

### Query Modificata (Sperimentale):

```promql
# Nodes (Sacred Orders come nodi)
label_replace(
  sacred_order_activity > 0,
  "id",
  "$1",
  "sacred_order",
  "(.*)"
)
```

**Problema**: Grafana Node Graph richiede trasformazioni che Prometheus non supporta nativamente. Richiede plugin o data transformation in Grafana.

**Steps Avanzati**:
1. Query 1: Nodi (Sacred Orders)
2. Query 2: Connessioni (stream_connection)
3. Aggiungi **Transformation**:
   - Type: "Prepare time series" → "Nodes"
   - Map fields: `sacred_order` → `id`, `Value` → `mainstat`
4. Aggiungi seconda trasformazione per archi

**Raccomandazione**: ❌ Troppo complesso, usa Table (Opzione 1)

---

## 📊 Query Alternative Utili

### Query 1: Top Consumer Groups (by streams consumed)
```promql
count(stream_consumer_lag >= 0) by (consumer_group)
```

### Query 2: Active Stream Connections
```promql
count(stream_consumer_lag{stream=~".*memory.*"}) by (consumer_group)
```

### Query 3: Sacred Order Interconnections
```promql
# Quanti stream di Memory sono consumati da Vault?
count(
  stream_consumer_lag{
    stream=~".*memory.*",
    consumer_group=~".*vault.*"
  }
)
```

### Query 4: Listener Activity Matrix
```promql
# Matrix: Sacred Order (rows) x Consumer Groups (columns)
sum by (sacred_order, consumer_group) (stream_consumer_lag >= 0)
```

---

## 🎯 Soluzione Consigliata (Step by Step)

### **Implementazione Rapida (5 minuti)**

1. **Entra in Edit Mode**:
   ```
   Dashboard → Mycelial Network → Edit
   ```

2. **Cambia Visualization**:
   ```
   Top-right dropdown: Node Graph → Table
   ```

3. **Incolla questa Query**:
   ```promql
   count by (consumer_group, stream) (
     stream_consumer_lag{stream=~"vitruvyan:.*"} >= 0
   )
   ```

4. **Panel Options**:
   - **Title**: "Consumer Groups → Streams Matrix"
   - **Description**: "Shows which consumer groups consume from which streams"

5. **Table Options**:
   - **Show Header**: Yes
   - **Cell Display Mode**: Color background (Blue gradient)
   - **Sortable Columns**: Yes

6. **Apply → Save Dashboard**

---

## 📈 Esempio Output (Table)

| consumer_group | stream | Value |
|----------------|--------|-------|
| group:vault_keepers | vitruvyan:memory.write.completed | 1.0 |
| group:orthodoxy_wardens | vitruvyan:memory.coherence.requested | 1.0 |
| memory_orders_group | vitruvyan:babel.sentiment.completed | 1.0 |
| group:pattern_weavers | vitruvyan:codex.enrichment.completed | 1.0 |

**Interpretazione**: Ogni riga mostra una relazione "Consumer Group → Stream"

---

## 🐛 Se Table non Funziona (Debugging)

### Test 1: Verifica Metrica Disponibile
```bash
curl -s http://localhost:9122/metrics | grep "stream_consumer_lag" | head -5
```

**Expected**: Almeno 10+ righe con consumer groups e stream

### Test 2: Verifica in Grafana Explore
1. Apri **Explore** (menu laterale)
2. Data Source: **Prometheus**
3. Query:
   ```promql
   stream_consumer_lag
   ```
4. Run Query
5. **Expected**: Table con consumer_group, stream, value

### Test 3: Verifica Time Range
- Imposta: **Last 1 hour**
- Refresh: Manual refresh (click reload)

---

## 🔧 Follow-Up: Creare un Vero Node Graph (Futuro)

Per un vero Node Graph servirebbero:

### Opzione A: Exporter Custom
Modificare `redis_streams_exporter.py` per esporre metriche in formato specifico:
```python
# Nodi
node_metric{id="memory", type="sacred_order"} 1
node_metric{id="vault", type="sacred_order"} 1

# Archi
edge_metric{source="memory", target="vault", weight="5"} 1
```

### Opzione B: Grafana Plugin
Usare plugin come **Node Graph API** che supporta query custom

### Opzione C: External Service
Service esterno che trasforma metriche Prometheus in formato Node Graph JSON

**Raccomandazione**: Troppo effort per valore limitato. Table visualization è sufficiente.

---

## ✅ Checklist Post-Fix

- [ ] Pannello non mostra più errore "id field is required"
- [ ] Table mostra consumer groups e stream associati
- [ ] Almeno 8 consumer groups visibili
- [ ] Almeno 20+ stream relationships
- [ ] Dashboard salva senza errori

---

## 📚 Reference

- **Grafana Node Graph Docs**: https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/node-graph/
- **Prometheus Label Matching**: https://prometheus.io/docs/prometheus/latest/querying/basics/#instant-vector-selectors
- **Diagnostics Report**: [docs/GRAFANA_DASHBOARD_DIAGNOSTICS_FEB16_2026.md](GRAFANA_DASHBOARD_DIAGNOSTICS_FEB16_2026.md)

---

**Status**: ✅ Fix Ready  
**Difficulty**: ⭐ Easy (5 minutes)  
**Impact**: 🎯 High (fixes broken panel)
