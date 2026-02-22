# Vitruvyan Edge Extraction Plan
> **Last updated**: Feb 22, 2026 18:10 UTC

## 🎯 Executive Summary

**Obiettivo**: Creare `vitruvyan_edge/` come package di primo livello al pari di `vitruvyan_core/`, iniziando con l'estrazione di Oculus Prime da `infrastructure/edge/`. Il package è progettato come **contenitore multi-modulo**: Oculus Prime è il primo modulo, altri seguiranno (DSE-CPS, stream intake, ecc.).

**Motivazione architetturale**: 
- `vitruvyan_core/` = OS autonomo (kernel epistemico)
- `vitruvyan_edge/` = Package contenitore multi-modulo (pluggable ingestion/acquisition layer)
  - `oculus_prime/` = Gateway multimodale (documents, images, audio, video, CAD, GIS)
  - `dse_cps/` = *(futuro)* DSE-CPS engine integration
  - Altri moduli pluggabili nel core seguendo lo stesso pattern
- `infrastructure/` = Deployment assets ONLY (no business logic)

**Scope**: 32 file, 55+ modifiche, 9 fasi sequenziali, ~45 minuti esecuzione.

---

## 📊 Impact Assessment (Pre-Migration Analysis)

### Test Coverage Baseline
- **Test suite**: 7/8 passed (87.5% success rate)
- **Total LOC**: 448 lines (4 test files)
- **Files**:
  - ✅ `test_document_ingest_integration.py` (89 LOC)
  - ✅ `test_event_emitter_migration.py` (105 LOC)
  - ✅ `test_persistence.py` (181 LOC)
  - ⚠️ `test_routes.py` (73 LOC) - 1 test skipped (missing `multipart` dependency)

### Impact Analysis by Component

| Component | Files | Changes | Priority | Risk |
|-----------|-------|---------|----------|------|
| **Python imports (internal)** | 7 `.py` | 7 occurrences | 🔴 Critical | High |
| **Python imports (service adapters)** | 2 `.py` | 8 occurrences | 🔴 Critical | High |
| **Python imports (tests)** | 2 `.py` | 2 occurrences | 🔴 Critical | Medium |
| **Dockerfile** | 1 | 1 line | 🔴 Critical | High |
| **MkDocs runtime (compose + Dockerfile)** | 2 | 2 lines | 🔴 Critical | High |
| **Non-Python assets** | 4 (JSON/SQL) | Copy only | 🟡 Important | Low |
| **Documentation** | 11 `.md` | ~25 occurrences | 🟡 Important | Low |
| **MkDocs config** | 2 `.yml` | 2 nav entries | 🟡 Important | Medium |
| **pyproject.toml** | 1 | 2 lines | 🟡 Important | Medium |
| **TOTALE** | **32** | **~55** | - | - |

### Complete File Inventory (Verified by Audit)

#### Python files to COPY from `infrastructure/edge/oculus_prime/` (12 files):
```
core/agents/api_intake.py        (960 LOC) — NO import of infrastructure.edge (uses try/except vitruvyan_core)
core/agents/audio_intake.py      — imports infrastructure.edge.oculus_prime.core.guardrails
core/agents/cad_intake.py        — imports infrastructure.edge.oculus_prime.core.guardrails
core/agents/document_intake.py   — imports infrastructure.edge.oculus_prime.core.guardrails
core/agents/geo_intake.py        — imports infrastructure.edge.oculus_prime.core.guardrails
core/agents/image_intake.py      — imports infrastructure.edge.oculus_prime.core.guardrails
core/agents/landscape_intake.py  — imports infrastructure.edge.oculus_prime.core.guardrails
core/agents/video_stream_intake.py — imports infrastructure.edge.oculus_prime.core.guardrails
core/event_emitter.py            — imports vitruvyan_core (NOT infrastructure.edge) ✅
core/guardrails.py               — pure Python, no edge imports ✅
dse_bridge/__init__.py           — relative import only (.main) ✅
dse_bridge/main.py               — imports vitruvyan_core (NOT infrastructure.edge) ✅
```

#### Non-Python assets to COPY (4 files):
```
core/event_evidence_created_v1.json
core/event_evidence_created_v2.json
core/evidence_pack_schema_v1.json
core/schema.sql
```

#### Markdown files to COPY and UPDATE (4 files within edge):
```
core/README.md                        — 4 code examples with infrastructure.edge + 1 path ref
core/COMPLIANCE_CHECKLIST.md          — relative refs to schema.sql/JSON (OK as-is)
core/INTAKE_CODEX_BOUNDARY_CONTRACT.md — relative refs to schema.sql/JSON (OK as-is)
dse_bridge/README.md                  — 1 path reference
```

#### External files to UPDATE (not copy):
```
services/api_edge_oculus_prime/adapters/runtime.py          — 1 import
services/api_edge_oculus_prime/adapters/oculus_prime_adapter.py — 7 imports
services/api_edge_oculus_prime/tests/test_document_ingest_integration.py — 1 import
services/api_edge_oculus_prime/tests/test_event_emitter_migration.py — 1 import
services/api_edge_oculus_prime/Dockerfile                   — 1 COPY line
services/api_edge_oculus_prime/README.md                    — 1 path reference
infrastructure/edge/README.md                               — rewrite (deprecation)
infrastructure/docker/mkdocs/mkdocs.yml                     — 1 nav entry
infrastructure/docker/mkdocs/backups/.../mkdocs.yml         — 1 nav entry (backup)
infrastructure/docker/docker-compose.yml                     — 1 mount line (mkdocs service)
infrastructure/docker/mkdocs/Dockerfile                      — 1 symlink line (docs_root visibility)
docs/infrastructure/EDGE_OCULUS_PRIME_INFRA.md              — 3 path references
docs/planning/INTAKE_EDGE_REFACTOR_INTEGRATION_PLAN_FEB16_2026.md — 1 path reference
docs/planning/ANDROID_OCULUS_PRIME_APP_ROADMAP_FEB17_2026.md — 4 path references
docs/knowledge_base/oculus_prime/intake_flow_graph.md       — 2 path references
pyproject.toml                                              — 2 lines
```

**Nota**: `docs/planning/EDGE_INTEROPERABILITY_CONTRACT_DRAFT_V0.md` resta invariato perché referenzia `infrastructure/edge/` in modo architetturale (non `.../oculus_prime`).

### __init__.py Status (CRITICAL FINDING)

