"""
    📯 The Herald of the Synaptic Conclave
Intelligent event routing and Order coordination

The Herald determines which Sacred Orders should receive
specific events and manages the routing logic.
"""
    
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import httpx
import structlog

from .lexicon import get_lexicon
from .heart import get_heart

logger = structlog.get_logger("conclave.herald")


class OrderEndpoint:
    """
    Represents a Sacred Order's communication endpoint.
    """
    def __init__(self, name: str, port: int, health_endpoint: str = "/health", container_name: str = None):
        self.name = name
        self.port = port
        # Use Docker container name if provided, otherwise fallback to localhost
        if container_name:
            self.base_url = f"http://{container_name}:{port}"
        else:
            self.base_url = f"http://localhost:{port}"
        self.health_endpoint = health_endpoint
        self.is_alive = False
        self.last_heartbeat: Optional[datetime] = None


class ConclaveHerald:
    """
    The Herald manages routing of semantic events to appropriate Orders.
    """
    
    def __init__(self):
        self.orders: Dict[str, OrderEndpoint] = {}
        self.routing_rules: Dict[str, Set[str]] = {}
        self.lexicon = get_lexicon()
        self._initialize_orders()
        self._initialize_routing_rules()
    
    def _initialize_orders(self):
        """
        Initialize all known Sacred Order endpoints.
        Uses Docker container names for proper inter-container communication.
        Ports verified from docker-compose.yml and actual container bindings.
        """
        self.orders = {
            "babel": OrderEndpoint("babel", 8009, "/health", "vitruvyan_babel_gardens"),
            "memory": OrderEndpoint("memory", 8016, "/health/memory", "vitruvyan_memory_orders"),  # ✅ Fixed: 8016 not 8013
            "orthodoxy": OrderEndpoint("orthodoxy", 8006, "/divine-health", "vitruvyan_api_orthodoxy_wardens"),
            "vault": OrderEndpoint("vault", 8007, "/health", "vitruvyan_vault_keepers"),
            "semantic": OrderEndpoint("semantic", 8002, "/health", "vitruvyan_api_semantic"),
            "neural": OrderEndpoint("neural", 8003, "/health", "vitruvyan_api_neural"),
            "crewai": OrderEndpoint("crewai", 8005, "/health", "vitruvyan_api_crewai"),
            "graph": OrderEndpoint("graph", 8004, "/health", "vitruvyan_api_graph"),
            "conclave": OrderEndpoint("conclave", 8012, "/health/conclave", "vitruvyan_api_conclave"),
            "codex": OrderEndpoint("codex", 8008, "/health", "vitruvyan_codex_hunters"),  # ✅ Fixed: 8008 not 8011
        }
    
    def _initialize_routing_rules(self):
        """
        Initialize routing rules - which Orders should receive which events.
        """
        self.routing_rules = {
            # Babel Gardens events (EPOCH II Enhanced)
            "babel.sentiment.requested": {"babel"},
            "babel.sentiment.fused": {"orthodoxy", "neural", "semantic", "compose"},
            "babel.linguistic.analysis.requested": {"babel"},
            "babel.language.interpreted": {"semantic", "compose"},
            "babel.fusion.completed": {"orthodoxy", "neural", "semantic"},
            "babel.fusion.failed": {"orthodoxy"},
            "babel.sentiment.shifted": {"sentiment", "orthodoxy"},
            "babel.language.detected": {"semantic"},
            
            # Memory Orders events (EPOCH II)
            "memory.write.requested": {"memory"},
            "memory.write.completed": {"orthodoxy", "compose"},
            "memory.write.failed": {"orthodoxy"},
            "memory.read.requested": {"memory"},
            "memory.read.fulfilled": {"compose", "orthodoxy"},
            "memory.read.failed": {"orthodoxy"},
            "memory.vector.match.requested": {"memory"},
            "memory.vector.match.fulfilled": {"compose", "orthodoxy"},
            "memory.vector.match.failed": {"orthodoxy"},
            "memory.coherence.validated": {"orthodoxy"},
            "memory.coherence.failed": {"orthodoxy"},
            
            # Orthodoxy Wardens events
            "orthodoxy.heresy.detected": {"conclave", "system"},
            "orthodoxy.healing.completed": {"babel", "neural", "semantic"},
            "orthodoxy.validation.requested": {"babel", "neural", "memory"},
            
            # Conclave events
            "conclave.heartbeat": {"orthodoxy"},
            "conclave.event.failed": {"orthodoxy"},
            
            # System events
            "system.health.critical": {"orthodoxy", "conclave"},
            "system.startup.completed": {"babel", "orthodoxy", "neural", "semantic", "memory"},
            
            # Neural Engine events
            "neural.ranking.completed": {"semantic", "crewai"},
            "neural.model.updated": {"babel", "orthodoxy"},
            
            # Semantic Engine events
            "semantic.analysis.completed": {"neural", "crewai"},
            "semantic.intent.classified": {"graph", "crewai"},
            
            # CrewAI events
            "crew.analysis.completed": {"semantic", "neural"},
            "crew.strategy.generated": {"graph", "orthodoxy"},
            
            # Graph/LangGraph events
            "graph.node.entered": {"conclave"},
            "graph.flow.completed": {"orthodoxy", "crewai"}
        }
    
    async def route_event(self, domain: str, intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a semantic event to appropriate Orders.
        
        Returns routing results with success/failure information.
        """
        event_key = f"{domain}.{intent}"
        
        # Get target Orders for this event
        target_orders = self.routing_rules.get(event_key, set())
        
        if not target_orders:
            logger.warning(
                "📯 No routing rules found for event",
                event_key=event_key,
                available_rules=list(self.routing_rules.keys())[:5]
            )
            return {
                "routed": False,
                "reason": "no_routing_rules",
                "target_orders": [],
                "results": {}
            }
        
        # Route to each target Order
        routing_results = {}
        successful_routes = 0
        
        for order_name in target_orders:
            if order_name not in self.orders:
                routing_results[order_name] = {
                    "success": False,
                    "error": "order_not_configured"
                }
                continue
            
            try:
                result = await self._send_event_to_order(
                    self.orders[order_name], 
                    domain, 
                    intent, 
                    payload
                )
                routing_results[order_name] = result
                
                if result.get("success", False):
                    successful_routes += 1
                    
            except Exception as e:
                routing_results[order_name] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(
                    "📯 Failed to route to Order",
                    order=order_name,
                    event_key=event_key,
                    error=str(e)
                )
        
        # Publish routing completion event
        heart = await get_heart()
        await heart.publish_event("conclave", "event.routed", {
            "original_domain": domain,
            "original_intent": intent,
            "target_orders": list(target_orders),
            "successful_routes": successful_routes,
            "total_targets": len(target_orders),
            "routing_time_ms": 0  # TODO: Add timing
        })
        
        logger.info(
            "📯 Event routing completed",
            event_key=event_key,
            successful_routes=successful_routes,
            total_targets=len(target_orders)
        )
        
        return {
            "routed": True,
            "successful_routes": successful_routes,
            "total_targets": len(target_orders),
            "target_orders": list(target_orders),
            "results": routing_results
        }
    
    async def _send_event_to_order(
        self, 
        order: OrderEndpoint, 
        domain: str, 
        intent: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send semantic event to a specific Order.
        """
        try:
            # Prepare event payload
            event_payload = {
                "domain": domain,
                "intent": intent,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "conclave.herald"
            }
            
            # Try to send to Order's event endpoint first
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try /events/receive endpoint first (preferred)
                try:
                    response = await client.post(
                        f"{order.base_url}/events/receive",
                        json=event_payload
                    )
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "method": "events_endpoint",
                            "response_code": response.status_code
                        }
                        
                except httpx.RequestError:
                    pass  # Try alternative methods
                
                # Try webhook endpoint as fallback
                try:
                    response = await client.post(
                        f"{order.base_url}/webhook/conclave",
                        json=event_payload
                    )
                    
                    if response.status_code in [200, 202]:
                        return {
                            "success": True,
                            "method": "webhook_endpoint", 
                            "response_code": response.status_code
                        }
                        
                except httpx.RequestError:
                    pass
                
                # Log the event for the Order to poll later
                logger.info(
                    "📯 Order unreachable, logging event for polling",
                    order=order.name,
                    event=f"{domain}.{intent}"
                )
                
                return {
                    "success": False,
                    "method": "unreachable",
                    "fallback": "event_logged_for_polling"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_order_health(self) -> Dict[str, Any]:
        """
        Check health status of all Sacred Orders.
        """
        health_results = {}
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            for order_name, order in self.orders.items():
                try:
                    response = await client.get(f"{order.base_url}{order.health_endpoint}")
                    
                    if response.status_code == 200:
                        order.is_alive = True
                        order.last_heartbeat = datetime.utcnow()
                        health_results[order_name] = {
                            "status": "alive",
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "last_heartbeat": order.last_heartbeat.isoformat()
                        }
                    else:
                        order.is_alive = False
                        health_results[order_name] = {
                            "status": "unhealthy",
                            "status_code": response.status_code
                        }
                        
                except Exception as e:
                    order.is_alive = False
                    health_results[order_name] = {
                        "status": "unreachable",
                        "error": str(e)
                    }
        
        return health_results
    
    async def get_routing_map(self) -> Dict[str, Any]:
        """
        Get the complete routing map for documentation.
        """
        return {
            "routing_rules": {
                event: list(orders) for event, orders in self.routing_rules.items()
            },
            "configured_orders": {
                name: {
                    "port": order.port,
                    "base_url": order.base_url,
                    "is_alive": order.is_alive,
                    "last_heartbeat": order.last_heartbeat.isoformat() if order.last_heartbeat else None
                }
                for name, order in self.orders.items()
            },
            "total_rules": len(self.routing_rules),
            "total_orders": len(self.orders)
        }
    
    def add_routing_rule(self, event_key: str, target_orders: Set[str]):
        """
        Add a new routing rule.
        """
        self.routing_rules[event_key] = target_orders
        logger.info(
            "📯 Added new routing rule",
            event_key=event_key,
            target_orders=list(target_orders)
        )
    
    def remove_routing_rule(self, event_key: str):
        """
        Remove a routing rule.
        """
        if event_key in self.routing_rules:
            del self.routing_rules[event_key]
            logger.info("📯 Removed routing rule", event_key=event_key)


# Global Herald instance
_herald: Optional[ConclaveHerald] = None

async def get_herald() -> ConclaveHerald:
    """
    Get the global Herald instance.
    """
    global _herald
    if _herald is None:
        _herald = ConclaveHerald()
    return _herald