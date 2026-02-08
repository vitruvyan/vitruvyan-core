"""
Mock Data Provider - Domain Implementation Example

This is a STUB IMPLEMENTATION showing how to implement IDataProvider
for your specific domain.

HOW TO USE THIS AS TEMPLATE:
1. Copy this file to your domain package (e.g., vitruvyan_core/domains/finance/)
2. Rename class to match your domain (e.g., TickerDataProvider)
3. Replace mock data generation with real data sources (PostgreSQL, APIs, files)
4. Keep the same method signatures (contract compliance)
5. Add domain-specific validation logic

CURRENT BEHAVIOR:
- Generates synthetic data (10 entities, 3 features)
- No external dependencies (works offline)
- Suitable for testing and development
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from vitruvyan_core.contracts import IDataProvider, DataProviderError


class MockDataProvider(IDataProvider):
    """
    Mock implementation of IDataProvider contract.
    
    Generates synthetic data for testing without database dependencies.
    Use this as a template for real domain implementations.
    
    Example domains that would implement this:
    - Finance: Query PostgreSQL for tickers, momentum, trend, volatility
    - Healthcare: Query EHR system for patients, vitals, labs, diagnoses
    - Logistics: Query tracking system for shipments, routes, delays
    """
    
    def __init__(self, num_entities: int = 10, seed: int = 42):
        """
        Initialize mock provider with synthetic data parameters.
        
        Args:
            num_entities: Number of entities to generate (default 10)
            seed: Random seed for reproducibility (default 42)
        
        TODO (for real implementation):
            Replace with real connection parameters:
            - Database connection string
            - API credentials
            - File paths
        """
        self.num_entities = num_entities
        self.seed = seed
        np.random.seed(seed)
    
    def get_universe(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Generate mock entity universe.
        
        Returns DataFrame with:
        - entity_id: Unique identifier (E001, E002, ...)
        - entity_name: Display name
        - group: Stratification group (GroupA, GroupB)
        - metadata: Additional domain info
        
        Args:
            filters: Optional filters (e.g., {"group": "GroupA", "active": True})
        
        Returns:
            DataFrame with entity_id, entity_name, group columns
        
        TODO (for real implementation):
            Replace with actual data query:
            
            Finance example:
                SELECT ticker as entity_id, 
                       company_name as entity_name,
                       sector as group,
                       market_cap, industry
                FROM tickers
                WHERE active = true
            
            Healthcare example:
                SELECT patient_id as entity_id,
                       patient_name as entity_name,
                       risk_category as group,
                       age, gender, diagnosis
                FROM patients
                WHERE admission_date >= NOW() - INTERVAL '90 days'
        """
        # Generate entity IDs (E001-E010)
        entity_ids = [f"E{i:03d}" for i in range(1, self.num_entities + 1)]
        
        # Assign groups for stratification
        groups = ['GroupA' if i % 2 == 0 else 'GroupB' for i in range(self.num_entities)]
        
        df = pd.DataFrame({
            'entity_id': entity_ids,
            'entity_name': [f"Entity {i}" for i in range(1, self.num_entities + 1)],
            'group': groups,
            'metadata': [{'category': g} for g in groups]
        })
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if key in df.columns:
                    df = df[df[key] == value]
        
        return df
    
    def get_features(
        self, 
        entity_ids: List[str], 
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Generate mock features for entities.
        
        Returns DataFrame with:
        - entity_id: Entity identifier
        - momentum: Synthetic momentum score (-2 to +2)
        - trend: Synthetic trend score (-2 to +2)
        - volatility: Synthetic volatility score (0 to 2)
        
        Args:
            entity_ids: List of entity IDs to fetch features for
            feature_names: Optional list of specific features (default: all)
        
        Returns:
            DataFrame with entity_id and feature columns
        
        Raises:
            ValidationError: If entity_ids contains invalid IDs
        
        TODO (for real implementation):
            Replace with actual feature queries:
            
            Finance example:
                SELECT ticker as entity_id,
                       rsi_14 as momentum,
                       sma_50_trend as trend,
                       atr_14 as volatility,
                       sentiment_score,
                       dark_pool_ratio
                FROM momentum_logs m
                JOIN trend_logs t USING (ticker)
                JOIN volatility_logs v USING (ticker)
                WHERE ticker IN %(entity_ids)s
                AND date = CURRENT_DATE
            
            Healthcare example:
                SELECT patient_id as entity_id,
                       vital_stability as momentum,
                       disease_progression as trend,
                       symptoms_volatility as volatility,
                       lab_results_score
                FROM patient_metrics
                WHERE patient_id IN %(entity_ids)s
        """
        # Validate entity IDs
        valid_ids = [f"E{i:03d}" for i in range(1, self.num_entities + 1)]
        invalid = [eid for eid in entity_ids if eid not in valid_ids]
        if invalid:
            raise DataProviderError(f"Invalid entity IDs: {invalid}")
        
        # Generate synthetic features
        data = {
            'entity_id': entity_ids,
            'momentum': np.random.uniform(-2, 2, len(entity_ids)),
            'trend': np.random.uniform(-2, 2, len(entity_ids)),
            'volatility': np.random.uniform(0, 2, len(entity_ids))
        }
        
        df = pd.DataFrame(data)
        
        # Filter to requested features if specified
        if feature_names:
            available = ['entity_id'] + [f for f in feature_names if f in df.columns]
            df = df[available]
        
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return mock metadata about data source.
        
        Returns:
            Dict with domain, version, last_updated, entity_count
        
        TODO (for real implementation):
            Return actual metadata:
            
            Finance example:
                {
                    'domain': 'finance',
                    'source': 'PostgreSQL',
                    'version': '2.0',
                    'last_updated': query_last_updated_timestamp(),
                    'entity_count': query_ticker_count(),
                    'features': ['momentum', 'trend', 'volatility', 'sentiment'],
                    'stratification_groups': ['Technology', 'Healthcare', 'Finance']
                }
        """
        return {
            'domain': 'mock',
            'source': 'synthetic',
            'version': '1.0',
            'last_updated': '2026-02-08',
            'entity_count': self.num_entities,
            'features': ['momentum', 'trend', 'volatility'],
            'stratification_groups': ['GroupA', 'GroupB']
        }
    
    def validate_entity_ids(self, entity_ids: List[str]) -> List[str]:
        """
        Validate which entity IDs exist in mock universe.
        
        Args:
            entity_ids: List of entity IDs to validate
        
        Returns:
            List of valid entity IDs found
        
        TODO (for real implementation):
            Query database to check existence:
            
            Finance example:
                SELECT ticker FROM tickers 
                WHERE ticker IN %(entity_ids)s
                AND active = true
        """
        valid_ids = [f"E{i:03d}" for i in range(1, self.num_entities + 1)]
        return [eid for eid in entity_ids if eid in valid_ids]


# ============================================================================
# HOW TO IMPLEMENT FOR YOUR DOMAIN
# ============================================================================
"""
STEP 1: Copy this file to your domain package
    vitruvyan_core/domains/finance/ticker_provider.py

STEP 2: Rename class to match domain
    class TickerDataProvider(IDataProvider):

STEP 3: Replace __init__ with real connection
    def __init__(self, db_connection_string: str):
        from core.leo.postgres_agent import PostgresAgent
        self.pg = PostgresAgent()

STEP 4: Replace get_universe with real query
    def get_universe(self, filters=None):
        query = "SELECT ticker as entity_id, company_name as entity_name, sector as group FROM tickers WHERE active=true"
        return self.pg.execute_query(query).to_df()

STEP 5: Replace get_features with real query
    def get_features(self, entity_ids, feature_names=None):
        query = '''
            SELECT ticker as entity_id, rsi_14 as momentum, sma_50_trend as trend
            FROM momentum_logs WHERE ticker IN %s
        '''
        return self.pg.execute_query(query, (entity_ids,)).to_df()

STEP 6: Test with real data
    provider = TickerDataProvider(db_string)
    universe = provider.get_universe()
    features = provider.get_features(['AAPL', 'MSFT'])

DONE! Now your domain is pluggable into Neural Engine.
"""
