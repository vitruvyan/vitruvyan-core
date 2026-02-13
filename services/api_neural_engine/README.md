# 🧠 Vitruvyan Neural Engine API

> **Last updated**: February 13, 2026

**Port**: 8003  
**Status**: ✅ Production Ready (Domain-Agnostic v2.0)  
**Architecture**: Pluggable domain providers via contracts (IDataProvider, IScoringStrategy)

---

## 🎯 Purpose

Neural Engine is the **CORE quantitative ranking service** in Vitruvyan ecosystem. It:

1. **Reads data from domain providers** (PostgreSQL, APIs, files)
2. **Normalizes via z-scores** (global, stratified, composite modes)
3. **Applies profile weights** (balanced, aggressive, momentum-focused, etc.)
4. **Ranks entities** by composite score
5. **Returns top-k entities** with explainability metadata

**Philosophy**: *Read data. Normalize. Rank. Return.*

---

## 🏗️ Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Endpoints (main.py)                                │
│  - POST /screen   - Multi-factor screening                  │
│  - POST /rank     - Single-factor ranking                   │
│  - GET  /health   - Health check                            │
│  - GET  /metrics  - Prometheus metrics                      │
│  - GET  /profiles - List scoring profiles                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│  EngineOrchestrator (modules/engine_orchestrator.py)        │
│  - Initializes NeuralEngine with domain provider + strategy │
│  - Caches results (30s TTL)                                 │
│  - Health checks for dependencies                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│  NeuralEngine (vitruvyan_core.core.neural_engine)           │
│  - Domain-agnostic orchestrator                             │
│  - Executes 8-step pipeline:                                │
│    1. Load universe (via IDataProvider)                     │
│    2. Load features (via IDataProvider)                     │
│    3. Compute z-scores (via ZScoreCalculator)               │
│    4. Apply time decay (optional)                           │
│    5. Compute composite score (via IScoringStrategy)        │
│    6. Apply risk adjustment (via IScoringStrategy)          │
│    7. Rank entities (via RankingEngine)                     │
│    8. Return results                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│  Domain Implementations (pluggable contracts)               │
│  - IDataProvider:     Get universe, features, metadata      │
│  - IScoringStrategy:  Get weights, compute composite, risk  │
│                                                              │
│  Examples:                                                   │
│  - Finance:    TickerDataProvider + FinancialStrategy       │
│  - Healthcare: PatientDataProvider + ClinicalStrategy       │
│  - Mock:       MockDataProvider + MockScoringStrategy       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Container Structure

```
services/api_neural_engine/
├── Dockerfile                  ← Multi-stage build
├── README.md                   ← This file
├── main.py                     ← FastAPI bootstrap (83 lines, < 100 ✅)
├── config.py                   ← Environment variables, settings (extracted Feb 13)
├── api/
│   ├── __init__.py
│   └── routes.py               ← Thin HTTP endpoints (extracted Feb 13)
├── monitoring/
│   ├── __init__.py
│   └── metrics.py              ← Prometheus metric declarations (extracted Feb 13)
├── modules/
│   ├── __init__.py
│   └── engine_orchestrator.py  ← NeuralEngine wrapper
├── schemas/
│   ├── __init__.py
│   └── api_models.py           ← Pydantic request/response models
└── requirements.txt
```

> **Feb 13, 2026**: `main.py` refactored from 386 → 83 lines.
> Extracted `config.py`, `api/routes.py`, `monitoring/metrics.py`.
> Service now at 100% SACRED_ORDER_PATTERN conformance.

---

## 🚀 Quick Start

### Build Container

```bash
# From vitruvyan-core root
docker build -t vitruvyan/neural-engine:latest \
  -f services/core/api_neural_engine/Dockerfile .
```

### Run Container

```bash
docker run -d \
  --name vitruvyan_neural_engine \
  -p 8003:8003 \
  -e DOMAIN=mock \
  -e LOG_LEVEL=info \
  vitruvyan/neural-engine:latest
```

