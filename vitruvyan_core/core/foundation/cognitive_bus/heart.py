"""
Synaptic Conclave - Heart Module
The beating heart of all Sacred Orders communication via Redis Pub/Sub
Port: 8012 - The nervous system of Vitruvian cognitive organism
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, asdict
import redis.asyncio as redis
import uuid

logger = logging.getLogger(__name__)

@dataclass
class SemanticEvent:
    """Sacred event following domain.intent.payload format"""
    domain: str
    intent: str
    payload: Dict[str, Any]
    timestamp: str = None
    event_id: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())

    @property
    def channel(self) -> str:
        """Get Redis channel name: domain.intent"""
        return f"{self.domain}.{self.intent}"

    def to_json(self) -> str:
        """Serialize event to JSON for Redis"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'SemanticEvent':
        """Deserialize event from JSON"""
        return cls(**json.loads(data))

class ConclaveHeart:
    """
    Synaptic Conclave - Heart Module
    The beating heart of all Sacred Orders communication via Redis Pub/Sub  
    Port: 8012 - The nervous system of Vitruvian cognitive organism
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.is_beating = False
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None

    async def awaken(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis connection and start heartbeat"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.is_beating = True
            
            # Start event listener
            await self._start_listener()
            
            logger.info("Sacred Heart awakened and beating")
            return True
            
        except Exception as e:
            logger.error(f"Failed to awaken Sacred Heart: {e}")
            self.is_beating = False
            return False

    async def _start_listener(self):
        """Start Redis pub/sub listener for incoming events"""
        try:
            self._pubsub = self.redis_client.pubsub()
            # Initialize with empty subscription to avoid connection errors
            await self._pubsub.subscribe('__conclave_init__')
            self._listener_task = asyncio.create_task(self._listen_for_events())
        except Exception as e:
            logger.error(f"Failed to start event listener: {e}")

    async def _listen_for_events(self):
        """Background task to listen for Redis events"""
        try:
            while self.is_beating:
                try:
                    message = await self._pubsub.get_message(timeout=5.0)  # PHASE 5: Reduced CPU (was 1.0s)
                    if message and message['type'] == 'message' and message['channel'] != '__conclave_init__':
                        await self._handle_incoming_event(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await asyncio.sleep(1)  # Prevent rapid error loops
                        
        except Exception as e:
            logger.error(f"Event listener crashed: {e}")
            
    async def _handle_incoming_event(self, message):
        """Process incoming Redis message and trigger callbacks"""
        try:
            channel = message['channel']
            data = message['data']
            
            event = SemanticEvent.from_json(data)
            
            # Find matching subscribers
            callbacks = []
            
            # Domain-level subscribers (domain.*)
            domain_key = f"{event.domain}.*"
            if domain_key in self.subscribers:
                callbacks.extend(self.subscribers[domain_key])
            
            # Specific event subscribers (domain.intent)
            event_key = event.channel
            if event_key in self.subscribers:
                callbacks.extend(self.subscribers[event_key])
            
            # Execute callbacks
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Callback error for {event_key}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to handle incoming event: {e}")

    async def publish_event(self, domain: str, intent: str, payload: Dict[str, Any]) -> bool:
        """Publish semantic event to Redis"""
        if not self.is_beating:
            logger.error("Heart not beating - cannot publish event")
            return False
            
        try:
            event = SemanticEvent(domain=domain, intent=intent, payload=payload)
            
            # Publish to Redis
            await self.redis_client.publish(event.channel, event.to_json())
            
            logger.info(f"Published event: {event.channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {domain}.{intent}: {e}")
            return False

    async def subscribe_to_domain(self, domain: str, callback: Callable) -> bool:
        """Subscribe to all events in a domain (domain.*)"""
        try:
            pattern = f"{domain}.*"
            
            if pattern not in self.subscribers:
                self.subscribers[pattern] = []
                # Subscribe to Redis pattern
                await self._pubsub.psubscribe(f"{domain}.*")
                
            self.subscribers[pattern].append(callback)
            logger.info(f"Subscribed to domain: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to domain {domain}: {e}")
            return False

    async def subscribe_to_event(self, domain: str, intent: str, callback: Callable) -> bool:
        """Subscribe to specific event (domain.intent)"""
        try:
            channel = f"{domain}.{intent}"
            
            if channel not in self.subscribers:
                self.subscribers[channel] = []
                # Subscribe to specific Redis channel
                await self._pubsub.subscribe(channel)
                
            self.subscribers[channel].append(callback)
            logger.info(f"Subscribed to event: {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to event {domain}.{intent}: {e}")
            return False

    async def get_vitals(self) -> Dict[str, Any]:
        """Get Heart health status"""
        try:
            redis_ping = await self.redis_client.ping() if self.redis_client else False
            
            return {
                "is_beating": self.is_beating,
                "redis_connected": redis_ping,
                "subscribers_count": len(self.subscribers),
                "active_channels": list(self.subscribers.keys()),
                "listener_active": self._listener_task and not self._listener_task.done(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get vitals: {e}")
            return {"is_beating": False, "error": str(e)}

    async def silence(self):
        """Stop the Heart gracefully"""
        self.is_beating = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
                
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Sacred Heart silenced")

# Global Heart instance
_heart_instance: Optional[ConclaveHeart] = None

async def get_heart() -> ConclaveHeart:
    """Get or create the global Heart instance"""
    global _heart_instance
    
    if _heart_instance is None:
        _heart_instance = ConclaveHeart()
        
        # Try to awaken with default settings
        import os
        redis_url = os.getenv("REDIS_URL", "redis://vitruvyan_redis:6379/0")
        await _heart_instance.awaken(redis_url)
        
    return _heart_instance

# Convenience functions
async def publish_event(domain: str, intent: str, payload: Dict[str, Any]) -> bool:
    """Convenience function to publish events."""
    heart = await get_heart()
    return await heart.publish_event(domain, intent, payload)

async def subscribe_to_domain(domain: str, callback: Callable) -> bool:
    """Convenience function to subscribe to domain events."""
    heart = await get_heart()
    return await heart.subscribe_to_domain(domain, callback)

async def subscribe_to_event(domain: str, intent: str, callback: Callable) -> bool:
    """Convenience function to subscribe to specific events."""
    heart = await get_heart()
    return await heart.subscribe_to_event(domain, intent, callback)