# infrastructure/ — Deployment & Operations

> **Last Updated**: February 12, 2026  
> **Purpose**: Docker orchestration, monitoring, secrets management  
> **Type**: Infrastructure-as-code, ops tooling

---

## 🎯 Cosa Contiene

`infrastructure/` contiene tutto il necessario per **deployare e monitorare** Vitruvyan in produzione:
- Docker Compose configurations
- Grafana dashboards
- Prometheus metrics
- Secrets management (Ansible Vault)

**Caratteristiche**:
- ✅ **Single Command Deploy**: `docker compose up -d`
- ✅ **Observability**: Grafana + Prometheus + custom dashboards
- ✅ **Secrets Management**: Ansible Vault per credenziali
- ✅ **Multi-Service**: 14+ services orchestrati

---

## 📂 Struttura

```
infrastructure/
├── docker/                      # Docker Compose orchestration
│   ├── docker-compose.yml       → Main compose file (14+ services)
│   ├── .env.example             → Environment variables template
│   └── volumes/                 → Persistent data directories
│
├── monitoring/                  # Observability stack
│   ├── grafana/                 → Grafana configuration
│   │   ├── dashboards/          → JSON dashboard definitions
│   │   │   ├── synaptic_bus_dashboard.json       → Bus monitoring
│   │   │   ├── orthodoxy_wardens_dashboard.json  → Governance metrics
│   │   │   └── ...
│   │   └── provisioning/        → Auto-provisioning configs
│   ├── prometheus/              → Prometheus configuration
│   │   └── prometheus.yml       → Scrape configs, targets
│   └── docs/                    → Monitoring documentation
│       └── GRAFANA_DASHBOARD_VALIDATION_REPORT.md
│
└── secrets/                     # Secrets management (gitignored)
    ├── ansible-vault.yml.enc    → Encrypted credentials
    └── .vault_pass              → Vault password (local only)
```

---

## 🐳 Docker Compose

### Services Orchestrati (14+)

**Infra Core** (3):
```yaml
postgres:         # PostgreSQL 16 (port 9432)
redis:            # Redis 7 (port 9379)
qdrant:           # Qdrant vector store (ports 9333, 9334)
```

**Vitruvyan Services** (9):
```yaml
graph:            # LangGraph orchestration (port 9004)
neural:           # Neural engine (port 9003)
mcp:              # Model Context Protocol (port 8020)
memory_orders:    # Memory & coherence (port 9008)
vault_keepers:    # Archival & persistence (port 9007)
orthodoxy_wardens: # Governance & validation (port 9006)
codex_hunters:    # Data discovery (port 9005)
babel_gardens:    # Linguistic analysis (port 9009)
pattern_weavers:  # Pattern detection (port 9011)
```

**Listeners** (6):
```yaml
memory_orders_listener:     # Consumes memory.* channels
vault_keepers_listener:     # Consumes vault.* channels
orthodoxy_wardens_listener: # Consumes orthodoxy.* channels
codex_hunters_listener:     # Consumes codex.* channels
babel_gardens_listener:     # Consumes babel.* channels
pattern_weavers_listener:   # Consumes pattern.* channels
```

**Monitoring** (2):
```yaml
prometheus:       # Metrics aggregation (port 9090)
grafana:          # Dashboards & visualization (port 3000)
```

### Deploy Commands

```bash
cd infrastructure/docker

# Deploy everything
docker compose up -d --build

# Deploy specific service
docker compose up -d --build memory_orders memory_orders_listener

# Check status
docker compose ps

# View logs
docker compose logs -f memory_orders

# Stop all
docker compose down

# Stop with volume cleanup
docker compose down -v
```

---

## 📊 Monitoring (Grafana + Prometheus)

### Grafana Dashboards

**Accesso**: http://localhost:3000  
**Default credentials**: admin/admin

**Dashboards disponibili**:

| Dashboard | Purpose | Metrics |
|-----------|---------|---------|
| **Synaptic Bus** | Redis Streams monitoring | Stream lengths, consumer lag, events/sec |
| **Orthodoxy Wardens** | Governance metrics | BLESSED/PURIFIED/HERETICAL, validation times |
| **Memory Orders** | Coherence analysis | Cache hits, vector searches, embedding times |
| **Vault Keepers** | Archival operations | Archive requests, snapshot sizes |