**Current state**: Only `infrastructure/edge/oculus_prime/dse_bridge/__init__.py` exists.
No `__init__.py` in:
- `infrastructure/`
- `infrastructure/edge/`
- `infrastructure/edge/oculus_prime/`
- `infrastructure/edge/oculus_prime/core/`
- `infrastructure/edge/oculus_prime/core/agents/`

**How it works now**: Python 3.3+ implicit **namespace packages** (PEP 420). Import resolution works without `__init__.py` when the directory tree exists on `sys.path`.

**For `vitruvyan_edge/`**: We MUST create `__init__.py` at every level to ensure proper **regular package** behavior (not namespace packages). This guarantees:
- Consistent import behavior across Python tooling
- Proper `pip install -e .` discovery by setuptools
- No ambiguity with namespace packages

### Regression Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Import errors runtime** | 🔴 High | 🔴 BLOCKER | Pre-test imports after each batch |
| **Docker build failures** | 🟡 Medium | 🔴 BLOCKER | Incremental rebuild + PYTHONPATH verification |
| **Test failures** | 🟡 Medium | 🟠 High | Execute test suite BEFORE and AFTER migration |
| **Service downtime** | 🟡 Medium | 🟠 High | Migration on dedicated branch, atomic deploy |
| **Namespace vs regular package** | 🟡 Medium | 🟠 High | Create __init__.py at ALL levels in vitruvyan_edge |
| **Missing non-Python assets** | 🟡 Medium | 🟠 High | Copy JSON schemas + SQL alongside Python files |
| **Documentation drift** | 🟢 Low | 🟢 Low | Final review pre-merge |
| **MkDocs KB broken links** | 🟢 Low | 🟡 Medium | Test navigation post-rebuild |
| **MkDocs runtime path non visibile** | 🟡 Medium | 🔴 BLOCKER | Add mount in compose + symlink in mkdocs Dockerfile |
| **MkDocs backup stale** | 🟢 Low | 🟢 Low | Update backup mkdocs.yml too |

---

## 📐 Target Architecture

```
/home/vitruvyan/vitruvyan-core/
├── vitruvyan_core/          # OS autonomo (invariato)
│   ├── core/
│   ├── contracts/
│   └── domains/
│
├── vitruvyan_edge/          # 🆕 Package contenitore multi-modulo (nuovo)
│   ├── __init__.py          # Package root (version, module registry)
│   ├── README.md
│   ├── oculus_prime/        # MODULO 1: Gateway multimodale (questa migrazione)
│   │   ├── __init__.py
│   │   ├── README.md        # (spostato da infrastructure/edge/oculus_prime/)
│   │   ├── core/            # (spostato da infrastructure/edge/oculus_prime/core/)
│   │   │   ├── __init__.py
│   │   │   ├── agents/      # 8 intake agents (document, image, audio, video, CAD, geo, landscape, api)
│   │   │   │   └── __init__.py
│   │   │   ├── event_emitter.py
│   │   │   ├── guardrails.py
│   │   │   ├── schema.sql                      # PostgreSQL append-only schema
│   │   │   ├── event_evidence_created_v1.json   # Legacy event schema
│   │   │   ├── event_evidence_created_v2.json   # Canonical event schema
│   │   │   ├── evidence_pack_schema_v1.json     # Evidence Pack JSON schema
│   │   │   ├── COMPLIANCE_CHECKLIST.md          # Compliance verification
│   │   │   ├── INTAKE_CODEX_BOUNDARY_CONTRACT.md # Contract with Codex Hunters
│   │   │   └── README.md
│   │   └── dse_bridge/      # (spostato da infrastructure/edge/oculus_prime/dse_bridge/)
│   │       ├── __init__.py  # (già esistente nell'originale)
│   │       ├── main.py
│   │       └── README.md
│   ├── contracts/           # (futuro: contratti edge-specific)
│   │   └── __init__.py
│   ├── dse_cps/             # (futuro: MODULO 2 — DSE-CPS engine)
│   │   └── ...
│   └── ...                  # (futuro: altri moduli edge pluggabili)
│
├── infrastructure/edge/     # 🔄 Deprecato → archivio deployment notes
│   └── README.md            # (aggiornato: puntatore a vitruvyan_edge/)
│
└── services/
    └── api_edge_oculus_prime/  # (imports aggiornati)
        ├── adapters/
        │   ├── runtime.py       # 1 import update
        │   └── oculus_prime_adapter.py  # 7 import updates
        └── tests/               # 2 import updates
```

### Dipendenze cross-package (vitruvyan_edge → vitruvyan_core)

Il codice edge importa dal core in 3 file (queste dipendenze NON cambiano con la migrazione):

| File edge | Import da vitruvyan_core |
|-----------|--------------------------|
| `core/event_emitter.py` | `from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus` |
| `core/agents/api_intake.py` | `from vitruvyan_core.core.agents.postgres_agent import PostgresAgent` (try/except) |
| `dse_bridge/main.py` | `from vitruvyan_core.core.agents.postgres_agent import PostgresAgent`, `StreamBus`, `IntakeDSEBridge` |

**Nota**: Questi import usano già `vitruvyan_core.*` (non `core.*`), quindi sono indipendenti dal PYTHONPATH e funzionano identicamente dopo la migrazione.

---

## 🔄 Execution Sequence (9 Phases)

### FASE 0: PREPARAZIONE & BASELINE ⏱️ 2 min

**Obiettivo**: Creare ambiente isolato e snapshot pre-migrazione.

```bash
# 0.1 — Verificare stato git pulito
git status

# 0.2 — Creare branch dedicato
git checkout -b feat/vitruvyan-edge-extraction

# 0.3 — Baseline test (SNAPSHOT PRE-MIGRAZIONE)
python3 -m pytest services/api_edge_oculus_prime/tests/ -v --tb=short > /tmp/test_baseline_pre_migration.log

# 0.4 — Verificare 7/8 test passed
grep "passed" /tmp/test_baseline_pre_migration.log
```

**Checkpoint**: 
- ✅ Git clean
- ✅ Branch creato
- ✅ Test baseline salvata (7/8 passed)

**Rollback**:
```bash
git switch main
# opzionale: eliminare il branch solo se non contiene commit da preservare
git branch -D feat/vitruvyan-edge-extraction
```

---

### FASE 1: CREAZIONE STRUTTURA `vitruvyan_edge/` ⏱️ 5 min

**Obiettivo**: Creare directory tree, copiare TUTTO il codice e gli asset non-Python.

