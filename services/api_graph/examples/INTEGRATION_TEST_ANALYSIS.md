# LangGraph Integration Test Analysis — COO Report

**Date:** February 10, 2026  
**Status:** 🔴 **CRITICAL GAP IDENTIFIED**

---

## Executive Summary

**Current Test Status:** Surface-level validation ONLY (HTTP endpoints + schema compliance)  
**Integration Testing:** ❌ **NOT PERFORMED** — Sacred Orders integration never validated  
**Critical Discovery:** Sacred Orders listeners are **UNHEALTHY/RESTARTING** → Integration impossible

**Assessment:** While graph HTTP API is functional, **production-critical Sacred Orders integration is UNVALIDATED and currently BROKEN**.

---

## Test Coverage Analysis

### ✅ What Has Been Tested (Surface Layer)

| Test | Coverage | Value | Production Risk |
|------|----------|-------|-----------------|
| **HTTP Health** | 100% | Verifies service responds | LOW (basic connectivity) |
| **Prometheus Metrics** | 100% | Verifies monitoring exposed | LOW (observability) |
| **Entity Search** | 100% | Verifies API schema | LOW (no DB dependency tested) |
| **Graph Execution** | 100% | Verifies adapter transformation | **MEDIUM** (only validates HTTP surface, not graph flow) |
| **Audit System** | 100% | Verifies audit endpoints | LOW (disabled state) |

**Summary:** We tested the **API surface** (request → response schema), not the **graph execution flow** (nodes → Sacred Orders → Redis → responses).

**Value of Surface Tests:**
- ✅ Confirms service deploys correctly
- ✅ Confirms API contracts are valid (Pydantic schemas)
- ✅ Confirms adapter transformation works (domain → API)
- ❌ Does NOT confirm graph nodes execute correctly
- ❌ Does NOT confirm Sacred Orders integration works
- ❌ Does NOT confirm Redis Streams communication works

---

### ❌ What Has NOT Been Tested (Integration Layer)

| Component | Test Required | Current Status | Production Risk |
|-----------|---------------|----------------|-----------------|
| **Orthodoxy Node** | Graph → Redis → Orthodoxy Wardens → Redis → Graph | ❌ UNTESTED | 🔴 **CRITICAL** |
| **Vault Node** | Graph → Redis → Vault Keepers → Redis → Graph | ❌ UNTESTED | 🔴 **CRITICAL** |
| **Memory Orders** | Graph → Redis → Memory Orders → Redis → Graph | ❌ UNTESTED | 🔴 **CRITICAL** |
| **Redis Streams** | Event emission + consumption cycles | ❌ UNTESTED | 🔴 **CRITICAL** |
| **Event Correlation** | correlation_id tracking across services | ❌ UNTESTED | 🔴 **CRITICAL** |
| **Timeout Handling** | Sacred Orders timeout → emergency blessing | ❌ UNTESTED | 🟡 **HIGH** |
| **Error Propagation** | Sacred Order failure → graph continues | ❌ UNTESTED | 🟡 **HIGH** |

---

## Critical Discovery: Sacred Orders Listeners ARE DOWN

**Container Status (Feb 10, 2026 15:35 UTC):**

```bash
docker ps --format "{{.Names}}\t{{.Status}}"
```

| Service | Status | Health | Uptime |
|---------|--------|--------|--------|
| `core_orthodoxy_wardens` | Up | ✅ **healthy** | 2 hours |
| `core_orthodoxy_listener` | Up | ❌ **unhealthy** | 37 minutes |
| `core_vault_keepers` | Up | ⚠️ **starting** | 2 seconds |
| `core_vault_listener` | Up | ❌ **unhealthy** | 37 minutes |
| `core_memory_orders` | **Restarting** | ❌ **FAILED** | 11 seconds |
| `core_memory_orders_listener` | **Restarting** | ❌ **FAILED** | 27 seconds |

**Interpretation:**  
- **Sacred Orders services** (orthodoxy_wardens, vault_keepers) are healthy ✅
- **Listeners** (consume events from Redis Streams) are **UNHEALTHY** ❌
- **Memory Orders** is in **crash loop** (restarting every ~30 seconds) 🔴

**Impact:**  
- Graph can **emit events** to Redis Streams ✅
- Sacred Orders **CANNOT consume events** (listeners down) ❌
- Graph will **timeout waiting** for responses → **emergency blessings** applied
- Integration tests would **FAIL** even if written correctly

---

## Architecture: How Graph Integrates with Sacred Orders

