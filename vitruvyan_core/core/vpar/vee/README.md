# VEE — Vitruvyan Explainability Engine v3.0

**Domain-agnostic multi-level explainability kernel.**

VEE transforms raw metrics into stratified, auditable natural language explanations.
It contains **zero domain knowledge** — all semantics are injected at runtime via the
`ExplainabilityProvider` contract.

---

## What is VEE?

VEE is one of the proprietary algorithms in VPAR (Vitruvyan Proprietary Algorithms Repository).
It answers the question: **"Why did the system produce this result?"**

Given a set of metrics for any entity (a patient, a device, a financial instrument, a legal case),
VEE produces explanations at three levels of detail:

| Level | Audience | Example |
|-------|----------|---------|
| **Summary** | General users | "Patient #123 shows strong cardiac indicators." |
| **Technical** | Analysts | "Dominant factor: cardiac function (0.92). Intensity: 0.79." |
| **Detailed** | Experts | Full breakdown with patterns, anomalies, confidence notes. |

---

## Architecture

VEE is a 5-phase pipeline. Each phase is a separate module:

```
Metrics + Provider
       │
       ▼
┌──────────────┐
│  VEEAnalyzer │  Phase 1-2: Normalize → Identify signals → Detect patterns
│  (352 lines) │  Output: AnalysisResult
└──────┬───────┘
       │
       ▼
┌───────────────┐
│ VEEGenerator  │  Phase 3: Render templates → Adapt to user level
│  (191 lines)  │  Output: ExplanationLevels
└──────┬────────┘
       │
       ▼
┌──────────────────┐
│ VEEMemoryAdapter │  Phase 4-5: Enrich with history → Store for future
│   (223 lines)    │  Output: Enriched ExplanationLevels
└──────────────────┘
       │
       ▼
  Dict[str, str]   ← System-compatible output
```

### File Map

| File | Lines | Responsibility |
|------|------:|----------------|
| `types.py` | 87 | `AnalysisResult`, `ExplanationLevels`, `HistoricalExplanation` — pure dataclasses |
| `vee_analyzer.py` | 352 | Normalization, signal identification, pattern detection, anomaly detection |
| `vee_generator.py` | 191 | Template rendering, level adaptation, VSGS semantic synthesis |
| `vee_engine.py` | 203 | Pipeline orchestrator — wires Analyzer → Generator → Memory |
| `vee_memory_adapter.py` | 223 | PostgreSQL persistence via `PostgresAgent` (lazy connection) |
| `_archived_v2/` | 2,205 | Previous version (finance-coupled, preserved for reference) |

### Key Design Decisions

- **Co-dominance**: `dominant_factors` is `List[Tuple[str, float]]`, not a single scalar. Multiple factors can be equally dominant.
- **Multi-dimensional confidence**: `confidence` is `Dict[str, float]` with `data_completeness`, `signal_clarity`, `consistency`, `overall`.
- **Direction is Optional**: The `direction` field is `Optional[str]` — domains define what "direction" means (or omit it entirely).
- **No Qdrant pseudo-embeddings**: Semantic search belongs in VSGS, not in VEE memory.
- **Schema-neutral persistence**: `entity_id VARCHAR(255)`, `domain_tag` column enables multi-domain coexistence in one table.

---

## The Contract: `ExplainabilityProvider`

**Location**: `vitruvyan_core/domains/explainability_contract.py`

This is the **sole injection point** for domain knowledge. VEE never contains domain concepts —
it delegates everything to the provider:

| Method | What it provides | Used by |
|--------|------------------|---------|
| `get_normalization_rules()` | How to normalize metrics to 0-1 | Analyzer |
| `get_analysis_dimensions()` | What categories of metrics exist | Analyzer |
| `get_pattern_rules()` | Domain-specific pattern detection | Analyzer |
| `get_intensity_weights()` | Relative weight per dimension | Analyzer |
| `get_confidence_criteria()` | Thresholds for confidence calculation | Analyzer |
| `get_explanation_templates()` | Narrative templates with `{placeholders}` | Generator |
| `format_entity_reference()` | How to name entities in text | Generator |
| `get_metric_definitions()` | Optional metric metadata | (informational) |

---

## How to Implement a New Domain

### Step 1: Create a provider