```bash
# 1.1 — Creare directory tree
mkdir -p vitruvyan_edge/oculus_prime/core/agents
mkdir -p vitruvyan_edge/oculus_prime/dse_bridge
mkdir -p vitruvyan_edge/contracts

# 1.2 — Creare __init__.py a TUTTI i livelli (regular packages, non namespace)
# NOTA: l'originale usa namespace packages (nessun __init__.py tranne dse_bridge/).
# vitruvyan_edge DEVE usare regular packages per compatibilità setuptools.
touch vitruvyan_edge/oculus_prime/__init__.py
touch vitruvyan_edge/oculus_prime/core/__init__.py
touch vitruvyan_edge/oculus_prime/core/agents/__init__.py
touch vitruvyan_edge/contracts/__init__.py

# 1.2b — Creare __init__.py root con metadata multi-modulo
cat > vitruvyan_edge/__init__.py << 'EOF'
# Last updated: Feb 22, 2026 16:30 UTC
"""
Vitruvyan Edge — Multi-Module Pluggable Ingestion Layer.

Package contenitore per moduli edge pluggabili nel core.
Ogni modulo è indipendente e comunica con vitruvyan_core via StreamBus.

Modules:
    - oculus_prime: Multi-modal intake gateway (documents, images, audio, video, CAD, GIS)
    - dse_cps: (planned) DSE-CPS engine integration
"""

__version__ = "1.0.0"

EDGE_MODULES = [
    "oculus_prime",
    # "dse_cps",       # planned
    # "stream_intake", # planned
]
EOF
# dse_bridge/__init__.py viene copiato dal sorgente (già esiste)

# 1.3 — Copiare TUTTI i file (Python + JSON + SQL + Markdown)
cp -r infrastructure/edge/oculus_prime/core/agents/*.py vitruvyan_edge/oculus_prime/core/agents/
cp infrastructure/edge/oculus_prime/core/event_emitter.py vitruvyan_edge/oculus_prime/core/
cp infrastructure/edge/oculus_prime/core/guardrails.py vitruvyan_edge/oculus_prime/core/
cp infrastructure/edge/oculus_prime/core/schema.sql vitruvyan_edge/oculus_prime/core/
cp infrastructure/edge/oculus_prime/core/*.json vitruvyan_edge/oculus_prime/core/
cp infrastructure/edge/oculus_prime/core/*.md vitruvyan_edge/oculus_prime/core/
cp -r infrastructure/edge/oculus_prime/dse_bridge/* vitruvyan_edge/oculus_prime/dse_bridge/
cp infrastructure/edge/oculus_prime/README.md vitruvyan_edge/oculus_prime/

# 1.4 — Verificare copia
echo "=== Python files ==="
find vitruvyan_edge -type f -name "*.py" | wc -l  # Expected: 17 (12 original + 5 new __init__.py)
echo "=== Non-Python assets ==="
find vitruvyan_edge -type f \( -name "*.json" -o -name "*.sql" \) | wc -l  # Expected: 4
echo "=== Markdown docs ==="
find vitruvyan_edge -type f -name "*.md" | wc -l  # Expected: 5
echo "=== __init__.py count ==="
find vitruvyan_edge -name "__init__.py" | wc -l  # Expected: 6
```

**Output atteso**: 12 source Python + 5 new __init__.py = 17 Python files, 4 JSON/SQL assets, 5 markdown docs.

**ATTENZIONE**: Non copiare `__pycache__/` directories. Il comando `cp` sopra li evita perché è selettivo.

**Commit**:
```bash
git add vitruvyan_edge/
git commit -m "feat(edge): create vitruvyan_edge package structure

- Created vitruvyan_edge/oculus_prime/ hierarchy
- Copied core/ and dse_bridge/ modules (12 Python files + 4 non-Python assets)
- Added __init__.py for package discovery
- No code changes yet (imports still use infrastructure.edge)

Refs: #vitruvyan-edge-extraction"
```

**Rollback**: `git revert HEAD`

---

### FASE 2: AGGIORNAMENTO IMPORT INTERNI (Oculus Prime Core) ⏱️ 5 min

**Obiettivo**: Aggiornare import interni in `vitruvyan_edge/` per self-consistency.

**File da modificare** (7 occorrenze in `vitruvyan_edge/oculus_prime/core/agents/*.py`):
- `document_intake.py` (riga 24)
- `image_intake.py` (riga 24)
- `audio_intake.py` (riga 24)
- `video_stream_intake.py` (riga 26)
- `cad_intake.py` (riga 32)
- `geo_intake.py` (riga 28)
- `landscape_intake.py` (riga 33)

**File che NON richiedono modifiche** (audit verificato):
- `api_intake.py` — Non importa `infrastructure.edge`, usa solo `vitruvyan_core` (try/except) ✅
- `event_emitter.py` — Importa solo `vitruvyan_core.core.synaptic_conclave` ✅
- `guardrails.py` — Pure Python, nessun import esterno ✅
- `dse_bridge/main.py` — Importa solo `vitruvyan_core` ✅
- `dse_bridge/__init__.py` — Relative import (`.main`) ✅

**Trasformazione**:
```python
# PRIMA
from infrastructure.edge.oculus_prime.core.guardrails import IntakeGuardrails

# DOPO
from vitruvyan_edge.oculus_prime.core.guardrails import IntakeGuardrails
```

**Esecuzione automatica**:
```bash
# Sostituzione globale in vitruvyan_edge/
cd /home/vitruvyan/vitruvyan-core
find vitruvyan_edge/ -name "*.py" -type f -exec sed -i 's/from infrastructure\.edge\.oculus_prime/from vitruvyan_edge.oculus_prime/g' {} \;
find vitruvyan_edge/ -name "*.py" -type f -exec sed -i 's/import infrastructure\.edge\.oculus_prime/import vitruvyan_edge.oculus_prime/g' {} \;

# Verifica modifiche
grep -r "infrastructure.edge" vitruvyan_edge/  # Expected: no matches
```

**Test parziale**:
```bash
python3 -c "from vitruvyan_edge.oculus_prime.core.guardrails import IntakeGuardrails; print('✅ Import OK')"
```

**Commit**:
```bash
git add vitruvyan_edge/
git commit -m "refactor(edge): update internal imports in vitruvyan_edge

- Changed 7 files in core/agents/*.py
- infrastructure.edge.oculus_prime → vitruvyan_edge.oculus_prime
- Internal consistency verified

Test: Import succeeds without infrastructure.edge dependency"
```

