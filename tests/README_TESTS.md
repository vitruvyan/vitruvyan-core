# tests/ — Test Suite

> **Last Updated**: February 15, 2026  
> **Purpose**: Unit tests, integration tests, test helpers  
> **Type**: pytest-based test suite (unit + integration + e2e)

---

## 🎯 Cosa Contiene

`tests/` contiene la **suite di test** per Vitruvyan Core:
- Unit tests (pure logic, no I/O)
- Integration tests (Redis Streams, PostgreSQL, Qdrant)
- End-to-end tests (full flow validation)
- Test helpers & fixtures

**Caratteristiche**:
- ✅ **pytest**: Test framework standard
- ✅ **Fixtures**: Shared setup/teardown
- ✅ **Mocking**: Isolato da infra quando necessario
- ✅ **Coverage**: Target 95%+ (attuale: ~85%)

---

## 📂 Struttura

```
tests/
├── unit/                        # Unit tests (pure logic, no I/O)
│   ├── test_consumers/          → Sacred Orders consumers
│   ├── test_governance/         → Governance rules, classifiers
│   └── test_orchestration/      → LangGraph nodes (mocked state)
│
├── integration/                 # Integration tests (require infra)
│   ├── test_bus/                → StreamBus, Redis Streams
│   ├── test_postgres/           → PostgresAgent, database ops
│   ├── test_qdrant/             → QdrantAgent, vector ops
│   └── test_e2e/                → Full flow tests
│
├── verticals/                   # Domain-vertical tests (guarded)
│   └── test_finance_vertical.py → Finance plugin tests (importorskip)
│
├── architectural/               # Structural guardrail tests
│   ├── test_domain_agnostic_guardrails.py
│   └── test_import_boundaries.py
│
├── helpers/                     # Test utilities
│   ├── fixtures.py              → pytest fixtures (bus, db, mock data)
│   ├── mock_data.py             → Test data generators
│   └── assertions.py            → Custom assertions
│
├── conftest.py                  # pytest configuration, global fixtures
└── pytest.ini                   # pytest settings
```

---

## 🧪 Run Tests

### All Tests

```bash
# From repository root
pytest tests/

# With coverage
pytest tests/ --cov=vitruvyan_core --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Unit Tests Only (No Infra)

```bash
# Fast, no Docker required
pytest tests/unit/

# Specific test file
pytest tests/unit/test_consumers/test_coherence_checker.py

# Specific test function
pytest tests/unit/test_consumers/test_coherence_checker.py::test_coherence_score_calculation
```

### Integration Tests (Require Infra)

```bash
# Requires Docker services running
cd infrastructure/docker
docker compose up -d postgres redis qdrant

# Run integration tests
pytest tests/integration/

# Specific integration test
pytest tests/integration/test_bus/test_stream_bus.py
```

### End-to-End Tests

```bash
# Requires full stack running
cd infrastructure/docker
docker compose up -d

# Run e2e tests
pytest tests/integration/test_e2e/

# Specific e2e flow
pytest tests/integration/test_e2e/test_archive_flow.py
```

---

## 🎯 Test Patterns

### Unit Test Pattern (Pure Logic)

```python
# tests/unit/test_consumers/test_coherence_checker.py
from vitruvyan_core.core.governance.memory_orders.consumers import CoherenceChecker

def test_coherence_score_calculation():
    """Test coherence score for perfectly matching texts."""
    checker = CoherenceChecker()
    
    result = checker.calculate_coherence(
        text_a="The market is volatile",
        text_b="The market is volatile"
    )
    
    assert result.score == 1.0
    assert result.status == "COHERENT"
```

### Integration Test Pattern (Real Infra)

```python
# tests/integration/test_bus/test_stream_bus.py
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

def test_publish_consume_flow(stream_bus_fixture):
    """Test full publish-consume cycle with real Redis."""
    bus = stream_bus_fixture
    
    # Publish event
    bus.publish("test.channel", {"data": "test"})
    
    # Create consumer group
    bus.create_consumer_group("test.channel", "test_group")
    
    # Consume event
    for event in bus.consume("test.channel", "test_group", "consumer_1"):
        assert event.payload["data"] == "test"
        bus.acknowledge(event.stream, "test_group", event.event_id)
        break
