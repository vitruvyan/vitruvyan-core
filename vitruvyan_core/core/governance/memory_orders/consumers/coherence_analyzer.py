"""
Memory Orders — Coherence Analyzer

Pure drift calculation between PostgreSQL (Archivarium) and Qdrant (Mnemosyne).
Pure calculation logic, NO I/O.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — consumers)
"""

from datetime import datetime
from .base import MemoryRole
from ..domain import (
    CoherenceInput,
    CoherenceReport,
)


class CoherenceAnalyzer(MemoryRole):
    """
    Pure coherence analysis: calculate drift and determine status.
    
    Algorithm:
    1. Calculate absolute drift: |pg_count - qdrant_count|
    2. Calculate drift percentage: (absolute_drift / max(pg, qdrant)) * 100
    3. Map drift to status using thresholds:
       - < healthy_threshold → 'healthy'
       - >= healthy_threshold AND < warning_threshold → 'warning'
       - >= warning_threshold → 'critical'
    4. Generate recommendation based on status
    
    NO I/O. NO database queries. NO HTTP calls.
    """
    
    def process(self, payload: CoherenceInput) -> CoherenceReport:
        """
        Analyze coherence between two memory systems.
        
        Args:
            payload: CoherenceInput with counts and thresholds
        
        Returns:
            CoherenceReport with status, drift metrics, and recommendation
        
        Raises:
            ValueError: If payload is not a CoherenceInput
        """
        if not isinstance(payload, CoherenceInput):
            raise ValueError(f"Expected CoherenceInput, got {type(payload)}")
        
        # Extract thresholds from immutable tuple
        thresholds_dict = dict(payload.thresholds)
        healthy_threshold = thresholds_dict.get("healthy", 5.0)
        warning_threshold = thresholds_dict.get("warning", 15.0)
        
        # Calculate drift (pure math)
        drift_absolute = abs(payload.pg_count - payload.qdrant_count)
        max_count = max(payload.pg_count, payload.qdrant_count)
        
        # Edge case: both systems empty
        if max_count == 0:
            drift_percentage = 0.0
        else:
            drift_percentage = (drift_absolute / max_count) * 100.0
        
        # Determine status based on drift
        if drift_percentage < healthy_threshold:
            status = "healthy"
            recommendation = "No action required. Coherence is within healthy range."
        elif drift_percentage < warning_threshold:
            status = "warning"
            recommendation = f"Schedule synchronization. Drift is {drift_percentage:.2f}%, approaching warning threshold."
        else:
            status = "critical"
            recommendation = f"IMMEDIATE synchronization required. Drift is {drift_percentage:.2f}%, exceeds warning threshold."
        
        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Return frozen report
        return CoherenceReport(
            status=status,
            drift_percentage=drift_percentage,
            recommendation=recommendation,
            pg_count=payload.pg_count,
            qdrant_count=payload.qdrant_count,
            drift_absolute=drift_absolute,
            timestamp=timestamp,
            table=payload.table,
            collection=payload.collection,
        )
    
    def can_handle(self, payload: CoherenceInput) -> bool:
        """Check if payload is valid CoherenceInput."""
        return isinstance(payload, CoherenceInput)
