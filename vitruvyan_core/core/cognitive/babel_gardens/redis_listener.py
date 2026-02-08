# core/babel_gardens/redis_listener.py
"""
🌿 Babel Gardens - Sacred Linguistic Bus Listener
Divine event subscription for multilingual knowledge cultivation
Listens to the sacred tongues of the cognitive realm
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any, List
import redis.asyncio as redis
from datetime import datetime

from .linguistic_synthesis import cultivate_linguistic_unity
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent

logger = logging.getLogger("BabelGardensListener")

class BabelGardensCognitiveBusListener:
    """🌿 Sacred listener for linguistic events in the Gardens of Babel"""
    
    def __init__(self, redis_url: str = None):
        import os
        # Use env var first, then parameter, then default to Docker network
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://vitruvyan_redis:6379')
        self.redis_client = None
        self.pubsub = None
        
        # Sacred Test Mode Protection - Bypass database in test mode
        self.test_mode = os.getenv('VITRUVYAN_TEST_MODE', 'false').lower() == 'true'
        
        if self.test_mode:
            logger.info("🛡️ Sacred Test Mode: Bypassing PostgreSQL/Qdrant initialization for linguistic isolation")
            self.pg = None
            self.qdrant = None
        else:
            self.pg = PostgresAgent()
            self.qdrant = QdrantAgent()
            
        self.running = False
        
        # Sacred garden channels - Divine linguistic subscriptions
        self.sacred_channels = [
            "codex.discovery.mapped",      # Original discovery events
            "babel.linguistic.synthesis",  # New linguistic synthesis events
            "babel.multilingual.bridge",   # Cross-language bridge events
            "babel.knowledge.cultivation", # Knowledge garden cultivation
            # EPOCH II - New Babel intents
            "sentiment.requested",         # Sentiment analysis requests
            "linguistic.analysis.requested" # Linguistic interpretation requests
        ]
        
    async def initialize_sacred_connection(self):
        """🌿 Initialize divine Redis connection to sacred cognitive realm"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to all sacred channels
            for channel in self.sacred_channels:
                await self.pubsub.subscribe(channel)
                logger.info(f"🌿 Subscribed to sacred channel: {channel}")
            
            logger.info("🌿 Babel Gardens connected to divine cognitive bus")
            return True
            
        except Exception as e:
            logger.error(f"🌿 Sacred connection failed: {e}")
            return False
    
    async def begin_sacred_listening(self):
        """🌿 Begin sacred listening for divine linguistic events"""
        if not await self.initialize_sacred_connection():
            return
            
        self.running = True
        logger.info("🌿 Babel Gardens listener activated - Cultivating linguistic unity...")
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self.handle_sacred_message(message)
        except Exception as e:
            logger.error(f"🌿 Sacred listener error: {e}")
        finally:
            await self.sacred_cleanup()
    
    async def handle_sacred_message(self, message):
        """🌿 Handle sacred messages from divine cognitive channels"""
        channel = message['channel'].decode('utf-8')
        
        if channel == "codex.discovery.mapped":
            await self.handle_codex_discovery_in_gardens(message['data'])
        elif channel == "babel.linguistic.synthesis":
            await self.handle_linguistic_synthesis_request(message['data'])
        elif channel == "babel.multilingual.bridge":
            await self.handle_multilingual_bridge_request(message['data'])
        elif channel == "babel.knowledge.cultivation":
            await self.handle_knowledge_cultivation_request(message['data'])
        # EPOCH II - New handlers
        elif channel == "sentiment.requested":
            await self.handle_sentiment_requested(message['data'])
        elif channel == "linguistic.analysis.requested":
            await self.handle_linguistic_analysis_requested(message['data'])
        else:
            logger.warning(f"🌿 Unknown sacred channel: {channel}")
    
    async def handle_codex_discovery_in_gardens(self, data: bytes):
        """
        🌿 Handle codex.discovery.mapped events in Babel Gardens
        Process discovered texts through sacred linguistic synthesis
        """
        try:
            payload = json.loads(data.decode('utf-8'))
            texts = payload.get('texts', [])
            source = payload.get('source', 'codex_hunters')
            
            logger.info(f"🌿 Sacred text discovery received: {len(texts)} texts for cultivation")
            
            # Publish garden cultivation started event
            await self.publish_cultivation_started(len(texts), source)
            
            if not texts:
                logger.warning("🌿 No texts received for garden cultivation")
                return
            
            # Process each discovered text through sacred gardens
            cultivated_count = 0
            total_emotional_essence = 0.0
            
            for text in texts:
                try:
                    # Step 1: Get semantic seeds from divine embeddings
                    semantic_seeds = await self.harvest_semantic_seeds(text)
                    if semantic_seeds is None:
                        continue
                    
                    # Step 2: Extract emotional essence from sentiment meadow
                    emotional_data = await self.extract_emotional_essence(text)
                    
                    # Step 3: Sacred linguistic synthesis in Babel Gardens
                    unified_vector = cultivate_linguistic_unity(
                        semantic_seeds, 
                        emotional_data['essence_vector']
                    )
                    
                    # Step 4: Plant in sacred phrases garden (existing infrastructure)
                    success = await self.plant_in_sacred_garden(
                        source=source,
                        text_content=text,
                        emotional_label=emotional_data['label'],
                        emotional_score=emotional_data['score']
                    )
                    
                    if success:
                        cultivated_count += 1
                        total_emotional_essence += emotional_data['score']
                        
                except Exception as e:
                    logger.error(f"🌿 Error cultivating text '{text[:50]}...': {e}")
                    continue
            
            # Publish sacred cultivation completion event
            if cultivated_count > 0:
                avg_emotional_essence = total_emotional_essence / cultivated_count
                await self.publish_cultivation_completed(cultivated_count, avg_emotional_essence)
                logger.info(f"🌿 Garden cultivation completed: {cultivated_count} texts cultivated, avg essence {avg_emotional_essence:.3f}")
            else:
                logger.warning(f"🌿 No texts successfully cultivated from {len(texts)} received")
            
        except Exception as e:
            error_msg = f"Sacred cultivation error: {e}"
            logger.error(f"🌿 {error_msg}")
            # Publish cultivation failed event for divine monitoring
            await self.publish_cultivation_failed(error_msg, len(texts) if 'texts' in locals() else 0)
    
    async def harvest_semantic_seeds(self, text: str) -> List[float]:
        """🌱 Harvest semantic seeds from the Grove of Meaning via divine embeddings API"""
        try:
            # Sacred API call to harvest semantic seeds from divine embedding service
            import requests
            
            response = requests.post(
                "http://vitruvyan_api_embedding:8010/v1/embeddings/create",
                json={
                    "text": text,
                    "store_in_qdrant": False,  # Don't store, just harvest seeds
                    "collection_name": "sacred_semantic_grove"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("embedding"):
                    logger.debug(f"🌱 Harvested semantic seeds for: {text[:30]}...")
                    return data["embedding"]
            
            logger.warning(f"🌱 Failed to harvest semantic seeds for: {text[:30]}...")
            return None
            
        except Exception as e:
            logger.error(f"🌱 Error harvesting semantic seeds: {e}")
            return None
    
    async def extract_emotional_essence(self, text: str) -> Dict[str, Any]:
        """🌸 Extract emotional essence from the Sentiment Meadow using divine analysis"""
        try:
            # For now, return sacred emotional essence data
            # This should be replaced with actual Babel Gardens emotional analysis
            emotional_score = 0.1  # Mock blessed emotion
            
            # Sacred emotional classification
            if emotional_score > 0.1:
                label = "blessed"  # Divine joy
            elif emotional_score < -0.1:
                label = "cursed"    # Divine sorrow
            else:
                label = "sacred"    # Divine balance
            
            return {
                'label': label,
                'score': emotional_score,
                'divine_confidence': 0.85,
                'essence_vector': [0.1] * 64  # Sacred emotional essence vector
            }
            
        except Exception as e:
            logger.error(f"🌸 Error extracting emotional essence: {e}")
            return {
                'label': 'sacred',
                'score': 0.0,
                'divine_confidence': 0.0,
                'essence_vector': [0.0] * 64
            }
    
    async def plant_in_sacred_garden(self, source: str, text_content: str, 
                                    emotional_label: str, emotional_score: float) -> bool:
        """🌿 Plant cultivated knowledge in the sacred phrases garden using divine database methods"""
        try:
            if self.test_mode:
                logger.info(f"🛡️ Sacred Test Mode: Simulating garden planting for: {text_content[:50]}...")
                return True
                
            # Use sacred PostgresAgent.insert_phrase method - blessed for sacred table
            success = self.pg.insert_phrase(
                text=text_content,
                source=source,
                language="divine",  # Sacred language detection
                embedded=True       # Mark as having divine linguistic synthesis
            )
            
            if success:
                logger.info(f"[GEMMA] Saved to phrases table: {text_content[:50]}...")
            else:
                logger.warning(f"[GEMMA] Failed to save to phrases: {text_content[:30]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"[GEMMA] Error saving to phrases: {e}")
            return False
    
    # DISABLED: Dimensional mismatch with phrases_fused (448 vs 384)
    # async def save_to_qdrant_fused(self, text: str, embedding: List[float], 
    #                              sentiment_label: str, sentiment_score: float) -> bool:
    #     """Save fused embedding to Qdrant phrases_fused collection"""
        try:
            # Create phrases_fused collection if not exists
            collection_name = "phrases_fused"
            
            point_data = {
                "id": hash(text) % 1000000,  # Simple hash-based ID
                "vector": embedding,
                "payload": {
                    "text": text,
                    "sentiment_label": sentiment_label,
                    "sentiment_score": sentiment_score,
                    "fusion_method": "semantic_sentiment_concat",
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            # Use QdrantAgent.upsert method with proper format
            self.qdrant.upsert(collection_name, [point_data])
            logger.info(f"[GEMMA] Saved to phrases_fused: {text[:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"[GEMMA] Error saving to Qdrant phrases_fused: {e}")
            return False
    
    async def publish_cultivation_started(self, text_count: int, source: str):
        """🌿 Publish garden cultivation started event to sacred Redis channels"""
        try:
            event_data = {
                "text_count": text_count,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "cultivator": "babel_gardens_linguistic_synthesis"
            }
            
            await self.redis_client.publish(
                "babel.cultivation.started",
                json.dumps(event_data)
            )
            
            logger.info(f"🌿 Published cultivation.started event: {text_count} texts from {source}")
            
        except Exception as e:
            logger.error(f"🌿 Error publishing cultivation started event: {e}")
    
    async def publish_cultivation_completed(self, count: int, avg_emotional_essence: float):
        """🌿 Publish garden cultivation completion event to sacred channels"""
        try:
            event_data = {
                "cultivated_count": count,
                "avg_emotional_essence": round(avg_emotional_essence, 3),
                "timestamp": datetime.now().isoformat(),
                "garden": "babel_gardens"
            }
            
            await self.redis_client.publish(
                "babel.cultivation.completed",
                json.dumps(event_data)
            )
            
            logger.info(f"🌿 Published cultivation.completed event: {count} texts cultivated")
            
        except Exception as e:
            logger.error(f"🌿 Error publishing cultivation completion event: {e}")
    
    async def publish_cultivation_failed(self, error_msg: str, text_count: int = 0):
        """🌿 Publish garden cultivation failed event to sacred channels"""
        try:
            event_data = {
                "error": error_msg,
                "text_count": text_count,
                "timestamp": datetime.now().isoformat(),
                "garden": "babel_gardens"
            }
            
            await self.redis_client.publish(
                "babel.cultivation.failed",
                json.dumps(event_data)
            )
            
            logger.error(f"🌿 Published cultivation.failed event: {error_msg}")
            
        except Exception as e:
            logger.error(f"🌿 Error publishing failed event: {e}")
    
    async def handle_linguistic_synthesis_request(self, data: bytes):
        """🌿 Handle babel.linguistic.synthesis requests for cross-language unity"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🌿 Received linguistic synthesis request: {payload}")
            
            # TODO: Implement actual linguistic synthesis processing
            # This would handle requests for multilingual text processing
            
        except Exception as e:
            logger.error(f"🌿 Linguistic synthesis error: {e}")
    
    async def handle_multilingual_bridge_request(self, data: bytes):
        """🌉 Handle babel.multilingual.bridge requests for language connections"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🌉 Received multilingual bridge request: {payload}")
            
            # TODO: Implement multilingual bridge cultivation
            # This would create connections between different language embeddings
            
        except Exception as e:
            logger.error(f"🌉 Multilingual bridge error: {e}")
    
    async def handle_knowledge_cultivation_request(self, data: bytes):
        """🌱 Handle babel.knowledge.cultivation requests for garden expansion"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🌱 Received knowledge cultivation request: {payload}")
            
            # TODO: Implement knowledge garden cultivation
            # This would expand the semantic understanding gardens
            
        except Exception as e:
            logger.error(f"🌱 Knowledge cultivation error: {e}")
    
    # EPOCH II - New Handlers
    
    async def handle_sentiment_requested(self, data: bytes):
        """
        🎭 Handle sentiment.requested events
        RESILIENCE: Publish babel.sentiment.fused even on failure (score=None)
        COO: Must fuse FinBERT + Gemma sentiment with weighted average
        """
        import time
        start_time = time.time()
        
        try:
            payload = json.loads(data.decode('utf-8'))
            text = payload.get('text', '')
            request_id = payload.get('request_id', 'unknown')
            
            logger.info(f"🎭 Sentiment analysis requested: {request_id} | text: {text[:50]}...")
            
            # Step 1: Call FinBERT sentiment service
            finbert_score = None
            finbert_label = None
            try:
                response = requests.post(
                    "http://vitruvyan_api_sentiment:8003/analyze",
                    json={"text": text},
                    timeout=5
                )
                if response.status_code == 200:
                    finbert_data = response.json()
                    finbert_label = finbert_data.get('label', 'neutral')
                    finbert_score = finbert_data.get('score', 0.0)
                    logger.debug(f"🎭 FinBERT: {finbert_label} ({finbert_score:.3f})")
            except Exception as e:
                logger.warning(f"🎭 FinBERT unavailable: {e}")
            
            # Step 2: Call Gemma sentiment analysis
            gemma_score = None
            gemma_label = None
            try:
                response = requests.post(
                    "http://vitruvyan_api_gemma:8006/v1/sentiment",
                    json={"text": text},
                    timeout=5
                )
                if response.status_code == 200:
                    gemma_data = response.json()
                    gemma_label = gemma_data.get('sentiment', 'neutral')
                    gemma_score = gemma_data.get('score', 0.0)
                    logger.debug(f"🎭 Gemma: {gemma_label} ({gemma_score:.3f})")
            except Exception as e:
                logger.warning(f"🎭 Gemma unavailable: {e}")
            
            # Step 3: Fuse sentiment scores (weighted average: FinBERT 60%, Gemma 40%)
            fused_score = None
            fused_label = "unknown"
            error_msg = None
            
            if finbert_score is not None and gemma_score is not None:
                fused_score = (finbert_score * 0.6) + (gemma_score * 0.4)
                # Determine fused label
                if fused_score > 0.1:
                    fused_label = "positive"
                elif fused_score < -0.1:
                    fused_label = "negative"
                else:
                    fused_label = "neutral"
                logger.info(f"🎭 Sentiment fused: {fused_label} ({fused_score:.3f})")
            elif finbert_score is not None:
                fused_score = finbert_score
                fused_label = finbert_label
                logger.info(f"🎭 Fallback to FinBERT: {fused_label} ({fused_score:.3f})")
            elif gemma_score is not None:
                fused_score = gemma_score
                fused_label = gemma_label
                logger.info(f"🎭 Fallback to Gemma: {fused_label} ({fused_score:.3f})")
            else:
                error_msg = "Both FinBERT and Gemma unavailable"
                logger.error(f"🎭 {error_msg}")
            
            # Step 4: RESILIENCE PATTERN - Always publish babel.sentiment.fused
            fusion_ms = int((time.time() - start_time) * 1000)
            
            fused_event = {
                "request_id": request_id,
                "text": text,
                "sentiment_label": fused_label,
                "sentiment_score": fused_score,  # None on failure
                "finbert_score": finbert_score,
                "gemma_score": gemma_score,
                "fusion_weight": "finbert_0.6_gemma_0.4",
                "fusion_duration_ms": fusion_ms,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(
                "babel.sentiment.fused",
                json.dumps(fused_event)
            )
            
            logger.info(f"🎭 Published babel.sentiment.fused: {fused_label} | {fusion_ms}ms")
            
        except Exception as e:
            error_msg = f"Sentiment handler critical error: {e}"
            logger.error(f"🎭 {error_msg}")
            
            # RESILIENCE: Publish failed event with score=None
            try:
                failed_event = {
                    "request_id": payload.get('request_id', 'unknown') if 'payload' in locals() else 'unknown',
                    "text": payload.get('text', '') if 'payload' in locals() else '',
                    "sentiment_label": "error",
                    "sentiment_score": None,
                    "finbert_score": None,
                    "gemma_score": None,
                    "fusion_weight": "finbert_0.6_gemma_0.4",
                    "fusion_duration_ms": int((time.time() - start_time) * 1000),
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.redis_client.publish(
                    "babel.sentiment.fused",
                    json.dumps(failed_event)
                )
                
                logger.info(f"🎭 Published babel.sentiment.fused (failed) with score=None")
            except Exception as pub_error:
                logger.critical(f"🎭 CRITICAL: Could not publish failed event: {pub_error}")
    
    async def handle_linguistic_analysis_requested(self, data: bytes):
        """
        🗣️ Handle linguistic.analysis.requested events
        Process text with Gemma multilingual analysis and format narrative for compose_node
        """
        import time
        start_time = time.time()
        
        try:
            payload = json.loads(data.decode('utf-8'))
            text = payload.get('text', '')
            request_id = payload.get('request_id', 'unknown')
            
            logger.info(f"🗣️ Linguistic analysis requested: {request_id} | text: {text[:50]}...")
            
            # Step 1: Call Gemma for multilingual analysis
            try:
                response = requests.post(
                    "http://vitruvyan_api_gemma:8006/v1/linguistic",
                    json={
                        "text": text,
                        "detect_language": True,
                        "cultural_context": True
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    gemma_data = response.json()
                    language = gemma_data.get('language', 'unknown')
                    confidence = gemma_data.get('confidence', 0.0)
                    cultural_context = gemma_data.get('cultural_context', '')
                    narrative = gemma_data.get('narrative', text)
                    
                    logger.info(f"🗣️ Language detected: {language} ({confidence:.2f}) | cultural: {cultural_context}")
                    
                    # Step 2: Format narrative for compose_node consumption
                    interpretation_ms = int((time.time() - start_time) * 1000)
                    
                    interpreted_event = {
                        "request_id": request_id,
                        "text": text,
                        "language": language,
                        "confidence": confidence,
                        "cultural_context": cultural_context,
                        "narrative": narrative,
                        "interpretation_duration_ms": interpretation_ms,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Step 3: Publish babel.language.interpreted
                    await self.redis_client.publish(
                        "babel.language.interpreted",
                        json.dumps(interpreted_event)
                    )
                    
                    logger.info(f"🗣️ Published babel.language.interpreted: {language} | {interpretation_ms}ms")
                
                else:
                    logger.error(f"🗣️ Gemma linguistic API error: {response.status_code}")
                    raise Exception(f"Gemma API returned {response.status_code}")
                    
            except Exception as e:
                logger.error(f"🗣️ Gemma linguistic analysis failed: {e}")
                
                # Fallback: Publish minimal interpretation
                interpretation_ms = int((time.time() - start_time) * 1000)
                
                fallback_event = {
                    "request_id": request_id,
                    "text": text,
                    "language": "unknown",
                    "confidence": 0.0,
                    "cultural_context": "",
                    "narrative": text,  # Passthrough on failure
                    "interpretation_duration_ms": interpretation_ms,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.redis_client.publish(
                    "babel.language.interpreted",
                    json.dumps(fallback_event)
                )
                
                logger.info(f"🗣️ Published babel.language.interpreted (fallback) | {interpretation_ms}ms")
            
        except Exception as e:
            logger.critical(f"🗣️ CRITICAL linguistic analysis error: {e}")
    
    async def sacred_cleanup(self):
        """🌿 Sacred cleanup of divine Redis connections"""
        try:
            if self.pubsub:
                # Unsubscribe from all sacred channels
                for channel in self.sacred_channels:
                    await self.pubsub.unsubscribe(channel)
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("🌿 Sacred connections to divine realm cleaned up")
        except Exception as e:
            logger.error(f"🌿 Sacred cleanup error: {e}")

# Sacred Babel Gardens listener instance
babel_gardens_listener = BabelGardensCognitiveBusListener()