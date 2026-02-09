# Sacred Orders Refactoring - Architectural Vision
**Date**: February 9, 2026  
**Status**: Architectural Planning Phase  
**Commit**: d9ec283 (WIP: Orthodoxy Wardens partial refactoring)

---

## 🎯 Contesto

**Vitruvyan Core** è un **sistema operativo epistemico agnostico** progettato per implementare verticali domain-specific (finance, healthcare, research, etc.).

### Problema Attuale
Il sistema è nato come **fork da un verticale finance**, risultando in:
1. ❌ **Finance-specific code nel CORE** (ticker validation, OHLCV schemas, "buy now" compliance)
2. ❌ **Strutture disorganizzate** (servizi vanno da 1 file a 14 directory, senza pattern)
3. ❌ **Due livelli confusi** (foundational library vs Docker services non separati chiaramente)
4. ❌ **Nessun template replicabile** (ogni Sacred Order organizzato diversamente)

### Refusi da Eliminare
- Referenze a "ticker", "stock", "market", "OHLCV", "sentiment analysis"
- Compliance patterns finance-specific ("buy now", "sell now", "financial advice")
- Dataset validators per dati finanziari
- Service names legacy ("sentiment_enhanced", naming vertical-specific)

---

## 🏛️ Architettura Target: DUE LIVELLI

### **LIVELLO 1: vitruvyan_core/core/** (Foundational Library)
**Scopo**: Libreria Python riutilizzabile, logica business agnostica, importabile da verticali

**Caratteristiche**:
- Codice **domain-agnostic** (nessun riferimento a verticali specifici)
- Agenti, workflows, contracts **generici**
- Importabile da qualsiasi verticale (`from core.governance.orthodoxy_wardens import Agent`)
- Testing robusto (unit + integration tests)

**Esempio**: `vitruvyan_core/core/governance/orthodoxy_wardens/`
- **Cosa fa**: Audit generico sistema (eventi, logs, code quality, security)
- **Cosa NON fa**: Validazione ticker, financial compliance, OHLCV checks

---

### **LIVELLO 2: services/** (Docker Microservices)
**Scopo**: Applicazioni FastAPI per orchestration, thin layer su foundational library

**Caratteristiche**:
- **Orchestrator** (non business logic)
- Dependency injection su agenti foundational
- API endpoints (HTTP REST)
- Synaptic Conclave listeners (Cognitive Bus integration)
- Config service-specific (rate limits, auth, logging)

**Esempio**: `services/governance/api_orthodoxy_wardens/`
- **Cosa fa**: Espone API HTTP per audit, gestisce richieste utente, coordina agenti foundational
- **Cosa NON fa**: Implementare audit logic (chiama foundational library)

---

## 📁 Pattern Strutturale TARGET

### **LIVELLO 1 - Foundational (6-7 directory)**

```
<sacred_order_name>/
├── agents/           ← CrewAI agents, business logic actors
├── core/             ← Workflows, orchestration, business rules (NON-agent code)
├── monitoring/       ← Health checks, metrics, observers
├── utils/            ← Utilities generiche (docker, git, formatters)
├── tests/            ← Unit tests (pytest)
├── docs/             ← Documentation, ADRs, guides
│   ├── README.md
│   ├── GUIDE.md
│   └── examples/     ← Usage examples (Python scripts)
└── README.md
```

**Directory opzionali** (solo se necessario):
- `models/` - Pydantic schemas (se eventi Cognitive Bus custom)
- `scripts/` - Operational scripts (shell, deployment)

**Eliminiamo** (non servono nel foundational):
- ❌ `api/` (solo in services)
- ❌ `db/` (usiamo PostgresAgent/QdrantAgent centralizzati)
- ❌ `clients/` (troppo specifico, va in Synaptic Conclave se serve)
- ❌ `transport/` (già in Synaptic Conclave)
- ❌ `listeners/` (va in `monitoring/`)
- ❌ `philosophy/` (va in `docs/`)
- ❌ `plasticity/` (feature-specific, non generalizzabile)

---

### **LIVELLO 2 - Services (6-8 directory)**

```
api_<sacred_order_name>/
├── api/              ← FastAPI routes (thin orchestrator)
├── core/             ← Service-specific initialization, DI setup
├── models/           ← Request/Response Pydantic schemas (API-specific)
├── monitoring/       ← Health endpoints + Synaptic listeners
├── utils/            ← Config, logging setup
├── docs/             ← API documentation
├── examples/         ← Usage examples (curl, client scripts)
└── main.py           ← FastAPI app entry point (<200 lines TARGET)
```

**Directory opzionali**:
- `governance/` - Service-level policies (rate limits, auth rules)

**Eliminiamo** (già nel foundational o non servono):
- ❌ `agents/` (già in foundational, importiamo)
- ❌ `tests/` (opzionale, test foundational è più importante)
- ❌ `db/` (usiamo foundational db managers)

---

## 🧹 CLEANUP OPERATIONS

### **FASE 1: Audit Finance-Specific Code**
Per ogni file in `vitruvyan_core/core/governance/`:
1. **Grep finance terms**: `financial|ticker|stock|OHLC|sentiment|market|price|buy|sell`
2. **Classificare**:
   - ❌ **ELIMINARE**: 100% finance-specific (schema_validator.py)
   - ⚠️ **RIPULIRE**: Parti generiche + parti finance (code_analyzer.py, inquisitor_agent.py)
   - ✅ **MANTENERE**: Già agnostico (git_monitor.py, docker_manager.py)