### Prometheus Metrics

**Accesso**: http://localhost:9090

**Targets**:
- Vitruvyan services: `http://<service>:<port>/metrics`
- Infrastructure: PostgreSQL exporter, Redis exporter

**Custom metrics** (esempi):
```
vitruvyan_bus_stream_length{stream="vault.archive.requested"}
vitruvyan_orthodoxy_verdicts_total{verdict="blessed"}
vitruvyan_memory_coherence_score{collection="default"}
```

### Dashboard Development

Vedere [monitoring/docs/](monitoring/docs/) per:
- Dashboard creation guide
- Metric naming conventions
- Grafana provisioning

---

## 🔐 Secrets Management

### Ansible Vault

**Encrypted credentials** in `secrets/ansible-vault.yml.enc`:
```yaml
# Encrypted content
postgres_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
redis_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

**Decrypt**:
```bash
ansible-vault decrypt infrastructure/secrets/ansible-vault.yml.enc
```

**Encrypt**:
```bash
ansible-vault encrypt infrastructure/secrets/ansible-vault.yml
```

**Edit**:
```bash
ansible-vault edit infrastructure/secrets/ansible-vault.yml.enc
```

⚠️ **NEVER commit** `.vault_pass` o file decriptati!

---

## 🌐 Environment Variables

### Template (.env.example)

```bash
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=9432
POSTGRES_DB=vitruvyan
POSTGRES_USER=vitruvyan
POSTGRES_PASSWORD=<from-vault>

# Redis
REDIS_HOST=redis
REDIS_PORT=9379
REDIS_PASSWORD=<from-vault>

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=9333
QDRANT_API_KEY=<from-vault>

# OpenAI
OPENAI_API_KEY=<from-vault>
```

### Setup

```bash
cd infrastructure/docker
cp .env.example .env
# Edit .env with real values (decrypt from vault)
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# 1. Copy environment template
cd infrastructure/docker
cp .env.example .env

# 2. Decrypt secrets
ansible-vault decrypt ../secrets/ansible-vault.yml.enc

# 3. Populate .env with decrypted values
# (or use script to auto-populate from vault)
```

### 2. Deploy Stack

```bash
# Full stack deploy
docker compose up -d --build

# Check all services are up
docker compose ps

# Check logs
docker compose logs -f graph neural mcp
```

### 3. Verify Health

```bash
# Check individual services
curl http://localhost:9004/health  # Graph
curl http://localhost:9008/health  # Memory Orders
curl http://localhost:8020/health  # MCP

# Check infrastructure
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana
```

### 4. Access Monitoring

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Qdrant UI**: http://localhost:9334/dashboard

---

## 📚 Documentazione

**Module docs**: [monitoring/docs/](monitoring/docs/)
- Grafana dashboard validation
- Prometheus configuration
- Metric definitions

**Global docs**: [../docs/](../docs/)
- [Architecture](../docs/architecture/)
- [Changelog](../docs/changelog/)

---

## 🎯 Design Principles

1. **Single Command Deploy**: `docker compose up -d` per tutto
2. **Observability-First**: Metrics + dashboards per ogni service
3. **Secrets Never Committed**: Ansible Vault + .gitignore
4. **Stateless Services**: Persistent data in volumes, servizi riavviabili
5. **Health Checks**: Ogni service espone `/health`

---

## 📖 Link Utili

- **[Services](../services/README_SERVICES.md)** — Microservizi deployati da questo stack
- **[Vitruvyan Core](../vitruvyan_core/README_VITRUVYAN_CORE.md)** — Core library
- **[Scripts](../scripts/README_SCRIPTS.md)** — Deploy automation, maintenance scripts
- **[Docs Portal](../docs/index.md)** — Entry point documentazione

---

**Purpose**: Deploy, orchestrate, monitor Vitruvyan in produzione.  
**Tools**: Docker Compose, Grafana, Prometheus, Ansible Vault.  
**Status**: 14+ services orchestrati, 4 dashboards Grafana, secrets encrypted.
