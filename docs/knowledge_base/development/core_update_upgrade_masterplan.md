# Core Update/Upgrade Masterplan 🚀

> **Last updated**: Feb 19, 2026 16:45 UTC  
> **Status**: Approved — Phase 0 starting  
> **CLI Command**: `vit update` / `vit upgrade`  
> **Architecture**: Hybrid (Library + CLI, built-in to Core)

## Objective 🎯

Define a distro-like update system for Vitruvyan Core:

- notify when updates are available 🔔
- provide one command to upgrade ⚙️
- validate vertical compatibility before and after upgrade ✅
- auto-rollback on failure 🛟

Expected outcome: **zero Core forks across verticals** and repeatable upgrades.

## Architectural Decisions (Approved) ✅

**Pattern**: Industry-standard hybrid (apt/pip/dnf model)
- **Library**: `core.platform.update_manager.engine` (business logic, testable)
- **CLI**: `vit` command (user interface, built-in)
- **Distribution**: Single package (`pip install vitruvyan-core` includes CLI)

**Location**: `vitruvyan_core/core/platform/update_manager/`
```
core/platform/update_manager/
├── engine/          # Library (compatibility, planning, execution)
│   ├── registry.py
│   ├── compatibility.py
│   ├── planner.py
│   └── executor.py
├── cli/             # CLI (commands, formatters)
│   ├── main.py
│   ├── commands/
│   └── formatters.py
└── tests/
```

**CLI Commands** (apt-style, concise):
- `vit update` = check for updates (like `apt update`)
- `vit upgrade` = apply upgrade (like `apt upgrade`)
- `vit plan` = show upgrade plan
- `vit rollback` = revert to previous version
- `vit channel` = switch stable/beta

**Versioning**:
- Git tags: `v1.0.0` (stable), `v1.1.0-beta.1` (beta)
- SemVer strict (MAJOR.MINOR.PATCH)
- Dual channels: `stable` (production), `beta` (early access)

## End State 🧭

When a vertical team runs:

```bash
vitruvyan update check
vitruvyan update apply
```

the platform must:

1. detect the latest Core release
2. validate compatibility using vertical manifest + contracts version
3. generate an upgrade plan (changes, risks, required tests)
4. apply upgrade transactionally
5. run vertical smoke tests
6. confirm upgrade or automatically rollback

## Non-Negotiable Principles 🧱

- Verticals import only from `contracts`, never from Core internals.
- No Core release ships without compatibility checks.
- Every upgrade is traceable via audit logs and reports.
- Contract breaking changes require major version + deprecation policy.

## Logical Architecture 🏗️

Main components:

- `Release Registry` (GitHub Releases API + metadata)
- `Compatibility Engine` (version validation + manifest parsing)
- `Update Manager CLI` (`vit` command)
- `Notification Engine` (startup check + periodic polling)
- `Safety Layer` (git snapshot, smoke tests, rollback)
- `Policy & Governance` (contracts, versioning, deprecations)

**Contract-Driven**: All interactions governed by `UPDATE_SYSTEM_CONTRACT_V1.md`

### 1) Release Registry 📦

Source of truth for Core releases (start with GitHub Releases).

Minimum metadata per release:

- Core version
- supported contracts version
- channel (`stable`, `canary`, `lts`)
- machine-readable changelog
- artifact checksum
- migration notes

### 2) Compatibility Engine 🧠

Reads:

- release metadata
- `vertical_manifest.yaml`

Outputs:

- `compatible`
- `compatible_with_warnings`
- `blocked`

Common block reasons:

- Core version is outside supported range
- contracts major mismatch
- required capability no longer available

### 3) Update Manager CLI 🛠️

**Command**: `vit` (concise, apt-style)

Target commands:

- `vit update` — check for updates (sync release registry)
- `vit upgrade` — apply upgrade (with compatibility validation)
- `vit plan` — show upgrade plan (changes, risks, tests)
- `vit rollback` — revert to previous version
- `vit channel [stable|beta]` — switch update channel
- `vit status` — show current version + available updates

Minimum behavior:

- human-readable output (tables, colors)
- CI-friendly exit codes (0=success, 1=blocked, 2=error)
- non-interactive mode (`--yes`) for automation
- JSON output mode (`--json`) for programmatic usage

### 4) Notification Engine 🔔

Minimum channels:

- notification on service startup
- scheduled periodic check

Optional channels:

