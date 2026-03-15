"""
LLMAgent — Centralized LLM Gateway
===================================

The canonical LLM agent following the PostgresAgent/QdrantAgent pattern.
All LLM access in the system MUST go through this agent.

Nuclear Option Philosophy (Appendix G):
    "LLM is PRIMARY, validation is MANDATORY, cache is OPTIMIZATION"

    Vitruvyan replaces rigid regex patterns with LLM-based natural
    language understanding, while maintaining epistemic integrity
    through structured validation layers.

Features:
    - Centralized access (singleton, one OpenAI client for all nodes)
    - Redis-backed caching via LLMCacheManager
    - Rate limiting (prevents 429 errors from provider)
    - Circuit breaker (graceful degradation on failures)
    - Provider abstraction (swap OpenAI for Anthropic/local/Gemma)
    - Function calling / tool use (complete_with_tools)
    - Metrics (latency, token usage, cache hit rate)
    - Both sync and async interfaces

Model Resolution (env var chain):
    VITRUVYAN_LLM_MODEL → GRAPH_LLM_MODEL → OPENAI_MODEL → "gpt-4o-mini"

Usage:
    from core.agents.llm_agent import get_llm_agent

    llm = get_llm_agent()  # singleton

    # Simple completion
    response = llm.complete("Classify this intent", system_prompt="You are...")

    # JSON mode
    data = llm.complete_json(prompt, system_prompt)

    # Function calling / MCP tools
    result = llm.complete_with_tools(messages, tools=[...])

    # Raw messages (full control)
    result = llm.complete_with_messages(messages, model="gpt-4o-mini")

Sacred Orders Alignment:
    - Discourse: LLM-first conversational layer
    - Truth: Validation layers post-LLM
    - Memory: Cache as optimization layer

Author: Vitruvyan Core Team
Created: February 10, 2026
Refactored: February 12, 2026 (v2.0 — domain-agnostic, tools support)
Status: PRODUCTION
"""

import os
import time
import json
import asyncio
import hashlib
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
from collections import deque

# Lazy import: Only load OpenAI if LLMAgent is actually instantiated
# This prevents import errors in services that import PostgresAgent
# but don't use LLM functionality (e.g., Memory Orders, Vault Keepers)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # Type hint compatibility

# NOTE: Configuration via environment variables only.
# load_dotenv() is called in service entrypoints (main.py), not in core modules.

# ===========================================================================
# MULTI-PROVIDER CONFIG
# ===========================================================================

# Providers that expose an OpenAI-compatible API — just swap base_url + api_key.
# Anthropic is handled separately (native SDK, different message format).
_OPENAI_COMPAT_PROVIDERS = {
    "openai":   None,   # default OpenAI endpoint
    "gemini":   "https://generativelanguage.googleapis.com/v1beta/openai/",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen":     "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "mistral":  "https://api.mistral.ai/v1",
    # "custom": base_url read from VITRUVYAN_LLM_BASE_URL at runtime
}

# Default models per provider (used when VITRUVYAN_LLM_MODEL is not set)
_PROVIDER_DEFAULT_MODELS = {
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "gemini":    "gemini-2.0-flash",
    "deepseek":  "deepseek-chat",
    "qwen":      "qwen-max",
    "mistral":   "mistral-large-latest",
    "custom":    "llama3.2",
}

logger = logging.getLogger(__name__)


# ===========================================================================
# RATE LIMITER
# ===========================================================================

