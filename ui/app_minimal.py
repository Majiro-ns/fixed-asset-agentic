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

# UI コンポーネント（オプショナル）
try:
    from ui.styles import inject_custom_css
    from ui.components.result_card import render_result_card
    from ui.components.guidance_panel import render_guidance_panel
    from ui.components.hero_section import render_hero
    from ui.components.input_area import render_input_area
    from ui.components.diff_display import render_diff_display
    _COMPONENTS_AVAILABLE = True
except ImportError:
    _COMPONENTS_AVAILABLE = False

# API URL (環境変数で上書き可能)
DEFAULT_API_URL = os.environ.get(
    "CLOUD_RUN_API_URL",
    "https://fixed-asset-agentic-api-{project}.asia-northeast1.run.app".format(
        project=os.environ.get("GOOGLE_CLOUD_PROJECT_NUMBER", "")
    ),
)
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
    # RACE-1 fix: source_nameが変わった場合、古いキーをクリアして再初期化
    prev_source = st.session_state.get("_line_item_source")
    if prev_source and prev_source != source_name:
        st.session_state.line_item_selections.pop(prev_source, None)
    st.session_state._line_item_source = source_name
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

# デモデータディレクトリ（サイドバー・メイン共通）
demo_cases_dir = ROOT_DIR / "data" / "demo"
demo_cases = []
if demo_cases_dir.exists():
    demo_cases = sorted([f.name for f in demo_cases_dir.glob("*.json")])

# サイドバー（整理済み: 履歴・ヘルプ・セキュリティのみ。開発者向けは?dev=1で表示）
with st.sidebar:
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
- **⚠️ 確認が必要です**: 税理士に相談
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

    # 開発者向け・台帳インポート: ?dev=1 URLパラメータでのみ表示
    if st.query_params.get("dev") == "1":
        st.markdown("---")
        st.markdown("### 🔧 開発者向け")
        st.session_state.dev_mode = st.toggle(
            "デバッグ表示",
            value=st.session_state.get("dev_mode", False),
            help="詳細なデバッグ情報を表示します"
        )

        # 類似検索スイッチ
        if HISTORY_SEARCH_AVAILABLE:
            st.session_state.enable_history_search = st.toggle(
                "📚 過去履歴から類似検索",
                value=st.session_state.enable_history_search,
                help="ONにすると、過去の判定履歴から類似事例を表示します"
            )

        # 台帳インポート機能
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
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(ledger_file.name).suffix) as tmp:
                            tmp.write(ledger_file.getvalue())
                            tmp_path = tmp.name
                        result = import_ledger_safe(tmp_path)
                        os.unlink(tmp_path)

                        if result["success"]:
                            st.session_state.ledger_data = result["data"]
                            st.success(f"✅ {len(result['data'])}件読み込み完了")
                            if EMBEDDING_AVAILABLE and len(result["data"]) > 0:
                                try:
                                    store = EmbeddingStore()
                                    added = store.add_items(result["data"])
                                    st.session_state.embedding_store = store
                                    st.caption(f"類似検索用に{added}件を学習")
                                except Exception:
                                    st.caption("類似検索は利用不可（APIキー未設定）")
                        else:
                            st.error(f"読み込みエラー: {result['error']}")

            if len(st.session_state.ledger_data) > 0:
                st.caption(f"学習済み: {len(st.session_state.ledger_data)}件")

# サンプル切り替え時にセッションリセット（RACE-2 fix: 全関連キーを一括リセット）
if "demo_selector" in st.session_state:
    current_demo = st.session_state.get("demo_selector")
    if current_demo != st.session_state.last_demo:
        st.session_state.result = None
        st.session_state.prev_result = None
        st.session_state.answers = {}
        st.session_state.last_demo = current_demo
        st.session_state.duplicate_warning = None
        st.session_state.multi_doc_results = None
        st.session_state.source_type = None
        st.session_state.source_name = None
        st.session_state.line_item_selections = {}

