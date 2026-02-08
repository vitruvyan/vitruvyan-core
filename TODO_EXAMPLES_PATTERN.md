# TODO - Examples Pattern Rollout
**Created**: 2026-02-08  
**Context**: Establishing service-level examples/ pattern across Sacred Orders

---

## 🔴 PRIORITY 1 - Critical Bugs (Blockers)

### 1. Fix Neural Engine MockDataProvider Bug
**Status**: 🔴 BLOCKING  
**Time Estimate**: 30-45 min  
**Issue**: DataFrame entity_name concatenation causes `"Could not convert string 'Entity 1Entity 2...' to numeric"`  
**File**: `vitruvyan_core/core/neural_engine/domain_examples/mock_data_provider.py` (line ~100)  
**Impact**: All Neural Engine screening/ranking tests fail  

**Steps**:
- [ ] Read `mock_data_provider.py` get_universe() method (lines 60-110)
- [ ] Fix DataFrame construction (ensure entity_name is array, not concatenated string)
- [ ] Rebuild container: `docker compose build vitruvyan_api_neural`
- [ ] Re-test: `cd services/core/api_neural_engine/examples && ./02_screen_basic.sh`
- [ ] Test remaining scripts: 03, 04, 05, 06
- [ ] Commit fix with message: `"fix(neural_engine): MockDataProvider DataFrame construction bug"`

**Success Criteria**: All 6 Neural Engine example scripts pass without errors

---

### 2. Debug Orthodoxy Wardens Database Corruption
**Status**: 🔴 BLOCKING  
**Time Estimate**: 45-60 min  
**Issue**: `orthodoxy_db_manager` status = "corrupted" blocks PostgreSQL queries  
**Impact**: Logs query and audit workflow tests fail (2/3 scripts blocked)  

**Steps**:
- [ ] Check Docker logs: `docker logs omni_api_orthodoxy_wardens --tail 100 | grep -i "database\|postgres"`
- [ ] Verify PostgreSQL connection from container:
  ```bash
  docker exec omni_api_orthodoxy_wardens python3 -c "from core.leo.postgres_agent import PostgresAgent; pg = PostgresAgent(); print(pg.connection.closed)"
  ```
- [ ] Check `orthodoxy_db_manager` initialization in `main.py` (around line 100-150)
- [ ] Fix connection/initialization issue
- [ ] Restart container: `docker compose restart vitruvyan_api_orthodoxy_wardens`
- [ ] Re-test: `./03_query_recent_logs.sh` and `python3 02_initiate_audit.py`

**Success Criteria**: `divine-health` shows `orthodoxy_db: "blessed"`, all 3 scripts pass

---

## 🟡 PRIORITY 2 - Pattern Expansion (Next Services)

### 3. Create Vault Keepers examples/
**Status**: ⏳ TODO  
**Time Estimate**: 1h  
**Pattern**: Apply same structure as Orthodoxy Wardens  

**Files to Create**:
- [ ] `services/governance/api_vault_keepers/examples/README.md` (2-3K)
- [ ] `01_health_check.sh` (test /health or /vault-status)
- [ ] `02_archive_request.sh` (POST archive request)
- [ ] `03_query_archived_data.py` (Query archived Neural Engine results)

**Port**: Check docker-compose.yml for Vault Keepers external port

---

### 4. Create Babel Gardens examples/
**Status**: ⏳ TODO  
**Time Estimate**: 1h  
**Pattern**: Same hybrid bash/Python approach  

**Files to Create**:
- [ ] `services/core/api_babel_gardens/examples/README.md`
- [ ] `01_health_check.sh`
- [ ] `02_sentiment_analysis.sh` (POST /v1/sentiment/batch)
- [ ] `03_emotion_detection.sh` (POST /v1/emotion/detect)
- [ ] `04_language_detection.py` (test 84 language support)

**Port**: 8009 (external), 8009 (internal) - check docker-compose.yml

---

### 5. Create Memory Orders examples/
**Status**: ⏳ TODO  
**Time Estimate**: 1h  

**Files to Create**:
- [ ] `services/governance/api_memory_orders/examples/README.md`
- [ ] `01_health_check.sh`
- [ ] `02_sync_memory.sh` (PostgreSQL ↔ Qdrant sync)
- [ ] `03_query_embeddings.py` (Query Qdrant collections)

---

## 🟢 PRIORITY 3 - Root E2E Tests (Future)

### 6. Create Root examples/ Directory
**Status**: ⏳ TODO  
**Time Estimate**: 2-4h  
**Purpose**: E2E pipeline tests (LangGraph orchestration)  

**Structure**:
```
examples/
├── README.md (E2E testing guide)
├── 01_single_ticker_analysis.py (Intent → Neural → VEE)
├── 02_comparison_workflow.py (Comparison node → Neural Engine 2 tickers)
├── 03_portfolio_review_flow.py (Portfolio → Orthodoxy audit → Sentinel)
├── 04_sentiment_pipeline.py (Babel Gardens → Neural → VEE)
└── 05_full_pipeline_stress_test.py (All Sacred Orders)
```

