# Babel Gardens v2.1 - Migration Guide
**From Sentiment/Emotion to Domain-Agnostic Signals**

---

## Overview

Babel Gardens v2.1 introduces **SignalSchema** — a domain-agnostic abstraction that replaces hardcoded sentiment/emotion concepts. This migration guide helps you transition your code to the new signal-based API.

**Key Changes**:
- ❌ **Deprecated**: `SentimentResult`, `EmotionResult`, hardcoded labels
- ✅ **New**: `SignalSchema`, `SignalExtractionResult`, configurable signals via YAML

---

## Why This Change?

### Problem: Domain Leakage
```python
# OLD (v2.0) - Finance-specific assumptions baked into core
result = sentiment_analyzer.analyze(text)
# Returns: {"positive": 0.7, "negative": 0.1, "neutral": 0.2}
```

This hardcodes financial sentiment labels in the **OS-level primitive**, making it unusable for cybersecurity, maritime, healthcare, etc.

### Solution: Configurable Signals
```python
# NEW (v2.1) - Domain-agnostic
config = load_config_from_yaml("config/signals_finance.yaml")
result = signal_extractor.extract(text, config=config)
# Returns: {"sentiment_valence": 0.6, "market_fear_index": 0.8}
```

Same core code, **different YAML config** for each vertical.

---

## Migration Phases

### Phase 1: Add SignalSchema Infrastructure (Week 1)
**Status**: ✅ **COMPLETED** (this commit)

- ✅ Introduced `SignalSchema`, `SignalConfig`, `SignalExtractionResult`
- ✅ Created 3 vertical YAML examples (finance, cybersecurity, maritime)
- ✅ Updated [charter.md](philosophy/charter.md)
- ✅ Added domain-agnostic tests

**Breaking Changes**: None (infrastructure only)

---

### Phase 2: Create Vertical Plugins (Week 2)
**Status**: ⏳ **PENDING**

**Task**: Move sentiment/emotion logic to plugins

```
services/api_babel_gardens/
├── plugins/
│   ├── finance_signals.py        # FinBERT → sentiment_valence adapter
│   ├── cybersecurity_signals.py  # SecBERT → threat_severity adapter
│   └── maritime_signals.py       # MaritimeBERT → delay_severity adapter
├── _legacy/
│   ├── sentiment_analyzer.py     # OLD: Moved here, marked @deprecated
│   └── emotion_detector.py       # OLD: Moved here, marked @deprecated
```

**Example Plugin**:
```python
# services/api_babel_gardens/plugins/finance_signals.py
from core.cognitive.babel_gardens.domain import SignalSchema, SignalExtractionResult
from .model_adapter import FinBERTAdapter

class FinanceSignalsPlugin:
    """Finance vertical signal extraction (sentiment, market fear)."""
    
    def __init__(self, config: SignalConfig):
        self.config = config
        self.model = FinBERTAdapter()
    
    def extract_sentiment_valence(self, text: str) -> SignalExtractionResult:
        """Extract sentiment_valence signal using FinBERT."""
        model_output = self.model.predict(text)  # {"positive": 0.7, "negative": 0.1}
        
        # Adapt model output to signal value
        signal_value = model_output["positive"] - model_output["negative"]
        
        return SignalExtractionResult(
            signal_name="sentiment_valence",
            value=signal_value,
            confidence=max(model_output.values()),
            extraction_trace={
                "method": "model:finbert",
                "model_version": "1.0.2",
                "timestamp": datetime.utcnow().isoformat(),
                "model_output": model_output
            }
        )
```

---

### Phase 3: Migrate Consumers (Week 3-4)
**Status**: ⏳ **PENDING**

#### 3A. Update Neural Engine Integration

**OLD (v2.0)**:
```python
# Neural Engine receives hardcoded sentiment
features = {
    "sentiment": sentiment_result.label,  # "positive", "negative", "neutral"
    "sentiment_score": sentiment_result.score
}
```

**NEW (v2.1)**:
```python
# Neural Engine receives generic signals dict
features = {
    "signals": {
        "sentiment_valence": 0.6,
        "market_fear_index": 0.8
    }
}
```