```

### E2E Test Pattern (Full Flow)

```python
# tests/integration/test_e2e/test_archive_flow.py
import requests

def test_archive_request_flow(running_services):
    """Test full archive flow: request → processing → storage."""
    
    # 1. Request archive via Vault Keepers API
    response = requests.post(
        "http://localhost:9007/archive",
        json={"entity_id": "test_entity", "snapshot_data": {...}}
    )
    assert response.status_code == 200
    
    # 2. Verify event published to bus
    # (check Redis Streams)
    
    # 3. Verify archive stored in PostgreSQL
    # (check database)
```

---

## 🔧 Fixtures

### Global Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

@pytest.fixture(scope="session")
def stream_bus():
    """Provide StreamBus instance for integration tests."""
    bus = StreamBus()
    yield bus
    # Cleanup

@pytest.fixture(scope="session")
def postgres_agent():
    """Provide PostgresAgent for database tests."""
    pg = PostgresAgent()
    yield pg
    # Cleanup

@pytest.fixture
def mock_entity_data():
    """Generate mock entity data for tests."""
    return {
        "entity_id": "test_001",
        "name": "Test Entity",
        "created_at": "2026-02-12T00:00:00Z"
    }
```

### Using Fixtures

```python
def test_with_fixtures(stream_bus, mock_entity_data):
    """Test using global fixtures."""
    stream_bus.publish("test.channel", mock_entity_data)
    # ...
```

---

## 📊 Coverage

### Current Status

```
vitruvyan_core/core/
├── agents/              95% ✅
├── cognitive/           82% ⚠️
├── governance/          88% ✅
├── llm/                 76% ⚠️
├── orchestration/       79% ⚠️
└── synaptic_conclave/   91% ✅

Overall: ~85% (target: 95%)
```

### Generate Coverage Report

```bash
# HTML report
pytest tests/ --cov=vitruvyan_core --cov-report=html

# Terminal report
pytest tests/ --cov=vitruvyan_core --cov-report=term-missing

# Fail if coverage < 80%
pytest tests/ --cov=vitruvyan_core --cov-fail-under=80
```

---

## 🎯 Test Principles

1. **Fast Unit Tests**: No I/O, mocked dependencies
2. **Realistic Integration Tests**: Real Redis/PostgreSQL/Qdrant
3. **Clear Test Names**: `test_<what>_<scenario>_<expected>`
4. **Isolated Tests**: No shared state between tests
5. **Coverage Target**: 95%+ (incrementale)

---

## 📚 Documentazione

### Test-Specific Docs

Vedere [../docs/testing/](../docs/testing/):
- [Boot Test Plan](../docs/testing/BOOT_TEST_PLAN.md)
- [Boot Test Status](../docs/testing/BOOT_TEST_STATUS.md)

### Module Docs

Ogni modulo ha esempi testabili in `examples/`:
- `vitruvyan_core/core/governance/memory_orders/examples/`
- `vitruvyan_core/core/governance/vault_keepers/examples/`
- Ecc.

---

## 🚀 CI/CD Integration (Future)

```yaml
# .github/workflows/test.yml (esempio)
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ --cov=vitruvyan_core
      
      - name: Start infra (integration tests)
        run: docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis qdrant
      
      - name: Run integration tests
        run: pytest tests/integration/ --cov=vitruvyan_core --cov-append
      
      - name: Coverage report
        run: pytest --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📖 Link Utili

- **[Vitruvyan Core](../vitruvyan_core/README_VITRUVYAN_CORE.md)** — Source code being tested
- **[Services](../services/README_SERVICES.md)** — Service integration tests
- **[Infrastructure](../infrastructure/README_INFRASTRUCTURE.md)** — Docker setup for integration tests
- **[Docs Portal](../docs/index.md)** — Entry point documentazione

---

**Purpose**: Validate Vitruvyan Core functionality (unit + integration + e2e).  
**Framework**: pytest, coverage target 95%.  
**Status**: ~85% coverage, integration tests require Docker infra.
