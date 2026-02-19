# UPDATE SYSTEM CONTRACT V1

> **Version**: 1.0.0  
> **Status**: BINDING (Phase 0 - Foundation)  
> **Last Updated**: February 19, 2026  
> **Scope**: Core + All Verticals  

---

## Purpose

Define the **binding contract** for Vitruvyan Core update/upgrade system.

This contract governs:
- How Core releases are versioned and published
- How Verticals declare compatibility constraints
- How upgrades are validated, executed, and rolled back
- What both parties MUST/MAY/MUST NOT do

**Violation = Deployment BLOCKED** (CI gates enforce compliance).

---

## 1. Manifest Schema (Vertical MUST Comply)

Every vertical MUST provide `vertical_manifest.yaml` with these fields:

### Required Fields

```yaml
domain_name: string              # Vertical identifier (lowercase, alphanumeric)
domain_version: string           # Vertical version (SemVer)
status: string                   # "active" | "deprecated" | "experimental"

compatibility:
  min_core_version: string       # REQUIRED (SemVer, e.g. "1.0.0")
  max_core_version: string       # REQUIRED (wildcard allowed, e.g. "1.x.x")
  contracts_major: integer       # REQUIRED (must match Core's contracts version)
  update_channel: string         # REQUIRED ("stable" | "beta")
  breaking_changes_allowlist: [] # OPTIONAL (explicit opt-in to specific breaking changes)
  smoke_tests_timeout: integer   # OPTIONAL (seconds, default 300)

ownership:
  team: string                   # REQUIRED
  tech_lead: string              # REQUIRED
  contact: string                # REQUIRED (email)
```

### Validation Rules

1. `min_core_version` ≤ `max_core_version` (SemVer comparison)
2. `contracts_major` MUST match Core's contracts major version
3. `update_channel` MUST be "stable" or "beta"
4. `smoke_tests_timeout` MUST be 60-600 seconds (if provided)

**Enforcement**: `vit upgrade` reads manifest and blocks if invalid.

### Wildcard Matching Rules

**Semantics**: `x` = any non-negative integer (permissive matching)

**Examples**:
- `1.x.x` matches: `1.0.0`, `1.5.2`, `1.999.0`
- `1.x.x` does NOT match: `2.0.0`, `0.9.0`
- `1.2.x` matches: `1.2.0`, `1.2.99`
- `1.2.x` does NOT match: `1.3.0`, `1.1.9`

**Implementation** (Python reference):
```python
def match_version(version: str, pattern: str) -> bool:
    """
    Match version against wildcard pattern.
    
    >>> match_version("1.5.2", "1.x.x")
    True
    >>> match_version("2.0.0", "1.x.x")
    False
    """
    pattern_parts = pattern.split('.')
    version_parts = version.split('-')[0].split('.')  # strip pre-release
    
    for p, v in zip(pattern_parts, version_parts):
        if p == 'x':
            continue  # wildcard = any value
        if p != v:
            return False
    return True
```

**Rationale**: Industry standard (npm `^1.0.0`, Cargo `1.*`). Reduces manifest maintenance burden.

---

## 2. Smoke Test Interface (Vertical MUST Provide)

Every vertical MUST provide executable smoke tests.

### Location

```
<vertical_root>/smoke_tests/run.sh
```

### Path Resolution

**Vertical root** = directory containing `vertical_manifest.yaml`

**Algorithm**:
```python
def find_vertical_root(manifest_path: str) -> str:
    """
    Vertical root = directory containing vertical_manifest.yaml
    
    Example:
        manifest: /home/vitruvyan/vitruvyan-core/domains/finance/vertical_manifest.yaml
        → vertical_root: /home/vitruvyan/vitruvyan-core/domains/finance/
    """
    return os.path.dirname(os.path.abspath(manifest_path))

def find_smoke_tests(vertical_root: str) -> str:
    return os.path.join(vertical_root, "smoke_tests/run.sh")
```

**Discovery**: `vit` searches for `vertical_manifest.yaml` starting from current directory, walking up to Git repo root.

**Structure** (example):
```
/home/vitruvyan/vitruvyan-core/domains/finance/
├── vertical_manifest.yaml       ← vit finds this
├── smoke_tests/
│   └── run.sh                   ← resolved as <manifest_dir>/smoke_tests/run.sh
├── intent_config.py
└── README.md
```