**Dependencies**: All service-level examples/ must pass first

---

## 📚 PRIORITY 4 - Documentation Updates

### 7. Update Main README.md
**Status**: ⏳ TODO  
**Time Estimate**: 30 min  

**Changes**:
- [ ] Add "Testing" section with examples/ pattern explanation
- [ ] Link to service-level examples/
- [ ] Document hybrid bash/Python approach (80/20 rule)
- [ ] Add "When to use" decision matrix

---

### 8. Create TESTING_GUIDE.md
**Status**: ⏳ TODO  
**Time Estimate**: 1h  

**Content**:
- [ ] Philosophy: Service-level vs E2E testing
- [ ] Pattern established: examples/ directory structure
- [ ] Bash for documentation, Python for workflows
- [ ] How to add tests to new services
- [ ] CI/CD integration (future)

---

## 🔄 Session Recap (2026-02-08)

### ✅ Completed Today
- [x] Pull Neural Engine refactoring from other VPS (commit f737847, +4,644 lines)
- [x] Read architecture docs (NEURAL_ENGINE_ARCHITECTURE, contracts/, api_neural_engine/)
- [x] Decided testing strategy: Hierarchical examples/ (service + root)
- [x] Created Neural Engine examples/ (7 files: 4 bash, 2 Python, README)
- [x] Updated docker-compose.yml to enable Neural Engine
- [x] Fixed stratification_mode bug in engine_orchestrator.py
- [x] Docker build + launch Neural Engine (container running)
- [x] Tested health endpoint (SUCCESS ✅)
- [x] Discovered MockDataProvider bug (documented in commit ad890d5)
- [x] Created Orthodoxy Wardens examples/ (4 files: 2 bash, 1 Python, README)
- [x] Tested Orthodoxy scripts (1/3 pass, 2/3 blocked by DB)
- [x] Committed partial work (2 commits: ad890d5, 45d3df2)

### ⚠️ Known Issues
1. **Neural Engine**: MockDataProvider DataFrame bug (screening fails)
2. **Orthodoxy Wardens**: Database corrupted (logs/audit blocked)

### 📊 Progress
- **Services with examples/**: 2/7 (Neural Engine ⚠️, Orthodoxy Wardens ⚠️)
- **Fully passing tests**: 1/2 services (50%)
- **Pattern established**: ✅ Hybrid bash/Python, service-level structure

---

## 🎯 Recommended Next Session Plan

**Session 1** (2-3h):
1. Fix Neural Engine MockDataProvider (30-45 min)
2. Debug Orthodoxy database corruption (45-60 min)
3. Re-test all scripts (15 min)
4. Commit fixes (10 min)

**Session 2** (2-3h):
1. Create Vault Keepers examples/ (1h)
2. Create Babel Gardens examples/ (1h)
3. Test + commit (30 min)

**Session 3** (3-4h):
1. Create Memory Orders examples/ (1h)
2. Create root examples/ E2E tests (2-3h)
3. Update documentation (1h)

---

## 📝 Notes

**Pattern Validation**: After 2 services (Neural, Orthodoxy), pattern is solid:
- 80% bash scripts for simple API calls (health, single endpoint)
- 20% Python for complex workflows (polling, multi-step, comparisons)
- Service-level examples/ test components in isolation
- Root examples/ (future) test full pipeline orchestration

**Blockers**: Both services have runtime issues (MockDataProvider, DB corruption), but **scripts are syntactically correct**. Pattern is reusable.

**Git Commits**:
- `ad890d5`: Neural Engine examples + docker-compose + partial bugfix
- `45d3df2`: Orthodoxy Wardens examples (3 scripts + README)

**Next Git State**: After Priority 1 fixes, commit:
- Neural Engine MockDataProvider fix
- Orthodoxy database fix
- Updated test results in example READMEs

---

## 🚀 Quick Start (Next Session)

```bash
# 1. Fix Neural Engine MockDataProvider
cd /home/vitruvyan/vitruvyan-core
vim vitruvyan_core/core/neural_engine/domain_examples/mock_data_provider.py
# Fix DataFrame construction around line 100
docker compose build vitruvyan_api_neural
docker compose up -d vitruvyan_api_neural
cd services/core/api_neural_engine/examples
./02_screen_basic.sh  # Should now pass

# 2. Debug Orthodoxy Database
docker logs omni_api_orthodoxy_wardens --tail 100 | grep -i database
docker exec omni_api_orthodoxy_wardens python3 -c "from core.leo.postgres_agent import PostgresAgent; pg = PostgresAgent(); print(pg.connection.closed)"
# Fix connection issue in main.py
docker compose restart vitruvyan_api_orthodoxy_wardens
cd /home/vitruvyan/vitruvyan-core/services/governance/api_orthodoxy_wardens/examples
./03_query_recent_logs.sh  # Should now pass
python3 02_initiate_audit.py  # Should complete workflow

# 3. Commit Fixes
git add -A
git commit -m "fix: Neural Engine MockDataProvider + Orthodoxy DB initialization"
```

---

**END OF TODO LIST**
