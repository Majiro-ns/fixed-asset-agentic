# -*- coding: utf-8 -*-
import json
import sys
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# --- ensure project root on sys.path (fix: ModuleNotFoundError: core) ---
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.policy import load_policy
from core.pdf_extract import extract_pdf, extraction_to_opal
from core.pipeline import run_pdf_pipeline

APP_TITLE = "見積書 固定資産判定（自動抽出 × 自動判定）"
APP_SUB = "項目抽出 / 自動判定処理（確認ポイント）"
TAGLINE = "疑わしい行は止める。人が見るべき行だけ残す。"

VALUE_STATEMENT = "AIが迷う行では自動判定を止め、人が確認すべき行だけを浮かび上がらせます。"
VALUE_BULLETS = [
    "固定資産/費用判定の誤りを防ぐ",
    "判断根拠（注意事項）が残り、後から検証できる",
    "AIに責任を押し付けない、責任境界の明確化",
]

STEP1 = "Step1｜データ抽出（入力データの補正）"
STEP2 = "Step2｜変換処理（データ形式の固定 v1.0）"
STEP3 = "Step3｜自動判定（3値・断定しない）"

STOP_NOTE = "要確認は精度不足ではなく、判断停止（確認ポイント）です。"
STEP_LABELS = ["Step1 抽出", "Step2 正規化", "Step3 判定"]

SAMPLE_DIR = ROOT_DIR / "data" / "opal_outputs"
POLICY_OPTIONS = {
    "None（デフォルト）": None,
    "company_default（demo）": ROOT_DIR / "policies" / "company_default.json",
}


def _read_json_file(path: Path) -> Dict[str, Any]:
    txt = path.read_text(encoding="utf-8-sig")
    return json.loads(txt)


def _safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _truncate(s: str, n: int = 30) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + "..."


def _count_by_class(items: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"CAPITAL_LIKE": 0, "EXPENSE_LIKE": 0, "GUIDANCE": 0}
    for it in items:
        c = (it.get("classification") or "").upper()
        if c in counts:
            counts[c] += 1
    return counts


def _to_table_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for it in items:
        cls = (it.get("classification") or "")
        label_ja = it.get("label_ja") or ""
        desc = it.get("description") or ""
        amount = it.get("amount")
        rationale_ja = it.get("rationale_ja") or ""
        flags = it.get("flags") or []
        flags_str_raw = ", ".join(flags) if isinstance(flags, list) else str(flags)
        flags_str = flags_str_raw if flags_str_raw else ""
        amount_display: Any = amount
        if isinstance(amount, (int, float)) and not isinstance(amount, bool):
            try:
                amount_display = f"JPY {amount:,.0f}"
            except Exception:
                amount_display = amount

        ev = it.get("evidence") or {}
        source_text = ""
        if isinstance(ev, dict):
            source_text = ev.get("source_text") or ""
        evidence_short = _truncate(source_text, 30)

        if str(cls).upper() == "GUIDANCE":
            prefix = "[要確認] "
            if not label_ja.startswith(prefix):
                label_ja = prefix + label_ja
            if not desc.startswith(prefix):
                desc = prefix + desc

        rows.append(
            {
                "priority": "要確認" if str(cls).upper() == "GUIDANCE" else "",
                "line_no": it.get("line_no"),
                "description": desc,
                "amount_display": amount_display,
                "label_ja": label_ja,
                "分類結果": cls,
                "判定理由": rationale_ja,
                "注意事項": flags_str,
                "根拠": evidence_short,
            }
        )
    return rows


def _render_dataframe(rows: List[Dict[str, Any]]) -> None:
    if rows:
        ordered_rows: List[Dict[str, Any]] = []
        preferred = ["description", "amount_display", "分類結果", "判定理由", "注意事項", "根拠"]
        for r in rows:
            ordered: Dict[str, Any] = {}
            for key in preferred:
                if key in r:
                    ordered[key] = r[key]
            for key, val in r.items():
                if key not in ordered:
                    ordered[key] = val
            ordered_rows.append(ordered)
    else:
        ordered_rows = rows
    column_config = {
        "amount_display": st.column_config.TextColumn("金額", help="表示用（JPYカンマ区切り）"),
    }
    try:
        st.dataframe(ordered_rows, hide_index=True, use_container_width=True, column_config=column_config)
    except TypeError:
        st.dataframe(ordered_rows, use_container_width=True, column_config=column_config)


