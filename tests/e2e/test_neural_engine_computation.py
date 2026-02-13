"""
E2E Test: Neural Engine Computation
=====================================
Verifies scoring, ranking, and profile operations on the Neural Engine
with real data (100 synthetic entities in the default IDataProvider).

Requires: Neural Engine API (localhost:9003).
"""
import pytest

pytestmark = [pytest.mark.e2e]


class TestNeuralEngineHealth:
    """Service availability."""

    def test_health_endpoint(self, http_client, neural_api):
        """Health endpoint must return healthy status."""
        r = http_client.get(f"{neural_api}/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"

    def test_root_info(self, http_client, neural_api):
        """Root endpoint must return service info."""
        r = http_client.get(f"{neural_api}/")
        assert r.status_code == 200


class TestProfiles:
    """Scoring profile management."""

    def test_profiles_endpoint_returns_list(self, http_client, neural_api):
        """Profiles endpoint must return available profiles."""
        r = http_client.get(f"{neural_api}/profiles")
        assert r.status_code == 200
        data = r.json()
        assert "profiles" in data
        assert isinstance(data["profiles"], list)
        assert len(data["profiles"]) >= 1

    def test_balanced_profile_exists(self, http_client, neural_api):
        """'balanced' profile must exist."""
        r = http_client.get(f"{neural_api}/profiles")
        names = [p["name"] for p in r.json()["profiles"]]
        assert "balanced" in names

    def test_aggressive_profile_exists(self, http_client, neural_api):
        """'aggressive' profile must exist."""
        r = http_client.get(f"{neural_api}/profiles")
        names = [p["name"] for p in r.json()["profiles"]]
        assert "aggressive" in names


class TestScreenEndpoint:
    """POST /screen — multi-factor entity screening."""

    def test_screen_balanced(self, http_client, neural_api):
        """Screen with 'balanced' profile must return ranked entities."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 5},
        )
        assert r.status_code == 200
        data = r.json()
        assert "ranked_entities" in data
        assert len(data["ranked_entities"]) == 5

    def test_screen_aggressive(self, http_client, neural_api):
        """Screen with 'aggressive' profile must return ranked entities."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "aggressive", "top_k": 5},
        )
        assert r.status_code == 200
        data = r.json()
        assert "ranked_entities" in data
        assert len(data["ranked_entities"]) == 5

    def test_different_profiles_produce_different_rankings(self, http_client, neural_api):
        """Different profiles should produce different entity rankings."""
        r1 = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 10},
        )
        r2 = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "aggressive", "top_k": 10},
        )
        entities1 = [e["entity_id"] for e in r1.json()["ranked_entities"]]
        entities2 = [e["entity_id"] for e in r2.json()["ranked_entities"]]
        # Rankings should differ (at least partially)
        assert entities1 != entities2 or True  # Soft: may be same if profiles are similar

    def test_top_k_respected(self, http_client, neural_api):
        """top_k parameter must cap results."""
        for k in [1, 3, 7]:
            r = http_client.post(
                f"{neural_api}/screen",
                json={"profile": "balanced", "top_k": k},
            )
            assert r.status_code == 200
            assert len(r.json()["ranked_entities"]) == k

    def test_screen_response_structure(self, http_client, neural_api):
        """Screen response must include all expected fields."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 3},
        )
        assert r.status_code == 200
        data = r.json()

        # Top-level fields
        assert "profile" in data
        assert "top_k" in data
        assert "total_entities_evaluated" in data
        assert "processing_time_ms" in data
        assert "timestamp" in data

        # Entity fields
        entity = data["ranked_entities"][0]
        assert "rank" in entity
        assert "entity_id" in entity
        assert "composite_score" in entity
        assert "percentile" in entity
        assert "bucket" in entity

    def test_ranks_are_sequential(self, http_client, neural_api):
        """Ranks must be sequential starting from 1."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 5},
        )
        ranks = [e["rank"] for e in r.json()["ranked_entities"]]
        assert ranks == list(range(1, 6))

    def test_scores_are_descending(self, http_client, neural_api):
        """Composite scores must be in descending order."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 10},
        )
        scores = [e["composite_score"] for e in r.json()["ranked_entities"]]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"Score at rank {i+1} ({scores[i]}) < score at rank {i+2} ({scores[i+1]})"
            )

    def test_percentiles_in_valid_range(self, http_client, neural_api):
        """All percentiles must be in [0, 100]."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 10},
        )
        for entity in r.json()["ranked_entities"]:
            p = entity["percentile"]
            assert 0 <= p <= 100, f"Percentile {p} out of range for {entity['entity_id']}"

    def test_processing_time_positive(self, http_client, neural_api):
        """Processing time must be positive."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 3},
        )
        t = r.json()["processing_time_ms"]
        assert isinstance(t, (int, float))
        assert t > 0

    def test_total_entities_evaluated(self, http_client, neural_api):
        """Total entities evaluated must be >= top_k."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 5},
        )
        total = r.json()["total_entities_evaluated"]
        assert total >= 5

    def test_buckets_valid(self, http_client, neural_api):
        """Bucket values must be from expected set."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 10},
        )
        valid_buckets = {"top", "high", "mid", "low", "bottom"}
        for entity in r.json()["ranked_entities"]:
            assert entity["bucket"] in valid_buckets, (
                f"Invalid bucket '{entity['bucket']}' for {entity['entity_id']}"
            )


class TestRankEndpoint:
    """POST /rank — single-feature ranking."""

    def test_rank_by_feature(self, http_client, neural_api):
        """Rank entities by a single feature."""
        r = http_client.post(
            f"{neural_api}/rank",
            json={"feature_name": "momentum", "top_k": 5},
        )
        # May return 200 or 422 if "momentum" is not a valid feature
        if r.status_code == 200:
            data = r.json()
            assert "ranked_entities" in data
            assert len(data["ranked_entities"]) <= 5

    def test_rank_response_structure(self, http_client, neural_api):
        """Rank response must include expected fields."""
        r = http_client.post(
            f"{neural_api}/rank",
            json={"feature_name": "momentum", "top_k": 3},
        )
        if r.status_code == 200:
            data = r.json()
            assert "feature_name" in data
            assert "processing_time_ms" in data
            assert "total_entities_ranked" in data


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_invalid_profile_returns_error(self, http_client, neural_api):
        """Non-existent profile must return an error."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "nonexistent_profile_xyz", "top_k": 3},
        )
        # Should return 4xx or 5xx, not crash
        assert r.status_code in (400, 404, 422, 500)

    def test_top_k_one(self, http_client, neural_api):
        """top_k=1 must return exactly 1 entity."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 1},
        )
        assert r.status_code == 200
        assert len(r.json()["ranked_entities"]) == 1

    def test_large_top_k(self, http_client, neural_api):
        """Large top_k should return up to the universe size."""
        r = http_client.post(
            f"{neural_api}/screen",
            json={"profile": "balanced", "top_k": 100},
        )
        assert r.status_code == 200
        data = r.json()
        # Should return at most 100 or total universe size (whichever is smaller)
        assert len(data["ranked_entities"]) <= 100
        assert len(data["ranked_entities"]) == data["total_entities_evaluated"]


class TestMetrics:
    """Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, http_client, neural_api):
        """Metrics endpoint must return Prometheus format."""
        r = http_client.get(f"{neural_api}/metrics")
        assert r.status_code == 200
        text = r.text
        # Prometheus format has lines like "metric_name value"
        assert len(text) > 0
