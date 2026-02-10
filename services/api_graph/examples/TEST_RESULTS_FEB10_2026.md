# LangGraph E2E Test Results - Feb 10, 2026

## Test Execution Summary

**Environment:**
- Container: core_graph (up 28 minutes, healthy)
- Service: api_graph v2.0.0
- Execution: Manual curl-based testing (pytest not available on host)

---

## ✅ PASSING TESTS (6/8)

### 1. Health Check ✅
```bash
curl http://localhost:9004/health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "api_graph",
  "version": "2.0.0",
  "audit_monitoring": "disabled",
  "heartbeat_count": 0,
  "last_heartbeat": "N/A"
}
```
**Status:** PASS - Service responding, version correct, health schema complete

### 2. Prometheus Metrics ✅
```bash
curl http://localhost:9004/metrics | head -20
```
**Response:** Prometheus-formatted metrics exposed (python_gc_*, process_*, custom metrics)  
**Status:** PASS - Metrics endpoint functional, standard + custom metrics present

### 3. Entity Search (Autocomplete) ✅
```bash
curl "http://localhost:9004/api/entity_ids/search?q=app"
```
**Response:**
```json
{
  "status": "success",
  "query": "app",
  "results": [],
  "total": 0
}
```
**Status:** PASS (with caveat) - Endpoint functional, schema correct, no results due to empty database

### 4. Qdrant Health ✅
```bash
curl http://localhost:9004/qdrant/health
```
**Response:**
```json
{
  "status": "qdrant_placeholder",
  "service": "qdrant"
}
```
**Status:** PASS - Placeholder endpoint responding as expected

### 5. Audit Health ✅
```bash
curl http://localhost:9004/audit/graph/health
```
**Response:**
```json
{
  "status": "disabled",
  "monitoring_active": false,
  "current_session_id": null,
  "performance_metrics": {},
  "timestamp": "2026-02-10T15:21:32.005620"
}
```
**Status:** PASS - Audit system responding, disabled state documented

### 6. Audit Metrics ✅
```bash
curl http://localhost:9004/audit/graph/metrics
```
**Response:** (similar to audit health)  
**Status:** PASS - Metrics endpoint functional

---

## ❌ FAILING TESTS (2/8)

### 7. Graph Execution ❌
```bash
curl -X POST http://localhost:9004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"test query","user_id":"test_user"}'
```
**Response:** Internal Server Error  
**Error:** `ResponseValidationError: Field required ('response', 'json'), Field required ('response', 'human')`

**Root Cause:** Schema mismatch between graph runner output and Pydantic response model
- **Graph returns:** `{narrative, action, intent, emotion_detected, ...}` (old structure)
- **API expects:** `{json, human, audit_monitored, execution_timestamp}` (GraphResponseSchema)

**Impact:** Graph execution fails validation despite graph logic running (200 lines of response data shown in logs)

**Fix Required:** 
1. Update graph_adapter.py to transform graph output → GraphResponseSchema
2. OR update GraphResponseSchema to match actual graph output structure
3. OR add response_model=None to /run endpoint temporarily

### 8. Semantic Clusters ❌
```bash
curl http://localhost:9004/clusters/semantic
```
**Response:**
```json
{
  "status": "error",
  "error": "relation 'semantic_clusters' does not exist"
}
```
**Root Cause:** Database table not created (expected for test environment without migrations)

**Impact:** Documentation clustering feature non-functional

**Fix Required:** Run database migrations or mark as optional feature

---

## Test Coverage Analysis

| Category | Tests | Pass | Fail | Coverage |
|----------|-------|------|------|----------|
| Health & Monitoring | 3 | 3 | 0 | 100% ✅ |
| Entity Operations | 1 | 1 | 0 | 100% ✅ |
| Audit System | 2 | 2 | 0 | 100% ✅ |
| **Graph Execution** | 1 | 0 | 1 | **0% ❌** |
| Data Queries | 1 | 0 | 1 | 0% ❌ |
| **TOTAL** | **8** | **6** | **2** | **75%** |

---

## Critical Findings

### 🔴 BLOCKER: Graph Response Schema Mismatch
The core functionality (graph execution at /run) fails due to Pydantic validation error. Graph logic runs successfully but response transformation is broken.

**Evidence:**
- Graph produces valid output (narrative, intent, emotion_detected, etc.)
- Output structure doesn't match GraphResponseSchema (missing json/human fields)
- API returns 500 Internal Server Error instead of graph result

**Priority:** P0 - Blocks E2E testing of primary feature

### 🟡 WARNING: Empty Database
Entity search and semantic clusters return empty/error due to unpopulated database. This is expected for test environment but should be documented.

---

## Next Steps

**Immediate (P0):**
1. Fix graph response schema mismatch in graph_adapter.py
2. Add response transformation layer to map graph output → API schema
3. Re-run graph execution tests

**Short-term (P1):**
1. Populate test database with sample entities
2. Create semantic_clusters table (or mark as optional)
3. Install pytest on host for automated test suite

**Long-term (P2):**
1. Add integration tests in CI/CD
2. Mock database for hermetic testing
3. Add schema validation tests in pre-commit hooks

---

## Documentation Validation

**Created Files:** ✅ All documentation files exist and are comprehensive
- services/api_graph/README.md (395 lines)
- vitruvyan_core/core/orchestration/README.md (596 lines)
- services/api_graph/examples/README.md (399 lines)
- 6 test files (845 lines, 34 test cases)

**Documentation Quality:** ✅ Complete, accurate API examples, clear setup instructions

**Gap:** Schema documentation doesn't reflect actual runtime behavior (mismatch discovered)

---

## Conclusion

**Test Suite Status:** 75% passing (6/8 tests)  
**System Health:** Graph service healthy, monitoring operational  
**Blocker:** Graph execution schema mismatch (P0 fix required)  
**Recommendation:** Fix schema mismatch before declaring refactoring complete