**Rollback**: `git revert HEAD`

---

### FASE 3: AGGIORNAMENTO SERVICE ADAPTERS ⏱️ 4 min

**Obiettivo**: Aggiornare import in service layer (runtime + adapter).

**File da modificare**:
1. `services/api_edge_oculus_prime/adapters/runtime.py` (1 import)
2. `services/api_edge_oculus_prime/adapters/oculus_prime_adapter.py` (7 imports)

**Trasformazione (runtime.py)**:
```python
# PRIMA (riga 9)
from infrastructure.edge.oculus_prime.core.event_emitter import OculusPrimeEventEmitter

# DOPO
from vitruvyan_edge.oculus_prime.core.event_emitter import OculusPrimeEventEmitter
```

**Trasformazione (oculus_prime_adapter.py, righe 15-21)**:
```python
# PRIMA
from infrastructure.edge.oculus_prime.core.agents.audio_intake import AudioIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.cad_intake import CADIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.geo_intake import GeoIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.image_intake import ImageIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.landscape_intake import LandscapeIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.video_stream_intake import VideoStreamIntakeAgent

# DOPO
from vitruvyan_edge.oculus_prime.core.agents.audio_intake import AudioIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.cad_intake import CADIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.geo_intake import GeoIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.image_intake import ImageIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.landscape_intake import LandscapeIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.video_stream_intake import VideoStreamIntakeAgent
```

**NOTA (Audit finding)**: il piano originale contava 8 imports nell'adapter, ma sono 7 (verificato riga per riga).

**Esecuzione**:
```bash
# Sostituzione automatica
find services/api_edge_oculus_prime/adapters/ -name "*.py" -type f -exec sed -i 's/from infrastructure\.edge\.oculus_prime/from vitruvyan_edge.oculus_prime/g' {} \;

# Verifica
grep -r "infrastructure.edge" services/api_edge_oculus_prime/adapters/  # Expected: no matches
```

**Commit**:
```bash
git add services/api_edge_oculus_prime/adapters/
git commit -m "refactor(edge): update service adapter imports

- Updated runtime.py (1 import)
- Updated oculus_prime_adapter.py (7 imports)
- infrastructure.edge → vitruvyan_edge

Test: Service layer now references new package"
```

**Rollback**: `git revert HEAD`

---

### FASE 4: AGGIORNAMENTO TEST IMPORTS ⏱️ 3 min

**Obiettivo**: Aggiornare import in test suite e verificare 7/8 test ancora passed.

**File da modificare**:
1. `services/api_edge_oculus_prime/tests/test_document_ingest_integration.py` (riga 19)
2. `services/api_edge_oculus_prime/tests/test_event_emitter_migration.py` (riga 19)

**Trasformazione**:
```python
# PRIMA
from infrastructure.edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent  # noqa: E402
from infrastructure.edge.oculus_prime.core.event_emitter import IntakeEventEmitter  # noqa: E402

# DOPO
from vitruvyan_edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent  # noqa: E402
from vitruvyan_edge.oculus_prime.core.event_emitter import IntakeEventEmitter  # noqa: E402
```

**Esecuzione**:
```bash
# Sostituzione automatica
find services/api_edge_oculus_prime/tests/ -name "*.py" -type f -exec sed -i 's/from infrastructure\.edge\.oculus_prime/from vitruvyan_edge.oculus_prime/g' {} \;

# Verifica
grep -r "infrastructure.edge" services/api_edge_oculus_prime/tests/  # Expected: no matches
```

**Test completo**:
```bash
python3 -m pytest services/api_edge_oculus_prime/tests/ -v --tb=short > /tmp/test_post_imports.log

# Verifica 7/8 test ancora passed
grep -E "([0-9]+ passed|[0-9]+ skipped)" /tmp/test_baseline_pre_migration.log > /tmp/test_baseline_summary.log
grep -E "([0-9]+ passed|[0-9]+ skipped)" /tmp/test_post_imports.log > /tmp/test_post_imports_summary.log
diff /tmp/test_baseline_summary.log /tmp/test_post_imports_summary.log
```

**Expected output**: summary IDENTICO a baseline (`7 passed, 1 skipped`).

**Commit**:
```bash
git add services/api_edge_oculus_prime/tests/
git commit -m "refactor(edge): update test imports

- Updated test_document_ingest_integration.py
- Updated test_event_emitter_migration.py
- infrastructure.edge → vitruvyan_edge

Test: 7/8 tests still passing (multipart skip unchanged)"
```

**Rollback**: `git revert HEAD`

---

### FASE 5: AGGIORNAMENTO DOCKER INFRASTRUCTURE ⏱️ 4 min

**Obiettivo**: Aggiornare Dockerfile COPY paths e verificare build locale.

**File**: `services/api_edge_oculus_prime/Dockerfile` (riga 21)

**Trasformazione**:
```dockerfile
# PRIMA
COPY vitruvyan_core /app/vitruvyan_core
COPY infrastructure/edge/oculus_prime /app/infrastructure/edge/oculus_prime
COPY services/api_edge_oculus_prime /app/services/api_edge_oculus_prime

# DOPO
COPY vitruvyan_core /app/vitruvyan_core
COPY vitruvyan_edge /app/vitruvyan_edge
COPY services/api_edge_oculus_prime /app/services/api_edge_oculus_prime
```

**Note**: `PYTHONPATH=/app:/app/vitruvyan_core` già include `/app`, quindi `vitruvyan_edge` è automaticamente scopribile (no changes needed to ENV).

**Rebuild test (locale)**:
```bash
# Rebuild container (NO push, solo local test)
cd infrastructure/docker
docker build -f ../../services/api_edge_oculus_prime/Dockerfile -t vitruvyan-edge-test ../..

# Verifica se build succeed
docker images | grep vitruvyan-edge-test
```

**Commit**:
```bash
git add services/api_edge_oculus_prime/Dockerfile
git commit -m "refactor(edge): update Dockerfile COPY paths

- infrastructure/edge/oculus_prime → vitruvyan_edge
- PYTHONPATH already includes /app (no changes needed)
- Container build verified locally

Test: Docker build succeeds without errors"
```

**Rollback**: `git revert HEAD`

---

### FASE 6: AGGIORNAMENTO PYPROJECT.TOML ⏱️ 2 min

**Obiettivo**: Includere `vitruvyan_edge` in package discovery per installabilità.

**File**: `pyproject.toml` (righe 74-76)

