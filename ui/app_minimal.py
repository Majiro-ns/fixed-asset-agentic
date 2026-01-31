#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Streamlit UI for fixed asset classification."""
import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent

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

st.title("📊 固定資産判定システム")
st.caption("見積書・請求書を「資産」か「経費」か「要確認」に自動分類します")
st.info("💡 **ヒント:** 「要確認」と表示された場合は、AIが判断に迷った項目です。エラーではありません。担当者の確認が必要な箇所を示しています。")

# Sidebar: Service URL and demo case selector
with st.sidebar:
    st.markdown("### 設定")
    service_url = st.text_input(
        "接続先サーバーURL",
        value="https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app",
        key="service_url",
    )

    st.markdown("### サンプルデータ")
    demo_cases_dir = ROOT_DIR / "data" / "demo"
    demo_cases = []
    if demo_cases_dir.exists():
        demo_cases = sorted([f.name for f in demo_cases_dir.glob("*.json")])

    if demo_cases:
        selected_demo = st.selectbox("サンプルを選択", ["選択しない"] + demo_cases, key="demo_selector")
    else:
        selected_demo = "選択しない"

    st.markdown("---")
    st.markdown("### PDFアップロード（任意）")
    st.caption("PDFファイルを直接アップロードして判定できます。")

# Initialize session state
if "result" not in st.session_state:
    st.session_state.result = None
if "prev_result" not in st.session_state:
    st.session_state.prev_result = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "initial_opal" not in st.session_state:
    st.session_state.initial_opal = None

# Input section
st.markdown("## 入力データ")

# PDF Upload (always available, server-side feature flag checked on upload)
uploaded_pdf = st.file_uploader("PDFファイルをアップロード（任意）", type=["pdf"], key="pdf_upload")
if uploaded_pdf:
    st.info(f"📄 アップロード済み: {uploaded_pdf.name}（{uploaded_pdf.size} バイト）")

# Opal JSON input (default flow)
opal_json_text = ""
if not uploaded_pdf:
    # Load demo case if selected
    if selected_demo != "選択しない" and demo_cases:
        demo_path = demo_cases_dir / selected_demo
        try:
            demo_json = json.loads(demo_path.read_text(encoding="utf-8"))
            opal_json_text = st.text_area(
                "見積書データ（JSON形式）",
                height=200,
                value=json.dumps(demo_json, ensure_ascii=False, indent=2),
                key="opal_input",
            )
        except Exception as e:
            st.error(f"サンプルデータの読み込みに失敗しました: {e}")
            opal_json_text = st.text_area(
                "見積書データ（JSON形式）",
                height=200,
                placeholder='{"invoice_date": "2024-01-01", "vendor": "株式会社サンプル", "line_items": [{"item_description": "サーバー設置工事", "amount": 500000, "quantity": 1}]}',
                key="opal_input",
            )
    else:
        opal_json_text = st.text_area(
            "見積書データ（JSON形式）",
            height=200,
            placeholder='{"invoice_date": "2024-01-01", "vendor": "株式会社サンプル", "line_items": [{"item_description": "サーバー設置工事", "amount": 500000, "quantity": 1}]}',
            key="opal_input",
        )

# Classify button (for Opal JSON)
if st.button("判定を実行", type="primary", use_container_width=True, disabled=bool(uploaded_pdf)):
    if not opal_json_text.strip():
        st.error("見積書データを入力してください")
    else:
        try:
            opal_json = json.loads(opal_json_text)
            st.session_state.initial_opal = opal_json.copy()
            
            # Call Cloud Run API
            classify_url = f"{service_url}/classify"
            payload = {"opal_json": opal_json}
            
            with st.spinner("判定中...しばらくお待ちください"):
                response = requests.post(
                    classify_url,
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                result_data = response.json()
            
            # Store result (preserve previous for comparison)
            if st.session_state.result:
                st.session_state.prev_result = st.session_state.result.copy()
            st.session_state.result = result_data
            st.session_state.answers = {}
            
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"JSONの形式が正しくありません: {e}")
        except requests.exceptions.Timeout:
            st.error("タイムアウトしました（15秒）。サーバーが混雑している可能性があります。")
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e, "response") and e.response is not None:
                # Handle 422 validation errors specifically
                if e.response.status_code == 422:
                    try:
                        error_body = e.response.json()
                        error_detail = f"入力データエラー (422): {json.dumps(error_body, indent=2, ensure_ascii=False)}"
                    except:
                        error_detail = f"入力データエラー (422): {e.response.text}"
                else:
                    try:
                        error_detail = e.response.text
                    except:
                        error_detail = str(e)
            else:
                error_detail = str(e)
            st.error(f"サーバーとの通信に失敗しました: {error_detail}")
        except Exception as e:
            st.error(f"判定処理に失敗しました: {e}")

