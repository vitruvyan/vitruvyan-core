# Graph Orchestrator E2E Tests

**End-to-end tests for `api_graph` service**

---

## Overview

This test suite validates the Graph Orchestrator API (`api_graph`) with real-world scenarios covering:
- Health checks and monitoring
- Graph execution (single-shot, multi-turn dialogue)
- Entity resolution and autocomplete
- Slot filling for missing parameters
- Audit monitoring integration
- Full conversational pipelines

---

## Prerequisites

**1. Docker stack running:**
```bash
cd infrastructure/docker
docker compose ps | grep core_graph
# Expected: core_graph (healthy), core_postgres (healthy), core_redis (healthy)
```

**2. Service accessible:**
```bash
curl http://localhost:9004/health
# Expected: {"status":"healthy","service":"api_graph","version":"2.0.0"}
```

**3. Python 3.11+:**
```bash
python3 --version  # >= 3.11
```

---

## Setup

### Install dependencies

```bash
cd services/api_graph/examples
pip install -r requirements.txt
```

**Dependencies:**
- `httpx==0.27.0` — HTTP client (sync/async)
- `pytest==8.0.0` — Test framework
- `pytest-asyncio==0.23.0` — Async test support
- `pydantic==2.12.4` — Data validation

---

## Test Suite

### 1. Health Checks (`test_health.py`)

**Purpose**: Verify service connectivity and status

**Tests:**
- `test_health_endpoint` — Basic health check
- `test_health_schema` — Validate response schema
- `test_pg_health` — PostgreSQL placeholder
- `test_qdrant_health` — Qdrant placeholder
- `test_metrics_endpoint` — Prometheus metrics

**Run:**
```bash
pytest test_health.py -v
```

**Expected output:**
```
test_health.py::test_health_endpoint PASSED
test_health.py::test_health_schema PASSED
test_health.py::test_pg_health PASSED
test_health.py::test_qdrant_health PASSED
test_health.py::test_metrics_endpoint PASSED
```

---

### 2. Simple Graph Execution (`test_graph_simple.py`)

**Purpose**: Execute single-intent graphs (no slot filling)

**Tests:**
- `test_graph_run_investment_verdict` — "Should I invest in Apple?"
- `test_graph_dispatch` — Backward compatibility endpoint
- `test_graph_with_dispatch` — Audit monitoring wrapper
- `test_graph_timeout` — Long-running queries

**Run:**
```bash
pytest test_graph_simple.py -v
```

**Expected output:**
```
test_graph_simple.py::test_graph_run_investment_verdict PASSED
test_graph_simple.py::test_graph_dispatch PASSED
test_graph_simple.py::test_graph_with_dispatch PASSED
test_graph_simple.py::test_graph_timeout PASSED
```

---

### 3. Slot Filling (`test_graph_slots.py`)

**Purpose**: Multi-turn dialogue for incomplete queries

**Tests:**
- `test_incomplete_query_slot_questions` — Missing parameters → questions
- `test_slot_filling_flow` — Iterative slot completion
- `test_slot_validation` — Invalid slot values
- `test_skip_slots_with_entities` — Pre-validated entities

**Scenario:**
```
User: "I want to invest"  (missing: entities, horizon, risk)
Bot: "Which companies are you interested in?"
User: "Apple and Microsoft"
Bot: "What is your investment horizon?"
User: "Long term"
Bot: "Based on Apple and Microsoft for long-term..."
```

**Run:**
```bash
pytest test_graph_slots.py -v
```

---

### 4. Entity Search (`test_entity_search.py`)

**Purpose**: Autocomplete and fuzzy entity matching

**Tests:**
- `test_entity_search_exact_match` — "AAPL" → Apple Inc.
- `test_entity_search_fuzzy` — "app" → Apple, Appian
- `test_entity_search_no_results` — "xyz999" → empty
- `test_entity_search_ranking` — Match score ordering

**Match scoring:**
- `1.0` — Exact match (AAPL → AAPL)
- `0.9` — Starts with (app → Apple)
- `0.7` — Prefix similarity (appl → Apple)
- `0.3` — Contains (pple → Apple)

**Run:**
```bash
pytest test_entity_search.py -v
```

---

### 5. Audit Monitoring (`test_audit.py`)

**Purpose**: Validate execution tracking and metrics

**Tests:**
- `test_audit_health` — Monitoring session status
- `test_audit_metrics` — Performance counters
- `test_audit_trigger` — Manual audit trigger
- `test_grafana_webhook` — Alert receiver

**Metrics tracked:**
- Execution count (graphs run)
- Error count + types
- Average/min/max duration
- Last execution timestamp
- Node-level timings

**Run:**
```bash
pytest test_audit.py -v
```

---

### 6. Full Pipeline (`test_e2e_pipeline.py`)

**Purpose**: End-to-end conversational flow validation

**Tests:**
- `test_pipeline_simple_verdict` — Query → verdict
- `test_pipeline_with_entity_search` — Autocomplete → graph
- `test_pipeline_slot_filling` — Incomplete → clarify → verdict
- `test_pipeline_comparison` — "Apple vs Microsoft"
- `test_pipeline_portfolio_gauge` — Portfolio health

