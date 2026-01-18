#!/usr/bin/env python3
"""
WorkingMemory — Local Consumer State
=====================================

Each consumer maintains its own working memory,
following the octopus proprioceptive model:
- Arms know their own position without asking the brain
- Memory is not shared directly (only via events)
- Old memories fade (TTL-based expiration)

This is NOT long-term memory (Vault Keepers handle that).
This is fast, local, ephemeral state.

Biological Model: Proprioceptive ganglia in octopus arms
Network Model: Redis namespace isolation

Author: Vitruvyan Cognitive Architecture
Date: January 18, 2026
"""

from typing import Any, Optional, Dict, List
import json
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class WorkingMemory:
    """
    Local working memory for a single consumer.
    
    Properties:
    - Namespaced: Each consumer has isolated keyspace
    - Ephemeral: TTL ensures memories fade
    - Fast: Redis-backed for low latency
    - Local: Not shared directly between consumers
    
    If consumers need to share state, they MUST do so via events
    on the cognitive bus. This enforces the architectural invariant
    that the bus is the only communication channel.
    """
    
    def __init__(self, consumer_name: str, ttl_seconds: int = 3600):
        """
        Initialize working memory for a consumer.
        
        Args:
            consumer_name: Unique consumer identifier
            ttl_seconds: Default TTL for memories (default 1 hour)
        """
        self.namespace = f"wm:{consumer_name}"
        self.ttl = ttl_seconds
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
        logger.debug(f"WorkingMemory initialized: {self.namespace}")
    
    async def connect(self, redis_url: str = "redis://localhost:6379") -> None:
        """Connect to Redis backend."""
        if self._connected:
            return
        
        self._client = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self._connected = True
        logger.info(f"WorkingMemory connected: {self.namespace}")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client and self._connected:
            await self._client.close()
            self._connected = False
            logger.info(f"WorkingMemory closed: {self.namespace}")
    
    # ─────────────────────────────────────────────────────────────
    # Core operations
    # ─────────────────────────────────────────────────────────────
    
    async def remember(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in working memory.
        
        Args:
            key: Memory key (will be namespaced)
            value: Any JSON-serializable value
            ttl: Optional custom TTL (default uses consumer TTL)
        """
        self._ensure_connected()
        
        full_key = self._key(key)
        serialized = json.dumps(value)
        effective_ttl = ttl or self.ttl
        
        await self._client.setex(full_key, effective_ttl, serialized)
        logger.debug(f"Remembered: {key} (TTL={effective_ttl}s)")
    
    async def recall(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from working memory.
        
        Args:
            key: Memory key
            
        Returns:
            The stored value, or None if not found/expired
        """
        self._ensure_connected()
        
        full_key = self._key(key)
        value = await self._client.get(full_key)
        
        if value is None:
            logger.debug(f"Recall miss: {key}")
            return None
        
        logger.debug(f"Recall hit: {key}")
        return json.loads(value)
    
    async def forget(self, key: str) -> bool:
        """
        Remove a value from working memory.
        
        Args:
            key: Memory key
            
        Returns:
            True if key existed, False otherwise
        """
        self._ensure_connected()
        
        full_key = self._key(key)
        result = await self._client.delete(full_key)
        
        logger.debug(f"Forgot: {key} (existed={result > 0})")
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in working memory."""
        self._ensure_connected()
        return await self._client.exists(self._key(key)) > 0
    
    async def refresh(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        Refresh TTL on an existing key.
        
        Like "touching" a memory to keep it active.
        """
        self._ensure_connected()
        
        full_key = self._key(key)
        effective_ttl = ttl or self.ttl
        
        result = await self._client.expire(full_key, effective_ttl)
        return result
    
    # ─────────────────────────────────────────────────────────────
    # Batch operations
    # ─────────────────────────────────────────────────────────────
    
    async def remember_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store multiple values atomically."""
        self._ensure_connected()
        
        effective_ttl = ttl or self.ttl
        pipe = self._client.pipeline()
        
        for key, value in items.items():
            full_key = self._key(key)
            serialized = json.dumps(value)
            pipe.setex(full_key, effective_ttl, serialized)
        
        await pipe.execute()
        logger.debug(f"Remembered {len(items)} items")
    
    async def recall_many(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple values."""
        self._ensure_connected()
        
        if not keys:
            return {}
        
        full_keys = [self._key(k) for k in keys]
        values = await self._client.mget(full_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                result[key] = json.loads(value)
        
        return result
    
    async def forget_all(self) -> int:
        """
        Clear all memories for this consumer.
        
        Use with caution — this is a full memory wipe.
        """
        self._ensure_connected()
        
        pattern = f"{self.namespace}:*"
        cursor = 0
        deleted = 0
        
        while True:
            cursor, keys = await self._client.scan(cursor, match=pattern, count=100)
            if keys:
                deleted += await self._client.delete(*keys)
            if cursor == 0:
                break
        
        logger.info(f"Forgot all: {deleted} keys deleted")
        return deleted
    
    # ─────────────────────────────────────────────────────────────
    # Context management (for async with)
    # ─────────────────────────────────────────────────────────────
    
    async def context(self, context_id: str) -> 'MemoryContext':
        """
        Create a sub-context for grouped memories.
        
        Useful for session-scoped or correlation-scoped memories.
        
        Example:
            async with memory.context(correlation_id) as ctx:
                await ctx.remember("step1_result", result)
                # All keys prefixed with context_id
        """
        return MemoryContext(self, context_id)
    
    # ─────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """List all keys matching pattern in this namespace."""
        self._ensure_connected()
        
        full_pattern = f"{self.namespace}:{pattern}"
        keys = []
        cursor = 0
        
        while True:
            cursor, batch = await self._client.scan(cursor, match=full_pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
        
        # Remove namespace prefix from keys
        prefix_len = len(self.namespace) + 1
        return [k[prefix_len:] for k in keys]
    
    async def ttl_remaining(self, key: str) -> int:
        """Get remaining TTL for a key in seconds."""
        self._ensure_connected()
        return await self._client.ttl(self._key(key))
    
    async def memory_stats(self) -> Dict[str, Any]:
        """Get statistics about this consumer's working memory."""
        self._ensure_connected()
        
        all_keys = await self.keys()
        
        return {
            "namespace": self.namespace,
            "default_ttl": self.ttl,
            "key_count": len(all_keys),
            "connected": self._connected
        }
    
    # ─────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────
    
    def _key(self, key: str) -> str:
        """Generate namespaced key."""
        return f"{self.namespace}:{key}"
    
    def _ensure_connected(self) -> None:
        """Ensure Redis connection is active."""
        if not self._connected or not self._client:
            raise RuntimeError(
                f"WorkingMemory not connected. Call connect() first."
            )


class MemoryContext:
    """
    Sub-context for grouped memories within a consumer.
    
    Useful for correlation-scoped or session-scoped state.
    """
    
    def __init__(self, parent: WorkingMemory, context_id: str):
        self._parent = parent
        self._context_id = context_id
        self._prefix = f"ctx:{context_id}"
    
    async def remember(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store in context namespace."""
        full_key = f"{self._prefix}:{key}"
        await self._parent.remember(full_key, value, ttl)
    
    async def recall(self, key: str) -> Optional[Any]:
        """Retrieve from context namespace."""
        full_key = f"{self._prefix}:{key}"
        return await self._parent.recall(full_key)
    
    async def forget(self, key: str) -> bool:
        """Remove from context namespace."""
        full_key = f"{self._prefix}:{key}"
        return await self._parent.forget(full_key)
    
    async def clear(self) -> int:
        """Clear all memories in this context."""
        keys = await self._parent.keys(f"{self._prefix}:*")
        count = 0
        for key in keys:
            if await self._parent.forget(key):
                count += 1
        return count
    
    async def __aenter__(self) -> 'MemoryContext':
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass  # Context memories persist until TTL or explicit clear