**Trasformazione**:
```toml
# PRIMA
[tool.setuptools.packages.find]
where = ["."]
include = ["vitruvyan_core*"]
exclude = ["tests*", "docs*", "examples*", "scripts*"]

# DOPO
[tool.setuptools.packages.find]
where = ["."]
include = ["vitruvyan_core*", "vitruvyan_edge*"]
exclude = ["tests*", "docs*", "examples*", "scripts*", "infrastructure*"]
```

**Verifica pacchettizzazione**:
```bash
python3 -m pip install -e . --no-deps
python3 -c "import vitruvyan_edge.oculus_prime; print('✅ Package discoverable')"
```

**Commit**:
```bash
git add pyproject.toml
git commit -m "feat(packaging): add vitruvyan_edge to installable packages

- Added vitruvyan_edge* to include list
- Excluded infrastructure* from packaging
- Verified package discovery with pip install -e

Test: vitruvyan_edge.oculus_prime importable"
```

**Rollback**: `git revert HEAD`

---

### FASE 7: AGGIORNAMENTO DOCUMENTAZIONE ⏱️ 10 min

**Obiettivo**: Aggiornare README, docs, examples per riflettere nuova struttura.

#### 7.1 — README infrastructure/edge (DEPRECATION NOTE)

**File**: `infrastructure/edge/README.md`

**Contenuto nuovo**:
```markdown
# Edge Infrastructure Notes
> **Last updated**: Feb 22, 2026 15:45 UTC

⚠️ **DEPRECATED**: This directory is archived for deployment notes only.

**NEW LOCATION**: All edge module code has been moved to `/vitruvyan_edge/`

Runtime service code is under:
- `services/api_edge_oculus_prime`

Oculus Prime module is now under:
- `vitruvyan_edge/oculus_prime/` (NEW package location)

This `infrastructure/edge` area is reserved for edge deployment assets, profiles, and operational docs only (no Python code).
```

#### 7.2 — README vitruvyan_edge (NUOVO)

**File**: `vitruvyan_edge/README.md` (creare nuovo)

**Contenuto**:
```markdown
# Vitruvyan Edge — Multi-Module Pluggable Ingestion Layer
> **Last updated**: Feb 22, 2026 16:30 UTC

Domain-agnostic edge ingestion layer for Vitruvyan OS.  
Package contenitore multi-modulo: ogni modulo è un plugin indipendente che si integra con `vitruvyan_core`.

## Architecture

- **Core OS**: `vitruvyan_core/` (autonomous epistemic kernel — runs independently)
- **Edge Layer**: `vitruvyan_edge/` (pluggable acquisition/ingestion modules)
  - Ogni modulo si "plugga" nel core tramite contratti e StreamBus events
  - Moduli sono indipendenti tra loro (no cross-module imports)

## Modules

| Module | Status | Description |
|--------|--------|-------------|
| **Oculus Prime** | ✅ Active | Multi-modal intake gateway (documents, images, audio, video, CAD, GIS) |
| **DSE-CPS** | 📋 Planned | DSE-CPS engine integration |
| *(others)* | 📋 Planned | Stream intake, API gateway, etc. |

### Oculus Prime
Multi-modal intake gateway — acquires raw evidence from multiple media types, normalizes to literal format, emits immutable Evidence Packs to the Redis Cognitive Bus.

**Location**: `vitruvyan_edge/oculus_prime/`  
**Service**: `services/api_edge_oculus_prime/`  
**Docs**: [Oculus Prime README](oculus_prime/README.md)

## Adding New Modules

New edge modules follow the same pattern:
```
vitruvyan_edge/
├── oculus_prime/   # ✅ Reference implementation
├── new_module/     # Create following oculus_prime structure
│   ├── __init__.py
│   ├── core/
│   └── README.md
```

Each module MUST:
1. Be self-contained (no cross-module imports within edge)
2. Import from `vitruvyan_core` for OS primitives (agents, bus, contracts)
3. Communicate with other modules via StreamBus events (not direct imports)
4. Have its own service under `services/api_edge_<module>/`

## Installation

```bash
pip install -e .  # Installs both vitruvyan_core and vitruvyan_edge
```

## Usage

```python
from vitruvyan_edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent
from vitruvyan_edge.oculus_prime.core.event_emitter import IntakeEventEmitter

# Initialize agents
agent = DocumentIntakeAgent(event_emitter=emitter, postgres_agent=pg)
```

## Philosophy

Edge modules are **intake-only** (no inference, no business logic).  
Semantic processing happens in the **Core OS** (Memory Orders, Pattern Weavers, etc.).
```

#### 7.3 — Oculus Prime core/README.md (4 code examples + import paths)

**File**: `vitruvyan_edge/oculus_prime/core/README.md`

**Esecuzione**:
```bash
# Sostituzione automatica import paths nei code examples
sed -i 's/from infrastructure\.edge\.oculus_prime/from vitruvyan_edge.oculus_prime/g' vitruvyan_edge/oculus_prime/core/README.md
# Aggiornare path reference nel directory tree
sed -i 's|infrastructure/edge/oculus_prime|vitruvyan_edge/oculus_prime|g' vitruvyan_edge/oculus_prime/core/README.md
```

#### 7.4 — Oculus Prime root README.md (6 path references + schema.sql paths)

**File**: `vitruvyan_edge/oculus_prime/README.md`

**Esecuzione**:
```bash
# Aggiornare tutti i path references (6 occorrenze)
sed -i 's|infrastructure/edge/oculus_prime|vitruvyan_edge/oculus_prime|g' vitruvyan_edge/oculus_prime/README.md
```

#### 7.5 — DSE Bridge README.md

**File**: `vitruvyan_edge/oculus_prime/dse_bridge/README.md`

**Esecuzione**:
```bash
sed -i 's|infrastructure/edge/oculus_prime|vitruvyan_edge/oculus_prime|g' vitruvyan_edge/oculus_prime/dse_bridge/README.md
```

#### 7.6 — Documentazione esterna (5 files)

**Files da aggiornare** (con conteggio occorrenze verificato):
- `docs/infrastructure/EDGE_OCULUS_PRIME_INFRA.md` — 3 occorrenze
- `docs/planning/INTAKE_EDGE_REFACTOR_INTEGRATION_PLAN_FEB16_2026.md` — 1 occorrenza
- `docs/planning/ANDROID_OCULUS_PRIME_APP_ROADMAP_FEB17_2026.md` — 4 occorrenze
- `docs/knowledge_base/oculus_prime/intake_flow_graph.md` — 2 occorrenze
- `services/api_edge_oculus_prime/README.md` — 1 occorrenza

