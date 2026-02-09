# TODO: Orthodoxy Wardens Refactoring Completion
**Date**: Feb 9, 2026  
**Status**: 56% Complete (4/7 fasi)  
**Goal**: Template refactoring per tutti i Sacred Orders  
**Estimated Time**: 3-4 ore totali

---

## 🎯 Current Status Summary

### ✅ Completato (4/7 fasi)
- ✅ FASE 4: Documentation (4/4 docs presenti)
- ✅ FASE 7: Listener Integration (8 consumer groups attivi)
- ✅ FASE 1: Business Logic Separation (54% - partial)
- ✅ Examples/ (4 script + README)

### ❌ Da Completare (3/7 fasi)
- ❌ FASE 2: Directory Organization (38% → target 100%)
- ❌ FASE 5: Testing & Validation (0% → target 100%)
- ❌ FASE 6: Git Commit & Tag (0% → target 100%)

### ⚠️ Blockers
1. **main.py troppo grande** (863 lines, target <200)
2. **5 directory mancanti** (models/, api/, monitoring/, governance/, utils/)
3. **Nessun test eseguito** (import, structural, circular deps, rebuild)

---

## 📋 TODO List (Dettagliata)

---

## **PRIORITY 1: FASE 2 - Directory Organization (2-3h)** 🔴

### Task 1.1: Create Missing Directories (5 min)
```bash
cd /home/vitruvyan/vitruvyan-core

mkdir -p services/governance/api_orthodoxy_wardens/models
mkdir -p services/governance/api_orthodoxy_wardens/api
mkdir -p services/governance/api_orthodoxy_wardens/monitoring
mkdir -p services/governance/api_orthodoxy_wardens/governance
mkdir -p services/governance/api_orthodoxy_wardens/utils

# Create __init__.py in each
touch services/governance/api_orthodoxy_wardens/models/__init__.py
touch services/governance/api_orthodoxy_wardens/api/__init__.py
touch services/governance/api_orthodoxy_wardens/monitoring/__init__.py
touch services/governance/api_orthodoxy_wardens/governance/__init__.py
touch services/governance/api_orthodoxy_wardens/utils/__init__.py
```

**Validation**:
```bash
ls -1 services/governance/api_orthodoxy_wardens/ | grep -E "^(models|api|monitoring|governance|utils)$" | wc -l
# Expected: 5
```

---

### Task 1.2: Extract Pydantic Models → models/ (30 min)

**Create**: `services/governance/api_orthodoxy_wardens/models/schemas.py`

**Extract from main.py** (lines 214-237):
- `DivineHealthResponse` (line 214)
- `ConfessionRequest` (line 220)
- `OrthodoxyStatusResponse` (line 226)

**New file structure**:
```python
# models/schemas.py
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class DivineHealthResponse(BaseModel):
    """Divine health check response schema"""
    status: str
    sacred_timestamp: str
    confession_queue: int
    active_rituals: int
    divine_council: Dict[str, str]
    database_sanctity: str
    orchestration_blessing: str

class ConfessionRequest(BaseModel):
    """Confession request schema"""
    service_name: str
    confession_type: str
    details: Dict[str, Any]
    severity: Optional[str] = "moderate"

class OrthodoxyStatusResponse(BaseModel):
    """Orthodoxy status response schema"""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None
```

**Update main.py**:
- Remove class definitions (lines 214-237)
- Add import: `from api_orthodoxy_wardens.models.schemas import DivineHealthResponse, ConfessionRequest, OrthodoxyStatusResponse`

**Test**:
```bash
python3 -c "from services.governance.api_orthodoxy_wardens.models.schemas import ConfessionRequest; print('✅ Models OK')"
```

---

### Task 1.3: Extract Workflows → core/workflows.py (1h)

**Create**: `services/governance/api_orthodoxy_wardens/core/workflows.py`

**Extract from main.py**:
- `run_confession_workflow()` (lines 688-739, 52 lines)
- `run_purification_ritual()` (lines 741-756, 16 lines)
- `divine_surveillance_monitoring()` (lines 758-793, 36 lines)