- Slack/Webhook
- internal dashboard

### 5) Safety Layer 🛡️

During `update apply`:

- snapshot current state (commit/tag/deps/manifest)
- apply update
- execute minimal smoke suite
- auto-rollback + report on failure

### 6) Policy & Governance 📜

- Core SemVer
- separate Contracts versioning
- deprecation policy with support window
- release channel policy (`stable/canary/lts`)

## Implementation Tracklist 🧭

## Phase 0 - Foundations (Week 1) 🧱

Goal: lock base rules and data schema.

Tasks:

- **Create contract**: `docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md`
  - Manifest schema (vertical compliance)
  - Smoke test interface (exit codes, timeout)
  - Versioning policy (SemVer, breaking changes)
  - Release metadata schema (JSON format)
- **Extend** `vertical_manifest.yaml` with compatibility fields
- **Create directory structure**: `core/platform/update_manager/{engine,cli,tests}/`
- **Define** initial compatibility matrix (core version → contracts version)

Deliverables:

- `UPDATE_SYSTEM_CONTRACT_V1.md` (binding contract)
- Updated `vertical_manifest.yaml` template
- Sample release metadata JSON
- Skeleton code structure (empty modules with docstrings)

Definition of Done:

- Contract approved by platform team
- Manifest schema validated (pytest schema test)
- One sample vertical using new schema (finance example)
- Directory structure created + committed

## Phase 1 - Compatibility Engine (Week 2) 🧠

Goal: block risky upgrades before apply.

Tasks:

- Implement `engine/registry.py` (GitHub Releases API client)
- Implement `engine/compatibility.py` (version range validation, SemVer parsing)
- Implement `engine/models.py` (dataclasses: Release, CompatibilityResult)
- Implement `cli/commands/update.py` (`vit update` command)
- Generate compatibility report (text + JSON formats)

Deliverables:

- Working `vit update` command
- Compatibility report: `compatible`, `compatible_with_warnings`, `blocked`
- JSON output mode: `vit update --json`
- Unit tests: `tests/test_compatibility.py` (100% coverage)

Definition of Done:

- `vit update` shows current version + latest available
- Incompatible upgrades blocked with explicit reason
- All unit tests pass (pytest)
- Works with sample vertical (finance)

## Phase 2 - Apply + Rollback (Weeks 3-4) 🔁

