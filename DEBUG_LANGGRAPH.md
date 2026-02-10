# LangGraph Debugging Branch

**Branch**: `debug/langgraph-integration`  
**Created**: Feb 10, 2026  
**Purpose**: Debug e risoluzione issue integrazione LangGraph con Sacred Orders

---

## Issue da Debuggare

### 1. CognitiveEvent.__init__() Error (P1)
**Symptom**: 
```
theological_metadata: {
  'fallback_reason': 'error_CognitiveEvent.__init__() got an unexpected keywor'
}
```

**Impact**: 
- Causa fallback a `local_blessing` invece di `approved` (remote audit)
- Prevents full Orthodoxy Wardens remote audit via Redis Streams
- Integration funziona ma con blessing locale invece che remoto

**Hypothesis**:
- CognitiveEvent constructor riceve keyword argument non previsto
- Probabilmente da orthodoxy_node.py o vault_node.py durante emit
- Verificare signature CognitiveEvent vs chiamate da nodi

**Files to Check**:
- `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py` (CognitiveEvent)
- `vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py` (emit logic)
- `vitruvyan_core/core/orchestration/langgraph/node/vault_node.py` (emit logic)

---

### 2. Risk Analysis Test Timeout (P2)
**Symptom**: 
- 2/3 integration tests passing (sentiment ✅, trend ✅)
- Risk analysis fails with "Missing Sacred Orders metadata"
- Manual curl shows metadata IS present

**Hypothesis**:
- Timeout during rapid test sequence
- Neural Engine processing time variabile per "risk" intent
- Non structural issue (manual execution confirms metadata present)

**Solution**: Aumentare timeout test o add retry logic

---

### 3. Listener Healthcheck False Positives (P2)
**Symptom**: 
```
orthodoxy_listener: unhealthy
vault_listener: unhealthy
```
- Ma logs mostrano Redis connectivity + execution normale

**Hypothesis**: DNS race condition durante startup healthcheck

**Files to Check**:
- `services/api_orthodoxy_wardens/monitoring/health.py`
- `services/api_vault_keepers/monitoring/health.py`
- Docker healthcheck definitions in compose.yaml

---

## Sacred Orders Integration Status (Post-Fix)

✅ **Completed (Feb 10, 2026)**:
- Memory Orders lazy-load openai (no più crash su imports)
- Quality check defensive type checks (2× AttributeError fixes)
- **Graph runner metadata propagation** (8 Sacred Orders fields)
- Integration test suite (test_integration_orthodoxy.py)
- Metadata validation: orthodoxy + vault in API response ✅

📊 **Container Health**: 6/6 Sacred Orders operational

🧪 **Integration Tests**: 2/3 passing (1 timeout edge case)

🎯 **API Response Validation**: 
```json
{
  "orthodoxy_verdict": "local_blessing",
  "orthodoxy_blessing": "...",
  "orthodoxy_confidence": 0.95,
  "orthodoxy_findings": [],
  "orthodoxy_message": "...",
  "orthodoxy_timestamp": "2026-02-10T16:20:13.481503",
  "theological_metadata": {...},
  "vault_blessing": {"vault_status": "blessed", ...}
}
```

---

## Debugging Strategy

### Phase 1: CognitiveEvent Error (Current Focus)
1. Read CognitiveEvent.__init__() signature
2. Grep all CognitiveEvent() instantiations in langgraph nodes
3. Identify unexpected keyword argument
4. Fix caller OR update CognitiveEvent constructor
5. Rebuild containers + test remote audit

### Phase 2: Test Reliability
1. Increase integration test timeouts
2. Add retry logic for transient failures
3. Consider parallelization impact on Neural Engine

### Phase 3: Healthcheck Tuning
1. Add DNS resolution delay in healthcheck
2. Consider healthcheck retry count increase
3. Document false positive pattern

---

## Branch Workflow

```bash
# Work in debug branch
git checkout debug/langgraph-integration

# Make fixes
git add -A
git commit -m "fix(langgraph): resolve CognitiveEvent constructor issue"

# Push to debug branch
git push origin debug/langgraph-integration

# When ready, merge to main
git checkout main
git merge debug/langgraph-integration
git push origin main
```

---

## Success Criteria

**Branch merge to main when**:
- ✅ CognitiveEvent error resolved
- ✅ Remote audit works (orthodoxy_verdict = "approved", not "local_blessing")
- ✅ 3/3 integration tests passing
- ✅ No fallback_reason in theological_metadata
- ✅ All containers healthy (no false positives)

---

## Reference Commits (main branch)

- `ca5aee8` — Sacred Orders metadata propagation fix (Feb 10, 2026)
- `5cf82c3` — Post-fix test results documentation
- `7fce74c` — Pre-fix diagnosis report

**Baseline**: Branch created from `ca5aee8` (main, Feb 10 2026)
