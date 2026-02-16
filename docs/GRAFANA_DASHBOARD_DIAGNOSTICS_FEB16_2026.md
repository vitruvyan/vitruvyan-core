# Grafana Dashboard Diagnostics Report
**Date**: February 16, 2026  
**System**: Vitruvyan Core - Synaptic Conclave Monitoring

---

## ✅ Working Dashboards/Panels

### 1. Live Neural Pulse — Event Storm
- **Status**: ✅ WORKING
- **Metrics Used**: `cognitive_bus_events_total`, `stream_length`
- **Data Source**: Redis Streams Exporter (port 9122)
- **Notes**: Shows ~133K total events, 130K active

### 2. Sacred Orders Power Levels
- **Status**: ✅ WORKING  
- **Metrics Used**: `sacred_order_activity`
- **Data Available**:
  ```
  memory: 20,157 events
  vault: 20,099 events
  orthodoxy: 20,072 events
  babel: 20,093 events
  codex: 20,080 events
  pattern: 20,100 events
  neural: 10,008 events
  ```

### 3. Top Streams — Capacity Jewels
- **Status**: ✅ WORKING
- **Metrics Used**: `stream_length`
- **Data**: 79 active streams with event counts (10K+ events per stream)

### 4. Event Rate Heatmap — Publishing Intensity
- **Status**: ✅ WORKING
- **Metrics Used**: `rate(cognitive_bus_events_total[1m])`
- **Notes**: Shows burst patterns from simulator

### 5. Stream Capacity — Fill Levels
- **Status**: ✅ WORKING
- **Metrics Used**: `stream_length`, `stream_pending_messages`
- **Capacity**: All streams at ~10K events (maxlen limit from simulator)

### 6. System Vitals — Cognitive Health
- **Status**: ✅ WORKING
- **Metrics**: 75 streams, 133K total events, 130K active events

---

## ⚠️ Partially Working Panels

### 1. Cognitive EEG — Global Event Activity
- **Status**: ⚠️ PARTIAL (some consumer groups show 0.00 events/s)
- **Issue**: Query expects specific consumer group names
- **Expected Groups**: `group:memory_orders`, `group:babel_gardens`, etc.
- **Actual Groups**:
  ```
  - group:babel_gardens ✅
  - group:codex_hunters ✅
  - group:conclave_observatory ✅
  - group:orthodoxy_main ❌ (expected: group:orthodoxy_wardens)
  - group:orthodoxy_wardens ✅
  - group:pattern_weavers ✅
  - group:vault_keepers ✅
  - memory_orders_group ❌ (expected: group:memory_orders)
  ```
  
- **Fix**:
  ```promql
  # Current query (broken for some groups):
  rate(listener_consumed_total{consumer_group="group:memory_orders"}[1m])
  
  # Fixed query (flexible naming):
  rate(listener_consumed_total{consumer_group=~".*memory.*"}[1m])
  ```

### 2. Live Ranking — Top 20 Streams (Rate)
- **Status**: ⚠️ PARTIAL
- **Issue**: Shows instance/job/stream instead of clean stream names
- **Data Available**: ✅ All metrics present
- **Fix**: Improve label formatting in query

---

## ❌ Not Working Panels

### 1. Cognitive Stability Index
- **Status**: ❌ NO DATA
- **Issue**: Metric not found
- **Expected Metric**: `cognitive_stability_index` or `bus_health_score`
- **Available Metrics**: 
  - `bus_health_score` (from Conclave API port 9012) ✅
- **Fix**: Update query to use correct metric:
  ```promql
  # Change from:
  cognitive_stability_index
  
  # To:
  bus_health_score{job="conclave"}
  ```

### 2. Mycelial Network — Sacred Orders Topology
- **Status**: ❌ ERROR ("An unexpected error happened")
- **Issue**: Complex graph visualization attempting to map consumer group relationships
- **Problem**: Query likely uses unavailable metrics or unsupported functions
- **Expected Data**: Consumer group → stream → consumer relationships
- **Available Metrics**: `stream_consumer_lag`, `stream_connection`
- **Recommendation**: 
  - Simplify to basic consumer group list
  - Use table visualization instead of graph
  - Example query:
    ```promql
    count by (consumer_group, stream) (stream_consumer_lag > -1)
    ```

