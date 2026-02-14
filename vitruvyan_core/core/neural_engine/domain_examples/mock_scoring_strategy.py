"""
Mock Scoring Strategy - Domain Implementation Example

This is a STUB IMPLEMENTATION showing how to implement IScoringStrategy
for your specific domain.

HOW TO USE THIS AS TEMPLATE:
1. Copy this file to your domain package (e.g., vitruvyan_core/domains/finance/)
2. Rename class to match your domain (e.g., FinancialScoringStrategy)
3. Replace mock profiles with real domain profiles
4. Implement domain-specific risk adjustment (optional)

Note: Composite score computation (weighted z-score average) is handled
by CompositeScorer in the core engine. The strategy provides WEIGHTS via
get_profile_weights(), not the scoring algorithm itself.

CURRENT BEHAVIOR:
- Provides 2 mock profiles (balanced, aggressive)
- No risk adjustment (returns scores unchanged)
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from contracts import IScoringStrategy, ScoringStrategyError


class MockScoringStrategy(IScoringStrategy):
    """
    Mock implementation of IScoringStrategy contract.
    
    Provides basic scoring logic for testing without domain complexity.
    Use this as a template for real domain implementations.
    
    The strategy provides profile weights and optional risk adjustment.
    Composite score computation is handled by CompositeScorer in the core.
    """
    
    def __init__(self):
        """
        Initialize mock strategy with predefined profiles.
        
        TODO (for real implementation):
            Load profiles from configuration:
            - Database table (profile_weights)
            - YAML/JSON config file
            - Environment variables
        """
        # Mock profiles: feature -> weight mapping
        self._profiles = {
            'balanced': {
                'momentum': 0.33,
                'trend': 0.33,
                'volatility': 0.34
            },
            'aggressive': {
                'momentum': 0.60,
                'trend': 0.30,
                'volatility': 0.10
            }
        }
    
    def get_profile_weights(self, profile: str) -> Dict[str, float]:
        """
        Get feature weights for a scoring profile.
        
        Args:
            profile: Profile name (e.g., 'balanced', 'aggressive')
        
        Returns:
            Dict mapping feature names to weights (must sum to 1.0)
        
        Raises:
            ScoringStrategyError: If profile doesn't exist
        
        TODO (for real implementation):
            Load from database/config:
            
            Finance example:
                profiles = {
                    'short_spec': {
                        'momentum': 0.40,
                        'trend': 0.20,
                        'volatility': 0.15,
                        'sentiment': 0.25
                    },
                    'balanced_mid': {
                        'momentum': 0.25,
                        'trend': 0.30,
                        'volatility': 0.20,
                        'sentiment': 0.15,
                        'fundamentals': 0.10
                    }
                }
            
            Healthcare example:
                profiles = {
                    'high_risk': {
                        'vital_stability': 0.40,
                        'disease_progression': 0.35,
                        'symptoms_volatility': 0.15,
                        'lab_results': 0.10
                    }
                }
        """
        if profile not in self._profiles:
            available = list(self._profiles.keys())
            raise ScoringStrategyError(
                f"Unknown profile '{profile}'. Available: {available}"
            )
        
        return self._profiles[profile].copy()
    
    def get_available_profiles(self) -> List[str]:
        """
        List all available scoring profiles.
        
        Returns:
            List of profile names
        
        TODO (for real implementation):
            Query from database:
            
            Finance example:
                SELECT DISTINCT profile_name 
                FROM profile_weights 
                WHERE active = true
                ORDER BY profile_name
        """
        return list(self._profiles.keys())
    
    def apply_risk_adjustment(
        self,
        df: pd.DataFrame,
        risk_tolerance: Optional[str] = None,
        risk_columns: Optional[list] = None
    ) -> pd.DataFrame:
        """
        Apply domain-specific risk adjustment to composite scores.
        
        Args:
            df: DataFrame with composite_score column
            risk_tolerance: 'low', 'medium', 'high' (or None for no adjustment)
            risk_columns: Optional column names containing risk metrics
        
        Returns:
            DataFrame with adjusted composite_score column
        
        TODO (for real implementation):
            Implement domain-specific risk logic:
            
            Finance example:
                - Query VARE risk scores
                - Apply penalty based on risk tolerance:
                    penalty = vare_risk_score / 100 * tolerance_multiplier
                    df['composite_score'] *= (1 - penalty)
                - Low tolerance: 0.40 multiplier (40% penalty for risk=100)
                - High tolerance: 0.08 multiplier (8% penalty for risk=100)
            
            Healthcare example:
                - Check patient comorbidities
                - Boost scores for preventive care profiles
                - Penalize if hospitalization risk > threshold
        """
        # Mock: no risk adjustment, return DataFrame unchanged
        return df.copy()
    
    def validate_profile(self, profile: str) -> bool:
        """
        Validate if a profile exists and has valid weights.
        
        Args:
            profile: Profile name to validate
        
        Returns:
            True if valid, False otherwise
        
        TODO (for real implementation):
            Add validation rules:
            - Check weights sum to ~1.0 (±0.01 tolerance)
            - Verify all features exist in data schema
            - Check profile is marked active in database
        """
        if profile not in self._profiles:
            return False
        
        weights = self._profiles[profile]
        weight_sum = sum(weights.values())
        
        # Validate weights sum to 1.0 (±0.01 tolerance)
        return abs(weight_sum - 1.0) < 0.01


# ============================================================================
# HOW TO IMPLEMENT FOR YOUR DOMAIN
# ============================================================================
"""
STEP 1: Copy this file to your domain package
    vitruvyan_core/domains/finance/scoring_strategy.py

STEP 2: Rename class to match domain
    class FinancialScoringStrategy(IScoringStrategy):

STEP 3: Load real profiles from config/database
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self._profiles = yaml.safe_load(f)

STEP 4: Implement real risk adjustment (optional)
    def apply_risk_adjustment(self, df, risk_tolerance=None, risk_columns=None):
        # Finance example: integrate VARE risk engine
        from core.vpar.vare.vare_engine import VAREEngine
        vare = VAREEngine()
        risk_scores = vare.assess_risk(df['entity_id'].tolist())
        
        penalties = {
            'low': 0.40,    # Conservative: 40% max penalty
            'medium': 0.20, # Balanced: 20% max penalty
            'high': 0.08    # Aggressive: 8% max penalty
        }
        penalty = penalties.get(risk_tolerance, 0.20)
        
        df = df.copy()
        df['composite_score'] *= (1 - risk_scores / 100 * penalty)
        return df

STEP 5: Test with real data
    strategy = FinancialScoringStrategy('config/profiles.yaml')
    weights = strategy.get_profile_weights('balanced_mid')
    # Composite scoring is handled by CompositeScorer using these weights

DONE! Now your domain is pluggable into Neural Engine.
"""
