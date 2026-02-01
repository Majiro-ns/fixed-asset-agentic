# -*- coding: utf-8 -*-
"""
Tests for EmbeddingStore.
"""
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from api.embedding_store import EmbeddingStore, generate_embeddings_for_ledger


class TestEmbeddingStoreUnit:
    """Unit tests for EmbeddingStore (mocked API)."""

    @pytest.fixture
    def mock_genai(self):
        """Create a mock genai module."""
        mock = MagicMock()
        # Mock single embedding response
        mock.embed_content.return_value = {
            'embedding': [0.1] * 768  # 768-dimensional vector
        }
        return mock

    @pytest.fixture
    def temp_store_path(self):
        """Create a temporary file path for store."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    def test_init(self, temp_store_path):
        """Test initialization."""
        store = EmbeddingStore(store_path=temp_store_path)
        assert store.store_path == temp_store_path
        assert store.items == []
        assert len(store) == 0

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("api.embedding_store.EmbeddingStore._ensure_configured")
    @patch("api.embedding_store.EmbeddingStore._get_batch_embeddings")
    def test_add_items(self, mock_batch, mock_config, temp_store_path):
        """Test adding items with embeddings."""
        # Setup mock
        mock_config.return_value = True
        mock_batch.return_value = [[0.1] * 768, [0.2] * 768]

        store = EmbeddingStore(store_path=temp_store_path)

        items = [
            {"name": "ノートPC HP ProBook", "amount": 150000},
            {"name": "デスクトップPC Dell", "amount": 200000}
        ]

        count = store.add_items(items)

        assert count == 2
        assert len(store) == 2
        assert store.items[0]["name"] == "ノートPC HP ProBook"
        assert store.items[0]["metadata"]["amount"] == 150000
        assert len(store.items[0]["embedding"]) == 768

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("api.embedding_store.EmbeddingStore._ensure_configured")
    @patch("api.embedding_store.EmbeddingStore._get_batch_embeddings")
    def test_add_items_empty(self, mock_batch, mock_config, temp_store_path):
        """Test adding empty items list."""
        store = EmbeddingStore(store_path=temp_store_path)
        count = store.add_items([])
        assert count == 0

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("api.embedding_store.EmbeddingStore._ensure_configured")
    @patch("api.embedding_store.EmbeddingStore._get_batch_embeddings")
    def test_add_items_skip_empty_names(self, mock_batch, mock_config, temp_store_path):
        """Test that empty names are skipped."""
        mock_config.return_value = True
        mock_batch.return_value = [[0.1] * 768]

        store = EmbeddingStore(store_path=temp_store_path)

        items = [
            {"name": "", "amount": 100000},  # Empty name - should skip
            {"name": "サーバー", "amount": 500000}
        ]

        count = store.add_items(items)
        assert count == 1
        assert store.items[0]["name"] == "サーバー"

    def test_save_and_load(self, temp_store_path):
        """Test save and load functionality."""
        store = EmbeddingStore(store_path=temp_store_path)
        store.items = [
            {
                "name": "テスト資産",
                "embedding": [0.5] * 768,
                "metadata": {"amount": 100000}
            }
        ]

        # Save
        store.save()

        # Create new store and load
        store2 = EmbeddingStore(store_path=temp_store_path)
        store2.load()

        assert len(store2) == 1
        assert store2.items[0]["name"] == "テスト資産"
        assert store2.items[0]["metadata"]["amount"] == 100000

    def test_load_nonexistent_file(self, temp_store_path):
        """Test loading from nonexistent file."""
        # Remove the temp file first
        if os.path.exists(temp_store_path):
            os.remove(temp_store_path)

        store = EmbeddingStore(store_path=temp_store_path)
        store.load()  # Should not raise
        assert store.items == []

    def test_clear(self, temp_store_path):
        """Test clearing the store."""
        store = EmbeddingStore(store_path=temp_store_path)
        store.items = [{"name": "test", "embedding": [], "metadata": {}}]
        assert len(store) == 1

        store.clear()
        assert len(store) == 0

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        # Identical vectors should have similarity 1.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert EmbeddingStore._cosine_similarity(vec1, vec2) == 1.0

        # Orthogonal vectors should have similarity 0.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert EmbeddingStore._cosine_similarity(vec1, vec2) == 0.0

        # Different length vectors should return 0.0
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert EmbeddingStore._cosine_similarity(vec1, vec2) == 0.0

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_search_by_name(self, temp_store_path):
        """Test search by name functionality."""
        store = EmbeddingStore(store_path=temp_store_path)

        # Pre-populate with items
        store.items = [
            {"name": "ノートPC", "embedding": [1.0, 0.0, 0.0], "metadata": {}},
            {"name": "デスクトップPC", "embedding": [0.9, 0.1, 0.0], "metadata": {}},
            {"name": "サーバー", "embedding": [0.0, 1.0, 0.0], "metadata": {}},
        ]

        # Mock the get_embedding method
        with patch.object(store, 'get_embedding', return_value=[1.0, 0.0, 0.0]):
            results = store.search_by_name("ノートPC", top_k=2)

        assert len(results) == 2
        assert results[0]["name"] == "ノートPC"  # Highest similarity
        assert results[0]["similarity"] == 1.0

    def test_no_api_key_raises_error(self, temp_store_path):
        """Test that missing API key raises error."""
        # Clear the API key
        env = os.environ.copy()
        if "GOOGLE_API_KEY" in env:
            del env["GOOGLE_API_KEY"]

        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=True):
            store = EmbeddingStore(store_path=temp_store_path)
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                store._ensure_configured()


class TestEmbeddingStoreIntegration:
    """Integration tests (require real API key)."""

    @pytest.fixture
    def temp_store_path(self):
        """Create a temporary file path for store."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set"
    )
    def test_real_embedding(self, temp_store_path):
        """Test with real Gemini API (only runs if API key is set)."""
        store = EmbeddingStore(store_path=temp_store_path)

        # Get single embedding
        embedding = store.get_embedding("ノートPC HP ProBook")

        assert isinstance(embedding, list)
        assert len(embedding) == 768  # text-embedding-004 outputs 768 dimensions
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set"
    )
    def test_real_batch_embedding(self, temp_store_path):
        """Test batch embedding with real API."""
        store = EmbeddingStore(store_path=temp_store_path)

        items = [
            {"name": "ノートPC HP ProBook", "amount": 150000},
            {"name": "サーバー Dell PowerEdge", "amount": 500000},
        ]

        count = store.add_items(items)

        assert count == 2
        assert len(store) == 2
        assert len(store.items[0]["embedding"]) == 768


class TestGenerateEmbeddingsForLedger:
    """Test convenience function."""

    @pytest.fixture
    def temp_store_path(self):
        """Create a temporary file path for store."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        yield path
        if os.path.exists(path):
            os.remove(path)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("api.embedding_store.EmbeddingStore._ensure_configured")
    @patch("api.embedding_store.EmbeddingStore._get_batch_embeddings")
    def test_generate_embeddings_for_ledger(self, mock_batch, mock_config, temp_store_path):
        """Test the convenience function."""
        mock_config.return_value = True
        mock_batch.return_value = [[0.1] * 768, [0.2] * 768]

        items = [
            {"name": "資産A", "amount": 100000},
            {"name": "資産B", "amount": 200000},
        ]

        count = generate_embeddings_for_ledger(items, output_path=temp_store_path)

        assert count == 2
        assert os.path.exists(temp_store_path)

        # Verify file contents
        with open(temp_store_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "資産A"
