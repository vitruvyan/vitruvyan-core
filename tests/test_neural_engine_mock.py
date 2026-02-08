"""
Mock Data Provider (for testing)
================================

Minimal implementation of IDataProvider for testing Neural Engine.

Author: vitruvyan-core
Date: February 8, 2026
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from vitruvyan_core.contracts import IDataProvider


class MockDataProvider(IDataProvider):
    """
    Mock data provider for testing.
    
    Simulates a simple domain with:
    - 10 entities (E001-E010)
    - 2 stratification groups (GroupA, GroupB)
    - 3 features (momentum, trend, volatility)
    """
    
    def __init__(self):
        # Mock universe
        self.universe = pd.DataFrame({
            "entity_id": [f"E{i:03d}" for i in range(1, 11)],
            "stratification_field": ["GroupA"] * 5 + ["GroupB"] * 5,
            "active": [True] * 10
        })
        
        # Mock features
        np.random.seed(42)
        self.features = pd.DataFrame({
            "entity_id": [f"E{i:03d}" for i in range(1, 11)],
            "momentum": np.random.randn(10) * 10 + 50,
            "trend": np.random.randn(10) * 5 + 10,
            "volatility": np.random.rand(10) * 20 + 5
        })
    
    def get_universe(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Returns mock universe."""
        return self.universe.copy()
    
    def get_features(
        self, 
        entity_ids: List[str],
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Returns mock features for specified entities."""
        df = self.features[self.features["entity_id"].isin(entity_ids)].copy()
        
        if feature_names:
            cols_to_keep = ["entity_id"] + [c for c in feature_names if c in df.columns]
            df = df[cols_to_keep]
        
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        """Returns provider metadata."""
        return {
            "domain": "mock",
            "entity_type": "generic_entity",
            "stratification_field": "stratification_field",
            "available_features": ["momentum", "trend", "volatility"],
            "feature_descriptions": {
                "momentum": "Mock momentum metric",
                "trend": "Mock trend metric",
                "volatility": "Mock volatility metric"
            }
        }
    
    def validate_entity_ids(self, entity_ids: List[str]) -> Dict[str, bool]:
        """Validates entity IDs."""
        valid_ids = set(self.universe["entity_id"])
        return {eid: eid in valid_ids for eid in entity_ids}
