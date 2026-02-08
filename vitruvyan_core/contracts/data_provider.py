"""
Data Provider Contract (Interface)
===================================

Defines the contract for domain-specific data providers.
Any domain (finance, healthcare, logistics) must implement this interface
to integrate with the Generic Aggregation Engine.

Author: vitruvyan-core
Date: February 8, 2026
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class IDataProvider(ABC):
    """
    Abstract interface for domain-specific data providers.
    
    Each domain must implement this contract to provide:
    1. Entity universe (e.g., tickers, patients, shipments)
    2. Feature data for each entity
    3. Metadata about available metrics
    
    Example domains:
    - Finance: TickerDataProvider (stocks, ETFs, crypto)
    - Healthcare: PatientDataProvider (patients, cohorts)
    - Logistics: ShipmentDataProvider (routes, carriers)
    """
    
    @abstractmethod
    def get_universe(
        self, 
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Returns the universe of entities to analyze.
        
        Args:
            filters: Optional filters (e.g., {"sector": "Technology", "country": "US"})
        
        Returns:
            DataFrame with columns:
              - entity_id: Unique identifier (e.g., ticker, patient_id, shipment_id)
              - stratification_field: Grouping field for stratified z-scores (e.g., sector, age_group, region)
              - [additional metadata columns]
        
        Example (Finance):
            | entity_id | stratification_field | country | active |
            |-----------|---------------------|---------|--------|
            | AAPL      | Technology          | US      | True   |
            | MSFT      | Technology          | US      | True   |
            | XOM       | Energy              | US      | True   |
        """
        pass
    
    @abstractmethod
    def get_features(
        self, 
        entity_ids: List[str],
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Returns feature data for specified entities.
        
        Args:
            entity_ids: List of entity identifiers
            feature_names: Optional list of specific features to fetch
                          (if None, returns all available features)
        
        Returns:
            DataFrame with columns:
              - entity_id: Entity identifier
              - [feature columns with raw values]
        
        Example (Finance):
            | entity_id | rsi  | sma_short | sma_medium | atr  | sentiment_raw |
            |-----------|------|-----------|------------|------|---------------|
            | AAPL      | 68.5 | 180.2     | 175.8      | 3.2  | 0.85          |
            | MSFT      | 45.2 | 380.1     | 382.3      | 5.1  | 0.65          |
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns metadata about the data provider.
        
        Returns:
            Dict with keys:
              - domain: Domain name (e.g., "finance", "healthcare", "logistics")
              - entity_type: Type of entities (e.g., "stock", "patient", "shipment")
              - stratification_field: Field used for stratification (e.g., "sector", "age_group")
              - available_features: List of feature names available
              - feature_descriptions: Dict mapping feature names to descriptions
        
        Example (Finance):
            {
                "domain": "finance",
                "entity_type": "stock",
                "stratification_field": "sector",
                "available_features": ["momentum", "trend", "volatility", "sentiment"],
                "feature_descriptions": {
                    "momentum": "RSI-based momentum indicator",
                    "trend": "SMA crossover trend strength",
                    ...
                }
            }
        """
        pass
    
    @abstractmethod
    def validate_entity_ids(self, entity_ids: List[str]) -> Dict[str, bool]:
        """
        Validates that entity IDs exist in the data source.
        
        Args:
            entity_ids: List of entity IDs to validate
        
        Returns:
            Dict mapping entity_id -> is_valid (True/False)
        
        Example:
            {"AAPL": True, "MSFT": True, "INVALID": False}
        """
        pass
    
    def get_entity_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Returns the count of entities matching filters (optional).
        Default implementation calls get_universe() and counts rows.
        
        Args:
            filters: Optional filters
        
        Returns:
            Number of entities
        """
        return len(self.get_universe(filters=filters))
    
    def supports_streaming(self) -> bool:
        """
        Returns True if provider supports streaming updates (optional).
        Default: False (batch-only).
        
        For real-time domains (e.g., IoT, trading), this can be overridden.
        """
        return False


class DataProviderError(Exception):
    """Base exception for data provider errors"""
    pass


class EntityNotFoundError(DataProviderError):
    """Raised when requested entity doesn't exist"""
    pass


class FeatureNotAvailableError(DataProviderError):
    """Raised when requested feature is not available"""
    pass
