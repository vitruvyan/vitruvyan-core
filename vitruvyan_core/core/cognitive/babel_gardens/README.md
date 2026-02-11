# Babel Gardens — Universal Semantic Signal Extraction Layer

> "The Tower accepts all tongues, weaves all signals, grounds all meaning."

**Sacred Order**: Perception (Linguistic Processing & Semantic Grounding)  
**Version**: 2.1 (Domain-Agnostic Refactoring)  
**Status**: Production Ready

---

## What is Babel Gardens?

Babel Gardens è il **layer di estrazione semantica universale** di Vitruvyan OS. Trasforma testo non strutturato in **segnali semantici domain-agnostic**, misurabili e tracciabili, che altri Sacred Orders possono consumare per ragionamento, correlazione e archival.

**Prima del refactoring v2.1** (legacy):
- Focus su sentiment analysis (finance-specific)
- Fusion di modelli multipli (gemma_sentiment, finbert, gemma_multilingual)
- Output: sentiment score [-1, 1]

**Dopo il refactoring v2.1** (attuale):
- **Domain-agnostic signal extraction**: ANY vertical (finance, cybersecurity, healthcare, legal, sports, IoT, etc.)
- **YAML-driven configuration**: Define custom signals per vertical
- **Plugin architecture**: Wrap ANY model (FinBERT, SecBERT, BioClinicalBERT, etc.) → SignalExtractionResult
- **Output**: Structured signals with explainability traces

---

## Core Capabilities

### 1. Universal Signal Extraction
Estrae **segnali semantici** da testo usando modelli domain-specific:
- **Finance**: `sentiment_valence` [-1,1], `market_fear_index` [0,1]
- **Cybersecurity**: `threat_severity` [0,1], `exploit_imminence` [0,1]
- **Healthcare**: `diagnostic_confidence` [0,1], `treatment_urgency` [0,10]
- **Legal**: `precedent_strength` [0,1], `liability_exposure` [0,1]
- **YOUR DOMAIN**: Create `signals_<domain>.yaml`

### 2. YAML-Driven Configuration
Define signals without code changes:
```yaml
# signals_finance.yaml
metadata:
  vertical: finance
  taxonomy_categories: [earnings, market_outlook, ...]

signals:
  - name: sentiment_valence
    description: "Sentiment polarity detected in financial text"
    value_range: [-1.0, 1.0]
    models: ["model:finbert"]
    output_type: float
```

### 3. Plugin Architecture
Wrap ANY HuggingFace model → SignalExtractionResult:
```python
from plugins.finance_signals import FinanceSignalsPlugin

plugin = FinanceSignalsPlugin()
signals = plugin.extract_signals(
    text="Apple announced record earnings...",
    config=finance_config
)

# Output: [SignalExtractionResult(
#     signal_name='sentiment_valence',
#     value=0.65,
#     confidence=0.88,
#     extraction_trace={'method': 'model:finbert', 'timestamp': '...'}
# )]
```

### 4. Explainability by Design
Every signal includes:
- **extraction_trace**: Method used (model:finbert, heuristic:volatility_calc)
- **confidence**: Model confidence [0,1]
- **timestamp**: When signal was extracted
- **taxonomy_match**: Matched categories (earnings, market_outlook)
- **model_version**: Frozen for reproducibility

---

## Architecture

### LIVELLO 1 (Pure Domain Logic)
```
vitruvyan_core/core/cognitive/babel_gardens/domain/
├── signal_schema.py          # SignalSchema, SignalConfig, SignalExtractionResult
├── config.py                  # YAML loading (load_config_from_yaml, merge_configs)
└── entities.py                # Legacy sentiment entities (deprecated)
```

**Sacred Laws** (invariants):
1. "The Tower accepts all tongues" (multilingual support)
2. "Words carry meaning, not secrets" (embeddings only)
3. "Signals are inferred, never invented" (grounded in text evidence)
4. "Explainability is sacred" (Orthodoxy Wardens integration)
5. "The Gardens grow with configuration" (YAML-driven extensibility)

