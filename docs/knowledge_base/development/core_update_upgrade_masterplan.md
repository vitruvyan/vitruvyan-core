# Core Update/Upgrade Masterplan 🚀

## Objective 🎯

Define a distro-like update system for Vitruvyan Core:

- notify when updates are available 🔔
- provide one command to upgrade ⚙️
- validate vertical compatibility before and after upgrade ✅
- auto-rollback on failure 🛟

Expected outcome: **zero Core forks across verticals** and repeatable upgrades.

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

- `Release Registry`
- `Compatibility Engine`
- `Update Manager CLI`
- `Notification Engine`
- `Safety Layer` (snapshot, tests, rollback)
- `Policy & Governance` (versioning, deprecations, support window)

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

Target commands:

- `vitruvyan update check`
- `vitruvyan update plan`
- `vitruvyan update apply`
- `vitruvyan update rollback`
- `vitruvyan update status`

Minimum behavior:

- human-readable output
- CI-friendly exit codes
- non-interactive mode (`--yes`) for automation

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

- formalize Core/Contracts versioning policy
- extend `vertical_manifest.yaml` with compatibility fields
- define release metadata schema
- define initial compatibility matrix

Deliverables:

- policy document (`docs/contracts/...`)
- updated manifest template
- sample release metadata JSON/YAML

Definition of Done:

- policy approved
- manifest schema validated
- one sample vertical using new schema

## Phase 1 - Compatibility Engine (Week 2) 🧠

Goal: block risky upgrades before apply.

Tasks:

- implement vertical manifest parser
- implement Core version range validation
- implement contracts major validation
- generate compatibility report with reasons

Deliverables:

- `compatibility_engine` module
- `vitruvyan update check` command
- text + JSON report

Definition of Done:

- 100% happy-path cases pass
- incompatible cases return `blocked` with explicit reason

## Phase 2 - Apply + Rollback (Weeks 3-4) 🔁

Goal: safe transactional upgrade flow.

Tasks:

- implement `update plan`
- implement `update apply`
- pre-upgrade snapshot
- post-upgrade smoke tests
- automatic rollback

Deliverables:

- local end-to-end upgrade workflow
- upgrade/rollback execution logs

Definition of Done:

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

Definition of Done:

- upgrade process is repeatable and auditable in production

## Minimum Technical Backlog ✅

- [ ] extend `vertical_manifest.yaml` (compatibility fields)
- [ ] define `release_metadata.json` schema
- [ ] implement `update check`
- [ ] implement `update plan`
- [ ] implement `update apply`
- [ ] implement `update rollback`
- [ ] create vertical smoke test pack
- [ ] generate JSON compatibility report
- [ ] implement CI compatibility gate
- [ ] add upgrade audit logging

## Required Manifest Fields (Target) 📄

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

- Risk: vertical imports Core internals instead of contracts.
  Mitigation: CI lint/policy to block non-approved imports.

- Risk: incomplete release metadata.
  Mitigation: mandatory release metadata template + pre-release validation.

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
