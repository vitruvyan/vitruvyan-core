# Cognitive Bus - Separation of Concerns Architecture
**Date**: February 6, 2026 (Post-FASE 1-4 Refactoring)  
**Status**: ✅ PRODUCTION READY

---

## 1. Executive Summary

Il Cognitive Bus di Vitruvyan segue il pattern **"Standalone Service Library"** ispirato a FastAPI, SQLAlchemy e Celery:
- **Core Library** in `vitruvyan-core/core/cognitive_bus/`: Business logic riutilizzabile
- **Services** in `vitruvyan-core/services/`: Microservizi Docker che consumano la library
- **Zero duplicazione**: I service sono thin wrappers che delegano alla core library

Questa separazione garantisce:
- ✅ **Riusabilità**: Core library usabile da qualsiasi service
- ✅ **Testabilità**: Business logic testabile senza Docker
- ✅ **Manutenibilità**: Modifiche alla library si propagano a tutti i services
- ✅ **Scalabilità**: Services possono scalare indipendentemente dalla library

---

## 2. Directory Structure

```
vitruvyan-core/
├── core/
│   └── cognitive_bus/              🏛️ CORE LIBRARY (standalone)
│       ├── __init__.py            → Public API exports
│       ├── transport/             → StreamBus, Redis Streams transport
│       │   └── streams.py         → StreamBus class (642 lines)
│       ├── events/                → Event schemas (CognitiveEvent, TransportEvent)
│       │   └── event_envelope.py  → Frozen dataclasses
│       ├── listeners/             → Business logic implementations (6 listeners)
│       │   ├── babel_gardens.py   → Linguistic processing listener
│       │   ├── codex_hunters.py   → Discovery expedition listener
│       │   ├── langgraph.py       → LangGraph orchestration listener
│       │   ├── mcp.py             → Model Context Protocol listener
│       │   ├── shadow_traders.py  → Trading strategy listener
│       │   └── vault_keepers.py   → Knowledge preservation listener
│       ├── consumers/             → Consumer patterns
│       │   └── listener_adapter.py → wrap_legacy_listener (zero-code migration)
│       ├── governance/            → Epistemic governance modules
│       ├── plasticity/            → Adaptive learning system
│       ├── orthodoxy/             → Validation rules
│       ├── monitoring/            → Metrics and observability
│       ├── client/                → High-level client API
│       ├── utils/                 → Shared utilities
│       ├── philosophy/            → Design principles
│       └── docs/                  → Architecture documentation
│
└── services/                      🐳 DOCKER SERVICES (thin wrappers)
    ├── governance/
    │   ├── api_vault_keepers/
    │   │   ├── main.py            → FastAPI service
    │   │   ├── redis_listener.py  → Legacy Pub/Sub handler (business logic)
    │   │   └── streams_listener.py → NEW: Thin wrapper
    │   │       import: from core.cognitive_bus.consumers import wrap_legacy_listener
    │   │       pattern: wrap_legacy_listener(redis_listener, "vault_keepers", channels)
    │   │
    │   └── api_orthodoxy_wardens/
    │       ├── main.py
    │       ├── redis_listener.py
    │       └── streams_listener.py → Same pattern
    │
    └── core/
        ├── api_memory_orders/
        │   ├── main.py            → import: from core.cognitive_bus.transport.streams import StreamBus
        │   └── (needs streams_listener.py)
        │
        ├── api_codex_hunters/
        │   ├── main.py            → import: from core.cognitive_bus.transport.streams import StreamBus
        │   └── (needs streams_listener.py)
        │
        └── ...
```

---

## 3. Import Policy (MANDATORY)

### ✅ CORRECT: Import from core library
```python
# In ANY service file (main.py, streams_listener.py, etc.)
from core.cognitive_bus.transport.streams import StreamBus
from core.cognitive_bus.events.event_envelope import CognitiveEvent, TransportEvent
from core.cognitive_bus.consumers import wrap_legacy_listener
from core.cognitive_bus.listeners.vault_keepers import VaultKeepersListener
```

### ❌ WRONG: Old vitruvyan_core imports (DELETED in FASE 4)
```python
# DEPRECATED - These paths no longer exist (55 files, 25,605 lines removed)
from vitruvyan_core.core.foundation.cognitive_bus import get_redis_bus  # ❌ DELETED
from vitruvyan_core.core.foundation.cognitive_bus.streams import StreamBus  # ❌ DELETED
from vitruvyan_core.core.foundation.cognitive_bus.consumers import ListenerAdapter  # ❌ DELETED
```

### ❌ WRONG: Relative imports across boundaries
```python
# DON'T import service code from core library
from services.governance.api_vault_keepers.main import VaultKeepersService  # ❌ VIOLATES SEPARATION
```

