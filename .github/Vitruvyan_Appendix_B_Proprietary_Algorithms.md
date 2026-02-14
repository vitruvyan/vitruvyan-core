# Appendix B — Explainability Patterns & Finance Vertical Algorithms
*Core Epistemic Patterns + Domain-Specific Implementations*

**Last Updated**: February 14, 2026  
**Scope**: Core explainability patterns (VEE, VWRE) + Finance vertical algorithms (VGOP, VARE, VHSW, VMFL)

> **Architecture Note (Feb 2026)**: This document covers TWO distinct categories:
> 
> **1. CORE PATTERNS** (domain-agnostic, vitruvyan-core primitives):  
> - **VEE** (Explainability Engine): Universal narrative generation framework (ANY domain)  
> - **VWRE** (Weighted Reverse Engineering): Generic attribution analysis (ANY composite scoring)
> 
> **2. FINANCE VERTICAL IMPLEMENTATIONS** (examples/verticals/finance/):  
> - **VGOP** (Goal Optimization Protocol): Ticker filtering by user goals (finance-specific)  
> - **VARE** (Adaptive Risk Engine): Portfolio risk modulation (finance-specific)  
> - **VHSW** (Human Sentiment Weighting): Market psychology integration (finance-specific)  
> - **VMFL** (Memory Feedback Loop): Performance-based learning (finance-specific)
> 
> The core Neural Engine is now domain-agnostic via `IDataProvider` + `IScoringStrategy` contracts.  
> Finance implementations remain valid as vertical reference patterns.

---

## Overview

This document covers **epistemic patterns** that enable explainability, attribution, and adaptive intelligence:

- **Core Patterns** (VEE, VWRE): Universal frameworks applicable to ANY domain (healthcare, e-commerce, research, finance)
- **Finance Vertical** (VGOP, VARE, VHSW, VMFL): Domain-specific implementations for trading/portfolio management

Each module corresponds to a distinct cognitive faculty — explainability, attribution, goal-optimization, prudence, empathy, and memory.

---

## Pattern & Algorithm Index

| Code | Name | Category | Status | Role |
|------|------|----------|--------|------|
| **VEE** | Vitruvyan Explainability Engine | 🌐 Core Pattern | ✅ Active | Multilevel explainability and narrative generation (universal) |
| **VWRE** | Vitruvyan Weighted Reverse Engineering | 🌐 Core Pattern | ✅ Active | Attribution analysis - reverse engineer composite scores (universal) |
| **VGOP** | Vitruvyan Goal Optimization Protocol | 💰 Finance Vertical | 📋 Designed | Goal-driven ticker filtering with probabilistic modeling |
| **VARE** | Vitruvyan Adaptive Risk Engine | 💰 Finance Vertical | ✅ Active | Dynamic portfolio risk modulation |
| **VHSW** | Vitruvyan Human Sentiment Weighting | 💰 Finance Vertical | 🚧 Partial | Integration of market sentiment and human priors |
| **VMFL** | Vitruvyan Memory Feedback Loop | 💰 Finance Vertical | 🚧 Partial | Performance-based feedback and learning loop |

---

## CORE PATTERNS (Domain-Agnostic)

### 1. Vitruvyan Explainability Engine (VEE)
**Category:** 🌐 Core Pattern (Universal)  
**Status:** ✅ Active  
**Purpose:** Transform raw numeric outputs into human-understandable explanations (ANY domain).

### Architecture (Domain-Agnostic)
```
Neural Engine (any domain) → Explainability Layer → LangGraph Narrative → UI/API Output
```
- Uses rule-based templates + LLM interpretive layer
- Three levels of explanation: *Summary*, *Detailed*, *Technical*
- Integrated with `compose_node` and VEE generator
- Outputs JSON with narrative + causal reasoning trace
- **Universal**: Works with healthcare diagnoses, e-commerce recommendations, research rankings, financial portfolios

### Cognitive Function
Transparency and storytelling — allows users to trust the model by understanding it (domain-independent).

---

### 2. Vitruvyan Weighted Reverse Engineering (VWRE)
**Category:** 🌐 Core Pattern (Universal)  
**Status:** ✅ Active (Dec 23, 2025)  
**Purpose:** Attribution Analysis — reverse engineer ANY composite score into weighted factor contributions.

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
Retrospection and introspection — the system explains its own reasoning chain with mathematical precision (domain-independent).

