# Cognitive Bus Refactoring - Validation & Rebuild Prompt
**Date**: February 6, 2026  
**Status**: ✅ Refactoring FASE 1+2+3 completato in vitruvyan, migrato in core  
**Target**: AI Agent in vitruvyan-core repository

---

## 🎯 Context & Mission

**What Happened**:
We completed a major architectural refactoring of the Cognitive Bus module following the "app standalone" pattern (inspired by FastAPI, Celery, SQLAlchemy). The refactored code has been successfully tested in `vitruvyan` repository (7/7 containers operational) and is now being migrated to `vitruvyan-core` as a foundation library.

**Your Mission**:
1. **Validate** the refactored cognitive_bus structure in `core/cognitive_bus/`
2. **Verify** architectural integrity (no broken imports, proper separation)
3. **Test** the module as standalone library
4. **Rebuild** any dependent services if necessary
5. **Document** findings and confirm production readiness

---

## 📁 What Was Refactored (FASE 1+2+3)

### FASE 1: Listener Separation (Feb 5, 2026)
**Change**: Business logic moved from `docker/services/*/streams_listener.py` to `core/cognitive_bus/listeners/`

**Files Migrated** (2,153 lines total):
```
core/cognitive_bus/listeners/
├── codex_hunters.py (323 lines) - Data collection expeditions
├── babel_gardens.py - Multilingual sentiment/emotion analysis  
├── shadow_traders.py - Shadow trading execution
├── vault_keepers.py - Data archival and versioning
├── mcp.py (388 lines) - Model Context Protocol bridge
└── langgraph.py (181 lines) - Portfolio monitoring workflows
```

**Entrypoints** (now thin wrappers <80 lines):
```
docker/services/api_*/streams_listener.py
- Import listener from core.cognitive_bus.listeners.*
- Wrap with ListenerAdapter (for legacy listeners)
- Start async loop
```

**Rationale**: 
- Separation of concerns (deployment vs code)
- Easier testing (import classes directly)
- Multi-repo strategy enabled (core as library)

---

### FASE 2: Directory Organization (Feb 5, 2026)
**Change**: Flat structure (14 root files) → Logical grouping (7 directories)

**New Structure**:
```
core/cognitive_bus/
├── __init__.py (main package, clean exports)
├── client/ (reserved for future API wrappers)
├── events/
│   ├── event_envelope.py (CognitiveEvent, TransportEvent)
│   └── event_schema.py (event validation schemas)
├── transport/
│   ├── streams.py (StreamBus - Redis Streams interface)
│   └── redis_client.py (Redis connection management)
├── monitoring/
│   ├── metrics.py (Prometheus metrics - 18 metrics)
│   └── metrics_server.py (HTTP metrics endpoint)
├── governance/
│   └── rite_of_validation.py (Orthodoxy validation rules)
├── utils/
│   ├── lexicon.py (terminology & constants)
│   └── scroll_of_bonds.json (channel configurations)
├── philosophy/
│   ├── Vitruvyan_Bus_Invariants.md (4 Sacred Invariants)
│   ├── Vitruvyan_Epistemic_Charter.md (design principles)
│   ├── Vitruvyan_Octopus_Mycelium_Architecture.md (bio-inspired foundation)
│   └── Vitruvyan_Vertical_Specification.md (technical spec)
├── listeners/ (business logic - FASE 1)
│   ├── codex_hunters.py
│   ├── babel_gardens.py
│   ├── shadow_traders.py
│   ├── vault_keepers.py
│   ├── mcp.py
│   └── langgraph.py
├── consumers/ (consumer patterns & adapters)
│   ├── base_consumer.py (abstract base class)
│   ├── listener_adapter.py (legacy Pub/Sub → Streams adapter)
│   └── [other consumer patterns]
├── plasticity/ (bounded learning system)
│   ├── manager.py (parameter adaptation)
│   └── observer.py (anomaly detection)
├── orthodoxy/ (governance & audit)
│   └── [validation & compliance modules]
└── docs/ (comprehensive documentation)
    ├── README.md (entry point)
    ├── COGNITIVE_BUS_GUIDE.md (988 lines implementation guide)
    ├── API_REFERENCE.md (600 lines API docs)
    ├── ARCHITECTURAL_DECISIONS.md (800 lines ADRs)
    └── history/ (6 phase reports archived)
```

