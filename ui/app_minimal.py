#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Streamlit UI for fixed asset classification."""
import csv
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent

# 親ディレクトリをsys.pathに追加（coreモジュール等のインポート用）
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# .env ファイルから環境変数を読み込み
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass  # python-dotenv がなければスキップ

# 新機能モジュールのインポート（オプショナル）
try:
    from ui.similar_cases import render_similar_cases
    SIMILAR_CASES_AVAILABLE = True
except ImportError:
    SIMILAR_CASES_AVAILABLE = False

try:
    from core.ledger_import import import_ledger_safe
    LEDGER_IMPORT_AVAILABLE = True
except ImportError:
    LEDGER_IMPORT_AVAILABLE = False

try:
    from api.embedding_store import EmbeddingStore
    from api.similarity_search import search_similar
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

# 履歴ベース検索（API不要版）
try:
    from api.history_search import search_similar_from_history
    HISTORY_SEARCH_AVAILABLE = True
except ImportError:
    HISTORY_SEARCH_AVAILABLE = False

# PDF分割機能（高精度モード用）
try:
    from core.pdf_splitter import generate_thumbnail_grid_with_metadata
    from api.gemini_splitter import detect_document_boundaries
    PDF_SPLITTER_AVAILABLE = True
    PDF_SPLITTER_ERROR = None
except ImportError as e:
    PDF_SPLITTER_AVAILABLE = False
    PDF_SPLITTER_ERROR = str(e)

# API URL (環境変数で上書き可能)
DEFAULT_API_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"
API_URL = os.environ.get("API_URL", DEFAULT_API_URL)


def _get_applicable_tax_rules(total_amount: Optional[float]) -> List[str]:
    """金額に基づいて該当する税務ルールのみを返す"""
    if total_amount is None:
        return []
    rules = []
    amount = float(total_amount)
    if amount < 100000:
        rules.append("10万円未満 → 少額資産として全額経費OK")
    elif amount < 200000:
        rules.append("10〜20万円 → 一括償却資産（3年均等）を選べます")
    elif amount < 300000:
        rules.append("20〜30万円 → 中小企業なら特例で全額経費にできる場合あり")
    else:
        rules.append("30万円以上 → 通常の固定資産として計上・償却が必要です")
    return rules


def _format_amount(amount: Any) -> str:
    """金額をカンマ区切りで表示"""
    if amount is None:
        return ""
    try:
        return f"¥{int(float(amount)):,}"
    except (ValueError, TypeError):
        return str(amount)


def _get_line_item_selection_key(source_name: str, index: int) -> str:
    """明細選択状態のキーを生成"""
    return f"{source_name}_{index}"


def _init_line_item_selections(source_name: str, line_items: List[Dict]) -> None:
    """明細選択状態を初期化（デフォルトは全てON）"""
    if source_name not in st.session_state.line_item_selections:
        st.session_state.line_item_selections[source_name] = {}
    for i in range(len(line_items)):
        if i not in st.session_state.line_item_selections[source_name]:
            st.session_state.line_item_selections[source_name][i] = True


def _get_selected_total(source_name: str, line_items: List[Dict]) -> Tuple[float, int]:
    """選択された明細の合計金額と件数を計算"""
    _init_line_item_selections(source_name, line_items)
    selections = st.session_state.line_item_selections.get(source_name, {})
    selected_total = 0.0
    selected_count = 0
    for i, item in enumerate(line_items):
        if selections.get(i, True):
            amount = item.get("amount", 0) or 0
            selected_total += amount
            selected_count += 1
    return selected_total, selected_count


def _check_duplicate(source_name: str, total_amount: float) -> bool:
    """履歴に同じファイル名・金額の組み合わせがあるかチェック"""
    for entry in st.session_state.history:
        if entry.get("source") == source_name:
            # 同じソース名が既にある
            return True
    return False


