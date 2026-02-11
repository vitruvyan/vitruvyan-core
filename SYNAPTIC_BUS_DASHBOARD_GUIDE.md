# Synaptic Bus EEG Dashboard — User Guide
**Dashboard UID**: `synaptic-bus-eeg`  
**Access**: http://localhost:3000/d/synaptic-bus-eeg/synaptic-bus-eeg  
**Credentials**: `admin` / `vitruvyan_admin`

---

## Overview
The **Synaptic Bus EEG Dashboard** visualizes the Redis Streams-based event bus ("Synaptic Conclave") as a living cognitive system. It provides real-time insights into:
- Event publish/consume rates across all Sacred Orders
- Consumer group health and lag
- System stability and bottleneck detection
- Network topology of micelial polyp architecture

---

## Panel Guide

### 1. ⚡ Cognitive EEG — Global Event Activity
**Type**: Time Series  
**Purpose**: Real-time "electroencephalogram" showing publish/consume patterns

**Metrics**:
- 📤 **Publish Rate** (`sum(rate(cognitive_bus_events_total{event_type="publish"}[1m]))`)
  - Events published to Redis Streams per second/per service
- 📥 **Consume Rate** (`sum(rate(listener_consumed_total[1m]))`)
  - Events consumed by listener containers per second/per consumer group
- ⏱️ **p95 Latency** (`histogram_quantile(0.95, ...)`)
  - 95th percentile event processing time
- 🐌 **Lag** (`sum(stream_consumer_lag)`)
  - Backlog of unprocessed messages per consumer group

**Interpretation**:
- **Healthy**: Publish and consume lines roughly parallel (balanced flow)
- **Backpressure**: Publish > consume with increasing lag (scale consumers)
- **Idle**: Consume > publish with decreasing lag (excess capacity)

---

### 2. 🧠 Polypo Matrix — Consumer Group Health
**Type**: Table  
**Purpose**: Snapshot of all consumer group states with color-coded lag thresholds

**Columns**:
| Column | Metric | Description |
|--------|--------|-------------|
| Consumer Group | `consumer_group` label | Name (e.g., `group:vault_keepers`) |
| Lag | `stream_consumer_lag` | Unprocessed messages count |
| Pending | `stream_pending_messages` | Acknowledged but not completed |
| Rate (events/s) | `rate(listener_consumed_total[1m])` | Current consumption rate |

**Color Coding**:
- 🟢 **Green** (0-10): Healthy, near real-time processing
- 🟡 **Yellow** (10-100): Mild backlog, monitor trend
- 🔴 **Red** (>100): Critical lag, investigate consumer

**Actions on Red State**:
1. Check consumer container logs: `docker logs core_<order>_listener`
2. Verify consumer is running: `docker ps --filter "name=listener"`
3. Scale horizontally (add consumer instances if stateless)
4. Optimize processing logic (reduce per-event latency)

---

### 3. 🕸️ Micelial Network — Sacred Orders Topology
**Type**: Node Graph  
**Purpose**: Living visualization of inter-service event flows

**Visual Elements**:
- **Nodes**: Sacred Order services (Memory, Vault, Orthodoxy, Codex, Babel, PatternWeavers, Conclave)
- **Node Size**: Proportional to message throughput (events/s)
- **Edges**: Redis Streams (channels)
- **Edge Thickness**: Event rate (thicker = higher traffic)
- **Node Color**: Consumer lag (green=healthy, yellow=warning, red=critical)

**Interpretation**:
- **Dense connections**: High inter-service coupling (expected for Conclave)
- **Isolated nodes**: Service not participating in event flow (check configuration)
- **Thick edge**: Hot channel (e.g., `memory.coherence.completed`)
- **Red node**: Consumer lag detected (zoom into Polypo Matrix for details)

**Interaction**:
- Click node → View service details
- Click edge → View channel metrics
- Hover → Tooltip with exact rates/lag values

---

### 4. ⚖️ Cognitive Stability Index
**Type**: Gauge  
**Purpose**: System-wide consume/publish ratio (equilibrium indicator)

**Formula**:
```
Stability = sum(rate(listener_consumed_total[1m])) / sum(rate(cognitive_bus_events_total{event_type="publish"}[1m]))
```