### Expected Flow (When Healthy)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User sends query to /run endpoint                            │
│    POST /run {"input_text": "...", "user_id": "..."}           │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. graph_adapter.py executes LangGraph via run_graph_once()    │
│    → LangGraph builds state machine with nodes                  │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Graph executes nodes in sequence:                            │
│    - entity_resolver: Match entities to DB                      │
│    - screener: Calculate scores                                 │
│    - sentiment: Analyze sentiment                               │
│    - orthodoxy_node: 🏛️ REQUEST DIVINE AUDIT                   │
│    - vault_node: 🏰 REQUEST DIVINE PROTECTION                   │
│    - compose: Format response                                   │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. orthodoxy_node emits event to Redis Streams:                │
│    Channel: "orthodoxy.audit.requested"                         │
│    Payload: {graph_state_summary, session_id, timestamp}        │
│    correlation_id: "graph_audit_user123_1707580000"            │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. orthodoxy_listener (streams_listener.py) consumes event     │
│    → Calls orthodoxy_wardens service HTTP endpoint              │
│    → Warden performs confession + verdict analysis              │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Orthodoxy Wardens emits response to Redis Streams:          │
│    Channel: "orthodoxy.absolution.granted"                      │
│    Payload: {verdict, blessing, heresy_detected}                │
│    correlation_id: "graph_audit_user123_1707580000" (SAME)     │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. orthodoxy_node (in graph) listens for response:             │
│    → Subscribes to "orthodoxy.absolution.granted" channel      │
│    → Matches correlation_id to original request                 │
│    → Timeout: 10 seconds (fallback to emergency blessing)      │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Graph augments state with verdict and continues:            │
│    state["orthodoxy_verdict"] = verdict                         │
│    state["orthodoxy_blessing"] = blessing                       │
│    → Proceeds to vault_node (same flow)                         │
│    → Proceeds to compose_node (format response)                 │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. graph_adapter transforms final state → GraphResponseSchema  │
│    Returns: {json, human, audit_monitored, timestamp}          │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. FastAPI returns 200 OK to client                            │
└─────────────────────────────────────────────────────────────────┘
```

### Current Reality (Listeners Down)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1-3. Same as above (graph executes, emits event to Redis)      │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. orthodoxy_node emits event to Redis → ✅ SUCCESS            │
│    Event written to stream "orthodoxy.audit.requested"         │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. orthodoxy_listener SHOULD consume → ❌ LISTENER UNHEALTHY   │
│    Event sits in Redis stream, never consumed                   │
│    No HTTP call to orthodoxy_wardens                            │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. orthodoxy_node waits for response → ⏰ TIMEOUT (10 seconds) │
│    No "orthodoxy.absolution.granted" event received             │
│    Fallback: _apply_local_blessing(state, "divine_timeout")    │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Graph continues with emergency blessing (degraded mode)     │
│    state["orthodoxy_verdict"] = "emergency_blessing"            │
│    → Same for vault_node → emergency blessing                   │
│    → Same for memory_orders → skipped (service restarting)     │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9-10. Response returned but WITHOUT Sacred Orders validation   │
│    ⚠️ Production risk: No orthodoxy audit, no vault protection │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Test Requirements (COO Specification)

### Test 1: Orthodoxy Wardens Integration ✅ CRITICAL

**Purpose:** Verify graph → orthodoxy → graph round-trip with divine verdict

**Prerequisites:**
- orthodoxy_wardens container healthy ✅
- orthodoxy_listener container healthy ❌ (MUST FIX)
- Redis Streams operational ✅

**Test Steps:**
```python
# 1. Send graph execution request with audit trigger
response = httpx.post("http://localhost:9004/run", json={
    "input_text": "Should I invest in Apple?",  # Triggers audit
    "user_id": "integration_test_orthodoxy"
})

# 2. Verify response received (200 OK)
assert response.status_code == 200
data = response.json()

# 3. Verify orthodoxy verdict in graph output
parsed = json.loads(data["json"])
assert "orthodoxy_verdict" in parsed
assert parsed["orthodoxy_verdict"] != "emergency_blessing"  # Real verdict
assert parsed["orthodoxy_verdict"] in ["blessed", "heretical", "requires_confession"]

# 4. Check Redis Streams for event traces
redis_client = redis.Redis()
events = redis_client.xread({"orthodoxy.audit.requested": '0'}, count=10)
assert len(events) > 0  # Event was emitted

absolutions = redis_client.xread({"orthodoxy.absolution.granted": '0'}, count=10)
assert len(absolutions) > 0  # Response was received