### LIVELLO 2 (Service Layer)
```
services/api_babel_gardens/plugins/
├── __init__.py
├── finance_signals.py         # FinanceSignalsPlugin (FinBERT wrapper)
├── cybersecurity_signals.py   # Planned (SecBERT wrapper)
└── healthcare_signals.py      # Planned (BioClinicalBERT wrapper)
```

**Plugins are optional** — use YAML + generic extractor without HuggingFace if needed.

---

## Main Modules

### 1. SignalSchema (`domain/signal_schema.py`)
**Purpose**: Define domain-agnostic signal primitives  
**Key Classes**:
- `SignalSchema`: Metadata about a signal (name, description, value_range, models)
- `SignalConfig`: Collection of signals for a vertical (finance, cyber, etc.)
- `SignalExtractionResult`: Immutable result of signal extraction
- `MultiSignalFusionConfig`: Config for cross-signal correlation

**Pure domain logic**: Zero I/O, no model loading, no external dependencies.

### 2. YAML Config Loader (`domain/signal_schema.py`)
**Purpose**: Load vertical configs from YAML  
**Key Functions**:
- `load_config_from_yaml(path)`: Parse + validate YAML → SignalConfig
- `merge_configs(configs)`: Combine signals from multiple verticals

**Example**:
```python
from core.cognitive.babel_gardens.domain import load_config_from_yaml

finance_config = load_config_from_yaml("examples/signals_finance.yaml")
cyber_config = load_config_from_yaml("examples/signals_cybersecurity.yaml")

# Merge for cross-vertical analysis
merged = merge_configs([finance_config, cyber_config])
# → 7 signals total (finance: 3 + cyber: 4)
```

### 3. FinanceSignalsPlugin (`plugins/finance_signals.py`)
**Purpose**: Wrap FinBERT model → finance signals  
**Key Method**: `extract_signals(text, config) → List[SignalExtractionResult]`

**Features**:
- Lazy model loading (load on first use)
- Automatic taxonomy matching (financial keywords)
- Explainability traces (Orthodoxy compliance)
- Confidence calibration

**Example**:
```python
plugin = FinanceSignalsPlugin()
signals = plugin.extract_signals(
    text="Apple stock surges on earnings beat",
    config=finance_config
)

# Output: [
#   SignalExtractionResult(signal_name='sentiment_valence', value=0.72, confidence=0.91),
#   SignalExtractionResult(signal_name='market_fear_index', value=0.23, confidence=0.85)
# ]
```

### 4. Legacy Modules (`_legacy/`)
**Archived** (Phase 2 refactoring):
- `emotion_detector.py`: Deprecated (use SignalSchema)
- `sentiment_fusion.py`: Deprecated (use FinanceSignalsPlugin)
- Backward compatibility wrappers will be removed in Phase 4

---

## Sacred Orders Integration

### 🧠 Neural Engine
**Consumes**: SignalExtractionResult → features dict  
**Adapter**: `services/adapters/babel_to_neural.py` (SignalToFeatureAdapter)

```python
from services.adapters.babel_to_neural import signals_to_features

# Babel Gardens extracts signals
signals = plugin.extract_signals(text="...", config=finance_config)

# Adapter converts to Neural Engine format
features = signals_to_features(signals, legacy_sentiment=True)
# {"sentiment_valence": 0.65, "market_fear_index": 0.35, "sentiment": "positive"}

# Neural Engine ranks entities
engine.run(entity_features={"AAPL": features})
```

### 🗄️ Vault Keepers
**Consumes**: SignalExtractionResult → SignalTimeseries archival  
**Integration**: `vitruvyan_core/core/governance/vault_keepers` (SignalArchivist)

