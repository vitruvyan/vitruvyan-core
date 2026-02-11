# Babel Gardens - Signal Schema Examples

## Purpose

This directory contains **reference signal configurations** for 3 verticals to demonstrate Babel Gardens' domain-agnostic design.

**Key Principle**: The same core code processes all 3 verticals — only the YAML config changes.

---

## Verticals

### 1. Finance (`signals_finance.yaml`)
**Use Case**: Market sentiment analysis, earnings event detection

**Signals**:
- `sentiment_valence` (polarity: -1 to 1)
- `market_fear_index` (stress level: 0 to 1)
- `volatility_perception` (uncertainty: 0 to 1)

**Taxonomy**: earnings, macroeconomic, fed_policy, geopolitical, sector_rotation

---

### 2. Cybersecurity (`signals_cybersecurity.yaml`)
**Use Case**: Threat intelligence, vulnerability assessment

**Signals**:
- `threat_severity` (CVE severity: 0 to 1)
- `exploit_imminence` (active exploitation risk: 0 to 1)
- `attribution_confidence` (threat actor identification: 0 to 1)
- `lateral_movement_risk` (network pivot risk: 0 to 1)

**Taxonomy**: malware, phishing, ransomware, zero_day, apt, data_exfiltration

---

### 3. Maritime (`signals_maritime.yaml`)
**Use Case**: Shipping logistics, port operations monitoring

**Signals**:
- `operational_disruption` (port/route impact: 0 to 1)
- `delay_severity` (estimated delay: 0 to 10 days)
- `route_viability` (safety/accessibility: 0 to 1)
- `cargo_risk` (damage/theft risk: 0 to 1)

**Taxonomy**: port_congestion, weather_disruption, piracy, labor_strikes

---

## Usage

### Loading a Vertical Config

```python
from core.cognitive.babel_gardens.domain import load_config_from_yaml
from pathlib import Path

# Finance vertical
finance_config = load_config_from_yaml(
    signals_path=Path("examples/signals_finance.yaml")
)

# Cybersecurity vertical
cyber_config = load_config_from_yaml(
    signals_path=Path("examples/signals_cybersecurity.yaml")
)

# Maritime vertical
maritime_config = load_config_from_yaml(
    signals_path=Path("examples/signals_maritime.yaml")
)
```

### Extracting Signals

```python
from core.cognitive.babel_gardens.consumers import SignalExtractor

extractor = SignalExtractor(config=finance_config)

# Same interface across all verticals
result = extractor.extract(
    text="Market volatility spiked after Fed announcement",
    embedding=embed_text(...)
)

# Output (finance):
# {
#   "sentiment_valence": -0.6,
#   "market_fear_index": 0.8,
#   "volatility_perception": 0.9,
#   "confidence": 0.85
# }
```

---

## Cross-Vertical Signal Fusion

Babel Gardens supports **multi-vertical fusion** for hybrid use cases:

```python
# Geopolitical risk impacts both finance AND maritime
combined_config = merge_configs([
    finance_config.select_signals(["market_fear_index"]),
    maritime_config.select_signals(["route_viability", "delay_severity"])
])

result = extractor.extract(
    text="Suez Canal closure disrupts global supply chains, oil prices surge",
    embedding=embed_text(...),
    config=combined_config
)

# Output:
# {
#   "market_fear_index": 0.9,      # Finance signal
#   "route_viability": 0.2,        # Maritime signal
#   "delay_severity": 7.0          # Maritime signal (days)
# }
```

---

## Validation Testing

These configs are used in acceptance tests to prove domain-agnosticism:

```bash
# Test: Same core code works for all verticals
pytest tests/test_domain_agnostic.py

# Expected: All 3 verticals pass with 0 code changes in LIVELLO 1
```

---

## Creating New Verticals

1. Copy `signals_finance.yaml` as template
2. Define domain-specific signals (name, range, aggregation)
3. Define taxonomy categories
4. NO CODE CHANGES required in Babel Gardens core
5. Deploy with new YAML config

**Example verticals** (future):
- Healthcare (clinical urgency, triage priority)
- Legal (case precedent strength, litigation risk)
- Real Estate (market momentum, liquidity)
- Climate (disaster severity, adaptation urgency)

---

## Integration with Sacred Orders

### Orthodoxy Wardens
Validates signal extraction explainability:
```python
# Every signal must have extraction_trace
if signal.explainability_required:
    assert "extraction_trace" in result
    assert "model" in result["extraction_trace"]
```

### Neural Engine
Uses signals as features (replaces hardcoded sentiment):
```python
# Old: features["sentiment"]
# New: features["signals"]["market_fear_index"]
```

### Vault Keepers
Archives signal time-series (not sentiment history):
```python
vault.archive_signal_timeseries(
    signal_name="threat_severity",
    value=0.85,
    timestamp=now(),
    vertical="cybersecurity"
)
```

---

## Sacred Laws Applied

1. ✅ **The Tower accepts all tongues** — All verticals support multilingual input
2. ✅ **Words carry meaning, not secrets** — Only embeddings + signals stored
3. ✅ **Signals are inferred, never invented** — No LLM narrative generation
4. ✅ **Explainability is sacred** — Every signal has `extraction_trace`
5. ✅ **The Gardens grow with configuration** — Add verticals via YAML only

---

## Version
- **Babel Gardens**: v2.1
- **Signal Schema Version**: 2.1.0
- **Created**: February 11, 2026
