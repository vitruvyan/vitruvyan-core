# Sacred Orders Graph Nodes - Rewrite Plan

**Status**: ACTIVE REWRITE IN PROGRESS  
**Date**: February 11, 2026  
**Contract**: `.github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md`  

---

## Identified Sacred Orders Nodes

| # | Sacred Order | Current Node File | Lines | Status | Violations |
|---|--------------|-------------------|-------|--------|-----------|
| 1 | **Babel Gardens** | `babel_gardens_node.py` | 143 | ✅ **NEW** | 0 (contract-compliant) |
| 2 | **Pattern Weavers** | `pattern_weavers_node.py` | 142 | ⚠️ **NEW** | 1 (line 92-94: avg calculation) |
| 3 | **Memory Orders** | `mnemosyne_node.py` | 373 | ❌ **OLD** | Multiple (avg, similarity calc) |
| 4 | **Vault Keepers** | `archivarium_node.py` | 376 | ❌ **OLD** | Unknown (needs audit) |
| 5 | **Codex Hunters** | `codex_hunters_node.py` | 470 | ❌ **OLD** | Unknown (needs audit) |
| 6 | **Orthodoxy Wardens** | `orthodoxy_node.py` | Unknown | ❌ **OLD** | Unknown (needs audit) |

---

## Rewrite Strategy

### Template Pattern (60 lines max)

```python
"""Sacred Order Node - [Order Name]"""

import logging
from typing import Any, Dict
import httpx
from config.api_config import get_[order]_url

logger = logging.getLogger(__name__)

def [order]_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thin adapter for [Sacred Order Name].
    
    Calls: [Sacred Order Service] API
    Contract: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md
    """
    try:
        # 1. Extract input from state (no validation - service handles it)
        request_payload = {
            "input": state.get("input_text", ""),
            "context": state.get("context", {}),
        }
        
        # 2. HTTP call to Sacred Order service
        response = httpx.post(
            f"{get_[order]_url()}/v1/[endpoint]",
            json=request_payload,
            timeout=5.0,
        )
        
        # 3. Store opaque result + convenience fields
        if response.status_code == 200:
            result = response.json()
            state["[order]_result"] = result  # Opaque
            state["[order]_data"] = result.get("data", {})  # Convenience
        else:
            state["[order]_result"] = {"error": response.status_code}
            
    except httpx.HTTPError as e:
        logger.error(f"[Order] error: {e}")
        state["[order]_result"] = {"error": "network_failure"}
    
    return state
```

**Key characteristics**:
- ✅ < 60 lines
- ✅ Zero domain logic
- ✅ Zero calculations
- ✅ Opaque result storage
- ✅ Simple HTTP adapter

---

## Rewrite Sequence

### Phase 1: Fix Immediate Violations (Today)

**Task 1.1: Pattern Weavers Node** (15 min)
- **File**: `pattern_weavers_node.py`
- **Issue**: Lines 92-94 calculate avg confidence
- **Fix**: Remove calculation, extract from service response
- **Service change required**: Pattern Weavers API must return `avg_confidence`

**Status**: Service already compliant (routes.py returns metrics)  
**Action**: Just remove lines 92-94, extract `result["metrics"]["avg_confidence"]`

---

### Phase 2: Rewrite Memory/Vault Nodes (Week 1)

**Task 2.1: Memory Orders Node** (60 min)
- **File**: `mnemosyne_node.py` (373 lines → 60 lines)
- **Current**: Event-driven (Redis Cognitive Bus), processes VSGS results
- **New**: HTTP call to Memory Orders service `/v1/semantic_search`
- **Service endpoint**: Memory Orders API (port 8013)
- **Violations**: Calculates avg similarity, min/max scores

**Service changes required**:
```python
# services/api_memory_orders/api/routes.py
@router.post("/v1/semantic_search")
def semantic_search(request: SearchRequest):
    matches = search_qdrant(...)
    
    # Pre-calculate metrics
    scores = [m.score for m in matches]
    return {
        "matches": matches,
        "metrics": {
            "avg_similarity": sum(scores) / len(scores),
            "max_similarity": max(scores),
            "min_similarity": min(scores),
        }
    }
```

