"""
Integration Test — LLMAgent caching, rate-limiting, and circuit breaker.

Tests the LLMAgent singleton against mocked OpenAI and Redis backends
to verify cache hits/misses, rate limiting, and circuit breaker behaviour.

Markers: integration
"""

import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock

from core.agents.llm_agent import (
    LLMAgent,
    LLMMetrics,
    RateLimiter,
    CircuitBreaker,
    LLMRateLimitError,
    LLMCircuitOpenError,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset LLMAgent singleton between tests."""
    LLMAgent._instance = None
    yield
    LLMAgent._instance = None


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI ChatCompletion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Test response"
    response.choices[0].message.role = "assistant"
    response.choices[0].message.tool_calls = None
    response.usage = MagicMock()
    response.usage.total_tokens = 50
    response.usage.prompt_tokens = 30
    response.usage.completion_tokens = 20
    return response


@pytest.fixture
def llm(mock_openai_response):
    """Create an LLMAgent with mocked OpenAI client."""
    with patch("core.agents.llm_agent.OPENAI_AVAILABLE", True), \
         patch("core.agents.llm_agent.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        MockOpenAI.return_value = mock_client

        agent = LLMAgent(
            api_key="test-key",
            default_model="gpt-4o-mini",
            enable_cache=False,
            enable_rate_limiting=False,
            enable_circuit_breaker=False,
        )
    return agent


class TestLLMComplete:
    """LLMAgent.complete() — basic text completion."""

    def test_complete_returns_text(self, llm):
        result = llm.complete("What is 2+2?", system_prompt="You are a calculator.")
        assert result == "Test response"

    def test_complete_increments_metrics(self, llm):
        llm.reset_metrics()
        llm.complete("prompt")
        metrics = llm.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["total_tokens"] == 50

    def test_complete_json_parses_response(self, llm):
        llm._client.chat.completions.create.return_value.choices[0].message.content = (
            '{"answer": 42}'
        )
        result = llm.complete_json("return JSON")
        assert result == {"answer": 42}

    def test_complete_json_extracts_from_markdown_fence(self, llm):
        llm._client.chat.completions.create.return_value.choices[0].message.content = (
            'Sure, here is the result:\n```json\n{"key": "value"}\n```'
        )
        result = llm.complete_json("return JSON")
        assert result == {"key": "value"}


class TestLLMCaching:
    """LLMAgent cache hit/miss behaviour."""

    def test_cache_hit_skips_api_call(self, llm):
        mock_cache = MagicMock()
        cached_entry = MagicMock()
        cached_entry.response = "cached answer"
        mock_cache.get_cached_response.return_value = cached_entry

        llm._enable_cache = True
        llm._cache = mock_cache
        llm.reset_metrics()

        result = llm.complete("prompt")

        assert result == "cached answer"
        llm._client.chat.completions.create.assert_not_called()
        assert llm.get_metrics()["cache_hits"] == 1

    def test_cache_miss_calls_api_and_stores(self, llm):
        mock_cache = MagicMock()
        mock_cache.get_cached_response.return_value = None

        llm._enable_cache = True
        llm._cache = mock_cache
        llm.reset_metrics()

        result = llm.complete("prompt")

        assert result == "Test response"
        llm._client.chat.completions.create.assert_called_once()
        assert llm.get_metrics()["cache_misses"] == 1

    def test_skip_cache_bypasses_lookup(self, llm):
        mock_cache = MagicMock()
        llm._enable_cache = True
        llm._cache = mock_cache
        llm.reset_metrics()

        llm.complete("prompt", skip_cache=True)

        mock_cache.get_cached_response.assert_not_called()


class TestRateLimiter:
    """RateLimiter token-bucket logic."""

    def test_acquire_within_limits(self):
        rl = RateLimiter(rpm=100, tpm=10000)
        assert rl.acquire(500) is True

    def test_acquire_exceeds_rpm(self):
        rl = RateLimiter(rpm=2, tpm=100000)
        rl.acquire(10)
        rl.acquire(10)
        assert rl.acquire(10) is False

    def test_acquire_exceeds_tpm(self):
        rl = RateLimiter(rpm=1000, tpm=100)
        assert rl.acquire(150) is False


class TestCircuitBreaker:
    """CircuitBreaker state transitions."""

    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.can_execute() is True

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        assert cb.can_execute() is False

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb._failure_count == 0

    def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()
        # With recovery_timeout=0.0, accessing state immediately transitions
        # from OPEN to HALF_OPEN
        import time
        time.sleep(0.01)
        assert cb.state == CircuitBreaker.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()
        import time
        time.sleep(0.01)
        _ = cb.state  # trigger HALF_OPEN transition
        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED
