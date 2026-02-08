# Sacred Orders Refactoring Plan - Feb 8, 2026

## 🎯 Status Attuale

### ✅ Synaptic Conclave (Cognitive Bus)
**Status**: ✅ OPERATIVO - Refactoring completato FASE 1-5
- **Container**: `omni_api_conclave` (Up 18 minutes, HEALTHY)
- **Listeners**: 1/5 operativo (`api_conclave_listener`)
- **Architettura**: 100% Redis Streams, zero Pub/Sub
- **Documentazione**: Blueprint completo (`STANDALONE_SERVICES_REFACTORING_PATTERN.md`)

### ⚠️ Listeners Status
| Listener | Status | Issue |
|----------|--------|-------|
| `api_conclave_listener` | ✅ HEALTHY | Operativo, 30+ consumer groups creati |
| `orthodoxy_wardens_listener` | ⚠️ UP | File `streams_listener.py` presente |
| `vault_keepers_listener` | ❌ CRASH LOOP | File `streams_listener.py` NON copiato nel container |
| `babel_gardens_listener` | ❌ CRASH LOOP | File `streams_listener.py` NON copiato nel container |
| `codex_hunters_listener` | ❌ CRASH LOOP | File `streams_listener.py` NON copiato nel container |

**Root Cause**: Listener code creato solo per `api_conclave`, non copiato negli altri container durante il build.

### 🏛️ Sacred Orders da Refactorare
| Service | Location | Status | Priority |
|---------|----------|--------|----------|
| Orthodoxy Wardens | `services/governance/api_orthodoxy_wardens/` | 🟡 Listener parziale | P1 |
| Vault Keepers | `services/governance/api_vault_keepers/` | 🟡 Listener parziale | P1 |
| Babel Gardens | `services/core/api_babel_gardens/` | 🟡 Listener parziale | P2 |
| Codex Hunters | `services/core/api_codex_hunters/` | 🟡 Listener parziale | P2 |
| Memory Orders | `services/core/api_memory_orders/` | 🔴 Legacy structure | P3 |
| Pattern Weavers | `services/core/api_pattern_weavers/` | 🔴 Legacy structure | P4 |

---

## 📚 Documentazione di Riferimento

### Blueprint Principale
**File**: `STANDALONE_SERVICES_REFACTORING_PATTERN.md` (771 lines)
**Sections**:
- 🏛️ The Cognitive Bus Pattern (reference implementation)
- 📐 The Refactoring Pattern (7 Phases)
- 📋 Service-Specific Guidelines (Neural Engine, LangGraph, Codex, Leo)
- 🚨 Common Pitfalls & Solutions
- ✅ Refactoring Checklist (comprehensive)

### Supporting Documentation
1. **ARCHITECTURAL_REFACTORING_FEB6_2026.md** (264 lines)
   - Motivazione del refactor
   - Cognitive Bus move: `core/cognitive_bus/` → `vitruvyan_core/core/cognitive_bus/`
   - Eliminazione `foundation/` → `agents/`, `llm/`, `cache/`, `governance/`

2. **COGNITIVE_BUS_REFACTORING_VALIDATION_PROMPT.md** (416 lines)
   - FASE 1: Listener Separation (6 listeners, 2,153 lines)
   - FASE 2: Directory Organization (14 root files → 7 directories)
   - FASE 3: Import Path Cleanup
   - Validation checklist

3. **TODO_API_CONCLAVE_REFACTORING.md**
   - api_conclave complete rewrite (692 → 229 lines, -67%)
   - 100% Streams architecture
   - E2E tests passed

---

## 🏛️ Pattern di Refactoring (7 Fasi)

### FASE 1: Business Logic Separation
**Goal**: Separare domain logic da deployment code

**Example (Cognitive Bus)**:
```
Before:
docker/services/api_*/streams_listener.py (300+ lines business logic)

After:
core/cognitive_bus/listeners/codex_hunters.py (323 lines)
docker/services/api_codex_hunters/streams_listener.py (thin wrapper, <80 lines)
```

**Benefit**: Business logic testabile senza Docker

---

### FASE 2: Directory Organization
**Goal**: Struttura flat → Logical grouping

**Recommended Structure**:
```
services/<domain>/api_<service>/
├── __init__.py
├── client/ (SDK wrappers, convenience classes)
├── core/ or engine/ (core algorithms, business logic)
├── models/ or schemas/ (data models, Pydantic schemas)
├── api/ or routes/ (FastAPI endpoints)
├── monitoring/ (metrics, health checks)
├── governance/ (validation, compliance)
├── utils/ (helpers, config)
├── philosophy/ (design docs - OPTIONAL)
└── docs/ (unified documentation)
    ├── README.md (entry point, 300-400 lines)
    ├── <SERVICE>_GUIDE.md (implementation, 800-1,200 lines)
    ├── API_REFERENCE.md (API docs, 500-800 lines)
    └── ARCHITECTURAL_DECISIONS.md (design rationale, 600-1,000 lines)
```

