"""
Babel Gardens - Linguistic Synthesis Consumer
==============================================

Pure linguistic synthesis logic.
Fuses semantic and sentiment embeddings into unified vectors.

NO I/O - pure numpy operations only.

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026)
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    BabelConfig,
    ProcessingStatus,
    SynthesisRequest,
    SynthesisResult,
)

logger = logging.getLogger(__name__)


class SynthesisConsumer(BaseConsumer):
    """
    Linguistic synthesis consumer.
    
    Fuses semantic and sentiment embeddings using various methods.
    All operations are pure numpy - no I/O.
    """
    
    SYNTHESIS_METHODS = [
        "concatenation",
        "weighted_average",
        "attention_fusion",
        "semantic_garden_fusion",
    ]
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process synthesis request.
        
        Expected input:
            semantic_vector: List[float] - Semantic embedding
            sentiment_vector: List[float] - Sentiment embedding
            method: str - Synthesis method (optional, default: semantic_garden_fusion)
            weights: Dict[str, float] - Custom weights (optional)
            
        Returns:
            ProcessResult with unified_vector in data
        """
        start_time = datetime.utcnow()
        
        # Validate input
        errors = self.validate_input(data, ["semantic_vector", "sentiment_vector"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        semantic = data["semantic_vector"]
        sentiment = data["sentiment_vector"]
        method = data.get("method", "semantic_garden_fusion")
        weights = data.get("weights", self.config.divine_weights)
        
        # Validate vectors
        if not semantic or not sentiment:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=["Empty vectors provided"],
            )
        
        # Validate method
        if method not in self.SYNTHESIS_METHODS:
            logger.warning(f"Unknown method {method}, using semantic_garden_fusion")
            method = "semantic_garden_fusion"
        
        try:
            # Convert to numpy arrays
            semantic_arr = np.array(semantic, dtype=np.float32)
            sentiment_arr = np.array(sentiment, dtype=np.float32)
            
            # Apply synthesis
            if method == "concatenation":
                unified = self._concatenation(semantic_arr, sentiment_arr)
            elif method == "weighted_average":
                unified = self._weighted_average(semantic_arr, sentiment_arr, weights)
            elif method == "attention_fusion":
                unified = self._attention_fusion(semantic_arr, sentiment_arr)
            else:  # semantic_garden_fusion (default)
                unified = self._semantic_garden_fusion(semantic_arr, sentiment_arr, weights)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._record_success()
            
            return ProcessResult(
                success=True,
                data={
                    "unified_vector": unified.tolist(),
                    "method": method,
                    "input_dimensions": {
                        "semantic": len(semantic),
                        "sentiment": len(sentiment),
                    },
                    "output_dimension": len(unified),
                    "status": ProcessingStatus.COMPLETED.value,
                },
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Synthesis error: {str(e)}"],
            )
    
    def _concatenation(
        self,
        semantic: np.ndarray,
        sentiment: np.ndarray,
    ) -> np.ndarray:
        """Simple concatenation of vectors."""
        return np.concatenate([semantic, sentiment])
    
    def _weighted_average(
        self,
        semantic: np.ndarray,
        sentiment: np.ndarray,
        weights: Dict[str, float],
    ) -> np.ndarray:
        """
        Weighted average of vectors.
        Requires same dimensions.
        """
        w_sem = weights.get("semantic", 0.7)
        w_sent = weights.get("sentiment", 0.3)
        
        # Handle dimension mismatch
        if len(semantic) != len(sentiment):
            max_len = max(len(semantic), len(sentiment))
            semantic = self._pad_vector(semantic, max_len)
            sentiment = self._pad_vector(sentiment, max_len)
        
        return w_sem * semantic + w_sent * sentiment
    
    def _attention_fusion(
        self,
        semantic: np.ndarray,
        sentiment: np.ndarray,
    ) -> np.ndarray:
        """
        Attention-based fusion.
        Uses sentiment to weight semantic dimensions.
        """
        # Handle dimension mismatch
        if len(semantic) != len(sentiment):
            max_len = max(len(semantic), len(sentiment))
            semantic = self._pad_vector(semantic, max_len)
            sentiment = self._pad_vector(sentiment, max_len)
        
        # Compute attention weights from sentiment
        attention = self._softmax(sentiment)
        
        # Apply attention to semantic
        attended = semantic * attention
        
        # Concatenate with original for richer representation
        return np.concatenate([attended, semantic])
    
    def _semantic_garden_fusion(
        self,
        semantic: np.ndarray,
        sentiment: np.ndarray,
        weights: Dict[str, float],
    ) -> np.ndarray:
        """
        Sacred semantic garden fusion.
        Combines weighted average with attention mechanism.
        """
        w_sem = weights.get("semantic", 0.7)
        w_sent = weights.get("sentiment", 0.3)
        
        # Handle dimension mismatch
        if len(semantic) != len(sentiment):
            max_len = max(len(semantic), len(sentiment))
            semantic_padded = self._pad_vector(semantic, max_len)
            sentiment_padded = self._pad_vector(sentiment, max_len)
        else:
            semantic_padded = semantic
            sentiment_padded = sentiment
        
        # Weighted fusion
        fused = w_sem * semantic_padded + w_sent * sentiment_padded
        
        # L2 normalize for consistent magnitude
        fused = self._l2_normalize(fused)
        
        # Concatenate with original semantic for full context
        return np.concatenate([fused, semantic])
    
    def _pad_vector(self, vector: np.ndarray, target_len: int) -> np.ndarray:
        """Pad vector to target length with zeros."""
        if len(vector) >= target_len:
            return vector[:target_len]
        return np.pad(vector, (0, target_len - len(vector)), mode="constant")
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax of vector."""
        exp_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
        return exp_x / exp_x.sum()
    
    def _l2_normalize(self, x: np.ndarray) -> np.ndarray:
        """L2 normalize vector."""
        norm = np.linalg.norm(x)
        if norm > 0:
            return x / norm
        return x
