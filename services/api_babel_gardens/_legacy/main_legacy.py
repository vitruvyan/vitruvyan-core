# api_babel_gardens/main.py
"""
🌿 VITRUVYAN BABEL GARDENS - SACRED LINGUISTIC UNITY:8009
Sacred Tower of Babel where all languages converge into divine understanding
4 sacred groves of linguistic cultivation:
- SemanticGrove: Sacred meaning embeddings across all tongues
- EmotionalMeadow: Divine sentiment synthesis with cross-cultural understanding
- CulturalArbor: Cross-linguistic behavioral analysis & sacred personalization
- DivinePortal: Sacred event orchestration & multilingual routing
"""

import os
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Import sacred Redis listener for divine linguistic cultivation
from core.cognitive.babel_gardens.redis_listener import babel_gardens_listener

# Import unified modules
from .modules.embedding_engine import EmbeddingEngineModule
from .modules.sentiment_fusion import SentimentFusionModule  
from .modules.profile_processor import ProfileProcessorModule
from .modules.cognitive_bridge import CognitiveBridgeModule

# Import shared infrastructure
from .shared.model_manager import model_manager
from .shared.vector_cache import vector_cache
from .shared.integrity_watcher import integrity_watcher

# Import schemas
from .schemas.api_models import *

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================
# PROMETHEUS METRICS
# ===========================

