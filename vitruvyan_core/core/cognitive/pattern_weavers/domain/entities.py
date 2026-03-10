"""
Pattern Weavers - Domain Entities
=================================

Immutable dataclasses for Pattern Weavers operations.
Pure Python - no I/O, no external dependencies.

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026 - Domain-Agnostic Refactoring)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WeaveStatus(str, Enum):
    """Status of a weave operation."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchType(str, Enum):
    """Type of pattern match."""
    EXACT = "exact"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    FUZZY = "fuzzy"


@dataclass(frozen=True)
class PatternMatch:
    """A single pattern match result."""
    
    category: str  # e.g., "concepts", "sectors", "regions"
    name: str  # e.g., "Technology"
    score: float  # Similarity score (0.0 to 1.0)
    match_type: MatchType = MatchType.SEMANTIC
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "name": self.name,
            "score": self.score,
            "match_type": self.match_type.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class WeaveRequest:
    """Request for a weave operation."""
    
    query_text: str
    user_id: str = "anonymous"
    language: str = "auto"
    top_k: int = 10
    similarity_threshold: float = 0.4
    categories: Optional[List[str]] = None  # Filter to specific categories
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_text": self.query_text,
            "user_id": self.user_id,
            "language": self.language,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "categories": self.categories,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
        }


@dataclass
class WeaveResult:
    """Result of a weave operation."""
    
    status: WeaveStatus
    matches: List[PatternMatch] = field(default_factory=list)
    extracted_concepts: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    processed_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def success(self) -> bool:
        """Check if operation was successful."""
        return self.status == WeaveStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "matches": [m.to_dict() for m in self.matches],
            "extracted_concepts": self.extracted_concepts,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "processed_at": self.processed_at.isoformat(),
        }


@dataclass(frozen=True)
class EmbeddingVector:
    """An embedding vector with metadata."""
    
    vector: List[float]
    text: str
    language: str = "auto"
    dimension: int = 768
    
    def validate(self) -> bool:
        """Validate embedding dimensions."""
        return len(self.vector) == self.dimension


@dataclass(frozen=True)
class TaxonomyEntry:
    """A single entry in the taxonomy (e.g., a concept to match)."""
    
    entry_id: str
    category: str
    name: str
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
