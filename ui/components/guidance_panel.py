# -*- coding: utf-8 -*-
"""
GUIDANCE Panel Component - AIが判断を保留した時の全画面演出UI。

AIが自信を持って判定できない場合に表示される、
ユーザーへの確認パネル。Stop-first原則の可視化。

ペルソナ: 高卒の設備会社経理事務。専門用語を知らない。
"""
import re
import textwrap
from typing import Dict, List, Optional

import streamlit as st

# ---------------------------------------------------------------------------
# CSS（インデントなし文字列 — CommonMarkコードブロック回避）
# ---------------------------------------------------------------------------
_GP_CSS = textwrap.dedent("""\
<style>
.gp-card {
    background-color: #FEF3C7;
    border: 2px solid #F59E0B;
    border-radius: 12px;
    padding: 2rem;
    margin: 1rem 0;
}
.gp-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #92400E;
    margin-bottom: 0.5rem;
}
.gp-sub {
    font-size: 1rem;
    color: #78350F;
    margin-bottom: 0.5rem;
}
.gp-similar-box {
    background-color: #EDE9FE;
    border: 1px solid #A78BFA;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-top: 1rem;
}
.gp-similar-title {
    font-weight: bold;
    color: #5B21B6;
    margin-bottom: 0.5rem;
}
.gp-similar-desc {
    color: #4C1D95;
    font-weight: bold;
    margin-bottom: 0.3rem;
}
.gp-similar-outcome {
    color: #6D28D9;
    margin-left: 0.5rem;
    line-height: 1.6;
}
.gp-similar-lesson {
    color: #7C3AED;
    font-size: 0.9rem;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px dashed #C4B5FD;
}
.gp-detail-box {
    background-color: #FFFBEB;
    border: 1px solid #FCD34D;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-top: 1rem;
}
.gp-detail-title {
    font-size: 1rem;
    font-weight: bold;
    color: #92400E;
    margin-bottom: 0.5rem;
}
.gp-detail-item {
    color: #78350F;
    margin-left: 0.5rem;
    line-height: 1.8;
}
.gp-detail-reason {
    color: #9A3412;
    margin-left: 1rem;
    font-size: 0.9rem;
}
.gp-hint-box {
    background-color: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-top: 1rem;
}
.gp-hint-title {
    font-weight: bold;
    color: #166534;
    margin-bottom: 0.3rem;
}
.gp-hint-item {
    color: #15803D;
    margin-left: 0.5rem;
    line-height: 1.8;
}
.gp-consult {
    text-align: center;
    color: #6B7280;
    font-size: 0.85rem;
    margin-top: 1rem;
}
.gp-step-progress {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.75rem 0 1rem;
    font-size: 0.9rem;
}
.gp-step-dot-done {
    width: 10px; height: 10px; border-radius: 50%;
    background: #16A34A; display: inline-block;
}
.gp-step-dot-current {
    width: 12px; height: 12px; border-radius: 50%;
    background: #D97706; display: inline-block;
    box-shadow: 0 0 0 3px rgba(217,119,6,0.3);
}
.gp-step-dot-pending {
    width: 10px; height: 10px; border-radius: 50%;
    background: #D1D5DB; display: inline-block;
}
.gp-step-line { width: 2rem; height: 2px; background: #D1D5DB; }
.gp-step-line-done { width: 2rem; height: 2px; background: #16A34A; }
.gp-step-done-box {
    background: #F0FDF4; border: 1px solid #86EFAC;
    border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 1rem;
}
.gp-step-done-label { color: #166534; font-weight: bold; font-size: 0.95rem; }
.gp-step2-card {
    background-color: #FFFBEB; border: 2px solid #F59E0B;
    border-radius: 12px; padding: 1.5rem; margin: 0.5rem 0 1rem;
}
.gp-step2-title {
    font-size: 1.2rem; font-weight: bold; color: #92400E; margin-bottom: 0.75rem;
}
/* ボタンをカード風に大型化 */
.stButton > button {
    min-height: 130px !important;
    font-size: 1.05rem !important;
    white-space: pre-wrap !important;
    line-height: 1.8 !important;
    border-radius: 12px !important;
    font-weight: bold !important;
    padding: 1.2rem 1rem !important;
    transition: transform 0.1s, box-shadow 0.1s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}
/* 修繕系ボタン（左列） */
.repair-btn .stButton > button {
    background: linear-gradient(135deg, #FEF2F2, #FEE2E2) !important;
    border: 2px solid #F87171 !important;
    color: #991B1B !important;
}
.repair-btn .stButton > button:hover {
    background: linear-gradient(135deg, #FEE2E2, #FECACA) !important;
    border-color: #EF4444 !important;
}
/* 新規購入系ボタン（右列） */
.upgrade-btn .stButton > button {
    background: linear-gradient(135deg, #EFF6FF, #DBEAFE) !important;
    border: 2px solid #60A5FA !important;
    color: #1E3A8A !important;
}
.upgrade-btn .stButton > button:hover {
    background: linear-gradient(135deg, #DBEAFE, #BFDBFE) !important;
    border-color: #3B82F6 !important;
}
</style>
""")


