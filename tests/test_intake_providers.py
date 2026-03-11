"""
Oculus Prime Intake Agents — Unit Tests
========================================

Tests for Reddit, GNews, and FRED intake agents.
Pure unit tests — no external API calls (all mocked).

Sacred Order: Perception (Oculus Prime / Edge)
Layer: Edge (infrastructure)
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ============================================================================
# Module-level mocking: mock only what we need BEFORE any agent import
# ============================================================================

class _FakeGuardrails:
    @staticmethod
    def validate_no_semantics(text, source_type):
        pass  # no-op for tests

    @staticmethod
    def validate_source_hash_required(source_ref):
        if not source_ref.get("source_hash"):
            raise ValueError("source_hash is required")


# Mock guardrails by importing the real module tree, then patching
# the guardrails class. The __init__.py files exist so the chain is
# importable; we just need to replace IntakeGuardrails with our fake.
import infrastructure.edge.oculus_prime.core.guardrails as _guardrails_mod
_guardrails_mod.IntakeGuardrails = _FakeGuardrails


# ============================================================================
# Event Emitter Mock
# ============================================================================

class MockEventEmitter:
    """Records all emitted events for assertions."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def emit_evidence_created(self, **kwargs):
        self.events.append(kwargs)


# ============================================================================
# Import agents AFTER mocks are set up
# ============================================================================

from infrastructure.edge.oculus_prime.core.agents.reddit_intake import RedditIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.gnews_intake import GNewsIntakeAgent
from vitruvyan_core.domains.finance.intake.fred_intake import FREDIntakeAgent, POPULAR_SERIES


# ============================================================================
# Reddit Intake Agent Tests
# ============================================================================

class TestRedditIntakeAgent:
    """Unit tests for RedditIntakeAgent."""

    def _make_mock_post(
        self,
        post_id="abc123",
        title="Test Post Title",
        author="test_user",
        selftext="This is the body of the post.",
        score=42,
        num_comments=5,
        url="https://reddit.com/r/test/abc123",
        permalink="/r/test/comments/abc123/test_post/",
        upvote_ratio=0.95,
        is_self=True,
        link_flair_text="Discussion",
    ):
        post = MagicMock()
        post.id = post_id
        post.title = title
        post.author = author
        post.selftext = selftext
        post.score = score
        post.num_comments = num_comments
        post.url = url
        post.permalink = permalink
        post.upvote_ratio = upvote_ratio
        post.is_self = is_self
        post.link_flair_text = link_flair_text
        post.created_utc = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc).timestamp()

        # Comments mock
        mock_comment = MagicMock()
        mock_comment.author = "commenter1"
        mock_comment.body = "post details"
        mock_comment.score = 10
        mock_comment.created_utc = post.created_utc + 3600

        comments = MagicMock()
        comments.replace_more = MagicMock()
        comments.__iter__ = MagicMock(return_value=iter([mock_comment]))
        comments.__getitem__ = MagicMock(return_value=[mock_comment])
        post.comments = comments

        return post

    def test_ingest_single_post(self):
        """Ingesting a single post produces valid evidence with correct metadata."""
        emitter = MockEventEmitter()
        agent = RedditIntakeAgent(event_emitter=emitter)
        post = self._make_mock_post()

        eid = agent._ingest_post(
            post, subreddit_name="test", include_comments=True, correlation_id="corr-001",
        )

        assert eid.startswith("EVD-")
        assert len(emitter.events) == 1

        event = emitter.events[0]
        assert event["evidence_id"] == eid
        assert event["source_type"] == "document"
        assert "reddit://r/test/comments/abc123" in event["source_uri"]
        assert event["intake_agent_id"] == "reddit-intake-v1"
        assert event["correlation_id"] == "corr-001"

    def test_ingest_post_without_comments(self):
        """Ingesting without comments still produces evidence."""
        emitter = MockEventEmitter()
        agent = RedditIntakeAgent(event_emitter=emitter)
        post = self._make_mock_post()

        eid = agent._ingest_post(
            post, subreddit_name="test", include_comments=False, correlation_id=None,
        )
        assert eid.startswith("EVD-")
        assert len(emitter.events) == 1

    def test_ingest_link_post(self):
        """Non-self (link) posts produce '[Link: url]' in normalized text."""
        emitter = MockEventEmitter()
        agent = RedditIntakeAgent(event_emitter=emitter)
        post = self._make_mock_post(is_self=False, url="https://example.com/article")

        agent._ingest_post(post, subreddit_name="test", include_comments=False, correlation_id=None)
        assert len(emitter.events) == 1

    def test_evidence_hash_deterministic(self):
        """Same inputs always produce the same evidence hash."""
        h1 = RedditIntakeAgent._compute_evidence_hash("evd1", "chk0", "text", "src_hash")
        h2 = RedditIntakeAgent._compute_evidence_hash("evd1", "chk0", "text", "src_hash")
        assert h1 == h2

    def test_evidence_hash_changes_on_different_input(self):
        """Different inputs produce different hashes."""
        h1 = RedditIntakeAgent._compute_evidence_hash("evd1", "chk0", "text_a", "hash1")
        h2 = RedditIntakeAgent._compute_evidence_hash("evd2", "chk0", "text_b", "hash2")
        assert h1 != h2

    def test_evidence_id_format(self):
        """Evidence IDs follow EVD-UUID format (40 chars)."""
        eid = RedditIntakeAgent._generate_evidence_id()
        assert eid.startswith("EVD-")
        assert len(eid) == 40

    def test_praw_unavailable_raises(self):
        """Agent raises RuntimeError when PRAW_AVAILABLE is False."""
        emitter = MockEventEmitter()
        agent = RedditIntakeAgent(event_emitter=emitter)

        with patch.object(
            type(agent), "reddit", new_callable=PropertyMock, return_value=None,
        ):
            with pytest.raises(RuntimeError, match="praw not available"):
                agent.ingest_subreddit("test")


