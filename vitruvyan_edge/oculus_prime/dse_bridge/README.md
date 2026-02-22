# Vitruvyan Intake → DSE Bridge

**Bridge between Codex Hunters (semantic enrichment) and DSE Epistemic Chain (Pattern Weavers)**

## Overview

The Intake → DSE Bridge is a critical architectural component that connects the Vitruvyan Intake Layer (raw file ingestion) with the DSE Epistemic Chain (decision intelligence pipeline).

### Problem Solved

**Before Bridge**:
- ❌ Intake Agents created `evidence_packs` (raw files) with no path to DSE
- ❌ Codex Hunters enriched evidence with embeddings, but no trigger for Pattern Weavers
- ❌ Manual intervention required to move data from Intake to DSE

**After Bridge**:
- ✅ Fully automated event-driven pipeline: Upload → Intake → Codex → Bridge → Pattern Weavers → DSE
- ✅ Zero manual steps from file upload to decision space exploration
- ✅ Idempotent processing (no duplicates)
- ✅ Full audit trail for compliance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  INTAKE AGENTS                                                           │
│  Document, Image, Audio, Video, CAD, GIS, Sensor                        │
│  ↓                                                                       │
│  Evidence Packs (evidence_packs table)                                  │
│  ↓                                                                       │
│  📡 Event: oculus_prime.evidence.created (legacy: intake.evidence.created) │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CODEX HUNTERS                                                           │
│  Semantic enrichment (embeddings, entity extraction)                     │
│  ↓                                                                       │
│  Qdrant (vitruvyan_embeddings collection)                                   │
│  ↓                                                                       │
│  📡 Event: codex.evidence.indexed                                       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ⭐ INTAKE → DSE BRIDGE ⭐                                              │
│  1. Subscribe: codex.evidence.indexed                                   │
│  2. Retrieve: Evidence Pack from evidence_packs                          │
│  3. Create: IntakeEvidence in dse_intake_evidence (binding='traceable') │
│  4. Emit: langgraph.intake.ready                                        │
│  5. Log: bridge_operations_log (audit trail)                            │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PATTERN WEAVERS (LangGraph Node)                                       │
│  Subscribe: langgraph.intake.ready                                      │
│  ↓                                                                       │
│  Semantic Hypothesis Generation                                          │
│  ↓                                                                       │
│  dse_semantic_hypotheses (binding='non_binding')                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
                    ORTHODOXY GATE → DSE KERNEL
```

---

## Quick Start

### 1. Deploy PostgreSQL Migration

```bash
PGPASSWORD='@Caravaggio971_omni' psql \
  -h localhost -p 9432 \
  -U vitruvyan_omni_user \
  -d vitruvyan_omni \
  -f infrastructure/migrations/002_create_bridge_operations_log.sql
```

### 2. Build & Start Bridge Service

```bash
cd /home/caravaggio/vitruvyan

# Build Docker image
docker compose build vitruvyan_intake_dse_bridge

# Start service
docker compose up -d vitruvyan_intake_dse_bridge

# Verify health
curl http://localhost:8021/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "intake_dse_bridge",
  "version": "1.0.0",
  "timestamp": "2026-01-11T12:00:00.000000"
}
```

### 3. Monitor Logs

```bash
docker logs -f omni_intake_dse_bridge
```

Expected log output:
```
🚀 Starting Vitruvyan Intake → DSE Bridge Service...
🌉 IntakeDSEBridge initialized - listening to: codex.evidence.indexed
✅ Subscribed to: codex.evidence.indexed
🎧 Waiting for events...
```

---

## API Endpoints

### Health Check
```bash
curl http://localhost:8021/health
```

### Service Info
```bash
curl http://localhost:8021/ | jq
```

### Prometheus Metrics
```bash
curl http://localhost:8021/metrics
```

Output:
```
bridge_operations_total 1523
bridge_operations_success 1489
bridge_operations_failed 34
bridge_operations_24h 287
```

### Bridge Status
```bash
curl http://localhost:8021/status | jq
```

Output:
```json
{
  "service": "intake_dse_bridge",
  "version": "1.0.0",
  "subscribe_channel": "codex.evidence.indexed",
  "publish_channel": "langgraph.intake.ready",
  "statistics": {
    "total_operations": 1523,
    "status_breakdown": {
      "success": 1489,
      "failed": 34
    },
    "success_rate": 97.77
  },
  "recent_operations": [...]
}
```

---

## Testing

### Manual Event Test

Simulate Codex Hunters event emission:

```bash
redis-cli
> PUBLISH codex.evidence.indexed '{"evidence_id": "EVD-TEST-001", "point_id": "test-point-123", "collection": "vitruvyan_embeddings", "timestamp": "2026-01-11T12:00:00Z"}'
```

Verify bridge operation:

```bash
# Check bridge log
PGPASSWORD='@Caravaggio971_omni' psql \
  -h localhost -p 9432 \
  -U vitruvyan_omni_user \
  -d vitruvyan_omni \
  -c "SELECT * FROM bridge_operations_log ORDER BY created_at DESC LIMIT 5;"