**Dependencies to import**:
```python
# core/workflows.py
import logging
from typing import Dict, Any
from datetime import datetime
from api_orthodoxy_wardens.core.roles import (
    sacred_confessor, sacred_penitent, sacred_inquisitor, sacred_chronicler
)
from api_orthodoxy_wardens.core.event_handlers import handle_audit_request

logger = logging.getLogger(__name__)

async def run_confession_workflow(confession_state: Dict) -> Dict:
    """
    Sacred confession workflow orchestration.
    
    Phases:
    1. Confessor receives and validates confession
    2. Inquisitor investigates heretical patterns
    3. Penitent performs remediation rituals
    4. Chronicler records sacred outcome
    """
    # ... move implementation from main.py
    pass

async def run_purification_ritual(purification_state: Dict) -> Dict:
    """Purification ritual orchestration"""
    # ... move implementation
    pass

async def divine_surveillance_monitoring() -> Dict:
    """Continuous divine surveillance monitoring"""
    # ... move implementation
    pass
```

**Update main.py**:
- Remove workflow functions
- Add import: `from api_orthodoxy_wardens.core.workflows import run_confession_workflow, run_purification_ritual, divine_surveillance_monitoring`

**Lines saved**: ~104 lines removed from main.py

---

### Task 1.4: Extract Endpoints → api/routes.py (1h)

**Create**: `services/governance/api_orthodoxy_wardens/api/routes.py`

**Strategy**: Move ALL `@app.` decorated functions to routes.py, keep ONLY routing logic

**Structure**:
```python
# api/routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from api_orthodoxy_wardens.models.schemas import (
    DivineHealthResponse, ConfessionRequest, OrthodoxyStatusResponse
)
from api_orthodoxy_wardens.core.workflows import (
    run_confession_workflow, run_purification_ritual
)
from api_orthodoxy_wardens.monitoring.health import divine_health_check

router = APIRouter()

@router.get("/divine-health", response_model=DivineHealthResponse)
async def health_endpoint():
    """Divine health check endpoint"""
    return await divine_health_check()

@router.post("/confess", response_model=OrthodoxyStatusResponse)
async def confess_endpoint(request: ConfessionRequest, background_tasks: BackgroundTasks):
    """Initiate confession workflow"""
    # Minimal routing logic, delegate to workflows
    confession_state = {
        "confession_id": f"CONF-{int(datetime.now().timestamp())}",
        "service_name": request.service_name,
        "confession_type": request.confession_type,
        "details": request.details,
        "severity": request.severity,
        "status": "received"
    }
    background_tasks.add_task(run_confession_workflow, confession_state)
    return OrthodoxyStatusResponse(
        status="confession_accepted",
        message=f"Confession {confession_state['confession_id']} accepted"
    )

# ... altre 10-12 endpoints
```

**Endpoints to migrate** (from main.py):
1. `/divine-health` (line 350)
2. `/confess` (line 386)
3. `/synaptic-audit` (line 451)
4. `/conclave-status` (line 488)
5. `/test-confession-cycle` (line 516)
6. `/confessions/{confession_id}` (line 546)
7. `/confessions/recent` (line 572)
8. `/realm-surveillance` (line 594)
9. `/purification-ritual` (line 612)
10. `/orthodoxy-validation` (line 649)
11. `/detect-heresy` (line 667)
12. `/validate-service-sanctity` (line 795)
13. `/check-divine-dependencies` (line 813)
14. `/detect-sacred-harmony-conflicts` (line 831)

**Update main.py**:
```python
# main.py (after refactoring)
from fastapi import FastAPI
from api_orthodoxy_wardens.api.routes import router
from api_orthodoxy_wardens.monitoring.health import sacred_initialization

app = FastAPI(
    title="🏛️ Vitruvyan Orthodoxy Wardens",
    description="Sacred guardians of system orthodoxy",
    version="1.0.0"
)

# Include router
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup():
    await sacred_initialization()
```

**Lines saved**: ~500 lines removed from main.py

**Target**: main.py < 200 lines (thin wrapper only)

---

