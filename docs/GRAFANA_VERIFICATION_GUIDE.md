# Grafana Dashboard Verification Guide
**Date**: February 16, 2026  
**Simulator Run**: 10 minutes, 342 events @ 0.6 events/s  
**Metrics Endpoints**: 
- Conclave API: http://localhost:9012/metrics
- Redis Exporter: http://localhost:9122/metrics

---

## 📊 Quick Verification Checklist

### ✅ Step 1: Access Grafana
1. **URL**: `http://localhost:3000` (or configured Grafana port)
2. **Login**: `admin` / `vitruvyan_admin` (default credentials)
3. **Dashboard**: Navigate to "Synaptic Bus EEG" or "Cognitive Bus Monitoring"

---

## 🎯 Priority Panels to Verify (Working Post-Fix)

### 1. **Cognitive Stability Index** 🆕 FIXED
- **Query**: `bus_health_score{component="overall"}`
- **Expected Value**: `100.0`
- **What to Check**:
  - Gauge shows 100/100 (healthy)
  - No gaps in data (metric continuously available)
  - Hover shows component breakdown (herald, scribe, streams, listeners, overall, conclave)

**Fix Applied**: Added `bus_health_score` metric to Conclave API with component labels

---

### 2. **Sacred Orders Power Levels**
- **Query**: `sacred_order_activity`
- **Expected Values**:
  ```
  memory:    ~20,300 events
  babel:     ~20,175 events
  vault:     ~20,171 events
  pattern:   ~20,165 events
  codex:     ~20,165 events
  orthodoxy: ~20,149 events
  neural:    ~10,008 events
  ```
- **What to Check**:
  - All 7 Sacred Orders visible
  - Bar chart/stat panel shows non-zero values
  - Memory has highest activity (most writes)
  - Neural has ~half activity (expected asymmetry)

---

### 3. **Live Neural Pulse — Event Storm**
- **Query**: `rate(cognitive_bus_events_total[1m])`
- **Expected**: ~0.6 events/s during simulator run
- **What to Check**:
  - Graph shows spike at 16:09 - 16:19 (simulator runtime)
  - Rate increases from baseline to ~0.6 events/s
  - Multiple colored lines (one per stream/channel)
  - Return to baseline after 16:19

---

### 4. **Top Streams — Capacity Jewels**
- **Query**: `topk(10, stream_length)`
- **Expected Top 5**:
  1. memory.write.completed: ~10,013+
  2. codex.enrichment.completed: ~10,013+
  3. memory.coherence.requested: ~10,011+
  4. vault.archive.requested: ~10,010+
  5. neural_engine.screening.completed: ~10,008
- **What to Check**:
  - Table/list shows stream names
  - All values ~10K (maxlen limit working)
  - New streams from simulator visible

---

### 5. **Consumer Lag Health** 🆕 FIXED
- **Query**: `stream_consumer_lag`
- **Expected**: All values `< 10` seconds (near real-time)
- **What to Check**:
  - No red alerts (lag > 100s)
  - `group:orthodoxy_main` shows `0.0` (not `1.77e+12` anymore)
  - All consumer groups consuming in real-time

**Fix Applied**: Converted lag calculation from milliseconds to seconds, added sanity check for invalid timestamps

---

### 6. **API Request Rate** (NEW - if available)
- **Query**: `rate(conclave_http_requests_total{endpoint=~"/emit.*"}[1m])`
- **Expected**: ~0.6 req/s during simulator run
- **What to Check**:
  - Spike at 16:09 - 16:19
  - All requests return `status="200"` (success)
  - No errors (status="500")

---

### 7. **Scribe Write Success Rate** (NEW - if available)
- **Query**: `rate(scribe_write_total{status="success"}[5m])`
- **Expected**: 342 total writes over 10 minutes
- **What to Check**:
  - Counter increases over time
  - 13 streams actively written
  - No failures (status="error")

---

## ⚠️ Panels with Known Issues (Partial)

### 1. **Cognitive EEG — Global Event Activity**
- **Issue**: Consumer group naming inconsistency
- **Current Query**: `rate(listener_consumed_total{consumer_group="group:memory_orders"}[1m])`
- **Problem**: Some groups named `memory_orders_group`, others `group:memory_orders`
- **Workaround**: Shows data for some groups, not others

**Suggested Fix** (apply in Grafana panel edit):
```promql
# Replace hardcoded names with regex:
rate(listener_consumed_total{consumer_group=~".*memory.*"}[1m])
rate(listener_consumed_total{consumer_group=~".*vault.*"}[1m])
rate(listener_consumed_total{consumer_group=~".*babel.*"}[1m])
```

