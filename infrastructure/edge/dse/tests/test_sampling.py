"""
Unit Tests — DSE Sampling Strategies
Pure pytest, no Docker, no external services.
"""

import pytest
from infrastructure.edge.dse.consumers.sampling import (
    latin_hypercube_sampling,
    cartesian_product_sampling,
    sobol_sequence_sampling,
    count_dimensions,
)


class TestCountDimensions:
    def test_empty_context(self):
        assert count_dimensions({}) == 0

    def test_single_dim(self):
        assert count_dimensions({"x": [1, 2, 3]}) == 3

    def test_multi_dim(self):
        ctx = {"a": [1, 2], "b": ["x", "y", "z"]}
        assert count_dimensions(ctx) == 6

    def test_non_list_values_ignored(self):
        ctx = {"a": [1, 2], "b": "not_a_list"}
        # "b" has no list → treated with len 0, ignored in product; only "a" counts
        assert count_dimensions(ctx) == 2


class TestLatinHypercubeSampling:
    DIMS = {"sector": ["Banking", "Tech", "Health"],
            "region": ["EU", "US"]}

    def test_returns_correct_count(self):
        pts = latin_hypercube_sampling(self.DIMS, num_samples=20)
        assert len(pts) == 20

    def test_all_keys_present(self):
        pts = latin_hypercube_sampling(self.DIMS, num_samples=10)
        for p in pts:
            assert "sector" in p
            assert "region" in p

    def test_values_from_domain(self):
        pts = latin_hypercube_sampling(self.DIMS, num_samples=30)
        for p in pts:
            assert p["sector"] in self.DIMS["sector"]
            assert p["region"] in self.DIMS["region"]

    def test_empty_dimensions_returns_empty(self):
        assert latin_hypercube_sampling({}, num_samples=10) == []

    def test_zero_samples_returns_empty(self):
        assert latin_hypercube_sampling(self.DIMS, num_samples=0) == []

    def test_deterministic_with_same_seed(self):
        a = latin_hypercube_sampling(self.DIMS, num_samples=10, seed=7)
        b = latin_hypercube_sampling(self.DIMS, num_samples=10, seed=7)
        assert a == b

    def test_different_seed_different_result(self):
        a = latin_hypercube_sampling(self.DIMS, num_samples=20, seed=1)
        b = latin_hypercube_sampling(self.DIMS, num_samples=20, seed=99)
        assert a != b


class TestCartesianProductSampling:
    DIMS = {"x": [0, 1], "y": ["a", "b"]}

    def test_returns_all_combinations(self):
        pts = cartesian_product_sampling(self.DIMS)
        assert len(pts) == 4

    def test_expected_combinations(self):
        pts = cartesian_product_sampling(self.DIMS)
        combos = {(p["x"], p["y"]) for p in pts}
        expected = {(0, "a"), (0, "b"), (1, "a"), (1, "b")}
        assert combos == expected

    def test_empty_dimensions_returns_empty(self):
        assert cartesian_product_sampling({}) == []

    def test_single_dimension(self):
        pts = cartesian_product_sampling({"z": [10, 20, 30]})
        assert len(pts) == 3


class TestSobolSequenceSampling:
    DIMS = {"a": [1, 2, 3, 4], "b": ["x", "y"]}

    def test_returns_requested_count(self):
        # Sobol pads to power of 2 but slices to num_samples
        pts = sobol_sequence_sampling(self.DIMS, num_samples=5)
        assert len(pts) == 5

    def test_values_from_domain(self):
        pts = sobol_sequence_sampling(self.DIMS, num_samples=8)
        for p in pts:
            assert p["a"] in self.DIMS["a"]
            assert p["b"] in self.DIMS["b"]

    def test_empty_returns_empty(self):
        assert sobol_sequence_sampling({}, num_samples=4) == []
