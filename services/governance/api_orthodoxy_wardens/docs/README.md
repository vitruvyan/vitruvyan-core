# Orthodoxy Wardens - Sacred Compliance & Audit API

**Status**: ✅ Production Ready (P1 FASE 3 Complete - Feb 8, 2026)  
**Port**: 9006 (external), 8006 (internal)  
**Purpose**: Event-driven compliance validation and auto-correction for the Vitruvyan ecosystem

---

## 🎯 What Is This?

Orthodoxy Wardens is a **governance service** that validates system compliance, detects architectural violations ("heresies"), and orchestrates auto-correction workflows through the Synaptic Conclave (Redis Streams).

**Core Responsibilities**:
- Audit request orchestration (Neural Engine, Babel Gardens, VEE completions)
- Real-time heresy detection and remediation
- System event logging and compliance monitoring
- Risk assessment and architectural validation

**Integration**: Consumes events from 7 sacred channels via Redis Streams, provides REST API for on-demand audits.

---

## ⚡ Quick Start

### Prerequisites
- Docker + docker-compose
- Redis Streams instance (omni_redis)
- PostgreSQL database (omni_postgres)

### 1. Build & Run
```bash
cd /home/vitruvyan/vitruvyan-core/infrastructure/docker
docker compose build vitruvyan_api_orthodoxy_wardens
docker compose up -d vitruvyan_api_orthodoxy_wardens
```

### 2. Verify Health
```bash
curl http://localhost:9006/divine-health | jq .
# Expected: {"sacred_status": "blessed|purifying", "blessing_level": 0.75-1.0, ...}
```

### 3. Test Event Consumption
```bash
# Check consumer groups (should show 7 channels)
docker exec omni_redis redis-cli XINFO GROUPS "vitruvyan:stream:orthodoxy.audit.requested"

# Verify background listener thread
docker logs omni_api_orthodoxy_wardens --tail=50 | grep "listeners thread started"
# Expected: 🔥 Synaptic Conclave listeners thread started (background processing active)
```

---

## 🏛️ Architecture Overview

### Sacred Roles Pattern (Theological → Functional Mapping)

**Design Philosophy**: Business logic wrapped in **event-driven roles** that emit/consume from Synaptic Conclave.

| Sacred Role | Functional Purpose | Agent Backend |
|-------------|-------------------|---------------|
| **Confessor** | Audit orchestration | AutonomousAuditAgent (LangGraph workflow) |
| **Penitent** | Auto-correction execution | AutoCorrector |
| **Chronicler** | Event logging | SystemMonitor |
| **Inquisitor** | Compliance investigation | ComplianceValidator |
| **Abbot** | Audit verdict finalization | AutonomousAuditAgent |

**Key Benefit**: Decouples business logic (agents) from infrastructure (FastAPI/Redis), enables testing without Docker.

### Synaptic Conclave Integration (7 Channels)

**Consumer Group**: `group:orthodoxy_main`  
**Consumer ID**: `orthodoxy_main:worker_1`

| Channel | Handler | Purpose |
|---------|---------|---------|
| `orthodoxy.audit.requested` | handle_audit_request | Orchestrate Inquisitor → Confessor → Abbot |
| `orthodoxy.validation.requested` | handle_audit_request | Same as audit (reuse handler) |
| `neural_engine.screening.completed` | handle_system_events | Log Neural Engine completions |
| `babel.sentiment.completed` | handle_system_events | Log Babel sentiment analysis |
| `memory.write.completed` | handle_system_events | Log memory writes |
| `vee.explanation.completed` | handle_system_events | Log VEE narrative generation |
| `langgraph.response.completed` | handle_system_events | Log LangGraph orchestration |

**Background Processing**: Listeners run in daemon thread (does NOT block FastAPI startup).

---

## 📂 Project Structure (P1 FASE 3 Refactored)

```
api_orthodoxy_wardens/
├── core/                           # Business logic (P1 FASE 3)
│   ├── __init__.py                # Package exports
│   ├── roles.py                   # 5 Sacred Role classes (382 lines)
│   └── event_handlers.py          # 3 event handlers + DI (136 lines)
│
├── docs/                           # Documentation (P1 FASE 4)
│   ├── README.md                  # This file (entry point)
│   ├── ORTHODOXY_WARDENS_GUIDE.md # Implementation guide
│   ├── API_REFERENCE.md           # Endpoint documentation
│   └── ARCHITECTURAL_DECISIONS.md # Design rationale
│
├── main.py                         # FastAPI app (thin wrapper, 829 lines)
├── streams_listener.py             # Standalone Redis Streams consumer
└── redis_listener.py               # Legacy Pub/Sub listener (deprecated)
```