**Migration**:
```python
# Add backward compatibility wrapper
def _map_signals_to_legacy_features(signals: Dict[str, float]) -> Dict[str, Any]:
    """Temporary adapter for Neural Engine v1.x compatibility."""
    sentiment_valence = signals.get("sentiment_valence", 0.0)
    
    # Map signal to legacy label
    if sentiment_valence > 0.3:
        legacy_label = "positive"
    elif sentiment_valence < -0.3:
        legacy_label = "negative"
    else:
        legacy_label = "neutral"
    
    return {
        "sentiment": legacy_label,
        "sentiment_score": abs(sentiment_valence),
        # NEW: Also include raw signals
        "signals": signals
    }
```

#### 3B. Update Vault Keepers Archival

**OLD (v2.0)**:
```python
# Hardcoded sentiment history
vault.archive_sentiment(
    entity_id="AAPL",
    sentiment_label="positive",
    score=0.7,
    timestamp=now()
)
```

**NEW (v2.1)**:
```python
# Generic signal time-series
vault.archive_signal_timeseries(
    entity_id="AAPL",
    signal_name="sentiment_valence",
    signal_value=0.6,
    signal_schema=schema,
    timestamp=now()
)
```

#### 3C. Update Pattern Weavers Correlation

**OLD (v2.0)**:
```python
# Correlate emotions over time
correlations = pattern_weaver.correlate_emotions(["joy", "fear", "anger"])
```

**NEW (v2.1)**:
```python
# Correlate arbitrary signals
correlations = pattern_weaver.correlate_signals([
    "sentiment_valence",
    "market_fear_index",
    "volatility_perception"
])
```

---

### Phase 4: Remove Legacy Code (Week 5)
**Status**: ⏳ **PENDING**

1. Delete `_legacy/sentiment_analyzer.py`
2. Delete `_legacy/emotion_detector.py`
3. Remove `SentimentLabel`, `EmotionLabel` enums from `domain/entities.py`
4. Update all docstrings to reference signals (not sentiment)

---

## API Migration Examples

<details>
<summary><b>Example 1: Sentiment Analysis (Finance Vertical)</b></summary>

### Before (v2.0)
```python
from core.cognitive.babel_gardens.consumers import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze("Apple beats earnings, stock surges")

print(result.label)        # "positive"
print(result.score)        # 0.85
print(result.confidence)   # 0.92
```

### After (v2.1)
```python
from core.cognitive.babel_gardens.domain import load_config_from_yaml
from core.cognitive.babel_gardens.consumers import SignalExtractor

config = load_config_from_yaml("config/signals_finance.yaml")
extractor = SignalExtractor(config=config)

result = extractor.extract("Apple beats earnings, stock surges")

print(result["sentiment_valence"])    # 0.75 (positive sentiment)
print(result["market_fear_index"])    # 0.2 (low fear)
print(result["confidence"])           # 0.92
```

**Benefit**: Can now extract **multiple signals** from same text (not just sentiment).

</details>

<details>
<summary><b>Example 2: Threat Intelligence (Cybersecurity Vertical)</b></summary>

### Before (v2.0)
```python
# Sentiment analyzer doesn't work for cyber threats!
# Had to create parallel implementation for cybersecurity vertical
```

### After (v2.1)
```python
from core.cognitive.babel_gardens.domain import load_config_from_yaml
from core.cognitive.babel_gardens.consumers import SignalExtractor

config = load_config_from_yaml("config/signals_cybersecurity.yaml")
extractor = SignalExtractor(config=config)

result = extractor.extract("Zero-day exploit targeting critical infrastructure")

print(result["threat_severity"])      # 0.95 (critical)
print(result["exploit_imminence"])    # 0.88 (imminent)
print(result["confidence"])           # 0.94
```

**Benefit**: **Same core code** as finance vertical, just different YAML config!

</details>

<details>
<summary><b>Example 3: Cross-Vertical Fusion</b></summary>

### Use Case: Geopolitical Event
"Suez Canal closure disrupts global supply chains, oil prices surge"

This impacts:
- **Finance**: Market sentiment, fear index
- **Maritime**: Route viability, delay severity

### After (v2.1)
```python
from core.cognitive.babel_gardens.domain import merge_configs, MultiSignalFusionConfig

# Merge finance + maritime configs
finance_config = load_config_from_yaml("config/signals_finance.yaml")
maritime_config = load_config_from_yaml("config/signals_maritime.yaml")

combined = merge_configs([finance_config, maritime_config])
extractor = SignalExtractor(config=combined)

result = extractor.extract("Suez Canal closure disrupts global supply chains, oil prices surge")

print(result["market_fear_index"])        # 0.9 (high market stress)
print(result["delay_severity"])           # 7.0 days (shipping delay)
print(result["operational_disruption"])   # 0.85 (major disruption)

# Fuse signals into composite score
fusion = MultiSignalFusionConfig(
    signals=[
        combined.get_signal("market_fear_index"),
        combined.get_signal("delay_severity")
    ],
    fusion_method="weighted_sum",
    output_name="geopolitical_impact_score"
)

impact = fusion.compute_fusion(result)
print(impact)  # 0.82 (high cross-vertical impact)
```

