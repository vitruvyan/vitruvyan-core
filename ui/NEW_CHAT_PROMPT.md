# Prompt per Nuova Chat - VEE Analysis System

## Contesto Sistema

**Architettura:**
- Backend: Python 3.12, LangGraph state machine (vitruvyan repo), Docker Compose
- Frontend: Next.js 15.2.4, React 19, porta 3003 (vitruvyan-ui repo)
- API Endpoint: https://graph.vitruvyan.com/run (POST /run)
- Database: PostgreSQL (vitruvyan DB), Qdrant (port 6333), Redis (port 6379)
- Containers chiave:
  - `vitruvyan_api_graph` (porta 8004) - orchestratore LangGraph
  - `vitruvyan_memory_orders` (porta 8016) - dual-memory system (Archivarium+Mnemosyne)

**Stato Attuale:**
- Backend: Funzionante dopo fix recenti (30 Nov 2025, ore 21:41)
- Frontend: Next.js server attivo su http://localhost:3003 (PID 3215764)
- Git: Frontend su commit 80ecb6e (include integrazione ChatGPT)

---

## Problema Risolto

**Sintomo originale:**
VEE analysis non appariva nel frontend - schermo bianco dopo ricerca ticker. Sistema entrava in loop di slot filler chiedendo budget invece di mostrare analisi.

**Root Cause Identificate:**

1. **Bug routing in `quality_check_node.py` (linea 334)**
   - File: `/home/caravaggio/vitruvyan/core/langgraph/node/quality_check_node.py`
   - Problema: Usava `state["error"] = "Data not available yet"` per gestire fallback PostgreSQL
   - Effetto: Il campo `error` triggherava `should_trigger_codex_expedition()` in `codex_trigger.py` (linee 272-276)
   - Risultato: Routing a `codex_expedition` invece di `compose`/`dispatcher_exec`, bypassando logica `validated_tickers`
   - **FIX APPLICATO:** Cambiato a `state["warning"] = "Data not available yet"` per evitare trigger Codex

2. **Container crash `vitruvyan_memory_orders`**
   - File: `/home/caravaggio/vitruvyan/docker/dockerfiles/Dockerfile.api_memory_orders`
   - Problema: `ModuleNotFoundError: No module named 'core.ledger'` - container restarting 10214+ volte
   - Causa: Commit abd6a263 (14 Nov) aggiunse RefactorManager→TronAgent (ledger integration) ma Dockerfile memory_orders non copiava modulo ledger
   - **FIX APPLICATO:** 
     - Aggiunto `COPY core/ledger /app/core/ledger` in Dockerfile
     - Aggiunto dipendenze Tron in `requirements.memory.txt`: `tronpy==0.4.0`, `eth-keys>=0.4.0`, `eth-utils>=2.0.0`
     - Rebuilded e restarted container (ora healthy)

