#!/usr/bin/env python3
"""
    Vitruvyan Redis Bus Client
==========================

Redis Pub/Sub client for the Cognitive Bus system. Handles event publishing
and subscription for inter-service communication following the standard
domain:intent:payload schema.

This client ensures proper event routing between Codex Hunters, LangGraph,
Audit Engine, and other system components.

Author: Vitruvyan Development Team
Created: 2025-01-14
"""
    
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
import redis
from redis.exceptions import ConnectionError, TimeoutError
import asyncio
import threading


@dataclass
class CognitiveEvent:
    """Standard event structure for Cognitive Bus"""
    event_type: str      # domain.intent (e.g., "codex.audit.alert")
    emitter: str         # Source agent/service
    target: str          # Target agent/service (or "broadcast")
    payload: Dict[str, Any]  # Event data
    timestamp: str       # ISO timestamp
    correlation_id: Optional[str] = None  # For tracking event chains
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitiveEvent':
        """Create event from dictionary"""
        return cls(**data)


class RedisBusClient:
    """
    Redis client for Cognitive Bus communication
    
    Handles event publishing, subscription, and proper Redis connection management
    with retry logic and error handling.
    """
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 db: int = 0,
                 password: str = None,
                 connection_timeout: int = 5,
                 retry_attempts: int = 3):
        """
        Initialize Redis Bus Client
        
        Args:
            host: Redis host (defaults to env REDIS_HOST or localhost)
            port: Redis port (defaults to env REDIS_PORT or 6379)
            db: Redis database number
            password: Redis password (if required)
            connection_timeout: Connection timeout in seconds
            retry_attempts: Number of retry attempts for operations
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.db = db
        self.password = password
        self.connection_timeout = connection_timeout
        self.retry_attempts = retry_attempts
        
        self.logger = logging.getLogger(__name__)
        
        # Redis connection pools
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub_client: Optional[redis.client.PubSub] = None
        
        # Subscription management
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.listening_thread: Optional[threading.Thread] = None
        self.is_listening = False
        
        # Statistics
        self.stats = {
            "events_published": 0,
            "events_received": 0,
            "connection_errors": 0,
            "last_error": None,
            "connected_since": None
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Redis
        
        Returns:
            bool: Success status
        """
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.connection_timeout,
                socket_connect_timeout=self.connection_timeout,
                retry_on_timeout=True,
                decode_responses=True
            )
            
            # Test connection
            self.redis_client.ping()
            
            self.stats["connected_since"] = datetime.utcnow().isoformat()
            self.logger.info(f"✅ Redis Bus connected to {self.host}:{self.port}")
            
            return True
            
        except Exception as e:
            self.stats["connection_errors"] += 1
            self.stats["last_error"] = str(e)
            self.logger.error(f"❌ Redis Bus connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Redis and cleanup"""
        try:
            self.stop_listening()
            
            if self.pubsub_client:
                self.pubsub_client.close()
                self.pubsub_client = None
            
            if self.redis_client:
                self.redis_client.close()
                self.redis_client = None
            
            self.logger.info("🔌 Redis Bus disconnected")
            
        except Exception as e:
            self.logger.error(f"❌ Redis Bus disconnect error: {e}")
    
    def publish(self, channel: str, event_data: str) -> bool:
        """
        Publish raw event data to Redis channel
        
        This is a low-level publish method that accepts pre-serialized event data.
        Use this when you already have the event data as a JSON string.
        
        Args:
            channel: Redis channel name (e.g., "crew.strategy.generated")
            event_data: Pre-serialized JSON event data
            
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            if not self.connect():
                return False
        
        try:
            # Publish with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    result = self.redis_client.publish(channel, event_data)
                    
                    if result >= 0:  # Redis returns number of subscribers
                        self.stats["events_published"] += 1
                        self.logger.debug(f"📡 Published to {channel} → {result} subscribers")
                        return True
                    
                except (ConnectionError, TimeoutError) as e:
                    if attempt < self.retry_attempts - 1:
                        self.logger.warning(f"⚠️ Publish attempt {attempt + 1} failed, retrying: {e}")
                        if not self.connect():
                            continue
                    else:
                        raise e
            
            return False
            
        except Exception as e:
            self.stats["connection_errors"] += 1
            self.stats["last_error"] = str(e)
            self.logger.error(f"❌ Failed to publish to {channel}: {e}")
            return False
    
    def publish_event(self, event: CognitiveEvent) -> bool:
        """
        Publish event to Redis channel
        
        Args:
            event: CognitiveEvent to publish
            
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            if not self.connect():
                return False
        
        try:
            # Use event_type as channel name (e.g., "codex.audit.alert")
            channel = event.event_type
            
            # Serialize event
            event_data = json.dumps(event.to_dict(), default=str)
            
            # Publish with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    result = self.redis_client.publish(channel, event_data)
                    
                    if result >= 0:  # Redis returns number of subscribers
                        self.stats["events_published"] += 1
                        self.logger.debug(f"📡 Published event {event.event_type} to {result} subscribers")
                        return True
                    
                except (ConnectionError, TimeoutError) as e:
                    if attempt < self.retry_attempts - 1:
                        self.logger.warning(f"WARNING Publish attempt {attempt + 1} failed, retrying: {e}")
                        if not self.connect():
                            continue
                    else:
                        raise e
            
            return False
            
        except Exception as e:
            self.stats["connection_errors"] += 1
            self.stats["last_error"] = str(e)
            self.logger.error(f"❌ Failed to publish event {event.event_type}: {e}")
            return False
    
    def publish_codex_event(self, 
                           domain: str,
                           intent: str,
                           emitter: str,
                           target: str,
                           payload: Dict[str, Any],
                           correlation_id: str = None) -> bool:
        """
        Convenience method for publishing Codex Hunter events
        
        Args:
            domain: Event domain (e.g., "codex", "langgraph", "audit")
            intent: Event intent (e.g., "discovered", "alert", "ready")
            emitter: Source agent/service
            target: Target agent/service
            payload: Event data
            correlation_id: Optional correlation ID
            
        Returns:
            bool: Success status
        """
        event = CognitiveEvent(
            event_type=f"{domain}.{intent}",
            emitter=emitter,
            target=target,
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id
        )
        
        return self.publish_event(event)
    
    def subscribe(self, channel_pattern: str, callback: Callable[[CognitiveEvent], None]) -> bool:
        """
        Subscribe to Redis channel with callback
        
        Args:
            channel_pattern: Channel pattern to subscribe to (supports wildcards)
            callback: Function to call when event received
            
        Returns:
            bool: Success status
        """
        try:
            if channel_pattern not in self.subscriptions:
                self.subscriptions[channel_pattern] = []
            
            self.subscriptions[channel_pattern].append(callback)
            
            self.logger.info(f"📥 Subscribed to channel pattern: {channel_pattern}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to subscribe to {channel_pattern}: {e}")
            return False
    
    def start_listening(self) -> bool:
        """
        Start listening for subscribed events in background thread
        
        Returns:
            bool: Success status
        """
        if self.is_listening:
            self.logger.warning("WARNING Already listening for events")
            return True
        
        try:
            if not self.redis_client:
                if not self.connect():
                    return False
            
            self.pubsub_client = self.redis_client.pubsub()
            
            # Subscribe to all registered patterns
            for pattern in self.subscriptions.keys():
                self.pubsub_client.psubscribe(pattern)
            
            # Start listening thread
            self.is_listening = True
            self.listening_thread = threading.Thread(target=self._listen_worker, daemon=True)
            self.listening_thread.start()
            
            self.logger.info(f"👂 Started listening on {len(self.subscriptions)} channel patterns")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start listening: {e}")
            return False
    
    def stop_listening(self) -> None:
        """Stop listening for events"""
        self.is_listening = False
        
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2.0)
        
        if self.pubsub_client:
            try:
                self.pubsub_client.unsubscribe()
                self.pubsub_client.punsubscribe()
            except Exception as e:
                self.logger.error(f"❌ Error unsubscribing: {e}")
        
        self.logger.info("🔇 Stopped listening for events")
    
    def _listen_worker(self) -> None:
        """Background worker for listening to events"""
        try:
            while self.is_listening and self.pubsub_client:
                try:
                    message = self.pubsub_client.get_message(timeout=1.0)
                    
                    if message and message['type'] == 'pmessage':
                        self._handle_message(message)
                
                except Exception as e:
                    if self.is_listening:  # Only log if we're supposed to be listening
                        self.logger.error(f"❌ Error in listen worker: {e}")
                        self.stats["connection_errors"] += 1
                        break
                
        except Exception as e:
            self.logger.error(f"❌ Listen worker crashed: {e}")
        
        finally:
            self.is_listening = False
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle received Redis message"""
        try:
            # Extract data
            pattern = message['pattern'].decode() if isinstance(message['pattern'], bytes) else message['pattern']
            channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
            data = message['data'].decode() if isinstance(message['data'], bytes) else message['data']
            
            # Parse event
            event_data = json.loads(data)
            event = CognitiveEvent.from_dict(event_data)
            
            # Find matching callbacks
            if pattern in self.subscriptions:
                for callback in self.subscriptions[pattern]:
                    try:
                        # Handle both sync and async callbacks
                        if asyncio.iscoroutinefunction(callback):
                            # For async callbacks, we need to schedule them properly
                            # Since we're in a sync context, we'll create a task
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    loop.create_task(callback(event))
                                else:
                                    asyncio.run(callback(event))
                            except RuntimeError:
                                # No event loop running, run in thread
                                threading.Thread(target=lambda: asyncio.run(callback(event)), daemon=True).start()
                        else:
                            # Sync callback
                            callback(event)
                            
                        self.stats["events_received"] += 1
                    except Exception as e:
                        self.logger.error(f"❌ Callback error for {channel}: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling message: {e}")
    
    def is_connected(self) -> bool:
        """Check if Redis connection is active"""
        try:
            if not self.redis_client:
                return False
            
            self.redis_client.ping()
            return True
            
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            "connected": self.is_connected(),
            "listening": self.is_listening,
            "subscriptions": len(self.subscriptions),
            "connection_info": {
                "host": self.host,
                "port": self.port,
                "db": self.db
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            connected = self.is_connected()
            
            return {
                "status": "healthy" if connected else "unhealthy",
                "connected": connected,
                "listening": self.is_listening,
                "events_published": self.stats["events_published"],
                "events_received": self.stats["events_received"],
                "connection_errors": self.stats["connection_errors"],
                "last_error": self.stats["last_error"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connected": False
            }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False


# Singleton instance for global use
_redis_bus_instance: Optional[RedisBusClient] = None


def get_redis_bus() -> RedisBusClient:
    """
    Get global Redis Bus Client instance
    
    Returns:
        RedisBusClient: Singleton instance
    """
    global _redis_bus_instance
    
    if _redis_bus_instance is None:
        _redis_bus_instance = RedisBusClient()
    
    return _redis_bus_instance


def reset_redis_bus() -> None:
    """Reset global Redis Bus Client (for testing)"""
    global _redis_bus_instance
    
    if _redis_bus_instance:
        _redis_bus_instance.disconnect()
        _redis_bus_instance = None


# Convenience functions
def publish_codex_event(domain: str, intent: str, emitter: str, target: str, 
                       payload: Dict[str, Any], correlation_id: str = None) -> bool:
    """Global convenience function for publishing events"""
    bus = get_redis_bus()
    return bus.publish_codex_event(domain, intent, emitter, target, payload, correlation_id)


def subscribe_to_events(channel_pattern: str, callback: Callable[[CognitiveEvent], None]) -> bool:
    """Global convenience function for subscribing to events"""
    bus = get_redis_bus()
    return bus.subscribe(channel_pattern, callback)