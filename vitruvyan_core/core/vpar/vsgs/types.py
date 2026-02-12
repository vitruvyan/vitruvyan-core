"""
VSGS Types — Domain-agnostic data structures for semantic grounding.

All types are plain Python dataclasses. No infrastructure dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class GroundingConfig:
    """Configuration for VSGS semantic grounding.

    Thresholds define match quality classification:
      score > high_threshold  → "high"
      score > medium_threshold → "medium"
      else                     → "low"
    """
    enabled: bool = False
    top_k: int = 3
    collection: str = "semantic_states"
    high_threshold: float = 0.8
    medium_threshold: float = 0.6
    prompt_budget_chars: int = 800
    embedding_timeout: float = 3.0
    search_timeout: float = 5.0


@dataclass
class SemanticMatch:
    """A single semantic match from Qdrant vector search."""
    text: str
    score: float
    quality: str              # "high", "medium", "low"
    intent: Optional[str] = None
    language: Optional[str] = None
    timestamp: Optional[str] = None
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for state/API compatibility."""
        return {
            "text": self.text,
            "score": self.score,
            "quality": self.quality,
            "intent": self.intent,
            "language": self.language,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
        }


@dataclass
class GroundingResult:
    """Result of a semantic grounding operation."""
    matches: List[SemanticMatch]
    status: str               # "enabled", "disabled", "error", "skipped"
    elapsed_ms: float = 0.0
    error: Optional[str] = None

    @property
    def top_score(self) -> float:
        return self.matches[0].score if self.matches else 0.0

    @property
    def match_count(self) -> int:
        return len(self.matches)

    def to_state_dict(self) -> Dict[str, Any]:
        """Convert to LangGraph state fields."""
        return {
            "semantic_matches": [m.to_dict() for m in self.matches],
            "vsgs_status": self.status,
            "vsgs_elapsed_ms": self.elapsed_ms,
            **({"vsgs_error": self.error} if self.error else {}),
        }