**File intenzionalmente NON toccato**:
- `docs/planning/EDGE_INTEROPERABILITY_CONTRACT_DRAFT_V0.md` (riferisce `infrastructure/edge/` a livello architetturale, non `.../oculus_prime`)

**Esecuzione**:
```bash
# Sostituzione path references nei docs esterni
for f in \
    docs/infrastructure/EDGE_OCULUS_PRIME_INFRA.md \
    docs/planning/INTAKE_EDGE_REFACTOR_INTEGRATION_PLAN_FEB16_2026.md \
    docs/planning/ANDROID_OCULUS_PRIME_APP_ROADMAP_FEB17_2026.md \
    docs/knowledge_base/oculus_prime/intake_flow_graph.md \
    services/api_edge_oculus_prime/README.md; do
    sed -i 's|infrastructure/edge/oculus_prime|vitruvyan_edge/oculus_prime|g' "$f"
    sed -i 's|infrastructure\.edge\.oculus_prime|vitruvyan_edge.oculus_prime|g' "$f"
done

# Verifica mirata (evita falsi positivi da documenti di pianificazione)
rg -n "from infrastructure\.edge" \
  docs/infrastructure/EDGE_OCULUS_PRIME_INFRA.md \
  docs/planning/INTAKE_EDGE_REFACTOR_INTEGRATION_PLAN_FEB16_2026.md \
  docs/planning/ANDROID_OCULUS_PRIME_APP_ROADMAP_FEB17_2026.md \
  docs/knowledge_base/oculus_prime/intake_flow_graph.md \
  services/api_edge_oculus_prime/README.md
# Verify: expected empty
```

**Commit**:
```bash
git add infrastructure/edge/README.md vitruvyan_edge/README.md vitruvyan_edge/oculus_prime/README.md vitruvyan_edge/oculus_prime/core/README.md vitruvyan_edge/oculus_prime/dse_bridge/README.md docs/ services/api_edge_oculus_prime/README.md
git commit -m "docs(edge): update documentation for vitruvyan_edge migration

- Deprecated infrastructure/edge/README.md (deployment only)
- Created vitruvyan_edge/README.md (new package docs)
- Updated code examples in core/README.md (4 occurrences)
- Updated 5 external docs/readmes with new path references

No code changes, documentation alignment only"
```

**Rollback**: `git revert HEAD`

---

### FASE 8: AGGIORNAMENTO MKDOCS CONFIG + RUNTIME ⏱️ 5 min

**Obiettivo**: Aggiornare navigation tree in MkDocs e garantire che `vitruvyan_edge/` sia visibile nel container docs.

**File 1**: `infrastructure/docker/mkdocs/mkdocs.yml` (riga 190)
**File 2**: `infrastructure/docker/mkdocs/backups/material_restore_20260219_105356/mkdocs.yml` (riga 158 — backup, aggiornare per coerenza)
**File 3**: `infrastructure/docker/docker-compose.yml` (service `mkdocs`, mount readonly)
**File 4**: `infrastructure/docker/mkdocs/Dockerfile` (symlink in `/app/docs_root`)

**Trasformazione**:
```yaml
# PRIMA
- Infrastructure:
  - Overview: infrastructure/README_INFRASTRUCTURE.md
  - Docker Setup: infrastructure/docker/README.md
  - Oculus Prime: infrastructure/edge/oculus_prime/README.md
  - Oculus Prime Flow Graph: docs/knowledge_base/oculus_prime/intake_flow_graph.md
  - Monitoring: infrastructure/docker/monitoring/README.md

# DOPO
- Infrastructure:
  - Overview: infrastructure/README_INFRASTRUCTURE.md
  - Docker Setup: infrastructure/docker/README.md
  - Edge (Deprecated): infrastructure/edge/README.md
  - Monitoring: infrastructure/docker/monitoring/README.md
  
- Edge Modules:
  - Overview: vitruvyan_edge/README.md
  - Oculus Prime: vitruvyan_edge/oculus_prime/README.md
  - Oculus Prime Core: vitruvyan_edge/oculus_prime/core/README.md
  - Oculus Prime Flow Graph: docs/knowledge_base/oculus_prime/intake_flow_graph.md
```

**Trasformazione runtime MkDocs (CRITICA)**:
```yaml
# infrastructure/docker/docker-compose.yml (service mkdocs, volumes)
- ../../vitruvyan_edge:/app/vitruvyan_edge:ro
```

```dockerfile
# infrastructure/docker/mkdocs/Dockerfile (RUN ... ln -s ...)
ln -s /app/vitruvyan_edge /app/docs_root/vitruvyan_edge
```

**NOTA (Audit finding)**: senza mount+symlink, la nav nuova punta a file non raggiungibili dal `docs_dir` nel container.

**Test MkDocs build**:
```bash
cd infrastructure/docker
docker compose up -d mkdocs
docker compose exec -T mkdocs ls -d /app/vitruvyan_edge /app/docs_root/vitruvyan_edge
docker compose exec -T mkdocs mkdocs build --strict --config-file /app/mkdocs.yml
# Expected: build OK, no errors
```

**Commit**:
```bash
git add \
  infrastructure/docker/mkdocs/mkdocs.yml \
  infrastructure/docker/mkdocs/backups/material_restore_20260219_105356/mkdocs.yml \
  infrastructure/docker/docker-compose.yml \
  infrastructure/docker/mkdocs/Dockerfile
git commit -m "docs(mkdocs): update edge nav and runtime path visibility

- Moved Oculus Prime section to new 'Edge Modules' category
- Updated paths: infrastructure/edge → vitruvyan_edge (main + backup)
- Added vitruvyan_edge mount in mkdocs compose service
- Added docs_root symlink for vitruvyan_edge in mkdocs image

Test: MkDocs build succeeds and new docs paths are reachable"
```

**Rollback**: `git revert HEAD`

---

### FASE 9: VERIFICA FINALE & CLEANUP ⏱️ 5 min

**Obiettivo**: Validazione completa end-to-end.

#### 9.1 — Test Suite Completo

```bash
# Test completo (deve matchare baseline)
python3 -m pytest services/api_edge_oculus_prime/tests/ -v --tb=short > /tmp/test_final.log

# Confronto risultati
grep -E "([0-9]+ passed|[0-9]+ skipped)" /tmp/test_baseline_pre_migration.log > /tmp/test_baseline_summary.log
grep -E "([0-9]+ passed|[0-9]+ skipped)" /tmp/test_final.log > /tmp/test_final_summary.log
diff /tmp/test_baseline_summary.log /tmp/test_final_summary.log
# Expected: summary IDENTICO (7 passed, 1 skipped)
```