**Test Eseguito (30 Nov, 21:41):**
\`\`\`bash
curl -X POST http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text": "analizza MSFT", "user_id": "test_user", "validated_tickers": ["MSFT"]}'
\`\`\`

**Risultato:**
✅ `"route": "compose"` (NON "codex_expedition")  
✅ `"action": "answer"` (NON "clarify")  
✅ Analisi eseguita con `numerical_panel`, `vee_explanations`, `explainability`  
⚠️ Minor bug: `'momentum_z'` KeyError in VEE explanation generation (non blocking)

---

## Issue Pendenti

### 1. ChatGPT API Loop (PRIORITÀ ALTA)

**Sintomo:**
Frontend logs mostrano chiamate ripetute a `/api/generate-vee` ogni 1-3 secondi in apparente loop infinito:
\`\`\`
POST /api/generate-vee 200 in 240ms
POST /api/generate-vee 200 in 1834ms
POST /api/generate-vee 200 in 3627ms
...
\`\`\`

**File Coinvolti:**
- `/home/caravaggio/vitruvyan/vitruvyan-ui/app/api/generate-vee/route.js` (creato in commit 4614637)
- `/home/caravaggio/vitruvyan/vitruvyan-ui/components/chat.jsx` (linee 632-704: handleApiRequest)

**Action Required:**
1. Ispezionare `app/api/generate-vee/route.js` per logic loop
2. Verificare `chat.jsx` per useEffect dependencies o chiamate uncontrolled
3. Opzioni:
   - Aggiungere conditional guards o debouncing
   - Rimuovere integrazione ChatGPT se non necessaria
   - Reset frontend a commit 6a56a88 (prima di commit ChatGPT 4614637)

**Git Timeline (per reference):**
\`\`\`
fdcc8b5 → 6a56a88 (VEE backend spec) → 4614637 (ChatGPT VEE) → 80ecb6e (Mercator logo, CURRENT)
\`\`\`

### 2. VEE Explanation Generation Bug (PRIORITÀ MEDIA)

**Sintomo:**
Response backend include errore in `vee_explanations`:
\`\`\`json
"summary": "Error in explanation generation for MSFT: 'momentum_z'"
\`\`\`

**Context:**
- Analisi numerica funziona (`numerical_panel` populated correttamente)
- Errore solo in layer explainability/VEE generation
- Possibile KeyError nel template o data mapping

**Action Required:**
1. Trovare file che genera `vee_explanations` (probabile: `compose_node.py` o modulo VEE dedicato)
2. Cercare KeyError `'momentum_z'` in try/except blocks
3. Verificare mapping tra `numerical_panel` fields e VEE template variables

### 3. Frontend Rendering Validation (PRIORITÀ BASSA)

**Action Required:**
- Test completo UI: http://localhost:3003
- Query test: "analizza MSFT" o "show me AAPL analysis"
- Verificare `ComposeNodeUI` rendering di `narrative` e `vee_explanations`
- Controllare console browser per errori React
- Verificare deprecation `VEEMultiLevelAccordion` non causa issues

---

## File Modificati (Ready for Git Commit)

**Backend (repo vitruvyan):**
1. `/home/caravaggio/vitruvyan/core/langgraph/node/quality_check_node.py`
   - Linea 334: `state["error"]` → `state["warning"]`

2. `/home/caravaggio/vitruvyan/docker/dockerfiles/Dockerfile.api_memory_orders`
   - Aggiunto: `COPY core/ledger /app/core/ledger`

3. `/home/caravaggio/vitruvyan/docker/requirements/requirements.memory.txt`
   - Aggiunte dipendenze Tron: `tronpy==0.4.0`, `eth-keys>=0.4.0`, `eth-utils>=2.0.0`

**Frontend (repo vitruvyan-ui):**
- Nessuna modifica applicata (git status clean su commit 80ecb6e)

---

## File da Ispezionare

**Per ChatGPT Loop Fix:**
1. `/home/caravaggio/vitruvyan/vitruvyan-ui/app/api/generate-vee/route.js`
   - Creato in commit 4614637 "feat: ChatGPT VEE generation via Next.js API"
   - Verificare loop logic, error handling, conditional guards

2. `/home/caravaggio/vitruvyan/vitruvyan-ui/components/chat.jsx`
   - Linee 632-704: `handleApiRequest()` function
   - Verificare useEffect dependencies, state updates che potrebbero triggherare re-calls

**Per VEE Bug Fix:**
1. Backend LangGraph nodes:
   - `/home/caravaggio/vitruvyan/core/langgraph/node/compose_node.py`
   - Cercare generate VEE explanations logic
   - Ispezionare KeyError handling per `momentum_z` e altri fields

2. VEE Templates/Generators:
   - Cercare file con "vee_explanations" o "explainability" generation
   - Verificare mapping tra `numerical_panel` e explanation templates

**Per Routing Logic (Reference, già funzionante):**
1. `/home/caravaggio/vitruvyan/core/langgraph/node/route_node.py`
   - Linee 21-30: Codex trigger check (runs BEFORE validated_tickers)
   - Linee 77-81: validated_tickers bypass logic
   - Note: Order matters - Codex check preempts ticker-based routing if error present

2. `/home/caravaggio/vitruvyan/core/langgraph/codex_trigger.py`
   - Linee 272-276: `should_trigger_codex_expedition()` function
   - Checks `state["error"]` field to trigger healing mode

---

## Comandi Utili

**Test Backend:**
\`\`\`bash
# Test con validated_tickers (bypass slot filler)
curl -X POST http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "analizza AAPL",
    "user_id": "test_user",
    "validated_tickers": ["AAPL"]
  }' | jq '.route, .action, .numerical_panel[0].ticker'

# Health check containers
docker ps --filter name=vitruvyan_api_graph --filter name=vitruvyan_memory_orders
docker logs vitruvyan_api_graph --tail 50
docker logs vitruvyan_memory_orders --tail 50
\`\`\`

**Frontend:**
\`\`\`bash
# Server già attivo su porta 3003 (PID 3215764)
# Per restart se necessario:
cd /home/caravaggio/vitruvyan/vitruvyan-ui
pkill -f "next dev"
pnpm dev

# Check API loop in logs
curl http://localhost:3003 >/dev/null 2>&1 && echo "Frontend active"
\`\`\`

**Git Operations:**
\`\`\`bash
# Frontend - reset a pre-ChatGPT se necessario
cd /home/caravaggio/vitruvyan/vitruvyan-ui
git log --oneline | grep -B 2 "4614637"  # trova commit parent
git reset --hard 6a56a88  # commit prima di ChatGPT integration

# Backend - commit fixes
cd /home/caravaggio/vitruvyan
git status
git add core/langgraph/node/quality_check_node.py \
        docker/dockerfiles/Dockerfile.api_memory_orders \
        docker/requirements/requirements.memory.txt
git commit -m "fix: quality_check warning + memory_orders ledger module"
\`\`\`

---

## Prompt Suggerito per Nuova Chat

\`\`\`
Ho un sistema VEE analysis (backend LangGraph + frontend Next.js) che presentava bug routing causando loop di slot filler invece di mostrare analisi.

**Fix già applicati (30 Nov 2025):**
1. Backend: Cambiato `state["error"]` → `state["warning"]` in quality_check_node.py linea 334 per evitare trigger Codex
2. Container: Fixato vitruvyan_memory_orders aggiungendo core/ledger module in Dockerfile
3. Test: Backend routing funziona correttamente (route=compose, action=answer)

**Issue pendenti da fixare:**
1. ChatGPT API loop: `/api/generate-vee` chiamato ripetutamente ogni 1-3sec
   - File: app/api/generate-vee/route.js (commit 4614637)
   - Possibili cause: useEffect dependencies in chat.jsx o logic loop in route handler
   
2. VEE explanation bug: KeyError 'momentum_z' in generation
   - Analisi numerica funziona, errore solo in explainability layer
   - File da ispezionare: compose_node.py o VEE generator modules

**Obiettivo:**
Fixare ChatGPT loop (priorità alta) e VEE explanation bug (priorità media), poi validare rendering frontend completo.

**Domanda iniziale:**
Puoi aiutarmi a debuggare il loop /api/generate-vee? Vorrei capire cosa triggera le chiamate ripetute e aggiungere guards appropriati.
\`\`\`

---

## Note Tecniche

**Validated Tickers Flow:**
- Frontend: `chat.jsx` (handleApiRequest) → `apiClient.ts` (runGraph) → Backend POST /run
- Backend: `route_node.py` checks `validated_tickers` in state
- If present: route="dispatcher_exec" (bypass slot_filler)
- BUT: Codex check (lines 21-30) runs BEFORE validated_tickers check (lines 77-81)
- Therefore: Error field preempts ticker-based routing

**Error vs Warning Semantics:**
- `state["error"]`: System error requiring Codex Hunters healing intervention
- `state["warning"]`: Temporary condition (e.g., PostgreSQL fallback), non-critical
- Quality check "Data not available yet" is warning, not error (CrewAI background job pending)

**Container Health Endpoints:**
- Memory Orders: `curl http://localhost:8016/health/memory`
- API Graph: `curl http://localhost:8004/health`

