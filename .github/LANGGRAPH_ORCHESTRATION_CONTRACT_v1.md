# LangGraph Orchestration Contract v1.0

**Status**: BINDING CONSTITUTIONAL DOCUMENT  
**Effective Date**: February 11, 2026  
**Authors**: Vitruvyan Core Team  
**Enforcement**: Mandatory (CI/CD blocking)

---

## 1. Architectural Philosophy

### Core Principle

Vitruvyan is an **epistemic operating system**, not a monolithic application. LangGraph serves as **pure orchestration infrastructure**—a data railway network routing information between specialized cognitive services.

**Metaphor**: LangGraph is the rail system. Sacred Orders are train operators. Rails decide routing; operators decide cargo handling.

### Separation of Concerns

| Layer | Responsibility | Analogy |
|-------|----------------|---------|
| **LangGraph** | Route, switch, fallback, interrupt | Railway tracks + signals |
| **Sacred Orders** | Process, calculate, interpret, decide | Cargo operators + quality control |

**Critical Distinction**: 
- **Strategy** (which path to take) = Orchestration
- **Semantics** (what the data means) = Domain

---

## 2. Hard Boundary Definition

### Transport Layer Architecture

Vitruvyan uses **heterogeneous transport** for orchestration:

| Pattern | Transport | Status | Use Case |
|---------|-----------|--------|----------|
| **Synchronous** | HTTP | Canonical | Request/response domain operations |
| **Asynchronous** | Redis Streams | Canonical | Event-driven cognitive processing |
| **Pub/Sub** | DEPRECATED | Legacy | ❌ Fire-and-forget ephemeral (removed) |

**Critical Distinction**: 
- **Redis Streams** = Persistent, ordered, replayable event log with consumer groups (XADD, XREADGROUP, acknowledgment)
- **Pub/Sub** = Ephemeral fire-and-forget broadcast (deprecated in Vitruvyan)

The Cognitive Bus is **Redis Streams only**. Events are durable state transitions, not notifications.

### Decision Tree: "Who Owns This?"

```
Is it a calculation on domain data?
├─ YES → Sacred Order
└─ NO → Is it routing/fallback logic?
    ├─ YES → LangGraph
    └─ NO → Is it HTTP transport?
        ├─ YES → LangGraph
        └─ NO → Is it event processing (Redis Streams)?
            ├─ YES → LangGraph (Event Processor Node)
            └─ NO → ⚠️ Undefined (escalate to architecture review)
```

### Litmus Test

**Question**: "Could this code work with ANY domain (finance, medical, legal, IoT)?"

- **YES** → Belongs in LangGraph (generic orchestration)
- **NO** → Belongs in Sacred Order (domain-specific)

**Examples**:
```python
# ✅ Domain-agnostic (LangGraph):
if response.status_code != 200:
    return route_to("fallback_node")

# ❌ Domain-specific (Sacred Order):
if confidence < 0.7:  # What is "confidence"? Finance? Medical?
    return route_to("low_quality_handler")
```

---

## 3. Allowed vs Forbidden Responsibilities

### 3.1 Node Category Definitions

LangGraph recognizes **three node categories** based on transport layer:

#### Category 1: HTTP Domain Adapters

**Purpose**: Synchronous request/response to Sacred Order services.

**Pattern**:
```python
def example_node(state: Dict[str, Any]) -> Dict[str, Any]:
    response = httpx.post(SERVICE_URL, json={"query": state["input"]})
    
    if response.status_code == 200:
        result = response.json()
        state["service_result"] = result  # Opaque storage
        state["metric"] = result["metrics"]["avg_confidence"]  # Extract
    
    return state
```

**Examples**: `babel_gardens_node.py`, `pattern_weavers_node.py`, `codex_hunters_node.py`

---

#### Category 2: Event Processor Nodes

**Purpose**: Consume Redis Streams events (persistent event log, not Pub/Sub).

**Pattern**:
```python
def mnemosyne_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process semantic search results from Cognitive Bus."""
    
    # Event already consumed by streams_listener (XREADGROUP)
    event = state.get("event")  # TransportEvent from Redis Streams
    
    if event:
        payload = event.get("payload", {})
        
        # Extract pre-calculated metrics from event producer
        state["search_results"] = payload.get("matches", [])
        state["avg_similarity"] = payload["metrics"]["avg_similarity"]  # ✅ Pre-computed
        state["match_count"] = payload["metrics"]["match_count"]
    
    return state
```