**Benefit**: Intuitive navigation, "Where is X?" → "Check `<directory>/`"

---

### FASE 3: Import Path Cleanup
**Goal**: Fix obsolete imports after moves

**Common Patterns**:
```python
# ❌ OLD: Obsolete after move
from ..module import X

# ✅ NEW: After file moved to subdir/
from ..subdir.module import X
```

**Test**:
```bash
python3 -c "from services.governance.api_orthodoxy_wardens.core import X; print('✅')"
```

---

### FASE 4: Documentation Unification
**Goal**: Fragmented docs → 3 core guides + README

**Required Files**:
1. **README.md** (300-400 lines): What, Quick start, Architecture, Links
2. **<SERVICE>_GUIDE.md** (800-1,200 lines): Setup, Concepts, API usage, Best practices
3. **API_REFERENCE.md** (500-800 lines): Classes, functions, parameters, examples
4. **ARCHITECTURAL_DECISIONS.md** (600-1,000 lines): Why X over Y, Trade-offs, Evolution

**Benefit**: 45-min onboarding (vs 4-6h before)

---

### FASE 5: Testing & Validation
**Test Checklist**:
```bash
# 1. Import test (no Docker)
python3 -c "from services.governance.api_orthodoxy_wardens import X; print('✅')"

# 2. Structural verification
ls -1 services/governance/api_orthodoxy_wardens/ | grep -E "core|models|api|monitoring|docs"

# 3. Circular dependency check
python3 -c "import services.governance.api_orthodoxy_wardens; print('No circular imports')"

# 4. Rebuild service
docker compose build api_orthodoxy_wardens
docker compose up -d api_orthodoxy_wardens
docker logs omni_api_orthodoxy_wardens --tail=50
```

---

### FASE 6: Git Commit
**Message Template**:
```
refactor(<service>): FASE 1-5 - Standalone service pattern

FASE 1: Business logic separation (moved X files, Y lines)
FASE 2: Directory organization (Z directories)
FASE 3: Import path cleanup (N files updated)
FASE 4: Documentation unification (4 core guides)
FASE 5: Testing & validation (all checks passed)

Result: Professional structure, 45-min onboarding, multi-repo ready

Files changed: [count]
Lines: [insertions/deletions]
Docs: [names]
```

---

### FASE 7: Listener Integration (Sacred Orders Specific)
**Goal**: Integrare Streams listener nel container

**Actions**:
1. Verify `streams_listener.py` exists in service directory
2. Update Dockerfile to copy listener code
3. Rebuild container
4. Start listener
5. Verify consumer groups in Redis
6. Test event consumption

**Example (Vault Keepers)**:
```dockerfile
# In Dockerfile.vault_keepers
COPY --chown=vitruvyan:vitruvyan services/governance/api_vault_keepers /app/api_vault_keepers

# Include streams_listener.py
```

```bash
# Test
docker compose build api_vault_keepers_listener
docker compose up -d api_vault_keepers_listener
docker logs omni_vault_keepers_listener --tail=50
# Expected: Consumer groups created, no errors
```

---

## 🎯 Priority Queue (Ordine di Refactoring)

### P1 - IMMEDIATE (Next 2-3 days)
**Services**: Orthodoxy Wardens, Vault Keepers

**Why**: Core governance services, già hanno `streams_listener.py`, solo manca integrazione container

**Tasks**:
1. ✅ Fix listener crash loop (copy code to containers)
2. 🔄 FASE 1: Separate audit logic from deployment
3. 🔄 FASE 2: Organize directories (core, models, api, monitoring, docs)
4. 🔄 FASE 3: Clean imports
5. 🔄 FASE 4: Create 4 core docs
6. 🔄 FASE 5: Test + rebuild
7. 🔄 FASE 6: Commit
8. 🔄 FASE 7: Validate listener integration

**Estimated Effort**: 4-6h per service (8-12h total)

---

### P2 - HIGH (Next 3-5 days)
**Services**: Babel Gardens, Codex Hunters

**Why**: Core services, hanno `streams_listener.py`, alta importanza architetturale

**Tasks**: Same as P1

**Estimated Effort**: 4-6h per service (8-12h total)

---

### P3 - MEDIUM (Next 7-10 days)
**Services**: Memory Orders

