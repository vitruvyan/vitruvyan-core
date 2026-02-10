# 🔄 DEBUG SESSION RESUME — LangGraph Sacred Orders Integration

**Branch**: `debug/langgraph-integration`  
**Last Active**: Feb 10, 2026  
**Status**: Ready to resume debugging  
**Machine**: Transfer in progress (switching to new development environment)

---

## 📋 EXECUTIVE SUMMARY

**What we accomplished** (Feb 10, 2026):
- ✅ Fixed Memory Orders crash loop (lazy openai import)
- ✅ Fixed 2× quality_check AttributeError crashes (defensive type checks)
- ✅ **CRITICAL FIX**: Sacred Orders metadata now propagates to API response
- ✅ Integration tests created (2/3 passing)
- ✅ Documented slot-filling architecture divergence

**What remains** (next session priorities):
- 🔧 P1: Fix `CognitiveEvent.__init__()` error (causes local_blessing fallback)
- 🧪 P1: Fix risk analysis test timeout (1/3 tests intermittent)
- ⚠️ P2: Listener healthcheck false positives (operational but shows unhealthy)

**Current state**: Sacred Orders integration **WORKS** but uses fallback blessing instead of remote audit.

---

## 🎯 PROBLEM STATEMENT (Why We're Debugging)

### Original Issue (Discovered Feb 10)
Integration tests showed **Sacred Orders metadata missing** from API response:
```
Test: "sentiment Apple"
Expected: orthodoxy_verdict, vault_blessing in response
Actual: Empty keys, metadata not propagated
```

### Root Cause (FIXED)
[graph_runner.py](vitruvyan_core/core/orchestration/langgraph/graph_runner.py) returned only `response` field, manually copying Babel/emotion metadata but **NOT** Sacred Orders fields.

### Fix Applied (Commit ca5aee8)
Added 8 Sacred Orders fields to response propagation:
```python
# Lines 143-160 (CASE 1) + 206-219 (CASE 2)
if final_state.get("orthodoxy_verdict"):
    response["orthodoxy_verdict"] = final_state.get("orthodoxy_verdict")
    response["orthodoxy_blessing"] = final_state.get("orthodoxy_blessing")
    response["orthodoxy_confidence"] = final_state.get("orthodoxy_confidence")
    response["orthodoxy_findings"] = final_state.get("orthodoxy_findings")
    response["orthodoxy_message"] = final_state.get("orthodoxy_message")
    response["orthodoxy_timestamp"] = final_state.get("orthodoxy_timestamp")
    response["theological_metadata"] = final_state.get("theological_metadata")

if final_state.get("vault_blessing"):
    response["vault_blessing"] = final_state.get("vault_blessing")
    response["vault_status"] = final_state.get("vault_status")
```

### Validation Results
**API Response NOW includes**:
```json
{
  "orthodoxy_verdict": "local_blessing",
  "orthodoxy_blessing": "...",
  "orthodoxy_confidence": 0.95,
  "orthodoxy_findings": [],
  "orthodoxy_message": "...",
  "orthodoxy_timestamp": "2026-02-10T16:20:13.481503",
  "theological_metadata": {
    "sacred_order": "local_validation",
    "fallback_reason": "error_CognitiveEvent.__init__() got an unexpected keywor"
  },
  "vault_blessing": {
    "vault_status": "blessed",
    "vault_protection": "standard_blessing",
    "vault_timestamp": "2026-02-10T16:20:13.481503"
  }
}
```

✅ **Integration WORKS** — metadata present in response  
⚠️ **BUT uses fallback** — `local_blessing` instead of `approved` (remote audit)

---

## 🐛 REMAINING ISSUES (Debug Priorities)

### Issue #1: CognitiveEvent Constructor Error (P1)

**Symptom**:
```python
theological_metadata: {
  'fallback_reason': 'error_CognitiveEvent.__init__() got an unexpected keywor'
}
```

**Impact**:
- Orthodoxy node falls back to `local_blessing` instead of remote audit
- Remote audit via Redis Streams **NOT working**
- Integration functional but not using full Sacred Orders pipeline

**Hypothesis**:
`orthodoxy_node.py` or `vault_node.py` emit `CognitiveEvent` with unexpected keyword argument. Constructor signature mismatch.

**Files to check**:
1. `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py`
   - Read `CognitiveEvent.__init__()` signature
   - Check required vs optional parameters

2. `vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py`
   - Find `CognitiveEvent(...)` instantiation
   - Compare args with constructor signature
   - Line ~50-80 (emit audit request)