**Key Characteristics**:
- Consumes from **Redis Streams** (persistent, ordered, replayable)
- Uses **consumer groups** for parallelism
- **Extracts** metrics from event payload (no calculation)
- Event producer (Sacred Order) **pre-calculates** all metrics

**Examples**: `mnemosyne_node.py` (semantic search results), `archivarium_node.py` (archival events)

**Not Pub/Sub**: Events are durable, acknowledged, replayable—not fire-and-forget.

---

#### Category 3: Infrastructure Adapters (Deprecated)

**Purpose**: Direct database/cache access (legacy, being phased out).

**Deprecation**: All infrastructure operations should flow through Sacred Order services.

---

### 3.2 Unified Prohibition (All Categories)

**The Hard Rule**: Regardless of transport layer, **no domain calculation** in orchestration.

| Forbidden | HTTP Nodes | Event Nodes | Reason |
|-----------|------------|-------------|--------|
| `sum()`, `avg()` | ❌ | ❌ | Calculation = domain semantics |
| `score > threshold` | ❌ | ❌ | Interpretation = business logic |
| `sorted(key=lambda...)` | ❌ | ❌ | Prioritization = domain knowledge |

**Calculation Location**:
- **HTTP Nodes**: Pre-calculated in service response
- **Event Nodes**: Pre-calculated in event producer payload

---

### 3.3 Orchestration Layer (LangGraph Nodes)

#### ✅ ALLOWED

| Category | Examples |
|----------|----------|
| **HTTP Transport** | `httpx.post()`, `response.status_code`, `response.json()` |
| **Routing Logic** | `if error: route_to("fallback")`, short-circuiting, path selection |
| **State Management** | `state["field"] = value`, extracting fields from state |
| **Neutral Fallbacks** | `state["results"] = []`, `state["score"] = 0.0` (empty defaults) |
| **Network Resilience** | Timeout handling, retry HTTP (not business retry) |
| **Observability** | Logging, tracing, request IDs |

#### ❌ FORBIDDEN

| Category | Examples | Why Forbidden |
|----------|----------|---------------|
| **Domain Arithmetic** | `sum()`, `avg()`, `min()`, `max()` | Calculation = semantics |
| **Threshold Logic** | `if score > 0.7`, `if confidence < threshold` | Interpretation = domain knowledge |
| **Ranking/Sorting** | `sorted(results, key=lambda x: x.score)` | Prioritization = business logic |
| **Semantic Filtering** | `[r for r in results if r.quality == "high"]` | Quality assessment = domain |
| **Metric Derivation** | `processing_time = end - start` | Should come from service telemetry |
| **Data Transformation** | List comprehensions that extract/transform domain objects | Service should return ready-to-use format |

---

### 3.4 Domain Layer (Sacred Orders)

#### ✅ REQUIRED

| Responsibility | Examples |
|----------------|----------|
| **All Calculations** | Confidence scores, averages, aggregations |
| **Threshold Application** | `is_acceptable = score >= threshold` |
| **Quality Assessment** | `quality = "high" if confidence > 0.7 else "low"` |
| **Ranking Logic** | Sort results by relevance, importance, etc. |
| **Semantic Filtering** | Remove low-quality results before returning |
| **Domain Error Codes** | Return `INSUFFICIENT_CONFIDENCE`, not just HTTP 500 |

#### ❌ FORBIDDEN

| Restriction | Reason |
|-------------|--------|
| **LangGraph State Schema Knowledge** | Service can't depend on GraphState structure |
| **Cross-Service Orchestration** | Routing between services = LangGraph's job |
| **Pipeline Control Flow** | Service doesn't decide "next node in graph" |

---

## 4. Concrete Examples

### 4.1 Violation: Domain Arithmetic in Orchestration

#### ❌ WRONG (Current Implementation)

```python
# pattern_weavers_node.py (Lines 92-94)
def pattern_weavers_node(state: Dict[str, Any]) -> Dict[str, Any]:
    response = httpx.post(url, json={"query": state["input_text"]})
    result = response.json()
    
    matches = result.get("matches", [])
    
    # ❌ VIOLATION: Domain arithmetic
    scores = [m.get("score", 0.0) for m in matches]
    state["weave_confidence"] = sum(scores) / len(scores) if scores else 0.0
    
    return state
```

