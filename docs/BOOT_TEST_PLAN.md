# 🔧 Boot Test Plan - Phase 1D Verification

**Date**: December 28, 2025  
**Goal**: Verify vitruvyan-core boots without crashes after node neutralization

---

## 🎯 Minimal Stack for Testing

### Core Services (Required):
1. **postgres** (omni_postgres) - Port 9432
2. **redis** (omni_redis) - Port 9379
3. **qdrant** (omni_qdrant) - Ports 9333, 9334
4. **vitruvyan_api_graph** - Port 9004 (LangGraph orchestration)
5. **vitruvyan_api_neural** - Port 9003 (Neural Engine)

### Optional (can skip for minimal test):
- embedding (omni_api_embedding) - Port 9010
- babel_gardens - Port 9009
- semantic - Port 9002
- monitoring (prometheus, grafana)

---

## 📋 Test Sequence

### Step 1: Check Dependencies
```bash
# Check if Docker is installed
docker --version
docker-compose --version

# Check if Python packages exist
ls -la infrastructure/docker/requirements/
```

### Step 2: Start Infrastructure Only
```bash
cd /home/caravaggio/projects/vitruvyan-core/infrastructure/docker
docker-compose up -d postgres redis qdrant
docker ps
docker logs omni_postgres
docker logs omni_redis
docker logs omni_qdrant
```

### Step 3: Start Neural Engine
```bash
docker-compose up -d vitruvyan_api_neural
docker logs -f omni_api_neural
# Wait for: "Application startup complete"
```

### Step 4: Start Graph API (LangGraph)
```bash
docker-compose up -d vitruvyan_api_graph
docker logs -f omni_api_graph
# Wait for: "Application startup complete"
# Watch for: DOMAIN_NEUTRAL logs from neutralized nodes
```

### Step 5: Health Checks
```bash
# Check all containers running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test endpoints
curl -s http://localhost:9004/health || echo "Graph API not ready"
curl -s http://localhost:9003/health || echo "Neural Engine not ready"
```

### Step 6: Conversational Test
```bash
# Minimal test payload to graph API
curl -X POST http://localhost:9004/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_text": "Analyze entity X under uncertainty",
    "language": "en"
  }' | jq .

# Expected response:
# - NO crashes
# - domain_neutral flags present
# - DOMAIN_NEUTRAL logs in docker logs
```

---

## ✅ Success Criteria

1. **Infrastructure boots**: postgres, redis, qdrant healthy
2. **Neural Engine starts**: No import errors, listens on 9003
3. **Graph API starts**: LangGraph initializes, listens on 9004
4. **Nodes execute**: ticker_resolver, screener, portfolio, advisor log DOMAIN_NEUTRAL
5. **No crashes**: All containers stay running for 2+ minutes
6. **Logs clear**: No Python exceptions, no missing module errors

---

## ❌ Expected Failures (Acceptable)

- Empty/neutral responses (expected - domain plugin not implemented)
- "Not implemented" messages
- Zero analysis results
- NO_ACTION recommendations

---

## 🚨 Red Flags (Stop and Fix)

- ImportError: Module not found
- Syntax errors in neutralized nodes
- Container crashes after 30 seconds
- LangGraph fails to build state graph
- Database connection failures

---

## 📝 Logging Strategy

```bash
# Terminal 1: Follow graph API logs
docker logs -f omni_api_graph 2>&1 | grep -E "(DOMAIN_NEUTRAL|ERROR|entity_resolver|entity_screener|collection_analyzer|decision_advisor)"

# Terminal 2: Follow neural engine logs
docker logs -f omni_api_neural 2>&1 | grep -E "(ERROR|startup|health)"

# Terminal 3: Check all errors
docker-compose logs --tail=50 | grep ERROR
```

---

## 🔄 Rollback Plan

If boot test fails catastrophically:
```bash
# Stop all containers
docker-compose down

# Restore original nodes from backups
cd /home/caravaggio/projects/vitruvyan-core/vitruvyan_core/core/orchestration/langgraph/node
mv ticker_resolver_node.py.backup ticker_resolver_node.py
mv screener_node.py.backup screener_node.py
mv portfolio_node.py.backup portfolio_node.py
mv advisor_node.py.backup advisor_node.py

# Retry boot
```

---

## 📊 Test Results Log

**Start Time**: [TBD]  
**Infrastructure Status**: [TBD]  
**Neural Engine Status**: [TBD]  
**Graph API Status**: [TBD]  
**Node Execution Status**: [TBD]  
**Conversational Test Result**: [TBD]

