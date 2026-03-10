# Core Hardening Roadmap — 8.5 → 10/10
> **Last updated**: Mar 10, 2026 18:00 UTC

Rating attuale: **8.5/10** — architettura solida, import hygiene 100%, Sacred Orders 100% conformant.

---

## Implementati oggi (Mar 10, 2026)

### ✅ DX-01: Pre-commit hooks
- **File**: `.pre-commit-config.yaml`
- **Cosa fa**: trailing-whitespace, check-yaml, check-json, ruff (lint+format), black, import-boundary check su pre-push
- **Setup**: `make dev` (installa pre-commit + hooks)

### ✅ DX-02: Makefile
- **File**: `Makefile`
- **Target**: `test`, `lint`, `format`, `check`, `test-cov`, `test-arch`, `smoke`, `build`, `up`, `down`, `health`, `clean`
- **Usage**: `make help` per lista completa

### ✅ DOCKER-01: Compose hardening
- **8 immagini `:latest` → versioni pinnate** (prometheus v2.52.0, grafana 11.0.0, etc.)
- **7 resource limits** aggiunti (mem_limit + cpus) su monitoring stack
- **Grafana password esternalizzata** → `${GRAFANA_ADMIN_PASSWORD}` (aggiunta a `.env.example`)

---

## Roadmap implementazione

### FASE 1: CI Quality Gate (→ 9.0) — Priorità ALTA
> *Dipende da: stabilizzazione Jenkins + familiarità workflow*

**Obiettivo**: Ogni push/PR deve passare lint + test + coverage gate.

**Task:**
- [ ] **CI-01**: Creare `.github/workflows/ci-quality-gate.yml`
  - Step 1: `ruff check vitruvyan_core/ services/`
  - Step 2: `black --check vitruvyan_core/ services/`
  - Step 3: `pytest -m "not e2e" --cov=vitruvyan_core --cov-fail-under=75`
  - Trigger: push to main + PR
- [ ] **CI-02**: Aggiornare Jenkinsfile
  - Aggiungere stage `lint` (ruff + black)
  - Aggiungere `--cov-report=xml` al stage test per artifact coverage
  - Aggiungere stage `docker-lint` (hadolint sui Dockerfile)
- [ ] **CI-03**: Badge coverage nel README.md

**Effort**: ~2h una volta che Jenkins è stabile
**Dipendenze**: Jenkins stabile, GitHub Actions runner attivo

---

### FASE 2: Integration Tests (→ 9.5) — Priorità ALTA
> *Non dipende da infra, si può fare subito*

**Obiettivo**: Coprire le interazioni cross-Sacred Order senza Docker.

**Test da creare:**

| File | Copertura | LOC stimate |
|------|-----------|-------------|
| `tests/integration/test_memory_vault_flow.py` | Memory Orders ↔ Vault Keepers coherence + archive | ~80 |
| `tests/integration/test_babel_weavers_flow.py` | Babel Gardens → Pattern Weavers compilation | ~60 |
| `tests/integration/test_orthodoxy_validation.py` | Orthodoxy Wardens audit pipeline | ~60 |
| `tests/integration/test_streambus_lifecycle.py` | StreamBus consumer create/consume/ack cycle | ~50 |
| `tests/integration/test_postgres_agent_tx.py` | PostgresAgent transaction + rollback | ~40 |
| `tests/integration/test_llm_agent_caching.py` | LLMAgent cache hit/miss/expiry | ~40 |
| `tests/integration/test_event_envelope.py` | TransportEvent → CognitiveEvent adapter | ~30 |

**Pattern da seguire:**
```python
@pytest.fixture
def mock_bus():
    """Mock StreamBus — no Redis, test pure consumer logic."""
    bus = MagicMock(spec=StreamBus)
    bus.consume.return_value = iter([mock_event("vault.archive.completed", {...})])
    return bus
```

**Effort**: ~1 giorno (7 file, ~360 LOC test)
**Dipendenze**: Nessuna — usa mock, no Docker

---

### FASE 3: Health Endpoints uniformi (→ 9.7) — Priorità MEDIA
> *Quick win, 30 min per servizio*

**Servizi senza `/health`:**
- [ ] `api_pattern_weavers`
- [ ] `api_neural_engine`
- [ ] `api_embedding`
- [ ] `api_codex_hunters`
- [ ] `api_edge_oculus_prime`

**Pattern standard** (copiare da api_memory_orders):
```python
@router.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "version": VERSION}
```

**Test**: `tests/integration/test_health_endpoints.py` — verifica che tutti i servizi espongano `/health` con schema corretto.

**Effort**: ~2h (5 endpoint + 1 test file)

---

### FASE 4: Contract Enforcement strict (→ 9.9) — Priorità MEDIA
> *Architetturalmente importante, ma il sistema funziona anche senza*

**Task:**
- [ ] **CONTRACT-01**: Aggiungere flag `ENFORCE_CONTRACTS` (env var)
  - `"warn"` (default, comportamento attuale) → logga violazioni
  - `"strict"` → alza `ContractViolationError`
  - `"off"` → disabilitato (performance mode)
- [ ] **CONTRACT-02**: Creare `tests/contracts/test_vertical_conformance.py`
  - Verifica che `vertical_manifest.yaml` sia valido
  - Verifica che i contracts dichiarati siano importabili
  - Verifica che le routes dichiarate esistano
- [ ] **CONTRACT-03**: Validazione event payload in bus_adapter
  - Prima di emettere su StreamBus, validare payload contro schema Pydantic
  - Solo in mode `strict` (no overhead in produzione)

**Effort**: ~4h (flag + 2 test file + validation middleware)

---

### FASE 5: Type Safety progressiva (→ 10.0) — Priorità BASSA
> *Valore a lungo termine, non urgente*

**Strategia graduale (non rompere nulla):**

1. `mypy --strict vitruvyan_core/contracts/` — i contratti DEVONO essere 100% tipizzati
2. `mypy vitruvyan_core/core/agents/` — gli agent sono boundary critico
3. `mypy vitruvyan_core/core/synaptic_conclave/` — il bus è infrastruttura core
4. Espandere gradualmente con `[[tool.mypy.overrides]]` per modulo

**Configurazione target** (pyproject.toml):
```toml
[[tool.mypy.overrides]]
module = "vitruvyan_core.contracts.*"
disallow_untyped_defs = true          # Contratti: strict

[[tool.mypy.overrides]]
module = "vitruvyan_core.core.agents.*"
disallow_untyped_defs = true          # Agents: strict
```

**Effort**: ~1 giorno per modulo (type annotations + fix)

---

## Nota su Jenkins & Update System

**Jenkins**: Appena installato, in fase di apprendimento. Le task CI (FASE 1) dipendono dalla stabilizzazione del Jenkins pipeline. Nel frattempo, i pre-commit hooks e il Makefile garantiscono quality gate locale.

**Update Manager (`vit` CLI)**: Sistema ancora instabile. Va stabilizzato prima di integrare i flussi CI/CD di rilascio automatico. Non blocca nessuna delle FASI sopra.

---

## Score projection

| Fase | Score | Stato |
|------|-------|-------|
| Baseline (architettura + import sweep) | 8.5 | ✅ |
| DX + Docker hardening (oggi) | 8.8 | ✅ |
| FASE 1: CI quality gate | 9.0 | ⏳ Dipende da Jenkins |
| FASE 2: Integration tests | 9.5 | 📋 Ready |
| FASE 3: Health endpoints | 9.7 | 📋 Ready |
| FASE 4: Contract enforcement | 9.9 | 📋 Ready |
| FASE 5: Type safety | 10.0 | 📋 Graduale |