class RateLimiter:
    """
    Token bucket rate limiter for LLM API calls.
    
    Prevents 429 errors from OpenAI by enforcing:
    - Max requests per minute (RPM)
    - Max tokens per minute (TPM)
    """
    
    def __init__(
        self,
        rpm: int = None,
        tpm: int = None,
        window_seconds: int = 60
    ):
        self.rpm = rpm or int(os.getenv("LLM_RATE_LIMIT_RPM", "500"))
        self.tpm = tpm or int(os.getenv("LLM_RATE_LIMIT_TPM", "30000"))
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._request_times: deque = deque()
        self._token_usage: deque = deque()
    
    def _cleanup_old_entries(self, now: float) -> None:
        """Remove entries older than the window."""
        cutoff = now - self.window_seconds
        
        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()
        
        while self._token_usage and self._token_usage[0][0] < cutoff:
            self._token_usage.popleft()
    
    def acquire(self, estimated_tokens: int = 500) -> bool:
        """
        Attempt to acquire a rate limit slot.
        
        Args:
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            True if acquired, False if rate limited
        """
        with self._lock:
            now = time.time()
            self._cleanup_old_entries(now)
            
            # Check RPM
            if len(self._request_times) >= self.rpm:
                logger.warning(f"🚫 Rate limited: {len(self._request_times)} requests in last minute")
                return False
            
            # Check TPM
            current_tokens = sum(t[1] for t in self._token_usage)
            if current_tokens + estimated_tokens > self.tpm:
                logger.warning(f"🚫 Token limited: {current_tokens} + {estimated_tokens} > {self.tpm}")
                return False
            
            # Acquire slot
            self._request_times.append(now)
            self._token_usage.append((now, estimated_tokens))
            return True
    
    def record_actual_tokens(self, actual_tokens: int) -> None:
        """Update the last entry with actual token usage."""
        with self._lock:
            if self._token_usage:
                # Remove last estimated entry and add actual
                last_time, _ = self._token_usage.pop()
                self._token_usage.append((last_time, actual_tokens))


# ===========================================================================
# CIRCUIT BREAKER
# ===========================================================================

