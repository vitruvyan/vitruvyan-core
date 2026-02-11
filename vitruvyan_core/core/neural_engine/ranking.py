"""
Ranking Engine
==============

Domain-agnostic entity ranking and bucketing.

Ranks entities by composite score with support for:
- Top-K selection
- Percentile bucketing
- Multi-tier ranking (top/middle/bottom)

Author: vitruvyan-core
Date: February 8, 2026
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Domain-agnostic ranking engine.
    
    Features:
    - Rank by composite score (descending)
    - Top-K selection
    - Percentile calculation
    - Bucket classification (top/middle/bottom) with configurable thresholds
    """
    
    def __init__(
        self,
        bucket_top_threshold: float = 70.0,
        bucket_bottom_threshold: float = 30.0
    ):
        """
        Initialize Ranking Engine.
        
        Args:
            bucket_top_threshold: Percentile threshold for 'top' bucket (default: 70.0)
            bucket_bottom_threshold: Percentile threshold for 'bottom' bucket (default: 30.0)
        """
        if not 0 <= bucket_bottom_threshold < bucket_top_threshold <= 100:
            raise ValueError(
                f"Invalid bucket thresholds: bottom={bucket_bottom_threshold}, top={bucket_top_threshold}. "
                f"Must satisfy 0 <= bottom < top <= 100."
            )
        self.bucket_top_threshold = bucket_top_threshold
        self.bucket_bottom_threshold = bucket_bottom_threshold
    
    def rank_entities(
        self,
        df: pd.DataFrame,
        score_column: str = "composite_score",
        entity_id_column: str = "entity_id",
        top_k: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Ranks entities by score and returns top-K.
        
        Args:
            df: DataFrame with score column
            score_column: Column to rank by (default: "composite_score")
            entity_id_column: Entity identifier column
            top_k: Number of top entities to return (None = all)
        
        Returns:
            DataFrame sorted by rank with additional columns:
              - rank: Rank position (1 = highest score)
              - percentile: Percentile (0-100, higher = better)
              - bucket: Classification (top/middle/bottom)
        """
        out = df.copy()
        
        # Filter entities with valid scores
        valid_mask = out[score_column].notna()
        valid_count = valid_mask.sum()
        
        if valid_count == 0:
            logger.warning("No entities with valid scores to rank")
            return pd.DataFrame()
        
        out = out[valid_mask].copy()
        
        # Sort by score (descending)
        out = out.sort_values(by=score_column, ascending=False).reset_index(drop=True)
        
        # Assign rank
        out["rank"] = range(1, len(out) + 1)
        
        # Calculate percentile (higher score = higher percentile)
        out["percentile"] = self._calculate_percentiles(out, score_column)
        
        # Assign bucket
        out["bucket"] = out["percentile"].apply(self._classify_bucket)
        
        # Top-K selection
        if top_k and top_k < len(out):
            out = out.head(top_k)
            logger.info(f"Top-{top_k} entities selected from {valid_count} total")
        else:
            logger.info(f"Ranked {len(out)} entities")
        
        return out
    
    def _calculate_percentiles(self, df: pd.DataFrame, score_column: str) -> pd.Series:
        """
        Calculates percentile for each entity.
        
        Percentile = (entities below / total entities) × 100
        
        Example:
            Rank 1 (highest score): percentile = 100
            Rank 50 (median): percentile = 50
            Rank 100 (lowest score): percentile = 0
        """
        n = len(df)
        ranks = df["rank"]
        
        # Percentile formula: (n - rank + 1) / n × 100
        percentiles = ((n - ranks + 1) / n * 100).round(1)
        
        return percentiles
    
    def _classify_bucket(self, percentile: float) -> str:
        """
        Classifies entity into bucket based on percentile.
        
        Buckets (configurable thresholds):
        - top: percentile >= bucket_top_threshold
        - middle: bucket_bottom_threshold <= percentile < bucket_top_threshold
        - bottom: percentile < bucket_bottom_threshold
        """
        if percentile >= self.bucket_top_threshold:
            return "top"
        elif percentile >= self.bucket_bottom_threshold:
            return "middle"
        else:
            return "bottom"
    
    def get_top_entities(
        self,
        df: pd.DataFrame,
        k: int,
        score_column: str = "composite_score"
    ) -> List[str]:
        """
        Returns list of top-K entity IDs.
        
        Args:
            df: Ranked DataFrame
            k: Number of top entities
            score_column: Score column name
        
        Returns:
            List of entity IDs (top-K by score)
        """
        ranked = self.rank_entities(df, score_column=score_column, top_k=k)
        
        if "entity_id" in ranked.columns:
            return ranked["entity_id"].tolist()
        else:
            return ranked.index.tolist()
    
    def get_bucket_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Returns statistics about bucket distribution.
        
        Args:
            df: Ranked DataFrame with bucket column
        
        Returns:
            Dict with keys:
              - total: Total entities ranked
              - top_count: Entities in top bucket
              - middle_count: Entities in middle bucket
              - bottom_count: Entities in bottom bucket
              - top_pct: Percentage in top bucket
        """
        if "bucket" not in df.columns:
            return {"error": "DataFrame missing 'bucket' column"}
        
        total = len(df)
        top_count = (df["bucket"] == "top").sum()
        middle_count = (df["bucket"] == "middle").sum()
        bottom_count = (df["bucket"] == "bottom").sum()
        
        return {
            "total": total,
            "top_count": int(top_count),
            "middle_count": int(middle_count),
            "bottom_count": int(bottom_count),
            "top_pct": round(top_count / total * 100, 1) if total > 0 else 0,
            "middle_pct": round(middle_count / total * 100, 1) if total > 0 else 0,
            "bottom_pct": round(bottom_count / total * 100, 1) if total > 0 else 0
        }


class RankingError(Exception):
    """Base exception for ranking errors"""
    pass
