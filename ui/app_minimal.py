#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Streamlit UI for fixed asset classification."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent


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

st.title("📊 固定資産判定システム")
st.caption("見積書・請求書を「資産」か「経費」に自動分類します")

# Sidebar: demo case selector
with st.sidebar:
    # サーバーURLは固定（ユーザーに見せない）
    service_url = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

    st.markdown("### サンプルデータ")
    demo_cases_dir = ROOT_DIR / "data" / "demo"
    demo_cases = []
    if demo_cases_dir.exists():
        demo_cases = sorted([f.name for f in demo_cases_dir.glob("*.json")])

    if demo_cases:
        selected_demo = st.selectbox("サンプルを選択", ["-- サンプルを選択 --"] + demo_cases, key="demo_selector")
    else:
        selected_demo = "-- サンプルを選択 --"

    st.markdown("---")
    st.markdown("### 読み取りモード")
    pdf_mode = st.radio(
        "読み取り方式を選択",
        options=["通常モード", "高精度モード"],
        index=0,
        key="pdf_mode",
        help="複雑なPDFは「高精度モード」を選んでください"
    )
    if pdf_mode == "高精度モード":
        st.caption("手書き・複雑な表・様々な様式のPDFに対応します")


# Initialize session state
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
st.markdown("## 見積書をアップロード")

# PDF Upload (メインの入力方法)
uploaded_pdf = st.file_uploader("PDFファイルをドラッグ＆ドロップ", type=["pdf"], key="pdf_upload")
if uploaded_pdf:
    st.success(f"📄 {uploaded_pdf.name} を読み込みました")