**Thresholds**:
- 🔴 **Red** (<0.9): **Backpressure** — Consumers falling behind, system accumulating lag
- 🟢 **Green** (0.9-1.1): **Healthy Equilibrium** — Balanced publish/consume, stable state
- 🔵 **Blue** (>1.1): **Idle Capacity** — Consumers faster than publishers, excess resources

**Recommended Actions**:
- **Red**: Scale consumers, optimize hot path, investigate slow queries
- **Green**: Maintain current configuration
- **Blue**: Consider reducing consumer resources to save costs (optional)

---

### 5. 📊 Stream Integrity — Pending Messages
**Type**: Stat Panel  
**Purpose**: Total unacknowledged events waiting for consumer processing

**Metric**: `sum(stream_pending_messages)`

**Thresholds**:
- 🟢 **Green** (0-100): Normal operation, low pending queue
- 🟡 **Yellow** (100-1000): Moderate backlog, monitor trend
- 🔴 **Red** (>1000): Critical pending overflow, immediate action required

**Root Causes of High Pending**:
1. Consumer crashed without acknowledging messages
2. Network partition between consumer and Redis
3. Long-running transactions blocking acknowledgment
4. Duplicate consumer IDs causing message theft

**Resolution**:
```bash
# Check pending messages per consumer
docker exec core_redis redis-cli XPENDING <stream> <consumer_group>

# Claim stale messages (manual recovery)
docker exec core_redis redis-cli XCLAIM <stream> <consumer_group> <new_consumer> <min_idle_time_ms> <msg_id>
```

---

### 6. 📈 Stream Capacity — Fill Levels
**Type**: Bar Gauge  
**Purpose**: Current stream length vs max_length cap (memory pressure)

**Metric**: `stream_length` (per stream)  
**Max Length**: 10,000 entries (configured in StreamBus)

**Thresholds**:
- 🟢 **Green** (0-70%): Healthy capacity
- 🟡 **Yellow** (70-90%): Approaching cap, pruning may occur
- 🔴 **Red** (>90%): Critical, Redis will auto-trim oldest entries

**Interpretation**:
- Streams near 10,000 length will lose oldest events (FIFO eviction)
- If critical streams hit cap, increase `maxlen` or purge archival data

**Mitigation**:
```python
# In StreamBus initialization, increase maxlen
self.redis_client.xadd(channel, {"payload": payload}, maxlen=50000, approximate=True)
```

---

### 7. 🔥 Top 10 Hottest Streams (Rate)
**Type**: Time Series (Bar Chart)  
**Purpose**: Identify most active channels for capacity planning

**Metric**: `topk(10, sum(rate(cognitive_bus_events_total{event_type="publish"}[1m])) by (channel))`

**Use Cases**:
- **Capacity Planning**: Hot streams may need dedicated Redis instances
- **Bottleneck Detection**: High rate + high lag = consumer can't keep up
- **Feature Usage**: Which Sacred Orders are most active?

**Example Output**:
```
memory.coherence.completed      : 45.3 events/s
vault.archive.requested         : 32.1 events/s
orthodoxy.validation.pending    : 28.7 events/s
codex.discovery.mapped          : 15.2 events/s
...
```

---

### 8. ⏳ Slowest Consumer Groups (Lag)
**Type**: Time Series (Line Chart)  
**Purpose**: Track which consumer groups are struggling to keep up

**Metric**: `topk(10, stream_consumer_lag)`

**Interpretation**:
- **Flat line near 0**: Consumer healthy, processing in real-time
- **Increasing line**: Consumer falling behind, investigate root cause
- **Spike**: Burst of events or consumer restart
- **Decreasing after spike**: Consumer catching up (good recovery)

**Troubleshooting High Lag**:
1. **Check CPU/Memory**: `docker stats core_<order>_listener`
2. **Profile Processing**: Add timing metrics to consumer code
3. **Database Bottleneck**: Slow queries in PostgresAgent/QdrantAgent
4. **Network Latency**: Check Redis connection stability
5. **Code Bug**: Infinite loop or deadlock in consumer logic

---

## Alert Integration

The dashboard is integrated with Prometheus Alertmanager. When alert rules fire, they appear as annotations on panels:

**Annotation Icon**: 🔔 Red bell in top-right panel corners

**Active Alerts**: Click icon to see alert details:
- Alert name (e.g., `SynapticBusHighLag`)
- Severity (warning/critical)
- Firing timestamp
- Affected labels (consumer_group, stream, etc.)

---

## Advanced Usage

### Custom Time Range
- **Default**: Last 30 minutes
- **Custom**: Click time picker (top-right) → Select range or type duration (e.g., `now-6h` to `now`)

### Panel Zoom
- Click and drag on any panel to zoom into time window
- Click "Reset zoom" icon to restore

### Panel Inspection
- Click panel title → "Inspect" → View raw PromQL query and returned data

### Export Panel Data
```bash
# Get panel data via API (replace panel_id)
curl -s -u admin:vitruvyan_admin \
  'http://localhost:3000/api/ds/query' \
  -H 'Content-Type: application/json' \
  -d '{"queries": [{"expr": "sum(rate(cognitive_bus_events_total[1m]))"}]}' | jq
```

### Share Dashboard
- Click "Share" icon (top-right) → Get link or export JSON
- For external access: Use Nginx reverse proxy to expose port 3000

---

## Prometheus Queries Reference

All queries are optimized for Grafana's 15s scrape interval:

| Panel | PromQL Query |
|-------|--------------|
| Publish Rate | `sum(rate(cognitive_bus_events_total{event_type="publish"}[1m])) by (service)` |
| Consume Rate | `sum(rate(listener_consumed_total[1m])) by (consumer_group)` |
| p95 Latency | `histogram_quantile(0.95, sum(rate(cognitive_bus_event_duration_seconds_bucket[1m])) by (le, service))` |
| Consumer Lag | `sum(stream_consumer_lag) by (consumer_group)` |
| Stability Index | `sum(rate(listener_consumed_total[1m])) / sum(rate(cognitive_bus_events_total{event_type="publish"}[1m]))` |
| Pending Messages | `sum(stream_pending_messages)` |
| Stream Length | `stream_length` |
| Hottest Streams | `topk(10, sum(rate(cognitive_bus_events_total{event_type="publish"}[1m])) by (channel))` |
| Slowest Consumers | `topk(10, stream_consumer_lag)` |

---

## Troubleshooting

### "No data" on panels
**Cause**: Metrics not being scraped or services not publishing events

**Fix**:
```bash
# 1. Verify Prometheus is scraping
curl -s http://localhost:15000/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# 2. Check if metric exists
curl -s 'http://localhost:15000/api/v1/label/__name__/values' | grep cognitive_bus

# 3. Generate test event
docker exec core_memory_orders \
  curl -X POST http://localhost:8000/coherence/analyze \
  -H 'Content-Type: application/json' \
  -d '{"entity_id": "test", "context": "test"}'
```

### Dashboard not updating
**Cause**: Grafana provisioning interval not triggered

**Fix**:
```bash
# Force reload (don't wait 30s)
docker compose restart grafana
```

### Node Graph not displaying
**Cause**: No event flow data (services not communicating)

**Fix**:
```bash
# Verify cross-service events exist
curl -s 'http://localhost:15000/api/v1/query?query=sum(rate(cognitive_bus_events_total[5m]))%20by%20(channel)' | \
  jq '.data.result[] | .metric.channel'
```

---

## See Also
- [SYNAPTIC_BUS_AUDIT_FINAL.md](SYNAPTIC_BUS_AUDIT_FINAL.md) — System topology audit
- [GRAFANA_DASHBOARD_VALIDATION_REPORT.md](GRAFANA_DASHBOARD_VALIDATION_REPORT.md) — Deployment validation
- [/infrastructure/docker/monitoring/alerts/synaptic_bus_alerts.yml](infrastructure/docker/monitoring/alerts/synaptic_bus_alerts.yml) — Alert rules
- [vitruvyan_core/core/synaptic_conclave/monitoring/metrics.py](vitruvyan_core/core/synaptic_conclave/monitoring/metrics.py) — Metric definitions

---

**Dashboard Version**: 1.0  
**Last Updated**: February 11, 2026  
**Maintainer**: Vitruvyan Core Team
