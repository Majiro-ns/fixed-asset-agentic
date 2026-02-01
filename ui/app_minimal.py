#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Streamlit UI for fixed asset classification."""
import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent

# API URL (環境変数で上書き可能)
DEFAULT_API_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"
API_URL = os.environ.get("API_URL", DEFAULT_API_URL)


def _format_reason_for_display(reason: str) -> Optional[str]:
    """
    技術的なflag表記を人間向けの説明に変換する。
    不要な技術情報はNoneを返してスキップ。
    """
    # tax_rule フラグを法令説明に変換
    if "flag: tax_rule:" in reason:
        if "R-AMOUNT-003" in reason:
            return "国税庁基準: 10万円未満は少額資産として費用処理可能"
        elif "R-AMOUNT-100k200k" in reason:
            return "国税庁基準: 10万円以上20万円未満は一括償却資産の可能性あり"
        elif "R-AMOUNT-001" in reason:
            return "国税庁基準: 20万円以上は一括償却資産の確認が必要"
        elif "R-AMOUNT-SME300k" in reason:
            return "国税庁基準: 30万円未満は中小企業特例の適用可能性あり"
        elif "R-AMOUNT-600k" in reason:
            return "国税庁基準: 60万円以上は資本的支出vs修繕費の判定が必要"
        else:
            return None  # 不明なルールはスキップ

    # その他の技術的flagはスキップ
    if reason.startswith("flag: "):
        # no_keywords, conflicting_keywords などはユーザーに見せない
        if "no_keywords" in reason or "conflicting" in reason or "mixed_keyword" in reason:
            return None
        if "policy:" in reason:
            return None
        if "api_error" in reason or "parse_error" in reason:
            return None
        return None

    # APIエラー系のメッセージは非表示
    if "Gemini API エラー" in reason or "Gemini レスポンス解析エラー" in reason:
        return None

    # 通常の判定理由はそのまま表示
    return reason