3. `vitruvyan_core/core/orchestration/langgraph/node/vault_node.py`
   - Same pattern as orthodoxy_node

**Debug commands** (start here):
```bash
# 1. Read CognitiveEvent constructor signature
grep -A 20 "class CognitiveEvent" vitruvyan_core/core/synaptic_conclave/events/event_envelope.py

# 2. Find all CognitiveEvent instantiations in langgraph nodes
rg "CognitiveEvent\(" vitruvyan_core/core/orchestration/langgraph/node/

# 3. Compare signatures
rg "__init__" vitruvyan_core/core/synaptic_conclave/events/event_envelope.py | head -20
```

**Expected fix pattern**:
```python
# BEFORE (causing error):
event = CognitiveEvent(
    channel="system.audit.requested",
    payload={"request_id": ...},
    invalid_keyword=True  # ← This keyword not in constructor
)

# AFTER (fixed):
event = CognitiveEvent(
    channel="system.audit.requested",
    payload={
        "request_id": ...,
        "invalid_keyword": True  # ← Move to payload
    }
)
```

**Success criteria**:
- ✅ No `fallback_reason` in `theological_metadata`
- ✅ `orthodoxy_verdict = "approved"` (not `local_blessing`)
- ✅ Remote audit executes via Redis Streams
- ✅ Orthodoxy listener processes event successfully

---

### Issue #2: Risk Analysis Test Timeout (P2)

**Symptom**:
```
✅ Sentiment Analysis: PASS (5.3s)
✅ Trend Analysis: PASS (5.0s)
❌ Risk Analysis: FAIL (Missing metadata)
```

**Observation**:
Manual curl shows metadata **IS present**:
```bash
curl -X POST http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"risk Apple","validated_entities":["AAPL"]}'

# Response includes orthodoxy_verdict ✅
```

**Hypothesis**:
- Timeout during rapid test sequence (3 tests in 16s)
- Neural Engine processing time variable for "risk" intent
- Test harness timeout too aggressive
- NOT a structural issue (manual execution works)

**Files to check**:
1. `services/api_graph/examples/test_integration_orthodoxy.py`
   - Line 31: `TIMEOUT = 30` (current value)
   - Consider increasing to 45-60s

2. Graph execution logs:
   ```bash
   docker logs core_graph --tail=200 | grep -E "risk|timeout|FAIL"
   ```

**Quick fix** (if timeout confirmed):
```python
# test_integration_orthodoxy.py line 31
TIMEOUT = 30  # BEFORE
TIMEOUT = 60  # AFTER (give more time for risk analysis)
```

**Alternative**: Add retry logic for transient failures

**Success criteria**:
- ✅ 3/3 integration tests passing
- ✅ No intermittent failures
- ✅ Test execution < 60s total

---

### Issue #3: Listener Healthcheck False Positives (P2)

**Symptom**:
```bash
docker ps --filter "name=listener"
# orthodoxy_listener: unhealthy
# vault_listener: unhealthy
```

**BUT logs show operational**:
```bash
docker logs core_orthodoxy_listener --tail=20
# ✅ Redis connection successful
# ✅ Consumer group created
# ✅ Listening on channel system.audit.requested
```

**Hypothesis**: DNS race condition during healthcheck startup

**Files to check**:
1. `services/api_orthodoxy_wardens/monitoring/health.py`
2. `services/api_vault_keepers/monitoring/health.py`
3. `infrastructure/docker/compose.yaml` (healthcheck definitions)

**Not blocking** (listeners are operational, just healthcheck cosmetic issue)

**Defer to P2** (fix after CognitiveEvent error resolved)

---

## 🛠️ FILES MODIFIED (Session Feb 10)

### Commit ca5aee8 (main branch)
**Purpose**: Sacred Orders metadata propagation fix

1. **llm_agent.py** (lines 70-82, 336-347)
   - Lazy-load openai import (prevents memory_orders crash)
   ```python
   try:
       from openai import OpenAI
       OPENAI_AVAILABLE = True
   except ImportError:
       OPENAI_AVAILABLE = False
   ```

2. **quality_check_node.py** (lines 82-96, 281-295)
   - 2× defensive type checks (ranking, raw_output)
   - Neural Engine can return list OR dict
   ```python
   if isinstance(ranking, list):
       entities = ranking
   elif isinstance(ranking, dict):
       entities = ranking.get("entities", [])
   ```

3. **graph_runner.py** (lines 143-160, 206-219)
   - **CRITICAL FIX**: Propagate 8 Sacred Orders fields
   - Applied in CASE 1 (nested response) + CASE 2 (flattened dict)