#### 9.2 — Import Resolution Test

```bash
# Test tutti gli import path
python3 -c "
from vitruvyan_edge.oculus_prime.core.agents.api_intake import APIIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.image_intake import ImageIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.audio_intake import AudioIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.video_stream_intake import VideoStreamIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.cad_intake import CADIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.geo_intake import GeoIntakeAgent
from vitruvyan_edge.oculus_prime.core.agents.landscape_intake import LandscapeIntakeAgent
from vitruvyan_edge.oculus_prime.core.event_emitter import OculusPrimeEventEmitter, IntakeEventEmitter
from vitruvyan_edge.oculus_prime.core.guardrails import IntakeGuardrails
from vitruvyan_edge.oculus_prime.dse_bridge.main import app as dse_bridge_app
print('✅ All core+bridge imports resolved')
"
```

#### 9.3 — Verifica Residui

```bash
# Nessun riferimento a infrastructure.edge in codice Python (runtime)
grep -r "infrastructure\.edge" --include="*.py" services/api_edge_oculus_prime/ vitruvyan_edge/
# Expected: (empty)

# Verifica docs aggiornati: nessun "from infrastructure.edge" nei file target
rg -n "from infrastructure\.edge" \
  docs/infrastructure/EDGE_OCULUS_PRIME_INFRA.md \
  docs/planning/INTAKE_EDGE_REFACTOR_INTEGRATION_PLAN_FEB16_2026.md \
  docs/planning/ANDROID_OCULUS_PRIME_APP_ROADMAP_FEB17_2026.md \
  docs/knowledge_base/oculus_prime/intake_flow_graph.md \
  services/api_edge_oculus_prime/README.md
# Expected: (empty)

# Verifica che vitruvyan_edge NON abbia namespace vs regular package conflicts
python3 -c "
import vitruvyan_edge
print('Package type:', type(vitruvyan_edge).__name__)
print('Package file:', vitruvyan_edge.__file__)
print('Has __init__:', hasattr(vitruvyan_edge, '__file__') and vitruvyan_edge.__file__ is not None)
"
# Expected: __file__ should point to vitruvyan_edge/__init__.py (regular package)

# Verify NO __pycache__ was copied
find vitruvyan_edge -name "__pycache__" -type d
# Expected: (empty)
```

#### 9.4 — Docker Rebuild Finale

```bash
cd infrastructure/docker
docker compose build edge_oculus_prime --no-cache
docker compose up -d edge_oculus_prime

# Health check
sleep 10
curl http://localhost:9050/health | jq
# Expected: {"status": "healthy", ...}

# Log check
docker logs core_edge_oculus_prime --tail=50 | grep -i "error\|exception"
# Expected: (empty)
```

**Commit finale**:
```bash
git add -A
git commit -m "refactor(edge): complete vitruvyan_edge extraction [FINAL]

SUMMARY:
- Moved infrastructure/edge/oculus_prime → vitruvyan_edge/oculus_prime
- Created __init__.py at all package levels (regular packages, not namespace)
- Updated ~10 import statements across 4 Python files (adapters + tests)
- Copied 4 non-Python assets (JSON schemas, SQL)
- Updated Dockerfile COPY paths + PYTHONPATH
- Updated pyproject.toml package discovery
- Updated 11 documentation files (16+ path occurrences)
- Updated MkDocs navigation + runtime visibility (main + backup yml, compose mount, docs_root symlink)

IMPACT: 32 files affected, 55+ modifications across 9 phases

VERIFICATION:
✅ 7/8 tests passing (identical to baseline)
✅ All imports resolved (vitruvyan_edge.* regular packages)
✅ Docker container healthy
✅ No infrastructure.edge references in runtime code
✅ Package installable via pip
✅ No stale __pycache__ artifacts

RISKS MITIGATED:
- Test suite verified at each step
- Atomic commits per phase
- Rollback possible via git revert
- Docker rebuild validated
- MkDocs runtime path explicitly validated in container
- Namespace vs regular package explicitly chosen (regular)

Closes: #vitruvyan-edge-extraction"
```

**Rollback**: `git revert HEAD` (rollback completo sicuro: revert sequenziale dei commit di migrazione)

---

## 📊 Timeline & Resource Allocation

| Fase | Durata | Commit | Rollback Point | Status |
|------|--------|--------|----------------|--------|
| 0. Preparazione | 2 min | - | - | ⬜ Pending |
| 1. Struttura + Assets | 5 min | ✅ | `git revert <commit_fase_1>` | ⬜ Pending |
| 2. Import interni | 5 min | ✅ | `git revert <commit_fase_2>` | ⬜ Pending |
| 3. Service adapters | 4 min | ✅ | `git revert <commit_fase_3>` | ⬜ Pending |
| 4. Test imports | 3 min | ✅ | `git revert <commit_fase_4>` | ⬜ Pending |
| 5. Docker | 4 min | ✅ | `git revert <commit_fase_5>` | ⬜ Pending |
| 6. Packaging | 2 min | ✅ | `git revert <commit_fase_6>` | ⬜ Pending |
| 7. Docs | 10 min | ✅ | `git revert <commit_fase_7>` | ⬜ Pending |
| 8. MkDocs + runtime | 5 min | ✅ | `git revert <commit_fase_8>` | ⬜ Pending |
| 9. Verifica | 5 min | ✅ FINAL | - | ⬜ Pending |
| **TOTALE** | **45 min** | **9 commits** | - | - |

---

## ✅ Success Criteria (Acceptance Checklist)

Pre-merge validation (ALL must pass):

- [ ] **Test suite**: 7/8 passed (identico a baseline pre-migration)
- [ ] **Import test**: Tutti i moduli importabili da `vitruvyan_edge.*`
- [ ] **Docker**: Container healthy + health endpoint 200 OK
- [ ] **Grep check**: Zero occorrenze `infrastructure.edge` in codice runtime Python
- [ ] **Package**: `pip install -e .` include `vitruvyan_edge`
- [ ] **MkDocs**: Build without errors, navigation tree corretto
- [ ] **MkDocs runtime**: `/app/vitruvyan_edge` e `/app/docs_root/vitruvyan_edge` visibili nel container
- [ ] **Logs**: Docker logs NO errors/exceptions
- [ ] **Commit history**: 9 atomic commits, messaggi conformi conventional commits
- [ ] **__init__.py**: Presenti a tutti i livelli (`vitruvyan_edge/`, `oculus_prime/`, `core/`, `agents/`, `dse_bridge/`)
- [ ] **Non-Python assets**: JSON schemas + schema.sql copiati correttamente
- [ ] **No __pycache__**: Nessuna directory `__pycache__` nella nuova struttura