**Benefits**:
- Intuitive navigation ("where do I find X?" is obvious)
- Logical grouping (related modules together)
- Professional structure (comparable to FastAPI, Celery)
- Scalability (easy to add new modules in proper directory)

---

### FASE 3: Import Cleanup (Feb 6, 2026)
**Change**: Fixed import errors after file moves & listener separation

**Issues Fixed**:
1. **Transitive Dependency Problem**:
   - `listeners/__init__.py` had centralized imports → loaded ALL dependencies
   - CodexHunters container imported babel_gardens dependencies (aiohttp) unnecessarily
   - **Fix**: Removed centralized imports, each entrypoint imports directly

2. **Obsolete Import Paths**:
   - After FASE 2 file moves, `consumers/` still used old paths
   - `from ..event_envelope` → should be `from ..events.event_envelope`
   - **Fix**: Batch updated 6 imports in 3 files (consumers/__init__.py, base_consumer.py, listener_adapter.py)

**Files Changed** (6 files):
- `core/cognitive_bus/listeners/__init__.py` - Removed centralized imports
- `core/cognitive_bus/consumers/__init__.py` - Updated import paths
- `core/cognitive_bus/consumers/base_consumer.py` - Updated import paths (2 locations)
- `core/cognitive_bus/consumers/listener_adapter.py` - Updated import paths (2 locations)

**Result**: 7/7 containers operational in vitruvyan (codex_hunters, babel_gardens, shadow_traders, vault_keepers, mcp, memory_orders, api_graph)

---

## 🔍 Your Validation Checklist

### 1. Structural Integrity ✅ (Expected: PASS)
```bash
# Verify all 13 directories present
cd /home/caravaggio/vitruvyan-core/core/cognitive_bus
find . -maxdepth 1 -type d | wc -l
# Expected: 14 (13 + root)

# Verify key files exist
ls -1 events/event_envelope.py transport/streams.py monitoring/metrics.py listeners/*.py
# Expected: All files present

# Verify listeners directory structure
ls -1 listeners/
# Expected: 6 listener files + __init__.py
```

### 2. Import Path Verification ✅ (Expected: PASS)
```bash
# Search for obsolete import patterns (should find NONE)
cd /home/caravaggio/vitruvyan-core/core/cognitive_bus
grep -rn "from \.\\.event_envelope\|from \.\\.event_schema\|from \.\\.streams\|from \.\\.metrics" --include="*.py"
# Expected: Empty result (no matches)

# Verify new import patterns present
grep -rn "from \.\.events\.event_envelope\|from \.\.transport\.streams\|from \.\.monitoring\.metrics" --include="*.py" | head -10
# Expected: Multiple matches with correct paths

# Verify no centralized listener imports
grep -A5 "from \.codex_hunters\|from \.babel_gardens" listeners/__init__.py
# Expected: No matches (only __all__ declaration)
```

### 3. Python Import Test (CRITICAL)
```bash
# Test that module can be imported without errors
cd /home/caravaggio/vitruvyan-core
python3 -c "from core.cognitive_bus.transport.streams import StreamBus; print('✅ StreamBus import OK')"
python3 -c "from core.cognitive_bus.events.event_envelope import CognitiveEvent; print('✅ CognitiveEvent import OK')"
python3 -c "from core.cognitive_bus.monitoring.metrics import record_listener_consumption; print('✅ Metrics import OK')"

# Test listener imports (should NOT trigger transitive dependencies)
python3 -c "from core.cognitive_bus.listeners.codex_hunters import CodexHuntersCognitiveBusListener; print('✅ CodexHunters listener import OK')"
# Expected: Should NOT require aiohttp or babel_gardens dependencies
```