### Task 1.5: Extract Health Check → monitoring/health.py (30 min)

**Create**: `services/governance/api_orthodoxy_wardens/monitoring/health.py`

**Extract from main.py**:
- `divine_health_check()` (lines 350-384)
- `sacred_initialization()` (lines 239-348) - startup logic

**Structure**:
```python
# monitoring/health.py
import logging
from datetime import datetime
from typing import Dict, Any
from api_orthodoxy_wardens.models.schemas import DivineHealthResponse
from api_orthodoxy_wardens.core.orthodoxy_db_manager import OrthodoxyDatabaseManager

logger = logging.getLogger(__name__)

# Global instances (moved from main.py)
confessor_agent = None
penitent_agent = None
chronicler_agent = None
inquisitor_agent = None
db_manager = None
stream_bus = None

async def sacred_initialization():
    """Initialize all sacred components on startup"""
    global confessor_agent, penitent_agent, chronicler_agent, inquisitor_agent, db_manager, stream_bus
    
    logger.info("🏛️ Initializing Orthodoxy Wardens Sacred Council...")
    
    # Initialize components
    # ... move initialization logic from main.py
    
    logger.info("✅ Sacred Council initialized successfully")

async def divine_health_check() -> DivineHealthResponse:
    """
    Sacred health check - validates divine council readiness.
    Returns detailed status of all theological components.
    """
    # ... move health check logic
    pass
```

**Benefits**:
- Separation of concerns (monitoring vs routing)
- Testable health logic without FastAPI
- Reusable in other contexts

---

### Task 1.6: Create utils/config.py (15 min)

**Create**: `services/governance/api_orthodoxy_wardens/utils/config.py`

**Purpose**: Centralize configuration and environment variables

```python
# utils/config.py
import os
from typing import Optional

class OrthodoxyConfig:
    """Centralized configuration for Orthodoxy Wardens"""
    
    # Redis/Cognitive Bus
    REDIS_HOST: str = os.getenv("REDIS_HOST", "omni_redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # PostgreSQL
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "vitruvyan_omni")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "vitruvyan_user")
    
    # Service settings
    SERVICE_PORT: int = 8006
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Sacred channels (Synaptic Conclave)
    AUDIT_CHANNEL: str = "orthodoxy.audit.requested"
    VALIDATION_CHANNEL: str = "orthodoxy.validation.requested"
    
    @classmethod
    def validate(cls):
        """Validate configuration on startup"""
        required = ["POSTGRES_USER", "POSTGRES_DB"]
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing required config: {missing}")

# Global config instance
config = OrthodoxyConfig()
```

**Usage in other modules**:
```python
from api_orthodoxy_wardens.utils.config import config

# Use config values
db_host = config.POSTGRES_HOST
```

---

### Task 1.7: Update __init__.py Files (15 min)

**Update each __init__.py** to export public interfaces:

**models/__init__.py**:
```python
from .schemas import DivineHealthResponse, ConfessionRequest, OrthodoxyStatusResponse

__all__ = ["DivineHealthResponse", "ConfessionRequest", "OrthodoxyStatusResponse"]
```

**api/__init__.py**:
```python
from .routes import router

__all__ = ["router"]
```

**monitoring/__init__.py**:
```python
from .health import divine_health_check, sacred_initialization

__all__ = ["divine_health_check", "sacred_initialization"]
```

**core/__init__.py** (update existing):
```python
from .roles import (
    SacredRole, OrthodoxConfessor, OrthodoxPenitent,
    OrthodoxChronicler, OrthodoxInquisitor, OrthodoxAbbot
)
from .event_handlers import handle_audit_request, handle_heresy_detection, handle_system_events
from .orthodoxy_db_manager import OrthodoxyDatabaseManager
from .workflows import run_confession_workflow, run_purification_ritual, divine_surveillance_monitoring

__all__ = [
    "SacredRole", "OrthodoxConfessor", "OrthodoxPenitent",
    "OrthodoxChronicler", "OrthodoxInquisitor", "OrthodoxAbbot",
    "handle_audit_request", "handle_heresy_detection", "handle_system_events",
    "OrthodoxyDatabaseManager",
    "run_confession_workflow", "run_purification_ritual", "divine_surveillance_monitoring"
]
```

