"""
Neural Engine (Domain-Agnostic Core)
=====================================

Generic multi-factor ranking engine that works with any domain.

The Neural Engine orchestrates:
1. Data acquisition (via IDataProvider)
2. Z-score calculation (stratified or global)
3. Composite scoring (via IScoringStrategy)
4. Risk adjustment (via IScoringStrategy)
5. Ranking and bucketing

Architecture:
- Core logic is 100% domain-agnostic
- Domain specifics provided via contracts (IDataProvider, IScoringStrategy)

Author: vitruvyan-core
Date: February 8, 2026
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd

from vitruvyan_core.contracts import IDataProvider, IScoringStrategy
from .scoring import ZScoreCalculator, StratificationMode
from .composite import CompositeScorer
from .ranking import RankingEngine

logger = logging.getLogger(__name__)


class NeuralEngine:
    """
    Domain-agnostic multi-factor ranking engine.
    
    The Neural Engine is the core orchestrator that:
    - Fetches entity universe and features from IDataProvider
    - Computes z-scores (with stratification support)
    - Calculates weighted composite scores using IScoringStrategy profiles
    - Applies risk adjustments
    - Ranks and buckets entities
    
    Usage:
        # Initialize with domain-specific implementations
        provider = FinancialDataProvider()  # implements IDataProvider
        strategy = FinancialScoringStrategy()  # implements IScoringStrategy
        
        engine = NeuralEngine(
            data_provider=provider,
            scoring_strategy=strategy,
            stratification_mode="composite"
        )
        
        # Run ranking
        results = engine.run(
            profile="aggressive",
            top_k=10,
            entity_ids=["AAPL", "MSFT", "GOOGL"],
            risk_tolerance="medium"
        )
    """
    
    def __init__(
        self,
        data_provider: IDataProvider,
        scoring_strategy: IScoringStrategy,
        stratification_mode: StratificationMode = "global",
        enable_time_decay: bool = False,
        time_decay_half_life: float = 30.0
    ):
        """
        Initialize Neural Engine.
        
        Args:
            data_provider: Implementation of IDataProvider
            scoring_strategy: Implementation of IScoringStrategy
            stratification_mode: "global", "stratified", or "composite"
            enable_time_decay: Apply exponential time decay to z-scores
            time_decay_half_life: Decay half-life in days (default: 30)
        """
        self.data_provider = data_provider
        self.scoring_strategy = scoring_strategy
        self.stratification_mode = stratification_mode
        self.enable_time_decay = enable_time_decay
        self.time_decay_half_life = time_decay_half_life
        
        # Get metadata from provider
        self.metadata = data_provider.get_metadata()
        self.stratification_field = self.metadata.get("stratification_field")
        
        # Initialize components
        self.z_calculator = ZScoreCalculator(
            stratification_mode=stratification_mode,
            stratification_field=self.stratification_field
        )
        self.composite_scorer = CompositeScorer(scoring_strategy)
        self.ranker = RankingEngine()
        
        logger.info(f"NeuralEngine initialized: domain={self.metadata.get('domain')}, "
                   f"stratification={stratification_mode}, time_decay={enable_time_decay}")
    
    def run(
        self,
        profile: str = "balanced",
        top_k: Optional[int] = None,
        entity_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        risk_tolerance: Optional[str] = None,
        feature_subset: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full Neural Engine pipeline.
        
        Args:
            profile: Scoring profile name (e.g., "aggressive", "balanced", "conservative")
            top_k: Number of top entities to return (None = all)
            entity_ids: Specific entity IDs to analyze (None = use universe)
            filters: Filters for universe extraction (e.g., {"sector": "Technology"})
            risk_tolerance: Risk adjustment level ("low", "medium", "high", None)
            feature_subset: Specific features to use (None = all available)
        
        Returns:
            Dict with keys:
              - ranked_entities: DataFrame with ranked entities
              - metadata: Engine and execution metadata
              - statistics: Bucket statistics
              - diagnostics: Execution diagnostics
        
        Pipeline:
            1. Extract universe (entities to analyze)
            2. Extract features (raw metrics)
            3. Compute z-scores (stratified or global)
            4. Apply time decay (if enabled)
            5. Compute composite scores (weighted average)
            6. Apply risk adjustment (if specified)
            7. Rank entities (by composite score)
            8. Return top-K results
        """
        logger.info(f"NeuralEngine.run: profile={profile}, top_k={top_k}, "
                   f"entity_ids={entity_ids[:3] if entity_ids else None}...")
        
        # Validate profile
        if not self.scoring_strategy.validate_profile(profile):
            available_profiles = self.scoring_strategy.get_available_profiles()
            raise ValueError(f"Invalid profile '{profile}'. Available: {available_profiles}")
        
        # STEP 1: Extract universe
        if entity_ids:
            # Filter universe to specific entities
            universe_df = self.data_provider.get_universe(filters=filters)
            universe_df = universe_df[universe_df["entity_id"].isin(entity_ids)]
            logger.info(f"Universe filtered to {len(universe_df)} specified entities")
        else:
            # Get full universe (optionally filtered)
            universe_df = self.data_provider.get_universe(filters=filters)
            logger.info(f"Universe extracted: {len(universe_df)} entities")
        
        if universe_df.empty:
            return self._empty_result("No entities in universe")
        
        entity_ids_to_fetch = universe_df["entity_id"].tolist()
        
        # STEP 2: Extract features
        features_to_fetch = feature_subset if feature_subset else None
        features_df = self.data_provider.get_features(
            entity_ids=entity_ids_to_fetch,
            feature_names=features_to_fetch
        )
        
        logger.info(f"Features extracted: {features_df.shape[1]} columns, {len(features_df)} rows")
        
        # Merge universe + features
        df = universe_df.merge(features_df, on="entity_id", how="left")
        
        # STEP 3: Compute z-scores
        # Identify feature columns (exclude metadata columns)
        metadata_cols = {"entity_id", self.stratification_field, "active", "country"}
        feature_cols = [c for c in df.columns if c not in metadata_cols and not c.endswith("_z")]
        
        df = self.z_calculator.compute_z_scores(
            df=df,
            feature_columns=feature_cols,
            output_suffix="_z"
        )
        
        logger.info(f"Z-scores computed for {len(feature_cols)} features")
        
        # STEP 4: Apply time decay (if enabled)
        if self.enable_time_decay and "timestamp" in df.columns:
            z_score_cols = [f"{c}_z" for c in feature_cols]
            df = self.z_calculator.apply_time_decay(
                df=df,
                z_score_columns=z_score_cols,
                timestamp_column="timestamp",
                half_life_days=self.time_decay_half_life
            )
        
        # STEP 5: Compute composite scores
        # Build mapping: feature_name -> z_score_column
        feature_z_mapping = {c: f"{c}_z" for c in feature_cols}
        
        df = self.composite_scorer.compute_composite_scores(
            df=df,
            profile=profile,
            feature_z_mapping=feature_z_mapping
        )
        
        valid_scores = df["composite_score"].notna().sum()
        logger.info(f"Composite scores: {valid_scores}/{len(df)} entities scored")
        
        # STEP 6: Apply risk adjustment (if specified)
        if risk_tolerance:
            df = self.composite_scorer.apply_risk_adjustment(
                df=df,
                risk_tolerance=risk_tolerance
            )
            logger.info(f"Risk adjustment applied: tolerance={risk_tolerance}")
        
        # STEP 7: Rank entities
        ranked_df = self.ranker.rank_entities(
            df=df,
            score_column="composite_score",
            entity_id_column="entity_id",
            top_k=top_k
        )
        
        # STEP 8: Prepare results
        statistics = self.ranker.get_bucket_statistics(ranked_df)
        
        result = {
            "ranked_entities": ranked_df,
            "metadata": {
                "domain": self.metadata.get("domain"),
                "profile": profile,
                "stratification_mode": self.stratification_mode,
                "time_decay_enabled": self.enable_time_decay,
                "risk_tolerance": risk_tolerance,
                "total_entities_scored": valid_scores,
                "top_k": top_k if top_k else len(ranked_df)
            },
            "statistics": statistics,
            "diagnostics": {
                "universe_count": len(universe_df),
                "features_extracted": len(feature_cols),
                "valid_scores": valid_scores,
                "ranked_count": len(ranked_df)
            }
        }
        
        logger.info(f"NeuralEngine.run completed: {len(ranked_df)} entities ranked")
        
        return result
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Returns empty result structure with diagnostic message."""
        return {
            "ranked_entities": pd.DataFrame(),
            "metadata": {
                "domain": self.metadata.get("domain"),
                "error": reason
            },
            "statistics": {},
            "diagnostics": {
                "reason": reason
            }
        }
    
    def get_available_profiles(self) -> List[str]:
        """Returns list of available scoring profiles."""
        return self.scoring_strategy.get_available_profiles()
    
    def get_profile_metadata(self, profile: str) -> Dict[str, Any]:
        """Returns metadata for a specific profile."""
        return self.scoring_strategy.get_profile_metadata(profile)
    
    def get_domain_metadata(self) -> Dict[str, Any]:
        """Returns metadata about the data provider domain."""
        return self.metadata


class NeuralEngineError(Exception):
    """Base exception for Neural Engine errors"""
    pass