```python
# vitruvyan_core/domains/my_domain/explainability_provider.py

from domains.explainability_contract import (
    ExplainabilityProvider, ExplanationTemplate, NormalizationRule,
    AnalysisDimension, PatternRule, ConfidenceCriteria
)


class MyDomainProvider(ExplainabilityProvider):

    def get_explanation_templates(self):
        return ExplanationTemplate(
            summary_template="{entity_reference}: {signals_text} ({direction}).",
            technical_template=(
                "Analysis of {entity_reference}: "
                "dominant factor is {dominant_factor}, "
                "intensity {intensity:.2f}."
            ),
            detailed_template=(
                "Full evaluation for {entity_reference}: {signals_text}. "
                "{patterns_text}{confidence_text}"
            ),
        )

    def format_entity_reference(self, entity_id: str) -> str:
        return f"Case #{entity_id}"

    def get_normalization_rules(self):
        return [
            NormalizationRule("_z", "zscore_tanh"),
            NormalizationRule("_score", "linear_100"),
            NormalizationRule("_risk", "linear_custom", invert=True,
                              min_value=0, max_value=10),
        ]

    def get_analysis_dimensions(self):
        return [
            AnalysisDimension("quality", ["quality_score", "accuracy_z"],
                              "quality metrics", direction="higher_better"),
            AnalysisDimension("risk", ["risk_score"],
                              "risk assessment", direction="lower_better"),
        ]

    def get_pattern_rules(self):
        return [
            PatternRule(
                "high_risk_low_quality",
                "High risk with degraded quality detected",
                condition=lambda m: (
                    m.get("risk_score", 0) > 0.7
                    and m.get("quality_score", 1) < 0.4
                ),
            ),
        ]

    def get_intensity_weights(self):
        return {"quality": 1.5, "risk": 1.0}

    def get_confidence_criteria(self):
        return ConfidenceCriteria(
            min_metrics_high=5,
            min_metrics_moderate=3,
            min_signals_high=2,
        )
```

### Step 2: Use VEE with your provider

```python
from core.vpar.vee import VEEEngine
from domains.my_domain.explainability_provider import MyDomainProvider

engine = VEEEngine(domain_tag="my_domain")
provider = MyDomainProvider()

metrics = {
    "quality_score": 85,
    "accuracy_z": 1.2,
    "risk_score": 3,
}

# Simple output (Dict[str, str])
result = engine.explain("ENTITY_42", metrics, provider)
print(result["summary"])

# Full output with analysis metadata
full = engine.explain_comprehensive("ENTITY_42", metrics, provider,
                                     profile={"level": "expert"})
print(full["analysis"]["confidence"])
```

### Step 3: That's it

No VEE files modified. No core changes. Your provider is the only new code.

---

## Template Placeholders

Templates use Python `str.format()` syntax. Available placeholders:

| Placeholder | Type | Description |
|-------------|------|-------------|
| `{entity_id}` | `str` | Raw entity identifier |
| `{entity_reference}` | `str` | Result of `format_entity_reference()` |
| `{signals_text}` | `str` | Top 3 signals, comma-separated |
| `{dominant_factor}` | `str` | Name of the primary factor |
| `{secondary_factors}` | `str` | Names of secondary factors |
| `{intensity}` | `float` | Overall intensity (0.0–1.0) |
| `{direction}` | `str` | Overall direction or "neutral" |
| `{signals_summary}` | `str` | Brief signals summary |
| `{patterns_text}` | `str` | Detected patterns (empty if none) |
| `{confidence_text}` | `str` | Confidence note sentence |

---

## Normalization Methods

| Method | Formula | Use case |
|--------|---------|----------|
| `zscore_tanh` | `(tanh(v/2) + 1) / 2` | Z-scores (unbounded, centered at 0) |
| `linear_100` | `min(1, abs(v)/100)` | Percentage-like scores (0–100) |
| `linear_custom` | `(v - min) / (max - min)` | Custom-range metrics |
| `sigmoid` | `1 / (1 + e^(-v/10))` | Soft normalization |

Set `invert=True` on the rule to flip: high raw value → low normalized (e.g., risk metrics).

---

## Invariants

1. **VEE core NEVER imports domain code.** Direction is always: `domain → contract → VEE`.
2. **Provider is REQUIRED.** `VEEEngine.explain()` has no default provider and will not guess.
3. **No finance, medical, or any domain terms** exist in VEE source code.
4. **Memory adapter uses `PostgresAgent`** only — no raw `psycopg2` clients.
5. **All archived code** lives in `_archived_v2/` and must not be imported.