# PDF Classify button (if PDF uploaded)
if uploaded_pdf:
    if st.button("PDFを判定", type="primary", use_container_width=True):
        try:
            # Call Cloud Run API /classify_pdf
            classify_pdf_url = f"{service_url}/classify_pdf"

            # Reset file pointer
            uploaded_pdf.seek(0)

            with st.spinner("PDFを解析中...しばらくお待ちください"):
                files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                response = requests.post(
                    classify_pdf_url,
                    files=files,
                    timeout=30,  # PDF processing may take longer
                )
                response.raise_for_status()
                result_data = response.json()
            
            # Store result (same as Opal JSON flow)
            if st.session_state.result:
                st.session_state.prev_result = st.session_state.result.copy()
            st.session_state.result = result_data
            st.session_state.answers = {}
            
            st.rerun()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e.response, 'status_code') else None

            # Handle 404: endpoint not available (demo accident prevention)
            if status_code == 404:
                st.error("**このサーバーではPDF判定機能が利用できません。**\n\n"
                        "PDF判定機能がまだデプロイされていません。\n"
                        "上のJSON入力欄にデータを入力して判定してください。")
                # Continue to next iteration (no return in Streamlit button handler)
            
            # Handle 400/503: feature disabled or service unavailable
            if status_code in (400, 503):
                try:
                    error_body = e.response.json()
                    error_detail = error_body.get("detail", {})

                    # Machine-readable check: detail.error == "PDF_CLASSIFY_DISABLED"
                    if isinstance(error_detail, dict) and error_detail.get("error") == "PDF_CLASSIFY_DISABLED":
                        how_to_enable = error_detail.get("how_to_enable", "サーバー側でPDF_CLASSIFY_ENABLED=1を設定")
                        message = error_detail.get("message", "このサーバーではPDF判定機能が無効です")
                        fallback = error_detail.get("fallback", "JSON入力欄にデータを入力して判定してください")
                        st.error(f"**サーバー側でPDF判定機能が無効になっています。**\n\n"
                                f"サーバーメッセージ: {message}\n\n"
                                f"有効化方法: {how_to_enable}\n\n"
                                f"代替手段: {fallback}\n\n"
                                "※ PDFアップロード欄は常に表示されますが、サーバー側の設定で機能が制限されている場合があります。")
                    else:
                        # Other 400/503 errors
                        st.error(f"PDF判定に失敗しました (HTTP {status_code}): {json.dumps(error_body, indent=2, ensure_ascii=False)}")
                except:
                    # Fallback: if JSON parsing fails, show raw response
                    response_text = e.response.text if hasattr(e.response, 'text') else str(e)
                    st.error(f"PDF判定に失敗しました (HTTP {status_code}): {response_text}")
            else:
                # Other HTTP errors (500, etc.)
                try:
                    error_body = e.response.json()
                    error_detail = error_body.get("detail", {})
                    # Check if detail is dict and has error field (consistent with 400/503 handling)
                    if isinstance(error_detail, dict) and error_detail.get("error") == "PDF_CLASSIFY_ERROR":
                        message = error_detail.get("message", "PDF判定に失敗しました")
                        st.error(f"**PDF判定エラー (HTTP {status_code}):**\n\n{message}")
                    else:
                        st.error(f"PDF判定に失敗しました (HTTP {status_code}): {json.dumps(error_body, indent=2, ensure_ascii=False)}")
                except:
                    st.error(f"PDF判定に失敗しました (HTTP {status_code}): {str(e)}")
        except requests.exceptions.Timeout:
            st.error("タイムアウトしました（30秒）。PDFの処理には時間がかかる場合があります。")
        except requests.exceptions.RequestException as e:
            st.error(f"PDF判定リクエストに失敗しました: {str(e)}")
        except Exception as e:
            st.error(f"PDF判定に失敗しました: {e}")