```python
from core.governance.vault_keepers.consumers import archive_signal_timeseries

# Archive signal timeseries for AAPL
timeseries = archive_signal_timeseries(
    entity_id="AAPL",
    signal_results=signals,  # From Babel Gardens
    vertical="finance",
    retention_days=365
)

# Vault Keepers stores in PostgreSQL (signal_timeseries table)
```

### 🕸️ Pattern Weavers
**Consumes**: SignalTimeseries (from Vault Keepers) → correlation patterns  
**Integration**: Planned (Phase 4)

```python
from core.governance.pattern_weavers import correlate_signals

# Detect cross-vertical correlations
patterns = correlate_signals(
    entity_id="AAPL",
    signals=["sentiment_valence", "market_fear_index"],
    window_days=30
)
```

### 📊 Orthodoxy Wardens
**Validates**: Explainability traces (extraction_trace metadata)  
**Integration**: Automatic (signals include extraction_trace by design)

---

## Usage Examples

### 1. Extract Finance Signals
```python
from core.cognitive.babel_gardens.domain import load_config_from_yaml
from plugins.finance_signals import FinanceSignalsPlugin

# Load config
config = load_config_from_yaml("examples/signals_finance.yaml")

# Extract signals
plugin = FinanceSignalsPlugin()
signals = plugin.extract_signals(
    text="Apple announced record Q4 earnings, beating analyst expectations.",
    config=config
)

# Result: [
#   SignalExtractionResult(signal_name='sentiment_valence', value=0.78, confidence=0.92),
#   SignalExtractionResult(signal_name='market_fear_index', value=0.15, confidence=0.88)
# ]
```

### 2. Create Custom Vertical
```yaml
# signals_sports.yaml
metadata:
  vertical: sports
  taxonomy_categories: [injuries, performance, transfers, contracts]

signals:
  - name: injury_severity
    description: "Severity of player injury (0=minor, 1=career-ending)"
    value_range: [0.0, 1.0]
    models: ["heuristic:injury_lexicon"]
    
  - name: performance_trend
    description: "Player performance trend (-1=declining, 1=improving)"
    value_range: [-1.0, 1.0]
    models: ["model:sportsbert"]
```

### 3. Cross-Vertical Fusion
```python
# Merge finance + cybersecurity signals for geopolitical analysis
finance_config = load_config_from_yaml("signals_finance.yaml")
cyber_config = load_config_from_yaml("signals_cybersecurity.yaml")

merged_config = merge_configs([finance_config, cyber_config])
# → 7 signals (finance: 3 + cyber: 4)

# Extract all signals from text about cyberattack on financial institution
all_signals = plugin.extract_signals(text="...", config=merged_config)
```

---

## Testing

### Unit Tests (LIVELLO 1)
```bash
# Test domain-agnostic signal schema
python3 -m pytest tests/test_domain_agnostic.py -v

# Test YAML loading + plugins
python3 -m pytest tests/test_phase2_yaml_plugins.py -v
```

### Integration Tests (LIVELLO 2)
```bash
# Inside Docker container
docker exec core_babel_gardens python3 /tmp/test_signal_extraction.py
```

---

## Configuration

### Environment Variables
```bash
# Model cache directory
MODEL_CACHE_DIR=/var/vitruvyan/models

# Vertical configs directory
SIGNAL_CONFIGS_DIR=/app/vitruvyan_core/core/cognitive/babel_gardens/examples

# Plugin settings
ENABLE_FINANCE_PLUGIN=true
ENABLE_CYBER_PLUGIN=false  # Not yet implemented
ENABLE_HEALTHCARE_PLUGIN=false  # Not yet implemented
```

