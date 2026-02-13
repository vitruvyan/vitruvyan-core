# Orthodoxy Wardens

<p class="kb-subtitle">Tribunale epistemico: findings, verdetti, piani di correzione (advisory) e direttive di audit.</p>

Orthodoxy Wardens è il **tribunale di governance epistemica**: audita eventi/output, produce findings, rende verdetti e dichiara cosa va loggato o corretto.

## Mappa del codice

- **LIVELLO 1 (governance pura, niente I/O)**: `vitruvyan_core/core/governance/orthodoxy_wardens/`
  - Consumers (Sacred Roles): `consumers/confessor.py`, `consumers/inquisitor.py`, `consumers/penitent.py`, `consumers/chronicler.py`
  - Helper analisi statica: `consumers/code_analyzer.py`
  - Verdict engine: `governance/verdict_engine.py`
  - Oggetti dominio: `domain/*` (Confession, Finding, Verdict, …)
  - Schema eventi: `events/orthodoxy_events.py`
- **Agenti di automazione (purity mista / legacy)**: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/*_agent.py`
  - `confessor_agent.py` (LangGraph “Autonomous Audit Agent”, usa LLM + tools)
  - `inquisitor_agent.py` (`ComplianceValidator`, pattern scan + opzionale controllo semantico LLM)
  - `penitent_agent.py` (`AutoCorrector`, esegue azioni correttive; usa system tools)
- **LIVELLO 2 (service + adapters)**: `services/api_orthodoxy_wardens/`

## Pipeline (interno)

Come in `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/README.md`:

1. `Confessor.process(event)` → `Confession`
2. `Inquisitor.process({confession, text, code})` → `InquisitorResult(findings=...)`
3. `VerdictEngine.render(findings)` → `Verdict`
4. `Penitent.process(verdict)` → `CorrectionPlan` *(solo advisory)*
5. `Chronicler.process(verdict)` → `ChronicleDecision` *(direttive log/archive; nessuna persistenza)*

---

## Sacred Roles (LIVELLO 1, puri)

### `Confessor` — intake officer (raw → caso strutturato)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/confessor.py`
- Funzioni:
  - accetta `OrthodoxyEvent` o dict
  - mappa `event_type` → `trigger_type`, `scope`, `urgency`
  - produce una `Confession` “frozen” (caso strutturato; `confession_id` è unico, non deterministico)

**Dettagli implementativi**:

- mapping tabelle per `event_type`:
  - `_EVENT_TO_TRIGGER`, `_EVENT_TO_SCOPE`, `_EVENT_TO_URGENCY` (con default)
- input dict:
  - `metadata` viene convertito in `tuple(...)` per immutabilità
- generazione ID:
  - `confession_<timestamp>_<uuid>` (unico per ogni intake)

### `Inquisitor` — examiner (caso → findings)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/inquisitor.py`
- Funzioni:
  - applica regole e classificatori per produrre `Finding`
  - combina:
    - `PatternClassifier` (testo)
    - `ASTClassifier` (codice; opzionale, warning su `SyntaxError`)
  - produce `InquisitorResult` (immutabile)

**Dettagli implementativi**:

- input:
  - dict `{confession, text, code}` oppure una `Confession` (esamina `metadata` come testo)
- output:
  - `InquisitorResult(findings=tuple[Finding, ...], rules_applied=int, text_examined=bool, code_examined=bool)`

### `Penitent` — correction advisor (verdetto → piano correzione)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/penitent.py`
- Funzioni:
  - trasforma un `Verdict` in un `CorrectionPlan`
  - non esegue mai correzioni (il service decide)

**Dettagli implementativi**:

- selezione strategia rule-based (categoria → strategy; severity → priority)
- revisione umana richiesta per:
  - categoria in `{security, architectural}` oppure severity `critical`

### `Chronicler` — logging strategist (verdetto → direttive archive)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/chronicler.py`
- Funzioni:
  - decide cosa loggare (`LogDecision`)
  - dichiara dove archiviare (`ArchiveDirective`: `postgresql`, `qdrant`, `blockchain`, `cognitive_bus`)
  - resta puro (niente I/O)

**Dettagli implementativi**:

- destinazioni di archiviazione da `verdict.status`:
  - `heretical` → tutte (include blockchain + broadcast su bus)
  - `purified` → `postgresql` + `qdrant` + `cognitive_bus`
  - `blessed` → solo `postgresql`
  - `non_liquet` → `postgresql` + `qdrant`

---

## Agente di supporto: `CodeAnalyzer` (analisi statica)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/code_analyzer.py`
- Funzioni:
  - pattern di compliance, sicurezza, performance e qualità

---

## Agenti di automazione (purity mista / legacy)

Questi file vivono nella stessa cartella ma **non sono LIVELLO 1-puri** (usano LLM e/o system tools). Considerali “automazione sperimentale” da migrare dietro adapter LIVELLO 2.

### `AutonomousAuditAgent` (LangGraph)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/confessor_agent.py`
- Cosa fa:
  - orchestra un workflow di audit come grafo (LangGraph)
  - usa il gateway LLM centralizzato (`core/agents/llm_agent.py`)
  - compone `CodeAnalyzer` + `ComplianceValidator` + `AutoCorrector`
- Nota:
  - il file stesso dichiara la violazione di purity (tool I/O da iniettare/configurare nel LIVELLO 2)

### `ComplianceValidator` (pattern scan + opzionale LLM)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/inquisitor_agent.py`
- Cosa fa:
  - stage 1: regex/pattern scan (linguaggio prescrittivo / claim non supportati / problemi disclaimer)
  - stage 2: opzionale validazione semantica LLM per ridurre falsi positivi
- Dove si usa:
  - gate di compliance prima di inviare output/narrative a utenti finali (finanza)

### `AutoCorrector` (esegue correzioni)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/penitent_agent.py`
- Cosa fa:
  - esegue azioni correttive (es. restart container, cleanup disco, rewrite testo compliance)
  - include concetti di rollback e safety check operativi