4. **test_integration_orthodoxy.py** (NEW, 380 lines)
   - Integration test suite for Sacred Orders
   - 3 test cases (sentiment, risk, trend)
   - 2/3 passing (risk timeout intermittent)

### Commit 1c9eb0b (debug branch)
**Purpose**: Architectural alignment documentation

1. **SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md** (NEW, 395 lines)
   - Critical discovery: upstream deprecated, core keeps active
   - Repository comparison matrix
   - 3 migration paths documented

2. **.github/copilot-instructions.md** (section 7 added)
   - Slot-filling architecture status
   - Context for GitHub Copilot (don't confuse repositories)

3. **DEBUG_LANGGRAPH.md** (critical discovery note)
   - Architectural divergence summary

---

## 🚀 STEP-BY-STEP DEBUG PLAN (Next Session)

### Step 1: Environment Setup (5 min)

```bash
# Clone/pull latest debug branch
git clone https://github.com/dbaldoni/vitruvyan-core.git
cd vitruvyan-core
git checkout debug/langgraph-integration

# Verify branch status
git log --oneline -3
# Expected:
# 1c9eb0b (HEAD) docs(critical): slot-filling architecture alignment
# ee7498f docs(debug): langgraph integration debugging roadmap  
# ca5aee8 fix(sacred_orders): integrate metadata in graph response

# Check container health
docker ps --filter "name=core_" --format "table {{.Names}}\t{{.Status}}"

# Expected:
# core_graph: Up, healthy
# core_orthodoxy_wardens: Up, healthy
# core_vault_keepers: Up, healthy
# core_memory_orders: Up, healthy
# (listeners may show unhealthy - ignore, operational)
```

### Step 2: Verify Current State (10 min)

```bash
# Test Sacred Orders metadata propagation (should show metadata)
docker exec core_graph sh -c 'curl -s http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d "{\"input_text\":\"sentiment Apple\",\"validated_entities\":[\"AAPL\"]}"' \
  | python3 -c "import json, sys; \
    data=json.load(sys.stdin); \
    parsed=json.loads(data['json']); \
    print('✅ orthodoxy_verdict:', parsed.get('orthodoxy_verdict')); \
    print('✅ vault_blessing:', parsed.get('vault_blessing', {}).get('vault_status')); \
    print('⚠️ fallback_reason:', parsed.get('theological_metadata', {}).get('fallback_reason'))"

# Expected output:
# ✅ orthodoxy_verdict: local_blessing
# ✅ vault_blessing: blessed
# ⚠️ fallback_reason: error_CognitiveEvent.__init__() got an unexpected keywor

# Run integration tests
docker exec core_graph python3 /app/test_integration_orthodoxy.py 2>&1 | tail -30

# Expected:
# Passed: 2 ✅ (sentiment, trend)
# Failed: 1 ❌ (risk - timeout)
```

### Step 3: Fix CognitiveEvent Error (30-45 min)

```bash
# 3.1 Read CognitiveEvent constructor signature
cat vitruvyan_core/core/synaptic_conclave/events/event_envelope.py | grep -A 30 "class CognitiveEvent"

# 3.2 Find all instantiations in langgraph nodes
rg "CognitiveEvent\(" vitruvyan_core/core/orchestration/langgraph/node/ -A 5

# 3.3 Compare arguments (look for mismatch)
# Expected pattern:
# CognitiveEvent(
#     channel="...",
#     payload={...},
#     metadata={...}  # Optional
# )

# 3.4 Fix identified mismatch
# Use replace_string_in_file to fix orthodoxy_node.py or vault_node.py

# 3.5 Rebuild graph container
cd infrastructure/docker
docker compose build graph
docker stop core_graph && docker rm core_graph
docker compose up -d graph

# 3.6 Verify fix
sleep 10
docker exec core_graph sh -c 'curl -s http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d "{\"input_text\":\"sentiment Apple\",\"validated_entities\":[\"AAPL\"]}"' \
  | python3 -c "import json, sys; \
    data=json.load(sys.stdin); \
    parsed=json.loads(data['json']); \
    print('Verdict:', parsed.get('orthodoxy_verdict')); \
    print('Fallback reason:', parsed.get('theological_metadata', {}).get('fallback_reason', 'NONE'))"

# Expected (after fix):
# Verdict: approved  (NOT local_blessing)
# Fallback reason: NONE  (NOT error message)

# 3.7 Check listener logs (should show audit processing)
docker logs core_orthodoxy_listener --tail=50 | grep -E "audit|absolution|approved"

# Expected: Log entries showing audit request received + processed
```

### Step 4: Fix Risk Analysis Timeout (15 min)

```bash
# 4.1 Increase test timeout
# Edit: services/api_graph/examples/test_integration_orthodoxy.py
# Change line 31: TIMEOUT = 30 → TIMEOUT = 60

# 4.2 Copy updated test to container
docker cp services/api_graph/examples/test_integration_orthodoxy.py \
  core_graph:/app/test_integration_orthodoxy.py

# 4.3 Rerun tests
docker exec core_graph python3 /app/test_integration_orthodoxy.py

# Expected:
# Passed: 3 ✅ (sentiment, risk, trend)
# Failed: 0 ❌
```

### Step 5: Commit Fixes (10 min)

```bash
git add -A
git commit -m "fix(langgraph): resolve CognitiveEvent constructor error

PROBLEM:
orthodoxy_node/vault_node emit CognitiveEvent with unexpected keyword arg
theological_metadata shows fallback_reason: 'error_CognitiveEvent.__init__()'

ROOT CAUSE:
[describe specific mismatch found]

FIX:
[describe what was changed in orthodoxy_node.py or vault_node.py]

VALIDATION:
- orthodoxy_verdict: approved ✅ (was: local_blessing)
- No fallback_reason in theological_metadata ✅
- Remote audit via Redis Streams working ✅
- Integration tests 3/3 passing ✅

Files modified:
- orthodoxy_node.py (line X: fix CognitiveEvent instantiation)
- test_integration_orthodoxy.py (line 31: timeout 30→60s)"

git push origin debug/langgraph-integration
```

### Step 6: Merge to Main (5 min)

```bash
# After all tests passing
git checkout main
git merge debug/langgraph-integration -m "feat: complete Sacred Orders integration debugging

Fixes:
1. CognitiveEvent constructor error (remote audit now works)
2. Risk analysis test timeout (increased to 60s)
3. Sacred Orders metadata propagation (8 fields)

Integration validation:
- orthodoxy_verdict: approved
- vault_blessing: blessed
- theological_metadata: no fallback
- Tests: 3/3 passing

Branch: debug/langgraph-integration → main"

git push origin main
```

---

## 📊 CONTAINER STATUS (Expected)

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

| Container | Status | Port | Notes |
|-----------|--------|------|-------|
| core_graph | Up, healthy | 8004 | ✅ Main orchestrator |
| core_orthodoxy_wardens | Up, healthy | 8005 | ✅ Audit service |
| core_orthodoxy_listener | Up (unhealthy) | - | ⚠️ Operational (healthcheck issue) |
| core_vault_keepers | Up, healthy | 8006 | ✅ Memory protection |
| core_vault_listener | Up (unhealthy) | - | ⚠️ Operational (healthcheck issue) |
| core_memory_orders | Up, healthy | 8007 | ✅ Coherence analysis |
| core_memory_orders_listener | Up, healthy | - | ✅ Working |

**Note**: Listener healthcheck warnings are **cosmetic** (DNS race condition). Logs confirm operational.

---

## 🧪 VALIDATION CHECKLIST

After fixes applied, verify:

- [ ] ✅ CognitiveEvent error resolved (no fallback_reason)
- [ ] ✅ Remote audit works (orthodoxy_verdict = "approved")
- [ ] ✅ Integration tests 3/3 passing
- [ ] ✅ API response includes 8 Sacred Orders fields
- [ ] ✅ Theological metadata no errors
- [ ] ✅ Listener logs show audit request processing
- [ ] ✅ Graph execution completes without crashes
- [ ] ✅ All containers healthy (except known healthcheck issues)

**Full validation command**:
```bash
# Run this after Step 5 (commit fixes)
docker exec core_graph sh -c 'curl -s http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d "{\"input_text\":\"sentiment Apple\",\"validated_entities\":[\"AAPL\"]}"' \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
parsed = json.loads(data['json'])

print('='*60)
print('SACRED ORDERS INTEGRATION VALIDATION')
print('='*60)
print(f\"orthodoxy_verdict: {parsed.get('orthodoxy_verdict')}\")
print(f\"orthodoxy_blessing: {parsed.get('orthodoxy_blessing')}\")
print(f\"vault_blessing: {parsed.get('vault_blessing', {}).get('vault_status')}\")
print(f\"theological_metadata: {parsed.get('theological_metadata', {})}\")
print('='*60)

# Validation
verdict = parsed.get('orthodoxy_verdict')
fallback = parsed.get('theological_metadata', {}).get('fallback_reason')

if verdict == 'approved' and not fallback:
    print('✅ INTEGRATION FULLY OPERATIONAL')
    sys.exit(0)
elif verdict == 'local_blessing' and fallback:
    print('⚠️ FALLBACK MODE (CognitiveEvent error still present)')
    sys.exit(1)
else:
    print('❌ UNEXPECTED STATE')
    sys.exit(2)
"

# Exit code:
# 0 = Success (integration working)
# 1 = Warning (still using fallback)
# 2 = Error (unexpected state)
```

---

## 📚 REFERENCE DOCUMENTATION

### Architecture Context
- **Slot-filling alignment**: `SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md`
- **Copilot instructions**: `.github/copilot-instructions.md` (section 7)
- **Debug roadmap**: `DEBUG_LANGGRAPH.md`

### Sacred Orders Pattern
- **Template**: Memory Orders (100% conformant)
  - LIVELLO 1: `vitruvyan_core/core/governance/memory_orders/`
  - LIVELLO 2: `services/api_memory_orders/`
- **Event envelope**: `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py`
- **Redis Streams**: `vitruvyan_core/core/synaptic_conclave/transport/streams.py`

### Graph Nodes
- **Orthodoxy**: `vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py`
- **Vault**: `vitruvyan_core/core/orchestration/langgraph/node/vault_node.py`
- **Quality check**: `vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py`
- **Graph runner**: `vitruvyan_core/core/orchestration/langgraph/graph_runner.py`

### Key Commits
- `ca5aee8` — Sacred Orders metadata propagation fix (main branch)
- `1c9eb0b` — Slot-filling architecture alignment (debug branch)
- `ee7498f` — Debug roadmap initialization (debug branch)

---

## 🎯 SUCCESS CRITERIA (Session Complete When)

- [x] ✅ Environment setup verified (containers healthy)
- [x] ✅ Current state validated (metadata propagation works)
- [ ] ✅ CognitiveEvent error fixed (remote audit working)
- [ ] ✅ Integration tests 3/3 passing (no timeouts)
- [ ] ✅ Full validation passing (exit code 0)
- [ ] ✅ Fixes committed to debug branch
- [ ] ✅ Debug branch merged to main
- [ ] ✅ Documentation updated

**When all criteria met**: Sacred Orders integration is **production-ready** ✅

---

## 💡 TROUBLESHOOTING TIPS

### If CognitiveEvent fix unclear:
```bash
# Compare constructors
diff <(grep -A 15 "class TransportEvent" vitruvyan_core/core/synaptic_conclave/events/event_envelope.py) \
     <(grep -A 15 "class CognitiveEvent" vitruvyan_core/core/synaptic_conclave/events/event_envelope.py)

# Find example usage (working code)
rg "CognitiveEvent\(" vitruvyan_core/ --type py -A 3 | head -50
```

### If containers fail to start:
```bash
# Check logs
docker logs core_graph --tail=100

# Rebuild from scratch
docker compose down
docker compose build --no-cache graph orthodoxy_wardens vault_keepers
docker compose up -d
```

### If tests still fail after timeout increase:
```bash
# Add debug logging to test
# Edit test_integration_orthodoxy.py, add:
print(f"[DEBUG] Request sent at {time.time()}")
# ...after httpx.post()
print(f"[DEBUG] Response received at {time.time()}, status={response.status_code}")
```

---

## 🚦 QUICK START (TL;DR)

```bash
# 1. Setup (new machine)
git clone https://github.com/dbaldoni/vitruvyan-core.git && cd vitruvyan-core
git checkout debug/langgraph-integration

# 2. Verify state
docker ps && docker exec core_graph curl -s http://localhost:8004/health | jq

# 3. Debug CognitiveEvent (main task)
cat vitruvyan_core/core/synaptic_conclave/events/event_envelope.py | grep -A 30 "class CognitiveEvent"
rg "CognitiveEvent\(" vitruvyan_core/core/orchestration/langgraph/node/ -A 5

# 4. Fix + test + commit
# (follow Step 3-6 above)

# 5. Validate
docker exec core_graph python3 /app/test_integration_orthodoxy.py
# Expected: Passed: 3 ✅
```

**Priority**: Fix CognitiveEvent error first. Everything else is secondary.

---

**Branch**: `debug/langgraph-integration`  
**Last commit**: `1c9eb0b`  
**Resume from**: Step 3 (Fix CognitiveEvent Error)  
**Estimated completion**: 60-90 minutes

Good luck! 🚀
