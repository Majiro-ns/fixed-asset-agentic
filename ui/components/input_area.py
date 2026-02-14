# -*- coding: utf-8 -*-
"""Input area component: PDF upload, demo buttons, and classify logic."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
import streamlit as st

# PDF splitter (optional, for high-accuracy multi-doc detection)
try:
    from core.pdf_splitter import generate_thumbnail_grid_with_metadata
    from api.gemini_splitter import detect_document_boundaries
    _PDF_SPLITTER_AVAILABLE = True
except ImportError:
    _PDF_SPLITTER_AVAILABLE = False


# ---------------------------------------------------------------------------
# Skeleton loading HTML
# ---------------------------------------------------------------------------
_SKELETON_HTML = (
    '<div style="padding:1rem;">'
    '<div style="background:linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%);'
    "background-size:200% 100%;animation:_sk 1.5s infinite;"
    'height:28px;border-radius:4px;margin-bottom:12px;"></div>'
    '<div style="background:linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%);'
    "background-size:200% 100%;animation:_sk 1.5s infinite;"
    'height:56px;border-radius:4px;margin-bottom:12px;"></div>'
    '<div style="background:linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%);'
    "background-size:200% 100%;animation:_sk 1.5s infinite;"
    'height:16px;width:60%;border-radius:4px;"></div>'
    "<style>@keyframes _sk{0%{background-position:200% 0}"
    "100%{background-position:-200% 0}}</style>"
    "</div>"
)


def _skeleton_with_msg(msg: str) -> str:
    """Return skeleton HTML prefixed with a status message."""
    return (
        f'<p style="color:#888;font-size:0.9rem;margin-bottom:0.5rem;">{msg}</p>'
        + _SKELETON_HTML
    )


# ---------------------------------------------------------------------------
# Demo case helpers
# ---------------------------------------------------------------------------
_DEMO_EMOJI = {
    "server": "\U0001f4bc",   # 💼
    "pc": "\U0001f4bb",       # 💻
    "maintenance": "\U0001f527",  # 🔧
    "expense": "\U0001f527",
    "ambiguous": "\u2753",    # ❓
    "guidance": "\u2753",
}


def _get_demo_info(filename: str, demo_cases_dir: str) -> Dict[str, str]:
    """Build display label & emoji for a demo-case file."""
    desc = ""
    try:
        data = json.loads(
            (Path(demo_cases_dir) / filename).read_text(encoding="utf-8")
        )
        items = data.get("line_items", [])
        if items:
            desc = items[0].get("item_description", "")
    except Exception:
        pass

    name_lower = filename.lower()
    emoji = "\U0001f4c4"  # 📄 default
    for kw, em in _DEMO_EMOJI.items():
        if kw in name_lower:
            emoji = em
            break

    if not desc:
        desc = Path(filename).stem.replace("_", " ")

    return {"emoji": emoji, "label": desc, "filename": filename}


# ---------------------------------------------------------------------------
# History / duplicate helpers (self-contained copy of app_minimal logic)
# ---------------------------------------------------------------------------
def _check_duplicate_source(source_name: str) -> bool:
    """Return True if *source_name* already appears in the session history."""
    for entry in st.session_state.get("history", []):
        if entry.get("source") == source_name:
            return True
    return False


def _add_to_history(source_name: str, result: Dict[str, Any]) -> None:
    """Append classification *result* to the session history list."""
    if "history" not in st.session_state:
        st.session_state.history = []

    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    useful_life = result.get("useful_life") or {}
    line_items = result.get("line_items", [])

    for item in line_items:
        desc = item.get("description", "")
        if desc.startswith("明細(") or desc.startswith("\u660e\u7d30\uff08"):
            desc = ""
        st.session_state.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_name,
            "description": desc,
            "amount": item.get("amount"),
            "decision": item.get("classification", decision),
            "confidence": confidence,
            "category": useful_life.get("category", ""),
            "useful_life_years": useful_life.get("useful_life_years", ""),
        })

    if not line_items:
        st.session_state.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_name,
            "description": "",
            "amount": None,
            "decision": decision,
            "confidence": confidence,
            "category": useful_life.get("category", ""),
            "useful_life_years": useful_life.get("useful_life_years", ""),
        })


# ---------------------------------------------------------------------------
# Session-state result storage
# ---------------------------------------------------------------------------
def _save_result(
    result_data: dict,
    source_type: str,
    source_name: str,
    *,
    multi_results: list = None,
) -> None:
    """Persist classification result into session state."""
    if st.session_state.get("result"):
        st.session_state.prev_result = st.session_state.result.copy()
    st.session_state.result = result_data
    st.session_state.multi_doc_results = multi_results
    st.session_state.answers = {}
    st.session_state.source_type = source_type
    st.session_state.source_name = source_name

    if _check_duplicate_source(source_name):
        st.session_state.duplicate_warning = source_name
    else:
        st.session_state.duplicate_warning = None


# ---------------------------------------------------------------------------
# Classify: JSON (demo data)
# ---------------------------------------------------------------------------
def _run_classify_json(
    api_url: str,
    opal_json: dict,
    source_name: str,
    placeholder,
) -> None:
    """POST JSON to /classify and store the result."""
    placeholder.markdown(
        _skeleton_with_msg("\U0001f50d 判定中..."), unsafe_allow_html=True
    )
    try:
        resp = requests.post(
            f"{api_url}/classify",
            json={"opal_json": opal_json},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException:
        placeholder.empty()
        st.error("\u26a0\ufe0f 通信エラー。インターネット接続を確認し、再度お試しください。")
        return
    except Exception:
        placeholder.empty()
        st.error("\u26a0\ufe0f 判定に失敗しました。別のサンプルをお試しください。")
        return

    placeholder.empty()
    _save_result(data, "json", source_name)
    _add_to_history(source_name, data)
    st.rerun()


# ---------------------------------------------------------------------------
# Classify: single PDF
# ---------------------------------------------------------------------------
def _classify_single_pdf(
    classify_url: str,
    uploaded_pdf,
    use_vision: bool,
    placeholder,
) -> None:
    """POST a single PDF to /classify_pdf."""
    uploaded_pdf.seek(0)
    mode_label = "（高精度モード）" if use_vision else ""
    placeholder.markdown(
        _skeleton_with_msg(f"\U0001f50d 解析中...{mode_label}"),
        unsafe_allow_html=True,
    )
    files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
    params: Dict[str, str] = {"estimate_useful_life_flag": "1"}
    if use_vision:
        params["use_gemini_vision"] = "1"

    resp = requests.post(
        classify_url,
        files=files,
        params=params,
        timeout=60 if use_vision else 30,
    )
    resp.raise_for_status()
    data = resp.json()

    placeholder.empty()
    _save_result(data, "pdf", uploaded_pdf.name)
    _add_to_history(uploaded_pdf.name, data)
    st.rerun()


# ---------------------------------------------------------------------------
# Classify: PDF (with optional multi-doc detection)
# ---------------------------------------------------------------------------
def _run_classify_pdf(
    api_url: str,
    uploaded_pdf,
    use_vision: bool,
    placeholder,
) -> None:
    """Classify an uploaded PDF, optionally detecting multiple documents."""
    classify_url = f"{api_url}/classify_pdf"

    # High-accuracy + splitter → attempt multi-doc detection
    if use_vision and _PDF_SPLITTER_AVAILABLE:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_pdf.getvalue())
            tmp_pdf_path = tmp.name

        boundaries: List[dict] = []
        try:
            placeholder.markdown(
                _skeleton_with_msg("\U0001f4d1 書類構造を解析中..."),
                unsafe_allow_html=True,
            )
            grid = generate_thumbnail_grid_with_metadata(tmp_pdf_path)
            boundaries = detect_document_boundaries(
                grid["image_bytes"], grid["total_pages"]
            )
            placeholder.empty()

            # Multiple documents detected
            if len(boundaries) > 1 and not boundaries[0].get("error"):
                st.info(f"\U0001f4d1 {len(boundaries)}件の書類を検出しました")
                multi_results: List[dict] = []
                for doc in boundaries:
                    doc_label = (
                        f"書類{doc['document_id']}: {doc['doc_type']} "
                        f"(p.{doc['start_page']}-{doc['end_page']})"
                    )
                    placeholder.markdown(
                        _skeleton_with_msg(f"\U0001f50d {doc_label} を判定中..."),
                        unsafe_allow_html=True,
                    )
                    uploaded_pdf.seek(0)
                    files = {
                        "file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")
                    }
                    params = {
                        "estimate_useful_life_flag": "1",
                        "use_gemini_vision": "1",
                        "start_page": str(doc["start_page"]),
                        "end_page": str(doc["end_page"]),
                    }
                    resp = requests.post(
                        classify_url, files=files, params=params, timeout=60,
                    )
                    resp.raise_for_status()
                    doc_result = resp.json()
                    doc_result["_doc_info"] = doc
                    multi_results.append(doc_result)
                    _add_to_history(
                        f"{uploaded_pdf.name}_{doc['doc_type']}_{doc['document_id']}",
                        doc_result,
                    )

                placeholder.empty()
                _save_result(
                    multi_results[0] if multi_results else None,
                    "pdf_multi",
                    uploaded_pdf.name,
                    multi_results=multi_results,
                )
                st.rerun()
        finally:
            os.unlink(tmp_pdf_path)

        # Single document or boundary-detection error → normal classify
        if not (len(boundaries) > 1 and not boundaries[0].get("error")):
            _classify_single_pdf(classify_url, uploaded_pdf, use_vision, placeholder)
    else:
        # Normal mode (or splitter unavailable)
        _classify_single_pdf(classify_url, uploaded_pdf, use_vision, placeholder)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_input_area(
    api_url: str,
    demo_cases_dir: str,
    demo_cases: list,
) -> None:
    """Render the input area: PDF upload, demo buttons, and classify logic.

    Args:
        api_url: Base URL for the classification API.
        demo_cases_dir: Path to directory containing demo-case JSON files.
        demo_cases: Sorted list of demo-case filenames.
    """
    # ---- PDF Upload ----
    uploaded_pdf = st.file_uploader(
        "\U0001f4c4 見積書・請求書のPDFをここにドロップ",
        type=["pdf"],
        key="input_pdf_upload",
    )

    # ---- RACE-3 Fix: reset state when a different file is uploaded ----
    if uploaded_pdf:
        new_name = uploaded_pdf.name
        if st.session_state.get("uploaded_file_name") != new_name:
            st.session_state.multi_doc_results = None
            st.session_state.result = None
            st.session_state.uploaded_file_name = new_name

    # ---- PDF read-mode toggle ----
    use_high_accuracy = st.toggle(
        "\U0001f3af 高精度モード（AI Vision）",
        value=True,
        key="input_pdf_mode",
        help="Gemini Vision で高精度に読み取り（推奨）",
    )

    # Placeholder for skeleton loading animation
    skeleton = st.empty()

    # ---- Uploaded PDF → classify button ----
    if uploaded_pdf:
        if st.button(
            "\U0001f50d 判定を実行",
            type="primary",
            use_container_width=True,
            key="input_classify_btn",
        ):
            try:
                _run_classify_pdf(api_url, uploaded_pdf, use_high_accuracy, skeleton)
            except requests.exceptions.Timeout:
                skeleton.empty()
                st.error(
                    "\u26a0\ufe0f タイムアウト。"
                    "ファイルサイズが大きい場合は、ページ数を減らしてお試しください。"
                )
            except requests.exceptions.RequestException:
                skeleton.empty()
                st.error(
                    "\u26a0\ufe0f 通信エラー。"
                    "インターネット接続を確認し、再度お試しください。"
                )
            except Exception:
                skeleton.empty()
                st.error(
                    "\u26a0\ufe0f PDFの読み取りに失敗しました。"
                    "別のPDFファイルをお試しください。"
                )

    # ---- No PDF uploaded: show guidance ----
    else:
        st.markdown(
            "📄 **請求書・見積書・領収書のPDFをアップロードしてください。**\n\n"
            "対応形式: PDF（テキスト埋め込み型推奨）"
        )