### Supported Verticals (v2.1)
| Vertical | Signals | Plugin | Status |
|----------|---------|--------|--------|
| Finance | sentiment_valence, market_fear_index, volatility_perception | ✅ FinanceSignalsPlugin | Production |
| Cybersecurity | threat_severity, exploit_imminence, attribution_confidence, lateral_movement_risk | ⏳ Planned | Phase 4 |
| Maritime | operational_disruption, delay_severity, route_viability, cargo_risk | ⏳ Planned | Phase 4 |
| Healthcare | diagnostic_confidence, treatment_urgency, patient_risk_score, adverse_event_probability | ⏳ Planned | Phase 4 |
| Legal | precedent_strength, liability_exposure, verdict_probability, compliance_risk | ⏳ Planned | Phase 4 |
| **Your Domain** | Custom signals | 📝 YAML config | Always Available |

---

## Migration from Legacy

### v1.x (Legacy Sentiment API) → v2.1 (SignalSchema)
**Before** (legacy):
```python
# Old sentiment API (deprecated)
result = sentiment_fusion.analyze(text="...")
# → {"sentiment": "positive", "score": 0.78}
```

**After** (v2.1):
```python
# New signal extraction API
signals = plugin.extract_signals(text="...", config=finance_config)
# → [SignalExtractionResult(signal_name='sentiment_valence', value=0.78, ...)]
```

**Backward Compatibility** (Phase 3 - current):
```python
# Adapter maintains legacy API during migration
from services.adapters.babel_to_neural import signals_to_features

features = signals_to_features(signals, legacy_sentiment=True)
# → {"sentiment_valence": 0.78, "sentiment": "positive", "sentiment_score": 0.78}
```

See [MIGRATION_GUIDE_V2.1.md](docs/MIGRATION_GUIDE_V2.1.md) for full details.

---

## Documentation

- **Charter**: [philosophy/charter.md](philosophy/charter.md) — Sacred mandate and laws
- **Migration Guide**: [docs/MIGRATION_GUIDE_V2.1.md](docs/MIGRATION_GUIDE_V2.1.md) — v1.x → v2.1 upgrade path
- **Phase 1 Report**: [docs/REFACTORING_REPORT_V2.1_PHASE1.md](docs/REFACTORING_REPORT_V2.1_PHASE1.md) — Domain-agnostic infrastructure
- **Phase 2 Report**: [docs/REFACTORING_REPORT_V2.1_PHASE2.md](docs/REFACTORING_REPORT_V2.1_PHASE2.md) — YAML loading + plugins
- **Examples**: [examples/README.md](examples/README.md) — YAML configs for 5 verticals
- **Knowledge Base**: `.github/Vitruvyan_Appendix_K_Babel_Gardens.md` — Architectural deep dive

---

## Roadmap

### ✅ Phase 1 (Complete)
- SignalSchema domain primitives
- 3 vertical YAML examples (finance, cyber, maritime)
- Domain-agnostic tests

### ✅ Phase 2 (Complete)
- YAML config loading (load_config_from_yaml, merge_configs)
- FinanceSignalsPlugin (FinBERT wrapper)
- 2 additional verticals (healthcare, legal)

### ✅ Phase 3 (Complete)
- Babel → Neural Engine adapter (SignalToFeatureAdapter)
- Babel → Vault Keepers integration (SignalArchivist)
- Backward compatibility (dual-mode)

### ⏳ Phase 4 (Q2 2026)
- Additional plugins (SecBERT, MaritimeBERT, BioClinicalBERT, LegalBERT)
- Pattern Weavers signal correlation
- Legacy removal (_legacy/ deletion)

---

## Contributing

When adding a new vertical:
1. Create `signals_<vertical>.yaml` in `examples/`
2. (Optional) Create plugin in `services/api_babel_gardens/plugins/<vertical>_signals.py`
3. Test with existing core code (zero changes needed)
4. Submit PR with YAML config + test results

**Principle**: Babel Gardens is **infinitely extensible** via YAML. Code changes only needed for new plugins.

---

**Version**: 2.1.0  
**Last Updated**: February 11, 2026  
**Status**: Production Ready (Phase 1-3 Complete)
