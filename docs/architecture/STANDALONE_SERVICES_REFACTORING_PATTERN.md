# Standalone Services Refactoring Pattern (Kernel Documentation)
**Version**: 1.0  
**Date**: February 6, 2026  
**Status**: 🟢 CANONICAL - Part of vitruvyan-core kernel  
**Purpose**: Define the architectural pattern for refactoring Vitruvyan services as standalone, reusable modules

---

## 🎯 Vision: Services as Foundation Libraries

**Philosophy**: Every major service in Vitruvyan should be architecturally independent, well-documented, and reusable across projects—just like FastAPI, Celery, or SQLAlchemy.

**Benefits**:
- **Multi-repo strategy**: Core services in vitruvyan-core, applications in vitruvyan
- **Easier testing**: Import classes directly, no Docker required
- **Better onboarding**: Intuitive structure, comprehensive docs (45-min learning curve instead of 4-6h)
- **Scalability**: Add features without tangling with deployment code
- **Professionalism**: Structure comparable to industry-standard open-source projects

---

## 📐 The Cognitive Bus Pattern (Reference Implementation)

**Context**: Cognitive Bus was the first service refactored using this pattern (Feb 5-6, 2026). It serves as the **canonical example** for all future refactorings.

### Before Refactoring (Flat Structure) ❌
```
core/cognitive_bus/
├── event_envelope.py (mixed concerns)
├── event_schema.py (mixed concerns)
├── streams.py (mixed concerns)
├── metrics.py (mixed concerns)
├── redis_client.py (mixed concerns)
├── lexicon.py (mixed concerns)
├── rite_of_validation.py (mixed concerns)
├── base_consumer.py (mixed concerns)
├── listener_adapter.py (mixed concerns)
├── [10+ other files in root]
└── docs/
    ├── IMPLEMENTATION_ROADMAP.md (2,000 lines)
    ├── PHASE_0_REPORT.md (1,000 lines)
    ├── PHASE_4_REPORT.md (800 lines)
    └── [6 fragmented phase reports]
```

**Problems**:
- ❌ **No intuitive organization**: "Where do I find X?" requires reading docs
- ❌ **Mixed concerns**: Transport, events, metrics, governance all in root
- ❌ **Fragmented docs**: 14 separate files, no entry point, overlapping content
- ❌ **Long onboarding**: 4-6 hours to understand architecture
- ❌ **Difficult testing**: Import chains unclear, circular dependencies risk

---

### After Refactoring (Organized Structure) ✅
```
core/cognitive_bus/
├── __init__.py (clean exports, no business logic)
│
├── client/ (future: SDK wrappers)
│   └── __init__.py
│
├── events/ (event models & schemas)
│   ├── __init__.py
│   ├── event_envelope.py (CognitiveEvent, TransportEvent)
│   └── event_schema.py (validation schemas)
│
├── transport/ (communication infrastructure)
│   ├── __init__.py
│   ├── streams.py (StreamBus - Redis Streams interface)
│   └── redis_client.py (connection management)
│
├── monitoring/ (observability)
│   ├── __init__.py
│   ├── metrics.py (Prometheus metrics)
│   └── metrics_server.py (HTTP /metrics endpoint)
│
├── governance/ (validation & compliance)
│   ├── __init__.py
│   └── rite_of_validation.py (Orthodoxy rules)
│
├── utils/ (helpers & config)
│   ├── __init__.py
│   ├── lexicon.py (terminology)
│   └── scroll_of_bonds.json (config)
│
├── philosophy/ (design documentation)
│   ├── Vitruvyan_Bus_Invariants.md (4 Sacred Invariants)
│   ├── Vitruvyan_Epistemic_Charter.md
│   ├── Vitruvyan_Octopus_Mycelium_Architecture.md
│   └── Vitruvyan_Vertical_Specification.md
│
├── listeners/ (business logic - domain-specific)
│   ├── __init__.py (NO centralized imports!)
│   ├── codex_hunters.py (323 lines)
│   ├── babel_gardens.py
│   ├── shadow_traders.py
│   ├── vault_keepers.py
│   ├── mcp.py (388 lines)
│   └── langgraph.py (181 lines)
│
├── consumers/ (patterns & adapters)
│   ├── __init__.py
│   ├── base_consumer.py (abstract base)
│   └── listener_adapter.py (Pub/Sub → Streams)
│
├── plasticity/ (learning system)
│   ├── __init__.py
│   ├── manager.py
│   └── observer.py
│
├── orthodoxy/ (audit & governance)
│   ├── __init__.py
│   └── [validation modules]
│
└── docs/ (unified documentation)
    ├── README.md (entry point, 320 lines)
    ├── COGNITIVE_BUS_GUIDE.md (implementation guide, 988 lines)
    ├── API_REFERENCE.md (API docs, 600 lines)
    ├── ARCHITECTURAL_DECISIONS.md (ADRs, 800 lines)
    └── history/ (archived phase reports)
        ├── IMPLEMENTATION_ROADMAP.md
        ├── PHASE_0_REPORT.md
        └── [6 phase reports]
```

**Improvements**:
- ✅ **Intuitive navigation**: "I need event models" → check `events/`
- ✅ **Logical grouping**: Related modules together (transport, monitoring, governance)
- ✅ **Unified documentation**: 3 core guides + README (2,388 lines total), 45-min onboarding
- ✅ **Clean separation**: Business logic (`listeners/`) separate from infrastructure
- ✅ **Testability**: Import paths clear, no circular dependencies
- ✅ **Professionalism**: Structure comparable to FastAPI, Celery, Prometheus client

---

## 🏛️ The Refactoring Pattern (7 Phases)

### Phase 1: Business Logic Separation
**Goal**: Separate domain-specific logic from deployment/infrastructure code

**Actions**:
1. Identify business logic files currently in `docker/services/`
2. Create `<service>/listeners/` or `<service>/handlers/` directory
3. Move business logic to new directory (preserve git history)
4. Update Docker entrypoints to thin wrappers (<80 lines):
   ```python
   # Before: 300+ lines business logic in docker/services/api_X/main.py
   # After: docker/services/api_X/main.py (thin wrapper)
   from core.<service>.listeners.X import XListener
   
   async def main():
       listener = XListener()
       await listener.start()
   ```

**Example** (Cognitive Bus):
- Moved 6 listener files (2,153 lines) from `docker/services/api_*/streams_listener.py` to `core/cognitive_bus/listeners/`
- Entrypoints now import: `from core.cognitive_bus.listeners.codex_hunters import CodexHuntersCognitiveBusListener`

**Benefits**:
- Business logic can be imported and tested without Docker
- Deployment code stays minimal and focused
- Easier to share logic across services

---

### Phase 2: Directory Organization
**Goal**: Organize flat structure into logical directories

**Recommended Directory Structure**:
```
core/<service>/
├── __init__.py
├── client/ (SDK, wrappers, convenience classes)
├── core/ or engine/ (core algorithms, business logic)
├── models/ or events/ (data models, schemas)
├── transport/ or api/ (communication layer)
├── monitoring/ (metrics, health checks)
├── governance/ (validation, compliance)
├── utils/ (helpers, config)
├── philosophy/ (design docs, principles)
├── [domain-specific directories]
└── docs/ (unified documentation)
```

**Grouping Principles**:
1. **Functional cohesion**: Group by purpose (all transport code together)
2. **Intuitive naming**: `monitoring/` not `metr/`, `transport/` not `io/`
3. **Shallow hierarchy**: Max 2-3 levels deep (avoid `core/X/Y/Z/A/B/...`)
4. **Reserved names**:
   - `client/`: Always for SDK/wrapper classes
   - `docs/`: Always for documentation
   - `philosophy/`: Always for design principles
   - `utils/`: Always for helpers/config

**Actions**:
1. Create logical directories following the pattern
2. Move files from root to appropriate directories
3. Create `__init__.py` in each directory with clean exports
4. Update import paths throughout codebase (batch edit recommended)

**Example** (Cognitive Bus):
- 14 root files → organized into 7 directories
- Batch update: `sed -i 's/from \.\.event_envelope/from ..events.event_envelope/g' **/*.py`

---

### Phase 3: Import Path Cleanup
**Goal**: Fix import errors after file moves

**Common Issues**:
1. **Obsolete relative imports**: `from ..X` after X moved to `subdir/X`
2. **Centralized imports**: `__init__.py` imports all submodules → transitive dependencies
3. **Circular dependencies**: Poor module separation

**Actions**:
1. Search for obsolete patterns:
   ```bash
   grep -rn "from \.\.[module_name]" --include="*.py"
   # Should match new directory structure
   ```

2. Fix import paths:
   ```python
   # Old: from ..event_envelope import X
   # New: from ..events.event_envelope import X
   
   # Old: from ..metrics import Y
   # New: from ..monitoring.metrics import Y
   ```

3. Remove centralized imports in `__init__.py`:
   ```python
   # ❌ BAD: Centralized imports (loads all dependencies)
   from .submodule1 import Class1
   from .submodule2 import Class2
   
   # ✅ GOOD: Only __all__ for documentation
   __all__ = ['Class1', 'Class2']
   # Let consumer import directly:
   # from core.service.submodule1 import Class1
   ```

4. Test imports:
   ```bash
   python3 -c "from core.<service>.module import Class; print('✅ OK')"
   ```

**Example** (Cognitive Bus):
- Fixed 6 imports in 3 files (`consumers/` after file moves)
- Removed centralized imports in `listeners/__init__.py` to avoid transitive dependencies

---

### Phase 4: Documentation Unification
**Goal**: Replace fragmented docs with 3 core guides + README

**Required Files**:
1. **README.md** (Entry Point, 300-400 lines):
   - What is this service?
   - Quick start (5-minute example)
   - Architecture overview (directory map)
   - Links to other guides
   - Common use cases
   - FAQ

2. **<SERVICE>_GUIDE.md** (Implementation Guide, 800-1,200 lines):
   - Installation & setup
   - Core concepts explained
   - API usage examples
   - Integration patterns
   - Configuration reference
   - Best practices
   - Common pitfalls

3. **API_REFERENCE.md** (API Documentation, 500-800 lines):
   - All public classes/functions
   - Parameters, return types, exceptions
   - Code examples for each API
   - Quick reference table

4. **ARCHITECTURAL_DECISIONS.md** (Design Rationale, 600-1,000 lines):
   - Why we chose X over Y
   - Trade-offs explained
   - Alternative approaches considered
   - Evolution timeline
   - Future roadmap