---

## 4. Separation of Concerns Rules

### 4.1 Core Library (`core/cognitive_bus/`)

**Responsibility**: Business logic, algorithms, protocols  
**Characteristics**:
- ✅ Pure Python (no Docker dependencies)
- ✅ Testable without containers
- ✅ Reusable across multiple services
- ✅ No service-specific configuration
- ✅ No hardcoded URLs, ports, or service names

**Examples of what BELONGS in core library**:
- StreamBus transport logic
- Event schema definitions
- Listener business logic (pattern recognition, processing algorithms)
- ListenerAdapter pattern
- Plasticity learning algorithms
- Orthodoxy validation rules

**Examples of what DOES NOT BELONG**:
- ❌ FastAPI routes
- ❌ Docker entrypoints
- ❌ Service-specific environment variables
- ❌ Hard-coded service URLs (e.g., "http://vitruvyan_redis:6379")

---

### 4.2 Services (`services/`)

**Responsibility**: Deployment wrappers, API endpoints, service integration  
**Characteristics**:
- ✅ Thin wrappers around core library
- ✅ FastAPI routes expose library functions
- ✅ Docker entrypoints (main.py, streams_listener.py)
- ✅ Service-specific configuration (env vars, ports)
- ✅ Dependency injection of config to library

**Examples of what BELONGS in services**:
- FastAPI application setup
- Health check endpoints
- Environment variable parsing
- Docker compose service definitions
- Prometheus metrics collection
- Logging configuration

**Examples of what DOES NOT BELONG**:
- ❌ Complex business logic (move to core library)
- ❌ Algorithm implementations (move to core library)
- ❌ Duplicate code between services (extract to library)

---

## 5. Listener Migration Pattern (Zero-Code-Change)

For services with existing `redis_listener.py` (legacy Pub/Sub), create `streams_listener.py` wrapper:

```python
# services/governance/api_vault_keepers/streams_listener.py
#!/usr/bin/env python3
"""
🔐 Vault Keepers - Redis Streams Listener (Phase 2 Migration)
ZERO-CODE-CHANGE wrapper using ListenerAdapter.
"""
import asyncio
import sys

sys.path.insert(0, '/app')

# Import existing legacy listener (NO MODIFICATIONS to redis_listener.py)
from redis_listener import VaultKeepersCognitiveBusListener

# Import core library adapter
from core.cognitive_bus.consumers import wrap_legacy_listener

async def main():
    """Start Vault Keepers Streams listener"""
    
    # Step 1: Instantiate existing legacy listener (NO CHANGES)
    legacy_listener = VaultKeepersCognitiveBusListener()
    
    # Step 2: Define sacred channels
    sacred_channels = [
        "vault.archive.requested",
        "vault.restore.requested",
        "vault.snapshot.requested",
        "orthodoxy.audit.completed",
        "neural_engine.screening.completed"
    ]
    
    # Step 3: Wrap with ListenerAdapter (handles Streams → Pub/Sub conversion)
    streams_consumer = wrap_legacy_listener(
        listener_instance=legacy_listener,
        listener_name="vault_keepers",
        sacred_channels=sacred_channels,
        handler_method_name="handle_event"  # Method in legacy listener
    )
    
    # Step 4: Start consuming from Redis Streams
    await streams_consumer.start()

if __name__ == "__main__":
    asyncio.run(main())
```

**Benefits**:
- ✅ **Zero code changes** to existing `redis_listener.py`
- ✅ **Gradual migration**: Services can run BOTH Pub/Sub and Streams listeners simultaneously
- ✅ **Rollback-friendly**: Just switch back to Pub/Sub if issues arise
- ✅ **Reusable pattern**: Same `wrap_legacy_listener` for all 7 services

---

## 6. Best Practices

### 6.1 When Adding New Features

**Question**: Should this code go in `core/cognitive_bus/` or `services/`?

**Decision Tree**:
1. **Is it business logic or an algorithm?** → Core library
2. **Is it reusable across multiple services?** → Core library
3. **Is it service-specific deployment code?** → Service
4. **Is it a FastAPI route?** → Service
5. **Is it environment-specific configuration?** → Service

**Example - Adding sentiment analysis to bus**:
- ❌ BAD: Add sentiment code to `services/governance/api_vault_keepers/main.py`
- ✅ GOOD: Create `core/cognitive_bus/modules/sentiment_analysis.py`, import in services

---

### 6.2 Testing Strategy

**Core Library Tests**:
```bash
# Test WITHOUT Docker
cd vitruvyan-core/
pytest tests/test_cognitive_bus_streams.py  # Pure Python, no containers
pytest tests/test_listener_adapter.py       # Unit tests
```