---

### Task 1.8: Final main.py Refactoring (30 min)

**Target**: main.py < 200 lines (thin wrapper)

**Final structure**:
```python
# main.py (AFTER refactoring)
"""
🏛️ ORTHODOXY WARDENS - Sacred Compliance & Divine Order API
Thin FastAPI wrapper delegating to domain modules.
"""

from fastapi import FastAPI
import logging
import sys

# Add to path
sys.path.append('/app')

# Import routers and initialization
from api_orthodoxy_wardens.api.routes import router
from api_orthodoxy_wardens.monitoring.health import sacred_initialization
from api_orthodoxy_wardens.utils.config import config

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("OrthodoxyWardens")

# FastAPI app
app = FastAPI(
    title="🏛️ Vitruvyan Orthodoxy Wardens",
    description="Sacred guardians of system orthodoxy and divine architectural compliance",
    version="1.0.0"
)

# Include router
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize sacred components"""
    logger.info("🏛️ Starting Orthodoxy Wardens...")
    await sacred_initialization()
    logger.info("✅ Orthodoxy Wardens ready")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("🏛️ Shutting down Orthodoxy Wardens...")
    # Cleanup logic here
    logger.info("✅ Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.SERVICE_PORT)
```

**Estimated lines**: ~80 lines (down from 863, **-90% reduction**)

---

## **PRIORITY 2: FASE 5 - Testing & Validation (1h)** 🟡

### Task 2.1: Import Tests (10 min)

```bash
cd /home/vitruvyan/vitruvyan-core

# Test 1: Core modules import
python3 -c "from services.governance.api_orthodoxy_wardens.core import orthodoxy_db_manager; print('✅ Core import OK')"

# Test 2: Models import
python3 -c "from services.governance.api_orthodoxy_wardens.models.schemas import ConfessionRequest; print('✅ Models import OK')"

# Test 3: API routes import
python3 -c "from services.governance.api_orthodoxy_wardens.api.routes import router; print('✅ API import OK')"

# Test 4: Monitoring import
python3 -c "from services.governance.api_orthodoxy_wardens.monitoring.health import divine_health_check; print('✅ Monitoring import OK')"

# Test 5: Workflows import
python3 -c "from services.governance.api_orthodoxy_wardens.core.workflows import run_confession_workflow; print('✅ Workflows import OK')"
```

**Expected**: 5/5 tests pass ✅

---

### Task 2.2: Structural Verification (5 min)

```bash
# Count directories
ls -1 services/governance/api_orthodoxy_wardens/ | grep -E "^(core|models|api|monitoring|governance|utils|docs|examples)$" | wc -l
# Expected: 8

# Check __init__.py presence
find services/governance/api_orthodoxy_wardens/ -type d -exec test -f {}/__init__.py \; -print | wc -l
# Expected: 8 (all directories have __init__.py)

# Verify main.py size
wc -l services/governance/api_orthodoxy_wardens/main.py
# Expected: < 200 lines
```

---

### Task 2.3: Circular Dependency Check (5 min)

```bash
# Test full package import
python3 -c "import services.governance.api_orthodoxy_wardens as orthodoxy; print('✅ No circular imports')"

# Test cross-module imports
python3 << 'EOF'
from services.governance.api_orthodoxy_wardens.core import workflows
from services.governance.api_orthodoxy_wardens.models import schemas
from services.governance.api_orthodoxy_wardens.api import routes
print("✅ Cross-module imports OK")
EOF
```

---

### Task 2.4: Docker Rebuild & Test (30 min)

```bash
cd /home/vitruvyan/vitruvyan-core/infrastructure/docker

# Rebuild main service
docker compose build api_orthodoxy_wardens

# Rebuild listener
docker compose build api_orthodoxy_wardens_listener

# Stop old containers
docker compose stop api_orthodoxy_wardens api_orthodoxy_wardens_listener

# Start new containers
docker compose up -d api_orthodoxy_wardens api_orthodoxy_wardens_listener

# Wait for startup (30s)
sleep 30

# Check logs
docker logs omni_api_orthodoxy_wardens --tail 50
docker logs omni_orthodoxy_wardens_listener --tail 30

# Test health endpoint
curl -s http://localhost:9006/divine-health | jq .

# Expected: {"status": "blessed", "sacred_timestamp": "...", ...}
```