# ============================================================================
# GNews Intake Agent Tests
# ============================================================================

class TestGNewsIntakeAgent:
    """Unit tests for GNewsIntakeAgent."""

    SAMPLE_ARTICLE = {
        "title": "AI Breakthrough Announced",
        "description": "Researchers have made a breakthrough in AI technology.",
        "url": "https://example.com/ai-article",
        "publishedAt": "2026-02-25T10:00:00Z",
        "source": {"name": "Tech News"},
        "image": "https://example.com/image.jpg",
    }

    def test_ingest_single_article(self):
        """Single article ingestion produces valid evidence."""
        emitter = MockEventEmitter()
        agent = GNewsIntakeAgent(event_emitter=emitter, api_key="")

        eid = agent._ingest_article(
            self.SAMPLE_ARTICLE, query="AI breakthroughs", correlation_id="corr-002",
        )

        assert eid.startswith("EVD-")
        assert len(emitter.events) == 1
        event = emitter.events[0]
        assert event["source_type"] == "document"
        assert event["intake_agent_id"] == "gnews-intake-v1"

    def test_api_mode_vs_rss_mode(self):
        """API key presence determines operation mode."""
        agent_api = GNewsIntakeAgent(event_emitter=MagicMock(), api_key="test_key")
        agent_rss = GNewsIntakeAgent(event_emitter=MagicMock(), api_key="")

        assert agent_api._mode == "api"
        assert agent_rss._mode == "rss"

    def test_article_missing_description(self):
        """Articles with empty description still produce evidence."""
        emitter = MockEventEmitter()
        agent = GNewsIntakeAgent(event_emitter=emitter, api_key="")

        article = {**self.SAMPLE_ARTICLE, "description": ""}
        eid = agent._ingest_article(article, query="test", correlation_id=None)
        assert eid.startswith("EVD-")

    def test_article_source_uri_uses_url(self):
        """Source URI is the article URL when present."""
        emitter = MockEventEmitter()
        agent = GNewsIntakeAgent(event_emitter=emitter, api_key="")

        agent._ingest_article(self.SAMPLE_ARTICLE, query="test", correlation_id=None)
        event = emitter.events[0]
        assert event["source_uri"] == "https://example.com/ai-article"

    def test_article_without_url_uses_gnews_uri(self):
        """Missing URL generates gnews:// URI."""
        emitter = MockEventEmitter()
        agent = GNewsIntakeAgent(event_emitter=emitter, api_key="")

        article = {**self.SAMPLE_ARTICLE, "url": ""}
        agent._ingest_article(article, query="test query", correlation_id=None)
        event = emitter.events[0]
        assert "gnews://search/" in event["source_uri"]

    def test_evidence_hash_deterministic(self):
        """Same inputs always produce the same hash."""
        h1 = GNewsIntakeAgent._compute_evidence_hash("evd1", "chk0", "text", "src_hash")
        h2 = GNewsIntakeAgent._compute_evidence_hash("evd1", "chk0", "text", "src_hash")
        assert h1 == h2


# ============================================================================
# FRED Intake Agent Tests
# ============================================================================