# Check dse_intake_evidence
PGPASSWORD='@Caravaggio971_omni' psql \
  -h localhost -p 9432 \
  -U vitruvyan_omni_user \
  -d vitruvyan_omni \
  -c "SELECT evidence_id, binding_status, created_at FROM dse_intake_evidence ORDER BY created_at DESC LIMIT 5;"
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `omni_postgres` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `vitruvyan_omni` | Database name |
| `POSTGRES_USER` | `vitruvyan_omni_user` | Database user |
| `POSTGRES_PASSWORD` | `@Caravaggio971_omni` | Database password |
| `REDIS_HOST` | `omni_redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `BRIDGE_MAX_RETRIES` | `3` | Max retry attempts |
| `BRIDGE_RETRY_DELAY` | `5` | Retry delay (seconds) |

---

## Monitoring & Observability

### Grafana Dashboard

Import the bridge metrics dashboard:

```bash
# Dashboard JSON location
infrastructure/monitoring/grafana/dashboards/intake_dse_bridge.json
```

**Metrics Tracked**:
- Operations per minute
- Success rate (%)
- Failed operations count
- Average processing latency
- Recent operations timeline

### Prometheus Queries

```promql
# Operations per minute
rate(bridge_operations_total[1m])

# Success rate (last 5 minutes)
(sum(rate(bridge_operations_success[5m])) / sum(rate(bridge_operations_total[5m]))) * 100

# Failed operations (last 24 hours)
increase(bridge_operations_failed[24h])
```

---

## Troubleshooting

### Bridge Not Processing Events

**Symptoms**: No logs, no database inserts

**Diagnosis**:
```bash
# 1. Check service is running
docker ps | grep intake_dse_bridge

# 2. Check Redis connectivity
docker exec omni_intake_dse_bridge redis-cli -h omni_redis PING

# 3. Check PostgreSQL connectivity
docker exec omni_intake_dse_bridge psql \
  -h omni_postgres -U vitruvyan_omni_user -d vitruvyan_omni -c "SELECT 1"

# 4. Check logs
docker logs omni_intake_dse_bridge --tail 100
```

**Solution**: Restart bridge service
```bash
docker compose restart vitruvyan_intake_dse_bridge
```

---

### Duplicate Processing

**Symptoms**: Same evidence_id processed multiple times

**Diagnosis**:
```bash
# Check for duplicates in dse_intake_evidence
PGPASSWORD='@Caravaggio971_omni' psql \
  -h localhost -p 9432 \
  -U vitruvyan_omni_user \
  -d vitruvyan_omni \
  -c "SELECT evidence_id, COUNT(*) FROM dse_intake_evidence GROUP BY evidence_id HAVING COUNT(*) > 1;"
```

**Solution**: Idempotency is enforced via `ON CONFLICT (evidence_id) DO NOTHING`. Check bridge logs for race conditions.

---

### High Failure Rate

**Symptoms**: `bridge_operations_failed` > 10%

**Diagnosis**:
```bash
# Check failed operations
PGPASSWORD='@Caravaggio971_omni' psql \
  -h localhost -p 9432 \
  -U vitruvyan_omni_user \
  -d vitruvyan_omni \
  -c "SELECT evidence_id, metadata->>'error' FROM bridge_operations_log WHERE status='failed' ORDER BY created_at DESC LIMIT 10;"
```

**Common Causes**:
1. Evidence Pack not found in `evidence_packs` (Codex Hunters delay)
2. PostgreSQL connection timeout
3. Redis connection lost

**Solution**: Implement retry queue (planned Q2 2026)

---

## Performance Metrics

### Expected Throughput

| Scenario | Throughput | Latency |
|----------|-----------|---------|
| Single event | ~100-200 events/sec | <50ms |
| Bulk upload | ~50-100 events/sec | <100ms |
| Peak load | ~30-50 events/sec | <200ms |

### Resource Usage

| Resource | Typical | Peak |
|----------|---------|------|
| CPU | 5-10% | 20-30% |
| Memory | 50-100 MB | 200 MB |
| Network | <1 Mbps | <5 Mbps |

---

## Roadmap

### Q1 2026 ✅ COMPLETE
- [x] Core bridge implementation
- [x] Event subscription (codex.evidence.indexed)
- [x] dse_intake_evidence creation
- [x] Event emission (langgraph.intake.ready)
- [x] Audit trail logging
- [x] Health check endpoint
- [x] Prometheus metrics

### Q2 2026 (Planned)
- [ ] Retry queue for failed operations
- [ ] Multi-chunk aggregation (combine all Evidence Pack chunks)
- [ ] Rate limiting (prevent overload)
- [ ] User session tracking (correlate multiple uploads)
- [ ] Performance optimization (batch processing)

---

## References

- **Architecture Doc**: `docs/INTAKE_DSE_BRIDGE_IMPLEMENTATION_COMPLETE.md`
- **Intake Layer**: `vitruvyan_edge/oculus_prime/README.md`
- **Codex Hunters**: `services/core/api_codex_hunters/main.py`
- **Pattern Weavers**: `vitruvyan_core/core/orchestration/langgraph/node/pattern_weavers_node.py`
- **PostgreSQL Schema**: `infrastructure/migrations/002_create_bridge_operations_log.sql`

---

**Author**: Vitruvyan Development Team  
**Created**: 2026-01-11  
**Port**: 8021  
**Status**: ✅ PRODUCTION READY