**Why Wrong**: 
1. `sum(scores) / len(scores)` is a domain calculation (average confidence)
2. Orchestration doesn't know what "confidence" means semantically
3. If confidence formula changes (weighted average?), graph node must change

---

#### ✅ CORRECT (Contract-Compliant)

**Sacred Order (Pattern Weavers Service)**:
```python
# services/api_pattern_weavers/api/routes.py

@router.post("/weave")
def weave_patterns(request: WeaveRequest):
    matches = weaver_consumer.search(request.query)
    
    # Service calculates domain metrics
    scores = [m.score for m in matches]
    avg_confidence = sum(scores) / len(scores) if scores else 0.0
    quality = "high" if avg_confidence > 0.7 else "low"
    
    return WeaveResult(
        matches=matches,
        metrics={
            "avg_confidence": avg_confidence,  # Pre-calculated
            "quality": quality,
            "threshold_met": avg_confidence >= config.threshold,
        },
        status="completed",
    )
```

**LangGraph Node**:
```python
# pattern_weavers_node.py (Contract-Compliant)

def pattern_weavers_node(state: Dict[str, Any]) -> Dict[str, Any]:
    response = httpx.post(url, json={"query": state["input_text"]})
    
    if response.status_code == 200:
        result = response.json()
        
        # Store opaque payload
        state["weave_result"] = result
        
        # Extract convenience fields (no calculation)
        state["matched_concepts"] = result.get("matches", [])
        state["weave_confidence"] = result.get("metrics", {}).get("avg_confidence", 0.0)
    else:
        state["weave_result"] = {"error": response.status_code}
        state["matched_concepts"] = []
    
    return state
```

**Key Difference**: Node **retrieves** pre-calculated `avg_confidence`, doesn't **compute** it.

---

### 4.2 Violation: Metric Calculation in Orchestration

#### ❌ WRONG

```python
# babel_gardens_node.py (Line 95)

start_time = datetime.now()
response = httpx.post(url, ...)
processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ❌

state["babel_metadata"] = {"processing_time_ms": processing_time}
```

