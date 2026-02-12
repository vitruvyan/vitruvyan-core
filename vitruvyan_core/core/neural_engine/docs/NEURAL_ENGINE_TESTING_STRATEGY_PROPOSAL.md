# Neural Engine Testing Strategy - Architectural Proposal

**Date**: February 8, 2026  
**Context**: Neural Engine refactoring completed (commit `f737847`)  
**Purpose**: Decide optimal location for developer-friendly test scripts

---

## 🎯 What Has Been Completed

### 1. Domain-Agnostic Core Refactoring
- **Created**: `vitruvyan_core/contracts/` at root level
  - `IDataProvider` contract (190 lines): Generic data access interface
  - `IScoringStrategy` contract (185 lines): Generic scoring/ranking logic
  - **Decision**: Contracts at ROOT level (not inside `neural_engine/`) for cross-component reuse
  - **Rationale**: Future Allocation Engine, Optimization Engine, other Sacred Orders components will reuse same contracts

- **Created**: `vitruvyan_core/core/neural_engine/` domain-agnostic engine
  - `engine.py` (410 lines): Main `NeuralEngine` class with multi-factor logic
  - `scoring.py` (195 lines): Z-score normalization, composite score computation
  - `ranking.py` (225 lines): Percentile bucketing, stratification groups
  - `composite.py` (140 lines): Risk-adjusted composite calculations
  - **Philosophy**: Zero finance-specific code, 100% domain-agnostic

- **Created**: `vitruvyan_core/core/neural_engine/domain_examples/`
  - `mock_data_provider.py` (272 lines): Stub implementation with TODO comments showing Finance/Healthcare/Logistics examples
  - `mock_scoring_strategy.py` (304 lines): Stub with 2 profiles (balanced/aggressive)
  - `README.md`: Comprehensive guide for developers implementing new domains
  - **Purpose**: Teach developers HOW TO IMPLEMENT custom providers/strategies

### 2. Production Docker Container
- **Created**: `services/core/api_neural_engine/` (9 files, ~1,200 lines)
  - `Dockerfile` (77 lines): Multi-stage build (base → dependencies → final)
  - `main.py` (360 lines): FastAPI app with 6 endpoints, 15+ Prometheus metrics
  - `modules/engine_orchestrator.py` (230 lines): Bridge between FastAPI and NeuralEngine core
  - `schemas/api_models.py` (150 lines): Pydantic request/response models
  - `README.md` (350+ lines): Deployment guide, API documentation, architecture diagrams

- **Endpoints**: 
  1. `POST /screen` - Multi-factor screening with filters/stratification
  2. `POST /rank` - Single-feature ranking
  3. `GET /health` - Health check with dependency status
  4. `GET /metrics` - Prometheus metrics exposition
  5. `GET /profiles` - List available scoring profiles
  6. `GET /` - Service info

- **Port**: 8003 (Neural Engine canonical port from Sacred Orders)
- **Security**: Non-root user (uid 1000), health checks, input validation, CORS

### 3. Legacy Code Elimination
- **Deleted**: `vitruvyan_core/patterns/neural_engine/` (265 lines)
  - **Reason**: Broken imports to non-existent `core.cognitive.neural_engine` module
- **Deleted**: `vitruvyan_core/integration/` (319 lines)
  - **Reason**: Obsolete orchestration layer, now replaced by `EngineOrchestrator`
- **Deleted**: `examples/neural_engine_usage.py`, `examples/vertical_integration/`
  - **Reason**: Used old patterns, incompatible with new architecture
- **Deleted**: `tests/test_compatibility.py`, `tests/test_neural_engine_core.py`
  - **Reason**: Broken imports, superseded by `test_neural_engine_mock.py`

**Total Cleanup**: ~800 lines of legacy code eliminated

---

## 🤔 The Testing Strategy Question

**User Request**: Create a `tests/` or `examples/` folder with scripts that help developers understand how the Neural Engine service works.

**Two Competing Proposals**:

### Proposal A: `services/core/api_neural_engine/examples/` (MY RECOMMENDATION ⭐)