**Code Reduction**: main.py reduced from 1034 → 829 lines (-21%) after P1 FASE 3 business logic separation.

---

## 🔗 API Endpoints

### Health Check
```http
GET /divine-health
```
**Response**:
```json
{
  "sacred_status": "blessed",
  "divine_council": {
    "confessor": "blessed",
    "penitent": "blessed",
    "chronicler": "blessed",
    "inquisitor": "blessed",
    "abbot": "blessed"
  },
  "blessing_level": 0.875,
  "timestamp": "2026-02-08T18:48:00Z"
}
```

### Initiate Audit
```http
POST /confession/initiate
Content-Type: application/json

{
  "confession_type": "system_compliance",
  "sacred_scope": "complete_realm",
  "urgency": "divine_routine",
  "penitent_service": "neural_engine"
}
```

**Response**:
```json
{
  "confession_id": "confession_20260208_184800",
  "sacred_status": "confessing",
  "assigned_warden": "Confessor",
  "timestamp": "2026-02-08T18:48:00Z"
}
```

**See**: [API_REFERENCE.md](./API_REFERENCE.md) for complete endpoint documentation.

---

## 🧪 Testing

### 1. Import Test (No Docker Required)
```bash
python3 -c "from services.governance.api_orthodoxy_wardens.core.roles import OrthodoxConfessor; print('✅ Import successful')"
```

### 2. Container Health
```bash
docker ps | grep orthodoxy
# Expected: Container running, status "Up X minutes (healthy)"

docker logs omni_api_orthodoxy_wardens --tail=100 | grep -E "startup complete|Uvicorn running"
# Expected: "Application startup complete." + "Uvicorn running on http://0.0.0.0:8006"
```

### 3. Event Consumption
```bash
# Emit test event
curl -X POST http://localhost:9012/emit/orthodoxy.audit.requested \
  -H "Content-Type: application/json" \
  -d '{"event_type": "audit.test", "data": {"test": true}}'

# Check logs for consumption
docker logs omni_api_orthodoxy_wardens --tail=50 | grep "Processed and acknowledged"
```

### 4. API Integration
```bash
# Test health endpoint
curl http://localhost:9006/divine-health | jq '.sacred_status'
# Expected: "blessed" or "purifying"

# Test audit initiation
curl -X POST http://localhost:9006/confession/initiate \
  -H "Content-Type: application/json" \
  -d '{"confession_type": "system_compliance"}'
```

---

## 🛠️ Configuration

### Environment Variables
```bash
# Redis Streams (Synaptic Conclave)
REDIS_HOST=omni_redis
REDIS_PORT=6379

# PostgreSQL (Audit Storage)
POSTGRES_HOST=omni_postgres
POSTGRES_PORT=5432
POSTGRES_DB=vitruvyan_omni
POSTGRES_USER=vitruvyan_user
POSTGRES_PASSWORD=<secret>

# Test Mode (Disables DB/Redis for unit tests)
VITRUVYAN_TEST_MODE=false
```

### Docker Compose Config
```yaml
vitruvyan_api_orthodoxy_wardens:
  build:
    context: ../..
    dockerfile: infrastructure/docker/dockerfiles/Dockerfile.orthodoxy_wardens
  container_name: omni_api_orthodoxy_wardens
  ports:
    - "9006:8006"
  volumes:
    - ../../services/governance/api_orthodoxy_wardens:/app/api_orthodoxy_wardens:ro
    - ../../vitruvyan_core/core:/app/core:ro
  environment:
    - PYTHONPATH=/app
    - REDIS_HOST=omni_redis
    - POSTGRES_HOST=omni_postgres
  depends_on:
    - omni_redis
    - omni_postgres
```

---

## 📊 Performance Metrics

