# -*- coding: utf-8 -*-
"""
Tests for similarity_search module.
"""
import math

import pytest
import numpy as np

from api.similarity_search import cosine_similarity, search_similar, batch_search_similar


class TestCosineSimilarity:
    """Unit tests for cosine_similarity function."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        vec = [1.0, 0.0, 0.0]
        assert cosine_similarity(vec, vec) == 1.0

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert cosine_similarity(vec1, vec2) == 0.0

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        assert cosine_similarity(vec1, vec2) == -1.0

    def test_zero_vector_first(self):
        """Zero vector as first argument should return 0.0."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert cosine_similarity(vec1, vec2) == 0.0

    def test_zero_vector_second(self):
        """Zero vector as second argument should return 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0]
        assert cosine_similarity(vec1, vec2) == 0.0

    def test_both_zero_vectors(self):
        """Both zero vectors should return 0.0."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0]
        assert cosine_similarity(vec1, vec2) == 0.0

    def test_similar_vectors(self):
        """Similar vectors should have high similarity."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.9, 0.1, 0.0]
        sim = cosine_similarity(vec1, vec2)
        assert 0.9 < sim < 1.0

    def test_normalized_vectors(self):
        """Pre-normalized vectors should work correctly."""
        vec1 = [1.0 / math.sqrt(2), 1.0 / math.sqrt(2), 0.0]
        vec2 = [1.0 / math.sqrt(2), 1.0 / math.sqrt(2), 0.0]
        assert abs(cosine_similarity(vec1, vec2) - 1.0) < 1e-10

    def test_high_dimensional_vectors(self):
        """High dimensional vectors (like embeddings) should work."""
        vec1 = [0.1] * 768
        vec2 = [0.1] * 768
        assert abs(cosine_similarity(vec1, vec2) - 1.0) < 1e-10


class TestSearchSimilar:
    """Unit tests for search_similar function."""

    @pytest.fixture
    def sample_items(self):
        """Sample items for testing."""
        return [
            {"name": "ノートPC HP", "embedding": [0.9, 0.1, 0.0], "metadata": {"amount": 150000}},
            {"name": "デスクトップPC Dell", "embedding": [0.85, 0.15, 0.05], "metadata": {"amount": 200000}},
            {"name": "プリンター Canon", "embedding": [0.3, 0.7, 0.2], "metadata": {"amount": 80000}},
            {"name": "モニター LG", "embedding": [0.7, 0.3, 0.1], "metadata": {"amount": 50000}},
            {"name": "サーバー Dell", "embedding": [0.5, 0.5, 0.1], "metadata": {"amount": 500000}},
        ]

    def test_exact_match(self, sample_items):
        """Query matching an item exactly should have similarity 1.0."""
        query = [0.9, 0.1, 0.0]  # Same as ノートPC HP
        results = search_similar(query, sample_items, top_k=1, threshold=0.0)

        assert len(results) == 1
        assert results[0]["name"] == "ノートPC HP"
        assert results[0]["similarity"] == 1.0

    def test_top_k_limit(self, sample_items):
        """Should return at most top_k results."""
        query = [0.9, 0.1, 0.0]
        results = search_similar(query, sample_items, top_k=2, threshold=0.0)

        assert len(results) == 2

    def test_threshold_filtering(self, sample_items):
        """Should filter out items below threshold."""
        query = [0.9, 0.1, 0.0]
        results = search_similar(query, sample_items, top_k=10, threshold=0.95)

        # Only exact or near-exact matches should pass
        assert len(results) <= 2
        for r in results:
            assert r["similarity"] >= 0.95

    def test_sorted_by_similarity(self, sample_items):
        """Results should be sorted by similarity in descending order."""
        query = [0.9, 0.1, 0.0]
        results = search_similar(query, sample_items, top_k=5, threshold=0.0)

        for i in range(len(results) - 1):
            assert results[i]["similarity"] >= results[i + 1]["similarity"]

    def test_empty_stored_items(self):
        """Empty stored_items should return empty list."""
        query = [0.9, 0.1, 0.0]
        results = search_similar(query, [], top_k=5, threshold=0.5)

        assert results == []

    def test_empty_query(self, sample_items):
        """Empty query should return empty list."""
        results = search_similar([], sample_items, top_k=5, threshold=0.5)

        assert results == []

    def test_item_without_embedding(self):
        """Items without embedding should be skipped."""
        items = [
            {"name": "Item1", "metadata": {}},  # No embedding
            {"name": "Item2", "embedding": [1.0, 0.0, 0.0], "metadata": {}},
        ]
        query = [1.0, 0.0, 0.0]

        results = search_similar(query, items, top_k=5, threshold=0.0)

        assert len(results) == 1
        assert results[0]["name"] == "Item2"

    def test_item_with_empty_embedding(self):
        """Items with empty embedding should be skipped."""
        items = [
            {"name": "Item1", "embedding": [], "metadata": {}},  # Empty embedding
            {"name": "Item2", "embedding": [1.0, 0.0, 0.0], "metadata": {}},
        ]
        query = [1.0, 0.0, 0.0]

        results = search_similar(query, items, top_k=5, threshold=0.0)

        assert len(results) == 1
        assert results[0]["name"] == "Item2"

    def test_metadata_preserved(self, sample_items):
        """Metadata should be preserved in results."""
        query = [0.9, 0.1, 0.0]
        results = search_similar(query, sample_items, top_k=1, threshold=0.0)

        assert results[0]["metadata"]["amount"] == 150000

    def test_similarity_rounded(self, sample_items):
        """Similarity should be rounded to 4 decimal places."""
        query = [0.85, 0.15, 0.05]
        results = search_similar(query, sample_items, top_k=1, threshold=0.0)

        # Check that similarity has at most 4 decimal places
        sim_str = str(results[0]["similarity"])
        if "." in sim_str:
            decimal_places = len(sim_str.split(".")[1])
            assert decimal_places <= 4

    def test_high_threshold_no_results(self, sample_items):
        """Very high threshold should return no results."""
        query = [0.5, 0.5, 0.0]  # Doesn't exactly match anything
        results = search_similar(query, sample_items, top_k=10, threshold=0.9999)

        assert len(results) == 0

    def test_missing_name_field(self):
        """Items without name should return empty string for name."""
        items = [
            {"embedding": [1.0, 0.0, 0.0], "metadata": {"amount": 100}},
        ]
        query = [1.0, 0.0, 0.0]

        results = search_similar(query, items, top_k=1, threshold=0.0)

        assert results[0]["name"] == ""

    def test_missing_metadata_field(self):
        """Items without metadata should return empty dict for metadata."""
        items = [
            {"name": "Test", "embedding": [1.0, 0.0, 0.0]},
        ]
        query = [1.0, 0.0, 0.0]

        results = search_similar(query, items, top_k=1, threshold=0.0)

        assert results[0]["metadata"] == {}


class TestBatchSearchSimilar:
    """Unit tests for batch_search_similar function."""

    @pytest.fixture
    def sample_items(self):
        """Sample items for testing."""
        return [
            {"name": "ノートPC", "embedding": [1.0, 0.0, 0.0], "metadata": {}},
            {"name": "サーバー", "embedding": [0.0, 1.0, 0.0], "metadata": {}},
        ]

    def test_batch_search(self, sample_items):
        """Batch search should return results for each query."""
        queries = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]

        results = batch_search_similar(queries, sample_items, top_k=1, threshold=0.0)

        assert len(results) == 2
        assert results[0][0]["name"] == "ノートPC"
        assert results[1][0]["name"] == "サーバー"

    def test_empty_queries(self, sample_items):
        """Empty queries list should return empty list."""
        results = batch_search_similar([], sample_items, top_k=1, threshold=0.0)

        assert results == []