# ---------------------------------------------------------------------------
# Humanize helpers
# ---------------------------------------------------------------------------

def _humanize_missing_fields(raw_fields: list) -> List[str]:
    """
    Gemini内部形式のmissing_fieldsを人間向けの日本語に変換する。
    フラグ形式・内部用語は除外し、自然な表現に整形する。
    """
    humanized = []
    for field in raw_fields:
        if not isinstance(field, str) or not field.strip():
            continue
        # フラグ形式（description:mixed_keyword, mixed_keyword:一式 等）を除外
        if re.match(r"^[a-z][a-z0-9_.]*:", field):
            continue
        # 英語のみのフラグを除外
        if re.match(r"^[a-z_]+$", field):
            continue
        # 「一式」のオウム返しを修正
        text = field.replace("\u4e00\u5f0f", "まとめ購入")
        # 「不明」→わかりやすい表現に
        text = re.sub(r"が不明(です)?$", "がわかりませんでした", text)
        text = re.sub(r"不明$", "の情報が足りません", text)
        text = text.strip()
        if text and text not in humanized:
            humanized.append(text)
    return humanized


def _humanize_why_matters(raw_reasons: list) -> List[str]:
    """why_missing_mattersを人間向けに変換する。"""
    humanized = []
    for reason in raw_reasons:
        if not isinstance(reason, str) or not reason.strip():
            continue
        text = reason.replace("\u4e00\u5f0f", "まとめ購入")
        text = text.strip()
        if text and text not in humanized:
            humanized.append(text)
    return humanized


# ---------------------------------------------------------------------------
# メインレンダリング
# ---------------------------------------------------------------------------