st.set_page_config(
    page_title="固定資産判定システム",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better visual hierarchy and accessibility
st.markdown("""
<style>
    /* GUIDANCE highlight - amber warning color */
    .guidance-highlight {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    /* CAPITAL_LIKE - green success */
    .capital-highlight {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    /* EXPENSE_LIKE - blue info */
    .expense-highlight {
        background-color: #DBEAFE;
        border-left: 4px solid #3B82F6;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    /* Improve button focus visibility for accessibility */
    button:focus {
        outline: 3px solid #2563EB;
        outline-offset: 2px;
    }
    /* Responsive text */
    @media (max-width: 768px) {
        .stMetric label { font-size: 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📊 固定資産判定システム")
st.caption("見積書・請求書の「資産/経費」判定をAIが支援します")

# Initialize session state (サイドバーより先に初期化)
if "result" not in st.session_state:
    st.session_state.result = None
if "prev_result" not in st.session_state:
    st.session_state.prev_result = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "initial_opal" not in st.session_state:
    st.session_state.initial_opal = None
if "last_demo" not in st.session_state:
    st.session_state.last_demo = None
# 判定履歴（蓄積用）
if "history" not in st.session_state:
    st.session_state.history = []


def _add_to_history(source_name: str, result: Dict[str, Any]) -> None:
    """判定結果を履歴に追加"""
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    useful_life = result.get("useful_life", {}) or {}
    line_items = result.get("line_items", [])

    # 各明細を履歴に追加
    for item in line_items:
        desc = item.get("description", "")
        amount = item.get("amount")
        item_class = item.get("classification", decision)

        # フォールバック名はスキップ
        if desc.startswith("明細(") or desc.startswith("明細（"):
            desc = ""

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_name,
            "description": desc,
            "amount": amount,
            "decision": item_class,
            "confidence": confidence,
            "category": useful_life.get("category", ""),
            "useful_life_years": useful_life.get("useful_life_years", ""),
        }
        st.session_state.history.append(entry)

    # 明細がない場合はドキュメント単位で追加
    if not line_items:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_name,
            "description": "",
            "amount": None,
            "decision": decision,
            "confidence": confidence,
            "category": useful_life.get("category", ""),
            "useful_life_years": useful_life.get("useful_life_years", ""),
        }
        st.session_state.history.append(entry)


def _export_history_csv() -> str:
    """履歴をCSV形式でエクスポート"""
    output = io.StringIO()
    fieldnames = [
        "timestamp", "source", "description", "amount",
        "decision", "confidence", "category", "useful_life_years"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in st.session_state.history:
        writer.writerow(entry)
    return output.getvalue()


# 初回アクセスガイド
if "show_guide" not in st.session_state:
    st.session_state.show_guide = True

if st.session_state.show_guide:
    with st.container():
        st.info("""
**はじめての方へ** 📖

**使い方**
1. PDFをアップロード、またはサイドバーでサンプルを選択
2. 「判定を実行」ボタンをクリック

**このシステムの特徴: 止まる→聞く→変わる**
- **止まる**: 判断が難しい場合、AIは無理に判定せず「要確認」で停止します
- **聞く**: 「修繕？新規購入？」など、判定に必要な情報を質問します
- **変わる**: 追加情報をもとに再判定し、結果の変化を明示します

💡 まずはサイドバーの「サンプルデータ」から試してみてください！
        """)
        if st.button("✕ 閉じる", key="close_guide"):
            st.session_state.show_guide = False
            st.rerun()

# Sidebar
with st.sidebar:
    # サーバーURLは環境変数またはデフォルト
    service_url = API_URL

    st.markdown("### サンプルデータ")
    demo_cases_dir = ROOT_DIR / "data" / "demo"
    demo_cases = []
    if demo_cases_dir.exists():
        demo_cases = sorted([f.name for f in demo_cases_dir.glob("*.json")])

    if demo_cases:
        selected_demo = st.selectbox("サンプルを選択", ["-- サンプルを選択 --"] + demo_cases, key="demo_selector")
    else:
        selected_demo = "-- サンプルを選択 --"

    # 読み取りモード（常時表示）
    st.markdown("---")
    st.markdown("### 読み取りモード")
    pdf_mode = st.radio(
        "PDF読み取り方式",
        options=["通常モード", "高精度モード"],
        index=0,
        key="pdf_mode",
        label_visibility="collapsed"
    )
    if pdf_mode == "高精度モード":
        st.caption("手書き・複雑な表に対応")

    # 判定履歴・エクスポート
    st.markdown("---")
    st.markdown("### 判定履歴")
    history_count = len(st.session_state.history)
    st.caption(f"蓄積件数: {history_count}件")

    if history_count > 0:
        # CSVエクスポートボタン
        csv_data = _export_history_csv()
        st.download_button(
            label="📥 CSVエクスポート",
            data=csv_data,
            file_name=f"fixed_asset_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # 履歴クリアボタン
        if st.button("🗑️ 履歴をクリア", use_container_width=True):
            st.session_state.history = []
            st.rerun()


# サンプル切り替え時にセッションをリセット
if "demo_selector" in st.session_state:
    current_demo = st.session_state.get("demo_selector")
    if current_demo != st.session_state.last_demo:
        st.session_state.result = None
        st.session_state.prev_result = None
        st.session_state.answers = {}
        st.session_state.initial_opal = None
        st.session_state.last_demo = current_demo

# Input section
# サンプルデータを読み込む
opal_json_text = ""
demo_cases_dir = ROOT_DIR / "data" / "demo"  # 再定義（スコープ明確化）
current_selected = st.session_state.get("demo_selector", "-- サンプルを選択 --")

if current_selected != "-- サンプルを選択 --":
    demo_path = demo_cases_dir / current_selected
    if demo_path.exists():
        try:
            demo_json = json.loads(demo_path.read_text(encoding="utf-8"))
            opal_json_text = json.dumps(demo_json, ensure_ascii=False)
            st.info(f"📋 サンプル: {current_selected}")
        except Exception:
            st.error(f"サンプル読み込みエラー: {current_selected}")

# PDF Upload
uploaded_pdf = st.file_uploader("PDFをアップロード", type=["pdf"], key="pdf_upload", label_visibility="collapsed")
if uploaded_pdf:
    st.caption(f"📄 {uploaded_pdf.name}")

if not uploaded_pdf and not opal_json_text:
    st.caption("PDFをアップロード、またはサイドバーでサンプル選択")

# 判定ボタン（サンプルJSON用）
if opal_json_text and not uploaded_pdf:
    if st.button("🔍 判定を実行", type="primary", use_container_width=True):
        try:
            opal_json = json.loads(opal_json_text)
            st.session_state.initial_opal = opal_json.copy()

            classify_url = f"{service_url}/classify"
            payload = {"opal_json": opal_json}

            with st.spinner("判定中..."):
                response = requests.post(classify_url, json=payload, timeout=15)
                response.raise_for_status()
                result_data = response.json()

            if st.session_state.result:
                st.session_state.prev_result = st.session_state.result.copy()
            st.session_state.result = result_data
            st.session_state.answers = {}

            # 履歴に追加
            _add_to_history(current_selected, result_data)

            st.rerun()

        except json.JSONDecodeError:
            st.error("データ形式エラー")
        except requests.exceptions.RequestException:
            st.error("通信エラー。しばらく経ってから再度お試しください。")
        except Exception:
            st.error("判定に失敗しました。")

# PDF判定ボタン
if uploaded_pdf:
    if st.button("🔍 PDFを判定", type="primary", use_container_width=True):
        try:
            # Call Cloud Run API /classify_pdf
            classify_pdf_url = f"{service_url}/classify_pdf"

            # Reset file pointer
            uploaded_pdf.seek(0)

            # Determine extraction mode from sidebar selection
            use_gemini_vision = st.session_state.get("pdf_mode", "通常モード") == "高精度モード"

            with st.spinner("PDFを解析中..." + ("（高精度モード）" if use_gemini_vision else "")):
                files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                # Pass extraction mode and useful life flag as query parameters
                params = {}
                if use_gemini_vision:
                    params["use_gemini_vision"] = "1"
                params["estimate_useful_life_flag"] = "1"  # 常に耐用年数を判定
                response = requests.post(
                    classify_pdf_url,
                    files=files,
                    params=params,
                    timeout=60 if use_gemini_vision else 30,  # Gemini Vision may take longer
                )
                response.raise_for_status()
                result_data = response.json()
            
            # Store result (same as Opal JSON flow)
            if st.session_state.result:
                st.session_state.prev_result = st.session_state.result.copy()
            st.session_state.result = result_data
            st.session_state.answers = {}

            # 履歴に追加
            _add_to_history(uploaded_pdf.name, result_data)

            st.rerun()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e.response, 'status_code') else None

            # シンプルなエラーメッセージ（ユーザー向け）
            if status_code == 404:
                st.error("PDF判定機能は現在ご利用いただけません。テキスト入力をご利用ください。")
            elif status_code in (400, 503):
                st.error("PDF判定機能は現在ご利用いただけません。テキスト入力をご利用ください。")
            else:
                st.error("PDF判定に失敗しました。しばらく経ってから再度お試しください。")
        except requests.exceptions.Timeout:
            st.error("処理に時間がかかっています。しばらく経ってから再度お試しください。")
        except requests.exceptions.RequestException:
            st.error("通信に失敗しました。しばらく経ってから再度お試しください。")
        except Exception:
            st.error("判定に失敗しました。しばらく経ってから再度お試しください。")

# Output section
if st.session_state.result:
    result = st.session_state.result
    
    # Show DIFF card if this is a rerun (prev_result exists)
    # This implements "Step 5: 差分保存" from README.md Agentic definition
    # 「変わる」を強調 - 追加情報により判定が変化したことを明示
    if st.session_state.prev_result and st.session_state.prev_result != result:
        prev = st.session_state.prev_result
        st.markdown("## 🔄 判定が変わりました")

        prev_decision = prev.get("decision", "UNKNOWN")
        new_decision = result.get("decision", "UNKNOWN")
        prev_conf = prev.get("confidence", 0.0)
        new_conf = result.get("confidence", 0.0)

        # 判定変化を強調表示
        decision_labels = {
            "CAPITAL_LIKE": "資産計上の可能性あり",
            "EXPENSE_LIKE": "経費処理の可能性あり",
            "GUIDANCE": "要確認",
            "UNKNOWN": "不明",
        }
        prev_label = decision_labels.get(prev_decision, prev_decision)
        new_label = decision_labels.get(new_decision, new_decision)

        if prev_decision != new_decision:
            st.success(f"追加情報をもとに判定できるようになりました。")
            st.markdown(f"""
            <div style="background-color: #D1FAE5; border: 2px solid #10B981; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
                <p style="margin: 0; font-size: 1.2rem;">
                    <span style="color: #6B7280; text-decoration: line-through;">{prev_label}</span>
                    <span style="margin: 0 0.5rem;">→</span>
                    <strong style="color: #065F46;">{new_label}</strong>
                </p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #374151;">
                    判定の確かさ: {prev_conf:.0%} → <strong>{new_conf:.0%}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.caption("この変化の履歴は監査時の説明資料として利用できます。")
        else:
            st.info("追加情報を反映しましたが、判定は変わりませんでした。")
            st.write(f"**判定の確かさ**: {prev_conf:.0%} → **{new_conf:.0%}**")

        st.markdown("---")
    
    # 判定結果
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)

    # GUIDANCEの場合：確信度・傾向も表示しつつ、支出目的を聞く
    if decision == "GUIDANCE":
        # 傾向を分析（evidenceから）
        evidence = result.get("evidence", [])
        cap_count = sum(1 for e in evidence if e.get("classification") == "CAPITAL_LIKE")
        exp_count = sum(1 for e in evidence if e.get("classification") == "EXPENSE_LIKE")

        if cap_count > exp_count:
            tendency = "資産寄りの傾向"
            tendency_color = "#10B981"
        elif exp_count > cap_count:
            tendency = "経費寄りの傾向"
            tendency_color = "#3B82F6"
        else:
            tendency = "判断が分かれています"
            tendency_color = "#F59E0B"

        st.markdown(f"""
        <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem;">
            <h3 style="margin: 0; color: #B45309;">⚠️ 要確認</h3>
            <p style="margin: 0.3rem 0 0 0; font-size: 0.9rem; color: #78350F;">
                確信度: <strong>{confidence:.0%}</strong> ｜
                <span style="color: {tendency_color};">{tendency}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**この支出の目的を教えてください**")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔧 修繕・メンテナンス", use_container_width=True, key="btn_repair"):
                st.session_state.answers["purpose"] = "repair"
                st.rerun()
        with col_btn2:
            if st.button("📦 新規購入・設備増強", use_container_width=True, key="btn_upgrade"):
                st.session_state.answers["purpose"] = "upgrade"
                st.rerun()

        # 選択後の再判定
        if st.session_state.answers.get("purpose"):
            purpose_label = "修繕・メンテナンス" if st.session_state.answers["purpose"] == "repair" else "新規購入・設備増強"
            st.success(f"選択: {purpose_label}")
            if st.button("🔄 この情報で再判定", type="primary", use_container_width=True):
                if st.session_state.initial_opal:
                    try:
                        classify_url = f"{service_url}/classify"
                        payload = {"opal_json": st.session_state.initial_opal, "answers": st.session_state.answers}
                        with st.spinner("再判定中..."):
                            response = requests.post(classify_url, json=payload, timeout=15)
                            response.raise_for_status()
                            result_data = response.json()
                        st.session_state.prev_result = st.session_state.result.copy()
                        st.session_state.result = result_data
                        st.rerun()
                    except Exception:
                        st.error("再判定に失敗しました。")

    else:
        # CAPITAL_LIKE / EXPENSE_LIKE
        decision_config = {
            "CAPITAL_LIKE": ("✅", "資産計上の可能性あり", "#10B981"),
            "EXPENSE_LIKE": ("💰", "経費処理の可能性あり", "#3B82F6"),
        }
        icon, label, color = decision_config.get(decision, ("❓", "不明", "#6B7280"))

        st.markdown(f"""
        <div style="background-color: {color}20; border-left: 4px solid {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem;">
            <h3 style="margin: 0; color: {color};">{icon} {label}</h3>
            <p style="margin: 0.3rem 0 0 0; font-size: 0.9rem; color: #6B7280;">確信度: {confidence:.0%}</p>
        </div>
        """, unsafe_allow_html=True)

        # 耐用年数・資産種類（CAPITAL_LIKEのみ、コンパクト表示）
        useful_life = result.get("useful_life")
        if decision == "CAPITAL_LIKE" and useful_life and useful_life.get("useful_life_years", 0) > 0:
            years = useful_life.get("useful_life_years")
            category = useful_life.get("category", "")
            subcategory = useful_life.get("subcategory", "")

            # 資産種類を表示
            if category and category != "不明":
                category_text = category
                if subcategory:
                    category_text = f"{category}（{subcategory}）"
                st.caption(f"📦 資産種類: {category_text}")

            st.caption(f"📅 法定耐用年数: {years}年")

    # 判定理由（コンパクト表示）
    reasons = result.get("reasons", [])
    if reasons:
        display_reasons = []
        seen = set()
        for reason in reasons:
            formatted = _format_reason_for_display(reason)
            if formatted and formatted not in seen:
                display_reasons.append(formatted)
                seen.add(formatted)

        if display_reasons:
            st.markdown("**判定理由:**")
            for reason in display_reasons:
                st.caption(f"• {reason}")

    # 明細一覧（金額・内容）
    line_items = result.get("line_items", [])
    if line_items:
        with st.expander("明細一覧", expanded=True):
            for idx, item in enumerate(line_items, 1):
                desc = item.get("description", "")
                amount = item.get("amount")

                # 「明細(金額)」のようなフォールバック名は除外
                if desc.startswith("明細(") or desc.startswith("明細（"):
                    desc = ""

                if amount is not None:
                    amount_str = f"¥{amount:,.0f}"
                    if desc:
                        st.caption(f"{idx}. {desc}  —  {amount_str}")
                    else:
                        st.caption(f"{idx}. {amount_str}")
                elif desc:
                    st.caption(f"{idx}. {desc}")

    # 詳細情報は折りたたみ
    evidence = result.get("evidence", [])
    if evidence:
        with st.expander("判定根拠", expanded=False):
            for ev in evidence:
                desc = ev.get('description', '')
                src = ev.get('source_text', '')
                if src:
                    st.caption(f"{desc}: {src}")