### 4. Documentation Completeness Check
```bash
# Verify key documentation files
cd /home/caravaggio/vitruvyan-core/core/cognitive_bus/docs
ls -lh README.md COGNITIVE_BUS_GUIDE.md API_REFERENCE.md ARCHITECTURAL_DECISIONS.md
# Expected: 4 files, total ~2,388 lines

# Verify history archived
ls -1 docs/history/
# Expected: 6-9 phase reports (IMPLEMENTATION_ROADMAP.md, PHASE_*.md, etc.)

# Verify philosophy docs
ls -1 philosophy/
# Expected: 4 .md files (Invariants, Charter, Octopus_Mycelium, Vertical_Spec)
```

### 5. File Count & Size Verification
```bash
# Count Python files
find . -name "*.py" -type f | wc -l
# Expected: 30-50 .py files

# Count total lines of code
find . -name "*.py" -type f -exec wc -l {} + | tail -1
# Expected: 8,000-12,000 lines total

# Verify no __pycache__ in git
git ls-files | grep __pycache__
# Expected: Empty (no cached files in git)

# Verify size reasonable
du -sh .
# Expected: ~1.5-2.0 MB
```

---

## 🛠️ Rebuild Instructions (If Needed)

**Scenario 1: vitruvyan-core as Standalone Library** (Recommended)
```bash
# No rebuild needed - this is a library, not a deployed service
# Dependent projects (vitruvyan) will import from here

# Verify library structure
cd /home/caravaggio/vitruvyan-core
python3 -c "import sys; sys.path.insert(0, '.'); from core.cognitive_bus.transport.streams import StreamBus; print('Library import OK')"
```

**Scenario 2: If vitruvyan-core Has Services Using Cognitive Bus**
```bash
# Check if any service depends on cognitive_bus
cd /home/caravaggio/vitruvyan-core
grep -r "from core.cognitive_bus\|import cognitive_bus" services/ infrastructure/ --include="*.py"

# If matches found, rebuild those services
# Example:
docker compose build <service_name>
docker compose up -d <service_name>
docker compose logs <service_name> --tail=50
```

**Scenario 3: Integration Test with vitruvyan**
```bash
# Update vitruvyan to use core library
cd /home/caravaggio/vitruvyan
# Option A: Add vitruvyan-core to PYTHONPATH
export PYTHONPATH="/home/caravaggio/vitruvyan-core:$PYTHONPATH"

# Option B: Install as editable package (future)
# cd /home/caravaggio/vitruvyan-core
# pip install -e .

# Test integration
docker compose restart vitruvyan_codex_hunters_listener
docker compose logs vitruvyan_codex_hunters_listener --tail=30
# Expected: No import errors, listener starts successfully
```

---

## 📋 Expected Findings Report Template

After completing validation, document your findings:

```markdown
# Cognitive Bus Refactoring Validation Report
**Date**: [Your validation date]
**Validator**: [AI Agent name/version]

## Validation Results

### 1. Structural Integrity
- [ ] All 13 directories present
- [ ] All key files exist (events/, transport/, monitoring/, listeners/)
- [ ] No missing dependencies

**Status**: ✅ PASS / ⚠️ WARNINGS / ❌ FAIL
**Notes**: [Your observations]

### 2. Import Path Verification
- [ ] No obsolete import patterns found
- [ ] New import patterns correct
- [ ] No centralized listener imports

**Status**: ✅ PASS / ⚠️ WARNINGS / ❌ FAIL
**Notes**: [Your observations]

### 3. Python Import Test
- [ ] StreamBus import OK
- [ ] CognitiveEvent import OK
- [ ] Metrics import OK
- [ ] Listener imports work without transitive dependencies

**Status**: ✅ PASS / ⚠️ WARNINGS / ❌ FAIL
**Errors**: [Any import errors encountered]

### 4. Documentation Completeness
- [ ] README.md present and comprehensive
- [ ] COGNITIVE_BUS_GUIDE.md present (988 lines)
- [ ] API_REFERENCE.md present (600 lines)
- [ ] ARCHITECTURAL_DECISIONS.md present (800 lines)
- [ ] History archived properly

**Status**: ✅ PASS / ⚠️ WARNINGS / ❌ FAIL
**Notes**: [Your observations]

### 5. File Count & Size
- Python files: [count]
- Total lines: [count]
- Size: [MB]
- __pycache__ in git: [yes/no]

**Status**: ✅ PASS / ⚠️ WARNINGS / ❌ FAIL

## Rebuild Actions Taken
[List any rebuilds performed]

## Issues Found & Fixes Applied
[Document any issues and how you fixed them]

## Production Readiness Assessment
- [ ] Structure: Professional & intuitive
- [ ] Imports: All working, no circular dependencies
- [ ] Documentation: Comprehensive (2,388 lines)
- [ ] Testing: Successfully tested in vitruvyan (7/7 containers)
- [ ] Multi-repo ready: Can be used as foundation library

**Overall Status**: ✅ PRODUCTION READY / ⚠️ NEEDS FIXES / ❌ NOT READY

**Recommendation**: [Your recommendation for next steps]
```