**LangGraph State Machine Key Nodes:**
1. `route_node.py`: Decision router (Codex check → validated_tickers → intent-based routing)
2. `quality_check_node.py`: Validates Neural Engine output, handles PostgreSQL fallback
3. `compose_node.py`: Generates final narrative + VEE explanations
4. `codex_trigger.py`: Determines if Codex Hunters expedition needed

---

## Timeline Recap

- **14 Nov 2025**: Commit abd6a263 aggiunge RefactorManager→TronAgent (ledger integration)
- **14 Nov 2025**: Commit 0a202cb2 fixa api_graph Dockerfile (aggiunge core/ledger)
- **27 Oct 2025**: Commit d1486a03 crea quality_check_node.py (consolidation)
- **Before**: quality_check usava `state["error"]` per "Data not available yet"
- **30 Nov 2025 ~20:00**: User nota VEE analysis blank, slot filler loop
- **30 Nov 2025 ~21:00**: Debugging identifica root causes (quality_check error + memory_orders crash)
- **30 Nov 2025 21:30**: Fix applicati, containers restarted
- **30 Nov 2025 21:41**: Test curl conferma fix funzionante (route=compose, action=answer)
- **30 Nov 2025 21:45**: Recap completato per nuova chat

---

**Pronto per nuova chat pulita con contesto essenziale e action items chiari.**
