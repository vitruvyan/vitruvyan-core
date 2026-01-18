"""
    🔌 Listener Adapter — Migration Bridge
Enables existing pub/sub listeners to use Redis Streams

This adapter allows gradual migration from pub/sub to Streams
without rewriting entire listener classes.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime
import structlog

from ..streams import StreamBus
from .base_consumer import BaseConsumer, ConsumerType, ConsumerConfig

logger = structlog.get_logger("cognitive_bus.listener_adapter")


class ListenerAdapter(BaseConsumer):
    """
    Adapter that bridges existing pub/sub listeners to StreamBus.
    
    Usage:
        class VaultKeepersListener:
            sacred_channels = ["vault.archive.requested", ...]
            
            async def handle_sacred_message(self, message):
                # existing handler
        
        # Wrap with adapter
        adapter = ListenerAdapter(
            name="vault_keepers",
            listener_instance=vault_listener,
            sacred_channels=vault_listener.sacred_channels,
            handler_method="handle_sacred_message"
        )
        await adapter.start()
    """
    
    def __init__(
        self,
        name: str,
        listener_instance: Any,
        sacred_channels: List[str],
        handler_method: str = "handle_sacred_message",
        consumer_type: ConsumerType = ConsumerType.ADVISORY,
        stream_host: str = "localhost",
        stream_port: int = 6379
    ):
        # Create config for BaseConsumer
        config = ConsumerConfig(
            name=name,
            consumer_type=consumer_type,
            subscriptions=[f"stream:{ch}" for ch in sacred_channels]
        )
        super().__init__(config=config)
        
        self.listener_instance = listener_instance
        self.sacred_channels = sacred_channels
        self.handler_method = handler_method
        
        # Initialize StreamBus
        self.stream_bus = StreamBus(host=stream_host, port=stream_port)
        
        # Map channel names to stream names
        # "vault.archive.requested" → "stream:vault.archive.requested"
        self.stream_names = [f"stream:{ch}" for ch in sacred_channels]
        
        # Consumer group name (unique per listener type)
        self.consumer_group = f"group:{name}"
        
        logger.info(
            f"🔌 ListenerAdapter initialized",
            name=name,
            channels=sacred_channels,
            consumer_type=consumer_type.value
        )
    
    async def start(self):
        """
        Start consuming from streams.
        """
        logger.info(f"🔌 Starting {self.name} adapter", streams=self.stream_names)
        
        # Create consumer groups if not exist
        for stream_name in self.stream_names:
            try:
                self.stream_bus.create_consumer_group(stream_name, self.consumer_group)
                logger.info(f"✅ Consumer group created", stream=stream_name, group=self.consumer_group)
            except Exception as e:
                # Group may already exist
                logger.debug(f"Consumer group exists or error", stream=stream_name, error=str(e))
        
        # Start consuming
        tasks = [self._consume_stream(stream_name) for stream_name in self.stream_names]
        await asyncio.gather(*tasks)
    
    async def _consume_stream(self, stream_name: str):
        """
        Consume events from a single stream.
        """
        consumer_name = f"{self.name}:worker"
        
        logger.info(f"👂 Consuming stream", stream=stream_name, consumer=consumer_name)
        
        while True:
            try:
                # Consume batch (block=1000ms, count=10)
                events = self.stream_bus.consume(
                    stream_name=stream_name,
                    group_name=self.consumer_group,
                    consumer_name=consumer_name,
                    block=1000,
                    count=10
                )
                
                for event_id, event_data in events:
                    await self._handle_event(stream_name, event_id, event_data)
                    
            except Exception as e:
                logger.error(
                    f"❌ Error consuming stream",
                    stream=stream_name,
                    error=str(e),
                    exc_info=True
                )
                await asyncio.sleep(5)  # Back off on error
    
    async def _handle_event(self, stream_name: str, event_id: str, event_data: Dict[str, Any]):
        """
        Handle a single event by delegating to original listener.
        """
        try:
            # Extract channel name from stream name
            # "stream:vault.archive.requested" → "vault.archive.requested"
            channel = stream_name.replace("stream:", "")
            
            # Build message compatible with old pub/sub format
            # Old: {"type": "message", "channel": "...", "data": b"..."}
            # New: {"type": "message", "channel": "...", "data": event_data}
            message = {
                "type": "message",
                "channel": channel.encode(),
                "data": event_data.get("payload", b"{}"),
                "event_id": event_id,
                "emitter": event_data.get("emitter", "unknown"),
                "timestamp": event_data.get("timestamp", "")
            }
            
            # Call original handler
            handler = getattr(self.listener_instance, self.handler_method)
            await handler(message)
            
            # Acknowledge event
            self.stream_bus.ack(stream_name, self.consumer_group, event_id)
            
            logger.debug(
                f"✅ Event handled",
                stream=stream_name,
                event_id=event_id,
                channel=channel
            )
            
        except Exception as e:
            logger.error(
                f"❌ Error handling event",
                stream=stream_name,
                event_id=event_id,
                error=str(e),
                exc_info=True
            )
            # Don't ack — event will be retried
    
    async def process(self, event) -> Dict[str, Any]:
        """
        BaseConsumer interface (not used in adapter mode).
        Adapter delegates to wrapped listener instead.
        """
        # This method satisfies ABC requirement but is not called
        # Adapter uses _consume_stream → _handle_event → wrapped listener
        return {
            "status": "success",
            "note": "Adapter delegates to wrapped listener handler"
        }


class StreamsEnabledListener:
    """
    Base class for NEW listeners that use Streams natively.
    
    Usage:
        class VaultKeepersListener(StreamsEnabledListener):
            def __init__(self):
                super().__init__(
                    name="vault_keepers",
                    sacred_channels=["vault.archive.requested", ...]
                )
            
            async def handle_event(self, channel: str, event_data: Dict):
                # Your logic here
                pass
    """
    
    def __init__(
        self,
        name: str,
        sacred_channels: List[str],
        consumer_type: ConsumerType = ConsumerType.ADVISORY,
        stream_host: str = "localhost",
        stream_port: int = 6379
    ):
        self.name = name
        self.sacred_channels = sacred_channels
        self.consumer_type = consumer_type
        
        # Initialize StreamBus
        self.stream_bus = StreamBus(host=stream_host, port=stream_port)
        
        # Map channels to streams
        self.stream_names = [f"stream:{ch}" for ch in sacred_channels]
        self.consumer_group = f"group:{name}"
        
        logger.info(
            f"🌊 StreamsEnabledListener initialized",
            name=name,
            channels=sacred_channels,
            consumer_type=consumer_type.value
        )
    
    async def start(self):
        """
        Start consuming from streams.
        """
        logger.info(f"🌊 Starting {self.name}", streams=self.stream_names)
        
        # Create consumer groups
        for stream_name in self.stream_names:
            try:
                self.stream_bus.create_consumer_group(stream_name, self.consumer_group)
            except Exception as e:
                logger.debug(f"Consumer group exists", stream=stream_name)
        
        # Start consuming
        tasks = [self._consume_stream(stream_name) for stream_name in self.stream_names]
        await asyncio.gather(*tasks)
    
    async def _consume_stream(self, stream_name: str):
        """
        Consume events from stream.
        """
        consumer_name = f"{self.name}:worker"
        
        while True:
            try:
                events = self.stream_bus.consume(
                    stream_name=stream_name,
                    group_name=self.consumer_group,
                    consumer_name=consumer_name,
                    block=1000,
                    count=10
                )
                
                for event_id, event_data in events:
                    await self._handle_event(stream_name, event_id, event_data)
                    
            except Exception as e:
                logger.error(f"Error consuming", stream=stream_name, error=str(e))
                await asyncio.sleep(5)
    
    async def _handle_event(self, stream_name: str, event_id: str, event_data: Dict[str, Any]):
        """
        Handle event by calling subclass implementation.
        """
        try:
            channel = stream_name.replace("stream:", "")
            
            # Call subclass handler
            await self.handle_event(channel, event_data)
            
            # Acknowledge
            self.stream_bus.ack(stream_name, self.consumer_group, event_id)
            
            logger.debug(f"✅ Event handled", stream=stream_name, event_id=event_id)
            
        except Exception as e:
            logger.error(f"❌ Error handling event", error=str(e), exc_info=True)
    
    async def handle_event(self, channel: str, event_data: Dict[str, Any]):
        """
        Override this method in subclass.
        """
        raise NotImplementedError("Subclass must implement handle_event()")


# Migration helper function
def wrap_legacy_listener(
    listener_instance: Any,
    name: str,
    sacred_channels: List[str],
    handler_method: str = "handle_sacred_message",
    consumer_type: ConsumerType = ConsumerType.ADVISORY
) -> ListenerAdapter:
    """
    Convenience function to wrap existing listener.
    
    Usage:
        vault_listener = VaultKeepersCognitiveBusListener()
        adapter = wrap_legacy_listener(
            vault_listener,
            name="vault_keepers",
            sacred_channels=vault_listener.sacred_channels
        )
        await adapter.start()
    """
    return ListenerAdapter(
        name=name,
        listener_instance=listener_instance,
        sacred_channels=sacred_channels,
        handler_method=handler_method,
        consumer_type=consumer_type
    )