**Proposed Structure**:
```
services/core/api_neural_engine/
├── Dockerfile
├── main.py
├── modules/
├── schemas/
├── shared/
├── README.md
├── examples/                           # ← NEW: API consumption examples
│   ├── 01_health_check.sh             # curl http://localhost:8003/health
│   ├── 02_screen_basic.sh             # POST /screen with balanced profile
│   ├── 03_screen_filters.sh           # POST /screen with group filters
│   ├── 04_rank_by_feature.sh          # POST /rank by momentum
│   ├── 05_compare_profiles.py         # Python: balanced vs aggressive
│   └── README.md                       # Guide: how to use these scripts
└── tests/                              # pytest formal tests (future)
    └── test_api_endpoints.py
```

**What These Scripts Test**: The **deployed Docker container** (FastAPI REST API on port 8003)

**Example Script** (`02_screen_basic.sh`):
```bash
#!/bin/bash
# Test basic screening with balanced profile

curl -X POST http://localhost:8003/screen \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced",
    "top_k": 5
  }' | jq '.ranked_entities[] | {rank, entity_id, composite_score, percentile}'

# Expected output:
# {
#   "rank": 1,
#   "entity_id": "E004",
#   "composite_score": 1.23,
#   "percentile": 95.5
# }
```

**Advantages**:
1. ✅ **Tests the actual production interface** (HTTP REST API)
2. ✅ **Onboarding for service consumers** (frontend devs, orchestration devs)
3. ✅ **Deployment validation**: Run scripts after `docker compose up` to verify service works
4. ✅ **Consistent with Sacred Orders**: Each service container has its own examples (precedent: `services/mcp/`, `services/governance/`)
5. ✅ **Clear separation**: `domain_examples/` teaches IMPLEMENTATION (how to extend), `examples/` teaches CONSUMPTION (how to use)
6. ✅ **Realistic testing**: Requires Docker running (matches production environment)

**Disadvantages**:
1. ❌ Requires container running (`docker compose up neural_engine`)
2. ❌ Heavier setup (not just Python import)

---

### Proposal B: `vitruvyan-core/examples/neural_engine/` (ALTERNATIVE AGENT'S PROPOSAL)

**Proposed Structure** (from other VPS agent):
```
vitruvyan-core/
├── examples/
│   ├── neural_engine/                  # ← NEW: Core Python examples
│   │   ├── 01_basic_usage.py          # Import NeuralEngine, run with MockDataProvider
│   │   ├── 02_custom_provider.py      # Implement custom IDataProvider
│   │   ├── 03_custom_strategy.py      # Implement custom IScoringStrategy
│   │   └── README.md
│   └── ... (other examples)
```

**What These Scripts Test**: The **Python core library** (`vitruvyan_core.core.neural_engine.NeuralEngine` class)

**Example Script** (`01_basic_usage.py`):
```python
#!/usr/bin/env python3
from vitruvyan_core.core.neural_engine import NeuralEngine
from vitruvyan_core.core.neural_engine.domain_examples import MockDataProvider, MockScoringStrategy

# Initialize engine with mock domain
engine = NeuralEngine(
    data_provider=MockDataProvider(),
    scoring_strategy=MockScoringStrategy()
)

# Run screening
results = engine.run(profile="balanced", top_k=5)
print(f"Top 5 entities: {results.ranked_entities}")
```

**Advantages**:
1. ✅ **Lightweight**: No Docker required (direct Python import)
2. ✅ **Centralized examples**: All examples in one root `examples/` folder

**Disadvantages**:
1. ❌ **DUPLICATES `domain_examples/` purpose**: That folder already teaches core Python usage
2. ❌ **Wrong audience**: Most developers will consume the REST API, not import Python directly
3. ❌ **Doesn't test production interface**: Testing `NeuralEngine` class ≠ testing FastAPI service
4. ❌ **Inconsistent with Sacred Orders architecture**: Services are standalone containers, not Python libraries
5. ❌ **Maintenance burden**: Two places teaching same thing (`domain_examples/` vs `examples/neural_engine/`)