### Contract

**Signature**: No arguments  
**Exit Codes**:
- `0` - All tests passed (upgrade confirmed)
- `1` - Tests failed (rollback triggered)
- `2` - Tests could not run (rollback + alert)

**Timeout**: 5 minutes default (configurable via `manifest.smoke_tests_timeout`)

**Output**:
- STDOUT: Test execution logs
- STDERR: Errors only

### Minimal Example

```bash
#!/bin/bash
set -e

# Test 1: Core imports work
python3 -c "from core.agents.postgres_agent import PostgresAgent; print('✅ Imports OK')"

# Test 2: Contracts available
python3 -c "from contracts import VerticalContract; print('✅ Contracts OK')"

# Test 3: Service health (if applicable)
curl -f http://localhost:8000/health || exit 1

echo "✅ All smoke tests passed"
exit 0
```

**Enforcement**: `vit upgrade` executes `smoke_tests/run.sh` post-upgrade. Non-zero exit = automatic rollback.

---

## 3. Versioning Policy (Core MUST Comply)

Core follows **strict SemVer** (MAJOR.MINOR.PATCH).

### Version Semantics

- **MAJOR**: Breaking changes (contracts incompatible, API removed, behavior changed)
- **MINOR**: New features (backward compatible, new APIs, deprecations announced)
- **PATCH**: Bug fixes only (no API changes)

### Git Tags

- Stable release: `v1.0.0`, `v1.1.0`, `v2.0.0`
- Beta release: `v1.1.0-beta.1`, `v1.2.0-beta.2`

### Breaking Changes Process

1. **Deprecation Warning** (N-1 MINOR version)
   - Add `@deprecated` decorator + log warning
   - Document in `CHANGELOG.md`
   - Update migration guide

2. **Deprecation Window** (6 months minimum)
   - Feature marked deprecated but still functional
   - Verticals have time to migrate

3. **Removal** (MAJOR version only)
   - Breaking change applied
   - Migration guide published
   - Release notes highlight breaking changes

### Channels

- **stable**: Production-ready, tested on ≥2 verticals, no known critical bugs
- **beta**: Early access, breaking changes allowed, pre-release suffix (e.g. `-beta.1`)

**Promotion**: `v1.2.0-beta.3` → `v1.2.0` (after beta testing complete)

**Enforcement**: GitHub Actions + manual review before release publication.

---

## 4. Release Metadata Schema (Core MUST Provide)

Every Core release MUST include `release_metadata.json`.

### Location

- GitHub Release: attached as asset
- URL: `https://github.com/vitruvyan/vitruvyan-core/releases/download/v1.2.0/release_metadata.json`

### JSON Schema

```json
{
  "version": "1.2.0",
  "release_date": "2026-02-19T16:45:00Z",
  "channel": "stable",
  "contracts_version": "1.0.0",
  "changes": {
    "breaking": [],
    "features": [
      "New PostgresAgent connection pooling",
      "Added vit upgrade command"
    ],
    "fixes": [
      "Fixed Qdrant timeout issue #123"
    ]
  },
  "migration_guide_url": "https://docs.vitruvyan.io/migration/1.2.0",
  "minimum_vertical_version": {
    "finance": "0.2.0"
  },
  "checksum": {
    "type": "git_commit_sha",
    "value": "089178e4c5a2b1f9d3e7c4a9f8b2d5e1a3c7f9b0"
  }
}
```

### Checksum Specification

**Type**: `git_commit_sha` (Git commit hash of release tag)

**Verification Algorithm**:
```bash
# vit upgrade verifies:
git rev-parse v1.2.0  # → MUST match checksum.value
```

**Implementation** (Python):
```python
import subprocess

def verify_release(tag: str, expected_sha: str) -> bool:
    actual_sha = subprocess.check_output(
        ["git", "rev-parse", tag]
    ).decode().strip()
    
    if actual_sha != expected_sha:
        raise SecurityError(
            f"Checksum mismatch: expected {expected_sha}, got {actual_sha}"
        )
    return True
```