---

## 🚨 Rollback Plan

### Rollback Completo (Emergency)

```bash
# Identificare commit della migrazione (fase 1 → fase 9)
git log --oneline --graph

# Revert completo NON distruttivo (ordine inverso)
git revert --no-edit <commit_fase_9> <commit_fase_8> <commit_fase_7> <commit_fase_6> <commit_fase_5> <commit_fase_4> <commit_fase_3> <commit_fase_2> <commit_fase_1>

# Verify
git status
python3 -m pytest services/api_edge_oculus_prime/tests/  # Should pass 7/8
```

### Rollback Parziale (Surgical)

```bash
# Tornare a fase N (esempio: dopo fase 5)
git log --oneline --graph  # Identificare commit hash

# Revert ultimi 4 commit (tornare da fase 9 → fase 5)
git revert --no-edit <commit_fase_9> <commit_fase_8> <commit_fase_7> <commit_fase_6>
```

### Rollback Fase Singola

```bash
# Annullare solo fase 3 (preservare 1,2,4,5,...)
git revert <commit_hash_fase_3>

# Rebuild test
python3 -m pytest services/api_edge_oculus_prime/tests/
```

---

## 📈 Post-Migration Actions (Future)

1. **Infrastructure cleanup** (dopo 2-4 settimane stabilità):
   ```bash
   # Rimuovere infrastructure/edge/oculus_prime/ (codice, mantenere deployment docs)
   git rm -r infrastructure/edge/oculus_prime/core/
   git rm -r infrastructure/edge/oculus_prime/dse_bridge/
   git commit -m "chore(edge): remove deprecated infrastructure/edge code"
   ```

2. **Pyproject.toml enhancement** (opzionale):
   ```toml
   [project.optional-dependencies]
   edge = [
       "pdfplumber>=0.7.0",  # Document intake
       "python-docx>=0.8.11",  # DOCX support
       # ... altre dipendenze edge-specific
   ]
   ```

3. **CI/CD pipeline update**:
   - Aggiungere test stage: `pytest vitruvyan_edge/` (quando test suite creata)
   - Docker image tagging: `vitruvyan-edge:1.0.0`

4. **Next edge module — DSE-CPS** (priorità alta, seguire pattern Oculus Prime):
   ```
   vitruvyan_edge/
   ├── oculus_prime/     ✅ (reference implementation)
   ├── dse_cps/          📋 (prossimo: DSE-CPS engine integration)
   │   ├── __init__.py
   │   ├── core/
   │   └── README.md
   ├── stream_intake/    📋 (futuro: real-time streams)
   ├── api_gateway/      📋 (futuro: REST/GraphQL intake)
   └── ...
   ```
   
   **Pattern per nuovi moduli**:
   - Creare `vitruvyan_edge/<module>/` con `__init__.py` + `core/` + `README.md`
   - Creare service `services/api_edge_<module>/`
   - Import dal core: `from vitruvyan_core.core.agents...` (mai import cross-modulo edge)
   - Comunicazione inter-modulo: solo via StreamBus events

---

## 🎯 Benefits Realized

### Architectural
- ✅ Simmetria `vitruvyan_core/` ↔ `vitruvyan_edge/` (first-class citizens)
- ✅ Separation of concerns: Core (OS autonomo) vs Edge (plugins ingestion)
- ✅ `infrastructure/` semanticamente corretto (deployment only, no business logic)
- ✅ **Multi-modulo by design**: `vitruvyan_edge/` è un contenitore, Oculus Prime è il primo modulo. DSE-CPS, stream intake e altri seguiranno lo stesso pattern senza toccare la struttura

### Operational
- ✅ Pacchettizzazione futura: Edge diventa installabile standalone (`pip install vitruvyan-edge`)
- ✅ Modularity: Ogni modulo edge è indipendente (no cross-module imports)
- ✅ Testability: Ogni modulo edge isolabile per test integrazione
- ✅ Scalabilità: Aggiungere un nuovo modulo = `vitruvyan_edge/<nome>/` + service, zero impatto sugli altri

### Philosophical Alignment
- ✅ "Pluggable" architecture per estensibilità verticali
- ✅ Core OS domain-agnostic (edge gestisce input, core gestisce reasoning)
- ✅ Sacred Order boundaries rispettate (Perception = edge layer)

---

## 📚 References

- **Sacred Orders Architecture**: `.github/copilot-instructions.md` (Sacred Orders section)
- **Service Pattern**: `services/SERVICE_PATTERN.md`
- **Oculus Prime Docs**: `infrastructure/edge/oculus_prime/README.md` (pre-migration)
- **Test Coverage Report**: Fase 0 baseline (`/tmp/test_baseline_pre_migration.log`)

---

## 👥 Stakeholders & Approvals

| Role | Name | Approval Status | Date |
|------|------|-----------------|------|
| **Architect** | - | ⬜ Pending | - |
| **Tech Lead** | - | ⬜ Pending | - |
| **DevOps** | - | ⬜ Pending | - |
| **QA** | - | ⬜ Pending | - |

---

## 📝 Execution Log (To be filled during migration)

| Fase | Start Time | End Time | Status | Notes |
|------|-----------|----------|--------|-------|
| 0. Preparazione | - | - | ⬜ | - |
| 1. Struttura | - | - | ⬜ | - |
| 2. Import interni | - | - | ⬜ | - |
| 3. Service adapters | - | - | ⬜ | - |
| 4. Test imports | - | - | ⬜ | - |
| 5. Docker | - | - | ⬜ | - |
| 6. Packaging | - | - | ⬜ | - |
| 7. Docs | - | - | ⬜ | - |
| 8. MkDocs | - | - | ⬜ | - |
| 9. Verifica | - | - | ⬜ | - |

---

**Document Status**: ✅ Ready for review  
**Next Action**: Stakeholder approval → Execute Phase 0  
**Owner**: Vitruvyan Core Team  
**Last Review**: Feb 22, 2026 18:30 UTC (re-audit post ChatGPT review)