### **FASE 2: Restructure Foundational**
Per ogni Sacred Order in `vitruvyan_core/core/governance/`:
1. Creare struttura 6-7 directory
2. Spostare file puliti nelle directory corrette:
   - Agents → `agents/`
   - Business logic → `core/`
   - Utilities → `utils/`
   - Health → `monitoring/`
3. Update imports
4. Validare tests passano

### **FASE 3: Restructure Services**
Per ogni servizio in `services/governance/` e `services/core/`:
1. Creare struttura 6-8 directory
2. Estrarre routes → `api/`
3. Estrarre orchestration → `core/`
4. Estrarre listeners → `monitoring/`
5. Ridurre `main.py` < 200 lines
6. Test Docker rebuild

### **FASE 4: Deprecation**
1. Rimuovere `services/core/api_orthodoxy_wardens/` (old location)
2. Consolidare in `services/governance/api_orthodoxy_wardens/`

---

## 🎯 Obiettivo Finale

### **Success Criteria**
- [ ] **CORE agnostico**: Zero finance-specific code in `vitruvyan_core/core/governance/`
- [ ] **Pattern uniforme**: Tutti i Sacred Orders seguono struttura 6-7 dir (foundational) + 6-8 dir (services)
- [ ] **Template documentato**: `SACRED_ORDERS_REFACTORING_TEMPLATE.md` pronto per replicare
- [ ] **Orthodoxy completo**: Primo Sacred Order completamente refactored (riferimento per altri)
- [ ] **Tutti i Sacred Orders refactored**: Codex, Memory, Vault, Pattern, Babel applicano pattern

### **Metriche**
- **Foundational**: 6-7 directory standard, <15 file per ordine (media)
- **Services**: main.py <200 lines, API routes separate, monitoring isolato
- **Code quality**: 0 finance references in core, 100% test coverage maintained

### **Timeline Stimata**
- **FASE 1** (Audit): 2-3h (tutti i Sacred Orders)
- **FASE 2** (Foundational restructure): 1-2h per ordine × 5 = 5-10h
- **FASE 3** (Services restructure): 1-2h per servizio × 6 = 6-12h
- **FASE 4** (Deprecation + docs): 2h
- **TOTALE**: 15-27h

---

## 📝 Prossimi Passi Immediati

### **STEP 1: Validate Vision** (10 min)
- [ ] Review questo documento con il team
- [ ] Confermare pattern 6-7 directory foundational + 6-8 directory services
- [ ] Confermare eliminazione completa finance-specific code

### **STEP 2: Complete Orthodoxy Audit** (1h)
- [ ] Audit completo file per file di `vitruvyan_core/core/governance/orthodoxy_wardens/`
- [ ] Classificare ogni file: ELIMINARE / RIPULIRE / MANTENERE
- [ ] Creare `ORTHODOXY_CLEANUP_PLAN.md` con dettaglio azioni

### **STEP 3: Execute Orthodoxy Cleanup** (2-3h)
- [ ] Eliminare file 100% finance-specific
- [ ] Ripulire file misti (mantenere solo parti generiche)
- [ ] Ristrutturare in 6-7 directory pattern
- [ ] Validare tests passano
- [ ] Commit: "refactor: Orthodoxy Wardens foundational cleanup (finance-agnostic)"

### **STEP 4: Complete Orthodoxy Service** (1-2h)
- [ ] Completare `services/governance/api_orthodoxy_wardens/` refactoring
- [ ] Tasks 1.6-1.8 rimasti (config, cleanup main.py <200 lines)
- [ ] Rimuovere `services/core/api_orthodoxy_wardens/` (deprecated)
- [ ] Test Docker rebuild
- [ ] Commit: "refactor: Orthodoxy Wardens service complete"

### **STEP 5: Document Template** (1h)
- [ ] Creare `SACRED_ORDERS_REFACTORING_TEMPLATE.md`
- [ ] Includere checklist replicabile
- [ ] Includere esempi directory mapping
- [ ] Commit: "docs: Sacred Orders refactoring template"

### **STEP 6: Replicate to Other Orders** (10-15h)
- [ ] Vault Keepers (pilot test del template)
- [ ] Codex Hunters
- [ ] Memory Orders
- [ ] Pattern Weavers (services/core/)
- [ ] Babel Gardens (services/core/)

---

## 🤝 Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| **6-7 directory foundational** | Balance clarity vs simplicity, avoid 14-dir overkill | Feb 9, 2026 |
| **No db/ directory** | Use centralized PostgresAgent/QdrantAgent | Feb 9, 2026 |
| **Services <200 lines main.py** | Force thin orchestrator pattern | Feb 9, 2026 |
| **Eliminate finance-specific** | Core must be domain-agnostic | Feb 9, 2026 |
| **Two-level architecture** | Clear separation library vs application | Feb 9, 2026 |

---

## ❓ Open Questions

1. **models/ directory**: Creare vuota per futuro, o solo quando serve eventi custom?
2. **examples/ vs scripts/**: Separati o dentro docs/?
3. **governance/ directory**: Solo in services, o anche in foundational?
4. **Testing strategy**: Test foundational sufficiente, o anche test services?

---

## 📚 References

- [Copilot Instructions](.github/copilot-instructions.md) - Sacred Orders epistemic hierarchy
- [Synaptic Conclave Architecture](.github/Vitruvyan_Appendix_L_Synaptic_Conclave.md) - Reference model
- [TODO Phase 4](TODO_ORTHODOXY_WARDENS_COMPLETION.md) - Original refactoring plan
- Commit d9ec283 - WIP checkpoint before architectural review
