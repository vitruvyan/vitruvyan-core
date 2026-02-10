"""
Babel Gardens - Domain Entities
================================

Immutable domain objects for Babel Gardens.
Pure data structures - no I/O, no side effects.

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class ProcessingStatus(str, Enum):
    """Status of processing request."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EmotionLabel(str, Enum):
    """Emotion classification labels."""
    
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class EmbeddingVector:
    """An embedding vector with metadata."""
    
    vector: tuple  # Immutable tuple of floats
    dimension: int
    model: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_list(self) -> List[float]:
        """Convert to list for JSON serialization."""
        return list(self.vector)
    
    @classmethod
    def from_list(cls, vector: List[float], model: str = "unknown") -> "EmbeddingVector":
        """Create from list of floats."""
        return cls(
            vector=tuple(vector),
            dimension=len(vector),
            model=model,
        )


@dataclass(frozen=True)
class EmbeddingRequest:
    """Request to generate embedding."""
    
    text: str
    language: str = "auto"
    model_type: str = "multilingual"
    use_cache: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "language": self.language,
            "model_type": self.model_type,
            "use_cache": self.use_cache,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EmbeddingResult:
    """Result of embedding generation."""
    
    embedding: EmbeddingVector
    text: str
    language_detected: str
    status: ProcessingStatus
    processing_time_ms: float = 0.0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "embedding": self.embedding.to_list(),
            "dimension": self.embedding.dimension,
            "model": self.embedding.model,
            "text": self.text,
            "language_detected": self.language_detected,
            "status": self.status.value,
            "processing_time_ms": self.processing_time_ms,
            "cached": self.cached,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SentimentScore:
    """Sentiment analysis score."""
    
    label: SentimentLabel
    score: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "label": self.label.value,
            "score": self.score,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class SentimentResult:
    """Result of sentiment analysis."""
    
    sentiment: SentimentScore
    text: str
    language_detected: str
    status: ProcessingStatus
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sentiment": self.sentiment.to_dict(),
            "text": self.text,
            "language_detected": self.language_detected,
            "status": self.status.value,
            "processing_time_ms": self.processing_time_ms,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EmotionScore:
    """Emotion detection score."""
    
    label: EmotionLabel
    score: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "label": self.label.value,
            "score": self.score,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class EmotionResult:
    """Result of emotion detection."""
    
    primary_emotion: EmotionScore
    all_emotions: List[EmotionScore]
    text: str
    language_detected: str
    status: ProcessingStatus
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary_emotion": self.primary_emotion.to_dict(),
            "all_emotions": [e.to_dict() for e in self.all_emotions],
            "text": self.text,
            "language_detected": self.language_detected,
            "status": self.status.value,
            "processing_time_ms": self.processing_time_ms,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LanguageDetection:
    """Language detection result."""
    
    language: str
    confidence: float
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language,
            "confidence": self.confidence,
            "alternatives": list(self.alternatives),
        }


@dataclass(frozen=True)
class TopicMatch:
    """A matched topic from classification."""
    
    topic_id: str
    topic_name: str
    score: float
    keywords_matched: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "score": self.score,
            "keywords_matched": list(self.keywords_matched),
        }


@dataclass(frozen=True)
class TopicClassificationResult:
    """Result of topic classification."""
    
    topics: List[TopicMatch]
    text: str
    status: ProcessingStatus
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topics": [t.to_dict() for t in self.topics],
            "text": self.text,
            "status": self.status.value,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass(frozen=True)
class SynthesisRequest:
    """Request for linguistic synthesis."""
    
    semantic_vector: List[float]
    sentiment_vector: List[float]
    method: str = "semantic_garden_fusion"
    weights: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "semantic_vector": self.semantic_vector,
            "sentiment_vector": self.sentiment_vector,
            "method": self.method,
            "weights": self.weights,
        }


@dataclass(frozen=True)
class SynthesisResult:
    """Result of linguistic synthesis."""
    
    unified_vector: List[float]
    method: str
    input_dimensions: Dict[str, int]
    output_dimension: int
    status: ProcessingStatus
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "unified_vector": self.unified_vector,
            "method": self.method,
            "input_dimensions": self.input_dimensions,
            "output_dimension": self.output_dimension,
            "status": self.status.value,
            "processing_time_ms": self.processing_time_ms,
        }
