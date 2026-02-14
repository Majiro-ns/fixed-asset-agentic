# -*- coding: utf-8 -*-
"""
判定結果の大型カード表示コンポーネント。
CAPITAL_LIKE / EXPENSE_LIKE の結果をリッチなカードUIで表示する。
※ GUIDANCE は guidance_panel.py が担当するため、ここでは扱わない。
"""
from typing import Any, Dict, List

import streamlit as st


# ---------------------------------------------------------------------------
# 内部ヘルパー
# ---------------------------------------------------------------------------

def _sum_amounts(line_items: List[Dict[str, Any]]) -> int:
    """line_items の amount を合算する。"""
    total = 0
    for item in line_items:
        amt = item.get("amount")
        if isinstance(amt, (int, float)) and not isinstance(amt, bool):
            total += int(amt)
    return total


def _tax_rule_text(total: int) -> str:
    """金額に応じた税務ルールを初心者向けに1行で返す。"""
    if total < 100_000:
        return "消耗品として一括で経費にできます"
    if total < 200_000:
        return "3年で均等に経費にできます"
    if total < 300_000:
        return "中小企業なら一括で経費にできる特例があります"
    if total < 600_000:
        return "固定資産として毎年少しずつ経費にします（減価償却）"
    return "固定資産として毎年少しずつ経費にします（減価償却）"


def _confidence_bar_html(confidence: float) -> str:
    """信頼度プログレスバーのHTMLを生成する。"""
    pct = max(0.0, min(1.0, confidence)) * 100

    if confidence >= 0.8:
        color = "#10B981"
        label = "ほぼ確実"
    elif confidence >= 0.6:
        color = "#F59E0B"
        label = "概ね確実（念のため確認推奨）"
    else:
        color = "#EF4444"
        label = "念のため確認を"

    return (
        '<div style="margin:0.75rem 0;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
        f'<span style="font-size:0.85rem;color:#374151;">信頼度</span>'
        f'<span style="font-size:0.85rem;font-weight:600;color:{color};">{pct:.0f}% — {label}</span>'
        '</div>'
        '<div style="background:#E5E7EB;border-radius:9999px;height:10px;overflow:hidden;">'
        f'<div style="background:{color};width:{pct:.1f}%;height:100%;border-radius:9999px;transition:width 0.3s;"></div>'
        '</div>'
        '</div>'
    )


def _useful_life_html(useful_life: Dict[str, Any]) -> str:
    """資産種類・耐用年数の表示HTMLを生成する。"""
    category = useful_life.get("category", "")
    subcategory = useful_life.get("subcategory", "")
    years = useful_life.get("useful_life_years")
    if not years:
        return ""

    asset_label = category
    if subcategory:
        asset_label = f"{category}（{subcategory}）"

    return (
        '<div style="margin:0.5rem 0;padding:0.5rem 0.75rem;background:#F9FAFB;border-radius:0.375rem;font-size:0.9rem;color:#374151;">'
        f'📦 {asset_label} / 📅 <strong>{years}年</strong>で償却'
        '</div>'
    )


def _reasons_html(reasons: List[str]) -> str:
    """判断理由を箇条書きHTMLで生成する。"""
    if not reasons:
        return ""

    items = "\n".join(
        f'<li style="margin-bottom:0.25rem; color:#4B5563;">{r}</li>'
        for r in reasons
    )
    return (
        '<div style="margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid #E5E7EB;">'
        '<div style="font-size:0.85rem;font-weight:600;color:#374151;margin-bottom:0.375rem;">判断理由</div>'
        f'<ul style="margin:0;padding-left:1.25rem;font-size:0.875rem;">{items}</ul>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# カード設定
# ---------------------------------------------------------------------------

_CARD_CONFIG = {
    "CAPITAL_LIKE": {
        "icon": "✅",
        "title": "資産として計上",
        "sub": "固定資産台帳へ登録し、毎年償却",
        "bg": "#ECFDF5",
        "border": "#10B981",
        "title_color": "#065F46",
        "sub_color": "#047857",
    },
    "EXPENSE_LIKE": {
        "icon": "💰",
        "title": "経費として処理OK",
        "sub": "今期の経費として全額処理可能",
        "bg": "#EFF6FF",
        "border": "#3B82F6",
        "title_color": "#1E3A8A",
        "sub_color": "#1D4ED8",
    },
}


# ---------------------------------------------------------------------------
# メイン関数
# ---------------------------------------------------------------------------

def render_result_card(result: dict) -> None:
    """
    判定結果の大型カードを描画する。

    Parameters
    ----------
    result : dict
        APIレスポンス。decision, confidence, reasons, line_items,
        useful_life, evidence, citations, metadata を含む。
    """
    decision = (result.get("decision") or "").upper()

    # GUIDANCE はこのコンポーネントの対象外
    if decision not in _CARD_CONFIG:
        return

    cfg = _CARD_CONFIG[decision]
    confidence = float(result.get("confidence", 0))
    reasons: List[str] = result.get("reasons") or []
    line_items: List[Dict[str, Any]] = result.get("line_items") or []
    useful_life: Dict[str, Any] = result.get("useful_life") or {}

    # 合計金額
    total = _sum_amounts(line_items)
    amount_display = f"¥{total:,}" if total > 0 else ""

    # 税務ルール
    tax_text = _tax_rule_text(total) if total > 0 else ""

    # 耐用年数（CAPITAL_LIKE のみ）
    life_html = ""
    if decision == "CAPITAL_LIKE" and useful_life and useful_life.get("useful_life_years"):
        life_html = _useful_life_html(useful_life)

    # 信頼度バー
    confidence_html = _confidence_bar_html(confidence)

    # 判断理由
    reasons_html = _reasons_html(reasons)

    # --- メインカード HTML（初期表示: 判定結果 + 金額 + 信頼度のみ） ---
    amount_html = ""
    if amount_display:
        amount_html = (
            f'<div style="font-size:1.75rem;font-weight:bold;'
            f'color:{cfg["title_color"]};white-space:nowrap;">'
            f'{amount_display}</div>'
        )

    main_card_html = (
        f'<div style="background:{cfg["bg"]};border-left:4px solid {cfg["border"]};'
        f'border-radius:0.75rem;padding:1.5rem;margin:1rem 0;'
        f'width:100%;box-sizing:border-box;">'
        '<div style="display:flex;justify-content:space-between;'
        'align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">'
        '<div>'
        f'<div style="font-size:1.5rem;font-weight:bold;color:{cfg["title_color"]};">'
        f'{cfg["icon"]} {cfg["title"]}</div>'
        f'<div style="font-size:0.95rem;color:{cfg["sub_color"]};margin-top:0.25rem;">'
        f'{cfg["sub"]}</div>'
        '</div>'
        + amount_html
        + '</div>'
        + confidence_html
        + '</div>'
    )

    st.markdown(main_card_html, unsafe_allow_html=True)

    # --- 詳細情報（expander内に格納） ---
    detail_parts: List[str] = []

    if tax_text:
        detail_parts.append(
            f"<div style='font-size:0.85rem; color:#6B7280; margin:0.25rem 0; padding:0.375rem 0.5rem; background:rgba(245,245,245,0.8); border-radius:0.25rem;'>📋 {tax_text}</div>"
        )

    if life_html:
        detail_parts.append(life_html)

    if reasons_html:
        detail_parts.append(reasons_html)

    if detail_parts:
        with st.expander("詳しく見る", expanded=False):
            st.markdown("\n".join(detail_parts), unsafe_allow_html=True)
