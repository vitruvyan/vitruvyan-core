"""
Evaluation orchestrator for the Neural Engine Core.

Coordinates factor computation, normalization, and aggregation.
"""

import time
from typing import List, Dict
import pandas as pd

from vitruvyan_core.core.cognitive.neural_engine.contracts import (
    AbstractFactor,
    NormalizerStrategy,
    AggregationProfile
)
from vitruvyan_core.core.cognitive.neural_engine.context import EvaluationContext
from vitruvyan_core.core.cognitive.neural_engine.result import (
    EvaluationResult,
    EntityEvaluation,
    FactorContribution
)


class EvaluationOrchestrator:
    """
    Orchestrates the evaluation pipeline.
    
    Coordinates:
    1. Factor computation (raw values)
    2. Normalization (raw → comparable scores)
    3. Aggregation (scores → composite)
    """
    
    def evaluate(
        self,
        entities: pd.DataFrame,
        context: EvaluationContext,
        factors: List[AbstractFactor],
        normalizer: NormalizerStrategy,
        profile: AggregationProfile
    ) -> EvaluationResult:
        """
        Execute complete evaluation pipeline.
        
        Args:
            entities: DataFrame with at least 'entity_id' column
            context: Evaluation context with parameters
            factors: List of factors to compute
            normalizer: Normalization strategy to apply
            profile: Aggregation profile for combining scores
        
        Returns:
            Complete evaluation result with scores and metadata
        
        Raises:
            ValueError: If entities DataFrame lacks 'entity_id' column
        """
        if 'entity_id' not in entities.columns:
            raise ValueError("entities DataFrame must have 'entity_id' column")
        
        start_time = time.time()
        
        # Step 1: Compute raw factor values
        raw_values: Dict[str, pd.Series] = {}
        stratification_groups: Dict[str, pd.Series] = {}
        
        for factor in factors:
            raw = factor.compute(entities, context)
            raw_values[factor.name] = raw
            
            # Capture stratification groups if needed
            if factor.requires_stratification and factor.stratification_field:
                if factor.stratification_field in entities.columns:
                    # Align with raw values index
                    groups = entities.set_index('entity_id')[factor.stratification_field]
                    stratification_groups[factor.name] = groups.reindex(raw.index)
        
        # Step 2: Normalize factor values
        normalized_values: Dict[str, pd.Series] = {}
        
        for factor in factors:
            raw = raw_values[factor.name]
            groups = stratification_groups.get(factor.name)
            
            normalized = normalizer.normalize(
                raw_values=raw,
                higher_is_better=factor.higher_is_better,
                stratification_groups=groups
            )
            normalized_values[factor.name] = normalized
        
        # Step 3: Get weights and aggregate
        factor_names = [f.name for f in factors]
        weights = profile.get_weights(factor_names)
        composite_scores = profile.aggregate(normalized_values)
        
        # Step 4: Rank entities
        ranked = composite_scores.sort_values(ascending=False)
        ranks = {entity_id: rank + 1 for rank, entity_id in enumerate(ranked.index)}
        
        # Step 5: Build result structure
        evaluations: List[EntityEvaluation] = []
        
        for entity_id in composite_scores.index:
            contributions: List[FactorContribution] = []
            
            for factor in factors:
                raw_val = raw_values[factor.name].get(entity_id)
                norm_val = normalized_values[factor.name].get(entity_id)
                weight = weights.get(factor.name, 0.0)
                
                contribution = weight * norm_val if norm_val is not None else 0.0
                
                contributions.append(FactorContribution(
                    factor_name=factor.name,
                    raw_value=raw_val,
                    normalized_value=norm_val,
                    weight=weight,
                    contribution=contribution
                ))
            
            evaluations.append(EntityEvaluation(
                entity_id=entity_id,
                composite_score=composite_scores[entity_id],
                rank=ranks.get(entity_id),
                factor_contributions=contributions
            ))
        
        duration_ms = (time.time() - start_time) * 1000
        
        return EvaluationResult(
            context=context,
            evaluations=evaluations,
            factors_used=factor_names,
            normalizer_used=normalizer.name,
            profile_used=profile.name,
            entity_count=len(evaluations),
            duration_ms=duration_ms
        )