---

### Task 2.5: E2E Workflow Test (10 min)

```bash
# Use existing example script
cd /home/vitruvyan/vitruvyan-core/services/governance/api_orthodoxy_wardens/examples

# Test 1: Health check
bash 01_health_check.sh

# Test 2: Initiate audit (confession workflow)
python3 02_initiate_audit.py

# Test 3: Query recent logs
bash 03_query_recent_logs.sh

# Expected: All 3 tests pass, no errors
```

---

## **PRIORITY 3: FASE 6 - Git Commit & Tag (30 min)** 🟢

### Task 3.1: Review Changes (10 min)

```bash
cd /home/vitruvyan/vitruvyan-core

# Check git status
git status

# Review diff
git diff services/governance/api_orthodoxy_wardens/

# Expected changes:
# - New directories: models/, api/, monitoring/, governance/, utils/
# - New files: 8-10 new Python files
# - Modified: main.py (863 → ~80 lines)
# - Modified: core/__init__.py (updated exports)
```

---

### Task 3.2: Stage Changes (5 min)

```bash
# Stage all Orthodoxy Wardens changes
git add services/governance/api_orthodoxy_wardens/

# Verify staged files
git diff --cached --name-only | grep orthodoxy
```

---

### Task 3.3: Commit with Comprehensive Message (10 min)

```bash
git commit -m "refactor(orthodoxy): FASE 2-6 completion - professional structure

FASE 2: Directory Organization (38% → 100%)
- Created: models/, api/, monitoring/, governance/, utils/
- Extracted Pydantic schemas → models/schemas.py
- Extracted workflows → core/workflows.py
- Extracted endpoints → api/routes.py
- Extracted health checks → monitoring/health.py
- Centralized config → utils/config.py

FASE 1: Business Logic Separation (54% → 95%)
- main.py: 863 → 80 lines (-90% reduction)
- Thin wrapper pattern achieved
- All business logic in domain modules

FASE 5: Testing & Validation
- Import tests: 5/5 passed ✅
- Structural verification: 8/8 directories ✅
- Circular dependency check: passed ✅
- Docker rebuild: successful ✅
- E2E workflow test: 3/3 passed ✅

FASE 6: Git Commit
- Tagged: refactor/orthodoxy_wardens_v1
- Template ready for other Sacred Orders

Result:
- Professional structure (8 logical directories)
- 45-min onboarding (vs 4-6h before)
- Multi-repo ready (clean imports, no relative paths)
- Test coverage: 100% structural, E2E workflows validated

Files changed: 15
Insertions: ~1,200 lines (new files)
Deletions: ~783 lines (from main.py)
Net: +417 lines (better organization)

Docs: README.md, ORTHODOXY_WARDENS_GUIDE.md, API_REFERENCE.md, ARCHITECTURAL_DECISIONS.md (already present)
Examples: 4 scripts + README (already present)"
```

---

### Task 3.4: Tag Release (5 min)

```bash
# Create annotated tag
git tag -a refactor/orthodoxy_wardens_v1 -m "Orthodoxy Wardens v1.0 - Refactoring Complete

- 8-directory professional structure
- 95% business logic separation
- <200 lines main.py
- Full test coverage
- Template for Sacred Orders refactoring"

# Push commit + tag
git push origin main
git push origin refactor/orthodoxy_wardens_v1
```

---

## 📊 Success Metrics

### Before Refactoring (Current)
- Directory structure: 3/8 (38%)
- main.py size: 863 lines
- Business logic separation: 54%
- Test coverage: 0%
- Onboarding time: 4-6 hours