# 5. Verify correlation_id matches
request_event = events[0][1][0][1]  # Last emitted event
response_event = absolutions[0][1][0][1]  # Last absolution
assert request_event[b'correlation_id'] == response_event[b'correlation_id']
```

**Expected Duration:** < 15 seconds (10s timeout + processing)  
**Success Criteria:**
- ✅ Graph emits event to Redis
- ✅ Ortodoxy listener consumes event
- ✅ Orthodoxy wardens processes confession
- ✅ Response emitted back to Redis
- ✅ Graph receives and applies verdict
- ✅ correlation_id matches across request/response

**Current Status:** ❌ BLOCKED (listener unhealthy)

---

### Test 2: Vault Keepers Integration ✅ CRITICAL

**Purpose:** Verify graph → vault → graph round-trip with divine protection

**Prerequisites:**
- vault_keepers container healthy ⚠️ (starting)
- vault_listener container healthy ❌ (MUST FIX)
- Redis Streams operational ✅

**Test Steps:**
```python
# 1. Send graph execution with vault protection trigger
response = httpx.post("http://localhost:9004/run", json={
    "input_text": "Backup my portfolio data",  # Triggers vault protection
    "user_id": "integration_test_vault"
})

# 2. Verify vault blessing applied
parsed = json.loads(response.json()["json"])
assert "vault_status" in parsed
assert parsed["vault_status"] != "emergency_blessing"
assert parsed["vault_status"] in ["blessed", "protected", "archived"]

# 3. Verify Redis event cycle
redis_client = redis.Redis()
protection_requests = redis_client.xread({"vault.protection.requested": '0'}, count=10)
assert len(protection_requests) > 0

blessings = redis_client.xread({"vault.protection.granted": '0'}, count=10)
assert len(blessings) > 0
```

**Expected Duration:** < 15 seconds  
**Success Criteria:**
- ✅ Vault keywords detected in input
- ✅ Protection request emitted
- ✅ Vault listener processes request
- ✅ Divine protection granted
- ✅ State augmented with vault blessing

**Current Status:** ❌ BLOCKED (listener unhealthy)

---

### Test 3: Memory Orders Integration 🔴 CRITICAL

**Purpose:** Verify graph → memory → graph with semantic memory operations

**Prerequisites:**
- memory_orders container healthy ❌ (RESTARTING — CRASH LOOP)
- memory_orders_listener container healthy ❌ (RESTARTING)
- Redis Streams operational ✅

**Test Steps:**
```python
# 1. Send query that should trigger memory storage
response = httpx.post("http://localhost:9004/run", json={
    "input_text": "Remember that I prefer tech stocks",
    "user_id": "integration_test_memory"
})

# 2. Verify memory interaction
parsed = json.loads(response.json()["json"])
assert "memory_status" in parsed or "memory_stored" in parsed

# 3. Verify Redis events
memory_events = redis_client.xread({"memory.semantic.store": '0'}, count=10)
assert len(memory_events) > 0
```

**Current Status:** 🔴 BLOCKED (service crashing, cannot test)

---

### Test 4: End-to-End Sacred Orders Flow ✅ CRITICAL

**Purpose:** Verify complete graph execution with ALL Sacred Orders active

**Test Steps:**
```python
# Full pipeline: entity resolution → scores → orthodoxy → vault → memory → compose
response = httpx.post("http://localhost:9004/run", json={
    "input_text": "Should I invest in Apple? Remember my preference for tech.",
    "user_id": "integration_test_full"
})

# Verify all Sacred Orders blessings present
parsed = json.loads(response.json()["json"])
assert "orthodoxy_verdict" in parsed
assert "vault_status" in parsed
assert "memory_status" in parsed or "memory_stored" in parsed

# Verify no emergency blessings (all real responses)
assert parsed["orthodoxy_verdict"] != "emergency_blessing"
assert parsed["vault_status"] != "emergency_blessing"
```

**Expected Duration:** < 30 seconds (multiple Sacred Orders)  
**Current Status:** ❌ BLOCKED (listeners + memory_orders down)

---

## Root Cause Analysis: Why Listeners Are Unhealthy

**Hypothesis 1: Import Path Errors**
- Listeners may have broken imports after refactoring
- Check: `docker logs core_orthodoxy_listener --tail=50`

**Hypothesis 2: Redis Connection Issues**
- Listeners can't connect to Redis Streams
- Check: REDIS_HOST env var, network connectivity

**Hypothesis 3: Missing Dependencies**
- Listener containers missing Python packages
- Check: requirements.txt in listener services

**Hypothesis 4: Service Discovery Failure**
- Listeners can't reach Sacred Orders HTTP endpoints
- Check: Service URLs (ORTHODOXY_URL, VAULT_URL, MEMORY_URL)

**Recommended Investigation:**
```bash
# Check orthodoxy_listener logs
docker logs core_orthodoxy_listener --tail=100

# Check vault_listener logs
docker logs core_vault_listener --tail=100

# Check memory_orders logs (crash loop)
docker logs core_memory_orders --tail=100

# Check Redis connectivity from listener
docker exec core_orthodoxy_listener nc -zv core_redis 6379