# 結果表示用のヘルパー関数（フォールバック用）
def _render_single_result(result: Dict[str, Any], doc_info: Optional[Dict] = None, is_expander: bool = False, source_key: str = "") -> None:
    """単一書類の判定結果を表示するヘルパー関数"""
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    line_items = result.get("line_items", [])
    total_amount = sum(item.get("amount", 0) or 0 for item in line_items)
    if decision == "GUIDANCE":
        st.markdown(
            '<div style="background:#FEF3C7; border-left:4px solid #F59E0B; padding:0.8rem; border-radius:0.5rem;">'
            '<b style="color:#B45309;">⚠️ 確認が必要です</b>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        if decision == "CAPITAL_LIKE":
            icon, label, color = "✅", "資産として計上", "#10B981"
        else:
            icon, label, color = "💰", "経費として処理OK", "#3B82F6"
        conf_text = "ほぼ確実" if confidence >= 0.8 else ("たぶん大丈夫" if confidence >= 0.6 else "念のため確認を")
        st.markdown(
            f'<div style="background:{color}15; border-left:4px solid {color}; padding:0.8rem; border-radius:0.5rem;">'
            f'<b style="color:{color};">{icon} {label}</b>'
            f'<small style="margin-left:1rem;">確度: {conf_text}（{confidence:.0%}）</small>'
            f'</div>',
            unsafe_allow_html=True,
        )
        useful_life = result.get("useful_life")
        if decision == "CAPITAL_LIKE" and useful_life and useful_life.get("useful_life_years", 0) > 0:
            years = useful_life.get("useful_life_years")
            category = useful_life.get("category", "")
            subcategory = useful_life.get("subcategory", "")
            if category and category != "不明":
                cat_text = f"{category}（{subcategory}）" if subcategory else category
                st.caption(f"📦 {cat_text} / 📅 {years}年で償却")
    if total_amount > 0:
        rules = _get_applicable_tax_rules(total_amount)
        if rules:
            st.caption(f"💡 {rules[0]}")
    if line_items and not is_expander:
        _CLS_ICONS = {"CAPITAL_LIKE": "✅", "EXPENSE_LIKE": "💰", "GUIDANCE": "⚠️"}
        with st.expander(f"📋 明細内訳（{len(line_items)}件）", expanded=False):
            for i, item in enumerate(line_items, 1):
                desc = item.get("description", "")
                amt = item.get("amount")
                cls = item.get("classification", "")
                if not desc or desc.startswith("明細("):
                    desc = "（品名なし）"
                amt_str = _format_amount(amt) if amt else ""
                icon = _CLS_ICONS.get(cls, "")
                st.caption(f"{icon} {i}. {desc} {amt_str}")
            if total_amount > 0:
                st.markdown(f"**合計: {_format_amount(total_amount)}**")
    reasons = result.get("reasons", [])
    filtered_reasons = [r for r in reasons if not r.startswith("flag:") and not r.startswith("ユーザー確認")]
    if filtered_reasons and not is_expander:
        st.markdown("**判断理由:**")
        for r in filtered_reasons[:2]:
            st.caption(f"• {r}")


def _render_line_items_and_actions(result: dict, decision: str, show_reasons: bool = True) -> None:
    """明細チェックボックス、次のアクション、詳細、類似事例を表示（共通ヘルパー）"""
    line_items = result.get("line_items", [])
    total_amount = sum(item.get("amount", 0) or 0 for item in line_items)
    source_key = st.session_state.source_name or "unknown"

    if line_items:
        # 明細ごとの分類色: 緑=資産、青=経費、黄=GUIDANCE
        _CLS_STYLE = {
            "CAPITAL_LIKE": {"icon": "✅", "color": "#10B981", "bg": "#ECFDF5", "label": "資産"},
            "EXPENSE_LIKE": {"icon": "💰", "color": "#3B82F6", "bg": "#EFF6FF", "label": "経費"},
            "GUIDANCE":     {"icon": "⚠️", "color": "#F59E0B", "bg": "#FEF3C7", "label": "要確認"},
        }

        # 取得価額（CAPITAL_LIKE合計）
        acq_cost = sum(
            (it.get("amount") or 0) for it in line_items
            if isinstance(it, dict) and it.get("classification") == "CAPITAL_LIKE"
        )
        exp_cost = sum(
            (it.get("amount") or 0) for it in line_items
            if isinstance(it, dict) and it.get("classification") == "EXPENSE_LIKE"
        )

        with st.expander(f"📋 明細内訳（{len(line_items)}件）", expanded=True):
            for i, item in enumerate(line_items):
                desc = item.get("description", "")
                amt = item.get("amount", 0) or 0
                cls = item.get("classification", "GUIDANCE")
                reason = item.get("reason", "")
                if not desc or desc.startswith("明細(") or desc.startswith("明細（"):
                    desc = "（品名なし）"
                amt_str = _format_amount(amt) if amt else ""
                style = _CLS_STYLE.get(cls, _CLS_STYLE["GUIDANCE"])
                # AI参考判定（GUIDANCE明細のみ）
                ai_hint_html = ""
                ai_hint = item.get("ai_hint")
                if cls == "GUIDANCE" and ai_hint and ai_hint.get("suggestion"):
                    hint_cls = ai_hint["suggestion"]
                    hint_label = ai_hint.get("suggestion_label", hint_cls)
                    hint_conf = ai_hint.get("confidence", 0)
                    hint_reason = ai_hint.get("reasoning", "")
                    hint_icon = {"CAPITAL_LIKE": "\u2705", "EXPENSE_LIKE": "\U0001f4b0"}.get(hint_cls, "\u2753")
                    ai_hint_html = (
                        f'<div style="background:#E3F2FD;border-left:2px solid #1976D2;'
                        f'padding:0.2rem 0.5rem;margin-top:0.2rem;border-radius:0.2rem;">'
                        f'<small style="color:#0D47A1;">'
                        f'\U0001f916 <b>AI\u53c2\u8003\u5224\u5b9a</b>: {hint_icon} {hint_label}'
                        f' (\u4fe1\u5ea6 {hint_conf:.0%})'
                        f'{" \u2014 " + hint_reason if hint_reason else ""}'
                        f'</small></div>'
                    )
                st.markdown(
                    f'<div style="background:{style["bg"]};border-left:3px solid {style["color"]};'
                    f'padding:0.4rem 0.6rem;margin-bottom:0.3rem;border-radius:0.3rem;">'
                    f'<span style="color:{style["color"]};font-weight:bold;">{style["icon"]} {style["label"]}</span>'
                    f' &nbsp; {desc} &nbsp; <b>{amt_str}</b>'
                    f'{"<br><small style=color:#666>" + reason + "</small>" if reason else ""}'
                    f'{ai_hint_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("---")
            # 取得価額・経費額の表示
            if acq_cost > 0:
                st.markdown(f"**📦 取得価額（資産計上額）: {_format_amount(acq_cost)}**")
            if exp_cost > 0:
                st.caption(f"💰 経費合計: {_format_amount(exp_cost)}")
            if total_amount > 0 and (acq_cost > 0 or exp_cost > 0):
                remaining = total_amount - acq_cost - exp_cost
                if remaining > 0:
                    st.caption(f"⚠️ 要確認: {_format_amount(remaining)}")
            elif total_amount > 0:
                st.markdown(f"**合計: {_format_amount(total_amount)}**")

        display_amount = acq_cost if acq_cost > 0 else total_amount
        if display_amount > 0:
            rules = _get_applicable_tax_rules(display_amount)
            if rules:
                st.caption(f"💡 {rules[0]}")
    else:
        if total_amount > 0:
            rules = _get_applicable_tax_rules(total_amount)
            if rules:
                st.caption(f"💡 {rules[0]}")

    # 判断理由
    reasons = result.get("reasons", [])
    if show_reasons:
        filtered_reasons = [r for r in reasons if not r.startswith("flag:") and not r.startswith("ユーザー確認")]
        if filtered_reasons:
            st.markdown("**判断理由:**")
            for r in filtered_reasons[:3]:
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

    # 詳細（開発者向け）: ?dev=1 パラメータがある場合のみ表示
    if st.query_params.get("dev") == "1":
        evidence = result.get("evidence", [])
        if evidence:
            with st.expander("開発者向け詳細", expanded=False):
                for r in reasons:
                    if not r.startswith("flag:"):
                        st.caption(f"• {r}")

    # 類似事例表示（履歴ベース検索）
    if SIMILAR_CASES_AVAILABLE and HISTORY_SEARCH_AVAILABLE and st.session_state.enable_history_search:
        current_name = ""
        if line_items and len(line_items) > 0:
            current_name = line_items[0].get("description", "")
        if current_name and not current_name.startswith("明細") and len(st.session_state.history) > 1:
            try:
                similar = search_similar_from_history(
                    current_name, st.session_state.history, top_k=3, threshold=0.5
                )
                if similar:
                    render_similar_cases(current_name, similar)
            except Exception:
                pass


def _handle_guidance_choice(choice: str) -> None:
    """GUIDANCE選択結果を処理してsession_stateを更新"""
    if choice == "repair":
        st.session_state.prev_result = st.session_state.result.copy()
        new_result = st.session_state.result.copy()
        new_result["decision"] = "EXPENSE_LIKE"
        new_result["confidence"] = 0.75
        new_result["reasons"] = ["ユーザー確認: 修繕目的"]
        st.session_state.result = new_result
        st.rerun()
    elif choice == "upgrade":
        st.session_state.prev_result = st.session_state.result.copy()
        new_result = st.session_state.result.copy()
        new_result["decision"] = "CAPITAL_LIKE"
        new_result["confidence"] = 0.75
        new_result["reasons"] = ["ユーザー確認: 新規購入目的"]
        st.session_state.result = new_result
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# メイン画面
# ═══════════════════════════════════════════════════════════════
service_url = API_URL

if _COMPONENTS_AVAILABLE:
    # === 新コンポーネントベースレイアウト（1カラム） ===
    inject_custom_css()
    render_hero()
    st.info("📤 アップロードされたPDFの内容は、判定のためにGoogle Gemini APIに送信されます。機密性の高い書類の場合はご注意ください。")
    render_input_area(service_url, str(demo_cases_dir), demo_cases)

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
            doc_decision = doc_result.get("decision", "UNKNOWN")
            if doc_decision == "CAPITAL_LIKE":
                result_icon = "✅"
            elif doc_decision == "EXPENSE_LIKE":
                result_icon = "💰"
            else:
                result_icon = "⚠️"
            expander_title = f"{result_icon} 書類{idx + 1}: {doc_type} (p.{start_page}-{end_page})"
            with st.expander(expander_title, expanded=(idx == 0)):
                render_result_card(doc_result)
        st.markdown("---")
        st.caption("※ 各書類をクリックして詳細を確認してください")

    elif st.session_state.result:
        result = st.session_state.result
        decision = result.get("decision", "UNKNOWN")

        # 判定変化表示
        if st.session_state.prev_result and st.session_state.prev_result.get("decision") != decision:
            render_diff_display(st.session_state.prev_result, result)

        # GUIDANCE
        if decision == "GUIDANCE":
            choice = render_guidance_panel(result)
            _handle_guidance_choice(choice)
        # CAPITAL_LIKE / EXPENSE_LIKE
        else:
            render_result_card(result)

        # 明細・アクション・類似事例（理由はrender_result_cardで表示済みのため非表示）
        _render_line_items_and_actions(result, decision, show_reasons=False)

    # フッター（免責事項 - 小型化）
    st.markdown("---")
    st.markdown(
        '<p class="disclaimer">'
        "本ツールの判定結果は参考情報です。最終的な会計処理の判断は、"
        "必ず顧問税理士・公認会計士にご確認ください。"
        "</p>",
        unsafe_allow_html=True,
    )

else:
    # === フォールバック: 既存2カラムレイアウト（コンポーネント未導入時） ===
    st.markdown("## 📊 固定資産判定")

    col_input, col_result = st.columns([1, 1])

    with col_input:
        # LLMデータ送信の情報開示
        st.info("📤 アップロードされたPDFの内容は、判定のためにGoogle Gemini APIに送信されます。機密性の高い書類の場合はご注意ください。")
        # PDFアップロード
        _fb_pdf = st.file_uploader(
            "見積書・請求書（PDF）をアップロード",
            type=["pdf"],
            key="pdf_upload",
        )

        # PDF判定ボタン
        if _fb_pdf:
            if st.button("🔍 PDFを判定", type="primary", use_container_width=True):
                try:
                    _fb_url = f"{service_url}/classify_pdf"
                    _fb_pdf.seek(0)
                    _fb_files = {"file": (_fb_pdf.name, _fb_pdf, "application/pdf")}
                    _fb_params = {"estimate_useful_life_flag": "1"}
                    with st.spinner("解析中..."):
                        _fb_resp = requests.post(_fb_url, files=_fb_files, params=_fb_params, timeout=30)
                        _fb_resp.raise_for_status()
                        _fb_data = _fb_resp.json()
                    if _check_duplicate(_fb_pdf.name, 0):
                        st.session_state.duplicate_warning = _fb_pdf.name
                    else:
                        st.session_state.duplicate_warning = None
                    if st.session_state.result:
                        st.session_state.prev_result = st.session_state.result.copy()
                    st.session_state.result = _fb_data
                    st.session_state.multi_doc_results = None
                    st.session_state.answers = {}
                    st.session_state.source_type = "pdf"
                    st.session_state.source_name = _fb_pdf.name
                    _add_to_history(_fb_pdf.name, _fb_data)
                    st.rerun()
                except requests.exceptions.Timeout:
                    st.error("⚠️ タイムアウト。ファイルサイズが大きい場合は、ページ数を減らしてお試しください。")
                except requests.exceptions.RequestException:
                    st.error("⚠️ 通信エラー。インターネット接続を確認し、再度お試しください。")
                except Exception:
                    st.error("⚠️ PDFの読み取りに失敗しました。別のPDFファイルをお試しください。")
        else:
            st.caption("👆 PDFをアップロードして判定を実行")

    with col_result:
        # 重複警告
        if st.session_state.duplicate_warning:
            st.warning(f"⚠️ 「{st.session_state.duplicate_warning}」は既に判定済みです（履歴に追加されました）")

        # 複数書類検出時の表示
        if st.session_state.multi_doc_results and st.session_state.source_type == "pdf_multi":
            _fb_multi = st.session_state.multi_doc_results
            st.markdown(f"### 📑 {len(_fb_multi)}件の書類を検出")
            st.caption(f"ファイル: {st.session_state.source_name}")
            for _fb_idx, _fb_doc in enumerate(_fb_multi):
                _fb_dinfo = _fb_doc.get("_doc_info", {})
                _fb_dtype = _fb_dinfo.get("doc_type", "その他")
                _fb_sp = _fb_dinfo.get("start_page", 1)
                _fb_ep = _fb_dinfo.get("end_page", 1)
                _fb_dd = _fb_doc.get("decision", "UNKNOWN")
                _fb_icon = "✅" if _fb_dd == "CAPITAL_LIKE" else ("💰" if _fb_dd == "EXPENSE_LIKE" else "⚠️")
                with st.expander(f"{_fb_icon} 書類{_fb_idx + 1}: {_fb_dtype} (p.{_fb_sp}-{_fb_ep})", expanded=(_fb_idx == 0)):
                    _render_single_result(_fb_doc, _fb_dinfo, is_expander=True)
            st.caption("※ 各書類をクリックして詳細を確認してください")

        elif st.session_state.result:
            _fb_result = st.session_state.result
            _fb_decision = _fb_result.get("decision", "UNKNOWN")

            # 判定変化の表示
            if st.session_state.prev_result and st.session_state.prev_result.get("decision") != _fb_decision:
                _fb_prev = st.session_state.prev_result.get("decision")
                _fb_labels = {"CAPITAL_LIKE": "資産", "EXPENSE_LIKE": "経費", "GUIDANCE": "確認が必要です"}
                st.success(f"🔄 判定変更: {_fb_labels.get(_fb_prev, _fb_prev)} → **{_fb_labels.get(_fb_decision, _fb_decision)}**")

            # GUIDANCE表示
            if _fb_decision == "GUIDANCE":
                st.markdown(
                    '<div style="background:#FEF3C7; border-left:4px solid #F59E0B; padding:1rem; border-radius:0.5rem;">'
                    '<b style="color:#B45309;">⚠️ 確認が必要です</b><br>'
                    '<span style="color:#78350F;">AIだけでは判断できません。下から選んでください。</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("")
                _fb_c1, _fb_c2 = st.columns(2)
                with _fb_c1:
                    if st.button("🔧 修繕・維持\n（壊れたものを直す）", use_container_width=True, key="btn_repair"):
                        _handle_guidance_choice("repair")
                with _fb_c2:
                    if st.button("📦 新規購入・増強\n（新しく買う・増やす）", use_container_width=True, key="btn_upgrade"):
                        _handle_guidance_choice("upgrade")
            else:
                _render_single_result(_fb_result)

            # 明細・アクション・類似事例
            _render_line_items_and_actions(_fb_result, _fb_decision)

    # フッター（免責事項）
    st.markdown("---")
    st.caption("⚠️ **ご注意**: 本ツールの判定結果は参考情報です。最終的な会計処理の判断は、"
               "必ず顧問税理士・公認会計士にご確認ください。")
