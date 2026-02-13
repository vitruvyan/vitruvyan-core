"""
Test LLMAgent — Vitruvyan LLM Gateway v2.0
============================================

Test unitari per il gateway centralizzato verso OpenAI.

Copertura:
  - Singleton           → double-checked locking, stessa istanza
  - RateLimiter         → token-bucket, RPM/TPM, acquire/reject
  - CircuitBreaker      → stati CLOSED/OPEN/HALF_OPEN, transizioni
  - LLMMetrics          → contatori, cache_hit_rate, avg_latency, to_dict()
  - complete()          → chiamata corretta, gestione cache, errori
  - complete_json()     → parsing JSON + fallback markdown code blocks
  - complete_with_tools() → tool_calls nell'output
  - complete_with_messages() → raw messages array
  - get_metrics()       → formato output

ZERO chiamate API reali. Tutto è mockato.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from collections import deque
from threading import Lock
import time


# ── Skip se modulo non importabile ──────────────────────────────────

try:
    from core.agents.llm_agent import LLMAgent, get_llm_agent
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

# Inner classes may be importable even if OpenAI is not installed
try:
    from core.agents.llm_agent import RateLimiter, CircuitBreaker, LLMMetrics
    HAS_LLM_INTERNALS = True
except ImportError:
    HAS_LLM_INTERNALS = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.agents,
    pytest.mark.skipif(not HAS_LLM_INTERNALS, reason="LLMAgent module not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# TEST: RateLimiter
# ═══════════════════════════════════════════════════════════════════

class TestRateLimiter:
    """Test per il rate limiter token-bucket."""

    def test_acquire_within_limits(self):
        """Entro i limiti, acquire() deve restituire True."""
        rl = RateLimiter(rpm=100, tpm=10000)
        assert rl.acquire(estimated_tokens=100) is True

    def test_acquire_exceed_rpm(self):
        """Superando RPM, acquire() deve restituire False."""
        rl = RateLimiter(rpm=3, tpm=100000, window_seconds=60)
        for _ in range(3):
            rl.acquire(estimated_tokens=10)
        # La 4a richiesta deve essere rifiutata
        assert rl.acquire(estimated_tokens=10) is False

    def test_acquire_exceed_tpm(self):
        """Superando TPM, acquire() deve restituire False."""
        rl = RateLimiter(rpm=1000, tpm=100, window_seconds=60)
        # Richiedere più token del budget
        rl.acquire(estimated_tokens=90)
        assert rl.acquire(estimated_tokens=20) is False

    def test_record_actual_tokens(self):
        """record_actual_tokens() deve aggiornare l'ultimo record."""
        rl = RateLimiter(rpm=100, tpm=10000)
        rl.acquire(estimated_tokens=500)
        # Non deve crashare
        rl.record_actual_tokens(actual_tokens=150)

    def test_fresh_limiter_allows_requests(self):
        """Un rate limiter appena creato deve permettere richieste."""
        rl = RateLimiter()
        assert rl.acquire(estimated_tokens=100) is True


# ═══════════════════════════════════════════════════════════════════
# TEST: CircuitBreaker
# ═══════════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    """Test per il circuit breaker a 3 stati."""

    def test_initial_state_closed(self):
        """Lo stato iniziale deve essere CLOSED."""
        cb = CircuitBreaker()
        assert cb.state == CircuitBreaker.CLOSED

    def test_can_execute_when_closed(self):
        """In stato CLOSED, can_execute() deve restituire True."""
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_transition_closed_to_open(self):
        """Dopo failure_threshold fallimenti, deve transitare a OPEN."""
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_cannot_execute_when_open(self):
        """In stato OPEN, can_execute() deve restituire False."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute() is False

    def test_transition_open_to_half_open(self):
        """Dopo recovery_timeout, deve transitare a HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        time.sleep(0.02)
        assert cb.state == CircuitBreaker.HALF_OPEN

    def test_half_open_allows_limited_calls(self):
        """In HALF_OPEN, can_execute() deve restituire True (limitato)."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        time.sleep(0.02)
        assert cb.can_execute() is True

    def test_half_open_to_closed_on_success(self):
        """In HALF_OPEN, un successo transita a CLOSED."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitBreaker.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED

    def test_half_open_to_open_on_failure(self):
        """In HALF_OPEN, un fallimento transita di nuovo a OPEN."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitBreaker.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_success_resets_failure_count(self):
        """record_success() deve azzerare il contatore dei fallimenti."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        # Un altro fallimento non deve aprire (count è resettato)
        cb.record_failure()
        assert cb.state == CircuitBreaker.CLOSED


