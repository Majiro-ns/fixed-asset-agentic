# -*- coding: utf-8 -*-
"""履歴ベースの類似検索（API不要版）"""
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional


def calculate_similarity(s1: str, s2: str) -> float:
    """
    2つの文字列の類似度を計算（0.0〜1.0）
    SequenceMatcherによる編集距離ベース
    """
    if not s1 or not s2:
        return 0.0
    # 正規化（小文字化、空白除去）
    s1_normalized = s1.lower().replace(" ", "").replace("　", "")
    s2_normalized = s2.lower().replace(" ", "").replace("　", "")
    return SequenceMatcher(None, s1_normalized, s2_normalized).ratio()


def search_similar_from_history(
    query: str,
    history: List[Dict[str, Any]],
    top_k: int = 3,
    threshold: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    履歴から類似アイテムを検索（API不要）

    Args:
        query: 検索クエリ（資産名）
        history: 判定履歴リスト
        top_k: 上位何件を返すか
        threshold: 類似度の閾値（デフォルト0.5）

    Returns: [
        {"name": "ノートPC HP", "similarity": 0.85, "decision": "CAPITAL_LIKE", ...},
        ...
    ]
    """
    if not query or not history:
        return []

    results = []
    seen_names = set()  # 重複除去用

    for entry in history:
        name = entry.get("description", "") or entry.get("name", "")
        if not name or name in seen_names:
            continue
        if name.startswith("明細(") or name.startswith("明細（"):
            continue

        similarity = calculate_similarity(query, name)
        if similarity >= threshold and similarity < 1.0:  # 完全一致は除外
            seen_names.add(name)
            results.append({
                "name": name,
                "similarity": similarity,
                "decision": entry.get("decision", ""),
                "amount": entry.get("amount"),
                "category": entry.get("category", ""),
                "useful_life_years": entry.get("useful_life_years", ""),
                "metadata": {
                    "source": entry.get("source", ""),
                    "timestamp": entry.get("timestamp", ""),
                }
            })

    # 類似度降順でソート、上位K件を返す
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def search_by_keywords(
    query: str,
    history: List[Dict[str, Any]],
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    キーワード部分一致で検索（より緩い検索）

    「ノートPC」で検索 → 「ノートPC HP」「ノートPC Dell」がヒット
    """
    if not query or not history:
        return []

    query_lower = query.lower().replace(" ", "").replace("　", "")
    results = []
    seen_names = set()

    for entry in history:
        name = entry.get("description", "") or entry.get("name", "")
        if not name or name in seen_names:
            continue
        if name.startswith("明細(") or name.startswith("明細（"):
            continue

        name_lower = name.lower().replace(" ", "").replace("　", "")

        # 部分一致チェック
        if query_lower in name_lower or name_lower in query_lower:
            seen_names.add(name)
            # 類似度は部分一致の割合で計算
            similarity = len(query_lower) / max(len(name_lower), 1)
            if similarity > 1.0:
                similarity = len(name_lower) / len(query_lower)

            results.append({
                "name": name,
                "similarity": min(similarity, 0.99),  # 最大0.99
                "decision": entry.get("decision", ""),
                "amount": entry.get("amount"),
                "category": entry.get("category", ""),
                "useful_life_years": entry.get("useful_life_years", ""),
                "metadata": {
                    "source": entry.get("source", ""),
                    "timestamp": entry.get("timestamp", ""),
                }
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]
