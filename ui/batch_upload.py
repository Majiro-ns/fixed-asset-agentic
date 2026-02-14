#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch upload UI for fixed asset classification.
複数PDFを一括でアップロードし、判定結果をテーブル表示する。
"""
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
import pandas as pd


def _get_decision_display(decision: Optional[str]) -> str:
    """判定結果を表示用に変換"""
    if decision == "CAPITAL_LIKE":
        return "資産"
    elif decision == "EXPENSE_LIKE":
        return "経費"
    elif decision == "GUIDANCE":
        return "要確認"
    elif decision == "UNKNOWN":
        return "不明"
    return decision or "-"


def _get_decision_icon(decision: Optional[str]) -> str:
    """判定結果のアイコンを取得"""
    if decision == "CAPITAL_LIKE":
        return "✅"
    elif decision == "EXPENSE_LIKE":
        return "💰"
    elif decision == "GUIDANCE":
        return "⚠️"
    return "❓"


def _format_confidence(confidence: Optional[float]) -> str:
    """確信度をパーセント表示"""
    if confidence is None:
        return "-"
    return f"{confidence:.0%}"


def render_batch_upload(api_url: str) -> None:
    """
    一括アップロードUIをレンダリング

    - 複数PDF選択
    - 判定実行ボタン
    - 結果テーブル表示

    Args:
        api_url: APIのベースURL（例: https://example.com）
    """
    st.markdown("## 📁 一括アップロード")
    st.caption("複数のPDFファイルをまとめて判定できます")

    # ファイルアップローダー（複数選択可）
    uploaded_files = st.file_uploader(
        "PDFファイルを選択（複数可・ドラッグ&ドロップ対応）",
        type=["pdf"],
        accept_multiple_files=True,
        key="batch_pdf_upload",
        help="Ctrlキーを押しながらクリックで複数選択できます",
    )

    # 選択されたファイル数を表示
    if uploaded_files:
        st.info(f"📄 {len(uploaded_files)}件のファイルが選択されています")

    # セッション状態の初期化
    if "batch_results" not in st.session_state:
        st.session_state.batch_results = None
    if "batch_processing" not in st.session_state:
        st.session_state.batch_processing = False

    # 一括判定ボタン
    col1, col2 = st.columns([2, 1])
    with col1:
        execute_button = st.button(
            "🔍 一括判定を実行",
            type="primary",
            use_container_width=True,
            disabled=not uploaded_files or st.session_state.batch_processing,
        )
    with col2:
        if st.session_state.batch_results:
            if st.button("🗑️ 結果をクリア", use_container_width=True):
                st.session_state.batch_results = None
                st.rerun()

    # 一括判定の実行
    if execute_button and uploaded_files:
        st.session_state.batch_processing = True
        st.session_state.batch_results = None

        # 進捗表示用のプレースホルダー
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        try:
            # APIエンドポイント
            batch_url = f"{api_url}/classify_batch"

            # ファイルをAPIに送信
            files_to_send = []
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)  # ファイルポインタをリセット
                files_to_send.append(
                    ("files", (uploaded_file.name, uploaded_file, "application/pdf"))
                )

            total_files = len(uploaded_files)

            # 進捗表示（API呼び出し前）
            progress_placeholder.progress(0.0, text=f"処理中... (0/{total_files})")
            status_placeholder.info("📤 ファイルをアップロードしています...")

            # API呼び出し（一括）
            # タイムアウトは1ファイル30秒を想定
            timeout = max(60, total_files * 30)

            response = requests.post(
                batch_url,
                files=files_to_send,
                params={"estimate_useful_life_flag": "1"},
                timeout=timeout,
            )

            # 進捗更新（API呼び出し完了）
            progress_placeholder.progress(1.0, text=f"処理完了 ({total_files}/{total_files})")
            status_placeholder.empty()

            if response.status_code == 200:
                result_data = response.json()
                st.session_state.batch_results = result_data
            elif response.status_code == 400:
                error_detail = response.json().get("detail", {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get("message", "エラーが発生しました")
                else:
                    error_msg = str(error_detail)
                st.error(f"⚠️ {error_msg}")
            else:
                st.error(f"⚠️ APIエラー（ステータス: {response.status_code}）")

        except requests.exceptions.Timeout:
            st.error("⚠️ タイムアウトしました。ファイル数を減らしてお試しください。")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ サーバーに接続できません。インターネット接続を確認してください。")
        except Exception as e:
            st.error(f"⚠️ エラーが発生しました: {str(e)}")
        finally:
            st.session_state.batch_processing = False
            progress_placeholder.empty()
            st.rerun()

    # 結果表示
    if st.session_state.batch_results:
        results = st.session_state.batch_results

        # サマリー表示
        st.markdown("---")
        col_total, col_success, col_failed = st.columns(3)
        with col_total:
            st.metric("合計", f"{results['total']}件")
        with col_success:
            st.metric("成功", f"{results['success']}件", delta=None)
        with col_failed:
            failed = results['failed']
            st.metric(
                "失敗",
                f"{failed}件",
                delta=f"-{failed}" if failed > 0 else None,
                delta_color="inverse" if failed > 0 else "off",
            )

        st.markdown("---")
        st.markdown("### 📋 結果一覧")

        # 結果をDataFrame形式に変換
        table_data = []
        for item in results.get("results", []):
            if item["success"]:
                decision = item.get("decision")
                icon = _get_decision_icon(decision)
                decision_display = f"{icon} {_get_decision_display(decision)}"
                confidence = _format_confidence(item.get("confidence"))
                reasons = item.get("reasons", [])
                reason_text = reasons[0] if reasons else "-"
                status = "✅"
            else:
                decision_display = "-"
                confidence = "-"
                reason_text = item.get("error", "不明なエラー")
                status = "❌"

            table_data.append({
                "状態": status,
                "ファイル名": item["filename"],
                "判定結果": decision_display,
                "確信度": confidence,
                "備考": reason_text[:50] + "..." if len(reason_text) > 50 else reason_text,
            })

        # DataFrameで表示
        df = pd.DataFrame(table_data)

        # スタイル適用（エラー行を強調）
        def highlight_errors(row):
            if row["状態"] == "❌":
                return ["background-color: #FEE2E2"] * len(row)
            return [""] * len(row)

        styled_df = df.style.apply(highlight_errors, axis=1)

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "状態": st.column_config.TextColumn("状態", width="small"),
                "ファイル名": st.column_config.TextColumn("ファイル名", width="medium"),
                "判定結果": st.column_config.TextColumn("判定結果", width="small"),
                "確信度": st.column_config.TextColumn("確信度", width="small"),
                "備考": st.column_config.TextColumn("備考", width="large"),
            },
        )

        # 詳細表示（expanderで各ファイルの詳細）
        with st.expander("📝 詳細情報を表示"):
            for i, item in enumerate(results.get("results", [])):
                filename = item["filename"]
                if item["success"]:
                    decision = item.get("decision")
                    icon = _get_decision_icon(decision)
                    st.markdown(f"**{i+1}. {filename}** - {icon} {_get_decision_display(decision)}")
                    reasons = item.get("reasons", [])
                    if reasons:
                        for reason in reasons:
                            st.caption(f"  • {reason}")
                else:
                    st.markdown(f"**{i+1}. {filename}** - ❌ エラー")
                    st.error(f"  {item.get('error', '不明なエラー')}")
                st.markdown("---")

        # CSVダウンロード
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 結果をCSVでダウンロード",
            data=csv_data,
            file_name="batch_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    elif not uploaded_files:
        # ファイル未選択時のガイド
        st.markdown("---")
        st.markdown("""
        <div style="
            border: 2px dashed #CBD5E1;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            color: #64748B;
        ">
            <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">
                📁 PDFファイルをドラッグ&ドロップ
            </p>
            <p style="font-size: 0.9rem;">
                または上の「Browse files」ボタンをクリック
            </p>
        </div>
        """, unsafe_allow_html=True)


# スタンドアロンでテスト実行する場合
if __name__ == "__main__":
    import os

    # ページ設定
    st.set_page_config(
        page_title="一括アップロード - 固定資産判定",
        page_icon="📁",
        layout="wide",
    )

    # API URL（環境変数から取得、デフォルトはlocalhost）
    api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    # 一括アップロードUIをレンダリング
    render_batch_upload(api_url)