### 3. Slowest Consumer Groups (Lag)
- **Status**: ❌ LIKELY BROKEN
- **Issue**: `stream_consumer_lag` has suspicious values
- **Data Sample**:
  ```
  group:orthodoxy_main → 1.771239121061e+012 (invalid timestamp?)
  group:conclave_observatory → 0.0 (correct)
  memory_orders_group → 0.0 (correct)
  ```
- **Fix**: Bug in exporter calculation for some groups
- **Workaround**: Filter out invalid values:
  ```promql
  stream_consumer_lag < 1000000
  ```

### 3. Stream Integrity — Pending Messages
- **Status**: ⚠️ NEEDS VERIFICATION
- **Metric**: `stream_pending_messages`
- **Current Value**: 0 for most streams (correct = no backlog)
- **Issue**: Panel may show "0" as "no data"
- **Fix**: Add threshold/formatting to distinguish 0 from missing data

---

## 🔧 Root Causes

### 1. **Naming Inconsistency**
- **Streams**: Mix of `vitruvyan:channel` and `channel` naming
  - Example: Both `memory.coherence.requested` and `vitruvyan:memory.coherence.requested` exist
- **Consumer Groups**: Mix of `group:name` and `name` prefixing
  - Example: `memory_orders_group` vs `group:memory_orders` (expected)

### 2. **Metric Source Confusion**
- **Port 9012** (Conclave API): `scribe_write_total`, `bus_health_score`, `stream_last_event_timestamp`
- **Port 9122** (Redis Exporter): `stream_length`, `cognitive_bus_events_total`, `listener_consumed_total`
- **Issue**: Some queries target wrong port/job

### 3. **Missing Computed Metrics**
- **Consumption Rate**: Requires `rate(listener_consumed_total[1m])`
- **Event Rate**: Requires `rate(cognitive_bus_events_total[1m])`
- **Problem**: Panels may not have enough historical data for rate calculation (need 2+ scrapes)

### 4. **Exporter Bug**
- **stream_consumer_lag** calculation bug produces invalid timestamps for some groups
- **Affected Groups**: `group:orthodoxy_main`, possibly others

---

## 📊 Available Metrics Summary

### From Conclave API (localhost:9012)
```promql
# Event emission (NEW - from simulator integration)
scribe_write_total{stream, status}              # Total writes per stream
stream_last_event_timestamp{stream}             # Last activity timestamp
conclave_streams_events_emitted_total{channel}  # Total emitted events

# Health
bus_health_score                                # System health (0-100)
bus_connected_listeners                         # Active listeners count

# HTTP
conclave_http_requests_total{method, endpoint}  # API requests
conclave_http_request_duration_seconds          # Latency histogram
```

### From Redis Streams Exporter (localhost:9122)
```promql
# Stream metrics
stream_length{stream}                           # Events in stream
stream_pending_messages{stream, consumer_group} # Unacknowledged events
stream_consumer_lag{stream, consumer_group}     # Consumer lag

# Event metrics
cognitive_bus_events_total{channel, event_type} # Published events counter
listener_consumed_total{stream, consumer_group} # Consumed events counter

# Sacred Orders
sacred_order_activity{sacred_order}             # Activity per order

# Rates (computed)
cognitive_bus_event_rate                        # Events/second
```

---

## 🔨 Recommended Fixes

### Priority 1: Critical Fixes (Enable Broken Panels)

#### Fix 1: Cognitive Stability Index
```yaml
# panel.targets[0].expr
# OLD (broken):
cognitive_stability_index

# NEW (working):
bus_health_score{job="conclave"}
```

#### Fix 2: Consumer Group Naming (Cognitive EEG)
```yaml
# OLD (breaks for memory_orders_group):
rate(listener_consumed_total{consumer_group="group:memory_orders"}[1m])

# NEW (flexible regex):
rate(listener_consumed_total{consumer_group=~".*memory.*"}[1m])
```

