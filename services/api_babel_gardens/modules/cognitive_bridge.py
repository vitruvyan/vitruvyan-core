# api_gemma_cognitive/modules/cognitive_bridge.py
"""
🌉 Cognitive Bridge Module
Intelligent routing and integration hub for the cognitive layer
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Tuple, Callable
import json
from datetime import datetime, timedelta
from enum import Enum
import random
from dataclasses import dataclass, field

from ..shared import GemmaServiceBase, model_manager, vector_cache, integrity_watcher
from ..schemas import (
    EventRequest, RoutingStrategy, RoutingRequest, Priority, LanguageCode
)

logger = logging.getLogger(__name__)

@dataclass
class RoutingRule:
    """Rule for routing requests"""
    condition: Callable[[Dict[str, Any]], bool]
    target_module: str
    weight: float = 1.0
    description: str = ""

@dataclass
class ServiceEndpoint:
    """External service endpoint configuration"""
    name: str
    url: str
    health_check_path: str = "/health"
    timeout: float = 30.0
    retry_count: int = 3
    enabled: bool = True
    last_health_check: Optional[datetime] = None
    is_healthy: bool = True

class CognitiveBridgeModule(GemmaServiceBase):
    """
    🧠 Intelligent coordination hub for the cognitive layer
    Handles routing, event management, and service orchestration
    """
    
    def __init__(self):
        super().__init__("cognitive_bridge")
        self.name = "CognitiveBridge"
        self.version = "1.0.0"
        self.event_queue = asyncio.Queue()
        self.routing_rules: List[RoutingRule] = []
        self.service_endpoints: Dict[str, ServiceEndpoint] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_event_history = 1000
        self.load_balancer_state = {}
        
        # Request routing statistics
        self.routing_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "route_distribution": {},
            "average_response_time": 0.0
        }
    
    async def _initialize_service(self):
        """Service-specific initialization for cognitive bridge"""
        pass
    
    async def initialize(self, model_manager, vector_cache, integrity_watcher):
        """Initialize cognitive bridge module"""
        await super().initialize(model_manager, vector_cache, integrity_watcher)
        
        # Initialize default routing rules
        await self._setup_default_routing_rules()
        
        # Initialize service endpoints
        await self._setup_service_endpoints()
        
        # Start event processor
        self._event_processor_task = asyncio.create_task(self._process_events())
        
        logger.info("🌉 Cognitive Bridge Module initialized")
    
    async def handle_event(self, request: EventRequest) -> Dict[str, Any]:
        """
        Handle cognitive events
        
        Args:
            request: Event request with type and payload
            
        Returns:
            Event handling result
        """
        try:
            start_time = datetime.now()
            
            # Validate event
            if not request.event_type or not request.payload:
                return {
                    "status": "error",
                    "error": "Invalid event: missing type or payload"
                }
            
            # Add event to queue for processing
            event_data = {
                "event_type": request.event_type,
                "payload": request.payload,
                "priority": request.priority.value,
                "correlation_id": request.correlation_id,
                "timestamp": start_time.isoformat(),
                "status": "queued"
            }
            
            await self.event_queue.put(event_data)
            
            # For high priority events, process immediately
            if request.priority in [Priority.HIGH, Priority.CRITICAL]:
                await self._process_single_event(event_data)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "accepted",
                "event_id": event_data.get("correlation_id", "unknown"),
                "processing_time_ms": processing_time,
                "queue_position": self.event_queue.qsize()
            }
            
        except Exception as e:
            logger.error(f"❌ Event handling error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def route_request(self, request: RoutingRequest) -> Dict[str, Any]:
        """
        Route request to appropriate service/module
        
        Args:
            request: Routing request with content and strategy
            
        Returns:
            Routing result with target and reasoning
        """
        try:
            start_time = datetime.now()
            self.routing_stats["total_requests"] += 1
            
            # Analyze request content
            content_analysis = await self._analyze_request_content(request.content)
            
            # Apply routing strategy
            if request.strategy == RoutingStrategy.CONTENT_BASED:
                route_result = await self._route_by_content(content_analysis, request.content)
            elif request.strategy == RoutingStrategy.USER_BASED:
                route_result = await self._route_by_user(request.user_context, content_analysis)
            elif request.strategy == RoutingStrategy.LOAD_BALANCED:
                route_result = await self._route_by_load_balance(content_analysis)
            elif request.strategy == RoutingStrategy.INTELLIGENT:
                route_result = await self._route_intelligently(content_analysis, request.user_context, request.content)
            else:
                route_result = await self._route_by_content(content_analysis, request.content)
            
            # Update statistics
            if route_result.get("status") == "success":
                self.routing_stats["successful_routes"] += 1
                target = route_result.get("target", "unknown")
                self.routing_stats["route_distribution"][target] = self.routing_stats["route_distribution"].get(target, 0) + 1
            else:
                self.routing_stats["failed_routes"] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.routing_stats["average_response_time"] = (
                (self.routing_stats["average_response_time"] * (self.routing_stats["total_requests"] - 1) + processing_time) /
                self.routing_stats["total_requests"]
            )
            
            route_result["processing_time_ms"] = processing_time
            route_result["strategy_used"] = request.strategy.value
            
            return route_result
            
        except Exception as e:
            logger.error(f"❌ Request routing error: {str(e)}")
            self.routing_stats["failed_routes"] += 1
            return {"status": "error", "error": str(e)}
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all connected services"""
        try:
            service_health = {}
            
            for service_name, endpoint in self.service_endpoints.items():
                health_status = await self._check_service_health(endpoint)
                service_health[service_name] = {
                    "url": endpoint.url,
                    "healthy": health_status["healthy"],
                    "response_time_ms": health_status.get("response_time_ms", 0),
                    "last_check": health_status.get("timestamp", "never"),
                    "enabled": endpoint.enabled
                }
            
            return {
                "status": "success",
                "services": service_health,
                "total_services": len(self.service_endpoints),
                "healthy_services": sum(1 for s in service_health.values() if s["healthy"]),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Service health check error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_routing_analytics(self) -> Dict[str, Any]:
        """Get routing analytics and statistics"""
        try:
            # Calculate success rate
            total_requests = self.routing_stats["total_requests"]
            success_rate = (self.routing_stats["successful_routes"] / total_requests) if total_requests > 0 else 0.0
            
            # Recent events summary
            recent_events = [e for e in self.event_history if 
                           (datetime.now() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 3600]
            
            return {
                "status": "success",
                "routing_statistics": {
                    **self.routing_stats,
                    "success_rate": round(success_rate, 3),
                    "error_rate": round(1 - success_rate, 3)
                },
                "recent_events": {
                    "last_hour_count": len(recent_events),
                    "event_types": list(set(e["event_type"] for e in recent_events))
                },
                "queue_status": {
                    "current_size": self.event_queue.qsize(),
                    "max_size": 1000  # Default queue size
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Analytics error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    # ===========================
    # PRIVATE ROUTING METHODS
    # ===========================
    
    async def _analyze_request_content(self, content: str) -> Dict[str, Any]:
        """Analyze request content for routing decisions"""
        
        analysis = {
            "content_type": "text",
            "language": "en",
            "topics": [],
            "intent": "unknown",
            "complexity": "medium",
            "urgency": "normal"
        }
        
        content_lower = content.lower()
        
        # Detect content type and intent
        if any(word in content_lower for word in ["embed", "vector", "similarity", "semantic"]):
            analysis["intent"] = "embedding"
            analysis["suggested_module"] = "embedding_engine"
        elif any(word in content_lower for word in ["sentiment", "emotion", "feeling", "opinion"]):
            analysis["intent"] = "sentiment"
            analysis["suggested_module"] = "sentiment_fusion"
        elif any(word in content_lower for word in ["profile", "user", "preference", "personalize"]):
            analysis["intent"] = "profile"
            analysis["suggested_module"] = "profile_processor"
        else:
            analysis["intent"] = "general"
        
        # Detect topics
        topic_keywords = {
            "trading": ["trading", "buy", "sell", "position"],
            "analysis": ["analysis", "chart", "technical", "fundamental"],
            "market": ["market", "entity", "index", "sector"],
            "risk": ["risk", "volatility", "hedge"],
            "news": ["news", "earnings", "announcement"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                analysis["topics"].append(topic)
        
        # Detect complexity
        if any(word in content_lower for word in ["simple", "basic", "explain"]):
            analysis["complexity"] = "simple"
        elif any(word in content_lower for word in ["advanced", "technical", "sophisticated"]):
            analysis["complexity"] = "advanced"
        
        # Detect urgency
        if any(word in content_lower for word in ["urgent", "critical", "emergency", "now"]):
            analysis["urgency"] = "high"
        elif any(word in content_lower for word in ["later", "when", "sometime"]):
            analysis["urgency"] = "low"
        
        return analysis
    
    async def _route_by_content(self, content_analysis: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Route based on content analysis"""
        
        intent = content_analysis["intent"]
        suggested_module = content_analysis.get("suggested_module", "embedding_engine")
        
        # Apply routing rules
        for rule in self.routing_rules:
            if rule.condition(content_analysis):
                return {
                    "status": "success",
                    "target": rule.target_module,
                    "confidence": 0.8,
                    "reasoning": f"Content-based routing: {rule.description}",
                    "analysis": content_analysis
                }
        
        # Fallback to suggested module
        return {
            "status": "success",
            "target": suggested_module,
            "confidence": 0.6,
            "reasoning": f"Default routing based on intent: {intent}",
            "analysis": content_analysis
        }
    
    async def _route_by_user(self, user_context: Dict[str, Any], content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Route based on user context"""
        
        if not user_context:
            return await self._route_by_content(content_analysis, "")
        
        user_id = user_context.get("user_id")
        if user_id:
            # Try to get user profile for personalized routing
            user_profile = await vector_cache.get_user_profile(user_id)
            if user_profile:
                complexity_level = user_profile.get("complexity_level", "medium")
                top_interests = list(user_profile.get("topic_interests", {}).keys())[:3]
                
                # Route based on user preferences
                if complexity_level == "expert" and content_analysis["intent"] == "sentiment":
                    target = "sentiment_fusion"
                elif top_interests and "trading" in top_interests:
                    target = "embedding_engine"  # Trading-focused embeddings
                else:
                    target = content_analysis.get("suggested_module", "embedding_engine")
                
                return {
                    "status": "success",
                    "target": target,
                    "confidence": 0.9,
                    "reasoning": f"User-based routing for complexity: {complexity_level}, interests: {top_interests}",
                    "user_profile": {"complexity": complexity_level, "interests": top_interests}
                }
        
        # Fallback to content-based routing
        return await self._route_by_content(content_analysis, "")
    
    async def _route_by_load_balance(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Route based on load balancing"""
        
        # Simple round-robin load balancing
        modules = ["embedding_engine", "sentiment_fusion", "profile_processor"]
        
        # Update load balancer state
        if "current_module_index" not in self.load_balancer_state:
            self.load_balancer_state["current_module_index"] = 0
        
        current_index = self.load_balancer_state["current_module_index"]
        target = modules[current_index % len(modules)]
        
        self.load_balancer_state["current_module_index"] = (current_index + 1) % len(modules)
        
        return {
            "status": "success",
            "target": target,
            "confidence": 0.7,
            "reasoning": f"Load-balanced routing (round-robin): {target}",
            "load_balance_index": current_index
        }
    
    async def _route_intelligently(
        self, content_analysis: Dict[str, Any], user_context: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """Intelligent routing combining multiple factors"""
        
        # Start with content-based routing
        content_route = await self._route_by_content(content_analysis, content)
        
        # Enhance with user context if available
        if user_context:
            user_route = await self._route_by_user(user_context, content_analysis)
            
            # Combine routing decisions
            if user_route["confidence"] > content_route["confidence"]:
                base_route = user_route
                base_route["reasoning"] += f" (enhanced from content-based: {content_route['target']})"
            else:
                base_route = content_route
        else:
            base_route = content_route
        
        # Apply intelligent enhancements
        urgency = content_analysis.get("urgency", "normal")
        complexity = content_analysis.get("complexity", "medium")
        
        # Adjust based on system load and health
        service_health = await self.get_service_health()
        healthy_services = [name for name, status in service_health.get("services", {}).items() if status["healthy"]]
        
        if base_route["target"] not in healthy_services:
            # Fallback to healthy service
            fallback_target = healthy_services[0] if healthy_services else "embedding_engine"
            base_route["target"] = fallback_target
            base_route["reasoning"] += f" (fallback due to service health)"
            base_route["confidence"] *= 0.8
        
        # Boost confidence for intelligent routing
        base_route["confidence"] = min(1.0, base_route["confidence"] * 1.1)
        base_route["reasoning"] = f"Intelligent routing: {base_route['reasoning']}"
        
        return base_route
    
    # ===========================
    # EVENT PROCESSING
    # ===========================
    
    async def _process_events(self):
        """Background event processor"""
        while True:
            try:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                    await self._process_single_event(event)
                except asyncio.TimeoutError:
                    continue  # No events to process
                    
            except Exception as e:
                logger.error(f"❌ Event processing error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_single_event(self, event_data: Dict[str, Any]):
        """Process a single event"""
        try:
            event_type = event_data["event_type"]
            payload = event_data["payload"]
            
            # Update event status
            event_data["status"] = "processing"
            event_data["processed_at"] = datetime.now().isoformat()
            
            # Route event based on type
            if event_type == "integrity_check":
                await self._handle_integrity_event(payload)
            elif event_type == "cache_invalidation":
                await self._handle_cache_event(payload)
            elif event_type == "model_reload":
                await self._handle_model_event(payload)
            elif event_type == "health_check":
                await self._handle_health_event(payload)
            else:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
            
            event_data["status"] = "completed"
            
        except Exception as e:
            logger.error(f"❌ Event processing error: {str(e)}")
            event_data["status"] = "failed"
            event_data["error"] = str(e)
        
        finally:
            # Add to history
            self.event_history.append(event_data)
            if len(self.event_history) > self.max_event_history:
                self.event_history = self.event_history[-self.max_event_history:]
    
    async def _handle_integrity_event(self, payload: Dict[str, Any]):
        """Handle integrity check events"""
        check_type = payload.get("check_type", "general")
        logger.info(f"🔍 Processing integrity check: {check_type}")
        # Integration with integrity watcher
        await integrity_watcher.run_all_checks()
    
    async def _handle_cache_event(self, payload: Dict[str, Any]):
        """Handle cache-related events"""
        action = payload.get("action", "refresh")
        pattern = payload.get("pattern", "*")
        logger.info(f"🗃️ Processing cache event: {action} for pattern {pattern}")
        
        if action == "invalidate":
            await vector_cache.invalidate_pattern(pattern)
    
    async def _handle_model_event(self, payload: Dict[str, Any]):
        """Handle model-related events"""
        model_key = payload.get("model_key", "all")
        action = payload.get("action", "reload")
        logger.info(f"🧠 Processing model event: {action} for {model_key}")
        
        if action == "reload" and model_key != "all":
            await model_manager.get_model(model_key, force_load=True)
    
    async def _handle_health_event(self, payload: Dict[str, Any]):
        """Handle health check events"""
        target = payload.get("target", "all")
        logger.info(f"❤️ Processing health check for: {target}")
        # Trigger health checks as needed
    
    # ===========================
    # SETUP AND CONFIGURATION
    # ===========================
    
    async def _setup_default_routing_rules(self):
        """Setup default routing rules"""
        
        # Embedding-related requests
        self.routing_rules.append(RoutingRule(
            condition=lambda ctx: ctx.get("intent") == "embedding" or "embed" in ctx.get("content", "").lower(),
            target_module="embedding_engine",
            weight=1.0,
            description="Embedding or similarity requests"
        ))
        
        # Sentiment-related requests
        self.routing_rules.append(RoutingRule(
            condition=lambda ctx: ctx.get("intent") == "sentiment" or any(
                word in ctx.get("content", "").lower() for word in ["sentiment", "emotion", "feeling"]
            ),
            target_module="sentiment_fusion",
            weight=1.0,
            description="Sentiment analysis requests"
        ))
        
        # Profile-related requests
        self.routing_rules.append(RoutingRule(
            condition=lambda ctx: ctx.get("intent") == "profile" or any(
                word in ctx.get("content", "").lower() for word in ["profile", "user", "personalize"]
            ),
            target_module="profile_processor",
            weight=1.0,
            description="User profiling and personalization requests"
        ))
        
        logger.info(f"📋 Setup {len(self.routing_rules)} default routing rules")
    
    async def _setup_service_endpoints(self):
        """Setup external service endpoints"""
        
        # Add Vitruvyan services
        self.service_endpoints["semantic_engine"] = ServiceEndpoint(
            name="semantic_engine",
            url=os.getenv("SEMANTIC_ENGINE_URL", "http://localhost:8003"),
            health_check_path="/health"
        )
        
        self.service_endpoints["oracle"] = ServiceEndpoint(
            name="oracle", 
            url=os.getenv("NEURAL_ENGINE_URL", "http://localhost:8004"),
            health_check_path="/health"
        )
        
        self.service_endpoints["crewai_agents"] = ServiceEndpoint(
            name="crewai_agents",
            url=os.getenv("CREWAI_URL", "http://localhost:8002"),
            health_check_path="/health"
        )
        
        logger.info(f"🔗 Setup {len(self.service_endpoints)} service endpoints")
    
    async def _check_service_health(self, endpoint: ServiceEndpoint) -> Dict[str, Any]:
        """Check health of a service endpoint"""
        
        if not endpoint.enabled:
            return {"healthy": False, "reason": "disabled"}
        
        try:
            start_time = datetime.now()
            # In practice, make HTTP request to health endpoint
            # For now, simulate health check
            await asyncio.sleep(0.1)  # Simulate network call
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            endpoint.last_health_check = datetime.now()
            endpoint.is_healthy = True
            
            return {
                "healthy": True,
                "response_time_ms": response_time,
                "timestamp": endpoint.last_health_check.isoformat()
            }
            
        except Exception as e:
            endpoint.is_healthy = False
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cognitive bridge module"""
        try:
            # Check event processing
            event_processor_healthy = self._event_processor_task and not self._event_processor_task.done()
            
            # Check service endpoints
            service_health = await self.get_service_health()
            healthy_services = service_health.get("healthy_services", 0)
            total_services = service_health.get("total_services", 0)
            
            return {
                "status": "healthy",
                "module": self.name,
                "version": self.version,
                "event_processor": "running" if event_processor_healthy else "stopped",
                "queue_size": self.event_queue.qsize(),
                "routing_rules": len(self.routing_rules),
                "service_endpoints": f"{healthy_services}/{total_services}",
                "routing_stats": self.routing_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "module": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, '_event_processor_task'):
            self._event_processor_task.cancel()
            try:
                await self._event_processor_task
            except asyncio.CancelledError:
                pass
        
        await super().cleanup()
        logger.info("🌉 Cognitive Bridge cleaned up")