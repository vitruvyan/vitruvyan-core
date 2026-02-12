# scripts/ — Automation & Maintenance Scripts

> **Last Updated**: February 12, 2026  
> **Purpose**: Deployment automation, maintenance scripts, utilities  
> **Type**: Bash, Python, Expect scripts

---

## 🎯 Cosa Contiene

`scripts/` contiene **script di automazione** per deployment, maintenance, e operazioni comuni.

**Caratteristiche**:
- ✅ **Deployment Automation**: Deploy remoto, validazione infra
- ✅ **Maintenance**: Database cleanup, cache flush, log rotation
- ✅ **Utilities**: Health checks, metric collection, backup
- ✅ **Interactive**: Expect scripts per deploy automatici

---

## 📂 Struttura (Typical)

```
scripts/
├── deploy/                      # Deployment scripts
│   ├── deploy_remote.sh         → Remote deployment via SSH
│   ├── deploy_expect.exp        → Automated deploy (Expect script)
│   └── validate_infra.sh        → Post-deploy validation
│
├── maintenance/                 # Maintenance routines
│   ├── cleanup_db.py            → PostgreSQL cleanup (old data)
│   ├── flush_redis.sh           → Redis cache flush
│   └── rotate_logs.sh           → Log rotation
│
├── monitoring/                  # Monitoring utilities
│   ├── health_check.sh          → Check all services health
│   ├── collect_metrics.py       → Metric collection script
│   └── alert_if_down.sh         → Simple alerting
│
├── backup/                      # Backup scripts
│   ├── backup_postgres.sh       → PostgreSQL backup
│   ├── backup_qdrant.sh         → Qdrant vector store backup
│   └── restore.sh               → Restore from backup
│
└── utils/                       # General utilities
    ├── reset_test_env.sh        → Reset test environment
    └── generate_test_data.py    → Generate test fixtures
```

---

## 🚀 Deploy Scripts

### deploy_remote.sh

**Purpose**: Deploy Vitruvyan to remote server via SSH

**Usage**:
```bash
./scripts/deploy/deploy_remote.sh <host> [branch]

# Examples
./scripts/deploy/deploy_remote.sh production main
./scripts/deploy/deploy_remote.sh staging develop
```

**What it does**:
1. SSH to remote host
2. Pull latest code from git
3. Rebuild Docker containers
4. Run health checks
5. Validate deployment

### deploy_expect.exp

**Purpose**: Automated deploy with password/prompt handling (Expect script)

**Usage**:
```bash
expect scripts/deploy/deploy_expect.exp <host> <password>
```

**What it does**:
- Automates interactive SSH session
- Handles sudo password prompts
- Runs deployment commands
- Captures output for logging

### validate_infra.sh

**Purpose**: Post-deploy infrastructure validation

**Usage**:
```bash
./scripts/deploy/validate_infra.sh

# Check specific service
./scripts/deploy/validate_infra.sh memory_orders
```

**Checks**:
- ✅ All services running (Docker ps)
- ✅ Health endpoints responding (/health)
- ✅ Database connectivity (PostgreSQL, Redis, Qdrant)
- ✅ Log errors (check recent logs)

---

## 🧹 Maintenance Scripts

### cleanup_db.py

**Purpose**: Clean old data from PostgreSQL (archival, logs, temp data)

**Usage**:
```bash
python scripts/maintenance/cleanup_db.py --days 30

# Dry run (show what would be deleted)
python scripts/maintenance/cleanup_db.py --days 30 --dry-run
```

### flush_redis.sh

**Purpose**: Flush Redis cache (development/testing)

**Usage**:
```bash
# Flush all keys
./scripts/maintenance/flush_redis.sh

# Flush specific database
./scripts/maintenance/flush_redis.sh 1
```

⚠️ **DANGER**: Use only in dev/test environments!

### rotate_logs.sh

**Purpose**: Rotate application logs (compress old, remove ancient)

**Usage**:
```bash
./scripts/maintenance/rotate_logs.sh

# Keep last 7 days
./scripts/maintenance/rotate_logs.sh --days 7
```

---

## 📊 Monitoring Scripts

### health_check.sh

**Purpose**: Check health of all Vitruvyan services