**Rationale**: 
- Zero overhead (Git built-in)
- Cryptographically secure (SHA-1, migrating to SHA-256)
- Industry standard (Docker image digests, Kubernetes manifests)
- Immutable (Git commits are content-addressable)

### Required Fields

- `version` (string, SemVer)
- `release_date` (ISO 8601)
- `channel` ("stable" | "beta")
- `contracts_version` (string, SemVer)
- `changes` (object with `breaking`, `features`, `fixes` arrays)

### Optional Fields

- `migration_guide_url` (REQUIRED if `changes.breaking` is non-empty)
- `minimum_vertical_version` (map of vertical → min version)
- `checksum` (artifact verification)

**Enforcement**: `vit update` downloads + verifies checksum before showing to user.

---

## 5. Update Flow Guarantees (Bidirectional Contract)

### Core MUST

✅ Validate compatibility BEFORE applying upgrade  
✅ Create snapshot (git tag) BEFORE checkout  
✅ Run smoke tests AFTER upgrade  
✅ Auto-rollback on ANY failure (smoke test fail, pip install error, etc.)  
✅ Provide audit trail (`.vitruvyan/upgrade_history.json`)  
✅ Support channels (stable/beta) via manifest  
✅ Respect `min_core_version` / `max_core_version` constraints  
✅ Block upgrade if `contracts_major` mismatch  

### Core MAY

- Provide warnings for deprecated features (non-blocking)
- Cache release metadata locally (5-minute TTL)
- Parallel smoke test execution (if vertical supports it)

### Core MUST NOT

- Override vertical's `validated_*` lists (respect client validation)
- Apply upgrade without compatibility check
- Skip smoke tests (even if `--force` flag)
- Expose secrets in logs/output

### Vertical MUST

✅ Declare version constraints in `vertical_manifest.yaml`  
✅ Provide `smoke_tests/run.sh` (exit 0 = pass)  
✅ Import ONLY from `contracts/` (never from Core internals)  
✅ Handle deprecation warnings (migrate within 6-month window)  
✅ Update manifest when Core version changes  

### Vertical MAY

- Skip beta updates (stick to stable channel)
- Opt-in to specific breaking changes via `breaking_changes_allowlist`
- Define custom `smoke_tests_timeout` (60-600s range)

### Vertical MUST NOT

- Import from `vitruvyan_core.core.*` (use `contracts.*` instead)
- Modify Core files (all changes via PRs to Core repo)
- Skip smoke tests (no `--no-test` flag exists)

---

## 6. Error Codes (Standardized)

### CLI Exit Codes (`vit` command)

| Code | Meaning | Example |
|------|---------|---------|
| `0` | Success | Upgrade completed |
| `1` | Blocked | Incompatible version, manifest violation |
| `2` | Error | Network failure, GitHub API timeout |
| `3` | Rollback executed | Upgrade failed, state restored |

### JSON Output (`vit update --json`)

```json
{
  "status": "blocked",
  "current_version": "1.0.0",
  "latest_version": "1.2.0",
  "compatible": false,
  "reason": "contracts_major_mismatch",
  "details": "Core requires contracts v2, vertical declares v1",
  "timestamp": "2026-02-19T16:45:00Z"
}
```

**Status values**: `compatible`, `blocked`, `error`, `rollback_executed`

---

## 7. Rollback Scope (MVP)

### Pre-Upgrade Validation

**REQUIRED BEFORE UPGRADE**: `vit upgrade` MUST verify clean working tree.

**Checks**:
1. **No uncommitted changes**:
   ```bash
   git diff-index --quiet HEAD --
   # Exit code 0 = clean, non-zero = dirty
   ```

2. **No untracked files in critical paths**:
   - `vitruvyan_core/`
   - `contracts/`
   - (Vertical files in `domains/` are allowed)

**Error Handling**:
```bash
vit upgrade
# Output if dirty:
# ❌ Upgrade blocked: Uncommitted changes detected
#
# Modified files:
#   vitruvyan_core/core/agents/postgres_agent.py
#   domains/finance/intent_config.py
#
# Actions:
#   git commit -am "WIP: save changes"
#   OR
#   git stash
#
# Exit code: 1 (blocked)
```

**Rationale**: 
- Prevents data loss (uncommitted work)
- Ensures rollback can restore exact state
- Zero tolerance for safety-critical operations
- Industry standard (Kubernetes, Docker, apt)

