# Update Manager — Capacità Attuali & Roadmap

> **Last updated**: Feb 19, 2026 18:00 UTC  
> **Codebase**: ~4,100 righe (esclusi test)  
> **Status**: Phase 0-4 complete (80% feature-complete)  
> **Contract**: `UPDATE_SYSTEM_CONTRACT_V1.md`

---

## 📦 Cosa Fa il Sistema Attualmente

### ✅ Phase 0 - Foundations (COMPLETE)

**Contract & Schema**
- ✅ `UPDATE_SYSTEM_CONTRACT_V1.md` — Binding contract tra Core e Verticals
- ✅ `vertical_manifest.yaml` esteso con sezione `compatibility`:
  ```yaml
  compatibility:
    min_core_version: "1.0.0"      # Versione minima Core supportata
    max_core_version: "1.x.x"      # Wildcard support (npm-style)
    contracts_major: 1              # Versione major contracts
    update_channel: "stable"        # stable | beta
    breaking_changes_allowlist: []  # Opt-in esplicito a breaking changes
    smoke_tests_timeout: 300        # Timeout smoke tests (secondi)
  ```
- ✅ `release_metadata.json` schema (GitHub Releases)
- ✅ Struttura directory `core/platform/update_manager/`

**Deliverable**:
- Contract pubblicato in KB (con 5 diagrammi Mermaid flow)
- Template manifest aggiornato

---

### ✅ Phase 1 - Compatibility Engine (COMPLETE)

**Command**: `vit update`

**Cosa fa**:
1. **Legge versione Core corrente** (da `vitruvyan_core.__version__` o `git describe`)
2. **Fetcha latest release da GitHub** (via GitHub Releases API)
3. **Legge vertical_manifest.yaml** (dal repo corrente, walking up to Git root)
4. **Valida compatibilità**:
   - ✅ Target version dentro range `min_core_version` ↔ `max_core_version`
   - ✅ Wildcard matching (`1.x.x` = qualsiasi `1.*.*`)
   - ✅ Contracts major version match
   - ✅ Breaking changes check (opt-in via allowlist)
5. **Output human-readable**:
   ```
   Current version: v1.0.0
   Latest available: v1.2.0 (stable)
   
   Compatibility: ✅ COMPATIBLE
   
   Next steps:
     vit upgrade    # Apply upgrade
     vit plan       # Review upgrade plan
   ```

**Implementazione**:
- `engine/registry.py` (284L): GitHub API client, release fetching, checksum verification
- `engine/compatibility.py` (356L): SemVer matching, wildcard logic, breaking changes check
- `engine/models.py` (150L): `Release`, `CompatibilityResult` dataclasses
- `cli/commands/update.py` (215L): CLI command implementation
- `cli/formatters.py` (120L): Tabelle, colori, output formattato

**Casi d'uso supportati**:
```bash
# Check standard
vit update

# Check specifica canale
vit update --channel beta

# Output JSON (per CI/automation)
vit update --json
```

**Limitazioni attuali**:
- ❌ Non supporta proxy/firewall configurabili
- ❌ GitHub rate limiting non gestito (fallback locale)
- ❌ Cache releases (ogni call = nuovo fetch API)

---

### ✅ Phase 2 - Apply + Rollback (COMPLETE)

**Commands**: `vit upgrade`, `vit plan`, `vit rollback`

#### `vit upgrade` — Applica Upgrade

**Flusso**:
1. **Pre-flight check**: Compatibilità (riusa `CompatibilityChecker`)
2. **Create snapshot**: Git tag `pre-upgrade-YYYYMMDD-HHMMSS`
3. **Checkout target version**: `git checkout v1.2.0`
4. **Install dependencies**: `pip install -e .` (editable mode)
5. **Run smoke tests**: `smoke_tests/run.sh` (timeout configurabile)
6. **Confirm or rollback**:
   - ✅ Tests pass (exit 0) → upgrade confermato
   - ❌ Tests fail (exit ≠ 0) → **rollback automatico**
7. **Audit log**: Write entry in `~/.vitruvyan/audit.json`

**Implementazione**:
- `engine/executor.py` (420L): Orchestrazione upgrade, snapshot, rollback
- `engine/planner.py` (280L): Genera upgrade plan (diff, changelog, tests required)
- `cli/commands/upgrade.py` (220L): CLI wrapper
- `cli/commands/plan.py` (183L): Mostra upgrade plan senza eseguire
- `cli/commands/rollback.py` (75L): Manual rollback

**Audit log format**:
```json
{
  "upgrades": [
    {
      "timestamp": "2026-02-19T17:30:00.123456",
      "from_version": "1.0.0",
      "to_version": "1.2.0",
      "snapshot_tag": "pre-upgrade-20260219-173000",
      "success": true
    }
  ]
}
```

**Casi d'uso supportati**:
```bash
# Upgrade interattivo
vit upgrade

# Upgrade non-interattivo (CI)
vit upgrade --yes

# Upgrade specifica versione
vit upgrade --target v1.5.0

# Preview upgrade plan
vit plan --target v1.2.0

# Rollback manuale
vit rollback
```

**Smoke tests contract**:
- Location: `<vertical_root>/smoke_tests/run.sh`
- Exit codes: `0` = pass, `1` = fail, `2` = error
- Timeout: 300s default (configurabile via manifest)
- Output: STDOUT/STDERR logged, non parsato

**Limitazioni attuali**:
- ❌ Rollback limitato a 1 snapshot (no rollback stack)
- ❌ No database migration support (solo Git + pip)
- ❌ Snapshot non include virtualenv (solo Git state)
- ❌ Smoke tests output non strutturato (no JUnit XML)

---

### ✅ Phase 3 - CI/CD Integration (COMPLETE)

**GitHub Actions Workflow**: `.github/workflows/update_manager_ci.yml`

**Trigger**: Git tag push (`v*.*.*`)

**Jobs**:
1. **validate-manifests**: Valida tutti i vertical manifests (ContractValidator)
2. **check-compatibility**: Verifica compatibilità verticals con release
3. **run-compatibility-tests**: Esegue pytest suite (8 test compatibility)
4. **summary**: Genera report JSON + artifacts

**Release Blocking**:
- ❌ Manifest invalido → BLOCK (exit 1)
- ❌ Vertical incompatibile → BLOCK (exit 1)
- ❌ Compatibility test fail → BLOCK (exit 1)

**Implementazione**:
- `ci/contract_validator.py` (325L): Valida manifests vs contract schema
- `ci/pytest_integration.py` (150L): Markers, fixtures, parametrization
- `ci/release_blocker.py` (250L): CLI tool, blocking logic, exit codes
- `.github/workflows/update_manager_ci.yml` (172L): GitHub Actions workflow

**Test suite** (`tests/test_compatibility.py`, 175L):
- ✅ Wildcard matching (`1.x.x`, `1.2.x`)
- ✅ Pre-release handling (`1.2.0-beta.1`)
- ✅ Contracts major mismatch
- ✅ Breaking changes allowlist
- ✅ Edge cases (invalid semver, empty manifest)

**Artifacts prodotti**:
- `compliance_report.json` (manifest validation)
- `compatibility-report.json` (version check results)
- `test-results.xml` (pytest JUnit)

**Limitazioni attuali**:
- ❌ No multi-vertical test matrix (testa 1 vertical alla volta)
- ❌ No performance benchmarks (solo functional tests)
- ❌ No smoke tests in CI (solo compatibility logic)

---

### ✅ Phase 4 - Notification System (COMPLETE)

**Features**:
- ✅ Startup check (controlla updates all'avvio servizi)
- ✅ Periodic polling (daemon background, intervallo configurabile)
- ✅ Multi-channel distribution (desktop, log, webhook, email*)

**Command**: `vit status`

**Output**:
```
─────────────────────────────────────────────────────────
  Vitruvyan Core — Update Status
─────────────────────────────────────────────────────────

  Current version:  1.0.0
  Latest version:   1.2.0

  ✨ Update available

  Changelog: https://github.com/.../releases/tag/v1.2.0

  Notification settings:
    Status: Enabled
    Channels: desktop, log
    Check interval: 24h

  Last check: 2 hours ago

─────────────────────────────────────────────────────────
```

**Implementazione**:
- `notifications/config.py` (193L): Multi-tier config (env > manifest > defaults)
- `notifications/startup_check.py` (163L): Check on boot, throttling
- `notifications/periodic_poller.py` (128L): Background daemon
- `notifications/notifiers/`:
  - `desktop.py` (134L): Linux (notify-send), macOS (osascript), Windows (win10toast)
  - `log.py` (71L): `~/.vitruvyan/update_notifications.log`
  - `webhook.py` (126L): Slack (rich attachments) + generic HTTP POST
  - `base.py` (42L): `BaseNotifier` interface
- `cli/commands/status.py` (259L): `vit status` command

**Configurazione** (manifest):
```yaml
notifications:
  enabled: true
  channels: ["desktop", "log"]      # desktop, log, webhook, email
  check_on_startup: true
  check_interval_hours: 24          # Intervallo polling
  desktop_urgency: "normal"         # low | normal | critical
  webhook_url: "https://hooks.slack.com/..."
  webhook_format: "slack"           # slack | generic
```

**Env vars override**:
- `VIT_NOTIFY_ENABLED=0/1`
- `VIT_NOTIFY_CHANNELS=desktop,log,webhook`
- `VIT_NOTIFY_INTERVAL=12`
- `VIT_NOTIFY_WEBHOOK_URL=...`

**Periodic Poller** (daemon):
```bash
# Start background daemon
python -m vitruvyan_core.core.platform.update_manager.notifications.periodic_poller

# Or programmatically
from vitruvyan_core.core.platform.update_manager.notifications import start_polling_daemon
poller = start_polling_daemon("vertical_manifest.yaml")
```

**Test suite** (`tests/test_notifications.py`, 347L):
- ✅ 15 tests (config loading, notifiers, startup logic, poller)
- ✅ Mocked subprocess (desktop notifier)
- ✅ Mocked httpx (webhook notifier)
- ✅ File I/O (log notifier)
- ✅ Time mocking (interval throttling)

**Limitazioni attuali**:
- ⚠️ Email notifier **stub** (interfaccia presente, SMTP non implementato)
- ❌ Webhook retry logic (single HTTP POST, no backoff)
- ❌ Desktop notification persistenza (no notification center integration)
- ❌ Rate limiting notifications (può spammare se update check fallisce)

---

## 🏗️ Come Funziona il Sistema

### Architettura Complessiva

```
┌─────────────────────────────────────────────────────────┐
│                   CLI Layer (vit)                       │
│  update | upgrade | plan | rollback | status | history │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               Engine Layer (Library)                     │
│                                                          │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │   Registry   │  │ Compatibility│  │    Planner     │ │
│  │  (GitHub)    │  │   Checker   │  │  (Upgrade Plan)│ │
│  └──────────────┘  └─────────────┘  └────────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │   Executor   │  │ Notifications│  │   CI Gates     │ │
│  │(Apply/Rollbck)│  │  (Multi-ch) │  │  (Validators)  │ │
│  └──────────────┘  └─────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                External Systems                          │
│                                                          │
│  GitHub API   │  Git   │  pip   │  Smoke Tests │  Logs  │
└──────────────────────────────────────────────────────────┘
```

### Flussi Principali (5 Diagrammi Mermaid in KB)

1. **Update Check Flow** → `vit update`
2. **Upgrade Flow** → `vit upgrade` (con rollback automatico)
3. **Notification Flow** → Startup check + periodic poller
4. **CI/CD Integration** → GitHub Actions release blocking
5. **Periodic Poller** → Background daemon lifecycle

**Vedi**: `UPDATE_SYSTEM_CONTRACT_V1.md` sezione "Update System Flow Diagrams"

### Dependency Graph

```
vit (CLI)
  └─> UpdateEngine (Facade)
       ├─> ReleaseRegistry
       │    └─> GitHub API (urllib)
       ├─> CompatibilityChecker
       │    └─> vertical_manifest.yaml (yaml)
       ├─> UpgradePlanner
       │    └─> Git commands (subprocess)
       ├─> UpgradeExecutor
       │    ├─> Git (snapshot, checkout)
       │    ├─> pip (install)
       │    └─> smoke_tests/run.sh (subprocess)
       └─> NotificationEngine
            ├─> DesktopNotifier (notify-send/osascript/win10toast)
            ├─> LogNotifier (file I/O)
            └─> WebhookNotifier (httpx)
```

### State Management

**Stateful components**:
1. **Audit log**: `~/.vitruvyan/audit.json` (upgrade history)
2. **Last check time**: `~/.vitruvyan/last_update_check` (timestamp float)
3. **Notification log**: `~/.vitruvyan/update_notifications.log` (append-only)
4. **Git snapshots**: Tags `pre-upgrade-*` (rollback points)

**Stateless** (ogni invocation è autonoma):
- Release fetching (GitHub API, no local cache)
- Compatibility validation (in-memory)
- Smoke tests execution (subprocess, no persistent state)

---

## 🚀 Cosa Può Essere Ulteriormente Implementato

### 🔥 Phase 5 - Hardening & Governance (PROPOSTA)

#### 1. Enhanced Audit Trail
**Attuale**: Audit log minimale (timestamp, versions, snapshot, success flag)

**Proposta**:
- ➕ Operation metadata (user, hostname, duration, PID)
- ➕ Compatibility check result (issues, warnings)
- ➕ Smoke tests details (exit code, log path, duration)
- ➕ Rollback reason (manual vs automatic)
- ➕ Checksum verification result
- ➕ Environment snapshot (Python version, OS, dependencies)

**Benefici**:
- Debugging post-mortem upgrade failures
- Compliance auditing (chi ha fatto cosa quando)
- Performance monitoring (durata upgrade nel tempo)

**Effort**: 🟢 Low (1-2 ore, extend existing `_write_audit_log()`)

---

#### 2. Support Window Policy
**Attuale**: Nessuna policy di EOL (End of Life) versioni

**Proposta**:
- ➕ `engine/support_policy.py`: Define N-X support window
- ➕ Warning nel CLI se target version è EOL
- ➕ `vit supported` command: Lista versioni supportate + EOL dates
- ➕ Auto-skip EOL versions in `vit update` (con flag override)

**Policy esempio**:
```
N (current): v1.2.0 (supported until v2.0.0)
N-1:         v1.1.x (supported until 2027-01-01)
N-2:         v1.0.x (EOL, security patches only)
```

**Benefici**:
- Prevent verticals da rimanere su versioni non supportate
- Comunicazione chiara lifecycle Core releases

**Effort**: 🟡 Medium (2-3 ore, date logic + integration)

---

#### 3. Rollback Resilience Tests
**Attuale**: Rollback testato manualmente, no automated resilience tests

**Proposta**: Test suite dedicata (`tests/test_rollback_resilience.py`)

**Test cases**:
- ✅ Rollback con snapshot corrotto (git tag missing)
- ✅ Rollback con disk space esaurito
- ✅ Rollback doppio (rollback di un rollback)
- ✅ Rollback con dirty git tree (uncommitted changes)
- ✅ Rollback con smoke tests timeout

**Benefici**:
- Confidence che rollback funziona in scenari edge case
- Regression prevention (rollback è safety critical)

**Effort**: 🟢 Low (1-2 ore, pytest parametrize)

---

#### 4. Operational Runbook
**Attuale**: Documentazione sparsa, no incident response guide

**Proposta**: `docs/knowledge_base/operations/UPDATE_MANAGER_RUNBOOK.md`

**Sezioni**:
1. **Pre-Upgrade Checklist** (backup, disk space, test environment)
2. **Post-Upgrade Verification** (smoke tests, health checks, logs)
3. **Incident Response Decision Tree**:
   - Smoke tests failed → auto-rollback
   - Service degradation post-upgrade → manual rollback
   - Partial upgrade (some verticals fail) → isolation strategy
4. **Common Failures & Solutions**:
   - Network timeout → retry logic, offline mode
   - Checksum mismatch → re-download, report corruption
   - Smoke tests timeout → extend timeout, debug test
5. **Communication Templates** (incident announcement, postmortem)

**Benefici**:
- Operational readiness per production
- Faster incident response (no improvvisazione)

**Effort**: 🟡 Medium (2-3 ore, documentation)

---

#### 5. Version History Dashboard
**Attuale**: Audit log esiste, ma no command per visualizzarlo

**Proposta**: `vit history` command

**Output** (human-readable):
```bash
$ vit history

Upgrade History (last 10):
┌────────────┬─────────┬──────────┬────────┬──────────┬─────────────┐
│ Date       │ From    │ To       │ Status │ Duration │ Rollback    │
├────────────┼─────────┼──────────┼────────┼──────────┼─────────────┤
│ 2026-02-19 │ v1.1.0  │ v1.2.0   │ ✅     │ 45.3s    │ —           │
│ 2026-02-10 │ v1.0.0  │ v1.1.0   │ ✅     │ 32.1s    │ —           │
│ 2026-01-25 │ v1.0.0  │ v1.1.0β1 │ ❌     │ 18.2s    │ auto (test) │
└────────────┴─────────┴──────────┴────────┴──────────┴─────────────┘

$ vit history --failed  # Show only failed upgrades
$ vit history --json    # Machine-readable
```

**Benefici**:
- Visibility su upgrade history (troubleshooting)
- Integration con monitoring esterni (Grafana, Datadog)

**Effort**: 🟢 Low (1 ora, CLI command + formatter)

---

### 🔮 Future Enhancements (Post-Phase 5)

#### 6. Database Migration Support
**Current limitation**: Solo Git + pip, no database schema changes

**Proposta**:
- ➕ Alembic/SQL migration integration
- ➕ Pre-upgrade DB snapshot (pg_dump)
- ➕ Rollback include DB restore
- ➕ Migration dry-run mode

**Use case**: Vertical use PostgreSQL, schema changes in upgrade

**Effort**: 🔴 High (5-8 ore, DB-specific logic)

---

#### 7. Partial Upgrade Support
**Current limitation**: All-or-nothing (tutto il Core, non single components)

**Proposta**:
- ➕ Component-level versioning (Sacred Orders indipendenti?)
- ➕ Dependency resolution (upgrade Order X → require Order Y v1.2+)
- ➕ Partial rollback

**Use case**: Hotfix su single Sacred Order senza full Core upgrade

**Effort**: 🔴 High (architectural, richiede Core refactoring)

---

#### 8. Offline Mode
**Current limitation**: Richiede GitHub API (no air-gapped environments)

**Proposta**:
- ➕ Local release repository (file:// schema)
- ➕ `vit import` command (import release tarball)
- ➕ Checksum verification offline

**Use case**: Deployment in ambiente senza internet

**Effort**: 🟡 Medium (3-4 ore, abstraction Registry)

---

#### 9. Multi-Core Multi-Vertical Matrix Testing
**Current limitation**: CI testa 1 vertical corrente, no cross-vertical

**Proposta**:
- ➕ GitHub Actions matrix build (N verticals × M Core versions)
- ➕ Compatibility matrix report (table)
- ➕ Auto-discovery verticals nel monorepo

**Use case**: Detect regression che rompe vertical X ma non Y

**Effort**: 🟡 Medium (2-3 ore, GitHub Actions)

---

#### 10. Incremental Upgrades (Multi-Hop)
**Current limitation**: Upgrade 1.0 → 1.5 richiede single hop (no 1.0→1.2→1.5)

**Proposta**:
- ➕ Path planning (calcola upgrade intermedii)
- ➕ Multi-step execution (checkpoint ogni hop)
- ➕ Rollback granulare (rollback al checkpoint precedente)

**Use case**: Major version jump con breaking changes intermedie

**Effort**: 🔴 High (6-10 ore, state machine complexity)

---

## 📊 Summary Matrix

| Feature | Status | Lines | Tests | Priority | Effort |
|---------|--------|-------|-------|----------|--------|
| **Phase 0** (Contract) | ✅ Complete | ~500 | — | Critical | Done |
| **Phase 1** (`vit update`) | ✅ Complete | ~1,200 | 8 | Critical | Done |
| **Phase 2** (`vit upgrade/rollback`) | ✅ Complete | ~1,500 | Manual | Critical | Done |
| **Phase 3** (CI gates) | ✅ Complete | ~700 | 8 | High | Done |
| **Phase 4** (Notifications) | ✅ Complete | ~900 | 15 | Medium | Done |
| **Phase 5a** (Enhanced audit) | ⏸️ Proposed | ~200 | 5 | Medium | Low |
| **Phase 5b** (Support policy) | ⏸️ Proposed | ~250 | 8 | Medium | Medium |
| **Phase 5c** (Rollback tests) | ⏸️ Proposed | ~150 | 10 | High | Low |
| **Phase 5d** (Runbook) | ⏸️ Proposed | ~0 | — | High | Medium |
| **Phase 5e** (`vit history`) | ⏸️ Proposed | ~100 | 3 | Low | Low |
| **Future** (DB migrations) | 💡 Idea | ~800 | 15 | Medium | High |
| **Future** (Offline mode) | 💡 Idea | ~300 | 8 | Low | Medium |
| **Future** (Multi-vertical CI) | 💡 Idea | ~200 | — | Medium | Medium |

**Total implemented**: ~4,100 lines (main) + ~540 lines (tests) = **~4,640 lines**

---

## 🎯 Raccomandazioni Next Steps

### Opzione A: **Complete Phase 5** (Production Readiness)
**Focus**: Hardening, governance, operational excellence

**Deliverables**:
1. Enhanced audit trail (metadata completo)
2. Support policy + EOL warnings
3. Rollback resilience tests (10 test cases)
4. Operational runbook (incident response)
5. `vit history` command

**Timeline**: 1-2 giorni  
**ROI**: 🟢 High (production-grade system)

---

### Opzione B: **Quick Wins** (Minimal Viable Phase 5)
**Focus**: Feature critiche con effort minimo

**Deliverables**:
1. Enhanced audit trail (solo duration + hostname)
2. Rollback resilience tests (5 test cases critici)
3. `vit history` command (basic table)

**Timeline**: 3-4 ore  
**ROI**: 🟡 Medium (good enough per MVP)

---

### Opzione C: **Future Features** (Innovation)
**Focus**: Estendere capabilities oltre MVP

**Deliverables**:
1. Database migration support (Alembic)
2. Offline mode (local repository)
3. Multi-vertical CI matrix

**Timeline**: 1 settimana  
**ROI**: ⚠️ Variable (dipende da use case)

---

## 📖 Risorse

- **Contract**: [UPDATE_SYSTEM_CONTRACT_V1.md](../../contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md)
- **Package Manager Contract**: [PACKAGE_MANAGER_SYSTEM_CONTRACT_V1.md](../../contracts/platform/PACKAGE_MANAGER_SYSTEM_CONTRACT_V1.md)
- **Update Manager System**: [Update_Manager_System.md](./Update_Manager_System.md)
- **Flow Diagrams**: UPDATE_SYSTEM_CONTRACT_V1.md § "Update System Flow Diagrams"
- **Codebase**: `vitruvyan_core/core/platform/update_manager/`
- **Tests**: `vitruvyan_core/core/platform/update_manager/tests/`

---

**END OF SUMMARY**
