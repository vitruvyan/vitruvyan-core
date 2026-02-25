import pandas as pd

from vitruvyan_core.domains.finance.neural_engine.scoring_strategy import (
    FinancialScoringStrategy,
)


def test_finance_profiles_sum_to_one():
    strategy = FinancialScoringStrategy()
    for profile in strategy.PROFILE_WEIGHTS.keys():
        weights = strategy.get_profile_weights(profile)
        assert abs(sum(weights.values()) - 1.0) < 1e-9, profile


def test_profile_alias_resolution():
    strategy = FinancialScoringStrategy()
    balanced_alias = strategy.get_profile_weights("balanced")
    balanced_canonical = strategy.get_profile_weights("balanced_mid")
    assert balanced_alias == balanced_canonical

    aggressive_alias = strategy.get_profile_weights("aggressive")
    aggressive_canonical = strategy.get_profile_weights("momentum_focus")
    assert aggressive_alias == aggressive_canonical


def test_risk_adjustment_vare_then_volatility_fallback():
    strategy = FinancialScoringStrategy()
    df = pd.DataFrame(
        [
            {
                "entity_id": "A",
                "composite_score": 1.0,
                "vare_risk_score": 50.0,
                "volatility_z": None,
            },
            {
                "entity_id": "B",
                "composite_score": 1.0,
                "vare_risk_score": None,
                "volatility_z": 2.0,
            },
            {
                "entity_id": "C",
                "composite_score": 1.0,
                "vare_risk_score": None,
                "volatility_z": None,
            },
        ]
    )

    out = strategy.apply_risk_adjustment(df, risk_tolerance="medium")

    # VARE formula: 1.0 * (1 - 0.50 * 0.20) = 0.90
    assert round(float(out.loc[out["entity_id"] == "A", "composite_score"].iloc[0]), 4) == 0.9

    # Fallback formula: 1.0 / (1 + abs(2.0) * 0.20) = 0.7143
    assert round(float(out.loc[out["entity_id"] == "B", "composite_score"].iloc[0]), 4) == 0.7143

    # No risk signal available -> unchanged
    assert round(float(out.loc[out["entity_id"] == "C", "composite_score"].iloc[0]), 4) == 1.0
