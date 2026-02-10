"""
Codex Hunters - Restorer Consumer
=================================

Pure data normalization and validation logic.
NO I/O - transforms DiscoveredEntity into RestoredEntity.

The Restorer:
- Normalizes raw data structures
- Validates data quality
- Handles missing/malformed fields
- Computes quality scores

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    CodexConfig,
    DiscoveredEntity,
    RestoredEntity,
    EntityStatus,
)

logger = logging.getLogger(__name__)


class RestorerConsumer(BaseConsumer):
    """
    Normalization consumer for Codex Hunters.
    
    Responsibilities:
    - Transform raw discovered data into normalized format
    - Validate data quality and completeness
    - Handle missing/null values
    - Compute quality scores
    
    NOT responsible for (handled by LIVELLO 2):
    - Database lookups for reference data
    - External validation services
    """
    
    def __init__(self, config: CodexConfig = None, normalizers: Dict[str, Callable] = None):
        """
        Initialize restorer with optional custom normalizers.
        
        Args:
            config: Domain configuration
            normalizers: Dict of source_name -> normalizer_function
                        Each normalizer: (raw_data: Dict) -> Dict
        """
        super().__init__(config)
        self._normalizers = normalizers or {}
    
    def register_normalizer(self, source: str, normalizer: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Register a normalizer function for a specific source.
        
        Args:
            source: Source name
            normalizer: Function that takes raw_data and returns normalized_data
        """
        self._normalizers[source] = normalizer
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process a discovered entity for restoration.
        
        Expected input:
            entity: DiscoveredEntity (or dict representation)
            
        Returns:
            ProcessResult with RestoredEntity in data["entity"]
        """
        start_time = datetime.utcnow()
        
        # Validate input
        if "entity" not in data:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=["Missing 'entity' in input"])
        
        entity_data = data["entity"]
        
        # Handle both DiscoveredEntity and dict
        if isinstance(entity_data, DiscoveredEntity):
            entity_id = entity_data.entity_id
            source = entity_data.source
            raw_data = entity_data.raw_data
        elif isinstance(entity_data, dict):
            entity_id = entity_data.get("entity_id")
            source = entity_data.get("source")
            raw_data = entity_data.get("raw_data", {})
        else:
            self._record_error()
            return ProcessResult(
                success=False, 
                data={}, 
                errors=[f"Invalid entity type: {type(entity_data)}"]
            )
        
        if not entity_id or not source:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=["Entity must have entity_id and source"]
            )
        
        try:
            # Normalize data
            normalized_data, validation_errors = self._normalize(source, raw_data)
            
            # Compute quality score
            quality_score = self._compute_quality_score(normalized_data, validation_errors)
            
            # Create restored entity
            restored = RestoredEntity(
                entity_id=entity_id,
                source=source,
                restored_at=datetime.utcnow(),
                normalized_data=normalized_data,
                quality_score=quality_score,
                validation_errors=validation_errors,
                status=EntityStatus.RESTORED if quality_score > 0.5 else EntityStatus.INVALID
            )
            
            self._record_success()
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ProcessResult(
                success=True,
                data={"entity": restored},
                errors=validation_errors if validation_errors else None,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Restoration failed: {str(e)}"]
            )
    
    def _normalize(self, source: str, raw_data: Dict[str, Any]) -> tuple:
        """
        Normalize raw data using registered normalizer or default.
        
        Returns:
            (normalized_data, validation_errors)
        """
        validation_errors = []
        
        if source in self._normalizers:
            # Use registered normalizer
            try:
                normalized = self._normalizers[source](raw_data)
            except Exception as e:
                validation_errors.append(f"Normalizer error: {str(e)}")
                normalized = self._default_normalize(raw_data)
        else:
            # Use default normalization
            normalized = self._default_normalize(raw_data)
        
        # Validate normalized data
        validation_errors.extend(self._validate_normalized(normalized))
        
        return normalized, validation_errors
    
    def _default_normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default normalization: clean keys, handle nulls.
        
        Domain-specific normalizers should override this.
        """
        if not raw_data:
            return {}
        
        normalized = {}
        for key, value in raw_data.items():
            # Clean key: lowercase, replace spaces with underscores
            clean_key = key.lower().replace(" ", "_").replace("-", "_")
            
            # Handle null/empty values
            if value is None:
                normalized[clean_key] = None
            elif isinstance(value, str) and value.strip() == "":
                normalized[clean_key] = None
            elif isinstance(value, dict):
                normalized[clean_key] = self._default_normalize(value)
            elif isinstance(value, list):
                normalized[clean_key] = [
                    self._default_normalize(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[clean_key] = value
        
        # Add metadata
        normalized["_normalized_at"] = datetime.utcnow().isoformat()
        
        return normalized
    
    def _validate_normalized(self, data: Dict[str, Any]) -> List[str]:
        """Validate normalized data structure."""
        errors = []
        
        if not data:
            errors.append("Normalized data is empty")
        
        # Count null fields
        null_count = sum(1 for v in data.values() if v is None)
        total_fields = len(data)
        if total_fields > 0 and null_count / total_fields > 0.5:
            errors.append(f"High null ratio: {null_count}/{total_fields} fields are null")
        
        return errors
    
    def _compute_quality_score(
        self,
        normalized_data: Dict[str, Any],
        validation_errors: List[str]
    ) -> float:
        """
        Compute quality score for restored data.
        
        Score from 0.0 (invalid) to 1.0 (perfect).
        """
        if not normalized_data:
            return 0.0
        
        score = 1.0
        
        # Deduct for validation errors
        score -= len(validation_errors) * 0.1
        
        # Deduct for null fields
        null_ratio = sum(1 for v in normalized_data.values() if v is None) / max(1, len(normalized_data))
        score -= null_ratio * 0.3
        
        return max(0.0, min(1.0, score))