def _export_history_csv() -> bytes:
    """履歴をCSV形式でエクスポート（Excel対応UTF-8 BOM付き）"""
    output = io.StringIO()
    fieldnames = [
        "timestamp", "source", "description", "amount",
        "decision", "confidence", "category", "useful_life_years"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in st.session_state.history:
        writer.writerow(entry)
    # UTF-8 BOM付きでバイト列として返す（Excel文字化け対策）
    return ('\ufeff' + output.getvalue()).encode('utf-8')


def _add_to_history(source_name: str, result: Dict[str, Any]) -> None:
    """判定結果を履歴に追加"""
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    useful_life = result.get("useful_life", {}) or {}
    line_items = result.get("line_items", [])

    for item in line_items:
        desc = item.get("description", "")
        amount = item.get("amount")
        item_class = item.get("classification", decision)
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


# ページ設定
st.set_page_config(
    page_title="固定資産判定",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",  # サイドバーは初期非表示
)

# CSS（コンパクト化）
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h2 { margin-bottom: 0.5rem; }
    .stButton button { font-size: 1rem; }
</style>
""", unsafe_allow_html=True)

# Session state初期化
if "result" not in st.session_state:
    st.session_state.result = None
if "prev_result" not in st.session_state:
    st.session_state.prev_result = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "last_demo" not in st.session_state:
    st.session_state.last_demo = None
if "history" not in st.session_state:
    st.session_state.history = []
if "source_type" not in st.session_state:
    st.session_state.source_type = None
if "source_name" not in st.session_state:
    st.session_state.source_name = None
if "duplicate_warning" not in st.session_state:
    st.session_state.duplicate_warning = None
if "ledger_data" not in st.session_state:
    st.session_state.ledger_data = []
if "embedding_store" not in st.session_state:
    st.session_state.embedding_store = None
if "enable_history_search" not in st.session_state:
    st.session_state.enable_history_search = False
if "multi_doc_results" not in st.session_state:
    st.session_state.multi_doc_results = None  # 複数書類検出時の結果リスト
if "line_item_selections" not in st.session_state:
    st.session_state.line_item_selections = {}  # 明細ごとの選択状態 {source_name: {index: bool}}

# サイドバー（ヘルプ・設定を隠す）
with st.sidebar:
    st.markdown("## ⚙️ 設定")

    # 読み取りモード
    pdf_mode = st.radio(
        "PDF読み取り方式",
        options=["通常モード", "高精度モード（AI Vision）"],
        index=0,
        key="pdf_mode",
    )
    st.caption("高精度: 手書き・複雑な表に対応（処理時間長め）")

    # 類似検索スイッチ
    if HISTORY_SEARCH_AVAILABLE:
        st.session_state.enable_history_search = st.toggle(
            "📚 過去履歴から類似検索",
            value=st.session_state.enable_history_search,
            help="ONにすると、過去の判定履歴から類似事例を表示します"
        )

    st.markdown("---")

    # サンプルデータ
    st.markdown("### サンプルデータ")
    demo_cases_dir = ROOT_DIR / "data" / "demo"
    demo_cases = []
    if demo_cases_dir.exists():
        demo_cases = sorted([f.name for f in demo_cases_dir.glob("*.json")])
    if demo_cases:
        selected_demo = st.selectbox("サンプルを選択", ["--"] + demo_cases, key="demo_selector")
    else:
        selected_demo = "--"

    st.markdown("---")

    # 履歴・エクスポート
    st.markdown("### 📋 判定履歴")
    history_count = len(st.session_state.history)
    st.metric("蓄積件数", f"{history_count}件")

    if history_count > 0:
        csv_data = _export_history_csv()
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv_data,
            file_name=f"判定結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv; charset=utf-8",
            use_container_width=True,
        )
        if st.button("🗑️ 履歴クリア", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔧 開発者向け")
    st.session_state.dev_mode = st.toggle(
        "デバッグ表示",
        value=st.session_state.get("dev_mode", False),
        help="詳細なデバッグ情報を表示します"
    )

    st.markdown("---")
    st.markdown("### ❓ ヘルプ")
    with st.expander("使い方"):
        st.markdown("""
1. PDFをドラッグ＆ドロップ
2. 「判定」ボタンをクリック
3. 結果を確認、CSVでダウンロード
        """)
    with st.expander("判定結果の見方"):
        st.markdown("""
- **✅ 資産として計上**: 固定資産台帳へ
- **💰 経費として処理OK**: 今期の経費
- **⚠️ 確認が必要**: 税理士に相談
        """)
    with st.expander("制限事項"):
        st.markdown("""
**対応PDF**:
- 高精度モードは最大5ページまで
- 高精度モードでは複数書類の自動検出・分割に対応

**税理士への相談時**:
- CSVは判定結果の一覧です
- 相談時は**原本（PDF/画像）も一緒に**お渡しください
        """)

    st.markdown("---")
    st.markdown("### 🔒 セキュリティ")
    st.caption("""
• アップロードファイルはサーバーに保存されません
• 判定処理後すぐに削除されます
• 履歴はブラウザ内のみ（閉じると消えます）
    """)

    # 台帳インポート機能（新機能）
    if LEDGER_IMPORT_AVAILABLE and EMBEDDING_AVAILABLE:
        st.markdown("---")
        st.markdown("### 📚 過去台帳で学習")
        ledger_file = st.file_uploader(
            "固定資産台帳（CSV/Excel）",
            type=["csv", "xlsx", "xls"],
            key="ledger_upload",
            label_visibility="collapsed",
        )
        if ledger_file:
            if st.button("📥 台帳を読み込み", use_container_width=True):
                with st.spinner("読み込み中..."):
                    # 一時ファイルに保存
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(ledger_file.name).suffix) as tmp:
                        tmp.write(ledger_file.getvalue())
                        tmp_path = tmp.name
                    # インポート実行
                    result = import_ledger_safe(tmp_path)
                    os.unlink(tmp_path)  # 一時ファイル削除

                    if result["success"]:
                        st.session_state.ledger_data = result["data"]
                        st.success(f"✅ {len(result['data'])}件読み込み完了")
                        # Embedding生成（オプショナル）
                        if EMBEDDING_AVAILABLE and len(result["data"]) > 0:
                            try:
                                store = EmbeddingStore()
                                added = store.add_items(result["data"])
                                st.session_state.embedding_store = store
                                st.caption(f"類似検索用に{added}件を学習")
                            except Exception as e:
                                st.caption("類似検索は利用不可（APIキー未設定）")
                    else:
                        st.error(f"読み込みエラー: {result['error']}")

        if len(st.session_state.ledger_data) > 0:
            st.caption(f"学習済み: {len(st.session_state.ledger_data)}件")

# サンプル切り替え時にセッションリセット
if "demo_selector" in st.session_state:
    current_demo = st.session_state.get("demo_selector")
    if current_demo != st.session_state.last_demo:
        st.session_state.result = None
        st.session_state.prev_result = None
        st.session_state.answers = {}
        st.session_state.last_demo = current_demo
        st.session_state.duplicate_warning = None

# メイン画面
st.markdown("## 📊 固定資産判定")
service_url = API_URL

# 入力エリア
col_input, col_result = st.columns([1, 1])

with col_input:
    # PDFアップロード
    uploaded_pdf = st.file_uploader(
        "見積書・請求書（PDF）をアップロード",
        type=["pdf"],
        key="pdf_upload",
    )

    # サンプルデータ読み込み
    opal_json_text = ""
    current_selected = st.session_state.get("demo_selector", "--")
    if current_selected != "--":
        demo_path = demo_cases_dir / current_selected
        if demo_path.exists():
            try:
                opal_json_obj = json.loads(demo_path.read_text(encoding="utf-8"))
                opal_json_text = json.dumps(opal_json_obj, ensure_ascii=False)
                st.info(f"📋 サンプル: {current_selected}")
            except Exception:
                st.error("サンプル読み込みエラー")

    # 判定ボタン（サンプル用）
    if opal_json_text and not uploaded_pdf:
        if st.button("🔍 判定を実行", type="primary", use_container_width=True):
            try:
                opal_json = json.loads(opal_json_text)
                classify_url = f"{service_url}/classify"
                payload = {"opal_json": opal_json}
                with st.spinner("判定中..."):
                    response = requests.post(classify_url, json=payload, timeout=15)
                    response.raise_for_status()
                    result_data = response.json()

                # 重複チェック
                if _check_duplicate(current_selected, 0):
                    st.session_state.duplicate_warning = current_selected
                else:
                    st.session_state.duplicate_warning = None

                if st.session_state.result:
                    st.session_state.prev_result = st.session_state.result.copy()
                st.session_state.result = result_data
                st.session_state.answers = {}
                st.session_state.source_type = "json"
                st.session_state.source_name = current_selected
                _add_to_history(current_selected, result_data)
                st.rerun()
            except requests.exceptions.RequestException:
                st.error("⚠️ 通信エラー。インターネット接続を確認し、再度お試しください。")
            except Exception:
                st.error("⚠️ 判定に失敗しました。別のサンプルをお試しください。")

    # 判定ボタン（PDF用）
    if uploaded_pdf:
        if st.button("🔍 PDFを判定", type="primary", use_container_width=True):
            try:
                classify_pdf_url = f"{service_url}/classify_pdf"
                uploaded_pdf.seek(0)
                use_gemini_vision = "高精度" in st.session_state.get("pdf_mode", "")

                # 高精度モード + PDF分割機能が利用可能な場合、複数書類検出を試みる
                if st.session_state.get("dev_mode"):
                    st.write(f"🔧 PDF分割機能: {'有効' if PDF_SPLITTER_AVAILABLE else '無効'}")
                    if not PDF_SPLITTER_AVAILABLE and PDF_SPLITTER_ERROR:
                        st.write(f"   理由: {PDF_SPLITTER_ERROR}")
                    st.write(f"🔧 高精度モード: {'ON' if use_gemini_vision else 'OFF'}")

                if use_gemini_vision and PDF_SPLITTER_AVAILABLE:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_pdf.getvalue())
                        tmp_pdf_path = tmp.name

                    try:
                        with st.spinner("書類構造を解析中..."):
                            # サムネイルグリッド生成
                            grid_result = generate_thumbnail_grid_with_metadata(tmp_pdf_path)
                            total_pages = grid_result["total_pages"]

                            # 境界検出
                            boundaries = detect_document_boundaries(
                                grid_result["image_bytes"],
                                total_pages
                            )

                        # デバッグ: 境界検出結果を表示（開発者オプションON時）
                        if st.session_state.get("dev_mode"):
                            st.write(f"🔍 PDF分割デバッグ:")
                            st.write(f"   - total_pages={total_pages}")
                            st.write(f"   - len(boundaries)={len(boundaries)}")
                            st.write(f"   - boundaries (JSON):")
                            st.json(boundaries)
                            # 各書類の詳細
                            for i, b in enumerate(boundaries):
                                has_error = b.get("error", None)
                                st.write(f"   - 書類{i+1}: start_page={b.get('start_page')}, end_page={b.get('end_page')}, type={b.get('doc_type')}, error={has_error}")

                        # 複数書類が検出された場合
                        condition_len_gt_1 = len(boundaries) > 1
                        condition_no_error = not boundaries[0].get("error") if boundaries else False
                        if st.session_state.get("dev_mode"):
                            st.write(f"🔍 条件評価:")
                            st.write(f"   - len(boundaries) > 1 : {condition_len_gt_1}")
                            st.write(f"   - not boundaries[0].get('error') : {condition_no_error}")
                            st.write(f"   - 複数書類処理に進む: {condition_len_gt_1 and condition_no_error}")

                        if len(boundaries) > 1 and not boundaries[0].get("error"):
                            st.info(f"📑 {len(boundaries)}件の書類を検出しました")

                            # 各書類を個別に判定
                            multi_results = []
                            for doc in boundaries:
                                doc_label = f"書類{doc['document_id']}: {doc['doc_type']} (p.{doc['start_page']}-{doc['end_page']})"
                                with st.spinner(f"{doc_label} を判定中..."):
                                    # PDFを部分的に送信（ページ範囲指定）
                                    uploaded_pdf.seek(0)
                                    files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                                    params = {
                                        "estimate_useful_life_flag": "1",
                                        "use_gemini_vision": "1",
                                        "start_page": str(doc["start_page"]),
                                        "end_page": str(doc["end_page"]),
                                    }
                                    response = requests.post(
                                        classify_pdf_url, files=files, params=params,
                                        timeout=60,
                                    )
                                    response.raise_for_status()
                                    doc_result = response.json()
                                    doc_result["_doc_info"] = doc
                                    multi_results.append(doc_result)
                                    _add_to_history(f"{uploaded_pdf.name}_{doc['doc_type']}_{doc['document_id']}", doc_result)

                            # 複数書類結果を保存
                            st.session_state.multi_doc_results = multi_results
                            st.session_state.result = multi_results[0] if multi_results else None
                            st.session_state.source_type = "pdf_multi"
                            st.session_state.source_name = uploaded_pdf.name
                            st.session_state.answers = {}
                            st.session_state.duplicate_warning = None
                            st.rerun()
                        else:
                            # 単一書類の場合またはエラーの場合
                            if st.session_state.get("dev_mode"):
                                if boundaries and boundaries[0].get("error"):
                                    st.warning(f"⚠️ 境界検出エラー: {boundaries[0].get('error')}")
                                else:
                                    st.info(f"📄 単一書類として処理します（検出数: {len(boundaries)}）")
                            pass

                    finally:
                        import os as _os
                        _os.unlink(tmp_pdf_path)

                    # 単一書類だった場合、または境界検出でエラーの場合は通常処理
                    if not (len(boundaries) > 1 and not boundaries[0].get("error")):
                        uploaded_pdf.seek(0)
                        with st.spinner("解析中...（高精度モード）"):
                            files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                            params = {"estimate_useful_life_flag": "1", "use_gemini_vision": "1"}
                            response = requests.post(
                                classify_pdf_url, files=files, params=params,
                                timeout=60,
                            )
                            response.raise_for_status()
                            result_data = response.json()

                        # 重複チェック
                        if _check_duplicate(uploaded_pdf.name, 0):
                            st.session_state.duplicate_warning = uploaded_pdf.name
                        else:
                            st.session_state.duplicate_warning = None

                        if st.session_state.result:
                            st.session_state.prev_result = st.session_state.result.copy()
                        st.session_state.result = result_data
                        st.session_state.multi_doc_results = None
                        st.session_state.answers = {}
                        st.session_state.source_type = "pdf"
                        st.session_state.source_name = uploaded_pdf.name
                        _add_to_history(uploaded_pdf.name, result_data)
                        st.rerun()

                else:
                    # 通常モード（従来処理）
                    with st.spinner("解析中..." + ("（高精度モード）" if use_gemini_vision else "")):
                        files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                        params = {"estimate_useful_life_flag": "1"}
                        if use_gemini_vision:
                            params["use_gemini_vision"] = "1"
                        response = requests.post(
                            classify_pdf_url, files=files, params=params,
                            timeout=60 if use_gemini_vision else 30,
                        )
                        response.raise_for_status()
                        result_data = response.json()

                    # 重複チェック
                    if _check_duplicate(uploaded_pdf.name, 0):
                        st.session_state.duplicate_warning = uploaded_pdf.name
                    else:
                        st.session_state.duplicate_warning = None

                    if st.session_state.result:
                        st.session_state.prev_result = st.session_state.result.copy()
                    st.session_state.result = result_data
                    st.session_state.multi_doc_results = None
                    st.session_state.answers = {}
                    st.session_state.source_type = "pdf"
                    st.session_state.source_name = uploaded_pdf.name
                    _add_to_history(uploaded_pdf.name, result_data)
                    st.rerun()
            except requests.exceptions.Timeout:
                st.error("⚠️ タイムアウト。ファイルサイズが大きい場合は、ページ数を減らしてお試しください。")
            except requests.exceptions.RequestException:
                st.error("⚠️ 通信エラー。インターネット接続を確認し、再度お試しください。")
            except Exception as e:
                st.error(f"⚠️ PDFの読み取りに失敗しました。別のPDFファイルをお試しください。")

    if not uploaded_pdf and not opal_json_text:
        st.caption("👆 PDFをアップロード、または左のサイドバーでサンプルを選択")

# 結果表示用のヘルパー関数
def _render_single_result(result: Dict[str, Any], doc_info: Optional[Dict] = None, is_expander: bool = False, source_key: str = "") -> None:
    """単一書類の判定結果を表示するヘルパー関数"""
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    line_items = result.get("line_items", [])
    total_amount = sum(item.get("amount", 0) or 0 for item in line_items)

    # GUIDANCE
    if decision == "GUIDANCE":
        st.markdown("""
        <div style="background:#FEF3C7; border-left:4px solid #F59E0B; padding:0.8rem; border-radius:0.5rem;">
            <b style="color:#B45309;">⚠️ 確認が必要です</b>
        </div>
        """, unsafe_allow_html=True)
    # CAPITAL_LIKE / EXPENSE_LIKE
    else:
        if decision == "CAPITAL_LIKE":
            icon, label, color = "✅", "資産として計上", "#10B981"
        else:
            icon, label, color = "💰", "経費として処理OK", "#3B82F6"

        conf_text = "ほぼ確実" if confidence >= 0.8 else ("たぶん大丈夫" if confidence >= 0.6 else "念のため確認を")

        st.markdown(f"""
        <div style="background:{color}15; border-left:4px solid {color}; padding:0.8rem; border-radius:0.5rem;">
            <b style="color:{color};">{icon} {label}</b>
            <small style="margin-left:1rem;">確度: {conf_text}（{confidence:.0%}）</small>
        </div>
        """, unsafe_allow_html=True)

        # 資産種類・耐用年数
        useful_life = result.get("useful_life")
        if decision == "CAPITAL_LIKE" and useful_life and useful_life.get("useful_life_years", 0) > 0:
            years = useful_life.get("useful_life_years")
            category = useful_life.get("category", "")
            subcategory = useful_life.get("subcategory", "")
            if category and category != "不明":
                cat_text = f"{category}（{subcategory}）" if subcategory else category
                st.caption(f"📦 {cat_text} / 📅 {years}年で償却")

    # 税務ルール（1行）
    if total_amount > 0:
        rules = _get_applicable_tax_rules(total_amount)
        if rules:
            st.caption(f"💡 {rules[0]}")

    # 明細一覧（コンパクト） - is_expanderの場合はチェックボックスなし
    if line_items and not is_expander:
        with st.expander(f"📋 明細内訳（{len(line_items)}件）", expanded=False):
            for i, item in enumerate(line_items, 1):
                desc = item.get("description", "")
                amt = item.get("amount")
                if not desc or desc.startswith("明細("):
                    desc = "（品名なし）"
                amt_str = _format_amount(amt) if amt else ""
                st.caption(f"{i}. {desc} {amt_str}")
            if total_amount > 0:
                st.markdown(f"**合計: {_format_amount(total_amount)}**")

    # 判断理由（常に表示）
    reasons = result.get("reasons", [])
    filtered_reasons = [r for r in reasons if not r.startswith("flag:") and not r.startswith("ユーザー確認")]
    if filtered_reasons and not is_expander:
        st.markdown("**判断理由:**")
        for r in filtered_reasons[:2]:  # 最大2件
            st.caption(f"• {r}")


# 結果表示
with col_result:
    # 重複警告
    if st.session_state.duplicate_warning:
        st.warning(f"⚠️ 「{st.session_state.duplicate_warning}」は既に判定済みです（履歴に追加されました）")

    # 複数書類検出時の表示
    if st.session_state.multi_doc_results and st.session_state.source_type == "pdf_multi":
        multi_results = st.session_state.multi_doc_results
        st.markdown(f"### 📑 {len(multi_results)}件の書類を検出")
        st.caption(f"ファイル: {st.session_state.source_name}")

        for idx, doc_result in enumerate(multi_results):
            doc_info = doc_result.get("_doc_info", {})
            doc_type = doc_info.get("doc_type", "その他")
            start_page = doc_info.get("start_page", 1)
            end_page = doc_info.get("end_page", 1)
            decision = doc_result.get("decision", "UNKNOWN")

            # 判定結果のアイコン
            if decision == "CAPITAL_LIKE":
                result_icon = "✅"
            elif decision == "EXPENSE_LIKE":
                result_icon = "💰"
            else:
                result_icon = "⚠️"

            expander_title = f"{result_icon} 書類{idx + 1}: {doc_type} (p.{start_page}-{end_page})"

            with st.expander(expander_title, expanded=(idx == 0)):
                _render_single_result(doc_result, doc_info, is_expander=True)

        st.markdown("---")
        st.caption("※ 各書類をクリックして詳細を確認してください")

    elif st.session_state.result:
        result = st.session_state.result
        decision = result.get("decision", "UNKNOWN")
        confidence = result.get("confidence", 0.0)
        line_items = result.get("line_items", [])
        total_amount = sum(item.get("amount", 0) or 0 for item in line_items)

        # 判定変化の表示
        if st.session_state.prev_result and st.session_state.prev_result.get("decision") != decision:
            prev_decision = st.session_state.prev_result.get("decision")
            labels = {"CAPITAL_LIKE": "資産", "EXPENSE_LIKE": "経費", "GUIDANCE": "要確認"}
            st.success(f"🔄 判定変更: {labels.get(prev_decision, prev_decision)} → **{labels.get(decision, decision)}**")

        # GUIDANCE
        if decision == "GUIDANCE":
            st.markdown("""
            <div style="background:#FEF3C7; border-left:4px solid #F59E0B; padding:1rem; border-radius:0.5rem;">
                <b style="color:#B45309;">⚠️ 確認が必要です</b><br>
                <span style="color:#78350F;">AIだけでは判断できません。下から選んでください。</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔧 修繕・維持\n（壊れたものを直す）", use_container_width=True, key="btn_repair"):
                    st.session_state.prev_result = st.session_state.result.copy()
                    new_result = st.session_state.result.copy()
                    new_result["decision"] = "EXPENSE_LIKE"
                    new_result["confidence"] = 0.75
                    new_result["reasons"] = ["ユーザー確認: 修繕目的"]
                    st.session_state.result = new_result
                    st.rerun()
            with c2:
                if st.button("📦 新規購入・増強\n（新しく買う・増やす）", use_container_width=True, key="btn_upgrade"):
                    st.session_state.prev_result = st.session_state.result.copy()
                    new_result = st.session_state.result.copy()
                    new_result["decision"] = "CAPITAL_LIKE"
                    new_result["confidence"] = 0.75
                    new_result["reasons"] = ["ユーザー確認: 新規購入目的"]
                    st.session_state.result = new_result
                    st.rerun()

        # CAPITAL_LIKE / EXPENSE_LIKE
        else:
            if decision == "CAPITAL_LIKE":
                icon, label, color, sub = "✅", "資産として計上", "#10B981", "固定資産台帳へ登録し、毎年償却"
            else:
                icon, label, color, sub = "💰", "経費として処理OK", "#3B82F6", "今期の経費として全額処理可能"

            conf_text = "ほぼ確実" if confidence >= 0.8 else ("たぶん大丈夫" if confidence >= 0.6 else "念のため確認を")

            st.markdown(f"""
            <div style="background:{color}15; border-left:4px solid {color}; padding:1rem; border-radius:0.5rem;">
                <b style="color:{color}; font-size:1.2rem;">{icon} {label}</b><br>
                <span style="color:#6B7280;">{sub}</span><br>
                <small>判定確度: <b>{conf_text}</b>（{confidence:.0%}）</small>
            </div>
            """, unsafe_allow_html=True)

            # 資産種類・耐用年数
            useful_life = result.get("useful_life")
            if decision == "CAPITAL_LIKE" and useful_life and useful_life.get("useful_life_years", 0) > 0:
                years = useful_life.get("useful_life_years")
                category = useful_life.get("category", "")
                subcategory = useful_life.get("subcategory", "")
                if category and category != "不明":
                    cat_text = f"{category}（{subcategory}）" if subcategory else category
                    st.info(f"📦 **{cat_text}** / 📅 **{years}年**で償却")

        # 明細一覧（チェックボックス付き）
        source_key = st.session_state.source_name or "unknown"
        if line_items:
            # 選択状態を初期化
            _init_line_item_selections(source_key, line_items)
            selected_total, selected_count = _get_selected_total(source_key, line_items)

            with st.expander(f"📋 明細内訳（{len(line_items)}件）", expanded=True):
                for i, item in enumerate(line_items):
                    desc = item.get("description", "")
                    amt = item.get("amount", 0) or 0
                    classification = item.get("classification", decision)
                    if not desc or desc.startswith("明細(") or desc.startswith("明細（"):
                        desc = "（品名なし）"
                    amt_str = _format_amount(amt) if amt else ""

                    # 分類に応じたラベル
                    if classification == "CAPITAL_LIKE":
                        class_label = "資産"
                    elif classification == "EXPENSE_LIKE":
                        class_label = "経費"
                    else:
                        class_label = ""

                    # チェックボックス
                    checkbox_key = f"line_item_{source_key}_{i}"
                    is_selected = st.session_state.line_item_selections[source_key].get(i, True)

                    col_check, col_desc = st.columns([0.1, 0.9])
                    with col_check:
                        new_selection = st.checkbox(
                            "",
                            value=is_selected,
                            key=checkbox_key,
                            label_visibility="collapsed"
                        )
                        # 選択状態を更新
                        if new_selection != is_selected:
                            st.session_state.line_item_selections[source_key][i] = new_selection
                            st.rerun()
                    with col_desc:
                        if new_selection:
                            st.markdown(f"{desc} {amt_str} -> 資産")
                        else:
                            st.markdown(f"~~{desc} {amt_str}~~ -> 除外")

                st.markdown("---")
                # 選択された明細の合計
                excluded_count = len(line_items) - selected_count
                if excluded_count > 0:
                    st.markdown(f"**合計（資産計上額）: {_format_amount(selected_total)}**")
                    st.caption(f"（{selected_count}件を資産計上、{excluded_count}件を除外）")
                else:
                    st.markdown(f"**合計: {_format_amount(total_amount)}**")

            # 税務ルール（選択された合計に基づく）
            display_amount = selected_total if selected_total > 0 else total_amount
            if display_amount > 0:
                rules = _get_applicable_tax_rules(display_amount)
                if rules:
                    st.caption(f"💡 {rules[0]}")
        else:
            # 明細がない場合
            if total_amount > 0:
                rules = _get_applicable_tax_rules(total_amount)
                if rules:
                    st.caption(f"💡 {rules[0]}")

        # 判断理由（常に表示）
        reasons = result.get("reasons", [])
        filtered_reasons = [r for r in reasons if not r.startswith("flag:") and not r.startswith("ユーザー確認")]
        if filtered_reasons:
            st.markdown("**判断理由:**")
            for r in filtered_reasons[:3]:  # 最大3件
                st.caption(f"• {r}")

        # 次のアクション
        st.markdown("---")
        if decision == "CAPITAL_LIKE":
            st.markdown("**📝 次にやること:**")
            st.caption("1. 固定資産台帳に登録")
            st.caption("2. 減価償却スケジュールを作成")
        elif decision == "EXPENSE_LIKE":
            st.markdown("**📝 次にやること:**")
            st.caption("1. 経費として仕訳入力")
            st.caption("2. 領収書・請求書を保管")
        elif decision == "GUIDANCE":
            st.markdown("**📝 次にやること:**")
            st.caption("上のボタンで用途を選択してください")

        # 詳細（税理士向け）
        evidence = result.get("evidence", [])
        if evidence:
            with st.expander("🔍 詳細（税理士向け）", expanded=False):
                for r in reasons:
                    if not r.startswith("flag:"):
                        st.caption(f"• {r}")

        # 類似事例表示（履歴ベース検索 - API不要）
        if SIMILAR_CASES_AVAILABLE and HISTORY_SEARCH_AVAILABLE and st.session_state.enable_history_search:
            # 現在の判定対象の名前を取得
            current_name = ""
            if line_items and len(line_items) > 0:
                current_name = line_items[0].get("description", "")
            if current_name and not current_name.startswith("明細") and len(st.session_state.history) > 1:
                try:
                    similar = search_similar_from_history(
                        current_name,
                        st.session_state.history,
                        top_k=3,
                        threshold=0.5
                    )
                    if similar:
                        render_similar_cases(current_name, similar)
                except Exception:
                    pass  # 類似検索エラーは無視

    else:
        st.caption("👈 PDFをアップロードして判定を実行")

# フッター（免責事項）
st.markdown("---")
st.caption("""
⚠️ **ご注意**: 本ツールの判定結果は参考情報です。最終的な会計処理の判断は、
必ず顧問税理士・公認会計士にご確認ください。
""")
