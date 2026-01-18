# Mercator Vertical Demo

Complete demonstration of Mercator Vertical's financial analysis capabilities.

## Overview

This demo showcases Vitruvyan Core's first complete vertical implementation - **Mercator**, a comprehensive financial analysis engine that orchestrates the full cognitive pipeline:

```
Neural Engine → VWRE → VARE → VEE
     ↓           ↓      ↓      ↓
  6 Factors → Attribution → Risk → Narrative
```

## Features Demonstrated

### 🧠 Quantitative Evaluation (Neural Engine)
- **6 Financial Factors**: Price momentum, earnings quality, valuation, growth, volatility, liquidity
- **Multi-strategy Support**: Balanced, growth, value, defensive investment strategies
- **Z-score Normalization**: Cross-sectional comparability

### 📊 Attribution Analysis (VWRE)
- **Factor Contribution Breakdown**: Which factors drive the investment thesis
- **Percentage Attribution**: Relative importance of each factor
- **Strategy-aware Weighting**: Different factor weights by investment style

### ⚠️ Risk Assessment (VARE)
- **5 Risk Dimensions**: Market, volatility, liquidity, credit, concentration
- **Risk Categories**: Very Low → Very High classification
- **Multi-dimensional Analysis**: Holistic risk profile assessment

### 💬 Investment Narrative (VEE)
- **Investment Thesis**: Clear buy/hold/sell recommendations
- **Risk Narrative**: Qualitative risk assessment
- **Valuation Commentary**: Relative attractiveness analysis
- **Catalyst Assessment**: Timing and momentum analysis

## Demo Scenarios

### 1. Single Entity Analysis
```python
from vitruvyan_core.verticals.mercator import MercatorVertical

mercator = MercatorVertical()
analysis = mercator.analyze_entity("EXAMPLE_ENTITY_1", financial_data, strategy="growth")
```

- Analyzes individual entities with different investment strategies
- Shows how strategy affects factor weighting and recommendations
- Demonstrates complete pipeline execution

### 2. Collection Analysis
```python
portfolio_analysis = mercator.analyze_portfolio(holdings, strategy="balanced")
```

- Multi-asset collection evaluation
- Risk contribution analysis by holding
- Diversification scoring
- Collection-level recommendations

### 3. Deep Factor Analysis
- Detailed factor contribution breakdown
- Risk dimension deep-dive
- Investment narrative generation
- Technical analysis explanations

## Sample Data

The demo uses realistic synthetic data for major technology companies:
- **AAPL** (Apple): Balanced growth with strong fundamentals
- **MSFT** (Microsoft): High growth with moderate volatility
- **GOOGL** (Alphabet): Growth-oriented with higher risk
- **BRK.B** (Berkshire Hathaway): Defensive value with low volatility

## Running the Demo

```bash
cd examples/mercator_demo
python mercator_demo.py
```

## Expected Output

The demo will show:
- Strategy-specific analysis results
- Factor contribution comparisons
- Risk assessment breakdowns
- Investment recommendations with confidence scores
- Collection-level aggregation and diversification analysis

## Key Insights

1. **Strategy Matters**: Different investment strategies (growth vs value) produce different recommendations for the same company

2. **Risk-Adjusted Returns**: Recommendations balance quantitative scores with comprehensive risk assessment

3. **Factor Interactions**: How different factors contribute to the overall investment thesis

4. **Collection Effects**: How individual analyses aggregate to collection-level insights

## Architecture Validation

This demo validates that Phase 4 vertical development successfully:
- ✅ Incarnates core contracts with domain-specific implementations
- ✅ Maintains clean separation between core and vertical logic
- ✅ Provides production-ready financial analysis capabilities
- ✅ Demonstrates scalable vertical development pattern

## Next Steps

After running this demo, you can:
- Implement additional financial factors
- Add more investment strategies
- Integrate real market data feeds
- Extend to other asset classes (bonds, commodities, crypto)
- Build trading strategy automation

---

**Built with Vitruvyan Core's provider incarnation pattern** 🚀