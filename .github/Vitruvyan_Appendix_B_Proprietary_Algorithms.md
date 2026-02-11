# Appendix B — Proprietary Algorithms & Cognitive Signatures
*Vitruvyan Cognitive Core — The Signature Algorithms*

**Last Updated**: February 11, 2026  
**Status**: Finance Domain Algorithms (Not Core Primitives)

> **Note (Feb 2026)**: VEE and VARE described below are **finance domain-specific algorithms**. The core Neural Engine is now domain-agnostic via `IDataProvider` + `IScoringStrategy` contracts. These algorithms remain valid for finance verticals but are not part of the core engine primitives.

---

## Overview
The proprietary algorithms of Vitruvyan form the **cognitive signature** of the system.  
They define how perception, reasoning, and self-awareness interact inside the epistemic architecture.  
Each module corresponds to a distinct cognitive faculty — explainability, retrospection, empathy, prudence, and memory.

---

## Algorithm Index
| Code | Name | Status | Role |
|------|------|--------|------|
| **VEE** | Vitruvyan Explainability Engine | ✅ Active | Multilevel explainability and narrative generation |
| **VWRE** | Vitruvyan Weighted Reverse Engineering | ✅ Active | Attribution analysis - reverse engineer composite_z into factor contributions |
| **VGOP** | Vitruvyan Goal Optimization Protocol | 📋 Designed | Goal-driven ticker filtering with probabilistic modeling |
| **VARE** | Vitruvyan Adaptive Risk Engine | ✅ Active | Dynamic risk modulation and profile matching |
| **VHSW** | Vitruvyan Human Sentiment Weighting | 🚧 Partial | Integration of collective sentiment and human priors |
| **VMFL** | Vitruvyan Memory Feedback Loop | 🚧 Partial | Performance-based feedback and learning loop |

---

## 1. Vitruvyan Explainability Engine (VEE)
**Status:** Active  
**Purpose:** Transform raw numeric outputs into human-understandable explanations.

### Architecture
```
Neural Engine → Explainability Layer → LangGraph Narrative → UI Panels
```
- Uses rule-based templates + LLM interpretive layer.
- Three levels of explanation: *Simple*, *Technical*, *Detailed*.
- Integrated with `compose_node` and `vee_explainer.py`.
- Outputs JSON with narrative + causal reasoning trace.

### Cognitive Function
Transparency and storytelling — allows users to trust the model by understanding it.

---

## 2. Vitruvyan Weighted Reverse Engineering (VWRE)
**Status:** ✅ Active (Dec 23, 2025)  
**Purpose:** Attribution Analysis — reverse engineer composite_z scores into weighted factor contributions.

### Core Logic
```python
composite_z = Σ (weight_i × factor_z_i)
→ VWRE: contribution_i = weight_i × factor_z_i
→ percentage_i = (contribution_i / sum_contributions) × 100
→ verification: |sum_contributions - composite_z| < 0.1
```

### Architecture
- **VWREEngine**: Core attribution analysis class
- **VWREResult**: Dataclass with factor_contributions, factor_percentages, primary_driver, verification_status
- **Methods**: analyze_attribution(), compare_tickers(), batch_analyze()

### Output Example
```python
VWREResult(
    ticker="AAPL",
    composite_score=1.85,
    primary_driver="momentum",
    factor_contributions={"momentum": 0.735, "fundamentals": 0.288, "trend": 0.225},
    factor_percentages={"momentum": 39.7, "fundamentals": 15.6, "trend": 12.2},
    verification_status="verified"
)
```

### Integration Points
- Neural Engine pack_rows(): Calls VWRE for each ticker
- VEE generator: Uses attribution data for precise narratives
- Orthodoxy Wardens: verification_status for audit compliance

### Benefits
- Explainability: Answers "Why AAPL rank 1 instead of TSLA rank 5?"
- Audit trail: Every rank is mathematically verifiable
- Zero cost: Pure Python math, <1ms per ticker
- VEE enhancement: "Rank driven by momentum (39.7% weight, +0.735 contribution)"

### Cognitive Function
Retrospection and introspection — the system explains its own reasoning chain with mathematical precision.

---

## 3. Vitruvyan Goal Optimization Protocol (VGOP)
**Status:** 📋 Designed (Q2 2026)  
**Purpose:** Goal-driven ticker filtering with probabilistic modeling.

### Original Vision
> "Un motore che parte dai tuoi obiettivi (es. +5% entro 1 settimana con max -2% risk) e calcola la probabilità inversa su ogni ticker, proponendo solo titoli compatibili con il tuo target."

### Key Differentiator
- **Neural Engine**: "Qual è il miglior titolo?" (generic ranking)
- **VGOP**: "Qual è il miglior titolo PER IL MIO OBIETTIVO?" (personalized ranking)