# Opal JSON input (開発者向け・折りたたみ)
opal_json_text = ""
if not uploaded_pdf:
    with st.expander("テキストで入力（開発者向け）", expanded=False):
        # Load demo case if selected
        if selected_demo != "-- サンプルを選択 --" and demo_cases:
            demo_path = demo_cases_dir / selected_demo
            try:
                demo_json = json.loads(demo_path.read_text(encoding="utf-8"))
                opal_json_text = st.text_area(
                    "見積書データ",
                    height=150,
                    value=json.dumps(demo_json, ensure_ascii=False, indent=2),
                    key="opal_input",
                )
            except Exception:
                opal_json_text = st.text_area(
                    "見積書データ",
                    height=150,
                    placeholder='{"line_items": [{"item_description": "サーバー設置工事", "amount": 500000}]}',
                    key="opal_input",
                )
        else:
            opal_json_text = st.text_area(
                "見積書データ",
                height=150,
                placeholder='{"line_items": [{"item_description": "サーバー設置工事", "amount": 500000}]}',
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
            
        except json.JSONDecodeError:
            st.error("入力データの形式が正しくありません。正しい形式で入力してください。")
        except requests.exceptions.Timeout:
            st.error("タイムアウトしました。しばらく経ってから再度お試しください。")
        except requests.exceptions.RequestException:
            st.error("サーバーとの通信に失敗しました。しばらく経ってから再度お試しください。")
        except Exception:
            st.error("判定処理に失敗しました。しばらく経ってから再度お試しください。")

# PDF Classify button (if PDF uploaded)
if uploaded_pdf:
    if st.button("PDFを判定", type="primary", use_container_width=True):
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
    
    st.markdown("## 判定結果")

    # Decision badge with WIN+1 fields - prominent at top
    decision = result.get("decision", "UNKNOWN")

    # Decision display with visual distinction - 高卒事務でもわかる説明
    decision_config = {
        "CAPITAL_LIKE": ("✅", "資産計上の可能性あり", "#10B981", "10万円以上の設備投資など、固定資産として計上する可能性が高い項目です"),
        "EXPENSE_LIKE": ("💰", "経費処理の可能性あり", "#3B82F6", "消耗品や修繕費など、経費として処理する可能性が高い項目です"),
        "GUIDANCE": ("⚠️", "要確認", "#F59E0B", ""),  # 止まるAI - 判定せず確認を求める
    }
    icon, label, color, desc = decision_config.get(decision, ("❓", "不明", "#6B7280", "判定できませんでした"))

    # Large decision display with color coding
    # GUIDANCEの場合は「止まる」を強調 - 判定を出さず確認を求める
    if decision == "GUIDANCE":
        # 「止まるAI」のコンセプトを体現
        st.markdown(f"""
        <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
            <h2 style="margin: 0; color: #B45309;">⚠️ 要確認</h2>
            <p style="margin: 0.8rem 0 0 0; font-size: 1.1rem; color: #92400E; font-weight: 500;">AIの判断では確定できません</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #78350F;">追加情報をいただければ、判定が可能になります。</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # CAPITAL_LIKE / EXPENSE_LIKE の場合
        # 確信度90%超なら免責不要、それ以下なら免責表示
        confidence = result.get("confidence", 0.0)
        if confidence > 0.9:
            # 高確信度: 免責不要
            st.markdown(f"""
            <div style="background-color: {color}20; border-left: 4px solid {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: {color};">{icon} 判定: {label}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #374151;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 確信度90%以下: 免責表示追加
            st.markdown(f"""
            <div style="background-color: {color}20; border-left: 4px solid {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: {color};">{icon} 判定: {label}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #374151;">{desc}</p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #6B7280;">※最終判断は税理士・経理担当者にご確認ください。</p>
            </div>
            """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        confidence = result.get("confidence", 0.0)
        st.metric("判定の確かさ", f"{confidence:.0%}")
    with col2:
        is_valid = result.get("is_valid_document", False)
        st.metric("データ形式", "OK" if is_valid else "要確認")

    # 耐用年数表示（CAPITAL_LIKEの場合のみ）
    useful_life = result.get("useful_life")
    if decision == "CAPITAL_LIKE" and useful_life and useful_life.get("useful_life_years", 0) > 0:
        years = useful_life.get("useful_life_years")
        category = useful_life.get("category", "")
        subcategory = useful_life.get("subcategory", "")
        legal_basis = useful_life.get("legal_basis", "")
        ul_confidence = useful_life.get("confidence", 0.0)

        st.markdown("### 📅 法定耐用年数")
        ul_col1, ul_col2 = st.columns(2)
        with ul_col1:
            st.metric("耐用年数", f"{years}年")
        with ul_col2:
            st.metric("判定の確かさ", f"{ul_confidence:.0%}")

        if category or subcategory:
            st.write(f"**資産区分**: {category}" + (f" / {subcategory}" if subcategory else ""))
        if legal_basis:
            st.caption(f"根拠: {legal_basis}")

    # Evidence panel - evidence-first, prominent (moved before Reasons)
    evidence = result.get("evidence", [])
    if evidence:
        st.markdown("### 判定根拠（なぜこの結果になったか）")
        for i, ev in enumerate(evidence):
            with st.expander(f"明細 {ev.get('line_no', '?')}: {ev.get('description', '')}", expanded=(i == 0)):
                if ev.get("source_text"):
                    st.write("**元のテキスト:**")
                    st.code(ev["source_text"], language="text")
    
    # Citations (Google Cloud: Vertex AI Search results)
    citations = result.get("citations", [])
    st.markdown("### 関連法令・規則（参考情報）")
    if citations:
        st.info("関連する法令・ガイドラインが見つかりました")
        for i, citation in enumerate(citations):
            with st.expander(f"参照 {i+1}: {citation.get('title', '無題')}", expanded=(i == 0)):
                if citation.get("snippet"):
                    st.write("**抜粋:**")
                    st.code(citation["snippet"], language="text")
                if citation.get("uri"):
                    st.markdown(f"**出典:** [{citation['uri']}]({citation['uri']})")
    else:
        st.caption("※関連法令の自動検索は現在準備中です")
    
    # Reasons
    reasons = result.get("reasons", [])
    if reasons:
        # 技術的なフラグを人間向け説明に変換
        display_reasons = []
        seen = set()
        for reason in reasons:
            formatted = _format_reason_for_display(reason)
            if formatted and formatted not in seen:
                display_reasons.append(formatted)
                seen.add(formatted)

        if display_reasons:
            st.markdown("#### 判定理由")
            for reason in display_reasons:
                st.write(f"- {reason}")
    
    # GUIDANCE: Questions and answers (agentic loop)
    if decision == "GUIDANCE":
        # Prominent "Agent needs info" panel at top - 「聞く」を強調
        st.markdown("---")
        st.markdown("### 追加情報をお聞きします")
        st.warning("AIが判断するために、以下の情報が必要です。")

        missing_fields = result.get("missing_fields", [])
        why_missing = result.get("why_missing_matters", [])

        # 不足情報をシンプルに表示
        if missing_fields:
            st.markdown("#### 不足している情報")
            for mf in missing_fields:
                st.write(f"• {mf}")

        # Why missing matters (prominent)
        if why_missing:
            st.markdown("#### なぜこの情報が必要か")
            for why in why_missing[:3]:  # Limit to top 3
                st.write(f"• {why}")

        # 用途選択（クイック選択）
        st.markdown("#### この支出の目的を選んでください")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔧 修繕・メンテナンス", use_container_width=True, key="btn_repair"):
                st.session_state.answers["purpose"] = "repair"
                st.rerun()
        with col_btn2:
            if st.button("📦 新規購入・設備増強", use_container_width=True, key="btn_upgrade"):
                st.session_state.answers["purpose"] = "upgrade"
                st.rerun()

        # 選択状態を表示
        if st.session_state.answers.get("purpose"):
            purpose_label = "修繕・メンテナンス" if st.session_state.answers["purpose"] == "repair" else "新規購入・設備増強"
            st.success(f"選択中: {purpose_label}")

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
                        st.error("タイムアウトしました。しばらく経ってから再度お試しください。")
                    except requests.exceptions.RequestException:
                        st.error("サーバーとの通信に失敗しました。しばらく経ってから再度お試しください。")
                    except Exception:
                        st.error("再判定に失敗しました。しばらく経ってから再度お試しください。")
    
    # Full result JSON (collapsible) - 審査員向け
    with st.expander("詳細データ（開発者向け）", expanded=False):
        st.json(result)