**Why**: Critical for memory coherence, ma più stabile quindi meno urgente

**Tasks**: Full FASE 1-6 (no listener, focus on API structure)

**Estimated Effort**: 6-8h

---

### P4 - LOWER (Next 10-14 days)
**Services**: Pattern Weavers

**Why**: Semantic contextualization, meno critico per operational stability

**Tasks**: Full FASE 1-6

**Estimated Effort**: 6-8h

---

## 📋 Per-Service Refactoring Checklist

### Orthodoxy Wardens (P1)
```
Planning:
- [ ] List all files (Python, docs, configs)
- [ ] Identify business logic (audit, validation, heresy detection)
- [ ] Plan directory structure (core, models, api, monitoring, governance, docs)

FASE 1: Business Logic Separation
- [ ] Create `api_orthodoxy_wardens/core/` (audit logic)
- [ ] Move audit functions from `main.py` to `core/audit_engine.py`
- [ ] Update `main.py` to thin FastAPI wrapper
- [ ] Test: Import audit_engine without Docker

FASE 2: Directory Organization
- [ ] Create: core/, models/, api/, monitoring/, governance/, utils/, docs/
- [ ] Move files to directories
- [ ] Create __init__.py in each directory
- [ ] Test: Directory structure intuitive

FASE 3: Import Path Cleanup
- [ ] Search obsolete imports: grep -rn "from ..[module]"
- [ ] Batch update import paths
- [ ] Remove centralized imports in __init__.py
- [ ] Test: python3 -c "from services.governance.api_orthodoxy_wardens.core import X"

FASE 4: Documentation
- [ ] Create README.md (entry point)
- [ ] Create ORTHODOXY_WARDENS_GUIDE.md (audit system explanation)
- [ ] Create API_REFERENCE.md
- [ ] Create ARCHITECTURAL_DECISIONS.md
- [ ] Archive old docs to docs/history/

FASE 5: Testing
- [ ] Import test (no Docker)
- [ ] Structural verification
- [ ] Circular dependency check
- [ ] Rebuild: docker compose build api_orthodoxy_wardens
- [ ] Start: docker compose up -d api_orthodoxy_wardens
- [ ] Logs: docker logs omni_api_orthodoxy_wardens --tail=50

FASE 6: Git Commit
- [ ] Commit with comprehensive message
- [ ] Tag: refactor/orthodoxy_wardens_v1

FASE 7: Listener Integration
- [ ] Verify streams_listener.py copied to container
- [ ] Rebuild listener: docker compose build api_orthodoxy_wardens_listener
- [ ] Start listener: docker compose up -d api_orthodoxy_wardens_listener
- [ ] Verify consumer groups: docker exec omni_redis redis-cli XINFO GROUPS "vitruvyan:stream:orthodoxy.audit.requested"
- [ ] Test event consumption
```

### Vault Keepers (P1)
```
[Same checklist structure as Orthodoxy Wardens]

Key Differences:
- Business logic: Archival, retrieval, snapshot creation
- Core modules: core/vault_engine.py, core/archival.py
- Documentation focus: Archival system, versioning, retrieval
```

### Babel Gardens (P2)
```
[Same checklist structure]

Key Differences:
- Business logic: Sentiment fusion, emotion detection, multilingual processing
- Core modules: core/sentiment_fusion.py, core/embedding_engine.py
- Documentation focus: FinBERT integration, Gemma emotion detection, 84 languages
```

### Codex Hunters (P2)
```
[Same checklist structure]

Key Differences:
- Business logic: Reddit scraping, news collection, data mapping
- Core modules: hunters/event_hunter.py, hunters/tracker.py, hunters/restorer.py
- Documentation focus: Async data collection, expedition scheduling
```

---

## 🚨 Common Pitfalls (Sacred Orders Specific)

### Pitfall 1: PostgresAgent/QdrantAgent Dependency
**Issue**: Services need PostgresAgent/QdrantAgent but they live in `vitruvyan_core/core/agents/`
**Solution**: 
- Import from core: `from vitruvyan_core.core.agents import PostgresAgent`
- Docker PYTHONPATH: `/app/vitruvyan_core` in PYTHONPATH
- Test: `python3 -c "from vitruvyan_core.core.agents import PostgresAgent"`

### Pitfall 2: Listener Crash Loop
**Issue**: `streams_listener.py` not copied to container during build
**Solution**:
- Update Dockerfile: `COPY services/<domain>/api_<service> /app/api_<service>`
- Verify: `docker exec <container> ls -la /app/api_<service>/streams_listener.py`