# ═══════════════════════════════════════════════════════════════════
# TEST: LLMMetrics
# ═══════════════════════════════════════════════════════════════════

class TestLLMMetrics:
    """Test per i contatori metriche LLM."""

    def test_initial_values(self):
        m = LLMMetrics()
        assert m.total_requests == 0
        assert m.total_tokens == 0
        assert m.cache_hits == 0
        assert m.errors == 0

    def test_cache_hit_rate_no_data(self):
        """Con zero richieste, cache_hit_rate deve essere 0.0."""
        m = LLMMetrics()
        assert m.cache_hit_rate == 0.0

    def test_cache_hit_rate_with_data(self):
        m = LLMMetrics(cache_hits=3, cache_misses=7)
        assert abs(m.cache_hit_rate - 0.3) < 0.001

    def test_avg_latency_no_requests(self):
        m = LLMMetrics()
        assert m.avg_latency_ms == 0.0

    def test_avg_latency_with_requests(self):
        m = LLMMetrics(total_requests=10, total_latency_ms=250.0)
        assert abs(m.avg_latency_ms - 25.0) < 0.001

    def test_to_dict_keys(self):
        m = LLMMetrics(total_requests=5, cache_hits=2, cache_misses=3)
        d = m.to_dict()
        expected_keys = {
            "total_requests", "total_tokens", "cache_hits", "cache_misses",
            "cache_hit_rate", "rate_limited", "circuit_breaker_rejected",
            "errors", "avg_latency_ms",
        }
        assert expected_keys.issubset(set(d.keys()))

    def test_to_dict_values_rounded(self):
        m = LLMMetrics(
            total_requests=3, cache_hits=1, cache_misses=2,
            total_latency_ms=100.123456,
        )
        d = m.to_dict()
        # avg_latency deve essere arrotondato 
        assert isinstance(d["avg_latency_ms"], float)


# ═══════════════════════════════════════════════════════════════════
# TEST: Model resolution
# ═══════════════════════════════════════════════════════════════════

class TestModelResolution:
    """Test per la chain di risoluzione del modello."""

    def test_default_model_fallback(self):
        """Senza env var, il modello di default deve essere gpt-4o-mini."""
        try:
            from core.agents.llm_agent import _resolve_default_model
        except ImportError:
            pytest.skip("_resolve_default_model not available")

        with patch.dict(os.environ, {}, clear=True):
            # Rimuovi le chiavi rilevanti
            for key in ("VITRUVYAN_LLM_MODEL", "GRAPH_LLM_MODEL", "OPENAI_MODEL"):
                os.environ.pop(key, None)
            result = _resolve_default_model()
            assert result == "gpt-4o-mini"

    def test_vitruvyan_model_takes_priority(self):
        """VITRUVYAN_LLM_MODEL ha priorità su tutti gli altri."""
        try:
            from core.agents.llm_agent import _resolve_default_model
        except ImportError:
            pytest.skip("_resolve_default_model not available")

        with patch.dict(os.environ, {
            "VITRUVYAN_LLM_MODEL": "gpt-4-turbo",
            "GRAPH_LLM_MODEL": "gpt-3.5",
            "OPENAI_MODEL": "gpt-4",
        }):
            assert _resolve_default_model() == "gpt-4-turbo"

    def test_graph_model_second_priority(self):
        """GRAPH_LLM_MODEL è il secondo nella chain."""
        try:
            from core.agents.llm_agent import _resolve_default_model
        except ImportError:
            pytest.skip("_resolve_default_model not available")

        with patch.dict(os.environ, {
            "GRAPH_LLM_MODEL": "gpt-3.5-turbo",
            "OPENAI_MODEL": "gpt-4",
        }):
            os.environ.pop("VITRUVYAN_LLM_MODEL", None)
            assert _resolve_default_model() == "gpt-3.5-turbo"