GoImplement `engine/planner.py` (upgrade plan generation)
- Implement `engine/executor.py` (git checkout, pip install, snapshot)
- Implement `cli/commands/plan.py` (`vit plan` command)
- Implement `cli/commands/upgrade.py` (`vit upgrade` command)
- Implement `cli/commands/rollback.py` (`vit rollback` command)
- Pre-upgrade snapshot (git tag: `pre-upgrade-<timestamp>`)
- Post-upgrade smoke tests (call vertical's `smoke_tests/run.sh`)
- Automatic rollback on failure

Deliverables:

- Working `vit upgrade` command (end-to-end flow)
- Working `vit rollback` command
- Upgrade audit log (`.vitruvyan/upgrade_history.json`)
- Functional tests: `tests/test_cli.py` (E2E scenarios)

Definition of Done:

- Compatible upgrade applies successfully + smoke tests pass
- Failing smoke tests trigger automatic rollback
- Rollback restores previous state (git + deps)
- Audit log records all upgrade attempts

- compatible update applies successfully
- failing tests trigger automatic rollback
- final state is consistent and verifiable

## Phase 3 - CI/CD Gate (Week 5) 🚦

Goal: prevent Core releases that break active verticals.

Tasks:

- multi-vertical compatibility CI pipeline
- PR/release gating rules
- compatibility report as CI artifact

Deliverables:

- updated CI pipeline
- release-blocking rule enabled

Definition of Done:

- incompatible release is automatically blocked

## Phase 4 - Notification System (Week 6) 📣

Goal: automatic update visibility for teams.

Tasks:

- notifications in `update check`
- scheduled update notifications
- (optional) Slack webhook

Deliverables:

- local notification + logs
- configurable notification channel

Definition of Done:

- vertical teams receive update alerts without manual polling

## Phase 5 - Hardening & Governance (Weeks 7-8) 🧰

Goal: production-grade reliability.

Tasks:

- full upgrade audit trail
- support window policy (N supported versions)
- rollback resilience tests
- incident runbook for failed upgrades

Deliverables:

- operational runbook
- pre/post-upgrade checklist
- vertical version status dashboard (minimal is fine)

**Phase 0 (Foundations)**:
- [ ] Create `UPDATE_SYSTEM_CONTRACT_V1.md`
- [ ] Extend `vertical_manifest.yaml` (compatibility fields)
- [ ] Define `release_metadata.json` schema
- [ ] Create directory structure `core/platform/update_manager/`

**Phase 1 (Compatibility Engine)**:
- [ ] Implement `engine/registry.py` (GitHub API)
- [ ] Implement `engine/compatibility.py` (version validation)
- [ ] Implement `vit update` command
- [ ] Generate JSON compatibility report
- [ ] Unit tests (compatibility logic)

**Phase 2 (Apply + Rollback)**:
- [ ] Implement `engine/planner.py` (upgrade plan)
- [ ] Implement `engine/executor.py` (apply/rollback)
- [ ] Implement `vit upgrade` command
- [ ] Implement `vit rollback` command
- [ ] Create vertical smoke test template
- [ ] Add upgrade audit logging

**Phase 3 (CI/CD Gate)**:
- [ ] Implement CI compatibility gate
- [ ] Multi-vertical test matrix
- [ ] Release blocking rules

**Phase 4 (Notifications)**:
- [ ] Startup update check
- [ ] Periodic polling (configurable)
- [ ] Webhook notifications (optional)

**Phase 5 (Hardening)**:
- [ ] Operational runbook
- [ ] Rollback resilience tests
- [ ] Version status dashboard
- [ ] implement `update apply`
- [ ] implement `update rollback`
- [ ] create vertical smoke test pack
**Developer workflow** (vertical team):

```bash
# 1. Check for updates
vit update
# Output: "New version v1.2.0 available (current: v1.1.0)"
#         "Compatibility: ✅ COMPATIBLE"

# 2. Review upgrade plan
vit plan --target v1.2.0
# Output: changelog, affected contracts, required tests

# 3. Apply upgrade
vit upgrade
# Platform auto-executes:
#   - Create snapshot (git tag pre-upgrade-20260219-164500)
#   - Checkout v1.2.0
#   - Install dependencies
#   - Run smoke tests
#   - Confirm OR rollback

# 4. Verify
vit status
# Output: "Core v1.2.0 (upgraded from v1.1.0 on 2026-02-19)"
```

**Rollback flow** (if issues found post-upgrade):
```bash
vit rollback
# Restores: git state + dependencies + audit log entry
```
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

## Standard Operating Flow (SOP) 🔄

1. vertical team runs `vitruvyan update check`
2. if `compatible`, run `vitruvyan update plan`
3. approve and run `vitruvyan update apply`
4. platform executes smoke tests
5. if pass, upgrade is confirmed
6. if fail, rollback runs and ticket/report is generated

## Main Risks & Mitigations ⚠️

**MVP Path** (3 weeks, immediate value):
1. **Phase 0** (Week 1): Foundations + contract
2. **Phase 1** (Week 1-2): `vit update` working (read-only checks)
3. **Phase 2** (Week 2-3): `vit upgrade` + `vit rollback` (manual testing)

**Production Hardening** (additional 2-4 weeks):
4. **Phase 3** (Week 4): CI gates (prevent breaking releases)
5. **Phase 4** (Week 5): Notifications (proactive alerts)
6. **Phase 5** (Week 6-7): Governance + runbooks

This sequence minimizes architectural risk before vertical expansion.

**Quick-win milestone**: After Week 2, vertical teams can run `vit update` to check compatibility (immediate safety net, even without auto-apply)
- Risk: unreliable rollback.
  Mitigation: atomic snapshot + recurring rollback drills.

## Suggested Ownership 👥

- Platform/Core team: release registry, contracts, update manager
- Vertical teams: manifest, smoke tests, vertical compliance
- DevOps/SRE: CI gates, notifications, observability, runbooks

## KPIs to Monitor 📈

- successful upgrades (%)
- mean time to upgrade (MTTU)
- rollback rate (%)
- incompatibilities caught pre-deploy
- post-upgrade incident count

## Recommended Rollout Order 🗺️

1. Phase 0 and Phase 1 first (breakage prevention)
2. Phase 2 next (apply + rollback)
3. Phase 3 before scaling vertical count
4. Phase 4 and 5 for continuous operations

This sequence minimizes architectural risk before vertical expansion.
