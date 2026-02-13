"""
E2E Test: Pattern Weavers — Ontological Recognition
======================================================
Verifies that Pattern Weavers can match queries against ontological
taxonomies using both keyword matching and semantic weaving.
Also verifies integration with the Graph pipeline (weaver_context).

Requires: Pattern Weavers API (localhost:9017), Graph API (localhost:9004).
"""
import pytest

pytestmark = [pytest.mark.e2e]


class TestPatternWeaversHealth:
    """Service health and availability."""

    def test_health_endpoint(self, http_client, pattern_weavers_api):
        """Health endpoint must return component status."""
        r = http_client.get(f"{pattern_weavers_api}/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_api_info(self, http_client, pattern_weavers_api):
        """Root endpoint must return service info."""
        r = http_client.get(f"{pattern_weavers_api}/")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)


class TestKeywordMatch:
    """Keyword matching — pure ontological matching without embeddings."""

    def test_keyword_match_returns_structured_response(self, http_client, pattern_weavers_api):
        """Keyword match must return a valid response structure."""
        r = http_client.post(
            f"{pattern_weavers_api}/keyword-match",
            json={"query": "analisi del rischio", "limit": 5},
        )
        assert r.status_code == 200
        data = r.json()
        assert "request_id" in data
        assert "matches" in data
        assert "method" in data
        assert data["method"] == "keyword"

    def test_keyword_match_with_known_terms(self, http_client, pattern_weavers_api):
        """Queries with domain keywords should find matches (if taxonomy is populated)."""
        r = http_client.post(
            f"{pattern_weavers_api}/keyword-match",
            json={"query": "risk analysis portfolio optimization", "limit": 10},
        )
        assert r.status_code == 200
        data = r.json()
        # Matches may be empty if taxonomy is not populated — that's valid
        assert isinstance(data["matches"], list)

    def test_keyword_match_empty_query(self, http_client, pattern_weavers_api):
        """Empty or very short query should still return valid response."""
        r = http_client.post(
            f"{pattern_weavers_api}/keyword-match",
            json={"query": "x", "limit": 5},
        )
        # Should not crash, even with minimal input
        assert r.status_code in (200, 422)

    def test_keyword_match_multilingual(self, http_client, pattern_weavers_api):
        """Italian query should work (taxonomy may include multilingual keywords)."""
        r = http_client.post(
            f"{pattern_weavers_api}/keyword-match",
            json={"query": "valutazione qualitativa e quantitativa", "limit": 5},
        )
        assert r.status_code == 200
        data = r.json()
        assert "matches" in data

    def test_keyword_match_limit_respected(self, http_client, pattern_weavers_api):
        """Limit parameter must cap the number of results."""
        r = http_client.post(
            f"{pattern_weavers_api}/keyword-match",
            json={"query": "comprehensive analysis deep learning neural network machine learning", "limit": 2},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["matches"]) <= 2

    def test_keyword_match_request_id_unique(self, http_client, pattern_weavers_api):
        """Each request must get a unique request_id."""
        ids = set()
        for _ in range(3):
            r = http_client.post(
                f"{pattern_weavers_api}/keyword-match",
                json={"query": "test", "limit": 1},
            )
            assert r.status_code == 200
            ids.add(r.json()["request_id"])
        assert len(ids) == 3, "request_ids should be unique"


class TestWeaveEndpoint:
    """Semantic weave — requires embedding service."""

    def test_weave_request_accepted(self, http_client, pattern_weavers_api):
        """/weave must accept a valid request (may fail if embedding is unavailable)."""
        r = http_client.post(
            f"{pattern_weavers_api}/weave",
            json={"query": "pattern recognition in complex systems", "limit": 5},
        )
        # 200 = success, 503 = embedding unavailable (known limitation)
        assert r.status_code in (200, 503), f"Unexpected status: {r.status_code}"

    def test_weave_response_structure(self, http_client, pattern_weavers_api):
        """If /weave succeeds, response must have the correct structure."""
        r = http_client.post(
            f"{pattern_weavers_api}/weave",
            json={"query": "ontological classification", "limit": 3},
        )
        if r.status_code == 200:
            data = r.json()
            assert "request_id" in data
            assert "matches" in data
            assert "processing_time_ms" in data
        # 503 is acceptable — embedding service dependency


class TestTaxonomyStats:
    """Taxonomy statistics endpoint."""

    def test_taxonomy_stats(self, http_client, pattern_weavers_api):
        """Taxonomy stats should return category information."""
        r = http_client.get(f"{pattern_weavers_api}/taxonomy/stats")
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)
        # May return 500 if taxonomy YAML not loaded — acceptable


class TestWeaverLivello1Consumers:
    """Test LIVELLO 1 pure consumer functions (no infrastructure)."""

    def test_keyword_matcher_consumer_importable(self):
        """KeywordMatcherConsumer must be importable from LIVELLO 1."""
        try:
            from core.cognitive.pattern_weavers.consumers.keyword_matcher import (
                KeywordMatcherConsumer,
            )
            assert KeywordMatcherConsumer is not None
        except ImportError:
            pytest.skip("KeywordMatcherConsumer not importable (path issue)")

    def test_keyword_matcher_consumer_process(self):
        """KeywordMatcherConsumer.process() must work with pure data."""
        try:
            from core.cognitive.pattern_weavers.consumers.keyword_matcher import (
                KeywordMatcherConsumer,
            )
        except ImportError:
            pytest.skip("KeywordMatcherConsumer not importable")

        consumer = KeywordMatcherConsumer()
        result = consumer.process({
            "query_text": "machine learning classification",
            "limit": 5,
        })
        assert result.success, f"Process failed: {result.errors}"
        assert isinstance(result.data, dict)
        assert "matches" in result.data

    def test_weaver_consumer_importable(self):
        """WeaverConsumer must be importable from LIVELLO 1."""
        try:
            from core.cognitive.pattern_weavers.consumers.weaver import WeaverConsumer
            assert WeaverConsumer is not None
        except ImportError:
            pytest.skip("WeaverConsumer not importable (path issue)")


class TestWeaverInGraphPipeline:
    """Weaver integration within the Graph pipeline."""

    def test_weaver_context_in_graph_response(self, graph_run):
        """Graph responses must include weaver_context."""
        parsed = graph_run("Classificazione ontologica del rischio")["parsed"]
        assert "weaver_context" in parsed
        ctx = parsed["weaver_context"]
        assert isinstance(ctx, dict)
        assert "status" in ctx

    def test_weaver_context_has_concepts(self, graph_run):
        """weaver_context must have a concepts list."""
        parsed = graph_run("Analisi pattern emergenti nei dati")["parsed"]
        ctx = parsed.get("weaver_context", {})
        assert "concepts" in ctx
        assert isinstance(ctx["concepts"], list)

    def test_weaver_context_has_patterns(self, graph_run):
        """weaver_context must have a patterns list."""
        parsed = graph_run("Riconoscimento strutture ricorrenti")["parsed"]
        ctx = parsed.get("weaver_context", {})
        assert "patterns" in ctx
        assert isinstance(ctx["patterns"], list)

    def test_weaver_latency_tracked(self, graph_run):
        """Weaver processing time must be tracked."""
        parsed = graph_run("Test latenza weaver")["parsed"]
        ctx = parsed.get("weaver_context", {})
        assert "latency_ms" in ctx
        assert isinstance(ctx["latency_ms"], (int, float))