### Pitfall 3: Redis Connection Errors
**Issue**: Listener can't connect to Redis (wrong host)
**Solution**:
- Environment: `REDIS_HOST=omni_redis` (NOT localhost)
- Network: `networks: [omni-net]` in docker-compose.yml
- Test: `docker exec <listener> ping omni_redis`

### Pitfall 4: Consumer Group Conflicts
**Issue**: Multiple listeners try to create same consumer group
**Solution**:
- Use unique group names: `group:orthodoxy_watcher` (NOT `group:watcher`)
- Check existing groups: `docker exec omni_redis redis-cli XINFO GROUPS "vitruvyan:stream:X"`

### Pitfall 5: Missing Sacred Orders Dependencies
**Issue**: Service needs StreamBus but Synaptic Conclave not imported
**Solution**:
- Import: `from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus`
- Docker volume: Mount `vitruvyan_core/` in all containers
- Test: `python3 -c "from vitruvyan_core.core.synaptic_conclave import StreamBus"`

---

## 🎯 Success Metrics

### Container Health
```bash
# Expected: All listeners HEALTHY, no restarts
docker ps --format "table {{.Names}}\t{{.Status}}" | grep listener
```

### Consumer Groups
```bash
# Expected: 5+ consumer groups per sacred channel
docker exec omni_redis redis-cli KEYS "vitruvyan:stream:*" | wc -l
docker exec omni_redis redis-cli XINFO GROUPS "vitruvyan:stream:orthodoxy.audit.requested"
```

### Event Flow
```bash
# Test: Emit event → Verify consumption
curl -X POST http://localhost:9012/emit/orthodoxy.audit.requested \
  -H "Content-Type: application/json" \
  -d '{"data": {"test": "refactoring_validation"}}'

# Check pending (should be 0 after consumption)
docker exec omni_redis redis-cli XPENDING "vitruvyan:stream:orthodoxy.audit.requested" "group:orthodoxy_watcher"
```

### Documentation
```bash
# Expected: 4 core docs per service
ls -lh services/governance/api_orthodoxy_wardens/docs/{README.md,*_GUIDE.md,API_REFERENCE.md,ARCHITECTURAL_DECISIONS.md}
```

---

## 📅 Timeline Estimate

| Phase | Services | Duration | Status |
|-------|----------|----------|--------|
| **Week 1** | Orthodoxy Wardens, Vault Keepers (P1) | 8-12h | 🔄 In Progress |
| **Week 2** | Babel Gardens, Codex Hunters (P2) | 8-12h | ⏳ Pending |
| **Week 3** | Memory Orders (P3) | 6-8h | ⏳ Pending |
| **Week 4** | Pattern Weavers (P4) | 6-8h | ⏳ Pending |

**Total Effort**: 28-40 hours over 4 weeks

---

## ✅ Next Actions (IMMEDIATE)

### 1. Fix Listener Crash Loop (30 min)
```bash
# Rebuild containers with streams_listener.py included
cd /home/vitruvyan/vitruvyan-core/infrastructure/docker
docker compose build api_vault_keepers_listener api_babel_gardens_listener api_codex_hunters_listener
docker compose up -d api_vault_keepers_listener api_babel_gardens_listener api_codex_hunters_listener

# Verify
docker logs omni_vault_keepers_listener --tail=50
docker logs omni_babel_gardens_listener --tail=50
docker logs omni_codex_hunters_listener --tail=50
```

### 2. Start Orthodoxy Wardens Refactoring (4-6h)
```bash
# Create branch
git checkout -b refactor/orthodoxy-wardens-phase1

# Follow checklist above (FASE 1-7)
# Commit after each FASE for incremental validation
```

### 3. Document Progress
```bash
# Create tracking doc
touch docs/SACRED_ORDERS_REFACTORING_PROGRESS.md

# Update after each service completion
```

---

## 🎓 Learning Resources

**Primary Blueprint**: `STANDALONE_SERVICES_REFACTORING_PATTERN.md` (771 lines)
**Reference Implementation**: `vitruvyan_core/core/synaptic_conclave/` (Cognitive Bus)
**Cognitive Bus Docs**: `core/synaptic_conclave/docs/COGNITIVE_BUS_GUIDE.md` (988 lines)

**Industry Examples**:
- FastAPI: `fastapi/` structure (routing, dependencies, security)
- Celery: `celery/` structure (app, worker, backends, utils)
- SQLAlchemy: `sqlalchemy/` structure (engine, orm, sql, ext)

---

**Created**: February 8, 2026 18:45 UTC  
**Status**: 🔄 ACTIVE - Refactoring in Progress  
**Next Review**: After P1 completion (Orthodoxy Wardens + Vault Keepers)
