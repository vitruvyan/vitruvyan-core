"""
Mercator Vertical Demo: Complete Financial Analysis

This demo showcases Mercator Vertical's complete financial analysis capabilities:
- Single entity analysis with different investment strategies
- Collection-level analysis and risk assessment
- Multi-factor quantitative evaluation
- Investment recommendation generation

The demo uses synthetic but realistic financial data to demonstrate:
1. Neural Engine quantitative evaluation (6 factors)
2. VWRE attribution analysis (factor contribution breakdown)
3. VARE risk assessment (5 risk dimensions)
4. VEE investment narrative generation
5. Strategy-specific recommendations

Author: Vitruvyan Development Team
Created: December 30, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

# Mercator Vertical
from vitruvyan_core.verticals.mercator import MercatorVertical


def create_sample_financial_data() -> List[Dict[str, Any]]:
    """
    Create realistic sample financial data for demonstration

    Returns sample data for major tech companies with realistic metrics
    """
    return [
        {
            "entity_id": "EXAMPLE_ENTITY_1",
            "company_name": "Apple Inc.",
            "current_price": 195.50,
            "price_1m": 185.20,
            "price_3m": 175.80,
            "price_12m": 165.30,
            "net_income": 97000,  # millions
            "cash_from_operations": 118000,
            "total_assets": 352000,
            "earnings_volatility": 0.15,
            "revenue_growth_1y": 0.08,
            "revenue_growth_3y": 0.12,
            "eps_growth_1y": 0.10,
            "eps_growth_3y": 0.15,
            "analyst_growth_est": 0.12,
            "market_cap": 3100000,  # billions
            "book_value": 58000,
            "enterprise_value": 3150000,
            "ebitda": 130000,
            "dividend_yield": 0.0045,
            "historical_volatility": 0.25,
            "beta": 1.2,
            "max_drawdown": 0.18,
            "var_95": 0.12,
            "avg_daily_volume": 55000000,
            "bid_ask_spread": 0.0008,
            "shares_outstanding": 15800  # millions
        },
        {
            "entity_id": "EXAMPLE_ENTITY_4",
            "company_name": "Microsoft Corporation",
            "current_price": 420.30,
            "price_1m": 395.50,
            "price_3m": 375.20,
            "price_12m": 335.60,
            "net_income": 88000,
            "cash_from_operations": 121000,
            "total_assets": 470000,
            "earnings_volatility": 0.12,
            "revenue_growth_1y": 0.15,
            "revenue_growth_3y": 0.18,
            "eps_growth_1y": 0.18,
            "eps_growth_3y": 0.22,
            "analyst_growth_est": 0.20,
            "market_cap": 3100000,
            "book_value": 87000,
            "enterprise_value": 3180000,
            "ebitda": 125000,
            "dividend_yield": 0.0068,
            "historical_volatility": 0.28,
            "beta": 1.1,
            "max_drawdown": 0.22,
            "var_95": 0.15,
            "avg_daily_volume": 22000000,
            "bid_ask_spread": 0.0006,
            "shares_outstanding": 7400
        },
        {
            "entity_id": "EXAMPLE_ENTITY_5",
            "company_name": "Alphabet Inc.",
            "current_price": 142.80,
            "price_1m": 138.50,
            "price_3m": 132.20,
            "price_12m": 125.40,
            "net_income": 84000,
            "cash_from_operations": 102000,
            "total_assets": 420000,
            "earnings_volatility": 0.20,
            "revenue_growth_1y": 0.12,
            "revenue_growth_3y": 0.16,
            "eps_growth_1y": 0.14,
            "eps_growth_3y": 0.19,
            "analyst_growth_est": 0.17,
            "market_cap": 1800000,
            "book_value": 105000,
            "enterprise_value": 1780000,
            "ebitda": 105000,
            "dividend_yield": 0.0042,
            "historical_volatility": 0.32,
            "beta": 1.3,
            "max_drawdown": 0.28,
            "var_95": 0.18,
            "avg_daily_volume": 25000000,
            "bid_ask_spread": 0.0012,
            "shares_outstanding": 12600
        },
        {
            "entity_id": "BRK.B",
            "company_name": "Berkshire Hathaway Inc.",
            "current_price": 450.20,
            "price_1m": 442.80,
            "price_3m": 435.60,
            "price_12m": 410.30,
            "net_income": 96000,
            "cash_from_operations": 145000,
            "total_assets": 1080000,
            "earnings_volatility": 0.08,
            "revenue_growth_1y": 0.06,
            "revenue_growth_3y": 0.08,
            "eps_growth_1y": 0.05,
            "eps_growth_3y": 0.07,
            "analyst_growth_est": 0.06,
            "market_cap": 980000,
            "book_value": 580000,
            "enterprise_value": 1020000,
            "ebitda": 145000,
            "dividend_yield": 0.0000,  # No dividend
            "historical_volatility": 0.18,
            "beta": 0.9,
            "max_drawdown": 0.15,
            "var_95": 0.08,
            "avg_daily_volume": 3500000,
            "bid_ask_spread": 0.0025,
            "shares_outstanding": 2180
        }
    ]


def demonstrate_single_entity_analysis():
    """Demonstrate single entity analysis with different strategies"""
    print("=" * 80)
    print("🏛️ MERCATOR VERTICAL DEMO: Single Entity Analysis")
    print("=" * 80)

    # Initialize Mercator
    mercator = MercatorVertical()

    # Sample data
    sample_data = create_sample_financial_data()

    # Analyze AAPL with different strategies
    aapl_data = next(item for item in sample_data if item["entity_id"] == "EXAMPLE_ENTITY_1")

    strategies = ["balanced", "growth", "value", "defensive"]

    for strategy in strategies:
        print(f"\n🎯 Analyzing AAPL with {strategy.upper()} strategy")
        print("-" * 60)

        analysis = mercator.analyze_entity("EXAMPLE_ENTITY_1", aapl_data, strategy=strategy)

        print(f"📊 Composite Score: {analysis.neural_evaluation['composite_score']:.3f}")
        print(f"🎖️  Rank: {analysis.neural_evaluation['rank']}")
        print(f"⚠️  Risk Category: {analysis.risk_assessment['risk_category']}")
        print(f"💡 Recommendation: {analysis.recommendation} (Confidence: {analysis.confidence_score:.1%})")

        print(f"\n📈 Key Factor Contributions:")
        factors = analysis.neural_evaluation['factor_contributions']
        for factor, contribution in sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)[:3]:
            print(".3f")

        print(f"\n💰 Investment Thesis: {analysis.explanation['investment_thesis']}")
        print(f"⚖️  Risk Narrative: {analysis.explanation['risk_narrative']}")


def demonstrate_portfolio_analysis():
    """Demonstrate collection-level analysis"""
    print("\n" + "=" * 80)
    print("🏛️ MERCATOR VERTICAL DEMO: Collection Analysis")
    print("=" * 80)

    # Initialize Mercator
    mercator = MercatorVertical()

    # Create sample collection
    sample_data = create_sample_financial_data()
    portfolio_holdings = [
        {"entity_id": item["entity_id"], "data": item}
        for item in sample_data
    ]

    print(f"\n📊 Analyzing collection with {len(portfolio_holdings)} holdings")

    # Analyze collection with balanced strategy
    portfolio_analysis = mercator.analyze_portfolio(
        portfolio_holdings,
        portfolio_id="tech_diversified",
        strategy="balanced"
    )

    print("
📈 Collection Metrics:"    metrics = portfolio_analysis.portfolio_metrics
    print(".3f"    print(".3f"    print(".3f"    print(".3f"    print(".3f"    print(".3f"
    print(f"\n🎯 Diversification Score: {portfolio_analysis.diversification_score:.1%}")
    print(f"📋 Recommendation: {portfolio_analysis.recommendation}")

    print("
⚠️  Risk Contribution by Category:"    for category, percentage in portfolio_analysis.risk_contribution.items():
        print(".1%")

    print("
🏆 Individual Holding Recommendations:"    for holding in portfolio_analysis.holdings_analysis:
        print(f"  {holding.entity_id}: {holding.recommendation} "
              f"(Score: {holding.neural_evaluation['composite_score']:.2f}, "
              f"Risk: {holding.risk_assessment['risk_category']})")


def demonstrate_factor_analysis():
    """Demonstrate detailed factor analysis"""
    print("\n" + "=" * 80)
    print("🏛️ MERCATOR VERTICAL DEMO: Factor Analysis Deep Dive")
    print("=" * 80)

    mercator = MercatorVertical()
    sample_data = create_sample_financial_data()

    # Analyze MSFT with detailed factor breakdown
    msft_data = next(item for item in sample_data if item["entity_id"] == "EXAMPLE_ENTITY_4")

    print("
🔍 Deep Factor Analysis for MSFT"    analysis = mercator.analyze_entity("EXAMPLE_ENTITY_4", msft_data, strategy="growth")

    print("
📊 Neural Engine Factor Contributions:"    factors = analysis.neural_evaluation['factor_contributions']
    for factor_name, contribution in sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True):
        factor_display = factor_name.replace('_', ' ').title()
        direction = "🚀 Positive" if contribution > 0 else "📉 Negative"
        print("6.3f"
    print("
🎯 VWRE Attribution Analysis:"    attr = analysis.attribution_analysis
    print(f"  Primary Driver: {attr['primary_driver']}")
    print("  Factor Percentages:"    for factor, percentage in sorted(attr['factor_percentages'].items(), key=lambda x: x[1], reverse=True):
        factor_display = factor.replace('_', ' ').title()
        print("5.1%"
    print("
⚠️  VARE Risk Assessment (5 Dimensions):"    risk = analysis.risk_assessment
    risk_dimensions = {
        'Market Risk': risk['market_risk'],
        'Volatility Risk': risk['volatility_risk'],
        'Liquidity Risk': risk['liquidity_risk'],
        'Credit Risk': risk['credit_risk'],
        'Concentration Risk': risk['concentration_risk']
    }

    for dimension, value in risk_dimensions.items():
        risk_level = "🔴 High" if value > 0.7 else "🟡 Medium" if value > 0.4 else "🟢 Low"
        print("5.3f"
    print("
💬 VEE Investment Narrative:"    exp = analysis.explanation
    print(f"  Summary: {exp['summary']}")
    print(f"  Technical: {exp['technical']}")
    print(f"  Valuation: {exp['valuation_commentary']}")
    print(f"  Catalysts: {exp['catalyst_assessment']}")


def main():
    """Run complete Mercator demonstration"""
    print("🚀 Starting Mercator Vertical Comprehensive Demo")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # Demo 1: Single entity with multiple strategies
        demonstrate_single_entity_analysis()

        # Demo 2: Collection analysis
        demonstrate_portfolio_analysis()

        # Demo 3: Deep factor analysis
        demonstrate_factor_analysis()

        print("\n" + "=" * 80)
        print("✅ Mercator Vertical Demo Complete!")
        print("🏛️ All financial analysis capabilities demonstrated successfully")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()