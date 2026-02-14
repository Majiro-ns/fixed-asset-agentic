# -*- coding: utf-8 -*-
"""
Diff display component for showing classification changes.

Renders a Before/After view when a GUIDANCE decision resolves
to a definitive classification after user input.
"""
import streamlit as st
from typing import Dict, List


_DECISION_LABELS: Dict[str, str] = {
    "CAPITAL_LIKE": "✅ 資産として計上",
    "EXPENSE_LIKE": "💰 経費として処理OK",
    "GUIDANCE": "⚠️ 確認が必要です",
}


def _label(decision: str) -> str:
    return _DECISION_LABELS.get(decision, decision)


def _diff_reasons(prev_reasons: List[str], current_reasons: List[str]) -> str:
    """Build HTML showing added/kept reasons between prev and current."""
    prev_set = set(prev_reasons)
    lines: List[str] = []
    for r in current_reasons:
        if r not in prev_set:
            lines.append(
                f'<div style="color:#059669;margin:2px 0;">＋ {r}</div>'
            )
        else:
            lines.append(
                f'<div style="color:#6B7280;margin:2px 0;">　 {r}</div>'
            )
    return "".join(lines)


def render_diff_display(prev_result: dict, current_result: dict) -> None:
    """Render a Before/After diff when classification changed.

    Parameters
    ----------
    prev_result : dict
        GUIDANCE-phase API response (decision, confidence, reasons, ...).
    current_result : dict
        Post-user-answer API response with the same structure.
    """
    prev_decision = (prev_result.get("decision") or "").upper()
    curr_decision = (current_result.get("decision") or "").upper()

    if prev_decision == curr_decision:
        return

    prev_label = _label(prev_decision)
    curr_label = _label(curr_decision)

    prev_reasons: List[str] = prev_result.get("reasons") or []
    curr_reasons: List[str] = current_result.get("reasons") or []
    reasons_html = _diff_reasons(prev_reasons, curr_reasons)

    prev_conf = prev_result.get("confidence")
    curr_conf = current_result.get("confidence")
    conf_html = ""
    if prev_conf is not None and curr_conf is not None:
        conf_html = (
            f'<div style="font-size:0.85rem;color:#6B7280;margin-top:8px;">'
            f"確信度: {prev_conf:.0%} → {curr_conf:.0%}"
            f"</div>"
        )

    reasons_section = ""
    if reasons_html:
        reasons_section = (
            '<div style="margin-top:12px;border-top:1px solid #DDD6FE;padding-top:8px;">'
            '<div style="font-size:0.85rem;color:#5B21B6;font-weight:600;margin-bottom:4px;">判断理由の変化</div>'
            + reasons_html
            + '</div>'
        )

    html = (
        '<div style="background:#F5F3FF;border:2px solid #8B5CF6;border-radius:12px;'
        'padding:1.5rem;margin:1rem 0;animation:fadeIn 0.5s ease-in;">'
        '<div style="font-size:1.1rem;font-weight:bold;color:#5B21B6;margin-bottom:0.8rem;">'
        '🔄 判定が変わりました</div>'
        '<div style="margin-bottom:4px;">'
        f'<span style="color:#6B7280;">変更前:</span> '
        f'<span style="font-weight:600;">{prev_label}</span></div>'
        '<div style="color:#8B5CF6;padding-left:1.5rem;margin-bottom:4px;">↓</div>'
        '<div style="margin-bottom:8px;">'
        f'<span style="color:#6B7280;">変更後:</span> '
        f'<span style="font-weight:600;">{curr_label}</span></div>'
        + conf_html
        + reasons_section
        + '<div style="margin-top:12px;padding:8px 12px;background:#EDE9FE;border-radius:8px;'
        'font-size:0.85rem;color:#5B21B6;">'
        '📋 この差分は監査時の説明資料として利用できます</div>'
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