**Override**: NONE (no `--force` flag, safety-critical)

---

### Included in Rollback

✅ Core codebase (git checkout snapshot tag)  
✅ Python dependencies (`requirements.txt` snapshot restored)  
✅ Audit log entry (`.vitruvyan/upgrade_history.json`)  

### NOT Included (Future Phases)

❌ Database migrations (vertical responsibility)  
❌ Qdrant collections schema (vertical responsibility)  
❌ Redis Streams schema (vertical responsibility)  
❌ Docker image rollback (orchestration-level, not Core)  

**Rationale**: MVP focuses on Core codebase + dependencies. Data migrations are vertical-specific and require custom logic.

---

## 8. Audit Trail Format

### Location

`.vitruvyan/upgrade_history.json` (Git repository root)

**Absolute Path Resolution**:
```bash
# vit determines repo root:
git rev-parse --show-toplevel
# → /home/vitruvyan/vitruvyan-core/

# Audit trail location:
# → /home/vitruvyan/vitruvyan-core/.vitruvyan/upgrade_history.json
```

**Rationale**:
- **Installation-scoped**: One audit trail per Core installation (not per vertical)
- **Shared history**: All verticals in same installation share upgrade history
- **Git-aligned**: Repo root is deterministic (`git rev-parse --show-toplevel`)
- **Portable**: `.vitruvyan/` added to `.gitignore` (local state, not committed)

**Structure** (example):
```
/home/vitruvyan/vitruvyan-core/       ← Git repo root
├── .vitruvyan/
│   └── upgrade_history.json         ← Installation-level audit
├── vitruvyan_core/                  ← Core code
└── domains/
    ├── finance/                     ← Vertical 1
    └── healthcare/                  ← Vertical 2
```

**Multi-Installation** (independent machines):
```
Machine A (Finance Team):
  /opt/finance-install/
    └── .vitruvyan/upgrade_history.json  ← Independent history

Machine B (Healthcare Team):
  /home/healthcare/vitruvyan/
    └── .vitruvyan/upgrade_history.json  ← Independent history
```

### Schema

```json
{
  "history": [
    {
      "timestamp": "2026-02-19T16:45:00Z",
      "from_version": "1.0.0",
      "to_version": "1.2.0",
      "status": "success",
      "snapshot_tag": "pre-upgrade-20260219-164500",
      "smoke_tests_duration": 35.2,
      "smoke_tests_result": "pass"
    },
    {
      "timestamp": "2026-02-20T10:00:00Z",
      "from_version": "1.2.0",
      "to_version": "1.3.0",
      "status": "rollback_executed",
      "snapshot_tag": "pre-upgrade-20260220-100000",
      "smoke_tests_duration": 120.0,
      "smoke_tests_result": "fail",
      "rollback_reason": "Smoke tests failed: PostgresAgent import error"
    }
  ]
}
```

**Retention**: Last 50 upgrade attempts (configurable).

---

## 9. CI/CD Enforcement (Phase 3)

### Pre-Release Compatibility Gate

Before publishing Core release to GitHub:

1. CI fetches all active verticals from registry
2. For each vertical:
   - Parse `vertical_manifest.yaml`
   - Check compatibility with new Core version
   - Run vertical's smoke tests against new Core
3. If ANY vertical fails: **BLOCK RELEASE**
4. Generate compatibility matrix report (artifact)

### Required Vertical Registry

```json
{
  "verticals": [
    {
      "name": "finance",
      "repo": "git@github.com:vitruvyan/vitruvyan-finance.git",
      "branch": "main",
      "status": "active"
    }
  ]
}
```

**Location**: `docs/contracts/platform/vertical_registry.json`

**Enforcement**: GitHub Actions workflow (`.github/workflows/release-compatibility-check.yml`)

---

## 10. Support Window Policy

### Core Version Support

- **Latest MAJOR**: Fully supported (security + bug fixes)
- **Latest-1 MAJOR**: Security fixes only (12 months)
- **Older MAJOR**: End of life (upgrade required)

Example (Feb 2026):
- Core v2.x.x: Fully supported
- Core v1.x.x: Security fixes until Feb 2027
- Core v0.x.x: EOL (upgrade to v1+ or v2+)

