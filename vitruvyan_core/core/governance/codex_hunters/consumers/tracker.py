"""
Codex Hunters - Tracker Consumer
================================

Pure data discovery and validation logic.
NO I/O - actual data fetching is done by adapters in LIVELLO 2.

The Tracker:
- Validates discovery requests
- Prepares discovery configurations
- Processes raw fetched data into DiscoveredEntity objects

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    CodexConfig,
    DiscoveredEntity,
    EntityStatus,
    CodexEvent,
)

logger = logging.getLogger(__name__)


class TrackerConsumer(BaseConsumer):
    """
    Discovery consumer for Codex Hunters.
    
    Responsibilities:
    - Validate entity IDs and discovery parameters
    - Prepare source-specific discovery configurations
    - Transform raw source data into DiscoveredEntity objects
    - Generate dedupe keys for duplicate detection
    
    NOT responsible for (handled by LIVELLO 2):
    - Actual network requests to data sources
    - Rate limiting (configured but not enforced here)
    - Caching
    """
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process a discovery request.
        
        Expected input:
            entity_id: str - Entity identifier
            source: str - Source name (must be in config.sources)
            raw_data: dict - Raw data from source (provided by adapter)
            
        Returns:
            ProcessResult with DiscoveredEntity in data["entity"]
        """
        start_time = datetime.utcnow()
        
        # Validate input
        errors = self.validate_input(data, ["entity_id", "source"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        entity_id = data["entity_id"]
        source = data["source"]
        raw_data = data.get("raw_data", {})
        
        # Validate source is configured
        source_config = self.config.get_source(source)
        if source_config is None:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Unknown source: {source}. Available: {list(self.config.sources.keys())}"]
            )
        
        # Create discovered entity
        try:
            discovered = self._create_discovered_entity(entity_id, source, raw_data)
            self._record_success()
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ProcessResult(
                success=True,
                data={
                    "entity": discovered,
                    "dedupe_key": self._generate_dedupe_key(entity_id, source),
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Discovery failed: {str(e)}"]
            )
    
    def prepare_discovery_config(self, entity_ids: List[str], sources: List[str]) -> Dict[str, Any]:
        """
        Prepare configuration for discovery operation.
        
        Returns dict with validated sources and rate limit info.
        Called by adapter before starting discovery.
        """
        validated_sources = []
        warnings = []
        
        for source in sources:
            source_config = self.config.get_source(source)
            if source_config is None:
                warnings.append(f"Unknown source '{source}' - skipping")
            elif not source_config.enabled:
                warnings.append(f"Source '{source}' is disabled - skipping")
            else:
                validated_sources.append({
                    "name": source,
                    "rate_limit": source_config.rate_limit_per_minute,
                    "timeout": source_config.timeout_seconds,
                    "retries": source_config.retry_attempts,
                })
        
        return {
            "entity_ids": entity_ids,
            "sources": validated_sources,
            "batch_size": self.config.default_batch_size,
            "warnings": warnings,
        }
    
    def _create_discovered_entity(
        self,
        entity_id: str,
        source: str,
        raw_data: Dict[str, Any]
    ) -> DiscoveredEntity:
        """Create DiscoveredEntity from raw data."""
        return DiscoveredEntity(
            entity_id=entity_id,
            source=source,
            discovered_at=datetime.utcnow(),
            raw_data=raw_data,
            metadata={
                "record_count": len(raw_data) if isinstance(raw_data, dict) else 0,
                "has_data": bool(raw_data),
            },
            status=EntityStatus.DISCOVERED
        )
    
    def _generate_dedupe_key(self, entity_id: str, source: str) -> str:
        """Generate deduplication key for entity."""
        key_data = f"{entity_id}:{source}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def validate_entity_id(self, entity_id: str) -> List[str]:
        """
        Validate entity ID format.
        
        Override in domain-specific implementations for stricter validation.
        Default accepts any non-empty string.
        """
        errors = []
        if not entity_id:
            errors.append("Entity ID cannot be empty")
        if len(entity_id) > 256:
            errors.append("Entity ID too long (max 256 characters)")
        return errors
