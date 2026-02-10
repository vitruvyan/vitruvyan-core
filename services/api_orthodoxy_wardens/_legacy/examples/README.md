# 🏛️ Orthodoxy Wardens API Examples

**Purpose**: Practical scripts demonstrating how to consume the Orthodoxy Wardens REST API.

---

## 🚀 Quick Start

### Prerequisites

**For Bash Scripts** (`.sh`):
- Docker container running: `docker compose up vitruvyan_api_orthodoxy_wardens`
- `curl` installed: `sudo apt install curl`
- `jq` installed: `sudo apt install jq`

**For Python Scripts** (`.py`):
- `requests` library: `pip install requests`

---

## 📁 Available Examples

### 1. **01_health_check.sh** - Health Check
```bash
./01_health_check.sh
```
**Tests**: Service health, Synaptic Conclave listeners, blessing_level  
**Use case**: Verify Orthodoxy Wardens is running before making audit requests

---

### 2. **02_initiate_audit.py** - Initiate Audit Workflow
```bash
python3 02_initiate_audit.py
```
**Tests**: POST `/confession/initiate` → async audit workflow  
**Use case**: Trigger audit confession and poll for results

---

### 3. **03_query_recent_logs.sh** - Query Audit Logs
```bash
./03_query_recent_logs.sh
```
**Tests**: GET `/logs/recent` with PostgreSQL filters  
**Use case**: Query last 10 audit events from orthodoxy_logs table

---

## 🎯 When to Use What?

| Task | Tool | Reason |
|------|------|--------|
| **Health check** | Bash (`.sh`) | Single API call, immediate results |
| **Audit workflow** | Python (`.py`) | Multi-step logic (initiate → poll → process) |
| **Log queries** | Bash (`.sh`) | Simple GET request with filters |

---

## 📖 Usage Patterns

### Pattern 1: Quick Validation (Bash)
```bash
# Make scripts executable
chmod +x *.sh

# Run health check
./01_health_check.sh
```

### Pattern 2: Audit Workflow (Python)
```bash
# Initiate audit and wait for completion
python3 02_initiate_audit.py

# Expected output:
# 🏛️ Triggering audit confession...
# ✅ Confession initiated: ID=abc-123
# ⏳ Polling status...
# ✅ Audit completed: Status=blessed
```

---

## 🔗 Related Documentation

**For API Reference** (detailed endpoint specs):
- See: `services/governance/api_orthodoxy_wardens/docs/API_REFERENCE.md`

**For Implementation Guide** (event handlers, Sacred Roles):
- See: `services/governance/api_orthodoxy_wardens/docs/ORTHODOXY_WARDENS_GUIDE.md`

**For Architecture** (Synaptic Conclave, LangGraph):
- See: `services/governance/api_orthodoxy_wardens/docs/ARCHITECTURAL_DECISIONS.md`

---

**Last Updated**: February 8, 2026  
**Maintainer**: Vitruvyan Core Team  
**Orthodoxy Wardens Port**: 9006 (external), 8006 (internal)
