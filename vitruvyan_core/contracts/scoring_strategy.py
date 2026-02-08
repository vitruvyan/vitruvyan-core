"""
Scoring Strategy Contract (Interface)
======================================

Defines the contract for domain-specific scoring strategies.
Scoring strategies define:
1. How to weight different features (profiles)
2. How to compute composite scores
3. Risk adjustment logic (optional)

Author: vitruvyan-core
Date: February 8, 2026
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class IScoringStrategy(ABC):
    """
    Abstract interface for domain-specific scoring strategies.
    
    Each domain defines:
    - Feature weights for different profiles (e.g., "aggressive", "conservative")
    - Composite score computation rules
    - Risk adjustment strategies
    
    Example domains:
    - Finance: profile-based weights (short_spec, balanced_mid, etc.)
    - Healthcare: risk-adjusted patient prioritization
    - Logistics: delivery urgency + cost optimization
    """
    
    @abstractmethod
    def get_profile_weights(self, profile: str) -> Dict[str, float]:
        """
        Returns feature weights for a specific profile.
        
        Args:
            profile: Profile name (e.g., "aggressive", "balanced", "conservative")
        
        Returns:
            Dict mapping feature_name -> weight (must sum to 1.0)
        
        Example (Finance - "short_spec" profile):
            {
                "momentum": 0.35,
                "trend": 0.20,
                "volatility": 0.15,
                "sentiment": 0.10,
                "fundamentals": 0.20
            }
        
        Example (Healthcare - "high_risk" profile):
            {
                "severity_score": 0.40,
                "comorbidity_index": 0.30,
                "admission_risk": 0.20,
                "readmission_risk": 0.10
            }
        """
        pass
    
    @abstractmethod
    def get_available_profiles(self) -> List[str]:
        """
        Returns list of available profile names.
        
        Returns:
            List of profile names
        
        Example (Finance):
            ["short_spec", "balanced_mid", "trend_follow", "momentum_focus"]
        
        Example (Healthcare):
            ["high_risk", "moderate_risk", "preventive_care"]
        """
        pass
    
    @abstractmethod
    def compute_composite_score(
        self, 
        df: pd.DataFrame, 
        profile: str,
        z_score_columns: List[str]
    ) -> pd.DataFrame:
        """
        Computes composite score using weighted z-scores.
        
        Args:
            df: DataFrame with z-score columns
            profile: Profile name for weight selection
            z_score_columns: List of z-score column names to use
        
        Returns:
            DataFrame with additional column:
              - composite_score: Weighted average of z-scores
        
        Algorithm:
            composite_score = Σ(z_score_i × weight_i) / Σ(weight_i)
        
        Note: Handles missing z-scores gracefully (normalize weights dynamically)
        """
        pass
    
    def apply_risk_adjustment(
        self, 
        df: pd.DataFrame,
        risk_tolerance: Optional[str] = None,
        risk_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Applies risk adjustment to composite scores (optional).
        
        Args:
            df: DataFrame with composite_score column
            risk_tolerance: Risk tolerance level (e.g., "low", "medium", "high")
            risk_columns: Column names containing risk metrics
        
        Returns:
            DataFrame with adjusted composite_score
        
        Default implementation: No adjustment (returns df as-is).
        Override in subclasses for domain-specific risk logic.
        
        Example (Finance VARE adjustment):
            adjusted_score = composite_score × (1 - vare_risk_score/100 × penalty)
        
        Example (Healthcare):
            adjusted_score = composite_score × (1 + patient_risk_factor × urgency_weight)
        """
        return df
    
    def get_profile_metadata(self, profile: str) -> Dict[str, Any]:
        """
        Returns metadata about a specific profile (optional).
        
        Args:
            profile: Profile name
        
        Returns:
            Dict with keys:
              - description: Human-readable profile description
              - use_case: When to use this profile
              - weights: Feature weights dict
              - risk_adjustment: Whether risk adjustment is enabled
        
        Example (Finance - "short_spec"):
            {
                "description": "Short-term speculation (1-2 weeks)",
                "use_case": "High-velocity trading, momentum plays",
                "weights": {
                    "momentum": 0.35,
                    "trend": 0.20,
                    ...
                },
                "risk_adjustment": True
            }
        """
        return {
            "description": f"Profile: {profile}",
            "weights": self.get_profile_weights(profile),
            "risk_adjustment": False
        }
    
    def validate_profile(self, profile: str) -> bool:
        """
        Validates that profile exists and weights sum to 1.0.
        
        Args:
            profile: Profile name
        
        Returns:
            True if valid, False otherwise
        """
        if profile not in self.get_available_profiles():
            return False
        
        weights = self.get_profile_weights(profile)
        weight_sum = sum(weights.values())
        
        # Allow 1% tolerance for floating-point errors
        return abs(weight_sum - 1.0) < 0.01


class ScoringStrategyError(Exception):
    """Base exception for scoring strategy errors"""
    pass


class InvalidProfileError(ScoringStrategyError):
    """Raised when profile doesn't exist"""
    pass


class InvalidWeightsError(ScoringStrategyError):
    """Raised when weights don't sum to 1.0"""
    pass