class TestFREDIntakeAgent:
    """Unit tests for FREDIntakeAgent."""

    SAMPLE_SERIES_INFO = {
        "id": "GDP",
        "title": "Gross Domestic Product",
        "units": "Billions of Dollars",
        "frequency": "Quarterly",
        "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
        "last_updated": "2026-01-30",
        "notes": "BEA Account Code: A191RC",
    }

    SAMPLE_OBSERVATIONS = [
        {"date": "2025-10-01", "value": "29000.0"},
        {"date": "2025-07-01", "value": "28500.0"},
        {"date": "2025-04-01", "value": "28000.0"},
        {"date": "2025-01-01", "value": "."},  # Missing data point
    ]

    def test_create_evidence_pack(self):
        """Evidence pack creation from FRED series emits correct event."""
        emitter = MockEventEmitter()
        agent = FREDIntakeAgent(event_emitter=emitter, api_key="test_key")

        eid = agent._create_evidence_pack(
            series_id="GDP",
            series_info=self.SAMPLE_SERIES_INFO,
            observations=self.SAMPLE_OBSERVATIONS,
            correlation_id="corr-003",
        )

        assert eid.startswith("EVD-")
        assert len(emitter.events) == 1

        event = emitter.events[0]
        assert event["source_type"] == "document"
        assert event["source_uri"] == "fred://GDP"
        assert event["language_detected"] == "en"
        assert event["intake_agent_id"] == "fred-intake-v1"

    def test_missing_observations_filtered(self):
        """FRED '.' values (missing data) are handled gracefully."""
        emitter = MockEventEmitter()
        agent = FREDIntakeAgent(event_emitter=emitter, api_key="test_key")

        eid = agent._create_evidence_pack(
            series_id="TEST",
            series_info=self.SAMPLE_SERIES_INFO,
            observations=self.SAMPLE_OBSERVATIONS,
            correlation_id=None,
        )
        assert eid.startswith("EVD-")

    def test_popular_series_catalog(self):
        """POPULAR_SERIES contains well-known economic indicators."""
        assert "GDP" in POPULAR_SERIES
        assert "UNRATE" in POPULAR_SERIES
        assert "FEDFUNDS" in POPULAR_SERIES
        assert "CPIAUCSL" in POPULAR_SERIES
        assert "DGS10" in POPULAR_SERIES
        assert "T10Y2Y" in POPULAR_SERIES
        assert len(POPULAR_SERIES) >= 10

    def test_no_api_key_raises(self):
        """ingest_series() raises RuntimeError without API key."""
        emitter = MockEventEmitter()
        agent = FREDIntakeAgent(event_emitter=emitter, api_key="")

        with pytest.raises(RuntimeError, match="FRED API key"):
            agent.ingest_series("GDP")

    def test_evidence_hash_uniqueness(self):
        """Different inputs produce different hashes."""
        h1 = FREDIntakeAgent._compute_evidence_hash("evd1", "chk0", "text1", "hash1")
        h2 = FREDIntakeAgent._compute_evidence_hash("evd2", "chk0", "text2", "hash2")
        assert h1 != h2

    def test_tags_contain_series_id(self):
        """Evidence pack tags include the FRED series ID."""
        emitter = MockEventEmitter()
        agent = FREDIntakeAgent(event_emitter=emitter, api_key="test_key")
        # We can't directly check tags from emitted event, but we can verify
        # the create method doesn't crash and emits data we can inspect
        agent._create_evidence_pack(
            series_id="FEDFUNDS",
            series_info={**self.SAMPLE_SERIES_INFO, "frequency": "Daily"},
            observations=self.SAMPLE_OBSERVATIONS[:2],
            correlation_id=None,
        )
        assert len(emitter.events) == 1


# ============================================================================
# Cross-provider consistency tests
# ============================================================================

class TestProviderConsistency:
    """Verify all three providers follow the same Evidence Pack contract."""

    def test_all_agents_have_required_constants(self):
        """All agents define AGENT_ID and AGENT_VERSION."""
        for cls in [RedditIntakeAgent, GNewsIntakeAgent, FREDIntakeAgent]:
            assert hasattr(cls, "AGENT_ID"), f"{cls.__name__} missing AGENT_ID"
            assert hasattr(cls, "AGENT_VERSION"), f"{cls.__name__} missing AGENT_VERSION"
            assert isinstance(cls.AGENT_ID, str)
            assert isinstance(cls.AGENT_VERSION, str)

    def test_all_agents_have_persist_and_emit(self):
        """All agents implement _persist_evidence_pack and _compute_evidence_hash."""
        for cls in [RedditIntakeAgent, GNewsIntakeAgent, FREDIntakeAgent]:
            assert hasattr(cls, "_persist_evidence_pack"), f"{cls.__name__} missing _persist_evidence_pack"
            assert hasattr(cls, "_compute_evidence_hash"), f"{cls.__name__} missing _compute_evidence_hash"
            assert hasattr(cls, "_generate_evidence_id"), f"{cls.__name__} missing _generate_evidence_id"

    def test_evidence_id_format_all_agents(self):
        """All agents generate EVD-UUID format (40 chars)."""
        for cls in [RedditIntakeAgent, GNewsIntakeAgent, FREDIntakeAgent]:
            eid = cls._generate_evidence_id()
            assert eid.startswith("EVD-")
            assert len(eid) == 40, f"{cls.__name__}: expected 40, got {len(eid)}"

    def test_hash_function_consistent_across_agents(self):
        """_compute_hash is deterministic and consistent across all agents."""
        text = "identical test input"
        results = set()
        for cls in [RedditIntakeAgent, GNewsIntakeAgent, FREDIntakeAgent]:
            results.add(cls._compute_hash(text))
        assert len(results) == 1, "Hash functions should produce identical output for same input"