# Check Sacred Orders HTTP endpoints from listener
docker exec core_orthodoxy_listener curl -s http://core_orthodoxy_wardens:8007/health
```

---

## Recommendations (COO Priority)

### P0 — IMMEDIATE (Production Blockers)

1. **Fix Memory Orders Crash Loop** 🔴
   - Investigate: `docker logs core_memory_orders`
   - Likely: Import error, missing dependency, or config issue
   - Impact: Memory integration completely broken

2. **Fix Orthodoxy Listener** 🔴
   - Status: Unhealthy for 37 minutes
   - Investigate: Health check failure, Redis connection, import errors
   - Impact: No divine audit → security/governance gap

3. **Fix Vault Listener** 🔴
   - Status: Unhealthy for 37 minutes  
   - Impact: No vault protection → data integrity risk

### P1 — SHORT-TERM (Integration Validation)

4. **Write Integration Test Suite**
   - Create: `services/api_graph/examples/test_integration_sacred_orders.py`
   - Tests: orthodoxy, vault, memory round-trips
   - CI/CD: Add to GitHub Actions workflow

5. **Add Integration Test Documentation**
   - Update: `services/api_graph/examples/README.md`
   - Add: Prerequisites (Sacred Orders healthy)
   - Add: Expected Redis event traces

### P2 — LONG-TERM (Architecture Hardening)

6. **Add Observability for Sacred Orders Integration**
   - Prometheus metrics: `sacred_orders_requests_total`, `sacred_orders_response_time`
   - Grafana dashboard: Integration health panel
   - Alerting: Listener unhealthy → PagerDuty

7. **Implement Circuit Breaker for Sacred Orders**
   - Current: 10s timeout → emergency blessing
   - Better: Track failure rate, open circuit after 3 consecutive failures
   - Benefit: Faster degradation, less latency

8. **Add Integration Tests to CI/CD**
   - Spin up: Redis, Orthodoxy, Vault, Memory in Docker Compose
   - Run: Integration test suite
   - Fail build if: Any Sacred Orders integration broken

---

## Value Assessment: Surface Tests vs Integration Tests

### Surface Tests (Completed ✅)

**Value:**
- ✅ Confirms service deploys and starts
- ✅ Confirms HTTP layer works (FastAPI routing)
- ✅ Confirms adapter transformation correct (schema compliance)
- ✅ Detects schema mismatches (caught ResponseValidationError)
- ✅ Fast to run (< 30 seconds)
- ✅ No external dependencies (only HTTP endpoints)

**Limitations:**
- ❌ Doesn't test graph node execution
- ❌ Doesn't test Redis Streams communication
- ❌ Doesn't test Sacred Orders integration
- ❌ Doesn't detect listener failures (discovered manually)
- ❌ Gives false confidence (API works, but integration broken)

**Analogy:** Testing a car by checking if the doors open. Doors work ✅, but engine might be broken ❌.

---

### Integration Tests (Pending ❌)

**Value:**
- ✅ Confirms complete execution flow (graph → Redis → Sacred Orders → Redis → graph)
- ✅ Detects listener failures (test would timeout)
- ✅ Validates event correlation (correlation_id matching)
- ✅ Confirms Sacred Orders are reachable and responsive
- ✅ Tests production-critical path (not just HTTP surface)
- ✅ Detects crash loops (memory_orders restarting)

**Challenges:**
- ⚠️ Requires all Sacred Orders healthy (current blocker)
- ⚠️ Slower to run (15-30 seconds per test)
- ⚠️ Depends on Redis Streams (external dependency)
- ⚠️ More complex to debug (multiple services involved)

**Analogy:** Test-driving the car on the highway. Checks if engine, transmission, brakes ALL work together.

---

## Conclusion

**Surface Tests Value:** ✅ **MEDIUM** — Caught schema mismatch, validated HTTP layer  
**Integration Tests Value:** ✅ **CRITICAL** — Would have detected listener failures immediately

**Current Production Risk:** 🔴 **HIGH**
- Graph API responds 200 OK ✅
- But Sacred Orders integration is **BROKEN** ❌
- Orthodoxy audits: **emergency blessings only** (no validation)
- Vault protection: **emergency blessings only** (no archival)
- Memory storage: **completely disabled** (service crashing)

**Recommendation:** **DO NOT DEPLOY** until:
1. Memory Orders crash loop fixed
2. Orthodoxy/Vault listeners healthy
3. Integration tests pass (all 4 tests green)

**Estimated Fix Time:**
- Listener fixes: 1-2 hours (diagnosis + deploy)
- Integration tests: 2-3 hours (write + validate)
- Total: **4-6 hours to production-ready**

---

**COO Assessment:** Surface tests were **necessary but insufficient**. Integration tests are **mandatory** for production approval.

---

**Next Action:** Investigate listener logs and fix crash loops before proceeding with integration tests.