### Architecture
```python
@dataclass
class UserGoal:
    target_return: float         # e.g., 0.05 = +5%
    timeframe_days: int          # e.g., 7 = 1 week
    max_drawdown: float          # e.g., 0.02 = -2%
    confidence_level: float      # e.g., 0.80 = 80% confidence

class VGOPEngine:
    def filter_by_goal(self, tickers, user_goal, neural_results):
        # 1. Fetch historical data (yfinance, 252 days)
        # 2. Monte Carlo simulation (10K runs per ticker)
        # 3. Calculate goal probability P(achieving goal)
        # 4. Re-rank by goal compatibility
        return sorted_by_probability
```

### Example Scenario
- User Goal: +5% in 7 days, max -2% drawdown
- Neural Engine: AAPL rank 1 (stable, low vol), NVDA rank 2 (high vol)
- VGOP Re-Rank: NVDA rank 1 (85% prob), AAPL filtered (35% prob, too slow)
- **Key Insight**: High volatility = ASSET for short-term goals (not liability!)

### Implementation Timeline
6 weeks (Q2 2026): Core engine → Goal extraction → LangGraph integration → Validation

### Cognitive Function
Goal-oriented reasoning — the system adapts recommendations to user objectives, not just absolute quality.

**See**: `docs/VGOP_DESIGN_SPEC_Q2_2026.md` for complete specification.

---

## 4. Vitruvyan Human Sentiment Weighting (VHSW)
**Status:** 🚧 Partial  
**Purpose:** Modulate quantitative signals with real-world human sentiment.

### Data Sources
- Reddit & X (Twitter) embeddings from Babel Gardens.
- FinBERT emotional polarity and credibility filters.
- Correlated to sectors and macro events.

### Integration
```
Sentiment Engine → VHSW weighting → Neural Engine z-normalization
```
### Cognitive Function
Empathy — aligns system reasoning with collective market psychology.

---

## 5. Vitruvyan Adaptive Risk Engine (VARE)
**Status:** ✅ Active  
**Purpose:** Adjust model aggressiveness and weighting based on volatility, drawdown, and regime detection.

### Implementation Plan
- Uses rolling volatility (σ), drawdown %, and sector beta.
- Adjusts weight of momentum vs. fundamental metrics dynamically.
- Integrated with Sentinel (Portfolio Guardian).

### Cognitive Function
Prudence — manages exposure adaptively, similar to a self-aware portfolio manager.

---

## 6. Vitruvyan Memory Feedback Loop (VMFL)
**Status:** 🚧 Partial  
**Purpose:** Learn from performance over time — feedback integration.

### Core Flow
```
Execution → Logging → Performance Δ → Weight Adjustment → Reinforcement
```
- Uses PostgreSQL logs + Redis streams for performance signals.
- Supports periodic retraining of z-score weights.
- Long-term goal: full self-optimization of Neural Engine profiles.

### Cognitive Function
Memory — enables the system to refine itself over time, creating experiential knowledge.

---

## Summary of Interactions
```
Codex Hunters → Neural Engine → VWRE (attribution) → VEE (explainability)
                              ↓
                           VGOP (goal filtering) → VARE (risk adaptation)
                              ↓
                           VMFL (feedback) → Vault Keepers
```
- **Input:** factual and sentiment data.
- **Process:** rank → attribute → explain → filter by goal → adapt risk → remember.
- **Output:** transparent, goal-aligned, and adaptive trading intelligence.

---

## Roadmap & Priorities (2025–2026)
| Quarter | Module | Priority | Status | Key Goal |
|----------|---------|-----------|---------|----------|
| Q4 2025 | VARE | 🔺 High | ✅ Complete | Integrate adaptive risk scoring |
| Q4 2025 | VWRE | 🔺 High | ✅ Complete | Enable explainable backtracking |
| Q1 2026 | VEE v3 | 🔺 High | 🔄 In Progress | Enhanced fundamentals integration |
| Q2 2026 | VGOP | 🔺 High | 📋 Designed | Goal-driven optimization |
| Q3 2026 | VMFL | 🔺 Medium | 🚧 Partial | Activate self-learning feedback |
| Q4 2026 | VHSW | 🔹 Low | 🚧 Partial | Introduce collective sentiment weighting |

---

**Author:** Vitruvyan Core Team  
**Version:** 2.0.0  
**Last Updated:** 2025-12-23  
**Key Achievements (Dec 2025):**  
- ✅ VWRE-A Attribution Analysis deployed (600+ lines, Neural Engine + VEE integration)  
- ✅ VARE Risk Engine operational (850 lines, multi-dimensional risk analysis)  
- 📋 VGOP comprehensive design spec complete (Q2 2026 implementation planned)