def _sort_rows_for_review(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    order = {"GUIDANCE": 0, "CAPITAL_LIKE": 1, "EXPENSE_LIKE": 2}
    return sorted(rows, key=lambda r: order.get(str(r.get("分類結果", "")).upper(), 9))


def _summarize_flags(flags: Any) -> Optional[str]:
    if isinstance(flags, list) and flags:
        raw_list = flags
    elif flags:
        raw_list = [str(flags)]
    else:
        return None
    humanized = []
    for f in raw_list:
        s = str(f)
        if s.startswith("policy:"):
            s = "企業ポリシー"
        elif s.startswith("mixed_keyword:"):
            s = "キーワード"
        elif s.startswith("regex:"):
            s = "正規表現"
        humanized.append(s)
        if len(humanized) >= 3:
            break
    return "/".join(humanized)


def _render_warnings(warnings: Optional[List[Dict[str, Any]]]) -> None:
    if not warnings:
        return
    for w in warnings:
        code = w.get("code") or "WARNING"
        msg = w.get("message") or ""
        page = f"(page {w.get('page')})" if w.get("page") is not None else ""
        st.warning(f"[{code}] {msg} {page}".strip())


def _init_state() -> None:
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "opal_dict" not in st.session_state:
        st.session_state.opal_dict = None
    if "input_source" not in st.session_state:
        st.session_state.input_source = "json"
    if "extraction" not in st.session_state:
        st.session_state.extraction = None
    if "adapted_doc" not in st.session_state:
        st.session_state.adapted_doc = None
    if "final_doc" not in st.session_state:
        st.session_state.final_doc = None
    if "policy_display" not in st.session_state:
        st.session_state.policy_display = "None"
    if "policy_path" not in st.session_state:
        st.session_state.policy_path = None
    if "applied_policy_display" not in st.session_state:
        st.session_state.applied_policy_display = "None"
    if "applied_policy_path" not in st.session_state:
        st.session_state.applied_policy_path = None
    if "pdf_extraction" not in st.session_state:
        st.session_state.pdf_extraction = None
    if "pdf_final_doc" not in st.session_state:
        st.session_state.pdf_final_doc = None
    if "pdf_upload_path" not in st.session_state:
        st.session_state.pdf_upload_path = None
    if "pdf_extract_path" not in st.session_state:
        st.session_state.pdf_extract_path = None
    if "pdf_final_path" not in st.session_state:
        st.session_state.pdf_final_path = None


def _go(step: int) -> None:
    st.session_state.step = step


def _save_uploaded_pdf(uploaded_file):
    if uploaded_file is None:
        return None
    uploads = ROOT_DIR / "data" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    path = uploads / f"{timestamp}_{safe_name}"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def _render_json_flow(policy_display: str, policy_path: Optional[str]) -> None:
    step_labels = STEP_LABELS
    current = st.session_state.step
    nav_step = st.radio(
        "ステップを選択",
        options=list(range(3)),
        format_func=lambda i: step_labels[i],
        index=current,
        horizontal=True,
    )
    if nav_step != current:
        _go(nav_step)
        current = nav_step

    st.progress(current / 2)
    st.caption(f"現在：{STEP_LABELS[current]}（Step1→Step2→Step3）")

    if st.session_state.step == 0:
        st.success(VALUE_STATEMENT)
        st.markdown("### このツールでできること")
        for b in VALUE_BULLETS:
            st.write(f"・{b}")

        with st.expander("進め方（3ステップ）", expanded=True):
            st.write(STEP1)
            st.write(STEP2)
            st.write(STEP3)

        st.markdown("## Step1｜入力（抽出データJSON）")
        st.caption("判定エンジンがOCR・項目抽出までを担当します。ここでサンプル選択またはJSON貼付を行います。")

        colA, colB = st.columns([1, 1], gap="large")

        with colA:
            st.markdown("### サンプル選択")
            samples: List[str] = []
            if SAMPLE_DIR.exists():
                samples = sorted([p.name for p in SAMPLE_DIR.glob("*.json")])
            sample_name = st.selectbox("サンプルを選択", options=(["（なし）"] + samples), index=1 if len(samples) else 0, help="デモ用の抽出JSONを選択できます")

            sample_data = None
            if sample_name and sample_name != "（なし）":
                try:
                    sample_data = _read_json_file(SAMPLE_DIR / sample_name)
                except Exception as e:
                    st.error(f"サンプル読み込みに失敗しました: {e}")

        with colB:
            st.markdown("### テキスト貼付")
            pasted = st.text_area(
                "抽出JSON を貼付（サンプル選択した場合は不要）",
                height=260,
                placeholder='例: {"vendor": null, "invoice_date": "...", "line_items": [...]}',
            )

        opal_dict: Optional[Dict[str, Any]] = None
        if sample_data is not None:
            opal_dict = sample_data
        elif pasted.strip():
            try:
                opal_dict = json.loads(pasted)
            except Exception as e:
                st.error(f"JSONのパースに失敗しました: {e}")

        st.divider()

        left, right = st.columns([1, 1])
        with left:
            st.caption("判定を実行すると自動でStep3へ進みます。Step2はナビで確認できます。")
        with right:
            run_disabled = opal_dict is None
            st.caption(f"Policy: {policy_display}")

            if st.button("判定を実行して進む", type="primary", use_container_width=True, disabled=run_disabled):
                try:
                    adapted = adapt_opal_to_v1(opal_dict)
                    policy_cfg = load_policy(policy_path)
                    final_doc = classify_document(adapted, policy_cfg)
                    st.session_state.applied_policy_display = policy_display
                    st.session_state.applied_policy_path = policy_path
                    st.session_state.opal_dict = opal_dict
                    st.session_state.adapted_doc = adapted
                    st.session_state.final_doc = final_doc
                    _go(2)
                except Exception as e:
                    st.error(f"判定に失敗しました: {e}")

        with st.expander("入力JSONプレビュー（任意）", expanded=False):
            if opal_dict is None:
                st.caption("サンプル選択または貼付を行うとプレビューできます。")
            else:
                st.code(_safe_json_dumps(opal_dict), language="json")

        return

    if st.session_state.step == 1:
        st.markdown("## Step2｜変換処理（正規化結果）")
        st.caption("抽出データを固定形式に正規化した内容を確認します。次へ進むと判定結果が出ます。")
        st.caption(f"Policy: {st.session_state.policy_display}")
        adapted = st.session_state.adapted_doc

        if adapted is None:
            st.warning("Step1でサンプル選択または貼付を行い、判定ボタンを押してください。")
        else:
            st.info("変換処理の出力（主要フィールドのみ抜粋）。")
            st.code(_safe_json_dumps(adapted), language="json")

        st.divider()
        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("戻る（Step1 入力）", use_container_width=True):
                _go(0)
        with b2:
            if st.button("次へ（Step3 判定）", type="primary", use_container_width=True, disabled=st.session_state.final_doc is None):
                _go(2)

        return

    if st.session_state.step == 2:
        st.markdown("## Step3｜自動判定")
        opal_dict = st.session_state.opal_dict
        final_doc = st.session_state.final_doc
        st.caption(f"Policy: {st.session_state.applied_policy_display}")
        _render_warnings(final_doc.get("warnings") if isinstance(final_doc, dict) else None)

        if not opal_dict or not final_doc:
            st.warning("結果がありません。Step1で入力し、判定を実行してください。")
            if st.button("Step1へ戻る", type="primary"):
                _go(0)
            return

        items = final_doc.get("line_items") or []
        counts = _count_by_class(items)
        guidance_items = [it for it in items if str(it.get("classification") or "").upper() == "GUIDANCE"]

        st.markdown("### 結果サマリー")

        # GUIDANCE件数が0より大きい場合は強調表示
        if counts["GUIDANCE"] > 0:
            st.markdown(f"""
            <div class="guidance-card">
                <h4 style="margin:0; color:#B45309;">⚠️ 要確認（GUIDANCE）: {counts["GUIDANCE"]}件</h4>
                <p style="margin:0.5rem 0 0 0; color:#78350F;">人による確認が必要な行があります</p>
            </div>
            """, unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("⚠️ 要確認", counts["GUIDANCE"], help="人による確認が必要な項目")
        m2.metric("✅ 資産計上の可能性あり", counts["CAPITAL_LIKE"], help="固定資産として計上される可能性が高い項目")
        m3.metric("💰 経費処理の可能性あり", counts["EXPENSE_LIKE"], help="経費として処理される可能性が高い項目")
        top_reason = None
        for it in guidance_items:
            summary = _summarize_flags(it.get("flags"))
            if summary:
                top_reason = summary
                break
        if top_reason:
            st.caption(f"🔍 代表的な停止理由: {top_reason}")
        st.info(STOP_NOTE)

        with st.container(border=True):
            st.markdown("**確認ポイント（断定しない思想）**")
            st.write("・撤去/移設/既設など、判断が割れる可能性があれば要確認として停止します。")
            st.write("・停止理由は注意事項に残し、後から検証できるようにします。")
            st.write("・最終的な判断（資産/費用の選択肢）は人が、現場で決める形にします。")

        st.markdown("### 判定結果（要確認順に表示）")
        if counts.get("GUIDANCE", 0) > 0:
            st.warning("要確認（GUIDANCE）は誤判定ではありません。判断が割れる可能性があるため停止しています。")
        rows = _to_table_rows(items)
        rows = _sort_rows_for_review(rows)
        _render_dataframe(rows)

        if guidance_items:
            with st.expander("要確認（GUIDANCE）の理由（クリックで開く）", expanded=False):
                options = list(range(len(guidance_items)))
                fmt = lambda idx: f"{guidance_items[idx].get('line_no') or '-'}: { (guidance_items[idx].get('description') or '')[:40] }"
                selected_idx = st.selectbox("要確認行を選択", options=options, format_func=fmt, key="guidance_select")
                selected_item = guidance_items[selected_idx]
                ev = selected_item.get("evidence") or {}
                source_text = ev.get("source_text") if isinstance(ev, dict) else ""
                flags = selected_item.get("flags") or []
                flags_str = ", ".join(flags) if isinstance(flags, list) else str(flags or "")
                with st.container(border=True):
                    st.write(f"行番号: {selected_item.get('line_no')}")
                    st.write(f"内容: {selected_item.get('description') or ''}")
                    st.write(f"分類ラベル: {selected_item.get('label_ja') or ''}")
                    st.write(f"理由: {selected_item.get('rationale_ja') or ''}")
                    if flags_str:
                        st.write(f"注意事項: {flags_str}")
                    if source_text:
                        st.write("根拠テキスト:")
                        st.code(source_text, language="text")

                guidance_rows: List[Dict[str, Any]] = []
                for it in guidance_items:
                    ev = it.get("evidence") or {}
                    source_text = ""
                    if isinstance(ev, dict):
                        source_text = ev.get("source_text") or ""
                    flags = it.get("flags") or []
                    flags_str = ", ".join(flags) if isinstance(flags, list) else str(flags or "")
                    row = {
                        "line_no": it.get("line_no"),
                        "description": it.get("description") or "",
                        "label_ja": it.get("label_ja") or "",
                        "判定理由": it.get("rationale_ja") or "",
                        "注意事項": flags_str,
                    }
                    if source_text:
                        row["根拠テキスト"] = source_text
                    guidance_rows.append(row)
                st.dataframe(guidance_rows, hide_index=True, use_container_width=True)
        else:
            st.caption("要確認（GUIDANCE）はありません。")

        st.markdown("### 次にやること")
        st.write("1. 要確認（GUIDANCE）の行を優先して、人が判断します。")
        st.write("2. 注意事項/根拠を見て、必要なら見積書原本に戻って確認します。")
        st.write("3. 判断結果をJSONとして保存・共有できます。")

        with st.expander("入力JSON（生データ）", expanded=False):
            st.code(_safe_json_dumps(opal_dict), language="json")

        with st.expander("Final JSON（全体）", expanded=False):
            st.code(_safe_json_dumps(final_doc), language="json")

        st.markdown("### 出力（保存）")
        final_text = _safe_json_dumps(final_doc)
        final_bytes = final_text.encode("utf-8-sig")
        st.caption("ダウンロードはUTF-8（BOM付き）で保存します（Windows互換）。")
        st.download_button(
            label="final.json をダウンロード",
            data=final_bytes,
            file_name="final.json",
            mime="application/json",
            use_container_width=True,
        )

        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("戻る（Step2 正規化）", use_container_width=True):
                _go(1)
        with b2:
            if st.button("Step1 入力へ", use_container_width=True):
                _go(0)


def _render_pdf_flow(policy_display: str, policy_path: Optional[str]) -> None:
    st.markdown("## PDFアップロード")
    st.caption(f"適用ポリシー: {policy_display}")
    uploaded_pdf = st.file_uploader("PDFファイルを選択", type=["pdf"], key="pdf_upload_input", help="見積書・請求書などのPDFをアップロードしてください")
    st.caption("💡 PDF抽出にはDocument AI（USE_DOCAI=1）またはローカルOCR（USE_LOCAL_OCR=1）を使用できます。")

    col_run, col_info = st.columns([1, 1])
    with col_run:
        disabled = uploaded_pdf is None
        if st.button("PDF→固定資産判定（進む/止まる）", type="primary", use_container_width=True, disabled=disabled):
            try:
                saved_pdf = _save_uploaded_pdf(uploaded_pdf)
                if saved_pdf is None:
                    raise ValueError("PDF file was not provided")
                result = run_pdf_pipeline(saved_pdf, ROOT_DIR / "data" / "results", policy_path)
                st.session_state.pdf_upload_path = str(result["upload_path"])
                st.session_state.pdf_extraction = result["extraction"]
                st.session_state.pdf_final_doc = result["final_doc"]
                st.session_state.pdf_extract_path = str(result["extraction_path"])
                st.session_state.pdf_final_path = str(result["final_path"])
                st.success("PDF→固定資産判定が完了しました。")
            except Exception as e:
                st.error(f"PDF出力に失敗しました: {e}")
    with col_info:
        if st.session_state.pdf_upload_path:
            st.write(f"📁 アップロード先: {st.session_state.pdf_upload_path}")
        if st.session_state.pdf_extract_path and st.session_state.pdf_final_path:
            st.write(f"📄 結果ファイル: {st.session_state.pdf_extract_path} / {st.session_state.pdf_final_path}")

    extraction = st.session_state.pdf_extraction
    final_doc = st.session_state.pdf_final_doc
    if not extraction or not final_doc:
        st.info("📤 PDFをアップロードして「判定を実行」ボタンを押してください。結果がここに表示されます。")
        return

    _render_warnings(final_doc.get("warnings") if isinstance(final_doc, dict) else None)

    items = final_doc.get("line_items") or []
    counts = _count_by_class(items)

    st.markdown("### 結果サマリー")
    m1, m2, m3 = st.columns(3)
    m1.metric("⚠️ 要確認", counts["GUIDANCE"], help="人による確認が必要な項目")
    m2.metric("✅ 資産計上の可能性あり", counts["CAPITAL_LIKE"], help="固定資産として計上される可能性が高い項目")
    m3.metric("💰 経費処理の可能性あり", counts["EXPENSE_LIKE"], help="経費として処理される可能性が高い項目")
    st.info(STOP_NOTE)

    st.markdown("### 判定結果とエビデンス")
    rows = _sort_rows_for_review(_to_table_rows(items))
    _render_dataframe(rows)

    evidence_rows: List[Dict[str, Any]] = []
    for page in extraction.get("pages") or []:
        page_no = page.get("page")
        for ev in page.get("evidence") or []:
            evidence_rows.append(
                {
                    "page": ev.get("page") or page_no,
                    "method": ev.get("method"),
                    "snippet": ev.get("snippet"),
                }
            )
    if evidence_rows:
        st.markdown("### エビデンス（抽出元の参照箇所）")
        st.dataframe(evidence_rows, hide_index=True, use_container_width=True)

    final_snippets: List[Dict[str, Any]] = []
    for it in items:
        ev = it.get("evidence") or {}
        for snip in ev.get("snippets") or []:
            final_snippets.append(
                {
                    "line_no": it.get("line_no"),
                    "page": snip.get("page"),
                    "method": snip.get("method"),
                    "snippet": snip.get("snippet"),
                }
            )
    if final_snippets:
        with st.expander("📎 最終判定のエビデンス（抽出結果→判定）", expanded=False):
            st.dataframe(final_snippets, hide_index=True, use_container_width=True)

    with st.expander("📄 抽出テキスト（ページごと）", expanded=False):
        for p in extraction.get("pages") or []:
            st.write(f"ページ {p.get('page')}: 抽出方法={p.get('method')}")
            st.code(p.get("text") or "", language="text")

    with st.expander("🔧 JSONデータ（開発者向け）", expanded=False):
        st.caption("抽出結果 (extraction)")
        st.code(_safe_json_dumps(extraction), language="json")
        st.caption("最終判定 (final)")
        st.code(_safe_json_dumps(final_doc), language="json")


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # カスタムCSS - GUIDANCE強調とアクセシビリティ改善
    st.markdown("""
    <style>
        /* GUIDANCE highlight - amber warning */
        .guidance-card {
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        /* CAPITAL_LIKE - green */
        .capital-card {
            background-color: #D1FAE5;
            border-left: 4px solid #10B981;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
        }
        /* EXPENSE_LIKE - blue */
        .expense-card {
            background-color: #DBEAFE;
            border-left: 4px solid #3B82F6;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
        }
        /* Focus visibility for accessibility */
        button:focus, input:focus, select:focus {
            outline: 3px solid #2563EB !important;
            outline-offset: 2px;
        }
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .stMetric label { font-size: 0.8rem; }
            .stMetric > div { padding: 0.5rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    _init_state()

    st.title(f"📊 {APP_TITLE}")
    st.caption(APP_SUB)
    st.caption(TAGLINE)
    st.info(
        "**なぜ「止まる自動判定」が必要なのか**\n"
        "現場では「誰かが確認したはず」という前提で処理されます。\n"
        "月末・決算期は、AIの結果も人の判断も十分に疑う余裕がありません。\n"
        "この仕組みは、疑わしい行を自動でGUIDANCEで停止し、\n"
        "「疑う余裕がない状況」でも誤った判定が通過しないようにします。"
    )

    st.sidebar.markdown("### ⚙️ 設定")
    policy_choice = st.sidebar.radio("判定ポリシー", options=list(POLICY_OPTIONS.keys()), help="企業固有の判定ルールを選択できます")
    selected_policy_path = POLICY_OPTIONS.get(policy_choice)
    policy_path: Optional[str] = None
    policy_display = "なし"
    if selected_policy_path:
        p = Path(selected_policy_path)
        if p.exists():
            policy_path = str(p)
            policy_display = p.name
        else:
            st.sidebar.warning(f"⚠️ ポリシーファイル `{p}` が見つかりません。デフォルト設定を使用します。")
    st.sidebar.caption(f"📋 適用中のポリシー: {policy_display}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 ヘルプ")
    st.sidebar.caption("・**要確認**: AIが判断を停止した項目。人による確認が必要です。")
    st.sidebar.caption("・**資産計上の可能性あり**: 固定資産として計上される可能性が高い項目。")
    st.sidebar.caption("・**経費処理の可能性あり**: 経費として処理される可能性が高い項目。")
    st.session_state.policy_path = policy_path
    st.session_state.policy_display = policy_display

    tab_json, tab_pdf = st.tabs(["📋 JSON入力", "📤 PDFアップロード"])
    with tab_json:
        _render_json_flow(policy_display, policy_path)
    with tab_pdf:
        _render_pdf_flow(policy_display, policy_path)


if __name__ == "__main__":
    main()