### Vertical Compatibility Window

Verticals using EOL Core versions will be:
1. Warned via `vit status` (3 months before EOL)
2. Blocked from production deployment (after EOL date)

**Enforcement**: `vit status` shows support window expiration.

---

## 11. Exemptions & Overrides

### No Exemptions Allowed

The following contract rules have **ZERO exemptions**:

- ❌ Smoke tests MUST run (no `--skip-tests` flag)
- ❌ Compatibility check MUST pass (no `--force-incompatible`)
- ❌ Rollback on smoke test failure (automatic, no override)

**Rationale**: Safety-critical rules. Manual overrides introduce production risk.

### Allowed Overrides (with Audit Trail)

- ✅ Beta channel upgrades (explicit opt-in via manifest)
- ✅ Breaking changes allowlist (vertical opts-in to specific changes)
- ✅ Custom smoke test timeout (60-600s range)

**Enforcement**: All overrides logged in audit trail.

---

## 12. Deprecation Example (Full Cycle)

### Scenario: Deprecate `PostgresAgent.execute_raw()`

**N-1 MINOR (v1.5.0)** - Deprecation announced:
```python
@deprecated(version="1.5.0", removal="2.0.0", alternative="execute()")
def execute_raw(self, sql):
    logger.warning("execute_raw() is deprecated, use execute()")
    return self.execute(sql)
```

**Docs**:
- `CHANGELOG.md`: "⚠️ `execute_raw()` deprecated, use `execute()` instead"
- Migration guide: Step-by-step replacement examples

**Window**: 6 months (until v2.0.0)

**v2.0.0 (MAJOR)** - Removal:
```python
# Method removed
# Breaking change documented in release_metadata.json:
{
  "changes": {
    "breaking": [
      "Removed PostgresAgent.execute_raw() (deprecated since v1.5.0)"
    ]
  },
  "migration_guide_url": "https://docs.vitruvyan.io/migration/2.0.0"
}
```

**Vertical Action**:
- Sees deprecation warning in v1.5.0
- Updates code before v2.0.0 release
- `vit upgrade` to v2.0.0 works (smoke tests pass)

---

## 13. Contract Versioning

This contract uses **independent versioning** from Core.

- **Current**: V1 (binding as of Feb 19, 2026)
- **Changes**: MAJOR version bump = breaking contract change
- **Backward compatibility**: V2 must support V1 verticals (grace period: 12 months)

**Future Versions**:
- V2: May add database migration rollback (Phase 4+)
- V3: May add multi-core-version support (vertical runs 2 Core versions in parallel)

**Update Process**:
1. Publish draft contract (V2-draft)
2. Feedback period (30 days)
3. Approve + publish (V2)
4. Deprecate V1 (12-month window)
5. V1 EOL

---

## 14. Compliance Checklist

### For Core Team

- [ ] Every release includes `release_metadata.json`
- [ ] SemVer followed strictly (MAJOR/MINOR/PATCH)
- [ ] Breaking changes have 6-month deprecation window
- [ ] CI compatibility gate runs pre-release
- [ ] Migration guide published for breaking changes

### For Vertical Team

- [ ] `vertical_manifest.yaml` present and valid
- [ ] `smoke_tests/run.sh` present and executable
- [ ] Imports only from `contracts/` (not Core internals)
- [ ] Smoke tests complete in <5 minutes
- [ ] Version constraints accurate (`min_core_version`, `max_core_version`)

**How to Verify**:
```bash
# Vertical compliance check
vit verify-manifest

# Output:
# ✅ Manifest valid
# ✅ Smoke tests executable
# ✅ No Core internal imports detected
# ✅ Compatibility: Core 1.0.0 - 1.x.x
```

---

## 15. References

- **Implementation**: `vitruvyan_core/core/platform/update_manager/`
- **Masterplan**: `docs/knowledge_base/development/core_update_upgrade_masterplan.md`
- **Vertical Contract**: `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`

---

## Signatures (Binding Agreement)

**Core Team**: [Approved - Feb 19, 2026]  
**Platform Team**: [Approved - Feb 19, 2026]  
**Vertical Teams**: [Binding upon vertical creation]

---

**END OF CONTRACT V1**
