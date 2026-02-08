# Neural Engine API Examples

Developer-friendly scripts demonstrating how to consume the Neural Engine REST API.

## 📚 Purpose

These examples teach you **how to USE the Neural Engine API** (consumption). For guides on **how to IMPLEMENT custom providers/strategies** (extension), see [`vitruvyan_core/core/neural_engine/domain_examples/`](../../../vitruvyan_core/core/neural_engine/domain_examples/).

**Separation of Concerns**:
- **This folder** (`examples/`) → API consumption (frontend devs, service orchestration)
- **`domain_examples/`** → Core implementation (creating new domains: Finance, Healthcare, Logistics)

---

## 🚀 Prerequisites

### 1. Docker Container Running
```bash
# Start Neural Engine service
docker compose up neural_engine

# Verify it's running
docker ps | grep neural_engine
# Expected: Container on port 8003
```

### 2. Required Tools
```bash
# Install jq for JSON parsing (bash scripts)
sudo apt install jq -y

# Install python requests (Python script)
pip install requests
```

### 3. Test Service Health
```bash
curl http://localhost:8003/health
# Expected: {"status": "healthy", ...}
```

---

## 📋 Available Examples

### 01. Health Check (`01_health_check.sh`)
**Purpose**: Verify service health and dependency status

```bash
./01_health_check.sh
```

**What it tests**:
- Service reachability
- Orchestrator health
- Data Provider health
- Scoring Strategy health

**Expected output**:
```
✅ Service is healthy (HTTP 200)

📊 Service Status: healthy
   - Orchestrator: healthy
   - Data Provider: healthy
   - Scoring Strategy: healthy
```

---

### 02. Basic Screening (`02_screen_basic.sh`)
**Purpose**: Multi-factor screening with balanced profile

```bash
./02_screen_basic.sh
```

**What it tests**:
- POST `/screen` endpoint
- Top K filtering (5 entities)
- Composite score computation
- Percentile bucketing

**Expected output**:
```
✅ Screening completed (HTTP 200)

📊 Summary:
   - Total entities evaluated: 10
   - Processing time: 45ms

🏆 Top 5 Ranked Entities:
   1. E004 (composite: 1.23, percentile: 95.5%)
   2. E007 (composite: 0.85, percentile: 87.2%)
   ...
```

---

### 03. Screening with Filters (`03_screen_filters.sh`)
**Purpose**: Filter entities by group and use stratification

```bash
./03_screen_filters.sh
```

**What it tests**:
- Filter by group (GroupA)
- Stratification mode (`by_group`)
- Bucket assignment (top/middle/bottom)

**Expected output**:
```
✅ Screening with filters completed (HTTP 200)

📊 Summary:
   - Total entities evaluated: 5
   - Filter applied: group=GroupA

🏆 Top 5 Ranked Entities (GroupA only):
   1. E001 (bucket: top, score: 1.45)
   2. E004 (bucket: top, score: 1.23)
   ...
```

---

### 04. Rank by Feature (`04_rank_by_feature.sh`)
**Purpose**: Single-feature ranking by momentum z-score

```bash
./04_rank_by_feature.sh
```

**What it tests**:
- POST `/rank` endpoint
- Single feature ranking
- Z-score extraction
- Higher-is-better sorting

**Expected output**:
```
✅ Ranking completed (HTTP 200)

📊 Summary:
   - Feature: momentum
   - Total entities ranked: 10

🏆 Top 5 by Momentum Z-Score:
   1. E009 (z-score: 1.67, percentile: 93.2%)
   2. E004 (z-score: 1.23, percentile: 87.8%)
   ...
```

---

### 05. Compare Profiles (`05_compare_profiles.py`)
**Purpose**: Python script comparing balanced vs aggressive profiles

```bash
python3 05_compare_profiles.py

# Or with custom URL
BASE_URL=http://production-ip:8003 python3 05_compare_profiles.py
```

