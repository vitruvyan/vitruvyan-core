# 🧠 Neural Engine API Examples

**Purpose**: Practical scripts demonstrating how to consume the Neural Engine REST API.

---

## 🚀 Quick Start

### Prerequisites

**For Bash Scripts** (`.sh`):
- Docker container running: `docker compose up neural_engine`
- `curl` installed: `sudo apt install curl`
- `jq` installed: `sudo apt install jq`

**For Python Scripts** (`.py`):
- `requests` library: `pip install requests`

---

## 📁 Available Examples

### Bash Scripts (Single API Calls)

#### 1. **01_health_check.sh** - Health Check
```bash
./01_health_check.sh
```
**Tests**: Service health, dependencies status, version info  
**Use case**: Verify Neural Engine is running before making requests

---

#### 2. **02_screen_basic.sh** - Basic Screening
```bash
./02_screen_basic.sh
```
**Tests**: POST `/screen` with balanced profile, top-k=5  
**Use case**: Simple multi-factor screening with default settings

---

#### 3. **03_screen_filters.sh** - Screening with Filters
```bash
./03_screen_filters.sh
```
**Tests**: POST `/screen` with group filters (stratification)  
**Use case**: Filter entities by group/sector before ranking

---

#### 4. **04_rank_by_feature.sh** - Single-Feature Ranking
```bash
./04_rank_by_feature.sh
```
**Tests**: POST `/rank` by momentum feature  
**Use case**: Rank entities by single metric (no profile weighting)

---

### Python Scripts (Multi-Step Workflows)

#### 5. **05_compare_profiles.py** - Profile Comparison
```bash
python3 05_compare_profiles.py
```
**Tests**: Compare balanced vs aggressive scoring profiles  
**Use case**: Understand how profile weights affect ranking

---

#### 6. **06_prometheus_metrics.sh** - Metrics Exposition
```bash
./06_prometheus_metrics.sh
```
**Tests**: GET `/metrics` endpoint (Prometheus format)  
**Use case**: Monitor Neural Engine performance (requests, latency, errors)

---

## 🎯 When to Use What?

| Task | Tool | Reason |
|------|------|--------|
| **Single API call** | Bash (`.sh`) | Zero setup, immediate results |
| **Documentation** | Bash (`.sh`) | Shows exact curl command to copy |
| **Multi-step logic** | Python (`.py`) | JSON parsing, comparisons, assertions |
| **Comparisons** | Python (`.py`) | Side-by-side analysis with formatting |
| **Stress testing** | Python (`.py`) | Loop 100+ requests, measure latency |

---

## 📖 Usage Patterns

### Pattern 1: Quick Validation (Bash)
```bash
# Make scripts executable
chmod +x *.sh

# Run all bash tests in sequence
./01_health_check.sh && \
./02_screen_basic.sh && \
./03_screen_filters.sh && \
./04_rank_by_feature.sh
```

### Pattern 2: Detailed Analysis (Python)
```bash
# Compare different profiles
python3 05_compare_profiles.py

# Expected output:
# === Balanced Profile ===
# 1. E004: 1.23 (risk-adjusted composite)
# 2. E007: 0.98
# 3. E002: 0.76
#
# === Aggressive Profile ===
# 1. E010: 1.87 (high momentum weight)
# 2. E004: 1.45
# 3. E003: 1.12
```

---

## 🔍 Common Use Cases

### Use Case 1: Onboarding New Developer
**Goal**: Understand Neural Engine API in 5 minutes

```bash
# Step 1: Verify service is running
./01_health_check.sh

# Step 2: See basic screening
./02_screen_basic.sh

# Step 3: Read curl commands in scripts (self-documenting)
cat 02_screen_basic.sh
```

---

### Use Case 2: Integration Testing
**Goal**: Verify API before deploying to production

```bash
# Test all endpoints
for script in *.sh; do
    echo "Testing $script..."
    ./"$script" || exit 1
done
echo "✅ All tests passed"
```

---

### Use Case 3: Performance Profiling
**Goal**: Compare profile performance

```bash
# Run comparison test
python3 05_compare_profiles.py > profile_comparison.txt

# Analyze results
cat profile_comparison.txt
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"
**Cause**: Neural Engine container not running

**Solution**:
```bash
docker compose up -d neural_engine
# Wait 5 seconds for startup
sleep 5
./01_health_check.sh
```

---

### Error: "jq: command not found"
**Cause**: `jq` not installed

**Solution**:
```bash
sudo apt update && sudo apt install -y jq
```

---

### Error: "Module 'requests' not found"
**Cause**: Python `requests` library missing

**Solution**:
```bash
pip install requests
# Or: pip3 install requests
```

---

## 🔗 Related Documentation

**For API Reference** (detailed endpoint specs):
- See: `services/core/api_neural_engine/README.md`

**For Implementation Guide** (extending Neural Engine with new domains):
- See: `vitruvyan_core/core/neural_engine/domain_examples/README.md`

**For Architecture Overview** (design philosophy, contracts):
- See: `docs/NEURAL_ENGINE_ARCHITECTURE.md`

---

## 📝 Script Maintenance

**Adding New Examples**:
1. Follow naming convention: `XX_description.sh` or `XX_description.py`
2. Add shebang line: `#!/bin/bash` or `#!/usr/bin/env python3`
3. Make executable: `chmod +x XX_description.sh`
4. Update this README with description and use case

**Testing Before Commit**:
```bash
# Verify all bash scripts run without errors
for script in *.sh; do
    bash -n "$script" || echo "Syntax error in $script"
done

# Verify all Python scripts have valid syntax
for script in *.py; do
    python3 -m py_compile "$script" || echo "Syntax error in $script"
done
```

---

**Last Updated**: February 8, 2026  
**Maintainer**: Vitruvyan Core Team  
**Neural Engine Version**: 2.0.0 (Domain-Agnostic)