**Full flow example:**
```
1. User: "Should I buy tech stocks?"
2. System: Fuzzy search "tech" → [AAPL, MSFT, GOOGL, ...]
3. User: "Apple and Microsoft"
4. System: Resolve "Apple" → AAPL, "Microsoft" → MSFT
5. System: Missing slot "investment_horizon"
6. System: "What is your investment horizon?"
7. User: "Long term"
8. Graph: Run screener + sentiment + portfolio nodes
9. Compose: Format verdict with gauge
10. Response: "Leonardo: Based on Apple and Microsoft..."
```

**Run:**
```bash
pytest test_e2e_pipeline.py -v
```

---

## Running All Tests

```bash
# Run all tests
pytest -v

# Show output for debugging
pytest -v -s

# Stop at first failure
pytest -x

# Run specific test
pytest test_health.py::test_health_endpoint -v

# Show full diff on assertion failure
pytest --tb=short
```

---

## Expected Results

**All tests passing:**
```
======================== test session starts =========================
collected 28 items

test_health.py::test_health_endpoint PASSED                    [  3%]
test_health.py::test_health_schema PASSED                      [  7%]
test_health.py::test_pg_health PASSED                          [ 10%]
test_health.py::test_qdrant_health PASSED                      [ 14%]
test_health.py::test_metrics_endpoint PASSED                   [ 17%]
test_graph_simple.py::test_graph_run_investment_verdict PASSED [ 21%]
test_graph_simple.py::test_graph_dispatch PASSED               [ 25%]
test_graph_simple.py::test_graph_with_dispatch PASSED          [ 28%]
test_graph_simple.py::test_graph_timeout PASSED                [ 32%]
test_graph_slots.py::test_incomplete_query_slot_questions PASSED [ 35%]
test_graph_slots.py::test_slot_filling_flow PASSED             [ 39%]
test_graph_slots.py::test_slot_validation PASSED               [ 42%]
test_graph_slots.py::test_skip_slots_with_entities PASSED      [ 46%]
test_entity_search.py::test_entity_search_exact_match PASSED   [ 50%]
test_entity_search.py::test_entity_search_fuzzy PASSED         [ 53%]
test_entity_search.py::test_entity_search_no_results PASSED    [ 57%]
test_entity_search.py::test_entity_search_ranking PASSED       [ 60%]
test_audit.py::test_audit_health PASSED                        [ 64%]
test_audit.py::test_audit_metrics PASSED                       [ 67%]
test_audit.py::test_audit_trigger PASSED                       [ 71%]
test_audit.py::test_grafana_webhook PASSED                     [ 75%]
test_e2e_pipeline.py::test_pipeline_simple_verdict PASSED      [ 78%]
test_e2e_pipeline.py::test_pipeline_with_entity_search PASSED  [ 82%]
test_e2e_pipeline.py::test_pipeline_slot_filling PASSED        [ 85%]
test_e2e_pipeline.py::test_pipeline_comparison PASSED          [ 89%]
test_e2e_pipeline.py::test_pipeline_portfolio_gauge PASSED     [ 92%]

======================== 28 tests passed in 12.34s ========================
```

---

## Troubleshooting

### Service not responding

```bash
# Check container status
docker ps --filter name=core_graph

# View logs
docker logs core_graph --tail=50

# Restart service
docker compose restart graph
```

### Connection refused

```bash
# Verify port mapping
docker port core_graph
# Expected: 8004/tcp -> 0.0.0.0:9004

# Test from container network
docker run --rm --network vitruvyan_core_net alpine wget -O- http://core_graph:8004/health
```

### Database not available

```bash
# Check postgres container
docker logs core_postgres --tail=30

# Verify connectivity from graph container
docker exec core_graph curl http://core_postgres:5432
```

### Test failures

```bash
# Run with detailed output
pytest -vv --tb=long

# Show print statements
pytest -s

# Enable DEBUG logging
export LOG_LEVEL=DEBUG
pytest -v
```

---

## Development

### Adding new tests

```python
# test_new_feature.py

import httpx
import pytest

BASE_URL = "http://localhost:9004"

def test_new_feature():
    response = httpx.get(f"{BASE_URL}/new_endpoint")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
```

### Mocking external dependencies

```python
# Mock PostgreSQL
@pytest.fixture
def mock_postgres(monkeypatch):
    def fake_fetch(*args):
        return [{"id": "AAPL", "name": "Apple Inc."}]
    monkeypatch.setattr("adapters.persistence.fetch", fake_fetch)
    yield

def test_with_mock(mock_postgres):
    # Test runs without real database
    ...
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker compose up -d --wait graph postgres redis
      - name: Run tests
        run: |
          pip install -r services/api_graph/examples/requirements.txt
          pytest services/api_graph/examples/ -v
```

---

## Related Documentation

- **Graph API**: [`services/api_graph/README.md`](../README.md)
- **Core Orchestration**: [`vitruvyan_core/core/orchestration/README.md`](../../../vitruvyan_core/core/orchestration/README.md)
- **Deployment**: [`infrastructure/docker/README.md`](../../../infrastructure/docker/README.md)

---

## License

Proprietary — Vitruvyan Core Team