**Task 2.2: Vault Keepers Node** (60 min)
- **File**: `archivarium_node.py` (376 lines → 60 lines)
- **Current**: Event-driven (Redis), processes PostgreSQL results
- **New**: HTTP call to Vault Keepers service `/v1/archive/query`
- **Service endpoint**: Vault Keepers API (port 8014)
- **Audit needed**: Unknown violations

---

### Phase 3: Rewrite Codex/Orthodoxy Nodes (Week 2)

**Task 3.1: Codex Hunters Node** (90 min)
- **File**: `codex_hunters_node.py` (470 lines → 60 lines)
- **Current**: Complex expedition management, polling, retries
- **New**: HTTP call to Codex Hunters service `/v1/expeditions`
- **Service endpoint**: Codex Hunters API (port 8008)
- **Challenge**: Async expedition tracking (move to service)

**Task 3.2: Orthodoxy Wardens Node** (90 min)
- **File**: `orthodoxy_node.py` (size unknown → 60 lines)
- **Current**: Unknown structure
- **New**: HTTP call to Orthodoxy Wardens service `/v1/audit`
- **Service endpoint**: Orthodoxy Wardens API (port 8012)

---

## Service API Requirements

All Sacred Order services MUST implement this response schema:

```json
{
  "status": "completed",
  "data": { /* domain payload */ },
  "metrics": {
    "avg_confidence": 0.85,
    "quality": "high",
    "processing_time_ms": 42
  },
  "metadata": {
    "model_version": "v2.1",
    "cached": false
  }
}
```

**Services to update**:
1. ✅ Pattern Weavers (already compliant)
2. ⏳ Memory Orders (needs metrics in response)
3. ⏳ Vault Keepers (needs metrics)
4. ⏳ Codex Hunters (needs standardization)
5. ⏳ Orthodoxy Wardens (needs standardization)

---

## Verification Checklist (Per Node)

After rewriting each node, verify:

```bash
# 1. Contract compliance
pytest tests/architectural/test_orchestration_contract.py::[node_name]

# 2. Line count
wc -l [node_file].py  # Target: < 60

# 3. Violations audit
.github/scripts/enforce_orchestration_contract.sh

# 4. Import test
python3 -c "from vitruvyan_core.core.orchestration.langgraph.node.[node] import [node]_node"

# 5. Runtime test
# Run graph with node enabled, verify HTTP calls work
```

---

## Timeline

| Phase | Duration | Effort | Completion |
|-------|----------|--------|-----------|
| **Phase 1** (Pattern Weavers fix) | 15 min | 1 developer | Today |
| **Phase 2** (Memory + Vault) | 2-3 hours | 1 developer | Week 1 |
| **Phase 3** (Codex + Orthodoxy) | 3-4 hours | 1 developer | Week 2 |
| **Total** | ~6 hours | 1 developer | 7 days |

---

## Archive Strategy

**OLD nodes** → `_legacy/[node_name]_v1.py`

Example:
```bash
mv mnemosyne_node.py _legacy/mnemosyne_node_v1_event_driven.py
# Create new mnemosyne_node.py (60 lines, contract-compliant)
```

**Reason**: Preserve historical implementation for reference, clean workspace.

---

## Success Criteria

1. ✅ All Sacred Orders nodes < 60 lines
2. ✅ Zero contract violations (enforcement passing)
3. ✅ All nodes use HTTP adapter pattern
4. ✅ All nodes store opaque results
5. ✅ Services return pre-calculated metrics
6. ✅ Graph execution functional end-to-end

---

## Next Actions

1. **Immediate**: Fix `pattern_weavers_node.py` lines 92-94
2. **Next**: Audit `mnemosyne_node.py` and `archivarium_node.py` violations
3. **Then**: Rewrite Memory Orders node (template for others)
4. **Finally**: Apply template to remaining nodes

---

**Status**: Ready to execute. Awaiting approval to start Phase 1.