---

## 📊 Comparison Table

| Criterion | Proposal A (`api_neural_engine/examples/`) | Proposal B (`vitruvyan-core/examples/`) |
|-----------|---------------------------------------------|------------------------------------------|
| **What it tests** | FastAPI REST API (port 8003) | Python core library |
| **Target audience** | Service consumers (frontend, orchestration) | Library developers |
| **Production relevance** | ⭐⭐⭐⭐⭐ (tests actual deployment) | ⭐⭐ (tests internal implementation) |
| **Overlap with existing docs** | None (`domain_examples/` teaches implementation) | High (duplicates `domain_examples/`) |
| **Sacred Orders consistency** | ⭐⭐⭐⭐⭐ (each service has own examples) | ⭐⭐ (breaks container isolation) |
| **Setup complexity** | Medium (requires Docker) | Low (just Python) |
| **Use case coverage** | API consumption (80% of use cases) | Direct import (20% of use cases) |

---

## 🎯 My Architectural Recommendation: **Proposal A**

### Core Rationale

**Vitruvyan's Sacred Orders architecture treats Neural Engine as a STANDALONE SERVICE, not a Python library.**

The vast majority of developers will:
1. **Call the REST API** (from LangGraph, frontend, other services)
2. **NOT import Python directly** (that's only for extending the engine with new domains)

**Separation of Concerns**:
- `vitruvyan_core/core/neural_engine/domain_examples/` → **IMPLEMENTATION**: "How do I create a custom provider/strategy?"
- `services/core/api_neural_engine/examples/` → **CONSUMPTION**: "How do I use the Neural Engine API?"

These are **orthogonal concerns**. Most developers need CONSUMPTION examples (80%), not IMPLEMENTATION examples (20%).

### Real-World Analogy

Think of **PostgreSQL**:
- **Implementation docs** (`domain_examples/` equivalent): "How to write a custom storage engine extension in C"
- **Consumption examples** (`examples/` equivalent): "How to connect from Python, insert data, query with SQL"

**Which do 80% of users need?** The consumption examples (SQL queries), not the C extension guide.

Neural Engine is the same: Most users will `curl http://neural-engine:8003/screen`, not `from vitruvyan_core.core.neural_engine import NeuralEngine`.

---

## 🧪 Proposed Implementation Plan (Proposal A)

### Phase 1: Create Basic Examples (2 hours)

**Files to create**:
1. `services/core/api_neural_engine/examples/01_health_check.sh`
   ```bash
   #!/bin/bash
   echo "Testing Neural Engine health..."
   curl -s http://localhost:8003/health | jq
   ```

2. `services/core/api_neural_engine/examples/02_screen_basic.sh`
   ```bash
   #!/bin/bash
   echo "Screening with balanced profile..."
   curl -X POST http://localhost:8003/screen \
     -H "Content-Type: application/json" \
     -d '{"profile": "balanced", "top_k": 5}' | jq '.ranked_entities'
   ```

3. `services/core/api_neural_engine/examples/03_screen_filters.sh`
   ```bash
   #!/bin/bash
   echo "Screening with group filter..."
   curl -X POST http://localhost:8003/screen \
     -H "Content-Type: application/json" \
     -d '{
       "profile": "balanced",
       "filters": {"group": "GroupA"},
       "top_k": 5
     }' | jq
   ```

4. `services/core/api_neural_engine/examples/04_rank_by_feature.sh`
   ```bash
   #!/bin/bash
   echo "Ranking by momentum feature..."
   curl -X POST http://localhost:8003/rank \
     -H "Content-Type: application/json" \
     -d '{
       "feature_name": "momentum",
       "top_k": 5,
       "higher_is_better": true
     }' | jq '.ranked_entities'
   ```

5. `services/core/api_neural_engine/examples/05_compare_profiles.py`
   ```python
   #!/usr/bin/env python3
   """
   Compare screening results between balanced and aggressive profiles.
   """
   import requests
   import json
   
   def screen(profile: str):
       response = requests.post(
           "http://localhost:8003/screen",
           json={"profile": profile, "top_k": 5}
       )
       return response.json()
   
   balanced = screen("balanced")
   aggressive = screen("aggressive")
   
   print("=== Balanced Profile ===")
   for entity in balanced["ranked_entities"][:3]:
       print(f"{entity['rank']}. {entity['entity_id']}: {entity['composite_score']:.2f}")
   
   print("\n=== Aggressive Profile ===")
   for entity in aggressive["ranked_entities"][:3]:
       print(f"{entity['rank']}. {entity['entity_id']}: {entity['composite_score']:.2f}")
   ```

6. `services/core/api_neural_engine/examples/README.md`
   ```markdown
   # Neural Engine API Examples
   
   Practical scripts demonstrating how to consume the Neural Engine REST API.
   
   ## Prerequisites
   - Docker container running: `docker compose up neural_engine`
   - `jq` installed: `sudo apt install jq`
   
   ## Quick Start
   ```bash
   # Make scripts executable
   chmod +x examples/*.sh
   
   # Test health endpoint
   ./examples/01_health_check.sh
   
   # Run basic screening
   ./examples/02_screen_basic.sh
   ```
   
   ## Scripts
   1. **01_health_check.sh** - Verify service health and dependencies
   2. **02_screen_basic.sh** - Basic screening with balanced profile
   3. **03_screen_filters.sh** - Screening with group filters
   4. **04_rank_by_feature.sh** - Ranking by single feature (momentum)
   5. **05_compare_profiles.py** - Python: Compare balanced vs aggressive
   
   ## For Implementation Guides
   See `vitruvyan_core/core/neural_engine/domain_examples/` for guides on:
   - Creating custom IDataProvider implementations
   - Creating custom IScoringStrategy implementations
   ```

### Phase 2: Add pytest Integration Tests (4 hours)

**File**: `services/core/api_neural_engine/tests/test_api_integration.py`
```python
import pytest
import requests

BASE_URL = "http://localhost:8003"

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "orchestrator" in data["dependencies"]

def test_screen_endpoint():
    response = requests.post(
        f"{BASE_URL}/screen",
        json={"profile": "balanced", "top_k": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["ranked_entities"]) == 5
    assert data["profile"] == "balanced"

# ... more tests
```

---

## ❓ Decision Required

**User (you)**: Please decide between:

1. **Proposal A** (my recommendation): `services/core/api_neural_engine/examples/`
   - Rationale: Tests production interface, targets service consumers (80% use case)
   
2. **Proposal B** (other agent's proposal): `vitruvyan-core/examples/neural_engine/`
   - Rationale: Centralized examples, lightweight setup

**OR**: Hybrid approach (create BOTH)?

---

## 📝 Next Steps After Decision

**If Proposal A chosen**:
1. Create `examples/` folder with 6 files (5 scripts + README)
2. Test all scripts with `docker compose up neural_engine`
3. Add section to `services/core/api_neural_engine/README.md` referencing examples
4. Create `tests/test_api_integration.py` for formal pytest coverage

**If Proposal B chosen**:
1. Create `examples/neural_engine/` at root with 4 Python scripts
2. Test scripts with direct import (no Docker)
3. Update `vitruvyan_core/core/neural_engine/README.md` to reference examples

**If Hybrid**:
1. Create both folders (but acknowledge overlap risk)
2. Clearly document when to use which (consumption vs implementation)

---

## 📚 References

- Commit: `f737847` (Neural Engine refactoring)
- File: `services/core/api_neural_engine/README.md` (API documentation)
- File: `vitruvyan_core/core/neural_engine/domain_examples/README.md` (Implementation guide)
- File: `vitruvyan_core/contracts/README.md` (Contracts architecture rationale)
- File: `docs/NEURAL_ENGINE_ARCHITECTURE.md` (Complete architecture overview)

---

**Prepared by**: GitHub Copilot Agent (VPS 1)  
**For**: GitHub Copilot Agent (VPS 2)  
**Awaiting**: User decision on testing strategy