**Service Integration Tests**:
```bash
# Test WITH Docker
docker compose up -d vitruvyan_redis vitruvyan_vault_keepers
pytest tests/test_vault_keepers_integration.py  # E2E with containers
```

---

### 6.3 Documentation Updates

When modifying core library, update:
- `core/cognitive_bus/docs/API_REFERENCE.md` - Public API changes
- `core/cognitive_bus/docs/BUS_ARCHITECTURE.md` - Architecture changes
- `core/cognitive_bus/docs/COGNITIVE_BUS_GUIDE.md` - Usage examples

When adding new service, document:
- `services/<service_name>/README.md` - Service-specific setup
- `infrastructure/docker/docker-compose.yml` - Container definition

---

## 7. Current Migration Status (Feb 6, 2026)

### ✅ Phase 1-4 Complete (FASE 1+2+3+4)
- ✅ FASE 1: Listener separation (2,153 lines moved to core/cognitive_bus/listeners/)
- ✅ FASE 2: Directory organization (flat → 12 subdirs)
- ✅ FASE 3: Import cleanup (fixed transitive dependencies)
- ✅ FASE 4: Legacy deletion (55 files, 25,605 lines removed from vitruvyan_core/)

### ✅ Services with Streams Listeners
- ✅ `services/governance/api_vault_keepers/` - streams_listener.py (82 lines)
- ✅ `services/governance/api_orthodoxy_wardens/` - streams_listener.py (85 lines)

### 🚧 Services Needing Streams Listeners (5 remaining)
- ⏳ `services/core/api_memory_orders/`
- ⏳ `services/core/api_codex_hunters/`
- ⏳ `services/core/api_babel_gardens/`
- ⏳ `services/core/api_langgraph/` (if separate listener needed)
- ⏳ `services/core/api_mcp/` (if separate listener needed)

---

## 8. Validation Checklist

Before merging any changes to `core/cognitive_bus/` or `services/`, verify:

- [ ] ✅ No imports from `vitruvyan_core.core.foundation.cognitive_bus` (path no longer exists)
- [ ] ✅ All service imports use `core.cognitive_bus.*`
- [ ] ✅ No business logic duplicated between services
- [ ] ✅ No hardcoded service URLs in core library
- [ ] ✅ Core library code is Docker-agnostic (can run standalone)
- [ ] ✅ Services are thin wrappers (no complex algorithms in main.py)
- [ ] ✅ Tests pass for modified modules
- [ ] ✅ Docker builds succeed: `docker compose build <service_name>`
- [ ] ✅ Documentation updated

---

## 9. References

**Core Library Documentation**:
- `core/cognitive_bus/docs/BUS_ARCHITECTURE.md` (419 lines)
- `core/cognitive_bus/docs/COGNITIVE_BUS_GUIDE.md` (988 lines)
- `core/cognitive_bus/docs/API_REFERENCE.md` (600 lines)

**Refactoring History**:
- `docs/CHANGELOG_JAN26_2026.md` - FASE 1-3 implementation
- `docs/CHANGELOG_PHASE3_JAN26_2026.md` - Import cleanup details
- `docs/LISTENER_MIGRATION_STATUS.md` - Phase 2 listener migration

**Architectural Decisions**:
- `core/cognitive_bus/docs/ARCHITECTURAL_DECISIONS.md` (588 lines)
- `docs/Vitruvyan_Octopus_Mycelium_Architecture.md` - Bio-inspired design principles

---

## 10. Common Issues & Solutions

### Issue: "ImportError: No module named 'vitruvyan_core.core.foundation.cognitive_bus'"
**Cause**: Using old import path after FASE 4 deletion  
**Solution**: Replace with `from core.cognitive_bus.transport.streams import StreamBus`

### Issue: "Cannot find StreamBus in core.cognitive_bus"
**Cause**: Not importing from correct submodule  
**Solution**: Use `from core.cognitive_bus.transport.streams import StreamBus` (NOT `from core.cognitive_bus import StreamBus`)

### Issue: "Service has complex business logic in main.py"
**Cause**: Violates separation of concerns  
**Solution**: Extract business logic to `core/cognitive_bus/modules/<module_name>.py`, import in service

### Issue: "Want to test core library but requires Docker"
**Cause**: Service-specific dependencies mixed with library code  
**Solution**: Refactor to use dependency injection. Library should accept config objects, not read env vars directly.

---

**Last Updated**: February 6, 2026  
**Status**: ✅ PRODUCTION READY  
**Architecture Version**: 2.0 (Post-FASE 1-4 Refactoring)