class CircuitBreaker:
    """
    Circuit breaker for LLM API resilience.
    
    States:
    - CLOSED: Normal operation, requests flow through
    - OPEN: Too many failures, fail fast (don't call API)
    - HALF_OPEN: Testing if API recovered
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = Lock()
    
    @property
    def state(self) -> str:
        """Get current circuit state."""
        with self._lock:
            if self._state == self.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time and \
                   time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = self.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("🔄 Circuit breaker: OPEN → HALF_OPEN")
            return self._state
    
    def can_execute(self) -> bool:
        """Check if request can proceed."""
        state = self.state
        
        if state == self.CLOSED:
            return True
        elif state == self.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        else:  # OPEN
            return False
    
    def record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            if self._state == self.HALF_OPEN:
                logger.info("✅ Circuit breaker: HALF_OPEN → CLOSED")
                self._state = self.CLOSED
            self._failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == self.HALF_OPEN:
                logger.warning("❌ Circuit breaker: HALF_OPEN → OPEN")
                self._state = self.OPEN
            elif self._failure_count >= self.failure_threshold:
                logger.warning(f"⚡ Circuit breaker: CLOSED → OPEN after {self._failure_count} failures")
                self._state = self.OPEN


# ===========================================================================
# METRICS
# ===========================================================================

@dataclass
class LLMMetrics:
    """Metrics for LLM usage tracking."""
    total_requests: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    rate_limited: int = 0
    circuit_breaker_rejected: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_requests if self.total_requests > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hit_rate, 3),
            "rate_limited": self.rate_limited,
            "circuit_breaker_rejected": self.circuit_breaker_rejected,
            "errors": self.errors,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }


# ===========================================================================
# LLM AGENT
# ===========================================================================

# ===========================================================================
# PROVIDER / MODEL RESOLUTION
# ===========================================================================

def _resolve_provider() -> str:
    """Resolve LLM provider from env. Defaults to 'openai' for backward compat."""
    return (os.getenv("VITRUVYAN_LLM_PROVIDER") or "openai").lower()


def _resolve_api_key(provider: str) -> Optional[str]:
    """Resolve API key: VITRUVYAN_LLM_API_KEY → OPENAI_API_KEY (compat)."""
    return (
        os.getenv("VITRUVYAN_LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )


def _resolve_default_model() -> str:
    """Resolve default LLM model from env var chain.

    Priority: VITRUVYAN_LLM_MODEL → GRAPH_LLM_MODEL → OPENAI_MODEL → provider default
    """
    provider = _resolve_provider()
    fallback = _PROVIDER_DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    return (
        os.getenv("VITRUVYAN_LLM_MODEL")
        or os.getenv("GRAPH_LLM_MODEL")
        or os.getenv("OPENAI_MODEL")
        or fallback
    )


# ===========================================================================
# ANTHROPIC ADAPTER  (translates anthropic SDK → OpenAI-compatible interface)
# ===========================================================================

class _AnthropicUsage:
    def __init__(self, usage):
        self.prompt_tokens = getattr(usage, "input_tokens", 0)
        self.completion_tokens = getattr(usage, "output_tokens", 0)
        self.total_tokens = self.prompt_tokens + self.completion_tokens


class _AnthropicMessage:
    def __init__(self, content_text: str):
        self.content = content_text
        self.role = "assistant"
        self.tool_calls = []  # tool calling via Anthropic SDK not yet wired


class _AnthropicChoice:
    def __init__(self, message: _AnthropicMessage):
        self.message = message


class _AnthropicResponse:
    """Wraps anthropic.Message to look like openai.ChatCompletion."""
    def __init__(self, response):
        text = response.content[0].text if response.content else ""
        self.choices = [_AnthropicChoice(_AnthropicMessage(text))]
        self.usage = _AnthropicUsage(response.usage)


class _AnthropicCompletionsAdapter:
    def __init__(self, client):
        self._client = client

    def create(self, model, messages, temperature=0.0, max_tokens=500,
               response_format=None, tools=None, tool_choice=None, **kwargs):
        system = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        call_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            call_kwargs["system"] = system

        response = self._client.messages.create(**call_kwargs)
        return _AnthropicResponse(response)


class _AnthropicClientAdapter:
    """Drop-in replacement for the OpenAI client inside LLMAgent."""
    def __init__(self, anthropic_client):
        self.chat = type("_Chat", (), {})()
        self.chat.completions = _AnthropicCompletionsAdapter(anthropic_client)


class LLMAgent:
    """
    Centralized LLM gateway following PostgresAgent/QdrantAgent pattern.
    
    Provides single point of access for ALL LLM calls in the system.
    Handles caching, rate limiting, circuit breaking, metrics, and tool use.
    
    Nuclear Option: "LLM is PRIMARY, validation is MANDATORY, cache is OPTIMIZATION"
    """
    
    # Singleton instance
    _instance: Optional['LLMAgent'] = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern - reuse connection across nodes."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        api_key: str = None,
        default_model: str = None,
        enable_cache: bool = True,
        enable_rate_limiting: bool = True,
        enable_circuit_breaker: bool = True,
    ):
        """
        Initialize LLM agent.

        Provider selection (env var chain):
            VITRUVYAN_LLM_PROVIDER → "openai" (default)

        Supported providers:
            openai, anthropic, gemini, deepseek, qwen, mistral, custom

        API key resolution:
            VITRUVYAN_LLM_API_KEY → OPENAI_API_KEY (backward compat)

        Args:
            api_key: Override API key (normally read from env)
            default_model: Override default model (normally read from env)
            enable_cache: Enable Redis-backed response caching
            enable_rate_limiting: Enable rate limiting
            enable_circuit_breaker: Enable circuit breaker
        """
        # Skip re-initialization for singleton
        if hasattr(self, '_initialized') and self._initialized:
            return

        provider = _resolve_provider()
        resolved_key = api_key or _resolve_api_key(provider)
        self.api_key = resolved_key
        self.provider = provider
        self.default_model = default_model or _resolve_default_model()

        # ── Build the right client ──────────────────────────────
        if provider == "anthropic":
            try:
                import anthropic as _anthropic_sdk
                _client_raw = _anthropic_sdk.Anthropic(api_key=resolved_key)
                self._client = _AnthropicClientAdapter(_client_raw)
                logger.info("✅ LLMAgent: Anthropic client initialised")
            except ImportError:
                raise ImportError(
                    "❌ Provider 'anthropic' requires the 'anthropic' package.\n"
                    "Install it: pip install anthropic"
                )
        elif provider == "custom":
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "❌ LLMAgent requires 'openai' package even for custom/on-premise providers.\n"
                    "Install it: pip install openai>=1.0.0"
                )
            base_url = os.getenv("VITRUVYAN_LLM_BASE_URL") or "http://localhost:11434/v1"
            # Ollama and most local servers accept any non-empty string as key
            self._client = OpenAI(api_key=resolved_key or "local", base_url=base_url)
            logger.info(f"✅ LLMAgent: on-premise client ({base_url})")
        else:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "❌ LLMAgent requires 'openai' package. "
                    "Install it: pip install openai>=1.0.0\n"
                    "Note: Services importing PostgresAgent without using LLM "
                    "functionality will not trigger this error (lazy import)."
                )
            base_url = _OPENAI_COMPAT_PROVIDERS.get(provider)  # None → default OpenAI endpoint
            self._client = OpenAI(api_key=resolved_key, base_url=base_url)
            label = f"{provider} ({base_url})" if base_url else provider
            logger.info(f"✅ LLMAgent: {label} client initialised")

        # ── Cache / rate limiter / circuit breaker ───────────────
        self._cache = None
        self._enable_cache = enable_cache

        self._rate_limiter = RateLimiter() if enable_rate_limiting else None
        self._circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        self._metrics = LLMMetrics()

        self._initialized = True
        logger.info(f"✅ LLMAgent ready (provider={provider}, model={self.default_model}, cache={enable_cache})")

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton — allows re-initialisation after provider change (e.g. in tests)."""
        with cls._lock:
            cls._instance = None
    
    @property
    def cache(self):
        """Lazy load cache manager."""
        if self._cache is None and self._enable_cache:
            try:
                from core.llm.cache_manager import LLMCacheManager
                self._cache = LLMCacheManager()
            except Exception as e:
                logger.warning(f"⚠️ Cache manager unavailable: {e}")
                self._enable_cache = False
        return self._cache
    
    def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
        json_mode: bool = False,
        cache_key: str = None,
        cache_ttl_hours: int = 24,
        skip_cache: bool = False,
        prompt_metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Complete a prompt using the LLM.
        
        This is the main entry point. All nodes should use this method
        instead of direct OpenAI calls.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (default: gpt-4o-mini)
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Max tokens in response
            json_mode: Enable JSON response format
            cache_key: Custom cache key (auto-generated if None)
            cache_ttl_hours: Cache TTL in hours
            skip_cache: Bypass cache for this request
            
        Returns:
            LLM response text
            
        Raises:
            LLMRateLimitError: If rate limited
            LLMCircuitOpenError: If circuit breaker is open
            LLMError: For other LLM errors
        """
        start_time = time.time()
        model = model or self.default_model
        
        self._metrics.total_requests += 1
        
        # Circuit breaker check
        if self._circuit_breaker and not self._circuit_breaker.can_execute():
            self._metrics.circuit_breaker_rejected += 1
            logger.warning("⚡ LLM request rejected by circuit breaker")
            raise LLMCircuitOpenError("Circuit breaker is open")
        
        # Rate limiter check
        estimated_tokens = len(prompt.split()) * 2 + max_tokens
        if self._rate_limiter and not self._rate_limiter.acquire(estimated_tokens):
            self._metrics.rate_limited += 1
            logger.warning("🚫 LLM request rate limited")
            raise LLMRateLimitError("Rate limited")
        
        # Cache check
        if not skip_cache and self._enable_cache and self.cache:
            cache_key = cache_key or self._generate_cache_key(prompt, system_prompt, model)
            cached = self._get_cached(cache_key)
            if cached:
                self._metrics.cache_hits += 1
                latency = (time.time() - start_time) * 1000
                self._metrics.total_latency_ms += latency
                logger.debug(f"📦 Cache hit (key={cache_key[:16]}...) latency={latency:.1f}ms")
                return cached
            self._metrics.cache_misses += 1
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # API call
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self._client.chat.completions.create(**kwargs)
            
            # Record success
            if self._circuit_breaker:
                self._circuit_breaker.record_success()
            
            # Update token metrics
            actual_tokens = response.usage.total_tokens if response.usage else estimated_tokens
            if self._rate_limiter:
                self._rate_limiter.record_actual_tokens(actual_tokens)
            self._metrics.total_tokens += actual_tokens
            if response.usage:
                self._metrics.prompt_tokens += response.usage.prompt_tokens or 0
                self._metrics.completion_tokens += response.usage.completion_tokens or 0
            
            # Extract response
            result = response.choices[0].message.content.strip()
            
            # Cache result
            if not skip_cache and self._enable_cache and self.cache and cache_key:
                self._set_cached(
                    cache_key=cache_key,
                    response=result,
                    ttl_hours=cache_ttl_hours,
                    state={},  # Complete method doesn't have state context
                    model=model,
                    tokens_used=actual_tokens,
                )
            
            # Record latency
            latency = (time.time() - start_time) * 1000
            self._metrics.total_latency_ms += latency
            
            logger.debug(f"✅ LLM complete (model={model}, tokens={actual_tokens}, latency={latency:.1f}ms)")
            
            # Audit trail (Phase 4.1)
            if prompt_metadata:
                logger.info("llm_audit", extra={
                    "prompt_id": prompt_metadata.get("prompt_id"),
                    "prompt_version": prompt_metadata.get("version"),
                    "domain": prompt_metadata.get("domain"),
                    "scenario": prompt_metadata.get("scenario"),
                    "model": model,
                    "tokens": actual_tokens,
                    "tenant_id": prompt_metadata.get("tenant_id"),
                    "latency_ms": round(latency, 1),
                })
            
            return result
            
        except Exception as e:
            # Record failure
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            self._metrics.errors += 1
            
            logger.error(f"❌ LLM error: {e}")
            raise LLMError(f"LLM call failed: {e}") from e
    
    async def acomplete(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
        json_mode: bool = False,
        cache_key: str = None,
        cache_ttl_hours: int = 24,
        skip_cache: bool = False,
    ) -> str:
        """
        Async version of complete() for future LangGraph ainvoke() migration.
        
        Currently wraps sync call in executor. Will be refactored to use
        AsyncOpenAI when LangGraph migrates to ainvoke().
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                cache_key=cache_key,
                cache_ttl_hours=cache_ttl_hours,
                skip_cache=skip_cache,
            )
        )
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """
        Complete and parse JSON response.
        
        Args:
            prompt: Prompt (should request JSON output)
            system_prompt: System prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens
            
        Returns:
            Parsed JSON dict
        """
        response = self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from markdown code block
            if "```json" in response:
                json_content = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_content)
            elif "```" in response:
                json_content = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_content)
            raise LLMError(f"Failed to parse JSON response: {e}")
    
    def complete_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        tool_choice: str = "auto",
        prompt_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Complete with function calling / tool use (MCP, OpenAI functions).
        
        Nuclear Option: LLM decides which tools to call based on semantic
        understanding — no regex routing.
        
        Args:
            messages: Full message array [{"role": ..., "content": ...}]
            tools: OpenAI-format tool definitions
            model: Model to use (default: env var chain)
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            tool_choice: "auto", "none", or {"type": "function", ...}
            
        Returns:
            Dict with "content", "tool_calls", "role" keys
        """
        start_time = time.time()
        model = model or self.default_model
        self._metrics.total_requests += 1
        
        # Circuit breaker check
        if self._circuit_breaker and not self._circuit_breaker.can_execute():
            self._metrics.circuit_breaker_rejected += 1
            raise LLMCircuitOpenError("Circuit breaker is open")
        
        # Rate limiter check
        estimated_tokens = sum(len(str(m.get("content", "")).split()) for m in messages) * 2 + max_tokens
        if self._rate_limiter and not self._rate_limiter.acquire(estimated_tokens):
            self._metrics.rate_limited += 1
            raise LLMRateLimitError("Rate limited")
        
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            if self._circuit_breaker:
                self._circuit_breaker.record_success()
            
            actual_tokens = response.usage.total_tokens if response.usage else estimated_tokens
            if self._rate_limiter:
                self._rate_limiter.record_actual_tokens(actual_tokens)
            self._metrics.total_tokens += actual_tokens
            if response.usage:
                self._metrics.prompt_tokens += response.usage.prompt_tokens or 0
                self._metrics.completion_tokens += response.usage.completion_tokens or 0
            
            latency = (time.time() - start_time) * 1000
            self._metrics.total_latency_ms += latency
            
            message = response.choices[0].message
            logger.debug(f"✅ LLM tools (model={model}, tokens={actual_tokens}, latency={latency:.1f}ms)")
            
            # Audit trail (Phase 4.1)
            if prompt_metadata:
                logger.info("llm_audit", extra={
                    "prompt_id": prompt_metadata.get("prompt_id"),
                    "domain": prompt_metadata.get("domain"),
                    "model": model,
                    "tokens": actual_tokens,
                    "tenant_id": prompt_metadata.get("tenant_id"),
                    "latency_ms": round(latency, 1),
                    "tool_calls": len(message.tool_calls or []),
                })
            
            return {
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in (message.tool_calls or [])
                ],
                "role": message.role,
            }
            
        except Exception as e:
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            self._metrics.errors += 1
            logger.error(f"❌ LLM tools error: {e}")
            raise LLMError(f"LLM tool call failed: {e}") from e
    
    def complete_with_messages(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
        json_mode: bool = False,
        skip_cache: bool = False,
        prompt_metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Complete with a raw messages array (full control over conversation).
        
        Use this when nodes need multi-turn messages or tool result injection.
        Standard complete() builds messages internally; this method gives
        full control.
        
        Args:
            messages: Full message array [{"role": ..., "content": ...}]
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens
            json_mode: Enable JSON response format
            skip_cache: Bypass cache
            
        Returns:
            LLM response text
        """
        start_time = time.time()
        model = model or self.default_model
        self._metrics.total_requests += 1
        
        # Circuit breaker check
        if self._circuit_breaker and not self._circuit_breaker.can_execute():
            self._metrics.circuit_breaker_rejected += 1
            raise LLMCircuitOpenError("Circuit breaker is open")
        
        # Rate limiter check
        estimated_tokens = sum(len(str(m.get("content", "")).split()) for m in messages) * 2 + max_tokens
        if self._rate_limiter and not self._rate_limiter.acquire(estimated_tokens):
            self._metrics.rate_limited += 1
            raise LLMRateLimitError("Rate limited")
        
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self._client.chat.completions.create(**kwargs)
            
            if self._circuit_breaker:
                self._circuit_breaker.record_success()
            
            actual_tokens = response.usage.total_tokens if response.usage else estimated_tokens
            if self._rate_limiter:
                self._rate_limiter.record_actual_tokens(actual_tokens)
            self._metrics.total_tokens += actual_tokens
            if response.usage:
                self._metrics.prompt_tokens += response.usage.prompt_tokens or 0
                self._metrics.completion_tokens += response.usage.completion_tokens or 0
            
            result = response.choices[0].message.content.strip()
            
            latency = (time.time() - start_time) * 1000
            self._metrics.total_latency_ms += latency
            
            logger.debug(f"✅ LLM messages (model={model}, tokens={actual_tokens}, latency={latency:.1f}ms)")
            
            # Audit trail (Phase 4.1)
            if prompt_metadata:
                logger.info("llm_audit", extra={
                    "prompt_id": prompt_metadata.get("prompt_id"),
                    "domain": prompt_metadata.get("domain"),
                    "model": model,
                    "tokens": actual_tokens,
                    "tenant_id": prompt_metadata.get("tenant_id"),
                    "latency_ms": round(latency, 1),
                })
            
            return result
            
        except Exception as e:
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            self._metrics.errors += 1
            logger.error(f"❌ LLM messages error: {e}")
            raise LLMError(f"LLM call failed: {e}") from e
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self._metrics.to_dict()
    
    def reset_metrics(self) -> None:
        """Reset metrics."""
        self._metrics = LLMMetrics()
    
    def _generate_cache_key(self, prompt: str, system_prompt: str, model: str) -> str:
        """Generate cache key from prompt and settings."""
        key_data = {
            "prompt": prompt,
            "system_prompt": system_prompt or "",
            "model": model,
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def _get_cached(self, cache_key: str) -> Optional[str]:
        """Get cached response."""
        try:
            if self.cache:
                entry = self.cache.get_cached_response(cache_key)
                if entry:
                    return entry.response
        except Exception as e:
            logger.warning(f"⚠️ Cache get error: {e}")
        return None
    
    def _set_cached(self, cache_key: str, response: str, ttl_hours: int, state: Dict[str, Any] = None, model: str = None, tokens_used: int = 0) -> None:
        """Set cached response."""
        try:
            if self.cache:
                self.cache.cache_response(
                    cache_key=cache_key,
                    response=response,
                    state=state or {},
                    model=model or self.default_model,
                    tokens_used=tokens_used,
                )
        except Exception as e:
            logger.warning(f"⚠️ Cache set error: {e}")


# ===========================================================================
# EXCEPTIONS
# ===========================================================================

class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limited."""
    pass


class LLMCircuitOpenError(LLMError):
    """Raised when circuit breaker is open."""
    pass


# ===========================================================================
# CONVENIENCE FUNCTION
# ===========================================================================

def get_llm_agent() -> LLMAgent:
    """
    Get the singleton LLMAgent instance.
    
    Usage:
        from core.agents.llm_agent import get_llm_agent
        
        llm = get_llm_agent()
        response = llm.complete(prompt="Classify intent", system_prompt="...")
    """
    return LLMAgent()


# ===========================================================================
# EXPORTS
# ===========================================================================

__all__ = [
    "LLMAgent",
    "get_llm_agent",
    "LLMError",
    "LLMRateLimitError",
    "LLMCircuitOpenError",
    "RateLimiter",
    "CircuitBreaker",
    "LLMMetrics",
]
