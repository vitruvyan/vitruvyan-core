# api_neural_engine/modules/engine_orchestrator.py
"""
Engine Orchestrator - Bridge between FastAPI and domain-agnostic Neural Engine.

This module:
1. Initializes NeuralEngine with domain-specific provider + strategy
2. Translates API requests to NeuralEngine.run() calls
3. Handles caching, error recovery, and metrics
4. Provides health checks for dependencies

Architecture:
    FastAPI endpoints → EngineOrchestrator → NeuralEngine → IDataProvider/IScoringStrategy
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any

from vitruvyan_core.core.neural_engine import NeuralEngine
from vitruvyan_core.contracts import IDataProvider, IScoringStrategy

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    Orchestrator for Neural Engine API operations.
    
    Responsibilities:
    - Initialize NeuralEngine with domain provider + strategy
    - Execute screening and ranking operations
    - Cache results for repeated queries
    - Monitor dependency health
    """
    
    def __init__(self):
        """Initialize orchestrator (deferred initialization in async method)"""
        self.engine: Optional[NeuralEngine] = None
        self.data_provider: Optional[IDataProvider] = None
        self.scoring_strategy: Optional[IScoringStrategy] = None
        self._cache: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize engine with domain-specific implementations.
        
        TODO: Load domain from environment variable
        - For finance: TickerDataProvider + FinancialScoringStrategy
        - For healthcare: PatientDataProvider + ClinicalScoringStrategy
        - For testing: MockDataProvider + MockScoringStrategy
        """
        logger.info("🔧 Initializing Engine Orchestrator...")
        
        try:
            # TODO: Load domain from ENV (for now, use mock for testing)
            from vitruvyan_core.core.neural_engine.domain_examples import (
                MockDataProvider,
                MockScoringStrategy
            )
            
            self.data_provider = MockDataProvider(num_entities=100)
            self.scoring_strategy = MockScoringStrategy()
            
            # Initialize Neural Engine
            self.engine = NeuralEngine(
                data_provider=self.data_provider,
                scoring_strategy=self.scoring_strategy
            )
            
            self._initialized = True
            logger.info("✅ Engine Orchestrator initialized with MockDataProvider")
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize Engine Orchestrator: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown orchestrator and cleanup resources"""
        logger.info("🛑 Shutting down Engine Orchestrator...")
        self._cache.clear()
        self._initialized = False
    
    async def screen(
        self,
        profile: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        stratification_mode: str = "global",
        risk_tolerance: str = "medium"
    ) -> Dict[str, Any]:
        """
        Execute multi-factor screening.
        
        Args:
            profile: Scoring profile name
            filters: Optional entity filters
            top_k: Number of top entities to return
            stratification_mode: Z-score calculation mode
            risk_tolerance: Risk adjustment level
        
        Returns:
            Dict with ranked_entities, metadata, diagnostics
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"screen:{profile}:{filters}:{top_k}:{stratification_mode}:{risk_tolerance}"
        
        # Check cache (30s TTL)
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < 30:
                logger.info(f"✅ Cache hit for {cache_key}")
                return cached_data
        
        # Execute screening via NeuralEngine
        try:
            result = self.engine.run(
                profile=profile,
                filters=filters,
                top_k=top_k,
                stratification_mode=stratification_mode,
                risk_tolerance=risk_tolerance
            )
            
            # Transform result to API response format
            response = {
                "ranked_entities": [
                    {
                        "rank": row["rank"],
                        "entity_id": row["entity_id"],
                        "entity_name": row.get("entity_name"),
                        "composite_score": row["composite_score"],
                        "percentile": row["percentile"],
                        "bucket": row["bucket"],
                        "group": row.get("group"),
                        "metadata": row.get("metadata")
                    }
                    for _, row in result["ranked_entities"].iterrows()
                ],
                "profile": profile,
                "top_k": top_k,
                "stratification_mode": stratification_mode,
                "total_entities_evaluated": result["metadata"]["total_entities"],
                "profile_weights": result["profile_weights"],
                "processing_time_ms": (time.time() - start_time) * 1000,
                "statistics": result.get("statistics")
            }
            
            # Cache result
            self._cache[cache_key] = (response, time.time())
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Screening failed: {e}")
            raise
    
    async def rank(
        self,
        feature_name: str,
        entity_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        higher_is_better: bool = True
    ) -> Dict[str, Any]:
        """
        Execute single-feature ranking.
        
        Args:
            feature_name: Feature to rank by
            entity_ids: Optional entity IDs to rank
            top_k: Number of top entities to return
            higher_is_better: Whether higher values are better
        
        Returns:
            Dict with ranked_entities, metadata
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        start_time = time.time()
        
        # Get universe
        universe = self.data_provider.get_universe()
        
        # Filter by entity_ids if provided
        if entity_ids:
            universe = universe[universe["entity_id"].isin(entity_ids)]
        
        # Get feature values
        features = self.data_provider.get_features(
            entity_ids=universe["entity_id"].tolist(),
            feature_names=[feature_name]
        )
        
        # Merge and sort
        merged = universe.merge(features, on="entity_id")
        merged = merged.sort_values(
            by=feature_name,
            ascending=not higher_is_better
        )
        
        # Apply top_k
        if top_k:
            merged = merged.head(top_k)
        
        # Add ranks
        merged["rank"] = range(1, len(merged) + 1)
        
        # Format response
        response = {
            "ranked_entities": [
                {
                    "rank": row["rank"],
                    "entity_id": row["entity_id"],
                    "entity_name": row.get("entity_name"),
                    "composite_score": row[feature_name],  # Raw feature value
                    "percentile": (len(merged) - row["rank"] + 1) / len(merged) * 100,
                    "bucket": "top" if row["rank"] <= len(merged) * 0.3 else "middle"
                }
                for _, row in merged.iterrows()
            ],
            "feature_name": feature_name,
            "higher_is_better": higher_is_better,
            "total_entities_ranked": len(merged),
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        return response
    
    async def get_available_profiles(self) -> List[Dict[str, str]]:
        """
        Get list of available scoring profiles.
        
        Returns:
            List of dicts with profile name and description
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        profiles = self.scoring_strategy.get_available_profiles()
        
        return [
            {"name": p, "description": f"Scoring profile: {p}"}
            for p in profiles
        ]
    
    async def health_check(self) -> bool:
        """Check orchestrator health"""
        return self._initialized
    
    async def check_data_provider(self) -> bool:
        """Check data provider health"""
        if not self.data_provider:
            return False
        try:
            # Test query
            universe = self.data_provider.get_universe()
            return len(universe) > 0
        except Exception as e:
            logger.error(f"❌ Data provider health check failed: {e}")
            return False
    
    async def check_scoring_strategy(self) -> bool:
        """Check scoring strategy health"""
        if not self.scoring_strategy:
            return False
        try:
            # Test query
            profiles = self.scoring_strategy.get_available_profiles()
            return len(profiles) > 0
        except Exception as e:
            logger.error(f"❌ Scoring strategy health check failed: {e}")
            return False