# Output section
if st.session_state.result:
    result = st.session_state.result
    
    # Show DIFF card if this is a rerun (prev_result exists)
    # This implements "Step 5: 差分保存" from README.md Agentic definition
    if st.session_state.prev_result and st.session_state.prev_result != result:
        prev = st.session_state.prev_result
        st.markdown("## 🔄 判定結果が更新されました")
        st.success("追加情報をもとに再判定を行いました。変更点は以下の通りです。")

        st.markdown("### 変更前 → 変更後の比較")
        diff_col1, diff_col2, diff_col3, diff_col4 = st.columns(4)
        with diff_col1:
            prev_decision = prev.get("decision", "UNKNOWN")
            new_decision = result.get("decision", "UNKNOWN")
            st.write("**判定結果**")
            st.write(f"`{prev_decision}` → `{new_decision}`")
            if prev_decision != new_decision:
                st.success("✓ 変更あり")
            else:
                st.info("変更なし")
        with diff_col2:
            prev_conf = prev.get("confidence", 0.0)
            new_conf = result.get("confidence", 0.0)
            st.write("**確信度**")
            st.write(f"{prev_conf:.2f} → {new_conf:.2f}")
            if abs(prev_conf - new_conf) > 0.01:
                st.info("✓ 更新")
        with diff_col3:
            prev_trace = prev.get("trace", [])
            new_trace = result.get("trace", [])
            st.write("**処理ステップ数**")
            st.write(f"{len(prev_trace)} → {len(new_trace)}")
            prev_trace_str = " → ".join(prev_trace)
            new_trace_str = " → ".join(new_trace)
            if prev_trace_str != new_trace_str:
                st.caption(f"変更前: {prev_trace_str}")
                st.caption(f"変更後: {new_trace_str}")
                st.info("✓ 拡張")
        with diff_col4:
            prev_citations = len(prev.get("citations", []))
            new_citations = len(result.get("citations", []))
            st.write("**法令参照数**")
            st.write(f"{prev_citations} → {new_citations}")
            if new_citations > prev_citations:
                st.info("✓ 追加")

        st.markdown("---")
    
    st.markdown("## 判定結果")

    # Decision badge with WIN+1 fields - prominent at top
    decision = result.get("decision", "UNKNOWN")

    # Decision display with visual distinction - 高卒事務でもわかる説明
    decision_config = {
        "CAPITAL_LIKE": ("✅", "資産計上の可能性あり", "#10B981", "10万円以上の設備投資など、固定資産として計上する可能性が高い項目です"),
        "EXPENSE_LIKE": ("💰", "経費処理の可能性あり", "#3B82F6", "消耗品や修繕費など、経費として処理する可能性が高い項目です"),
        "GUIDANCE": ("⚠️", "要確認（担当者の判断が必要）", "#F59E0B", "AIが自動判定できませんでした。経理担当者による確認が必要です"),
    }
    icon, label, color, desc = decision_config.get(decision, ("❓", "不明", "#6B7280", "判定できませんでした"))

    # Large decision display with color coding
    st.markdown(f"""
    <div style="background-color: {color}20; border-left: 4px solid {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <h3 style="margin: 0; color: {color};">{icon} 判定: {label}</h3>
        <p style="margin: 0.5rem 0 0 0; color: #374151;">{desc}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        confidence = result.get("confidence", 0.0)
        st.metric("確信度（AIの自信）", f"{confidence:.2f}")
    with col2:
        is_valid = result.get("is_valid_document", False)
        st.metric("データ形式", "正常" if is_valid else "異常あり")
    with col3:
        trace = result.get("trace", [])
        if trace:
            st.metric("処理ステップ数", len(trace))

    # Trace
    if trace:
        st.caption(f"処理の流れ: {' → '.join(trace)}")
    
    # Evidence panel - evidence-first, prominent (moved before Reasons)
    evidence = result.get("evidence", [])
    if evidence:
        st.markdown("### 判定根拠（なぜこの結果になったか）")
        for i, ev in enumerate(evidence):
            with st.expander(f"明細 {ev.get('line_no', '?')}: {ev.get('description', '')}（確信度: {ev.get('confidence', 0.8):.2f}）", expanded=(i == 0)):
                st.write(f"**確信度:** {ev.get('confidence', 0.8):.2f}")
                if ev.get("source_text"):
                    st.write("**元のテキスト:**")
                    st.code(ev["source_text"], language="text")
                if ev.get("position_hint"):
                    st.caption(f"位置: {ev['position_hint']}")
    
    # Citations (Google Cloud: Vertex AI Search results)
    citations = result.get("citations", [])
    st.markdown("### 関連法令・規則（参考情報）")
    if citations:
        st.info("関連する法令・ガイドラインが見つかりました（Vertex AI Search）")
        for i, citation in enumerate(citations):
            with st.expander(f"参照 {i+1}: {citation.get('title', '無題')}", expanded=(i == 0)):
                if citation.get("snippet"):
                    st.write("**抜粋:**")
                    st.code(citation["snippet"], language="text")
                if citation.get("uri"):
                    st.markdown(f"**出典:** [{citation['uri']}]({citation['uri']})")
                if citation.get("relevance_score"):
                    st.caption(f"関連度: {citation['relevance_score']:.2f}")
    else:
        # Show OFF state when feature is disabled (consistent with DEMO.md)
        st.caption("法令検索機能: OFF（サーバー側の設定で有効化できます）")
    
    # Reasons
    reasons = result.get("reasons", [])
    if reasons:
        st.markdown("#### 判定理由")
        for reason in reasons:
            st.write(f"- {reason}")
    
    # GUIDANCE: Questions and answers (agentic loop)
    if decision == "GUIDANCE":
        # Prominent "Agent needs info" panel at top
        st.markdown("---")
        st.markdown("### 🤖 追加情報が必要です")
        st.info("正確な判定を行うために、以下の情報を入力してください。AIが判断に迷った項目です。")

        missing_fields = result.get("missing_fields", [])
        why_missing = result.get("why_missing_matters", [])

        # Missing fields as checklist
        if missing_fields:
            st.markdown("#### 不足している情報（チェックリスト）")
            for i, mf in enumerate(missing_fields):
                checked = st.checkbox(
                    f"✓ {mf}",
                    value=mf in st.session_state.answers,
                    key=f"check_{i}",
                )
                if checked and mf not in st.session_state.answers:
                    st.session_state.answers[mf] = ""

        # Why missing matters (prominent)
        if why_missing:
            st.markdown("#### なぜこの情報が必要か")
            for why in why_missing[:3]:  # Limit to top 3
                st.write(f"• {why}")

        # What you should answer
        st.markdown("#### 確認していただきたいこと")
        st.caption("例：修繕なのか新規購入か、数量・単位、設置場所、耐用年数など")

        # Quick-pick buttons for common answers
        st.markdown("**よくある回答（クリックで選択）:**")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        with quick_col1:
            if st.button("修繕・メンテナンス", key="quick_repair"):
                st.session_state.answers["purpose"] = "repair"
                st.rerun()
        with quick_col2:
            if st.button("新規購入・設備増強", key="quick_upgrade"):
                st.session_state.answers["purpose"] = "upgrade"
                st.rerun()
        with quick_col3:
            if st.button("入力をクリア", key="quick_clear"):
                st.session_state.answers = {}
                st.rerun()
        
        # Questions from API response + missing_fields as form inputs
        questions = result.get("questions", [])
        with st.form("guidance_answers", clear_on_submit=False):
            st.markdown("#### 追加情報を入力")

            # Build form inputs from missing_fields
            form_answers = {}
            for i, mf in enumerate(missing_fields):
                answer = st.text_input(
                    f"**{mf}**",
                    value=st.session_state.answers.get(mf, ""),
                    key=f"form_{i}",
                    help=why_missing[i] if i < len(why_missing) else "追加の情報を入力してください",
                )
                if answer:
                    form_answers[mf] = answer

            # Also show questions from API if available
            if questions:
                for i, question in enumerate(questions):
                    q_key = f"q_{i}"
                    answer = st.text_input(
                        f"質問{i+1}: {question}",
                        value=st.session_state.answers.get(q_key, ""),
                        key=f"question_{i}",
                    )
                    if answer:
                        form_answers[q_key] = answer

            submitted = st.form_submit_button("追加情報をもとに再判定", type="primary")
            
            if submitted:
                # Update session state with form answers
                st.session_state.answers.update(form_answers)

                if st.session_state.initial_opal is None:
                    st.error("元のデータが見つかりません。最初から判定をやり直してください。")
                else:
                    try:
                        # Call Cloud Run API with answers
                        classify_url = f"{service_url}/classify"
                        payload = {
                            "opal_json": st.session_state.initial_opal,
                            "answers": st.session_state.answers,
                        }

                        with st.spinner("再判定中...しばらくお待ちください"):
                            response = requests.post(
                                classify_url,
                                json=payload,
                                timeout=15,
                            )
                            response.raise_for_status()
                            result_data = response.json()
                        
                        # Store previous result for comparison
                        st.session_state.prev_result = st.session_state.result.copy()
                        st.session_state.result = result_data
                        
                        st.rerun()
                        
                    except requests.exceptions.Timeout:
                        st.error("タイムアウトしました（15秒）。サーバーが混雑している可能性があります。")
                    except requests.exceptions.RequestException as e:
                        error_detail = ""
                        if hasattr(e, "response") and e.response is not None:
                            # Handle 422 validation errors specifically
                            if e.response.status_code == 422:
                                try:
                                    error_body = e.response.json()
                                    error_detail = f"入力データエラー (422): {json.dumps(error_body, indent=2, ensure_ascii=False)}"
                                except:
                                    error_detail = f"入力データエラー (422): {e.response.text}"
                            else:
                                try:
                                    error_detail = e.response.text
                                except:
                                    error_detail = str(e)
                        else:
                            error_detail = str(e)
                        st.error(f"サーバーとの通信に失敗しました: {error_detail}")
                    except Exception as e:
                        st.error(f"再判定に失敗しました: {e}")
    
    # Full result JSON (collapsible)
    with st.expander("詳細データ（JSON形式・技術者向け）", expanded=False):
        st.json(result)