### Health Check

```bash
curl http://localhost:8003/health
# Expected:
# {
#   "status": "healthy",
#   "timestamp": "2026-02-08T...",
#   "version": "2.0.0",
#   "dependencies": {
#     "orchestrator": "healthy",
#     "data_provider": "healthy",
#     "scoring_strategy": "healthy"
#   }
# }
```

---

## 🧪 Developer Examples

**New to Neural Engine?** Start with practical examples in [`examples/`](./examples/)!

We provide **5 ready-to-run scripts** that teach you how to consume the API:

| Script | Purpose | Tech |
|--------|---------|------|
| [`01_health_check.sh`](./examples/01_health_check.sh) | Test service health and dependencies | bash + curl |
| [`02_screen_basic.sh`](./examples/02_screen_basic.sh) | Basic multi-factor screening | bash + curl |
| [`03_screen_filters.sh`](./examples/03_screen_filters.sh) | Screening with filters and stratification | bash + curl |
| [`04_rank_by_feature.sh`](./examples/04_rank_by_feature.sh) | Single-feature ranking (momentum) | bash + curl |
| [`05_compare_profiles.py`](./examples/05_compare_profiles.py) | Compare balanced vs aggressive profiles | Python |

**Quick Test**:
```bash
# Make scripts executable
chmod +x examples/*.sh

# Test health
./examples/01_health_check.sh

# Run basic screening
./examples/02_screen_basic.sh
```

**Full guide**: See [`examples/README.md`](./examples/README.md)

---

## 📖 API Usage

### 1. Multi-Factor Screening (Primary Endpoint)

```bash
curl -X POST http://localhost:8003/screen \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced",
    "top_k": 10,
    "stratification_mode": "global",
    "risk_tolerance": "medium"
  }'
```

**Response**:
```json
{
  "ranked_entities": [
    {
      "rank": 1,
      "entity_id": "E007",
      "entity_name": "Entity 7",
      "composite_score": 1.85,
      "percentile": 90.0,
      "bucket": "top",
      "group": "GroupA"
    },
    ...
  ],
  "profile": "balanced",
  "top_k": 10,
  "stratification_mode": "global",
  "total_entities_evaluated": 100,
  "profile_weights": {
    "momentum": 0.33,
    "trend": 0.33,
    "volatility": 0.34
  },
  "processing_time_ms": 45.3
}
```

### 2. Single-Factor Ranking

```bash
curl -X POST http://localhost:8003/rank \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "momentum",
    "entity_ids": ["E001", "E002", "E003"],
    "top_k": 3,
    "higher_is_better": true
  }'
```

### 3. List Available Profiles

```bash
curl http://localhost:8003/profiles
# {"profiles": [{"name": "balanced", ...}, {"name": "aggressive", ...}]}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DOMAIN` | Domain implementation to load | `mock` | `finance`, `healthcare`, `mock` |
| `LOG_LEVEL` | Logging level | `info` | `debug`, `info`, `warning` |
| `PORT` | Service port | `8003` | `8003` |
| `WORKERS` | Uvicorn workers | `2` | `4` |
| `DB_HOST` | PostgreSQL host (if finance domain) | - | `postgres.vitruvyan.com` |
| `DB_PORT` | PostgreSQL port | `5432` | `5432` |
| `DB_NAME` | Database name | - | `vitruvyan` |
| `DB_USER` | Database user | - | `vitruvyan_user` |
| `DB_PASS` | Database password | - | `***` |

### Domain Loading (TODO)

Currently uses `MockDataProvider` for testing. In production:

```python
# modules/engine_orchestrator.py (TODO)
domain = os.getenv("DOMAIN", "mock")

if domain == "finance":
    from vitruvyan.domains.finance import TickerDataProvider, FinancialScoringStrategy
    self.data_provider = TickerDataProvider(db_connection_string)
    self.scoring_strategy = FinancialScoringStrategy(config_path)
elif domain == "healthcare":
    from vitruvyan.domains.healthcare import PatientDataProvider, ClinicalScoringStrategy
    self.data_provider = PatientDataProvider(ehr_api_url)
    self.scoring_strategy = ClinicalScoringStrategy(config_path)
else:  # mock
    from vitruvyan_core.core.neural_engine.domain_examples import MockDataProvider, MockScoringStrategy
    self.data_provider = MockDataProvider(num_entities=100)
    self.scoring_strategy = MockScoringStrategy()
```

---

## 📊 Observability

### Prometheus Metrics

Exposed at `GET /metrics`:

**HTTP Metrics**:
- `neural_engine_http_requests_total{method, endpoint, status}` - Total requests
- `neural_engine_http_request_duration_seconds{method, endpoint}` - Request latency

**Engine Metrics**:
- `neural_engine_screening_requests_total{profile, stratification_mode}` - Screening requests
- `neural_engine_screening_duration_seconds{profile}` - Screening latency
- `neural_engine_entities_processed_total{operation}` - Entities processed

**Data Provider Metrics**:
- `neural_engine_data_provider_calls_total{method, status}` - Provider calls

**Cache Metrics**:
- `neural_engine_cache_hits_total{cache_type}` - Cache hits
- `neural_engine_cache_misses_total{cache_type}` - Cache misses

**Health Metrics**:
- `neural_engine_service_healthy` - Service health (1=healthy, 0=unhealthy)

### Logs

Structured logs with correlation IDs:

```
2026-02-08 19:00:00 INFO [orchestrator] 🔧 Initializing Engine Orchestrator...
2026-02-08 19:00:01 INFO [orchestrator] ✅ Engine Orchestrator initialized with MockDataProvider
2026-02-08 19:00:05 INFO [main] 🚀 Neural Engine API ready on port 8003
```

---

## 🧪 Testing

### Local Testing (Without Docker)

```bash
# From vitruvyan-core root
export PYTHONPATH=/path/to/vitruvyan-core:$PYTHONPATH

# Run server
python3 -m services.core.api_neural_engine.main

# In another terminal
curl http://localhost:8003/health
curl -X POST http://localhost:8003/screen \
  -H "Content-Type: application/json" \
  -d '{"profile": "balanced", "top_k": 5}'
```

### Integration Tests

```bash
# Run integration tests (TODO - create tests)
pytest tests/integration/test_neural_engine_api.py -v
```

---

## 🔐 Security

### Hardening Checklist

- [x] Non-root user in container (`vitruvyan` uid 1000)
- [x] Health check configured
- [ ] Rate limiting (TODO - add middleware)
- [ ] Authentication (TODO - add JWT validation)
- [ ] Input validation (Pydantic models)
- [ ] SQL injection prevention (PostgresAgent uses parameterized queries)
- [ ] CORS configured (restrict origins in production)

---

## 📚 References

- **Core Engine**: `vitruvyan_core/core/neural_engine/README.md`
- **Contracts**: `vitruvyan_core/contracts/README.md`
- **Domain Examples**: `vitruvyan_core/core/neural_engine/domain_examples/README.md`
- **Architecture Doc**: `docs/NEURAL_ENGINE_ARCHITECTURE.md`
- **Vitruvyan Appendix A**: `.github/Vitruvyan_Appendix_A_Neural_engine.md`

---

## 🤝 Contributing

When modifying this service:

1. **Keep domain-agnostic**: Core logic stays in `vitruvyan_core/`, not here
2. **Follow Vitruvyan patterns**: Prometheus metrics, structured logs, health checks
3. **Test with MockDataProvider first**, then real domain
4. **Update this README** if adding endpoints or changing behavior

---

**Status**: ✅ Phase 1 Complete (Mock domain ready for testing)  
**Next Phase**: Integrate TickerDataProvider + FinancialScoringStrategy from vitruvyan monolith  
**Last Updated**: February 13, 2026
