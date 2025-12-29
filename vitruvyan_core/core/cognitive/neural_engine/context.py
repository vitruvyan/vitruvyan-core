"""
Evaluation context for the Neural Engine Core.

Defines the input parameters for factor evaluation.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any


@dataclass
class EvaluationContext:
    """
    Context for a factor evaluation request.
    
    Encapsulates all parameters needed to evaluate entities against
    a scoring profile.
    """
    
    entity_ids: List[str]
    """List of entity identifiers to evaluate"""
    
    profile_name: str
    """Name of the aggregation profile to use"""
    
    normalizer_name: str = "zscore"
    """Name of the normalization strategy (default: zscore)"""
    
    mode: str = "evaluate"
    """Evaluation mode: 'evaluate', 'rank', 'compare'"""
    
    options: Dict[str, Any] = field(default_factory=dict)
    """Additional options for factors or normalizers"""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this evaluation request"""
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp when evaluation was requested"""
