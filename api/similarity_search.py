# -*- coding: utf-8 -*-
"""
Similarity search module using cosine similarity with numpy.
Provides Top-K search functionality for embedding-based retrieval.
"""
import math
from typing import Any, Dict, List

import numpy as np


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    2つのベクトルのコサイン類似度を計算する。

    Args:
        vec1: 1つ目のベクトル
        vec2: 2つ目のベクトル

    Returns:
        コサイン類似度（-1.0 ~ 1.0）。ゼロベクトルの場合は0.0を返す。

    Examples:
        >>> cosine_similarity([1.0, 0.0], [1.0, 0.0])
        1.0
        >>> cosine_similarity([1.0, 0.0], [0.0, 1.0])
        0.0
        >>> cosine_similarity([0.0, 0.0], [1.0, 0.0])
        0.0
    """
    arr1 = np.array(vec1, dtype=np.float64)
    arr2 = np.array(vec2, dtype=np.float64)

    # ノルム計算
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    # ゼロベクトル対策：分母がゼロの場合は類似度0
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    # コサイン類似度 = (a・b) / (|a| * |b|)
    dot_product = np.dot(arr1, arr2)
    similarity = dot_product / (norm1 * norm2)

    # 浮動小数点誤差で1を超える可能性があるためクリップ
    return float(np.clip(similarity, -1.0, 1.0))


def search_similar(
    query_embedding: List[float],
    stored_items: List[Dict[str, Any]],
    top_k: int = 5,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    類似アイテムを検索する。

    クエリのEmbeddingと保存されたアイテムのEmbedding間のコサイン類似度を計算し、
    閾値以上かつ上位K件のアイテムを返却する。

    Args:
        query_embedding: クエリのEmbeddingベクトル
        stored_items: 保存されたアイテムのリスト。各アイテムは以下の構造:
            {
                "name": str,           # アイテム名
                "embedding": List[float],  # Embeddingベクトル
                "metadata": dict       # その他のメタデータ（任意）
            }
        top_k: 上位何件を返すか（デフォルト: 5）
        threshold: 類似度の閾値（デフォルト: 0.7）。これ以上の類似度を持つアイテムのみ返却

    Returns:
        類似アイテムのリスト。類似度降順でソート済み:
            [
                {
                    "name": "ノートPC HP",
                    "similarity": 0.92,
                    "metadata": {"amount": 150000, ...}
                },
                ...
            ]

    Examples:
        >>> items = [
        ...     {"name": "item1", "embedding": [1.0, 0.0, 0.0], "metadata": {"amount": 100}},
        ...     {"name": "item2", "embedding": [0.9, 0.1, 0.0], "metadata": {"amount": 200}},
        ... ]
        >>> results = search_similar([1.0, 0.0, 0.0], items, top_k=2, threshold=0.5)
        >>> len(results) >= 1
        True
    """
    if not stored_items:
        return []

    if not query_embedding:
        return []

    # 各アイテムとの類似度を計算
    scored_items: List[Dict[str, Any]] = []

    for item in stored_items:
        # embeddingキーが存在しない場合はスキップ
        if "embedding" not in item or not item["embedding"]:
            continue

        # 類似度計算
        similarity = cosine_similarity(query_embedding, item["embedding"])

        # 閾値以上のもののみ追加
        if similarity >= threshold:
            result_item = {
                "name": item.get("name", ""),
                "similarity": round(similarity, 4),  # 小数点4桁で丸める
                "metadata": item.get("metadata", {})
            }
            scored_items.append(result_item)

    # 類似度降順でソート
    scored_items.sort(key=lambda x: x["similarity"], reverse=True)

    # 上位K件を返却
    return scored_items[:top_k]


def batch_search_similar(
    query_embeddings: List[List[float]],
    stored_items: List[Dict[str, Any]],
    top_k: int = 5,
    threshold: float = 0.7
) -> List[List[Dict[str, Any]]]:
    """
    複数のクエリに対して一括で類似検索を行う。

    Args:
        query_embeddings: クエリのEmbeddingベクトルのリスト
        stored_items: 保存されたアイテムのリスト
        top_k: 各クエリに対して上位何件を返すか
        threshold: 類似度の閾値

    Returns:
        各クエリに対する検索結果のリスト
    """
    results = []
    for query_embedding in query_embeddings:
        result = search_similar(
            query_embedding=query_embedding,
            stored_items=stored_items,
            top_k=top_k,
            threshold=threshold
        )
        results.append(result)
    return results
