# api_gemma_cognitive/schemas/api_models.py
"""
🔗 Unified API Models for Gemma Cognitive Layer
Pydantic schemas for all 4 modules with shared base models
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# ===========================
# BASE MODELS
# ===========================

class LanguageCode(str, Enum):
    """Supported language codes"""
    AUTO = "auto"
    ENGLISH = "en" 
    ITALIAN = "it"
    SPANISH = "es"
    JAPANESE = "ja"
    ARABIC = "ar"
    CHINESE = "zh"
    KOREAN = "ko"
    HEBREW = "he"
    RUSSIAN = "ru"
    FRENCH = "fr"
    GERMAN = "de"
    LITHUANIAN = "lt"
    PORTUGUESE = "pt"  # Portuguese (Brazil/Portugal)
    HINDI = "hi"  # Hindi (India)
    SWAHILI = "sw"  # Swahili (East Africa)

class ModelType(str, Enum):
    """Model type categories"""
    FINANCIAL = "financial"
    GENERAL = "general"
    MULTILINGUAL = "multilingual"

class FusionMode(str, Enum):
    """Sentiment fusion modes"""
    BASIC = "basic"
    ENHANCED = "enhanced"  
    DEEP = "deep"

class Priority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ===========================
# MODULE 0: EMOTION DETECTOR MODELS (NEW - Phase 1)
# ===========================

class EmotionRequest(BaseModel):
    """Request for emotion detection with cultural awareness"""
    text: str = Field(..., description="Text to analyze for emotion", max_length=8192)
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code or auto-detect")
    fusion_mode: FusionMode = Field(default=FusionMode.ENHANCED, description="Sentiment fusion mode")
    use_cache: bool = Field(default=True, description="Whether to use Redis cache (24h TTL)")
    context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional conversation context for better emotion detection"
    )
    user_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user profile for personalized cultural context"
    )

class EmotionResponse(BaseModel):
    """Response with detected emotion and explainability"""
    status: str = Field(..., description="Response status: success or error")
    emotion: Dict[str, Any] = Field(
        ..., 
        description="Emotion data with primary, secondary, intensity (0-1), confidence (0-1)"
    )
    sentiment: Dict[str, Any] = Field(..., description="Underlying sentiment: label, score")
    cultural_context: str = Field(..., description="Cultural communication style applied")
    reasoning: str = Field(..., description="Explainability: why this emotion was detected")
    metadata: Dict[str, Any] = Field(
        ..., 
        description="Processing metadata: language, processing_time_ms, models_used, cached"
    )
    error: Optional[str] = Field(default=None, description="Error message if status=error")

# ===========================
# MODULE 1: EMBEDDING ENGINE MODELS
# ===========================

class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to embed", max_length=8192)
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code")
    model_type: ModelType = Field(default=ModelType.FINANCIAL, description="Model type")
    use_cache: bool = Field(default=True, description="Use vector cache")

class BatchEmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to embed", max_items=100)
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code")
    model_type: ModelType = Field(default=ModelType.FINANCIAL, description="Model type") 
    use_cache: bool = Field(default=True, description="Use vector cache")

class EmbeddingResponse(BaseModel):
    status: str
    embedding: List[float]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class BatchEmbeddingResponse(BaseModel):
    status: str
    embeddings: List[List[float]]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class SimilarityRequest(BaseModel):
    text1: str = Field(..., description="First text for comparison")
    text2: str = Field(..., description="Second text for comparison")
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code")

class SimilarityResponse(BaseModel):
    status: str
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
    metadata: Dict[str, Any]
    error: Optional[str] = None

# ===========================
# MODULE 2: SENTIMENT FUSION MODELS
# ===========================

class SentimentRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for sentiment", max_length=8192)
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code")
    fusion_mode: FusionMode = Field(default=FusionMode.ENHANCED, description="Fusion strategy")
    use_cache: bool = Field(default=True, description="Use sentiment cache")

class BatchSentimentRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze", max_items=50)
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code")
    fusion_mode: FusionMode = Field(default=FusionMode.ENHANCED, description="Fusion strategy")
    use_cache: bool = Field(default=True, description="Use sentiment cache")

class SentimentResponse(BaseModel):
    status: str
    sentiment: Dict[str, Any] = Field(..., description="Sentiment analysis result")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    language: str
    model_fusion: Dict[str, Any] = Field(..., description="Multi-model fusion details")
    metadata: Dict[str, Any]
    error: Optional[str] = None

class BatchSentimentResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class FeedbackData(BaseModel):
    text: str
    predicted_sentiment: str
    actual_sentiment: str = Field(..., pattern="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)

class CalibrationRequest(BaseModel):
    feedback_data: List[FeedbackData] = Field(..., min_items=1, max_items=1000)
    method: str = Field(default="online_learning", description="Calibration method")

# ===========================
# MODULE 3: PROFILE PROCESSOR MODELS
# ===========================

class InteractionData(BaseModel):
    timestamp: datetime
    action_type: str = Field(..., description="Type of user action")
    content: str = Field(..., description="Content of interaction")
    sentiment: Optional[str] = None
    topics: Optional[List[str]] = None

class UserPreferences(BaseModel):
    language: LanguageCode = Field(default=LanguageCode.AUTO)
    risk_tolerance: str = Field(default="medium", pattern="^(low|medium|high)$")
    complexity_preference: str = Field(default="medium", pattern="^(simple|medium|advanced|expert)$")
    topics_of_interest: List[str] = Field(default=[], max_items=20)
    notification_frequency: str = Field(default="daily", pattern="^(never|daily|weekly|monthly)$")

class ProfileRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    interaction_data: List[InteractionData] = Field(..., min_items=1, max_items=1000)
    preferences: Optional[UserPreferences] = None

class ProfileResponse(BaseModel):
    status: str
    user_id: str
    profile: Dict[str, Any] = Field(..., description="Generated user profile")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Profile accuracy confidence")
    metadata: Dict[str, Any]
    error: Optional[str] = None

class AdaptationType(str, Enum):
    """Content adaptation types"""
    TONE = "tone"
    COMPLEXITY = "complexity"
    LANGUAGE = "language"
    PERSONALIZATION = "personalization"

class AdaptationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    content: str = Field(..., description="Content to adapt")
    adaptation_type: AdaptationType = Field(..., description="Type of adaptation")

class AdaptationResponse(BaseModel):
    status: str
    original_content: str
    adapted_content: str
    adaptation_applied: Dict[str, Any] = Field(..., description="Adaptation details")
    metadata: Dict[str, Any]
    error: Optional[str] = None

class RecommendationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    content_type: str = Field(..., description="Type of content to recommend")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")

# ===========================
# MODULE 4: COGNITIVE BRIDGE MODELS
# ===========================

class EventRequest(BaseModel):
    event_type: str = Field(..., description="Type of cognitive event")
    payload: Dict[str, Any] = Field(..., description="Event payload data")
    priority: Priority = Field(default=Priority.MEDIUM, description="Event priority")
    correlation_id: Optional[str] = None

class RoutingStrategy(str, Enum):
    """Request routing strategies"""
    CONTENT_BASED = "content_based"
    USER_BASED = "user_based"
    LOAD_BALANCED = "load_balanced"
    INTELLIGENT = "intelligent"

class RoutingRequest(BaseModel):
    content: str = Field(..., description="Content to route")
    user_context: Optional[Dict[str, Any]] = Field(default={}, description="User context")
    strategy: RoutingStrategy = Field(default=RoutingStrategy.INTELLIGENT, description="Routing strategy")

# ===========================
# ADMIN & MONITORING MODELS
# ===========================

class HealthStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ModuleHealth(BaseModel):
    loaded: bool
    healthy: bool
    last_check: datetime = Field(default_factory=datetime.now)
    error_count: int = Field(default=0)
    response_time_ms: Optional[float] = None

class ServiceMetrics(BaseModel):
    requests_total: int = Field(default=0)
    requests_per_minute: float = Field(default=0.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_response_time_ms: float = Field(default=0.0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_usage_mb: float = Field(default=0.0)

class IntegrityReport(BaseModel):
    overall_status: str
    checks_performed: int
    violations_found: int
    recommendations: List[str]
    detailed_results: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

# ===========================
# ERROR MODELS
# ===========================

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None