# HTTP request metrics
http_requests_total = Counter(
    'babel_http_requests_total',
    'Total HTTP requests to Babel Gardens',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'babel_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Embedding processing metrics
embedding_requests_total = Counter(
    'babel_embedding_requests_total',
    'Total embedding requests processed',
    ['embedding_type', 'language']
)

embedding_processing_duration_seconds = Histogram(
    'babel_embedding_processing_duration_seconds',
    'Embedding processing time in seconds',
    ['embedding_type'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Sentiment analysis metrics
sentiment_requests_total = Counter(
    'babel_sentiment_requests_total',
    'Total sentiment analysis requests',
    ['sentiment_type']
)

sentiment_processing_duration_seconds = Histogram(
    'babel_sentiment_processing_duration_seconds',
    'Sentiment analysis processing time in seconds',
    ['sentiment_type'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Emotion detection metrics (Phase 1 - NEW)
emotion_requests_total = Counter(
    'babel_emotion_requests_total',
    'Total emotion detection requests',
    ['emotion_type']
)

emotion_processing_duration_seconds = Histogram(
    'babel_emotion_processing_duration_seconds',
    'Emotion detection processing time in seconds',
    ['emotion_type'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Model and cache health gauges
models_loaded_gauge = Gauge(
    'babel_models_loaded',
    'Number of AI models currently loaded in memory'
)

cache_hit_rate_gauge = Gauge(
    'babel_cache_hit_rate',
    'Cache hit rate (0.0 to 1.0)'
)

vector_cache_size_gauge = Gauge(
    'babel_vector_cache_size',
    'Number of cached vectors in Redis'
)

sacred_groves_blessed_gauge = Gauge(
    'babel_sacred_groves_blessed',
    'Number of sacred groves blessed and flourishing'
)

# Sacred service state in the Gardens of Babel
class BabelGardensLinguisticService:
    """
    🌿 Sacred Babel Gardens Linguistic Service
    Cultivates 4 sacred groves with divine linguistic infrastructure
    """
    
    def __init__(self):
        self.service_name = "babel_gardens_linguistic_unity"
        self.port = 8009
        self.start_time = datetime.now()
        self.version = "2.0.0"
        
        # Sacred infrastructure (divine initialization)
        self.model_manager = None
        self.vector_cache = None
        self.integrity_watcher = None
        
        # Sacred groves (divine initialization)
        self.emotion_detector = None    # 🎭 Emotional understanding & cultural awareness
        self.semantic_grove = None      # Sacred meaning cultivation
        self.emotional_meadow = None    # Divine sentiment gardens
        self.cultural_arbor = None      # Cross-linguistic wisdom trees
        self.divine_portal = None       # Sacred communication gateway
        
        # Sacred grove health state
        self.groves_blessed = {
            "emotion_detector": False,  # 🎭 NEW - Phase 1
            "semantic_grove": False,
            "emotional_meadow": False,  
            "cultural_arbor": False,
            "divine_portal": False
        }
        
        logger.info(f"🌿 {self.service_name} blessed and initialized on sacred port {self.port}")
    
    async def bless_sacred_infrastructure(self):
        """🌿 Bless sacred components used by all divine groves"""
        try:
            # Sacred Model Manager - handles divine loading and memory sanctification
            self.model_manager = model_manager
            logger.info("✅ Sacred model_manager blessed")
            
            # Divine Vector Cache - Redis with sacred linguistic partitioning
            self.vector_cache = vector_cache
            logger.info("✅ Divine vector_cache blessed")
            
            # Sacred Integrity Watcher - monitors cross-grove divine consistency
            self.integrity_watcher = integrity_watcher
            logger.info("✅ Sacred IntegrityWatcher blessed")
            
            return True
            
        except Exception as e:
            logger.error(f"💀 Failed to bless sacred infrastructure: {e}")
            return False
    
    async def cultivate_sacred_groves(self):
        """🌿 Cultivate all 5 sacred linguistic groves (updated Phase 1)"""
        try:
            # Sacred Grove 0: EmotionDetector (NEW - Phase 1)
            from .modules.emotion_detector import EmotionDetectorModule
            self.emotion_detector = EmotionDetectorModule()
            await self.emotion_detector.initialize(
                model_manager=self.model_manager,
                vector_cache=self.vector_cache,
                integrity_watcher=self.integrity_watcher
            )
            self.groves_blessed["emotion_detector"] = True
            logger.info("🎭 EmotionDetector cultivated and blessed")
            
            # Sacred Grove 1: SemanticGrove
            self.semantic_grove = EmbeddingEngineModule()
            await self.semantic_grove.initialize(
                model_manager=self.model_manager,
                vector_cache=self.vector_cache,
                integrity_watcher=self.integrity_watcher
            )
            self.groves_blessed["semantic_grove"] = True
            logger.info("🌱 SemanticGrove cultivated and blessed")
            
            # Sacred Grove 2: EmotionalMeadow  
            self.emotional_meadow = SentimentFusionModule()
            await self.emotional_meadow.initialize(
                model_manager=self.model_manager,
                vector_cache=self.vector_cache,
                integrity_watcher=self.integrity_watcher
            )
            self.groves_blessed["emotional_meadow"] = True
            logger.info("🌸 EmotionalMeadow cultivated and blessed")
            
            # Sacred Grove 3: CulturalArbor
            self.cultural_arbor = ProfileProcessorModule()
            await self.cultural_arbor.initialize(
                model_manager=self.model_manager,
                vector_cache=self.vector_cache,
                integrity_watcher=self.integrity_watcher
            )
            self.groves_blessed["cultural_arbor"] = True
            logger.info("🌳 CulturalArbor cultivated and blessed")
            
            # Sacred Grove 4: DivinePortal
            self.divine_portal = CognitiveBridgeModule()
            await self.divine_portal.initialize(
                model_manager=self.model_manager,
                vector_cache=self.vector_cache,
                integrity_watcher=self.integrity_watcher
            )
            self.groves_blessed["divine_portal"] = True
            logger.info("🚪 DivinePortal cultivated and blessed")
            
            return True
            
        except Exception as e:
            logger.error(f"💀 Failed to cultivate sacred groves: {e}")
            return False
    
    def get_sacred_grove_health(self) -> Dict[str, Any]:
        """🌿 Get divine health status of all sacred groves (updated Phase 1)"""
        return {
            "sacred_service": self.service_name,
            "divine_version": self.version,
            "blessed_uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "sacred_groves": {
                "emotion_detector": {  # 🎭 NEW - Phase 1
                    "blessed": self.groves_blessed["emotion_detector"],
                    "flourishing": self.emotion_detector.is_healthy() if self.emotion_detector else False
                },
                "semantic_grove": {
                    "blessed": self.groves_blessed["semantic_grove"],
                    "flourishing": self.semantic_grove.is_healthy() if self.semantic_grove else False
                },
                "emotional_meadow": {
                    "blessed": self.groves_blessed["emotional_meadow"],
                    "flourishing": self.emotional_meadow.is_healthy() if self.emotional_meadow else False
                },
                "cultural_arbor": {
                    "blessed": self.groves_blessed["cultural_arbor"], 
                    "flourishing": self.cultural_arbor.is_healthy() if self.cultural_arbor else False
                },
                "divine_portal": {
                    "blessed": self.groves_blessed["divine_portal"],
                    "flourishing": self.divine_portal.is_healthy() if self.divine_portal else False
                }
            },
            "sacred_infrastructure": {
                "model_manager": self.model_manager is not None,
                "vector_cache": self.vector_cache is not None,
                "integrity_watcher": self.integrity_watcher is not None
            }
        }

# Sacred service instance - Gardens of Babel
babel_service = BabelGardensLinguisticService()

# Sacred FastAPI lifespan management
@asynccontextmanager
async def sacred_lifespan(app: FastAPI):
    """🌿 Manage sacred service lifecycle - divine blessing and sanctification"""
    # Sacred startup blessing
    logger.info("🌿 Beginning sacred cultivation of Babel Gardens...")
    
    # Bless sacred infrastructure
    if not await babel_service.bless_sacred_infrastructure():
        raise RuntimeError("Failed to bless sacred infrastructure")
    
    # Cultivate all sacred groves
    if not await babel_service.cultivate_sacred_groves():
        raise RuntimeError("Failed to cultivate sacred groves")
    
    # Start sacred Redis listener for divine linguistic cultivation
    logger.info("🌿 Starting sacred cognitive bus listener...")
    listener_task = asyncio.create_task(babel_gardens_listener.begin_sacred_listening())
    
    logger.info("✅ Babel Gardens fully cultivated and blessed")
    
    yield
    
    # Sacred shutdown sanctification
    logger.info("🌿 Beginning sacred shutdown of Babel Gardens...")
    # Stop sacred Redis listener
    babel_gardens_listener.running = False
    if not listener_task.done():
        listener_task.cancel()
    await babel_gardens_listener.sacred_cleanup()

# Sacred FastAPI app with divine lifespan management
app = FastAPI(
    title="🌿 Vitruvyan Babel Gardens - Sacred Linguistic Unity",
    description="Divine linguistic cultivation with 4 sacred groves of understanding",
    version="2.0.0",
    lifespan=sacred_lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sacred dependency injection
async def get_babel_gardens_service() -> BabelGardensLinguisticService:
    """🌿 Sacred dependency injection for Babel Gardens service"""
    return babel_service

# Legacy compatibility for Gemma cognitive service references
async def get_cognitive_service() -> BabelGardensLinguisticService:
    """🌿 Legacy compatibility - Maps to Babel Gardens service"""
    return babel_service

# ===========================
# SACRED HEALTH & DIVINE MONITORING ENDPOINTS
# ===========================

@app.get("/sacred-health")
async def sacred_health_check(service: BabelGardensLinguisticService = Depends(get_babel_gardens_service)):
    """🌿 Comprehensive sacred health check for all divine groves"""
    sacred_status = service.get_sacred_grove_health()
    
    # Determine overall divine blessing
    all_groves_flourishing = all(
        grove["blessed"] and grove["flourishing"] 
        for grove in sacred_status["sacred_groves"].values()
    )
    
    sacred_status["divine_status"] = "blessed" if all_groves_flourishing else "requires_blessing"
    sacred_status["divine_timestamp"] = datetime.now().isoformat()
    
    return sacred_status

@app.get("/health")
async def legacy_health_check(service: BabelGardensLinguisticService = Depends(get_babel_gardens_service)):
    """Legacy health check endpoint - redirects to sacred health"""
    return await sacred_health_check(service)

@app.get("/metrics")
async def metrics(service: BabelGardensLinguisticService = Depends(get_babel_gardens_service)):
    """
    🌿 Prometheus metrics endpoint for Babel Gardens observability
    Exposes linguistic processing metrics, cache stats, and model health
    """
    try:
        # Update gauge metrics with current system state
        sacred_status = service.get_sacred_grove_health()
        
        # Count blessed and flourishing groves
        blessed_count = sum(
            1 for grove in sacred_status["sacred_groves"].values()
            if grove.get("blessed") and grove.get("flourishing")
        )
        sacred_groves_blessed_gauge.set(blessed_count)
        
        # Update models loaded gauge
        if hasattr(service.model_manager, 'loaded_models'):
            models_loaded_gauge.set(len(service.model_manager.loaded_models))
        
        # Update cache metrics if vector_cache is available
        if hasattr(service.vector_cache, 'get_stats'):
            cache_stats = await service.vector_cache.get_stats()
            if 'hit_rate' in cache_stats:
                cache_hit_rate_gauge.set(cache_stats['hit_rate'])
            if 'size' in cache_stats:
                vector_cache_size_gauge.set(cache_stats['size'])
        
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        # Return empty metrics on error (graceful degradation)
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health/{module_name}")
async def module_health_check(
    module_name: str,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Health check for specific module"""
    if module_name not in service.modules_loaded:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    module = getattr(service, module_name, None)
    if not module:
        raise HTTPException(status_code=503, detail=f"Module {module_name} not initialized")
    
    return {
        "module": module_name,
        "status": "healthy" if module.is_healthy() else "unhealthy",
        "loaded": service.modules_loaded[module_name],
        "details": module.get_health_details() if hasattr(module, 'get_health_details') else {}
    }

# ===========================
# MODULE 1: EMBEDDING ENGINE ENDPOINTS
# ===========================

@app.post("/v1/embeddings/create", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """[BABEL GARDENS] Standard embedding creation endpoint"""
    start_time = time.time()
    
    if not service.semantic_grove:
        raise HTTPException(status_code=503, detail="SemanticGrove module not available")
    
    try:
        logger.info(f"[BABEL GARDENS] Creating embedding for text: {request.text[:50]}...")
        result = await service.semantic_grove.create_financial_embedding(
            text=request.text,
            language=request.language,
            use_cache=request.use_cache
        )
        logger.info(f"[BABEL GARDENS] Embedding created successfully, dimension: {len(result.embedding)}")
        
        # Track metrics
        duration = time.time() - start_time
        embedding_requests_total.labels(embedding_type='standard', language=request.language or 'unknown').inc()
        embedding_processing_duration_seconds.labels(embedding_type='standard').observe(duration)
        http_requests_total.labels(method='POST', endpoint='/v1/embeddings/create', status='200').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/v1/embeddings/create').observe(duration)
        
        return result
    except Exception as e:
        logger.error(f"[BABEL GARDENS] Embedding error: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/v1/embeddings/create', status='500').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/v1/embeddings/create').observe(duration)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings/financial", response_model=EmbeddingResponse)
async def create_financial_embedding(
    request: EmbeddingRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Generate financial domain-specific embeddings"""
    if not service.semantic_grove:
        raise HTTPException(status_code=503, detail="EmbeddingEngine module not available")
    
    try:
        result = await service.semantic_grove.create_financial_embedding(
            text=request.text,
            language=request.language,
            use_cache=request.use_cache
        )
        return result
    except Exception as e:
        logger.error(f"Financial embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings/multilingual", response_model=EmbeddingResponse)
async def create_multilingual_embedding(
    request: EmbeddingRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Generate multilingual embeddings"""
    if not service.semantic_grove:
        raise HTTPException(status_code=503, detail="EmbeddingEngine module not available")
    
    try:
        result = await service.semantic_grove.create_multilingual_embedding(request)
        return result
    except Exception as e:
        logger.error(f"Multilingual embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings/batch", response_model=BatchEmbeddingResponse)
async def create_batch_embeddings(
    request: BatchEmbeddingRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Generate embeddings for multiple texts"""
    if not service.semantic_grove:
        raise HTTPException(status_code=503, detail="EmbeddingEngine module not available")
    
    try:
        result = await service.semantic_grove.create_batch_embeddings(request)
        return result
    except Exception as e:
        logger.error(f"Batch embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings/similarity", response_model=SimilarityResponse)
async def compute_semantic_similarity(
    request: SimilarityRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Compute semantic similarity between texts"""
    if not service.semantic_grove:
        raise HTTPException(status_code=503, detail="EmbeddingEngine module not available")
    
    try:
        result = await service.semantic_grove.compute_similarity(request)
        return result
    except Exception as e:
        logger.error(f"Similarity computation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# MODULE 0: EMOTION DETECTOR ENDPOINTS (NEW - Phase 1)
# ===========================

@app.post("/v1/emotion/detect", response_model=EmotionResponse)
async def detect_emotion(
    request: EmotionRequest,
    service: BabelGardensLinguisticService = Depends(get_babel_gardens_service)
):
    """
    🎭 Advanced emotion detection with cultural awareness
    
    Detects user emotion using 3-layer pipeline:
    1. Sentiment Analysis (positive/negative/neutral)
    2. Cultural Context (communication style)
    3. Emotion Classification (9 core emotions)
    
    Supported Emotions:
    - frustrated, excited, curious, anxious, confident
    - satisfied, bored, skeptical, neutral
    
    Cultural Contexts:
    - italian_expressive, japanese_formal, anglo_professional
    - latin_enthusiastic, chinese_formal, korean_formal, etc.
    
    Returns emotion with confidence, intensity, and reasoning
    """
    start_time = time.time()
    
    if not service.emotion_detector:
        raise HTTPException(status_code=503, detail="EmotionDetector module not available")
    
    try:
        logger.info(f"🎭 [emotion] Detecting emotion for text: {request.text[:50]}...")
        result = await service.emotion_detector.detect_emotion(request)
        
        # Track Prometheus metrics
        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/v1/emotion/detect', status='200').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/v1/emotion/detect').observe(duration)
        
        # Track emotion-specific metrics
        if result.status == "success":
            primary_emotion = result.emotion.get("primary", "unknown")
            emotion_requests_total.labels(emotion_type=primary_emotion).inc()
            emotion_processing_duration_seconds.labels(emotion_type=primary_emotion).observe(duration)
        
        logger.info(
            f"🎭 [emotion] Detected: {result.emotion.get('primary')} "
            f"(confidence: {result.emotion.get('confidence', 0):.2f}, "
            f"processing: {duration*1000:.0f}ms)"
        )
        
        return result
    except Exception as e:
        logger.error(f"🎭 ❌ Emotion detection error: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/v1/emotion/detect', status='500').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/v1/emotion/detect').observe(duration)
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# MODULE 2: SENTIMENT FUSION ENDPOINTS  
# ===========================

@app.post("/v1/sentiment/analyze", response_model=SentimentResponse)
async def analyze_sentiment_fusion(
    request: SentimentRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """[GEMMA] Advanced sentiment analysis with multi-model fusion"""
    start_time = time.time()
    
    if not service.emotional_meadow:
        raise HTTPException(status_code=503, detail="SentimentFusion module not available")
    
    try:
        logger.info(f"[GEMMA] Analyzing sentiment for text: {request.text[:50]}...")
        result = await service.emotional_meadow.analyze_sentiment(request)
        
        # Track metrics
        duration = time.time() - start_time
        sentiment_requests_total.labels(sentiment_type=request.fusion_mode or 'standard').inc()
        sentiment_processing_duration_seconds.labels(sentiment_type=request.fusion_mode or 'standard').observe(duration)
        http_requests_total.labels(method='POST', endpoint='/v1/sentiment/analyze', status='200').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/v1/sentiment/analyze').observe(duration)
        
        return result  # Already a SentimentResponse object
    except Exception as e:
        logger.error(f"Sentiment fusion error: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/v1/sentiment/analyze', status='500').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/v1/sentiment/analyze').observe(duration)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/sentiment/batch", response_model=BatchSentimentResponse)
async def analyze_batch_sentiment_fusion(
    request: BatchSentimentRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Batch sentiment analysis with fusion"""
    if not service.emotional_meadow:
        raise HTTPException(status_code=503, detail="SentimentFusion module not available")
    
    try:
        result = await service.emotional_meadow.analyze_batch_sentiment(request)
        return result  # Already a BatchSentimentResponse object
    except Exception as e:
        logger.error(f"Batch sentiment fusion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/sentiment/calibrate")
async def calibrate_sentiment_models(
    request: CalibrationRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Online learning for sentiment model weights"""
    if not service.emotional_meadow:
        raise HTTPException(status_code=503, detail="SentimentFusion module not available")
    
    try:
        result = await service.emotional_meadow.calibrate_models(
            feedback_data=request.feedback_data,
            calibration_method=request.method
        )
        return {"status": "success", "calibration_result": result}
    except Exception as e:
        logger.error(f"Model calibration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# MODULE 3: PROFILE PROCESSOR ENDPOINTS
# ===========================

@app.post("/v1/profiles/create", response_model=ProfileResponse)
async def create_user_profile(
    request: ProfileRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Create user behavioral profile"""
    if not service.cultural_arbor:
        raise HTTPException(status_code=503, detail="ProfileProcessor module not available")
    
    try:
        result = await service.cultural_arbor.create_profile(
            user_id=request.user_id,
            interaction_data=request.interaction_data,
            preferences=request.preferences
        )
        return ProfileResponse(**result)
    except Exception as e:
        logger.error(f"Profile creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/profiles/adapt", response_model=AdaptationResponse)
async def adapt_response_to_user(
    request: AdaptationRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Adapt response tone and complexity to user profile"""
    if not service.cultural_arbor:
        raise HTTPException(status_code=503, detail="ProfileProcessor module not available")
    
    try:
        result = await service.cultural_arbor.adapt_response(
            user_id=request.user_id,
            content=request.content,
            adaptation_type=request.adaptation_type
        )
        return AdaptationResponse(**result)
    except Exception as e:
        logger.error(f"Response adaptation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/profiles/recommend")
async def get_personalized_recommendations(
    request: RecommendationRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Get personalized content recommendations"""
    if not service.cultural_arbor:
        raise HTTPException(status_code=503, detail="ProfileProcessor module not available")
    
    try:
        result = await service.cultural_arbor.get_recommendations(
            user_id=request.user_id,
            content_type=request.content_type,
            context=request.context
        )
        return {"status": "success", "recommendations": result}
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# MODULE 4: COGNITIVE BRIDGE ENDPOINTS
# ===========================

@app.post("/v1/events/publish")
async def publish_cognitive_event(
    request: EventRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Publish event to Cognitive Bus"""
    if not service.divine_portal:
        raise HTTPException(status_code=503, detail="CognitiveBridge module not available")
    
    try:
        result = await service.divine_portal.publish_event(
            event_type=request.event_type,
            payload=request.payload,
            priority=request.priority
        )
        return {"status": "success", "event_id": result["event_id"]}
    except Exception as e:
        logger.error(f"Event publishing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/routing/intelligent")
async def intelligent_request_routing(
    request: RoutingRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """Intelligent request routing based on content analysis"""
    if not service.divine_portal:
        raise HTTPException(status_code=503, detail="CognitiveBridge module not available")
    
    try:
        result = await service.divine_portal.route_request(
            content=request.content,
            user_context=request.user_context,
            routing_strategy=request.strategy
        )
        return {"status": "success", "routing_decision": result}
    except Exception as e:
        logger.error(f"Intelligent routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# ADMIN & MONITORING ENDPOINTS
# ===========================

@app.get("/admin/metrics")
async def get_service_metrics(service: BabelGardensLinguisticService = Depends(get_cognitive_service)):
    """Get comprehensive service metrics"""
    metrics = {
        "service_info": service.get_module_health(),
        "cache_metrics": await service.vector_cache.get_metrics() if service.vector_cache else {},
        "model_metrics": service.model_manager.get_metrics() if service.model_manager else {},
        "integrity_metrics": await service.integrity_watcher.get_metrics() if service.integrity_watcher else {}
    }
    return metrics

@app.post("/admin/cache/cleanup")
async def cleanup_vector_cache(service: BabelGardensLinguisticService = Depends(get_cognitive_service)):
    """Clean up old cache entries"""
    if not service.vector_cache:
        raise HTTPException(status_code=503, detail="Vector cache not available")
    
    try:
        result = await service.vector_cache.cleanup_old_entries()
        return {"status": "success", "cleanup_result": result}
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/integrity/check")
async def run_integrity_check(service: BabelGardensLinguisticService = Depends(get_cognitive_service)):
    """Run comprehensive integrity check"""
    if not service.integrity_watcher:
        raise HTTPException(status_code=503, detail="Integrity watcher not available")
    
    try:
        result = await service.integrity_watcher.run_full_check()
        return {"status": "success", "integrity_report": result}
    except Exception as e:
        logger.error(f"Integrity check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# LEGACY ENDPOINTS (per compatibilità documentazione)
# ===========================

@app.post("/embedding/create", response_model=EmbeddingResponse, include_in_schema=False)
async def legacy_create_embedding(
    request: EmbeddingRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """[GEMMA] Legacy endpoint per compatibilità documentazione - redirect a /v1/embeddings/create"""
    return await create_embedding(request, service)

@app.post("/sentiment/analyze", response_model=SentimentResponse, include_in_schema=False)  
async def legacy_sentiment_analyze(
    request: SentimentRequest,
    service: BabelGardensLinguisticService = Depends(get_cognitive_service)
):
    """[GEMMA] Legacy endpoint per compatibilità documentazione - redirect a /v1/sentiment/analyze"""
    return await analyze_sentiment_fusion(request, service)

# ===========================
# STARTUP
# ===========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)