def render_guidance_panel(result: dict) -> Optional[str]:
    """
    GUIDANCE時の全画面演出パネルを描画する。

    レイアウト順序:
      1. ヘッダー（AIが止まった演出）
      2. 2択ボタン（修繕 or 新規購入）← 最上部
      3. 判断のヒント
      4. 類似事例（similar_case）← セレンディピティ
      5. なぜ止まったか（詳細）
      6. 税理士相談テキスト

    Args:
        result: APIレスポンス辞書

    Returns:
        "repair" / "upgrade" / None
    """
    # --- Session state 初期化 ---
    if "guidance_step" not in st.session_state:
        st.session_state.guidance_step = 1
    if "guidance_choice" not in st.session_state:
        st.session_state.guidance_choice = None
    if "guidance_detail" not in st.session_state:
        st.session_state.guidance_detail = None
    # Safety: step=2 なのに choice がない場合はリセット
    if st.session_state.guidance_step == 2 and not st.session_state.guidance_choice:
        st.session_state.guidance_step = 1
    # 前回の GUIDANCE フローが完了済み（detail が設定済み）なら新結果用にリセット
    if st.session_state.guidance_detail is not None:
        st.session_state.guidance_step = 1
        st.session_state.guidance_choice = None
        st.session_state.guidance_detail = None

    # --- CSS ---
    st.markdown(_GP_CSS, unsafe_allow_html=True)

    # ============================================================
    # STEP 2: 詳細質問（early return — 既存コードのインデント変更を回避）
    # ============================================================
    if st.session_state.guidance_step == 2:
        first_choice = st.session_state.guidance_choice
        choice_label = "\U0001f527 修繕・維持" if first_choice == "repair" else "\U0001f4e6 新規購入・増強"

        # ヘッダー
        st.markdown(
            '<div class="gp-card">'
            '<div class="gp-header">'
            "\U0001f4cb あと1つだけ教えてください</div>"
            '<div class="gp-sub">'
            "より正確に判定するための質問です。"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        # プログレス表示（Step 2）
        st.markdown(
            '<div class="gp-step-progress">'
            '<span class="gp-step-dot-done"></span>'
            '<span style="color:#16A34A;">質問1</span>'
            '<span class="gp-step-line-done"></span>'
            '<span class="gp-step-dot-current"></span>'
            '<span style="color:#D97706; font-weight:bold;">質問2</span>'
            '<span class="gp-step-line"></span>'
            '<span class="gp-step-dot-pending"></span>'
            '<span style="color:#9CA3AF;">判定</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        # Step 1 選択済み表示
        st.markdown(
            '<div class="gp-step-done-box">'
            f'<span class="gp-step-done-label">'
            f"\u2705 「{choice_label}」を選択済み</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("\u21a9 選び直す", key="gp_btn_back"):
            st.session_state.guidance_step = 1
            st.session_state.guidance_choice = None
            st.rerun()

        # 詳細質問: 修繕の場合
        if first_choice == "repair":
            st.markdown(
                '<div class="gp-step2-card">'
                '<div class="gp-step2-title">'
                "\U0001f527 修繕の頻度を教えてください</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="repair-btn">', unsafe_allow_html=True)
                if st.button(
                    "\U0001f504 定期的（3年以内）\n\n以前にも修理したことがある",
                    key="gp_btn_periodic",
                    use_container_width=True,
                ):
                    st.session_state.guidance_detail = "periodic"
                    return "repair"
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="upgrade-btn">', unsafe_allow_html=True)
                if st.button(
                    "\u2728 今回が初めて\n\n初めての修理です",
                    key="gp_btn_first_time",
                    use_container_width=True,
                ):
                    st.session_state.guidance_detail = "first_time"
                    return "repair"
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="gp-hint-box">'
                '<div class="gp-hint-title">\U0001f4a1 ヒント:</div>'
                '<div class="gp-hint-item">'
                "\u30fb定期的な修繕 \u2192 通常は経費として処理<br>"
                "\u30fb初めての大規模修繕 \u2192 資本的支出の可能性も"
                "</div></div>",
                unsafe_allow_html=True,
            )

        # 詳細質問: 新規購入の場合
        else:
            st.markdown(
                '<div class="gp-step2-card">'
                '<div class="gp-step2-title">'
                "\U0001f4e6 既存設備の入替ですか？</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="repair-btn">', unsafe_allow_html=True)
                if st.button(
                    "\U0001f504 はい（入替）\n\n古い設備を新しくする",
                    key="gp_btn_replacement",
                    use_container_width=True,
                ):
                    st.session_state.guidance_detail = "replacement"
                    return "upgrade"
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="upgrade-btn">', unsafe_allow_html=True)
                if st.button(
                    "\u2728 いいえ（純粋な新規）\n\n新しく追加する",
                    key="gp_btn_new",
                    use_container_width=True,
                ):
                    st.session_state.guidance_detail = "new"
                    return "upgrade"
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="gp-hint-box">'
                '<div class="gp-hint-title">\U0001f4a1 ヒント:</div>'
                '<div class="gp-hint-item">'
                "\u30fb既存設備の入替 \u2192 除却損の検討も必要<br>"
                "\u30fb純粋な新規導入 \u2192 資産計上が基本"
                "</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="gp-consult">'
            "わからない場合は税理士にご相談ください"
            "</div>",
            unsafe_allow_html=True,
        )
        return None

    # ============================================================
    # STEP 1: 初回質問（修繕 or 新規購入）
    # ============================================================

    # 1. ヘッダー（止まった感の演出）
    # ============================================================
    st.markdown(
        '<div class="gp-card">'
        '<div class="gp-header">'
        "\U0001f6d1 AIが判断を保留しました</div>"
        '<div class="gp-sub">'
        "この書類は自動判定できません。下のボタンで教えてください。"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # プログレス表示（Step 1）
    st.markdown(
        '<div class="gp-step-progress">'
        '<span class="gp-step-dot-current"></span>'
        '<span style="color:#D97706; font-weight:bold;">質問1</span>'
        '<span class="gp-step-line"></span>'
        '<span class="gp-step-dot-pending"></span>'
        '<span style="color:#9CA3AF;">質問2</span>'
        '<span class="gp-step-line"></span>'
        '<span class="gp-step-dot-pending"></span>'
        '<span style="color:#9CA3AF;">判定</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ============================================================
    # 2. 2択ボタン（最上部 — ユーザーが最初に見る）
    # ============================================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="repair-btn">', unsafe_allow_html=True)
        if st.button(
            "\U0001f527 修繕・維持\n\n壊れたものを直す\n\u2192 経費になります",
            key="gp_btn_repair",
            use_container_width=True,
        ):
            st.session_state.guidance_step = 2
            st.session_state.guidance_choice = "repair"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="upgrade-btn">', unsafe_allow_html=True)
        if st.button(
            "\U0001f4e6 新規購入・増強\n\n新しく買う・増やす\n\u2192 資産になります",
            key="gp_btn_upgrade",
            use_container_width=True,
        ):
            st.session_state.guidance_step = 2
            st.session_state.guidance_choice = "upgrade"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ============================================================
    # 3. 判断のヒント
    # ============================================================
    st.markdown(
        '<div class="gp-hint-box">'
        '<div class="gp-hint-title">\U0001f4a1 判断のヒント:</div>'
        '<div class="gp-hint-item">'
        "\u30fb元々ある設備の修理・メンテナンス \u2192 修繕<br>"
        "\u30fb初めて導入する、性能を上げる \u2192 新規購入"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ============================================================
    # 3.5 AI参考判定サマリー（GUIDANCE明細にai_hintがある場合）
    # ============================================================
    line_items = result.get("line_items", [])
    hints = [
        it for it in line_items
        if isinstance(it, dict)
        and it.get("classification") == "GUIDANCE"
        and isinstance(it.get("ai_hint"), dict)
        and it["ai_hint"].get("suggestion")
    ]
    if hints:
        _hint_icon = {"CAPITAL_LIKE": "\u2705", "EXPENSE_LIKE": "\U0001f4b0"}
        hint_rows = "".join(
            f'<div style="margin:0.2rem 0;">'
            f'{_hint_icon.get(h["ai_hint"]["suggestion"], "\u2753")} '
            f'{h.get("description", "")} \u2192 '
            f'<b>{h["ai_hint"].get("suggestion_label", "")}</b>'
            f' ({h["ai_hint"].get("confidence", 0):.0%})'
            f'</div>'
            for h in hints
        )
        st.markdown(
            '<div style="background:#E3F2FD;border:1px solid #90CAF9;'
            'border-radius:0.5rem;padding:0.8rem;margin:0.5rem 0;">'
            '<div style="color:#0D47A1;font-weight:bold;margin-bottom:0.3rem;">'
            '\U0001f916 AI\u53c2\u8003\u5224\u5b9a</div>'
            f'<div style="color:#1565C0;font-size:0.9rem;">{hint_rows}</div>'
            '<div style="color:#5C6BC0;font-size:0.75rem;margin-top:0.3rem;">'
            '\u203b \u3053\u308c\u306fAI\u306e\u53c2\u8003\u610f\u898b\u3067\u3059\u3002\u6700\u7d42\u5224\u65ad\u306f\u4e0a\u306e\u30dc\u30bf\u30f3\u3067\u9078\u3093\u3067\u304f\u3060\u3055\u3044\u3002'
            '</div></div>',
            unsafe_allow_html=True,
        )

    # ============================================================
    # 4. 類似事例（similar_case — セレンディピティ）
    # ============================================================
    similar_case: Optional[Dict] = result.get("similar_case")
    if isinstance(similar_case, dict) and similar_case.get("description"):
        desc = similar_case.get("description", "")
        outcome = similar_case.get("outcome", "")
        lesson = similar_case.get("lesson", "")
        st.markdown(
            '<div class="gp-similar-box">'
            '<div class="gp-similar-title">'
            "\U0001f4a1 似た事例:</div>"
            f'<div class="gp-similar-desc">{desc}</div>'
            '<div class="gp-similar-outcome">'
            f"\u2192 {outcome}</div>"
            + (
                f'<div class="gp-similar-lesson">'
                f"\U0001f4dd {lesson}</div>"
                if lesson
                else ""
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 5. なぜ止まったか（詳細 — ボタンの下に配置）
    # ============================================================
    raw_missing = result.get("missing_fields", [])
    raw_why = result.get("why_missing_matters", [])

    missing_fields = _humanize_missing_fields(raw_missing)
    why_matters = _humanize_why_matters(raw_why)

    if missing_fields:
        lines = []
        for i, field in enumerate(missing_fields):
            lines.append(f"\u30fb{field}")
            if i < len(why_matters):
                lines.append(
                    '<span class="gp-detail-reason">'
                    f"\u2192 {why_matters[i]}</span>"
                )
        st.markdown(
            '<div class="gp-detail-box">'
            '<div class="gp-detail-title">'
            "\U0001f50d AIが迷った理由:</div>"
            '<div class="gp-detail-item">'
            + "<br>".join(lines)
            + "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="gp-detail-box">'
            '<div class="gp-detail-title">'
            "\U0001f50d AIが迷った理由:</div>"
            '<div class="gp-detail-item">'
            "\u30fbこの書類は金額と品目から判断が分かれるケースです"
            "</div></div>",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 6. 税理士相談テキスト
    # ============================================================
    st.markdown(
        '<div class="gp-consult">'
        "わからない場合は税理士にご相談ください"
        "</div>",
        unsafe_allow_html=True,
    )

    return None