**Usage**:
```bash
./scripts/monitoring/health_check.sh

# Output
✅ graph (9004): healthy
✅ memory_orders (9008): healthy
❌ vault_keepers (9007): unreachable
```

### collect_metrics.py

**Purpose**: Collect custom metrics (outside Prometheus)

**Usage**:
```bash
python scripts/monitoring/collect_metrics.py --output metrics.json
```

### alert_if_down.sh

**Purpose**: Simple alerting (webhook on service down)

**Usage**:
```bash
# Check service, alert if down
./scripts/monitoring/alert_if_down.sh memory_orders http://slack-webhook-url
```

---

## 💾 Backup Scripts

### backup_postgres.sh

**Purpose**: Backup PostgreSQL database

**Usage**:
```bash
./scripts/backup/backup_postgres.sh

# Backup to specific location
./scripts/backup/backup_postgres.sh /path/to/backups
```

**Output**: `vitruvyan_backup_YYYYMMDD_HHMMSS.sql.gz`

### backup_qdrant.sh

**Purpose**: Backup Qdrant vector store

**Usage**:
```bash
./scripts/backup/backup_qdrant.sh

# Backup specific collection
./scripts/backup/backup_qdrant.sh memory_vectors
```

### restore.sh

**Purpose**: Restore from backup

**Usage**:
```bash
./scripts/backup/restore.sh /path/to/backup.sql.gz
```

⚠️ **DANGER**: Overwrites existing data!

---

## 🔧 Utility Scripts

### reset_test_env.sh

**Purpose**: Reset test environment (flush all data, restart containers)

**Usage**:
```bash
./scripts/utils/reset_test_env.sh
```

**What it does**:
1. Stop all containers
2. Remove volumes (flush data)
3. Rebuild images
4. Start fresh containers
5. Run migrations

### generate_test_data.py

**Purpose**: Generate test fixtures (entities, signals, events)

**Usage**:
```bash
python scripts/utils/generate_test_data.py --entities 100 --signals 500
```

---

## 🎯 Usage Patterns

### Running Scripts

```bash
# Make executable
chmod +x scripts/deploy/deploy_remote.sh

# Run from repository root
./scripts/deploy/deploy_remote.sh production

# Or from scripts directory
cd scripts/deploy
./deploy_remote.sh production
```

### Environment Variables

Scripts tipicamente usano `.env` o variabili d'ambiente:

```bash
# Export before running
export POSTGRES_HOST=localhost
export POSTGRES_PORT=9432
./scripts/backup/backup_postgres.sh

# Or inline
POSTGRES_HOST=remote-host ./scripts/backup/backup_postgres.sh
```

---

## 📚 Documentazione

### Script-Specific Docs

Ogni script ha docstring/comments interni:

```bash
#!/bin/bash
# deploy_remote.sh - Deploy Vitruvyan to remote server via SSH
#
# Usage:
#   ./deploy_remote.sh <host> [branch]
#
# Arguments:
#   host   - Remote hostname (e.g., production, staging)
#   branch - Git branch to deploy (default: main)
#
# Examples:
#   ./deploy_remote.sh production main
#   ./deploy_remote.sh staging develop
```

### Related Docs

- [Infrastructure README](../infrastructure/README_INFRASTRUCTURE.md) — Docker Compose, deployment
- [Services README](../services/README_SERVICES.md) — Service configuration
- [Docs Portal](../docs/index.md) — Global documentation

---

## 🎯 Design Principles

1. **Idempotent**: Scripts can be run multiple times safely
2. **Verbose**: Log all actions (use `set -x` in bash)
3. **Fail-Fast**: Exit on error (`set -e` in bash)
4. **Documented**: Usage in script header (docstring/comments)
5. **Environment-Aware**: Dev/staging/prod detection

---

## 📖 Link Utili

- **[Infrastructure](../infrastructure/README_INFRASTRUCTURE.md)** — Docker Compose, monitoring
- **[Services](../services/README_SERVICES.md)** — Service deployment
- **[Tests](../tests/README_TESTS.md)** — Test environment setup
- **[README Principale](../README.md)** — Repository overview

---

**Purpose**: Automate deployment, maintenance, monitoring, backup operations.  
**Pattern**: Bash/Python scripts, idempotent, fail-fast, documented.  
**Status**: Deploy automation (remote SSH), backup/restore, health checks.
