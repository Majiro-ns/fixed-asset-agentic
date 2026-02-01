#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
類似事例表示UIモジュール

過去の類似判定事例を表示するStreamlitコンポーネント。
判定結果画面に「過去の類似事例」セクションを追加し、
類似度スコアと過去の判定結果を表示する。
"""
from typing import Any, Dict, List, Optional

import streamlit as st


def _format_decision_label(decision: str) -> str:
    """判定結果を日本語ラベルに変換"""
    labels = {
        "CAPITAL_LIKE": "資産計上",
        "EXPENSE_LIKE": "経費処理",
        "GUIDANCE": "要確認",
    }
    return labels.get(decision, decision)


def _format_category_info(metadata: Dict[str, Any]) -> str:
    """資産カテゴリ情報をフォーマット"""
    category = metadata.get("category", "")
    subcategory = metadata.get("subcategory", "")
    useful_life = metadata.get("useful_life", 0) or metadata.get("useful_life_years", 0)

    parts = []

    # カテゴリ情報
    if category and category != "不明":
        if subcategory:
            parts.append(f"{category}（{subcategory}）")
        else:
            parts.append(category)

    # 耐用年数
    if useful_life and useful_life > 0:
        parts.append(f"{useful_life}年償却")

    return " / ".join(parts) if parts else ""


def _get_similarity_color(similarity: float) -> str:
    """類似度に応じた色を返す"""
    if similarity >= 0.9:
        return "#10B981"  # 緑（高類似度）
    elif similarity >= 0.7:
        return "#3B82F6"  # 青（中類似度）
    else:
        return "#6B7280"  # グレー（低類似度）


def render_similar_cases(
    current_item_name: str,
    similar_items: List[Dict[str, Any]],
    max_items: int = 3,
    expanded: bool = False,
) -> None:
    """
    類似事例セクションをレンダリング

    過去の判定履歴から類似した事例を表示し、
    ユーザーの判定作業をサポートする。

    Args:
        current_item_name: 現在判定中の資産名
        similar_items: 類似事例のリスト
            [
                {
                    "name": "ノートPC HP ProBook",
                    "similarity": 0.92,
                    "metadata": {
                        "decision": "CAPITAL_LIKE",
                        "category": "器具備品",
                        "subcategory": "電子計算機",
                        "useful_life": 4,
                        "amount": 150000
                    }
                },
                ...
            ]
        max_items: 表示する最大件数（デフォルト: 3）
        expanded: 初期状態で展開するか（デフォルト: False）

    Returns:
        None（Streamlit UIを直接レンダリング）

    Notes:
        - 類似事例がない場合（空リスト）は何も表示しない
        - 類似度はパーセント表示（0.92 → 92%）
        - st.expanderで折りたたみ可能
    """
    # 空リストの場合は何も表示しない
    if not similar_items:
        return

    # 表示件数を制限
    display_items = similar_items[:max_items]

    # Expanderで折りたたみ可能なセクションを作成
    with st.expander(f"📚 過去の類似事例（{len(display_items)}件）", expanded=expanded):
        # ヘッダーメッセージ
        st.markdown(
            f"「**{current_item_name}**」に似た過去の判定:"
        )

        st.markdown("")  # スペーサー

        # 各類似事例を表示
        for i, item in enumerate(display_items, 1):
            name = item.get("name", "不明")
            similarity = item.get("similarity", 0.0)
            metadata = item.get("metadata", {})

            # 判定結果
            decision = metadata.get("decision", "UNKNOWN")
            decision_label = _format_decision_label(decision)

            # カテゴリ情報
            category_info = _format_category_info(metadata)

            # 類似度の色
            sim_color = _get_similarity_color(similarity)

            # 類似度をパーセント表示
            similarity_pct = int(similarity * 100)

            # 事例表示
            st.markdown(
                f"**{i}. {name}**"
                f"<span style='color:{sim_color}; margin-left:8px;'>"
                f"（類似度: {similarity_pct}%）</span>",
                unsafe_allow_html=True
            )

            # 判定結果と詳細
            result_parts = [f"→ {decision_label}"]
            if category_info:
                result_parts.append(category_info)

            st.caption(" / ".join(result_parts))

            # 金額があれば表示
            amount = metadata.get("amount")
            if amount:
                try:
                    st.caption(f"　金額: ¥{int(amount):,}")
                except (ValueError, TypeError):
                    pass

            st.markdown("")  # 事例間のスペーサー

        # フッターメッセージ
        st.markdown(
            "<div style='background:#F3F4F6; padding:0.5rem; "
            "border-radius:0.25rem; margin-top:0.5rem;'>"
            "💡 過去の判定を参考にしてください"
            "</div>",
            unsafe_allow_html=True
        )


def render_similar_cases_compact(
    similar_items: List[Dict[str, Any]],
    max_items: int = 2,
) -> None:
    """
    類似事例をコンパクトに表示（1行サマリー形式）

    判定結果の横に小さく表示する場合に使用。

    Args:
        similar_items: 類似事例のリスト
        max_items: 表示する最大件数（デフォルト: 2）

    Returns:
        None
    """
    if not similar_items:
        return

    display_items = similar_items[:max_items]

    # 1行サマリー
    summaries = []
    for item in display_items:
        name = item.get("name", "")
        similarity = item.get("similarity", 0.0)
        metadata = item.get("metadata", {})
        decision = _format_decision_label(metadata.get("decision", ""))

        if name and decision:
            summaries.append(f"{name}({int(similarity*100)}%→{decision})")

    if summaries:
        st.caption(f"📚 類似事例: {', '.join(summaries)}")


# デモ用のサンプルデータ
DEMO_SIMILAR_ITEMS = [
    {
        "name": "ノートPC HP ProBook",
        "similarity": 0.92,
        "metadata": {
            "decision": "CAPITAL_LIKE",
            "category": "器具備品",
            "subcategory": "電子計算機",
            "useful_life": 4,
            "amount": 158000,
        }
    },
    {
        "name": "ノートPC Lenovo ThinkPad",
        "similarity": 0.88,
        "metadata": {
            "decision": "CAPITAL_LIKE",
            "category": "器具備品",
            "subcategory": "電子計算機",
            "useful_life": 4,
            "amount": 142000,
        }
    },
    {
        "name": "ノートPC Dell Latitude",
        "similarity": 0.85,
        "metadata": {
            "decision": "CAPITAL_LIKE",
            "category": "器具備品",
            "subcategory": "電子計算機",
            "useful_life": 4,
            "amount": 135000,
        }
    },
]


if __name__ == "__main__":
    # スタンドアロンでのテスト実行用
    st.set_page_config(page_title="類似事例UIテスト", page_icon="📚")
    st.title("類似事例表示UIテスト")

    st.markdown("---")
    st.subheader("通常表示")
    render_similar_cases(
        current_item_name="ノートPC Dell",
        similar_items=DEMO_SIMILAR_ITEMS,
        expanded=True,
    )

    st.markdown("---")
    st.subheader("コンパクト表示")
    render_similar_cases_compact(DEMO_SIMILAR_ITEMS)

    st.markdown("---")
    st.subheader("空リストの場合（何も表示されない）")
    render_similar_cases(
        current_item_name="テスト",
        similar_items=[],
    )
    st.caption("↑ 空リストの場合は何も表示されません")