---

## 🎯 Success Criteria

**Validation PASSES if**:
1. ✅ All structural checks pass (13 directories, all key files present)
2. ✅ No obsolete import patterns found
3. ✅ Python imports work without errors
4. ✅ Documentation complete and up-to-date
5. ✅ No __pycache__ files in git
6. ✅ Size reasonable (~1.5-2MB)

**PRODUCTION READY if**:
- All validation checks pass
- No critical import errors
- Documentation comprehensive
- Successfully tested in vitruvyan (already confirmed)

---

## 📚 Reference Documentation

**In This Repo** (vitruvyan-core):
- `core/cognitive_bus/docs/README.md` - Start here (entry point)
- `core/cognitive_bus/docs/COGNITIVE_BUS_GUIDE.md` - Implementation guide (988 lines)
- `core/cognitive_bus/docs/API_REFERENCE.md` - API documentation (600 lines)
- `core/cognitive_bus/docs/ARCHITECTURAL_DECISIONS.md` - Design rationale (800 lines)
- `STANDALONE_SERVICES_REFACTORING_PATTERN.md` - Future refactoring guide (sibling doc)

**In vitruvyan Repo** (origin):
- `LISTENER_REFACTORING_DEBUG_SUMMARY_FEB6.md` - FASE 3 debugging report
- `COGNITIVE_BUS_DOCUMENTATION_RESTRUCTURING_COMPLETE_FEB5_2026.md` - Documentation overhaul
- Git commit `164911c1` - "fix(cognitive_bus): FASE 3 - Import cleanup..."

**Philosophy Docs** (vitruvyan-core):
- `core/cognitive_bus/philosophy/Vitruvyan_Bus_Invariants.md` - 4 Sacred Invariants
- `core/cognitive_bus/philosophy/Vitruvyan_Octopus_Mycelium_Architecture.md` - Bio-inspired design

---

## 🚨 Common Issues & Solutions

### Issue 1: ModuleNotFoundError after import
**Symptom**: `ModuleNotFoundError: No module named 'core.cognitive_bus.event_envelope'`
**Cause**: Obsolete import path (should be `events.event_envelope`)
**Solution**: Check `consumers/` files, update import paths as per FASE 2

### Issue 2: Circular import dependency
**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`
**Cause**: Centralized imports in `__init__.py` files
**Solution**: Verify `listeners/__init__.py` has NO centralized imports (only `__all__`)

### Issue 3: Dependencies missing
**Symptom**: `ModuleNotFoundError: No module named 'aiohttp'` or similar
**Cause**: Transitive dependency from another listener
**Solution**: Each service should import only ITS listener directly, not via `listeners/__init__.py`

---

## ✅ Final Checklist

Before marking this validation complete:

- [ ] Ran all structural integrity checks
- [ ] Verified import paths correct
- [ ] Tested Python imports (no errors)
- [ ] Confirmed documentation complete
- [ ] No __pycache__ in git
- [ ] Documented findings in report
- [ ] Identified any rebuild needs
- [ ] Recommendation provided

**Your Decision**: [APPROVE for production / REQUEST FIXES / REJECT]

---

**Status**: Awaiting your validation  
**Priority**: HIGH (foundation library for multi-repo strategy)  
**Expected Duration**: 30-60 minutes  
**Contact**: Original developer if questions arise