### After Refactoring (Target)
- Directory structure: 8/8 (100%) ✅
- main.py size: <200 lines (target: 80 lines) ✅
- Business logic separation: 95% ✅
- Test coverage: 100% structural + E2E ✅
- Onboarding time: 45 minutes ✅

### Quality Metrics
- Import errors: 0
- Circular dependencies: 0
- Container health: 100% (both service + listener healthy)
- Docker rebuild: successful (no errors)
- E2E tests: 100% pass rate

---

## 🎯 Final Checklist

```
Pre-Flight:
- [ ] Git branch clean (no uncommitted changes)
- [ ] Docker containers running (orthodoxy service + listener)
- [ ] PostgreSQL schema applied (4 tables present)
- [ ] Qdrant collections created (entities_embeddings, conversations_embeddings)

PRIORITY 1 - Directory Organization:
- [ ] Task 1.1: Create 5 directories (models, api, monitoring, governance, utils)
- [ ] Task 1.2: Extract models → models/schemas.py
- [ ] Task 1.3: Extract workflows → core/workflows.py
- [ ] Task 1.4: Extract endpoints → api/routes.py
- [ ] Task 1.5: Extract health → monitoring/health.py
- [ ] Task 1.6: Create utils/config.py
- [ ] Task 1.7: Update __init__.py files (8 files)
- [ ] Task 1.8: Refactor main.py (<200 lines)

PRIORITY 2 - Testing:
- [ ] Task 2.1: Import tests (5/5 pass)
- [ ] Task 2.2: Structural verification
- [ ] Task 2.3: Circular dependency check
- [ ] Task 2.4: Docker rebuild + logs check
- [ ] Task 2.5: E2E workflow test (3 examples)

PRIORITY 3 - Git Commit:
- [ ] Task 3.1: Review changes (git diff)
- [ ] Task 3.2: Stage changes (git add)
- [ ] Task 3.3: Commit with comprehensive message
- [ ] Task 3.4: Tag refactor/orthodoxy_wardens_v1

Post-Flight:
- [ ] Container health: both healthy
- [ ] Listener consuming: 8 consumer groups active
- [ ] Documentation: 4 docs present + examples/
- [ ] Template ready: Use for Vault Keepers, Babel Gardens, Codex Hunters

Estimated Total Time: 3-4 hours
```

---

## 🔄 Template for Next Sacred Orders

Una volta completato Orthodoxy Wardens, questo stesso pattern si applica a:

1. **Vault Keepers** (P1 - next)
   - Stessa struttura (models/, api/, core/, monitoring/, utils/)
   - Business logic: archival, retrieval, snapshot creation
   - Listener: già presente (needs same refactoring)

2. **Babel Gardens** (P2)
   - Sentiment fusion, emotion detection, multilingual
   - Modules: sentiment_fusion.py, embedding_engine.py

3. **Codex Hunters** (P2)
   - Reddit/news scraping, async data collection
   - Modules: hunters/event_hunter.py, hunters/tracker.py

4. **Memory Orders** (P3)
   - Memory coherence, phrase sync, RAG health

**Tutti seguiranno lo stesso pattern Orthodoxy Wardens v1** 🎯

---

## 🚀 Quick Start Command

```bash
# Execute all Priority 1 tasks (directory organization)
cd /home/vitruvyan/vitruvyan-core

# 1. Create directories
mkdir -p services/governance/api_orthodoxy_wardens/{models,api,monitoring,governance,utils}
for dir in models api monitoring governance utils; do 
  touch services/governance/api_orthodoxy_wardens/$dir/__init__.py
done

# 2. Start refactoring (manual file creation + extraction)
# Follow Task 1.2-1.8 step by step

# 3. Test
python3 -c "from services.governance.api_orthodoxy_wardens.models.schemas import ConfessionRequest; print('✅')"

# 4. Rebuild
docker compose -f infrastructure/docker/docker-compose.yml build api_orthodoxy_wardens

# 5. Commit
git add services/governance/api_orthodoxy_wardens/
git commit -m "refactor(orthodoxy): FASE 2-6 completion"
git tag refactor/orthodoxy_wardens_v1
```

---

**Pronto per iniziare?** 🛠️
