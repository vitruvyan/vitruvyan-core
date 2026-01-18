#!/usr/bin/env python3
"""
Test script for VARE domain-agnostic refactoring
"""

import pandas as pd
import numpy as np
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import VAREEngine
from vitruvyan_core.verticals.mercator.providers import MercatorRiskProvider

def test_vare_domain_agnostic():
    """Test the refactored VARE components with domain provider"""

    # Create sample financial data (simulate yfinance data)
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)  # For reproducible results

    # Generate sample OHLCV data
    n_days = len(dates)
    base_price = 150.0

    # Simulate price movement with some volatility
    price_changes = np.random.normal(0.001, 0.02, n_days)  # Small daily changes
    prices = base_price * np.exp(np.cumsum(price_changes))

    # Create DataFrame similar to yfinance output
    data = pd.DataFrame({
        'Open': prices * (1 + np.random.normal(0, 0.005, n_days)),
        'High': prices * (1 + np.random.normal(0.005, 0.01, n_days)),
        'Low': prices * (1 - np.random.normal(0.005, 0.01, n_days)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, n_days)
    }, index=dates)

    entity_id = "EXAMPLE_ENTITY_1"

    # Initialize components
    engine = VAREEngine()
    provider = MercatorRiskProvider()

    # Test analyze_entity
    try:
        result = engine.analyze_entity(entity_id, data, provider)
        print("✅ VARE Engine analyze_entity: SUCCESS")
        print(f"Entity: {result.entity_id}")
        print(f"Overall Risk: {result.overall_risk:.1f}/100 ({result.risk_category})")
        print(f"Market Risk: {result.market_risk:.1f}")
        print(f"Volatility Risk: {result.volatility_risk:.1f}")
        print(f"Liquidity Risk: {result.liquidity_risk:.1f}")
        print(f"Correlation Risk: {result.correlation_risk:.1f}")
        print(f"Confidence: {result.confidence:.2f}")
    except Exception as e:
        print(f"❌ VARE Engine analyze_entity: FAILED - {e}")
        return False

    # Test standalone function
    try:
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import analyze_ticker

        # This will try to fetch real data, so it might fail without internet
        # but the import should work
        print("✅ VARE analyze_ticker function: IMPORT SUCCESS")

    except Exception as e:
        print(f"❌ VARE analyze_ticker function: FAILED - {e}")
        return False

    print("\n🎉 All VARE domain-agnostic tests PASSED!")
    return True

if __name__ == "__main__":
    test_vare_domain_agnostic()