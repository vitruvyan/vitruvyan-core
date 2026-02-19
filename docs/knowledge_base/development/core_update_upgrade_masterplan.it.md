# Masterplan Core Update/Upgrade 🚀

> **Ultimo aggiornamento**: 19 feb 2026 16:45 UTC  
> **Stato**: Approvato — Inizio Phase 0  
> **Comando CLI**: `vit update` / `vit upgrade`  
> **Architettura**: Ibrida (Library + CLI, built-in nel Core)

## Obiettivo 🎯

Definire un sistema di aggiornamento del Core Vitruvyan in stile distro:

- notifica quando un update è disponibile 🔔
- un comando unico per aggiornare ⚙️
- verifica compatibilità verticale prima e dopo l'upgrade ✅
- rollback automatico in caso di errore 🛟

Risultato atteso: **zero fork del Core tra i verticali** e update ripetibili.

## Decisioni Architetturali (Approvate) ✅

**Pattern**: Ibrido industry-standard (modello apt/pip/dnf)
- **Library**: `core.platform.update_manager.engine` (logica business, testabile)
- **CLI**: comando `vit` (interfaccia utente, built-in)
- **Distribuzione**: Package singolo (`pip install vitruvyan-core` include CLI)

**Location**: `vitruvyan_core/core/platform/update_manager/`
```
core/platform/update_manager/
├── engine/          # Library (compatibilità, planning, esecuzione)
│   ├── registry.py
│   ├── compatibility.py
│   ├── planner.py
│   └── executor.py
├── cli/             # CLI (comandi, formattatori)
│   ├── main.py
│   ├── commands/
│   └── formatters.py
└── tests/
```

**Comandi CLI** (stile apt, conciso):
- `vit update` = controlla aggiornamenti (come `apt update`)
- `vit upgrade` = applica upgrade (come `apt upgrade`)
- `vit plan` = mostra piano upgrade
- `vit rollback` = torna alla versione precedente
- `vit channel` = cambia canale stable/beta

**Versioning**:
- Git tags: `v1.0.0` (stable), `v1.1.0-beta.1` (beta)
- SemVer strict (MAJOR.MINOR.PATCH)
- Dual channel: `stable` (produzione), `beta` (early access)

## Stato Finale (End State) 🧭

Quando un team verticale esegue:

```bash
vitruvyan update check
vitruvyan update apply
```

la piattaforma deve:

1. rilevare l'ultima release del Core
2. validare compatibilita via manifest verticale + versione contracts
3. generare un piano upgrade (cosa cambia, rischi, test richiesti)
4. applicare upgrade in modalita transazionale
5. eseguire smoke test verticali
6. confermare l'upgrade oppure fare rollback automatico

## Principi Non Negoziabili 🧱

- I verticali importano solo da `contracts`, mai dagli internals Core.
- Nessuna release Core viene pubblicata senza compatibility checks.
- Ogni upgrade deve essere tracciabile via audit log e report.
- Le rotture contrattuali richiedono major version + deprecation policy.

## Architettura Logica 🏗️

Componenti principali:

- `Release Registry` (GitHub Releases API + metadata)
- `Compatibility Engine` (validazione versioni + parsing manifest)
- `Update Manager CLI` (comando `vit`)
- `Notification Engine` (check all'avvio + polling periodico)
- `Safety Layer` (snapshot git, smoke test, rollback)
- `Policy & Governance` (contracts, versioning, deprecazioni)

**Contract-Driven**: Tutte le interazioni governate da `UPDATE_SYSTEM_CONTRACT_V1.md`

### 1) Release Registry 📦

Fonte di verita delle release Core (inizio: GitHub Releases).

Metadati minimi per release:

- versione Core
- versione contracts supportata
- canale (`stable`, `canary`, `lts`)
- changelog machine-readable
- checksum artifact
- migration notes

### 2) Compatibility Engine 🧠

Legge:

- metadati release
- `vertical_manifest.yaml`

Produce:

- `compatible`
- `compatible_with_warnings`
- `blocked`

Motivi tipici di blocco:

- versione Core fuori range supportato
- mismatch contracts major
- capability richiesta non piu disponibile

### 3) Update Manager CLI 🛠️

**Comando**: `vit` (conciso, stile apt)

Comandi target:

- `vit update` — controlla aggiornamenti (sincronizza release registry)
- `vit upgrade` — applica upgrade (con validazione compatibilità)
- `vit plan` — mostra piano upgrade (cambiamenti, rischi, test)
- `vit rollback` — torna alla versione precedente
- `vit channel [stable|beta]` — cambia canale aggiornamenti
- `vit status` — mostra versione corrente + aggiornamenti disponibili

Comportamento minimo:

- output human-readable (tabelle, colori)
- exit code friendly per CI (0=success, 1=blocked, 2=error)
- modalità non interattiva (`--yes`) per automation
- output JSON (`--json`) per uso programmatico

### 4) Notification Engine 🔔

Canali minimi:

- notifica all'avvio servizio
- check periodico schedulato

Canali opzionali:

- Slack/Webhook
- dashboard interna

### 5) Safety Layer 🛡️

Durante `update apply`:

- snapshot dello stato corrente (commit/tag/deps/manifest)
- applica update
- esegue smoke suite minima
- se fallisce: rollback automatico + report

### 6) Policy & Governance 📜

- SemVer del Core
- versioning separato per Contracts
- policy deprecazioni con finestra supporto
- policy canali release (`stable/canary/lts`)

## Tracklist Implementativa 🧭

## Fase 0 - Fondazioni (Settimana 1) 🧱

Obiettivo: bloccare regole base e schema dati.

Task:

- **Creare contract**: `docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md`
  - Schema manifest (compliance verticale)
  - Interfaccia smoke test (exit code, timeout)
  - Policy versioning (SemVer, breaking changes)
  - Schema metadata release (formato JSON)
- **Estendere** `vertical_manifest.yaml` con campi compatibilità
- **Creare struttura directory**: `core/platform/update_manager/{engine,cli,tests}/`
- **Definire** matrice compatibilità iniziale (versione core → versione contracts)

Deliverable:

- `UPDATE_SYSTEM_CONTRACT_V1.md` (contract vincolante)
- Template `vertical_manifest.yaml` aggiornato
- Sample release metadata JSON
- Struttura codice scheletro (moduli vuoti con docstring)

Definition of Done:

- Contract approvato dal team platform
- Schema manifest validato (test pytest schema)
- Un verticale sample usa nuovo schema (esempio finance)
- Struttura directory creata + committata

## Fase 1 - Compatibility Engine (Settimana 2) 🧠

Obiettivo: bloccare upgrade rischiosi prima dell'apply.

Task:

- Implementare `engine/registry.py` (client GitHub Releases API)
- Implementare `engine/compatibility.py` (validazione range versioni, parsing SemVer)
- Implementare `engine/models.py` (dataclasses: Release, CompatibilityResult)
- Implementare `cli/commands/update.py` (comando `vit update`)
- Generare report compatibilità (formati testo + JSON)

Deliverable:

- Comando `vit update` funzionante
- Report compatibilità: `compatible`, `compatible_with_warnings`, `blocked`
- Modalità output JSON: `vit update --json`
- Unit test: `tests/test_compatibility.py` (coverage 100%)

Definition of Done:

- `vit update` mostra versione corrente + ultima disponibile
- Upgrade incompatibili bloccati con motivo esplicito
- Tutti gli unit test passano (pytest)
- Funziona con verticale sample (finance)

## Fase 2 - Apply + Rollback (Settimane 3-4) 🔁

Obiettivo: flusso di upgrade transazionale sicuro.

Task:

- Implementare `engine/planner.py` (generazione piano upgrade)
- Implementare `engine/executor.py` (git checkout, pip install, snapshot)
- Implementare `cli/commands/plan.py` (comando `vit plan`)
- Implementare `cli/commands/upgrade.py` (comando `vit upgrade`)
- Implementare `cli/commands/rollback.py` (comando `vit rollback`)
- Snapshot pre-upgrade (git tag: `pre-upgrade-<timestamp>`)
- Smoke test post-upgrade (chiama `smoke_tests/run.sh` del verticale)
- Rollback automatico su failure

Deliverable:

- Comando `vit upgrade` funzionante (flusso end-to-end)
- Comando `vit rollback` funzionante
- Audit log upgrade (`.vitruvyan/upgrade_history.json`)
- Test funzionali: `tests/test_cli.py` (scenari E2E)

Definition of Done:

- Upgrade compatibile si applica con successo + smoke test passano
- Smoke test falliti attivano rollback automatico
- Rollback ripristina stato precedente (git + dipendenze)
- Audit log registra tutti i tentativi di upgrade

## Fase 3 - CI/CD Gate (Settimana 5) 🚦

Obiettivo: impedire release Core che rompono verticali attive.

Task:

- pipeline CI di compatibilita multi-verticale
- regole gating su PR/release
- report compatibilita come artifact CI

Deliverable:

- pipeline CI aggiornata
- regola release-blocking attiva

Definition of Done:

- una release incompatibile viene bloccata automaticamente

## Fase 4 - Notification System (Settimana 6) 📣

Obiettivo: visibilita automatica degli update per i team.

Task:

- notifiche in `update check`
- notifiche schedulate periodiche
- (opzionale) webhook Slack

Deliverable:

- notifica locale + log
- configurazione canale notifiche

Definition of Done:

- i team verticali ricevono alert senza polling manuale

## Fase 5 - Hardening & Governance (Settimane 7-8) 🧰

Obiettivo: affidabilita production-grade.

Task:

- audit trail completo upgrade
- policy support window (N versioni supportate)
- test di resilienza rollback
- runbook incident per update falliti

Deliverable:

- runbook operativo
- checklist pre/post-upgrade
- dashboard stato versioni verticali (anche minima)

Definition of Done:

- processo upgrade ripetibile e auditabile in produzione

## Backlog Tecnico Minimo ✅

**Fase 0 (Fondazioni)**:
- [ ] Creare `UPDATE_SYSTEM_CONTRACT_V1.md`
- [ ] Estendere `vertical_manifest.yaml` (campi compatibilità)
- [ ] Definire schema `release_metadata.json`
- [ ] Creare struttura directory `core/platform/update_manager/`

**Fase 1 (Compatibility Engine)**:
- [ ] Implementare `engine/registry.py` (GitHub API)
- [ ] Implementare `engine/compatibility.py` (validazione versioni)
- [ ] Implementare comando `vit update`
- [ ] Generare report compatibilità JSON
- [ ] Unit test (logica compatibilità)

**Fase 2 (Apply + Rollback)**:
- [ ] Implementare `engine/planner.py` (piano upgrade)
- [ ] Implementare `engine/executor.py` (apply/rollback)
- [ ] Implementare comando `vit upgrade`
- [ ] Implementare comando `vit rollback`
- [ ] Creare template smoke test verticale
- [ ] Aggiungere audit logging upgrade

**Fase 3 (CI/CD Gate)**:
- [ ] Implementare gate compatibilità CI
- [ ] Matrice test multi-verticale
- [ ] Regole blocco release

**Fase 4 (Notifiche)**:
- [ ] Check update all'avvio
- [ ] Polling periodico (configurabile)
- [ ] Notifiche webhook (opzionale)

**Fase 5 (Hardening)**:
- [ ] Runbook operativo
- [ ] Test resilienza rollback
- [ ] Dashboard stato versioni

## Campi Manifest Richiesti (Target) 📄

```yaml
domain_name: "example"
domain_version: "0.1.0"
status: "active"

compatibility:
  min_core_version: "1.2.0"
  max_core_version: "1.4.x"
  contracts_major: 1
  update_channel: "stable" # stable|canary|lts

ownership:
  team: "domain-team"
  tech_lead: "name.surname"
  contact: "team@example.com"
```

## Flusso Operativo Standard (SOP) 🔄

**Workflow sviluppatore** (team verticale):

```bash
# 1. Controlla aggiornamenti
vit update
# Output: "Nuova versione v1.2.0 disponibile (corrente: v1.1.0)"
#         "Compatibilità: ✅ COMPATIBILE"

# 2. Rivedi piano upgrade
vit plan --target v1.2.0
# Output: changelog, contracts affetti, test richiesti

# 3. Applica upgrade
vit upgrade
# Piattaforma auto-esegue:
#   - Crea snapshot (git tag pre-upgrade-20260219-164500)
#   - Checkout v1.2.0
#   - Installa dipendenze
#   - Esegue smoke test
#   - Conferma O rollback

# 4. Verifica
vit status
# Output: "Core v1.2.0 (upgrade da v1.1.0 il 2026-02-19)"
```

**Flusso rollback** (se problemi trovati post-upgrade):
```bash
vit rollback
# Ripristina: stato git + dipendenze + entry audit log
```

## Rischi Principali & Mitigazioni ⚠️

- Rischio: il verticale importa internals Core invece dei contracts.
  Mitigazione: lint/policy CI che blocca import non autorizzati.

- Rischio: release metadata incompleti.
  Mitigazione: template metadata obbligatorio + validazione pre-release.

- Rischio: rollback non affidabile.
  Mitigazione: snapshot atomico + prove rollback periodiche.

## Ownership Consigliata 👥

- Team Platform/Core: release registry, contracts, update manager
- Team Verticali: manifest, smoke test, compliance verticale
- DevOps/SRE: CI gates, notifiche, observability, runbook

## KPI da Monitorare 📈

- upgrade riusciti (%)
- mean time to upgrade (MTTU)
- rollback rate (%)
- incompatibilita intercettate pre-deploy
- incident post-upgrade

## Ordine Rollout Raccomandato 🗺️

**Path MVP** (3 settimane, valore immediato):
1. **Fase 0** (Settimana 1): Fondazioni + contract
2. **Fase 1** (Settimana 1-2): `vit update` funzionante (check read-only)
3. **Fase 2** (Settimana 2-3): `vit upgrade` + `vit rollback` (test manuali)

**Hardening Produzione** (2-4 settimane aggiuntive):
4. **Fase 3** (Settimana 4): Gate CI (previene release che rompono)
5. **Fase 4** (Settimana 5): Notifiche (alert proattivi)
6. **Fase 5** (Settimana 6-7): Governance + runbook

Questa sequenza minimizza rischio architetturale prima dell'espansione verticali.

**Milestone quick-win**: Dopo Settimana 2, i team verticali possono eseguire `vit update` per controllare compatibilità (rete di sicurezza immediata, anche senza auto-apply).

---

## Progresso Implementazione 📊

> **Ultimo aggiornamento**: 19 feb 2026 18:30 UTC  
> **Fase Corrente**: Fase 1 (Compatibility Engine)  
> **Branch**: `feature/update-manager-vit-cli`

### ✅ Fase 0 Completata (19 feb 2026)

**Fondazioni + Contract**

- [x] Struttura directory creata: `vitruvyan_core/core/platform/update_manager/{engine,cli,tests}/`
- [x] Contract pubblicato: `docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md` (15 sezioni, vincolante)
  - [x] Emendamenti P0 applicati (semantica wildcard, path resolution, checksum, dirty tree, audit trail)
- [x] Template manifest esteso: `docs/contracts/verticals/templates/vertical_manifest.yaml`
- [x] Esempio verticale finance: `examples/verticals/finance/vertical_manifest.yaml` + smoke tests
- [x] Skeleton code: 13 moduli Python con docstring + stub NotImplementedError
- [x] Git commit: `089178e` (40 file, +4655/-257 righe)
- [x] Contract v1.0.1: `3afc2db` (conforme P0)

**Decisioni Chiave**:
- Comando CLI: `vit` (stile apt, conciso)
- Architettura: Ibrida (Library + CLI, built-in nel Core)
- Location: `vitruvyan_core/core/platform/update_manager/`
- Versioning: Git tags SemVer strict (`v1.0.0`, `v1.1.0-beta.1`)
- Canali: `stable` (produzione), `beta` (early access)

### ✅ Fase 1 Completata (19 feb 2026)

**Compatibility Engine — Check Read-Only**

Moduli implementati:

1. **engine/registry.py** (client API GitHub Releases)
   - `ReleaseRegistry.fetch_latest(channel)` → scarica ultima release da GitHub
   - `ReleaseRegistry.fetch_all(channel)` → scarica tutte le release (filtrate per canale)
   - `ReleaseRegistry.verify_checksum(release)` → verifica Git commit SHA
   - `ReleaseRegistry._parse_semver(version)` → parsing SemVer per ordinamento
   - Usa stdlib `urllib` (zero dipendenze esterne)
   - Supporto paginazione (100 release per richiesta)
   - Scarica asset `releases.json` da GitHub Release
   - Filtra per canale (`stable`, `beta`)
   - Ordina per SemVer (decrescente)

2. **engine/compatibility.py** (Matching versioni + validazione)
   - `CompatibilityChecker.check(current, target, manifest)` → valida compatibilità
   - `CompatibilityChecker._match_version(version, pattern, operator)` → confronto SemVer (`>=`, `<=`, `==`)
   - `CompatibilityChecker._match_wildcard(version, pattern)` → matching wildcard (`1.x.x` permissivo)
   - `CompatibilityChecker.parse_semver(version)` → parsing tuple SemVer
   - `CompatibilityChecker.check_contracts_major()` → validazione versione contracts
   - Blocca upgrade incompatibili (target < min o target > max)
   - Restituisce `CompatibilityResult` (bool compatible + blocking_reason)

3. **cli/commands/update.py** (comando `vit update`)
   - `cmd_update(args)` → logica comando principale
   - `get_current_version()` → rileva versione Core corrente (3 strategie: `__version__`, `git describe`, fallback)
   - `find_vertical_manifest()` → risale l'albero directory per trovare `vertical_manifest.yaml`
   - Mostra: versione corrente, ultima versione, data release, cambiamenti (breaking/features/fixes)
   - Check compatibilità con manifest verticale (se trovato)
   - Mostra URL guida migrazione
   - Next steps: `vit upgrade --channel stable`
   - Formato: output console human-readable (emoji, colori)

4. **cli/main.py** (entry point CLI)
   - Importa `register_update_command` da `commands/update.py`
   - Registra sottocomando `vit update` con argparse
   - Esegue pattern `args.func(args)` (dispatch comandi)
   - Logging configurato (livello INFO)
   - Comandi stub per Fase 2+ (upgrade, plan, rollback, channel, status)

5. **cli/formatters.py** (formattatori output)
   - `format_release_info(release)` → formatta oggetto Release per display
   - `format_compatibility_result(result)` → formatta CompatibilityResult
   - `OutputFormatter.color(text, color)` → output ANSI colorato

6. **pyproject.toml** (configurazione package)
   - Metadata progetto: name, version, description, authors, license
   - Dipendenze: pyyaml, pydantic, httpx, psycopg2, redis, qdrant-client, openai, langgraph
   - Dipendenze opzionali: dev (pytest, black, ruff, mypy), mcp (anthropic), monitoring (prometheus-client)
   - Entry point CLI: `vit = "vitruvyan_core.core.platform.update_manager.cli.main:cli_main"`
   - Configurazione setuptools: packages.find, pytest.ini_options
   - Configurazione tool: black, ruff, mypy

**Dettagli Implementazione**:
- **Zero breaking changes**: tutto il codice isolato in `core/platform/update_manager/`
- **Stdlib-first**: usa `urllib` (nessuna dipendenza `requests` ancora)
- **Error handling**: NetworkError per fallimenti API GitHub
- **Protezione timeout**: timeout 10 secondi per richieste di rete
- **Graceful degradation**: fallback a versione "unknown" se rilevamento fallisce
- **Vertical discovery**: risale da CWD a Git repo root cercando `vertical_manifest.yaml`

**Strategia Testing** (prossimo):
- Unit test: `tests/test_registry.py` (mock risposte API GitHub)
- Unit test: `tests/test_compatibility.py` (wildcard matching, confronto SemVer)
- Integration test: `tests/test_vit_update_e2e.py` (chiamata API GitHub reale)
- Test manuale: `pip install -e . && vit update --channel stable`

**Limitazioni Note** (Fase 1):
- Rilevamento versione corrente: fallback hardcoded a "unknown" se `__version__` e `git describe` falliscono
- Versione contracts: hardcoded a "1.0.0" (dovrebbe leggere da metadata Core in Fase 2)
- Nessun caching: API GitHub chiamata ad ogni `vit update` (aggiungere cache in Fase 2)
- Nessun rate limit handling: fallisce dopo 60 richieste/ora (non autenticato)
- Discovery manifest: si ferma a Git repo root (potrebbe supportare path custom)

### 🔜 Fase 2 Prossima (Settimana 3)

**Update Executor — Applica Upgrade**

Moduli da implementare:

1. **engine/planner.py** (`UpgradePlanner`)
   - Genera piano upgrade (cambiamenti, rischi, test)
   - Stima durata upgrade
   - Check breaking changes
   - Valida prerequisiti (working tree pulito, spazio disco sufficiente)

2. **engine/executor.py** (`UpgradeExecutor`)
   - Esegue transazione upgrade (git checkout, pip install)
   - Crea snapshot tag prima upgrade
   - Esegue smoke test verticale
   - Rollback su fallimento (ripristina snapshot)
   - Scrive entry audit log

3. **cli/commands/upgrade.py** (comando `vit upgrade`)
   - Conferma interattiva (mostra piano, chiede consenso)
   - Modalità non-interattiva (flag `--yes`)
   - Selezione versione target (`--target v1.2.0`)
   - Indicatori progresso (spinner, percentuale)
   - Report errori (diagnostica dettagliata)

4. **cli/commands/plan.py** (comando `vit plan`)
   - Mostra piano upgrade senza applicare
   - Risk assessment (breaking changes, complessità migrazione)
   - Preview smoke test (timeout, exit code)

5. **cli/commands/rollback.py** (comando `vit rollback`)
   - Ripristina versione precedente (snapshot tag)
   - Ripristina dipendenze (snapshot `requirements.txt`)
   - Aggiorna audit log

**Timeline**: Settimana 3 (20-26 feb 2026)

**Definition of Done**:
- `vit upgrade` funziona end-to-end (test manuali)
- `vit rollback` ripristina versione precedente
- Smoke test eseguiti automaticamente dopo upgrade
- Audit log creato (`.vitruvyan/upgrade_history.json`)
- Integration test passano (API GitHub mockato)

### 🔜 Fase 3-5 (Settimane 4-7)

**Gate CI, Notifiche, Governance** (vedi sezioni Masterplan sopra)

---

### ✅ Phase 2 Completata (19 Feb 2026)

**Update Executor — Applicazione Upgrade con Rollback**

Moduli implementati:

1. **engine/planner.py** (UpgradePlanner)
   - `plan(from, to, release, manifest_path)` → genera UpgradePlan
   - `validate_prerequisites()` → blocca su working tree sporco (contratto P0)
   - `_check_clean_working_tree()` → `git diff-index --quiet HEAD --`
   - `_check_disk_space()` → richiede minimo 100MB
   - `_determine_tests(manifest_path)` → scopre smoke test verticali
   - `_estimate_downtime(breaking, tests)` → base 30s + test 60s/test + buffer 20%
   - **PrerequisiteError**: sollevata con tree sporco o spazio insufficiente

2. **engine/executor.py** (UpgradeExecutor)
   - `apply(plan, manifest_path)` → esegue transazione di upgrade completa
   - `rollback()` → ripristina a tag snapshot
   - `create_snapshot()` → crea Git tag `pre-upgrade-YYYYMMDD-HHMMSS`
   - `run_smoke_tests(manifest_path)` → esegue `<vertical_root>/smoke_tests/run.sh`
   - `_write_audit_log()` → scrive in `.vitruvyan/upgrade_history.json` (contratto P0)
   - `_checkout_version(version)` → `git checkout v{version}`
   - `_get_audit_log_path()` → risolve a radice repo Git (contratto P0)
   - **Auto-rollback**: attivato al fallimento smoke test o qualsiasi eccezione

3. **cli/commands/upgrade.py** (comando `vit upgrade`)
   - **Workflow interattivo**:
     1. Recupera release target da GitHub (latest o `--target`)
     2. Controllo compatibilità con manifest verticale
     3. Genera piano di upgrade (planner)
     4. Mostra piano: modifiche (breaking/features/fixes), stima downtime, smoke test
     5. Richiesta conferma (salta con `--yes`)
     6. Esegue upgrade (executor)
     7. Mostra tag snapshot per rollback
   - **Flag**: `--channel stable|beta`, `--target VERSION`, `--yes`
   - **Codici di uscita**: 0 = successo, 1 = errore/rollback

4. **cli/commands/plan.py** (comando `vit plan`)
   - Mostra piano di upgrade senza applicarlo
   - **Sezioni**:
     - Timeline: stima downtime + strategia rollback
     - Modifiche: breaking/features/fixes (limite 5 ciascuno per leggibilità)
     - Smoke test: elenca tutti i test scoperti
     - Valutazione rischio: HIGH/MEDIUM/LOW (basata su modifiche breaking + test)
   - Next steps: suggerisce comando `vit upgrade`
   - **Arg richiesto**: `--target VERSION`

5. **cli/commands/rollback.py** (comando `vit rollback`)
   - Ripristina all'ultimo snapshot di upgrade
   - Legge tag snapshot da `.vitruvyan/upgrade_history.json`
   - Richiesta conferma
   - Esegue `git checkout {snapshot_tag}`
   - Verifica con `git describe --tags`

6. **cli/main.py** (orchestrazione CLI)
   - Registrati comandi `upgrade`, `plan`, `rollback`
   - Aggiornati import e testi di aiuto
   - Marker completamento Phase 2

**Dettagli Implementativi**:
- **Conformità contratto P0**:
  - Blocco tree sporco: tolleranza zero (no override `--force`)
  - Posizione audit log: radice repo Git `.vitruvyan/upgrade_history.json`
  - Tag snapshot: formato `pre-upgrade-YYYYMMDD-HHMMSS`
- **Smoke test**:
  - Posizione: `<vertical_root>/smoke_tests/run.sh` (contratto P0)
  - Timeout: da manifest `smoke_tests_timeout` (default 180s)
  - Codici uscita: 0 = pass, 1 = fail, 2 = error
  - Auto-rollback al fallimento
- **Formato audit log**:
  ```json
  {
    "upgrades": [
      {
        "timestamp": "2026-02-19T18:30:00",
        "from_version": "1.0.0",
        "to_version": "1.2.0",
        "snapshot_tag": "pre-upgrade-20260219-183000",
        "success": true
      }
    ]
  }
  ```
- **Degradazione graziosa**:
  - Controllo spazio disco: non bloccante (solo warning)
  - Nessuno smoke test: non bloccante (warning: "upgrade rischioso")
  - Ultima versione sconosciuta: mostra warning, consente prosecuzione

**Limitazioni Note (Phase 2)**:
- **pip install saltato**: Richiede gestione venv Python (Phase 3)
- **Snapshot requirements.txt**: Non implementato (Phase 3)
- **Nessun comando channel**: Cambio canali non ancora implementato
- **Nessun comando status**: Versione corrente + riepilogo aggiornamenti non ancora implementato
- **Solo Git**: Assume repository Git (nessun supporto tarball ancora)

**Test Eseguiti**:
- ✅ Test manuale: `vit upgrade --help` (parsing argomenti)
- ✅ Test manuale: `vit plan --help` (parsing argomenti)
- ✅ Test manuale: `vit rollback --help` (parsing argomenti)
- ✅ Validazione prerequisiti: rilevamento tree sporco
- ✅ Creazione snapshot: formato tag `pre-upgrade-*`
- ✅ Audit log: scrittura/lettura JSON
- ⚠️ Upgrade end-to-end: richiede release GitHub (Phase 3)

**Modifiche File** (commit `cfb2169`):
- 6 file modificati, +1049/-47 righe
- File nuovi: `upgrade.py`, `plan.py`, `rollback.py`
- Modificati: `planner.py`, `executor.py`, `main.py`