**Startup Time**: ~3-5 seconds (includes 5 Sacred Role initializations + 7 consumer group creations)  
**Memory Footprint**: ~150-200 MB (Python 3.11 + FastAPI + dependencies)  
**Event Processing Latency**: <50ms per event (Redis Streams consumption)  
**API Response Time**: <100ms (health check), 200-500ms (audit initiation)

**Scalability**: Horizontal scaling supported via consumer group architecture (add more consumers with same group_name).

---

## 🐛 Troubleshooting

### Issue: Container exits immediately
**Symptoms**: `docker ps` shows no orthodoxy container running
**Diagnosis**: `docker logs omni_api_orthodoxy_wardens` shows ModuleNotFoundError
**Solution**:
```bash
# Rebuild with latest code
docker compose build vitruvyan_api_orthodoxy_wardens
docker compose up -d vitruvyan_api_orthodoxy_wardens
```

### Issue: API not responding on port 9006
**Symptoms**: `curl http://localhost:9006/divine-health` → Connection refused
**Diagnosis**: Port mapping issue or container not started
**Solution**:
```bash
# Check port mapping
docker ps | grep orthodoxy
# Expected: 0.0.0.0:9006->8006/tcp

# Check container logs
docker logs omni_api_orthodoxy_wardens --tail=100 | grep "Uvicorn running"
# Expected: "Uvicorn running on http://0.0.0.0:8006"
```

### Issue: Events not consumed
**Symptoms**: Events in Redis Streams but no processing logs
**Diagnosis**: Consumer group not created or listener thread crashed
**Solution**:
```bash
# Verify consumer groups exist
docker exec omni_redis redis-cli XINFO GROUPS "vitruvyan:stream:orthodoxy.audit.requested"
# Expected: group:orthodoxy_main present

# Check listener thread status
docker logs omni_api_orthodoxy_wardens | grep "listeners thread started"
# Expected: "🔥 Synaptic Conclave listeners thread started"

# If missing, restart container
docker compose restart vitruvyan_api_orthodoxy_wardens
```

### Issue: "Permission denied" Docker errors
**Symptoms**: ERROR logs about Docker client connection
**Diagnosis**: Expected behavior (AutoCorrector tries Docker operations but fails inside container)
**Solution**: These are non-critical warnings, service functions normally without Docker management capabilities.

---

## 📚 Further Reading

- **Implementation Guide**: [ORTHODOXY_WARDENS_GUIDE.md](./ORTHODOXY_WARDENS_GUIDE.md) - Deep dive into Sacred Roles, event handlers, agent integration
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md) - Complete endpoint documentation with examples
- **Architectural Decisions**: [ARCHITECTURAL_DECISIONS.md](./ARCHITECTURAL_DECISIONS.md) - Why theological metaphors? Why event-driven? Design rationale.
- **Synaptic Conclave Docs**: `vitruvyan_core/core/synaptic_conclave/docs/COGNITIVE_BUS_GUIDE.md` - Redis Streams architecture
- **Refactoring Plan**: `SACRED_ORDERS_REFACTORING_PLAN.md` - P1-P4 roadmap for all Sacred Orders

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.3.0** | Feb 8, 2026 | P1 FASE 3: Business logic separation (core/ created, -21% main.py code) |
| **1.2.0** | Feb 8, 2026 | P1 FASE 2: English documentation, README upgrade |
| **1.1.0** | Feb 8, 2026 | P1 FASE 1: Synaptic Conclave listeners activated (7 channels) |
| **1.0.0** | Jan 2026 | Initial production deployment |

---

## 🤝 Contributing

**Before modifying**:
1. Read [ORTHODOXY_WARDENS_GUIDE.md](./ORTHODOXY_WARDENS_GUIDE.md) for architecture context
2. Test changes locally before Docker build
3. Follow Sacred Roles pattern (event-driven wrappers)
4. Update documentation if adding endpoints or modifying behavior

**Testing checklist**:
```bash
# 1. Import test
python3 -c "from services.governance.api_orthodoxy_wardens.core.roles import OrthodoxConfessor"

# 2. Docker build
docker compose build vitruvyan_api_orthodoxy_wardens

# 3. Integration test
docker compose up -d vitruvyan_api_orthodoxy_wardens
curl http://localhost:9006/divine-health
```

---

**Maintainer**: Vitruvyan Core Team  
**License**: Proprietary  
**Last Updated**: February 8, 2026