**What it tests**:
- Profile weight differences
- Ranking order changes
- Processing time comparison
- Python `requests` library usage

**Expected output**:
```
🔬 Neural Engine Profile Comparison
Endpoint: http://localhost:8003
======================================================================
✅ Service health check passed

======================================================================
  BALANCED PROFILE
======================================================================
Rank   Entity       Composite    Percentile   Bucket    
----------------------------------------------------------------------
1      E004         1.234        95.5         top       
2      E007         0.856        87.2         middle    
...

======================================================================
  RANKING COMPARISON
======================================================================
Entity       Balanced Rank   Aggressive Rank  Δ Rank    
----------------------------------------------------------------------
E001         5               3                +2        
E004         1               1                0         
...
```

---

## 🎯 Usage Patterns

### Running All Scripts Sequentially
```bash
# Make all scripts executable
chmod +x examples/*.sh

# Run all tests
for script in examples/*.sh; do
    echo "Running $script..."
    ./$script
    echo ""
done
```

### Custom Base URL (Production)
```bash
# Set environment variable
export BASE_URL=http://production-ip:8003

# Run any script
./examples/02_screen_basic.sh
```

### Integration with CI/CD
```yaml
# .github/workflows/test-neural-engine.yml
- name: Test Neural Engine API
  run: |
    docker compose up -d neural_engine
    sleep 5
    ./services/core/api_neural_engine/examples/01_health_check.sh
    ./services/core/api_neural_engine/examples/02_screen_basic.sh
```

---

## 🧪 Testing Checklist

Use these examples to validate:

- [ ] **Health endpoint**: `01_health_check.sh` returns healthy status
- [ ] **Basic screening**: `02_screen_basic.sh` returns 5 ranked entities
- [ ] **Filtered screening**: `03_screen_filters.sh` respects GroupA filter
- [ ] **Single feature**: `04_rank_by_feature.sh` ranks by momentum correctly
- [ ] **Profile comparison**: `05_compare_profiles.py` shows weight differences

---

## 🔗 Related Documentation

| Document | Purpose |
|----------|---------|
| [`vitruvyan_core/core/neural_engine/domain_examples/`](../../../vitruvyan_core/core/neural_engine/domain_examples/) | How to implement custom IDataProvider/IScoringStrategy |
| [`services/core/api_neural_engine/README.md`](../README.md) | API documentation, deployment guide |
| [`vitruvyan_core/contracts/README.md`](../../../vitruvyan_core/contracts/README.md) | Contract architecture rationale |
| [`docs/NEURAL_ENGINE_ARCHITECTURE.md`](../../../docs/NEURAL_ENGINE_ARCHITECTURE.md) | Complete architecture overview |

---

## 🐛 Troubleshooting

### Issue: "curl: (7) Failed to connect"
**Solution**: Make sure container is running
```bash
docker compose up -d neural_engine
docker logs neural_engine
```

### Issue: "jq: command not found"
**Solution**: Install jq
```bash
sudo apt install jq -y
```

### Issue: "HTTP 503 Service Unavailable"
**Solution**: Check dependency health
```bash
curl http://localhost:8003/health | jq '.dependencies'
```

### Issue: Python script "ModuleNotFoundError: No module named 'requests'"
**Solution**: Install requests
```bash
pip install requests
```

---

## 📝 Next Steps

After running these examples:

1. **Modify scripts**: Change `profile`, `top_k`, `filters` to test different scenarios
2. **Create custom domain**: Follow [`domain_examples/README.md`](../../../vitruvyan_core/core/neural_engine/domain_examples/README.md) to implement Finance/Healthcare/Logistics providers
3. **Production deployment**: See [`README.md`](../README.md) section "Deployment to Production VPS"
4. **Add pytest tests**: Create `tests/test_api_integration.py` for automated validation

---

**Examples Created**: February 8, 2026  
**Target Audience**: Frontend developers, service orchestration developers, DevOps  
**Scope**: API consumption only (not implementation)