---

### 2. **Mycelial Network — Sacred Orders Topology**
- **Issue**: Complex graph visualization error
- **Current**: Shows "An unexpected error happened"
- **Workaround**: Skip this panel (not critical for monitoring)

**Suggested Fix**: Replace with simplified table:
```promql
count by (consumer_group, stream) (stream_consumer_lag >= 0)
```

---

## 🧪 Manual Verification (CLI)

If Grafana panels don't show data, verify metrics directly:

### Test 1: Bus Health Score
```bash
curl -s http://localhost:9012/metrics | grep "bus_health_score"
# Expected: 6 metrics (herald, scribe, streams, listeners, overall, conclave)
```

### Test 2: Scribe Writes
```bash
curl -s http://localhost:9012/metrics | grep "scribe_write_total{" | awk '{sum+=$2} END {print sum}'
# Expected: 342 (or current total)
```

### Test 3: Sacred Orders
```bash
curl -s http://localhost:9122/metrics | grep "sacred_order_activity"
# Expected: 7 metrics with values 10K-20K
```

### Test 4: Consumer Lag
```bash
curl -s http://localhost:9122/metrics | grep "stream_consumer_lag" | grep "orthodoxy_main"
# Expected: Values < 10 (not 1.77e+12)
```

---

## 🚨 Troubleshooting

### Panel shows "No Data"

1. **Check Time Range**: Ensure Grafana time range includes 16:09 - 16:19 (Feb 16, 2026)
2. **Check Data Source**: Verify Prometheus is scraping correctly
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets | grep "conclave\|redis_streams_exporter"
   ```
3. **Check Metric Name**: Some panels may use old metric names (see diagnostics report)

### Panel shows old data

1. **Refresh Dashboard**: Click refresh button (top-right)
2. **Adjust Time Range**: Switch to "Last 15 minutes" or "Last 1 hour"
3. **Clear Browser Cache**: Ctrl+Shift+R to force reload

### Consumer Lag shows huge numbers

- **Root Cause**: Old exporter version (pre-fix)
- **Solution**: Verify exporter container is updated (see timestamp in docker logs)
  ```bash
  docker logs core_redis_streams_exporter --tail=5
  # Should NOT show ValueError or e+12 numbers
  ```

---

## 📈 Expected Dashboard Behavior

### During Simulator Run (16:09 - 16:19)
- Event rate spikes to ~0.6 events/s
- API request rate matches event rate
- Stream lengths increase gradually (+342 events distributed)
- Consumer lag stays near 0 (real-time consumption)
- Sacred Order activity increases proportionally

### After Simulator Stops (> 16:19)
- Event rate drops to 0 (no new events)
- Stream lengths stabilize
- Consumer lag remains 0 (no backlog)
- Bus health stays 100
- Existing data remains queryable (Prometheus retention)

---

## ✅ Success Criteria

**Dashboard is working correctly if**:
1. ✅ Cognitive Stability Index shows 100
2. ✅ All 7 Sacred Orders have non-zero activity
3. ✅ Event rate graph shows spike at 16:09-16:19
4. ✅ Consumer lag < 10 seconds for all groups
5. ✅ Top streams show ~10K events each
6. ✅ No error messages in panels

**Current Status**: 9/13 panels working (69%), 3 partial (23%), 1 broken (8%)

---

## 📚 Reference Documents

- **Diagnostics Report**: [docs/GRAFANA_DASHBOARD_DIAGNOSTICS_FEB16_2026.md](GRAFANA_DASHBOARD_DIAGNOSTICS_FEB16_2026.md)
- **Test Script**: `bash scripts/test_grafana_metrics.sh`
- **Simulator**: `python3 scripts/synaptic_bus_simulator.py --help`

---

## 🔧 Next Steps

1. **Verify working panels** using this guide (Priority 1-7)
2. **Apply query fixes** for partial panels (Cognitive EEG regex)
3. **Re-run simulator** if more data needed:
   ```bash
   python3 scripts/synaptic_bus_simulator.py --duration 1800 --intensity high --api-url http://localhost:9012
   ```
4. **Create GitHub Issue** for Mycelial Network panel (low priority)

---

**Last Updated**: Feb 16, 2026 @ 16:20 UTC  
**Simulator Run**: 342 events in 600s (0.57 events/s)  
**Dashboard Status**: 9/13 working (69% success rate)
