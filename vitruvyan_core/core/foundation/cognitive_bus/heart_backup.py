"""
    Sacred The Heart of the Synaptic Conclave
Sacred Pub/Sub Engine for Order Communication

The Heart is the central nervous system that allows all Sacred Orders
to communicate through semantic events in the sacred language.
"""
    
import asyncio
import json
import logging
import redis.asyncio as redis
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
import structlog

# Configure structured logging
logger = structlog.get_logger("conclave.heart")

class ConclaveHeart:
    """
    Synaptic Conclave - Heart Module
    The beating heart of all Sacred Orders communication via Redis Pub/Sub
    Port: 8012 - The nervous system of Vitruvian cognitive organism
    """
    Manages semantic event publication and subscription.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.is_beating = False
        
    async def awaken(self) -> bool:
        """
        Awaken the Heart - establish Redis connection
        """
        try:
            self.redis_client = redis.from_url(
                self.redis_url, 
                decode_responses=True,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.is_beating = True
            
            logger.info("💓 Conclave Heart awakened", redis_url=self.redis_url)
            return True
            
        except Exception as e:
            logger.error("💔 Heart failed to awaken", error=str(e))
            return False
    
    async def rest(self):
        """
        Put the Heart to rest - cleanup connections
        """
        self.is_beating = False
        
        if self.pubsub:
            await self.pubsub.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("😴 Conclave Heart at rest")
    
    async def publish_event(self, domain: str, intent: str, payload: Dict[str, Any]) -> bool:
        """
        Publish a semantic event in sacred language format.
        
        Args:
            domain: Sacred Order domain (babel, orthodoxy, codex, vault, crew, system)
            intent: Specific intent within domain (fusion.completed, heresy.detected, etc.)
            payload: Event data dictionary
            
        Returns:
            True if event published successfully
            
        Example:
            await heart.publish_event("babel", "fusion.completed", {
                "phrase_id": 12345,
                "language": "arabic",
                "dimensions": 384,
                "processing_time_ms": 27.3
            })
        """
        if not self.is_beating:
            logger.error("💔 Heart not beating - cannot publish event")
            return False
            
        try:
            # Sacred language format: domain.intent
            channel = f"{domain}.{intent}"
            
            # Enrich payload with metadata
            enriched_payload = {
                "domain": domain,
                "intent": intent,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "conclave.heart",
                "event_id": f"{domain}_{intent}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Publish to Redis
            subscribers_count = await self.redis_client.publish(
                channel, 
                json.dumps(enriched_payload)
            )
            
            logger.info(
                "📢 Event published",
                channel=channel,
                subscribers=subscribers_count,
                event_id=enriched_payload["event_id"],
                payload_keys=list(payload.keys())
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "💔 Failed to publish event",
                domain=domain,
                intent=intent,
                error=str(e)
            )
            return False
    
    async def subscribe_to_domain(self, domain: str, callback: Callable) -> bool:
        """
        Subscribe to all events from a specific Sacred Order domain.
        
        Args:
            domain: Sacred Order domain to listen to
            callback: Async function to handle events
            
        Returns:
            True if subscription successful
        """
        if not self.is_beating:
            logger.error("💔 Heart not beating - cannot subscribe")
            return False
            
        try:
            pattern = f"{domain}.*"
            
            if domain not in self.subscribers:
                self.subscribers[domain] = []
                
            self.subscribers[domain].append(callback)
            
            # Subscribe to pattern
            await self.pubsub.psubscribe(pattern)
            
            logger.info(
                "👂 Subscribed to domain",
                domain=domain,
                pattern=pattern,
                callback_count=len(self.subscribers[domain])
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "💔 Failed to subscribe to domain",
                domain=domain,
                error=str(e)
            )
            return False
    
    async def subscribe_to_event(self, domain: str, intent: str, callback: Callable) -> bool:
        """
        Subscribe to specific semantic event.
        
        Args:
            domain: Sacred Order domain
            intent: Specific intent
            callback: Async function to handle the event
        """
        if not self.is_beating:
            logger.error("💔 Heart not beating - cannot subscribe")
            return False
            
        try:
            channel = f"{domain}.{intent}"
            
            if channel not in self.subscribers:
                self.subscribers[channel] = []
                
            self.subscribers[channel].append(callback)
            
            # Subscribe to specific channel
            await self.pubsub.subscribe(channel)
            
            logger.info(
                "👂 Subscribed to specific event",
                channel=channel,
                callback_count=len(self.subscribers[channel])
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "💔 Failed to subscribe to event",
                domain=domain,
                intent=intent,
                error=str(e)
            )
            return False
    
    async def listen_to_heartbeat(self):
        """
        Main listening loop for processing incoming events.
        This should run as a background task.
        """
        if not self.is_beating or not self.pubsub:
            logger.error("💔 Heart not ready for listening")
            return
            
        logger.info("👂 Heart started listening to sacred communications")
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] in ['message', 'pmessage']:
                    await self._process_message(message)
                    
        except Exception as e:
            logger.error("💔 Heart listening interrupted", error=str(e))
    
    async def _process_message(self, message: Dict[str, Any]):
        """
        Process incoming semantic event message.
        """
        try:
            # Parse the sacred message
            event_data = json.loads(message['data'])
            channel = message.get('channel', '')
            
            domain = event_data.get('domain', '')
            intent = event_data.get('intent', '')
            
            logger.info(
                "📨 Processing sacred message",
                channel=channel,
                domain=domain,
                intent=intent,
                event_id=event_data.get('event_id', 'unknown')
            )
            
            # Find and execute callbacks
            callbacks_executed = 0
            
            # Check domain subscribers
            if domain in self.subscribers:
                for callback in self.subscribers[domain]:
                    try:
                        await callback(event_data)
                        callbacks_executed += 1
                    except Exception as e:
                        logger.error(
                            "💔 Callback execution failed",
                            domain=domain,
                            error=str(e)
                        )
            
            # Check specific event subscribers
            if channel in self.subscribers:
                for callback in self.subscribers[channel]:
                    try:
                        await callback(event_data)
                        callbacks_executed += 1
                    except Exception as e:
                        logger.error(
                            "💔 Callback execution failed",
                            channel=channel,
                            error=str(e)
                        )
            
            logger.info(
                "✅ Message processed",
                channel=channel,
                callbacks_executed=callbacks_executed
            )
            
        except Exception as e:
            logger.error(
                "💔 Failed to process message",
                message_type=message.get('type', 'unknown'),
                error=str(e)
            )
    
    async def get_vital_signs(self) -> Dict[str, Any]:
        """
        Get Heart vital signs and status.
        """
        vital_signs = {
            "is_beating": self.is_beating,
            "redis_connected": False,
            "active_subscriptions": len(self.subscribers),
            "subscriber_details": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
                vital_signs["redis_connected"] = True
                
                # Get Redis info
                info = await self.redis_client.info()
                vital_signs["redis_info"] = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                }
                
            except Exception as e:
                vital_signs["redis_error"] = str(e)
        
        # Subscriber details
        for key, callbacks in self.subscribers.items():
            vital_signs["subscriber_details"][key] = len(callbacks)
        
        return vital_signs


# Global Heart instance
_heart: Optional[ConclaveHeart] = None

async def get_heart() -> ConclaveHeart:
    """
    Get the global Heart instance.
    """
    global _heart
    if _heart is None:
        _heart = ConclaveHeart()
        await _heart.awaken()
    return _heart

async def publish_event(domain: str, intent: str, payload: Dict[str, Any]) -> bool:
    """
    Convenience function to publish events.
    """
    heart = await get_heart()
    return await heart.publish_event(domain, intent, payload)

async def subscribe_to_domain(domain: str, callback: Callable) -> bool:
    """
    Convenience function to subscribe to domain events.
    """
    heart = await get_heart()
    return await heart.subscribe_to_domain(domain, callback)

async def subscribe_to_event(domain: str, intent: str, callback: Callable) -> bool:
    """
    Convenience function to subscribe to specific events.
    """
    heart = await get_heart()
    return await heart.subscribe_to_event(domain, intent, callback)