**Benefit**: Can now analyze **cross-domain effects** that span multiple verticals!

</details>

---

## Testing Your Migration

### 1. Run Domain-Agnostic Tests
```bash
cd vitruvyan_core/core/cognitive/babel_gardens
pytest tests/test_domain_agnostic.py -v

# Expected output:
# ✅ Domain-Agnostic Validation: PASSED
# - 3 verticals tested
# - 0 vertical-specific code paths in LIVELLO 1
# - Cross-vertical fusion: WORKING
```

### 2. Validate Your Vertical Config
```python
from core.cognitive.babel_gardens.domain import SignalConfig

config = load_config_from_yaml("config/signals_myvertical.yaml")
errors = config.validate()

if errors:
    print(f"❌ Config invalid: {errors}")
else:
    print("✅ Config valid")
```

### 3. Test With 3 Sample Texts
```python
test_texts = [
    "Text relevant to your vertical domain",
    "Another test case",
    "Edge case: very short text"
]

for text in test_texts:
    result = extractor.extract(text)
    for signal_name, value in result.items():
        print(f"{signal_name}: {value}")
```

---

## Backward Compatibility

### Option A: Dual-Mode Operation (Recommended for Phase 2-3)
```python
# api/routes.py
@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Supports both legacy and new API."""
    
    if request.use_legacy_sentiment:  # Feature flag
        # OLD: sentiment_analyzer
        result = legacy_sentiment_analyzer.analyze(request.text)
        return {"sentiment": result.label, "score": result.score}
    
    else:
        # NEW: signal_extractor
        result = signal_extractor.extract(request.text)
        return {"signals": result}
```

### Option B: Legacy Wrapper (For External Consumers)
```python
# plugins/legacy_sentiment_wrapper.py
class LegacySentimentAdapter:
    """Wraps new signal API to provide old sentiment interface."""
    
    def __init__(self, signal_extractor: SignalExtractor):
        self.extractor = signal_extractor
    
    def analyze(self, text: str) -> "LegacySentimentResult":
        """Emulate old SentimentAnalyzer.analyze() interface."""
        signals = self.extractor.extract(text)
        
        # Map sentiment_valence signal to legacy label
        valence = signals.get("sentiment_valence", 0.0)
        if valence > 0.3:
            label = "positive"
        elif valence < -0.3:
            label = "negative"
        else:
            label = "neutral"
        
        return LegacySentimentResult(
            label=label,
            score=abs(valence),
            confidence=signals.get("confidence", 0.0)
        )
```

---

## FAQ

### Q: Do I need to rewrite all my code?
**A**: No! Use backward compatibility wrappers during Phase 2-3. Migrate incrementally.

### Q: Can I still use FinBERT?
**A**: Yes! FinBERT now powers the `sentiment_valence` signal via `ModelToSignalAdapter`.

### Q: What if my vertical needs custom signals?
**A**: Create a YAML config defining your signals. No code changes needed in Babel Gardens core.

### Q: How do I integrate with Orthodoxy Wardens?
**A**: Every `SignalExtractionResult` includes `extraction_trace` for explainability. Orthodoxy validates this automatically.

### Q: Can I mix signals from different verticals?
**A**: Yes! Use `MultiSignalFusionConfig` for cross-vertical signal synthesis.

---

## Support

- **Charter**: [philosophy/charter.md](philosophy/charter.md)
- **Examples**: [examples/](examples/)
- **Tests**: [tests/test_domain_agnostic.py](tests/test_domain_agnostic.py)
- **Issues**: File in GitHub with `babel-gardens-v2.1` label

---

## Version History

- **v2.0** (Feb 2026) — SACRED_ORDER_PATTERN refactoring
- **v2.1** (Feb 2026) — **SignalSchema**, domain-agnostic signals, removed sentiment hardcoding

**Migration Timeline**: Feb 11 - Mar 15, 2026 (5 weeks)