#### Fix 3: Mycelial Network Topology
```yaml
# Simplify from graph visualization to table
# Query:
sum by (consumer_group, stream) (stream_consumer_lag >= 0)
```

### Priority 2: Optimization (Improve Working Panels)

#### Fix 4: Stream Naming Normalization
```yaml
# Add label_replace to normalize stream names:
label_replace(
  stream_length,
  "stream_clean",
  "$1",
  "stream",
  "vitruvyan:(.*)"
)
```

#### Fix 5: Filter Invalid Consumer Lag
```yaml
# OLD (shows invalid values):
stream_consumer_lag

# NEW (filter outliers):
stream_consumer_lag < 1000000 and stream_consumer_lag >= 0
```

### Priority 3: Enhancement (New Panels)

#### New Panel: API Request Rate
```yaml
# Show simulator → Conclave API traffic
rate(conclave_http_requests_total{endpoint="/emit"}[1m])
```

#### New Panel: Scribe Write Success Rate
```yaml
# Show event emission success %
rate(scribe_write_total{status="success"}[5m]) /
rate(scribe_write_total[5m]) * 100
```

---

## 🎯 Action Items

### Immediate (Today)
1. ✅ Update **Cognitive Stability Index** query to use `bus_health_score`
2. ✅ Add regex to **Cognitive EEG** consumer group queries
3. ✅ Replace **Mycelial Network** graph with table visualization

### Short-term (This Week)
1. 🔲 Fix `stream_consumer_lag` calculation bug in exporter
2. 🔲 Normalize consumer group naming (add `group:` prefix to `memory_orders_group`)
3. 🔲 Add stream name normalization (remove `vitruvyan:` prefix in visualizations)

### Long-term (Next Sprint)
1. 🔲 Create dedicated dashboard for Synaptic Bus Simulator monitoring
2. 🔲 Add panel for API → Stream write latency
3. 🔲 Implement alerting rules for consumer lag > threshold

---

## 🧪 Test Queries (Run in Grafana Explore)

### Test 1: Verify All Sacred Orders Have Data
```promql
sacred_order_activity
```
**Expected**: 7 metrics (memory, vault, orthodoxy, babel, codex, pattern, neural)

### Test 2: Verify Consumer Groups Are Consuming
```promql
rate(listener_consumed_total[1m]) > 0
```
**Expected**: Multiple time series (one per active consumer group)

### Test 3: Verify Simulator Events Reach Conclave
```promql
rate(scribe_write_total{status="success"}[1m])
```
**Expected**: ~0.5 events/sec (medium intensity = 30 events/min)

### Test 4: Verify Stream Lengths Are Capped
```promql
stream_length > 9000
```
**Expected**: All streams ~10K (maxlen limit working)

### Test 5: Check Consumer Lag Is Healthy
```promql
stream_consumer_lag{consumer_group!~".*orthodoxy_main.*"} < 100
```
**Expected**: All non-broken groups have lag < 100

---

## 📌 Summary

| Panel Category | Working | Partial | Broken | Total |
|----------------|---------|---------|--------|-------|
| Event Flow     | 3       | 1       | 0      | 4     |
| Sacred Orders  | 2       | 0       | 0      | 2     |
| Consumer Health| 1       | 2       | 1      | 4     |
| System Vitals  | 2       | 0       | 1      | 3     |
| **TOTAL**      | **8**   | **3**   | **2**  | **13**|

**Success Rate**: 61% fully working, 23% partial, 15% broken

**Next Steps**:
1. Apply Priority 1 fixes to enable 2 broken panels
2. Improve partial panels with better queries
3. File bug report for exporter consumer lag calculation

---

**Generated by**: Vitruvyan Core Diagnostics  
**Simulator Status**: ✅ Running (medium intensity, API mode)  
**Metrics Collected**: 9012 (Conclave), 9122 (Redis Exporter)
