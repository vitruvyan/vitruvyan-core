# 📂 Codex Hunters Scripts Directory

**Sacred Order**: Codex Hunters (Data Acquisition & Population)  
**Last Updated**: 2025-11-09

---

## 📋 Overview

This directory contains **backfill and data population scripts** used by Codex Hunters to initialize and maintain the dual-memory architecture (PostgreSQL + Qdrant).

### Architecture Pattern

```
Manual Execution (Admin) → backfill_*.py → CrewAI Tools → PostgreSQL + Qdrant
                                               ↑
Redis Events (Automated) → Codex API ────→ Same Tools
```

**Key Insight**: Backfill scripts and Codex Hunters container use **the same underlying CrewAI Tools**, ensuring data consistency.

---

## 🗂️ File Inventory

### Core Backfill Scripts

| Script | Purpose | Target | Scheduler |
|--------|---------|--------|-----------|
| `backfill_technical_logs.py` | Populate trend/momentum/volatility logs | PostgreSQL | Manual/Cron |
| `backfill_momentum_vectors.py` | Populate momentum_vectors collection | Qdrant | Manual |
| `backfill_trend_vectors.py` | Populate trend_vectors collection | Qdrant | Manual |
| `backfill_volatility_vectors.py` | Populate volatility_vectors collection | Qdrant | Manual |
| `backfill_sentiment_vectors.py` | Populate sentiment_embeddings collection | Qdrant | Manual |
| `backfill_all.py` | Orchestrator for full backfill (techn + sentiment) | Both | Manual |

### Event-Driven Scripts

| Script | Purpose | Trigger |
|--------|---------|---------|
| `codex_event_scheduler.py` | Schedule periodic Redis events | Cron (daily 02:00 UTC) |
| `codex_event_listener.py` | Listen to Redis events and trigger expeditions | Always running |

### Support Scripts

| Script | Purpose |
|--------|---------|
| `ensure_momentum_schema.py` | Verify/create momentum_logs table schema |

---

## 🔧 Usage

### Manual Backfill (Initial Population)

```bash
# From project root
cd ~/vitruvyan-os

# 1. Technical indicators for all tickers (PostgreSQL)
python3 vitruvyan_os/core/governance/codex_hunters/scripts/backfill_technical_logs.py

# 2. Vector embeddings for all tickers (Qdrant)
python3 vitruvyan_os/core/governance/codex_hunters/scripts/backfill_momentum_vectors.py
python3 vitruvyan_os/core/governance/codex_hunters/scripts/backfill_trend_vectors.py
python3 vitruvyan_os/core/governance/codex_hunters/scripts/backfill_volatility_vectors.py

# 3. All-in-one (technical + sentiment)
python3 vitruvyan_os/core/governance/codex_hunters/scripts/backfill_all.py
```

### Automated Scheduling (Production)

**Current Setup** (from `~/vitruvyan` workspace):
```bash
# Cron jobs (check with: crontab -l)
0 2 * * * /home/caravaggio/vitruvyan/scripts/codex_event_scheduler.py

# Systemd service (always running)
# Check: systemctl status codex-event-listener
```

**Future Setup** (when migrated to `~/vitruvyan-os`):
- Update cron paths to use `~/vitruvyan-os/vitruvyan_os/core/governance/codex_hunters/scripts/`
- Update systemd service paths accordingly

---

## 🧪 Testing

```bash
# Run integration tests
cd ~/vitruvyan-os
python3 vitruvyan_os/core/governance/codex_hunters/tests/test_backfill_integration.py

# Expected output:
# ✅ PASS - Backfill Imports
# ✅ PASS - Database Connections  
# ✅ PASS - Scheduler Integration
# ✅ PASS - Embedding API
```

---

## 🔗 Dependencies

### Python Packages
- `pandas` + `pandas_ta` - Technical analysis
- `yfinance` - Market data
- `httpx` - Embedding API client
- `psycopg2` - PostgreSQL
- `qdrant-client` - Qdrant

### External Services
- **PostgreSQL** (localhost:5432) - Structured data storage
- **Qdrant** (vitruvyan_qdrant:6333) - Vector storage
- **Embedding API** (vitruvyan_api_embedding:8010) - Vector generation
- **Redis** (vitruvyan_redis:6379) - Event bus

### Internal Dependencies
- `core.leo.postgres_agent` - PostgreSQL interface
- `core.leo.qdrant_agent` - Qdrant interface
- `core.crewai.tools.*` - Technical analysis tools
- `core.cognitive_bus.redis_client` - Event publishing

---

## 📊 Data Flow

### PostgreSQL Tables Populated
```
momentum_logs (ticker, rsi, macd, roc, timestamp)
trend_logs (ticker, sma_short/med/long, trends, timestamp)
volatility_logs (ticker, atr, stdev, signal, timestamp)
sentiment_scores (ticker, combined_score, sentiment_tag, created_at)
```

### Qdrant Collections Populated
```
momentum_vectors (384-dim embeddings from momentum text)
trend_vectors (384-dim embeddings from trend text)
volatility_vectors (384-dim embeddings from volatility text)
sentiment_embeddings (384-dim embeddings from sentiment text)
```

---

## 🚨 Important Notes

### DO NOT Move Original Scripts
The scripts in `~/vitruvyan/scripts/` are **still used by cron/systemd**. These copies in `codex_hunters/scripts/` are for:
1. Organization (logical grouping with Sacred Order)
2. Future migration reference
3. Testing in new structure

### Migration Checklist (When Ready)
- [ ] Update crontab to use new paths
- [ ] Update systemd service files
- [ ] Test backfill from new location
- [ ] Verify Redis events still trigger
- [ ] Update documentation references
- [ ] Remove old scripts from `~/vitruvyan/scripts/`

---

## 🔍 Troubleshooting

### "No active tickers found"
```bash
# Check tickers table
PGPASSWORD='@Caravaggio971' psql -h 161.97.140.157 -U vitruvyan_user -d vitruvyan \
  -c "SELECT COUNT(*) FROM tickers WHERE active = true;"
```

### "Embedding API not reachable"
```bash
# Check if container is running
docker ps | grep embedding

# Check logs
docker logs vitruvyan_api_embedding --tail 50
```

### "Redis events not triggering"
```bash
# Check scheduler
crontab -l | grep codex

# Check listener service
systemctl status codex-event-listener

# Test Redis connection
docker exec -it vitruvyan_redis redis-cli PING
```

---

## 📚 Related Documentation

- **Architecture**: `docs/VITRUVYAN_COMPLETE_ARCHITECTURE_MAP.md`
- **RAG System**: `.github/Vitruvyan_Appendix_E_RAG_System.md`
- **Sacred Orders**: `.github/copilot-instructions.md` (Epistemic Hierarchy)
- **Codex Hunters**: `core/governance/codex_hunters/README.md` (if exists)

---

## 📝 Changelog

### 2025-11-09 - Sacred Orders Reorganization
- **COPIED** 9 backfill/scheduler scripts from `~/vitruvyan/scripts/`
- Created integration test suite
- Documented architecture and usage patterns
- **Status**: Scripts copied, original location still active (migration pending)

---

**Maintained by**: Codex Hunters Sacred Order  
**Contact**: Via Redis Cognitive Bus or GitHub Issues