---

## FINANCE VERTICAL IMPLEMENTATIONS

> **Note**: The following algorithms are **finance domain-specific** implementations. They demonstrate patterns that can be adapted for other verticals (healthcare risk scoring, e-commerce conversion optimization, etc.).

### 3. Vitruvyan Goal Optimization Protocol (VGOP)
**Category:** 💰 Finance Vertical  
**Status:** 📋 Designed (Q2 2026)  
**Purpose:** Goal-driven ticker filtering with probabilistic modeling (finance-specific).

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

### 4. Vitruvyan Human Sentiment Weighting (VHSW)
**Category:** 💰 Finance Vertical  
**Status:** 🚧 Partial  
**Purpose:** Modulate quantitative signals with real-world market sentiment (finance-specific).

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

### 5. Vitruvyan Adaptive Risk Engine (VARE)
**Category:** 💰 Finance Vertical  
**Status:** ✅ Active  
**Purpose:** Adjust portfolio aggressiveness based on volatility, drawdown, and regime detection (finance-specific).

### Implementation Plan
- Uses rolling volatility (σ), drawdown %, and sector beta.
- Adjusts weight of momentum vs. fundamental metrics dynamically.
- Integrated with Sentinel (Portfolio Guardian).

### Cognitive Function
Prudence — manages exposure adaptively, similar to a self-aware portfolio manager.

---

### 6. Vitruvyan Memory Feedback Loop (VMFL)
**Category:** 💰 Finance Vertical  
**Status:** 🚧 Partial  
**Purpose:** Learn from trading performance over time — feedback integration (finance-specific).

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

## Summary of Interactions (Finance Vertical Example)

```
Codex Hunters → Neural Engine → VWRE (attribution) → VEE (explainability)
                              ↓
                           VGOP (goal filtering) → VARE (risk adaptation)
                              ↓
                           VMFL (feedback) → Vault Keepers
```

**Finance Vertical Flow**:
- **Input:** Market data + sentiment (Babel Gardens)
- **Process:** Rank → Attribute (VWRE core) → Explain (VEE core) → Filter by goal (VGOP finance) → Adapt risk (VARE finance) → Remember (VMFL finance)
- **Output:** Transparent, goal-aligned, risk-aware trading intelligence

**Universal Pattern**:
- Replace "tickers" with "entities" (patients, products, papers)
- Replace "goal" with domain objective (diagnosis confidence, conversion probability, citation impact)
- Core patterns (VEE, VWRE) remain unchanged

---

## Roadmap & Priorities (2025–2026)

### Core Patterns (Domain-Agnostic)
| Quarter | Module | Priority | Status | Key Goal |
|----------|---------|-----------|---------|----------|
| Q4 2025 | VWRE | 🔺 High | ✅ Complete | Enable explainable attribution (universal formula) |
| Q1 2026 | VEE v3 | 🔺 High | ✅ Complete | Domain-agnostic narrative templates |
| Q2 2026 | VEE Multilingual | 🔺 High | 🔄 In Progress | 84-language support via Babel Gardens |

### Finance Vertical Implementations
| Quarter | Module | Priority | Status | Key Goal |
|----------|---------|-----------|---------|----------|
| Q4 2025 | VARE | 🔺 High | ✅ Complete | Integrate adaptive portfolio risk scoring |
| Q2 2026 | VGOP | 🔺 High | 📋 Designed | Goal-driven ticker optimization |
| Q3 2026 | VMFL | 🔹 Medium | 🚧 Partial | Activate self-learning feedback loop |
| Q4 2026 | VHSW | 🔹 Low | 🚧 Partial | Introduce market sentiment weighting |

---

**Author:** Vitruvyan Core Team  
**Version:** 3.0.0 (Core Patterns + Finance Vertical Separation)  
**Last Updated:** February 14, 2026  

**Key Achievements (Feb 2026)**:  
- ✅ **VEE v3**: Domain-agnostic narrative generation (healthcare, e-commerce, research, finance)  
- ✅ **VWRE**: Universal attribution analysis (600+ lines, mathematically verifiable)  
- ✅ **VARE**: Finance vertical risk engine operational (850 lines, multi-dimensional portfolio risk)  
- 📋 **VGOP**: Comprehensive design spec complete (Q2 2026 finance vertical implementation)