**Why Wrong**: Service should return its own processing time. Node timing includes network latency (not service's responsibility).

---

#### ✅ CORRECT

**Service Returns Metrics**:
```python
# Babel Gardens service response
{
  "embedding": [...],
  "metadata": {
    "processing_time_ms": 42,  # Service's internal timing
    "model": "multilingual-v2"
  }
}
```

**Node Extracts, Not Calculates**:
```python
state["babel_metadata"] = result.get("metadata", {})  # Opaque pass-through
```

---

### 4.3 Correct: Routing Strategy in Orchestration

#### ✅ ALLOWED

```python
def babel_gardens_node(state: Dict[str, Any]) -> Dict[str, Any]:
    response = httpx.post(babel_url, json={"text": state["input_text"]})
    
    # ✅ Routing logic based on transport status
    if response.status_code == 503:
        logger.warning("Babel Gardens unavailable, using cached embeddings")
        return route_to("cached_embedding_node")  # Fallback strategy
    
    if response.status_code == 200:
        state["babel_result"] = response.json()
    else:
        state["babel_result"] = {"error": response.status_code}
    
    return state
```

**Why Correct**: 
- Decision is based on HTTP status (transport layer), not domain semantics
- Fallback is a routing strategy, not semantic interpretation
- Node doesn't evaluate if embedding is "good enough" (domain concern)

---

### 4.4 Incorrect: Semantic Threshold in Orchestration

#### ❌ FORBIDDEN

```python
def pattern_weavers_node(state: Dict[str, Any]) -> Dict[str, Any]:
    result = httpx.post(url, ...).json()
    
    # ❌ VIOLATION: Semantic threshold
    if result["metrics"]["avg_confidence"] < 0.7:
        logger.warning("Low confidence, routing to manual review")
        return route_to("manual_review_node")
    
    state["weave_result"] = result
    return state
```

**Why Wrong**: 
- "0.7" is a domain threshold (what does it mean? business decision!)
- Node interprets semantic quality (is confidence "good enough"?)
- Service should return `"quality": "low"` and node routes based on that status

---

#### ✅ CORRECT

**Service Returns Semantic Status**:
```python
# Pattern Weavers response
{
  "matches": [...],
  "metrics": {"avg_confidence": 0.65},
  "quality": "low",  # Service decides semantic quality
  "requires_review": true  # Service flags action needed
}
```

**Node Routes Based on Status**:
```python
def pattern_weavers_node(state: Dict[str, Any]) -> Dict[str, Any]:
    result = httpx.post(url, ...).json()
    state["weave_result"] = result
    
    # ✅ Route based on service's semantic flag
    if result.get("requires_review"):
        return route_to("manual_review_node")
    
    return state
```

---

### 4.5 Event Processor Example: Mnemosyne Node

#### ❌ WRONG (Calculating in Event Consumer)

```python
# mnemosyne_node.py (Violation)

def mnemosyne_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process semantic search results from Cognitive Bus."""
    
    event = state.get("event")
    matches = event["payload"]["matches"]
    
    # ❌ VIOLATION: Domain arithmetic
    similarity_scores = [m["similarity_score"] for m in matches]
    avg_similarity = sum(similarity_scores) / len(similarity_scores)  # ❌
    
    state["avg_similarity"] = avg_similarity
    return state
```

**Why Wrong**: 
- Event consumer calculates `avg_similarity` (domain metric)
- Averaging logic belongs in event **producer** (Sacred Order)
- Formula change requires modifying orchestration layer

---

#### ✅ CORRECT (Extract from Event Producer)

**Event Producer (Memory Orders Service)**:
```python
# services/api_memory_orders/adapters/bus_adapter.py

class BusAdapter:
    def publish_search_results(self, query_id: str, matches: List[Match]):
        """Emit semantic search results to Cognitive Bus."""
        
        # Pre-calculate all metrics in producer
        similarity_scores = [m.similarity_score for m in matches]
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        max_similarity = max(similarity_scores) if similarity_scores else 0.0
        
        payload = {
            "query_id": query_id,
            "matches": [m.to_dict() for m in matches],
            "metrics": {
                "avg_similarity": avg_similarity,  # ✅ Pre-calculated
                "max_similarity": max_similarity,
                "match_count": len(matches),
                "threshold_met": avg_similarity >= 0.7,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Publish to Redis Streams (XADD)
        self.bus.publish("memory.vector.match.fulfilled", payload)
```

**Event Consumer (Mnemosyne Node)**:
```python
# vitruvyan_core/core/orchestration/langgraph/node/mnemosyne_node.py

def mnemosyne_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract semantic search results from Cognitive Bus."""
    
    event = state.get("event")
    
    if event:
        payload = event.get("payload", {})
        
        # ✅ Extract pre-calculated metrics (no computation)
        state["search_results"] = payload.get("matches", [])
        state["avg_similarity"] = payload["metrics"]["avg_similarity"]  # ✅
        state["match_count"] = payload["metrics"]["match_count"]
        state["threshold_met"] = payload["metrics"]["threshold_met"]
    else:
        # Neutral fallback
        state["search_results"] = []
        state["avg_similarity"] = 0.0
    
    return state
```

**Key Pattern**: 
- Producer (Sacred Order) calculates → Consumer (LangGraph) extracts
- Same prohibition as HTTP nodes, different transport
- Redis Streams provides durable event log (not Pub/Sub)

---

## 5. Enforcement Rules

### 5.1 Automated Detection (Pre-Commit Hook)

**Forbidden Patterns in `langgraph/node/*.py`**:

```regex
# Arithmetic operations on collections
sum\([^\)]*\)
min\([^\)]*\)
max\([^\)]*\)

# Average calculations
/ len\(
.mean\(\)

# Threshold comparisons on domain terms
(confidence|score|quality|rating)\s*[<>]=?\s*\d

# Explicit sorting by domain criteria
sorted\(.*key=lambda.*\b(score|confidence|priority)

# Semantic filtering
\[.*for.*if.*\b(quality|confidence|score).*[<>]
```

---

### 5.2 CI Pipeline Guard

```bash
#!/bin/bash
# .github/scripts/enforce_orchestration_contract.sh

echo "🔍 Enforcing LangGraph Orchestration Contract v1.0..."

VIOLATIONS=0

# Check graph nodes for forbidden patterns
for FILE in vitruvyan_core/core/orchestration/langgraph/node/*.py; do
  if grep -E "sum\(|/ len\(|\.mean\(\)" "$FILE"; then
    echo "❌ VIOLATION: Domain arithmetic in $FILE"
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
  
  if grep -E "(confidence|score).*[<>].*\d|\d.*[<>].*(confidence|score)" "$FILE"; then
    echo "❌ VIOLATION: Threshold logic in $FILE"
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

if [ $VIOLATIONS -gt 0 ]; then
  echo ""
  echo "📜 See .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md"
  echo "   Section 3: Allowed vs Forbidden Responsibilities"
  exit 1
fi

echo "✅ Contract compliance verified"
```

---

### 5.3 Pytest Architectural Guard

```python
# tests/architectural/test_orchestration_contract.py

import ast
import glob
import re
import pytest

FORBIDDEN_FUNCTIONS = {"sum", "min", "max", "sorted"}
FORBIDDEN_ATTRIBUTES = {"mean", "median", "std"}
DOMAIN_TERMS = ["confidence", "score", "quality", "rating", "priority"]

def test_graph_nodes_contain_no_domain_arithmetic():
    """Verify LangGraph nodes don't perform domain calculations."""
    
    node_files = glob.glob("vitruvyan_core/core/orchestration/langgraph/node/*.py")
    violations = []
    
    for filepath in node_files:
        if filepath.endswith("__init__.py"):
            continue
        
        with open(filepath) as f:
            source = f.read()
            tree = ast.parse(source)
        
        # Check for forbidden function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if hasattr(node.func, "id"):
                    func_name = node.func.id
                elif hasattr(node.func, "attr"):
                    func_name = node.func.attr
                
                if func_name in FORBIDDEN_FUNCTIONS:
                    violations.append(f"{filepath}: Forbidden function {func_name}()")
        
        # Check for threshold comparisons
        for term in DOMAIN_TERMS:
            pattern = f"{term}\\s*[<>]=?\\s*\\d"
            if re.search(pattern, source):
                violations.append(f"{filepath}: Threshold comparison on '{term}'")
    
    if violations:
        msg = "\n".join([
            "❌ LangGraph Orchestration Contract v1.0 VIOLATIONS:",
            *violations,
            "",
            "See .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 3"
        ])
        pytest.fail(msg)

def test_graph_nodes_dont_interpret_semantics():
    """Verify nodes don't contain semantic interpretation logic."""
    
    node_files = glob.glob("vitruvyan_core/core/orchestration/langgraph/node/*.py")
    violations = []
    
    for filepath in node_files:
        if filepath.endswith("__init__.py"):
            continue
        
        with open(filepath) as f:
            source = f.read()
        
        # Check for semantic filtering
        patterns = [
            r"\[.*for.*if.*(quality|confidence).*[<>]",  # List comp with filter
            r"filter\(lambda.*:\s*.*\.(quality|confidence)",  # filter() usage
        ]
        
        for pattern in patterns:
            if re.search(pattern, source):
                violations.append(f"{filepath}: Semantic filtering detected")
                break
    
    if violations:
        pytest.fail("\n".join(violations))
```

---

## 6. Migration Path

### Phase 1: Service API Enrichment (Week 1)

**Objective**: Make Sacred Orders return pre-calculated metrics.

**Tasks**:
1. **Pattern Weavers**: Add `avg_confidence`, `quality`, `threshold_met` to response
2. **Babel Gardens**: Ensure `processing_time_ms` in metadata
3. **All Services**: Standardize response schema:
   ```json
   {
     "status": "completed",
     "data": { ... },
     "metrics": { "avg_confidence": 0.85, "quality": "high" },
     "metadata": { "processing_time_ms": 42 }
   }
   ```

**Validation**: Service tests verify metric presence.

---

### Phase 2: Graph Node Rewrite (Week 2)

**Objective**: Remove all domain logic from orchestration nodes.

**Checklist per node**:
- [ ] Remove `sum()`, `avg()`, `min()`, `max()` calls
- [ ] Remove threshold comparisons (`score > X`)
- [ ] Remove semantic filtering/sorting
- [ ] Replace calculations with extraction: `state["x"] = result["metrics"]["x"]`
- [ ] Verify line count < 60 (thin adapter target)

**Priority Order**:
1. `babel_gardens_node.py` (highest usage)
2. `pattern_weavers_node.py` (critical violation)
3. `codex_hunters_node.py`
4. Other nodes (audit first)

---

### Phase 3: Enforcement Activation (Week 3)

**Objective**: Make contract violations impossible to merge.

**Steps**:
1. Add pre-commit hook (`.git/hooks/pre-commit`)
2. Add CI check (`.github/workflows/architectural_checks.yml`)
3. Add pytest guards (`tests/architectural/`)
4. Update CONTRIBUTING.md to reference contract

**Success Criteria**:
```bash
# This must fail:
git commit -m "Add confidence calculation to node"
# ❌ Pre-commit hook blocks commit

# This must pass CI:
git commit -m "Extract confidence from service response"
# ✅ CI approves
```

---

## 7. Service Response Contract

### 7.1 Standard Schema

All Sacred Order APIs MUST return:

```typescript
{
  status: "completed" | "partial" | "error",
  data: { ... },  // Domain-specific payload
  metrics: {      // Pre-calculated domain metrics
    avg_confidence?: number,
    quality?: "high" | "medium" | "low",
    processing_time_ms?: number,
    // Add domain-specific metrics here
  },
  metadata: {     // Operational metadata
    model_version?: string,
    cached?: boolean,
    request_id?: string,
  },
  errors?: {      // Domain error codes
    code: string,  // e.g., "INSUFFICIENT_DATA"
    message: string,
    recoverable: boolean,
  }[]
}
```

---

### 7.2 Domain Error Codes

Services MUST return semantic error codes, not just HTTP status.

**Examples**:

| HTTP | Domain Code | Meaning | Graph Action |
|------|-------------|---------|--------------|
| 200 | `LOW_CONFIDENCE` | Result exists but uncertain | Route to validation |
| 400 | `INVALID_QUERY` | Input malformed | Return error to user |
| 503 | `MODEL_UNAVAILABLE` | Temporary failure | Route to fallback |
| 200 | `INSUFFICIENT_DATA` | Not enough context | Route to data enrichment |

**Usage**:
```python
# Service returns
{"status": "partial", "errors": [{"code": "LOW_CONFIDENCE", "recoverable": true}]}

# Node routes based on code
if result.get("errors", [{}])[0].get("code") == "LOW_CONFIDENCE":
    return route_to("validation_node")
```

---

## 8. Compliance Checklist

Before merging any LangGraph node code, verify:

- [ ] No `sum()`, `min()`, `max()`, `avg()` on domain data
- [ ] No `score > threshold` or similar comparisons
- [ ] No `sorted()`, `filter()` on domain criteria
- [ ] No `/len()` calculations (avg)
- [ ] No `.mean()`, `.std()`, `.median()` calls
- [ ] Extracts metrics from service response
- [ ] Stores opaque `<service>_result` payload
- [ ] Routes based on status codes or semantic flags, not thresholds
- [ ] Line count < 80 (thin adapter target)
- [ ] Passes `pytest tests/architectural/test_orchestration_contract.py`

---

## 9. Exceptions & Escalation

### Approved Exceptions

1. **State validation** (non-domain): Checking `if state.get("input_text")` is allowed
2. **Default values**: Setting `state["results"] = []` on error is allowed
3. **HTTP metrics**: Calculating network latency for *transport* monitoring is allowed

### Requesting Exception

If you believe a case requires domain logic in orchestration:

1. Open GitHub issue: `[Architecture] Contract Exception Request`
2. Describe use case and why service can't provide metric
3. Tag: @architecture-team
4. Required approvals: 2+ core maintainers

**Default answer**: NO. Refactor service instead.

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.0** | 2026-02-11 | Initial contract, binding enforcement |

---

## Appendix A: Current Violations Audit

### babel_gardens_node.py

**Line 95**: Processing time calculation
```python
processing_time = (datetime.now() - start_time).total_seconds() * 1000
```
**Fix**: Remove. Service should return `processing_time_ms` in metadata.

---

### pattern_weavers_node.py

**Lines 92-94**: Confidence aggregation
```python
scores = [m.get("score", 0.0) for m in matches]
state["weave_confidence"] = sum(scores) / len(scores) if scores else 0.0
```
**Fix**: Service must return `avg_confidence` in response.

---

## Appendix B: Reference Implementation

See `.github/examples/contract_compliant_node.py` for minimal reference implementation.

---

**END OF CONTRACT**

*This document is binding. Violations block CI/CD pipeline.*