**Optional**:
- **history/**: Archive old phase reports, migration docs
- **philosophy/**: Design principles, paradigms (if applicable)

**Actions**:
1. Audit existing documentation (list all .md files)
2. Identify overlapping/redundant content
3. Extract core information, create 4 unified guides
4. Move old docs to `docs/history/`
5. Update root README to link to new docs

**Metrics**:
- **Before**: 14 fragmented files, 4-6h onboarding
- **After**: 4 core guides, 45-min onboarding
- **Total**: ~2,500-3,500 lines (comprehensive but not overwhelming)

**Example** (Cognitive Bus):
- Consolidated 14 docs → 3 guides + README (2,388 lines)
- Archived 6 phase reports to `docs/history/`
- Added entry point: `docs/README.md`

---

### Phase 5: Testing & Validation
**Goal**: Ensure refactored module works as standalone library

**Test Checklist**:
1. **Import test** (no Docker required):
   ```bash
   python3 -c "from core.<service>.module import Class; print('✅')"
   ```

2. **Structural verification**:
   ```bash
   # All expected directories present
   ls -1 core/<service>/ | grep -E "client|core|models|transport|monitoring|docs"
   
   # No obsolete import patterns
   grep -rn "from \.\.[old_module]" --include="*.py"
   # Expected: 0 matches
   ```

3. **Circular dependency check**:
   ```bash
   # Install madge (Node.js tool, works with Python via AST)
   # Or use: python -m pytest --import-mode=importlib
   python3 -c "import core.<service>; print('No circular imports')"
   ```

4. **Documentation completeness**:
   ```bash
   ls -lh docs/{README.md,*_GUIDE.md,API_REFERENCE.md,ARCHITECTURAL_DECISIONS.md}
   # Expected: 4 files, 2,500-3,500 lines total
   ```

5. **Rebuild dependent services** (if any):
   ```bash
   docker compose build <service>
   docker compose up -d <service>
   docker compose logs <service> --tail=50
   # Expected: No import errors, service starts successfully
   ```

**Success Criteria**:
- ✅ All imports work without Docker
- ✅ No circular dependencies
- ✅ Documentation comprehensive (45-min onboarding)
- ✅ Dependent services rebuild successfully
- ✅ No runtime errors in logs

---

### Phase 6: Git & Repository Sync
**Goal**: Commit changes and migrate to vitruvyan-core (if applicable)

**Actions**:
1. **Commit in vitruvyan** (comprehensive message):
   ```bash
   git add -A
   git commit -m "refactor(<service>): FASE 1-5 - Standalone service pattern
   
   FASE 1: Business logic separation (moved X files, Y lines)
   FASE 2: Directory organization (Z directories)
   FASE 3: Import path cleanup (N files updated)
   FASE 4: Documentation unification (4 core guides)
   FASE 5: Testing & validation (all checks passed)
   
   Result: Professional structure, 45-min onboarding, multi-repo ready
   
   Files changed: [count]
   Lines: [insertions/deletions]
   Docs: [doc names]"
   ```

2. **Copy to vitruvyan-core** (if foundation library):
   ```bash
   cd /home/caravaggio
   cp -r vitruvyan/core/<service> vitruvyan-core/core/
   
   # Verify
   du -sh vitruvyan-core/core/<service>
   cd vitruvyan-core/core/<service> && find . -maxdepth 2 -type d
   ```

3. **Create validation prompt** (for core agent):
   - Document what was refactored
   - Provide validation checklist
   - Include rebuild instructions

4. **Create kernel doc** (if pattern extends to other services):
   - Document pattern used
   - Provide template for future refactorings

5. **Sync git**:
   ```bash
   cd /home/caravaggio/vitruvyan-core
   git add core/<service>/
   git commit -m "feat: Add <service> foundation library (refactored)"
   git push origin main
   ```

---

### Phase 7: Multi-Repo Strategy (Optional)
**Goal**: Update vitruvyan to use core library instead of local copy

**Options**:

**A. PYTHONPATH (Temporary)**:
```bash
# In vitruvyan docker-compose.yml
environment:
  - PYTHONPATH=/home/caravaggio/vitruvyan-core:$PYTHONPATH
```

**B. Editable Install (Development)**:
```bash
# In vitruvyan Dockerfile
RUN pip install -e /path/to/vitruvyan-core
```

**C. Package Install (Production)**:
```bash
# In vitruvyan-core, create setup.py
# Then in vitruvyan:
pip install git+https://github.com/user/vitruvyan-core.git@main
```

**Benefits**:
- Single source of truth (core)
- Easier updates (change once, deploy everywhere)
- Cleaner separation (vitruvyan = application, core = libraries)

---

## 📋 Service-Specific Guidelines

### Neural Engine (`core/logic/neural_engine/`)
**Suggested Structure**:
```
core/logic/neural_engine/
├── __init__.py
├── client/ (convenience wrappers)
├── engine/ (core algorithms)
│   ├── engine_core.py (main ranking engine)
│   ├── factors/ (14 functions A-L + P + Earnings)
│   └── profiles/ (screening profiles)
├── models/ (data models)
│   ├── ticker.py (Ticker class)
│   ├── screener_result.py (ScreenerResult)
│   └── schemas.py (Pydantic schemas)
├── api/ (FastAPI endpoints - if applicable)
│   └── main.py
├── monitoring/ (metrics)
│   └── metrics.py
├── utils/ (helpers)
│   └── config.py
└── docs/
    ├── README.md
    ├── NEURAL_ENGINE_GUIDE.md
    ├── API_REFERENCE.md
    └── ARCHITECTURAL_DECISIONS.md
```

**Business Logic**: `engine/engine_core.py` (1,200+ lines) - keep as core, but split `factors/` for readability

---

### LangGraph (`core/langgraph/`)
**Suggested Structure**:
```
core/langgraph/
├── __init__.py
├── client/ (graph builder helpers)
├── nodes/ (LangGraph nodes)
│   ├── intent_detection_node.py
│   ├── sentiment_node.py
│   ├── [15 other nodes]
├── workflows/ (composite workflows)
│   ├── graph_flow.py (main orchestration)
│   └── subgraphs/
├── models/ (state schemas)
│   ├── graph_state.py
│   └── node_schemas.py
├── api/ (FastAPI wrapper)
│   └── main.py
├── monitoring/ (metrics)
└── docs/
    ├── README.md
    ├── LANGGRAPH_GUIDE.md
    ├── API_REFERENCE.md
    └── ARCHITECTURAL_DECISIONS.md
```

**Business Logic**: `nodes/` (14+ files) - already well organized, just add docs

---

### Codex Hunters (`core/codex_hunters/`)
**Suggested Structure**:
```
core/codex_hunters/
├── __init__.py
├── client/ (convenience classes)
├── hunters/ (data collection logic)
│   ├── event_hunter.py
│   ├── tracker.py (Reddit tracker)
│   ├── restorer.py (Qdrant)
│   └── binder.py (PostgreSQL)
├── expeditions/ (scheduled hunts)
│   └── scheduler.py
├── models/ (data models)
│   ├── codex_event.py
│   └── schemas.py
├── api/ (FastAPI wrapper)
│   └── main.py
├── monitoring/ (metrics)
└── docs/
    ├── README.md
    ├── CODEX_HUNTERS_GUIDE.md
    ├── API_REFERENCE.md
    └── ARCHITECTURAL_DECISIONS.md
```

**Business Logic**: `hunters/` (4 files) - already separated, just add directory structure

---

### Leo (Agents) (`core/leo/`)
**Suggested Structure**:
```
core/leo/
├── __init__.py
├── client/ (agent factory)
├── agents/ (individual agents)
│   ├── postgres_agent.py (MANDATORY: all PostgreSQL access)
│   ├── qdrant_agent.py (MANDATORY: all Qdrant access)
│   ├── redis_agent.py
│   └── [other agents]
├── patterns/ (common patterns)
│   ├── base_agent.py
│   └── memory_patterns.py
├── utils/ (helpers)
└── docs/
    ├── README.md
    ├── LEO_GUIDE.md (agent system explanation)
    ├── API_REFERENCE.md
    └── ARCHITECTURAL_DECISIONS.md
```

**Critical**: PostgresAgent and QdrantAgent are **MANDATORY interfaces** - all services MUST use them (no direct psycopg2/qdrant_client calls)

---

## 🚨 Common Pitfalls & Solutions

### Pitfall 1: Circular Dependencies
**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`
**Cause**: Module A imports B, B imports A
**Solution**: 
- Extract shared code to `utils/` or `models/`
- Use dependency injection instead of direct imports
- Lazy imports (import inside function, not top-level)

---

### Pitfall 2: Transitive Dependencies
**Symptom**: ServiceA needs DependencyX for ServiceB's code it doesn't use
**Cause**: Centralized imports in `__init__.py` load all dependencies
**Solution**: 
- Remove centralized imports
- Each consumer imports directly what it needs
- Use `__all__` for documentation only

**Example**:
```python
# ❌ BAD: listeners/__init__.py
from .codex_hunters import CodexHuntersCognitiveBusListener  # Loads ALL dependencies
from .babel_gardens import BabelGardensCognitiveBusListener  # aiohttp, etc.

# ✅ GOOD: listeners/__init__.py
__all__ = ['CodexHuntersCognitiveBusListener', 'BabelGardensCognitiveBusListener']
# Each service imports directly:
# from core.service.listeners.codex_hunters import CodexHuntersCognitiveBusListener
```

---

### Pitfall 3: Import Path Confusion
**Symptom**: Imports work locally but fail in Docker
**Cause**: PYTHONPATH differs, relative vs absolute imports
**Solution**:
- Use absolute imports from project root: `from core.service.module import X`
- Avoid relative imports beyond 1 level: `from ..module import X` OK, `from ../../X` BAD
- Test imports in clean environment (Docker)

---

### Pitfall 4: Documentation Overload
**Symptom**: 20+ documentation files, nobody reads them
**Cause**: Incremental additions without consolidation
**Solution**:
- **3 core guides + README** (2,500-3,500 lines total)
- Archive old docs to `history/`
- README as entry point (links to other guides)
- Target: 45-min onboarding for new developer

---

### Pitfall 5: Shallow Refactoring
**Symptom**: Directory structure changed but code quality unchanged
**Cause**: Moving files without improving design
**Solution**:
- Use refactoring as opportunity to improve code
- Split large files (>1,000 lines) into logical modules
- Extract reusable patterns
- Add type hints, docstrings
- Update tests

---

## 🎯 Success Metrics

**Before Refactoring**:
- ❌ Flat structure (10-20 files in root)
- ❌ Fragmented docs (10+ files, overlapping content)
- ❌ Long onboarding (4-6 hours)
- ❌ Difficult testing (Docker required)
- ❌ Mixed concerns (business logic in deployment code)

**After Refactoring**:
- ✅ Organized structure (5-10 logical directories)
- ✅ Unified docs (3 core guides + README, 2,500-3,500 lines)
- ✅ Short onboarding (45 minutes)
- ✅ Easy testing (import without Docker)
- ✅ Clean separation (business logic separate from deployment)

**Quantitative Targets**:
- Directory depth: Max 2-3 levels
- Files per directory: 3-10 (not 50)
- Documentation: 4 core files (README + 3 guides)
- Onboarding time: 45-60 minutes (measured from "git clone" to "first contribution")
- Import test: `python3 -c "from core.service import X"` should work

---

## 📚 References

**Inspiration** (Industry-Standard Open Source):
- **FastAPI**: `fastapi/` structure (routing, dependencies, security, etc.)
- **Celery**: `celery/` structure (app, worker, backends, utils)
- **SQLAlchemy**: `sqlalchemy/` structure (engine, orm, sql, ext)
- **Pytest**: `pytest/` structure (_pytest/ for internals, public API at root)

**Vitruvyan Examples**:
- **Cognitive Bus** (Feb 5-6, 2026): Full refactoring FASE 1-5
  - Docs: `core/cognitive_bus/docs/README.md`
  - Validation: `vitruvyan-core/COGNITIVE_BUS_REFACTORING_VALIDATION_PROMPT.md`
  - Debug summary: `vitruvyan/LISTENER_REFACTORING_DEBUG_SUMMARY_FEB6.md`

**Further Reading**:
- Clean Architecture (Robert C. Martin)
- Domain-Driven Design (Eric Evans)
- The Pragmatic Programmer (Hunt & Thomas)

---

## ✅ Refactoring Checklist

Use this checklist for each service refactoring:

### Planning Phase
- [ ] Identify service to refactor
- [ ] List all files (Python, docs, configs)
- [ ] Identify business logic vs deployment code
- [ ] Plan directory structure (5-10 directories)
- [ ] Estimate effort (4-8 hours per service)

### FASE 1: Business Logic Separation
- [ ] Create `<service>/listeners/` or `<service>/handlers/`
- [ ] Move business logic files (preserve git history)
- [ ] Update Docker entrypoints to thin wrappers
- [ ] Test: Business logic importable without Docker

### FASE 2: Directory Organization
- [ ] Create logical directories (client, core, models, transport, monitoring, utils, docs)
- [ ] Move files from root to directories
- [ ] Create `__init__.py` in each directory
- [ ] Test: Directory structure intuitive

### FASE 3: Import Path Cleanup
- [ ] Search for obsolete import patterns
- [ ] Batch update import paths
- [ ] Remove centralized imports in `__init__.py`
- [ ] Test: `python3 -c "from core.service.module import X"`

### FASE 4: Documentation Unification
- [ ] Create README.md (entry point)
- [ ] Create <SERVICE>_GUIDE.md (implementation)
- [ ] Create API_REFERENCE.md (API docs)
- [ ] Create ARCHITECTURAL_DECISIONS.md (design rationale)
- [ ] Archive old docs to `docs/history/`
- [ ] Test: New developer onboards in 45 minutes

### FASE 5: Testing & Validation
- [ ] Import test (no Docker)
- [ ] Structural verification
- [ ] Circular dependency check
- [ ] Documentation completeness check
- [ ] Rebuild dependent services
- [ ] Test: All checks pass

### FASE 6: Git & Repository Sync
- [ ] Commit in vitruvyan (comprehensive message)
- [ ] Copy to vitruvyan-core (if foundation library)
- [ ] Create validation prompt (for core agent)
- [ ] Sync git (push to remote)

### FASE 7: Multi-Repo Strategy (Optional)
- [ ] Update vitruvyan to use core library
- [ ] Test integration
- [ ] Update deployment scripts

### Post-Refactoring
- [ ] Monitor logs (48-72h)
- [ ] Collect feedback from team
- [ ] Update this kernel doc if patterns evolve

---

## 🎊 Conclusion

**This pattern transforms services from "deployment-coupled code" to "standalone foundation libraries".**

**Key Principles**:
1. **Intuitive structure** (self-documenting directory names)
2. **Clean separation** (business logic vs deployment)
3. **Unified documentation** (3 guides + README)
4. **Testability** (import without Docker)
5. **Professional quality** (comparable to FastAPI, Celery)

**When to apply**:
- Service has 10+ files in root directory
- Documentation is fragmented (5+ files)
- Onboarding takes >2 hours
- Testing requires Docker
- Business logic mixed with deployment code

**Expected ROI**:
- **Onboarding**: 4-6h → 45 min (80% reduction)
- **Testing**: Docker required → `python3 -c "import X"` (instant feedback)
- **Maintenance**: "Where is X?" requires reading docs → "Check `<directory>/`" (obvious)
- **Scalability**: Multi-repo strategy enabled (core as foundation)

---

**Status**: 🟢 CANONICAL - Use this pattern for all future refactorings  
**Version**: 1.0  
**Last Updated**: February 6, 2026  
**Maintainer**: Vitruvyan Core Team  
**Questions**: See `core/cognitive_bus/` for reference implementation
