"""
Codex Hunters - Binder Consumer
===============================

Pure binding logic for permanent storage.
NO I/O - prepares data for persistence by adapters in LIVELLO 2.

The Binder:
- Prepares entities for storage
- Generates storage references
- Creates embedding payloads
- Handles deduplication logic

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    CodexConfig,
    RestoredEntity,
    BoundEntity,
    EntityStatus,
)

logger = logging.getLogger(__name__)


class BinderConsumer(BaseConsumer):
    """
    Binding consumer for Codex Hunters.
    
    Responsibilities:
    - Prepare restored entities for permanent storage
    - Generate storage-ready payloads for PostgreSQL
    - Generate embedding payloads for Qdrant
    - Create deduplication keys
    - Track binding metadata
    
    NOT responsible for (handled by LIVELLO 2):
    - Actual database writes (PostgresAgent)
    - Actual vector writes (QdrantAgent)
    - Embedding generation (embedding model in adapter)
    """
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process a restored entity for binding.
        
        Expected input:
            entity: RestoredEntity (or dict representation)
            embedding: List[float] (optional, from adapter)
            
        Returns:
            ProcessResult with domain-agnostic BoundEntity.
            Adapter layer (LIVELLO 2) constructs provider-specific payloads.
        """
        start_time = datetime.utcnow()
        
        # Validate input
        if "entity" not in data:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=["Missing 'entity' in input"])
        
        entity_data = data["entity"]
        embedding = data.get("embedding")
        
        # Handle both RestoredEntity and dict
        if isinstance(entity_data, RestoredEntity):
            entity_id = entity_data.entity_id
            source = entity_data.source
            normalized_data = entity_data.normalized_data
            quality_score = entity_data.quality_score
        elif isinstance(entity_data, dict):
            entity_id = entity_data.get("entity_id")
            source = entity_data.get("source")
            normalized_data = entity_data.get("normalized_data", {})
            quality_score = entity_data.get("quality_score", 1.0)
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
            # Generate dedupe key (deterministic hash)
            dedupe_key = self._generate_dedupe_key(entity_id, source, normalized_data)
            
            # Generate embedding ID if embedding provided
            embedding_id = None
            if embedding:
                embedding_id = self._generate_embedding_id(entity_id, source)
            
            # Create domain-agnostic BoundEntity
            bound = BoundEntity(
                entity_id=entity_id,
                source=source,
                bound_at=datetime.utcnow(),
                storage_refs={
                    "relational": self.config.entity_table.name,
                    "vector": self.config.embedding_collection.name if embedding_id else None,
                },
                embedding_id=embedding_id,
                dedupe_key=dedupe_key,
                status=EntityStatus.BOUND
            )
            
            self._record_success()
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Return domain-agnostic entity + data
            # LIVELLO 2 adapter constructs provider-specific payloads
            return ProcessResult(
                success=True,
                data={
                    "bound_entity": bound,
                    "normalized_data": normalized_data,
                    "embedding": embedding,
                    "quality_score": quality_score,
                    "dedupe_key": dedupe_key,
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Binding failed: {str(e)}"]
            )
    
    def _generate_dedupe_key(
        self,
        entity_id: str,
        source: str,
        data: Dict[str, Any]
    ) -> str:
        """Generate deduplication key from entity data."""
        # Create deterministic key from entity + source + data hash
        data_str = json.dumps(data, sort_keys=True, default=str)
        content = f"{entity_id}:{source}:{data_str}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _generate_embedding_id(self, entity_id: str, source: str) -> str:
        """Generate unique ID for embedding."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        content = f"{entity_id}:{source}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _prepare_postgres_payload(
        self,
        entity_id: str,
        source: str,
        normalized_data: Dict[str, Any],
        quality_score: float,
        dedupe_key: str
    ) -> Dict[str, Any]:
        """
        Prepare payload for PostgreSQL insert.
        
        Schema-agnostic: stores normalized_data as JSONB.
        Domain-specific tables can have additional columns.
        """
        return {
            "entity_id": entity_id,
            "source": source,
            "data": normalized_data,  # JSONB column
            "quality_score": quality_score,
            "dedupe_key": dedupe_key,
            "bound_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def _prepare_qdrant_payload(
        self,
        embedding_id: str,
        entity_id: str,
        source: str,
        normalized_data: Dict[str, Any],
        embedding: List[float]
    ) -> Dict[str, Any]:
        """
        Prepare payload for Qdrant upsert.
        
        Returns dict with:
        - id: Unique point ID
        - vector: Embedding vector
        - payload: Metadata for filtering
        """
        return {
            "id": embedding_id,
            "vector": embedding,
            "payload": {
                "entity_id": entity_id,
                "source": source,
                "bound_at": datetime.utcnow().isoformat(),
                # Include searchable fields from normalized data
                **self._extract_searchable_fields(normalized_data)
            }
        }
    
    def _extract_searchable_fields(self, data: Dict[str, Any], max_fields: int = 10) -> Dict[str, Any]:
        """
        Extract searchable fields from normalized data.
        
        Only includes primitive types (str, int, float, bool).
        """
        searchable = {}
        count = 0
        
        for key, value in data.items():
            if count >= max_fields:
                break
            if key.startswith("_"):  # Skip internal fields
                continue
            if isinstance(value, (str, int, float, bool)) and value is not None:
                searchable[key] = value
                count += 1
        
        return searchable
    
    def prepare_batch(self, entities: List[Dict[str, Any]]) -> ProcessResult:
        """
        Prepare a batch of entities for binding.
        
        Returns aggregated payloads for batch insert.
        """
        postgres_batch = []
        qdrant_batch = []
        bound_entities = []
        errors = []
        
        for entity_data in entities:
            result = self.process(entity_data)
            if result.success:
                postgres_batch.append(result.data["postgres_payload"])
                if result.data.get("qdrant_payload"):
                    qdrant_batch.append(result.data["qdrant_payload"])
                bound_entities.append(result.data["bound_entity"])
            else:
                errors.extend(result.errors)
        
        return ProcessResult(
            success=len(errors) == 0,
            data={
                "postgres_batch": postgres_batch,
                "qdrant_batch": qdrant_batch,
                "bound_entities": bound_entities,
                "batch_size": len(entities),
                "success_count": len(bound_entities),
                "error_count": len(errors),
            },
            errors=errors if errors else None
        )
