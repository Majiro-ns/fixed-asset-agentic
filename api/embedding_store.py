# -*- coding: utf-8 -*-
"""
Embedding Store for Fixed Asset Names.

Uses Gemini text-embedding-004 API to generate embeddings for asset names.
Supports batch processing with rate limiting and JSON persistence.
"""
import json
import os
import time
from typing import Any, Dict, List, Optional


class EmbeddingStore:
    """
    Store for asset name embeddings using Gemini API.

    Features:
    - Batch processing (100 items per batch) for rate limit compliance
    - Automatic retry with exponential backoff
    - JSON persistence
    """

    # Gemini embedding model
    EMBEDDING_MODEL = "models/text-embedding-004"
    # Batch size for API calls (Gemini limit)
    BATCH_SIZE = 100
    # Maximum retry attempts
    MAX_RETRIES = 3
    # Base wait time for retry (seconds)
    BASE_RETRY_WAIT = 1.0

    def __init__(self, store_path: str = "data/embeddings.json"):
        """
        Initialize the embedding store.

        Args:
            store_path: Path to JSON file for persistence
        """
        self.store_path = store_path
        self.items: List[Dict[str, Any]] = []
        self._genai = None
        self._configured = False

    def _ensure_configured(self) -> bool:
        """
        Ensure Gemini API is configured.

        Returns:
            True if configured successfully, False otherwise
        """
        if self._configured:
            return True

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
            self._configured = True
            return True
        except ImportError:
            raise ImportError(
                "google-generativeai library not installed. "
                "Run: pip install google-generativeai"
            )

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector
        """
        self._ensure_configured()

        for attempt in range(self.MAX_RETRIES):
            try:
                result = self._genai.embed_content(
                    model=self.EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']

            except Exception as e:
                error_str = str(e).lower()
                # Check for rate limit error
                if "rate" in error_str or "quota" in error_str or "429" in error_str:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = self.BASE_RETRY_WAIT * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                raise

        # Should not reach here, but just in case
        raise RuntimeError(f"Failed to get embedding after {self.MAX_RETRIES} retries")

    def _get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a batch of texts.

        Args:
            texts: List of texts to embed (max BATCH_SIZE)

        Returns:
            List of embedding vectors
        """
        self._ensure_configured()

        if len(texts) > self.BATCH_SIZE:
            raise ValueError(f"Batch size exceeds limit: {len(texts)} > {self.BATCH_SIZE}")

        for attempt in range(self.MAX_RETRIES):
            try:
                result = self._genai.embed_content(
                    model=self.EMBEDDING_MODEL,
                    content=texts,
                    task_type="retrieval_document"
                )
                return result['embedding']

            except Exception as e:
                error_str = str(e).lower()
                # Check for rate limit error
                if "rate" in error_str or "quota" in error_str or "429" in error_str:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = self.BASE_RETRY_WAIT * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                raise

        raise RuntimeError(f"Failed to get batch embeddings after {self.MAX_RETRIES} retries")

    def add_items(self, items: List[Dict[str, Any]]) -> int:
        """
        Add items to the store with embeddings.

        台帳データをEmbedding化して保存

        Args:
            items: List of dicts with at least "name" field
                   Example: [{"name": "ノートPC", "amount": 150000, ...}, ...]

        Returns:
            Number of items added
        """
        if not items:
            return 0

        added_count = 0

        # Process in batches
        for batch_start in range(0, len(items), self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, len(items))
            batch_items = items[batch_start:batch_end]

            # Extract names for embedding
            names = [item.get("name", "") for item in batch_items]

            # Skip empty names
            valid_indices = [i for i, name in enumerate(names) if name.strip()]
            if not valid_indices:
                continue

            valid_names = [names[i] for i in valid_indices]
            valid_items = [batch_items[i] for i in valid_indices]

            # Get embeddings for batch
            try:
                embeddings = self._get_batch_embeddings(valid_names)

                # Store items with embeddings
                for item, name, embedding in zip(valid_items, valid_names, embeddings):
                    # Extract metadata (everything except name)
                    metadata = {k: v for k, v in item.items() if k != "name"}

                    self.items.append({
                        "name": name,
                        "embedding": embedding,
                        "metadata": metadata
                    })
                    added_count += 1

                # Small delay between batches to avoid rate limits
                if batch_end < len(items):
                    time.sleep(0.1)

            except Exception as e:
                # Log error but continue with other batches
                print(f"Error processing batch {batch_start}-{batch_end}: {e}")
                continue

        return added_count

    def save(self) -> None:
        """
        Save the store to JSON file.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.store_path) or ".", exist_ok=True)

        data = {"items": self.items}

        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        """
        Load the store from JSON file.
        """
        if not os.path.exists(self.store_path):
            self.items = []
            return

        with open(self.store_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.items = data.get("items", [])

    def clear(self) -> None:
        """
        Clear all items from the store.
        """
        self.items = []

    def __len__(self) -> int:
        """Return number of items in store."""
        return len(self.items)

    def search_by_name(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar items by name.

        Args:
            query: Query text
            top_k: Number of results to return

        Returns:
            List of items with similarity scores
        """
        if not self.items:
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)

        # Calculate cosine similarity
        results = []
        for item in self.items:
            item_embedding = item.get("embedding", [])
            if not item_embedding:
                continue

            similarity = self._cosine_similarity(query_embedding, item_embedding)
            results.append({
                "name": item["name"],
                "metadata": item.get("metadata", {}),
                "similarity": similarity
            })

        # Sort by similarity (descending) and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


# Convenience function for one-off embedding generation
def generate_embeddings_for_ledger(
    ledger_items: List[Dict[str, Any]],
    output_path: str = "data/embeddings.json"
) -> int:
    """
    Generate embeddings for ledger items and save to file.

    Args:
        ledger_items: List of ledger entries with "name" field
        output_path: Path to save embeddings JSON

    Returns:
        Number of items processed
    """
    store = EmbeddingStore(store_path=output_path)
    count = store.add_items(ledger_items)
    store.save()
    return count
