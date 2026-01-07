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

APP_TITLE = "���Ϗ� �Œ莑�Y����iOpal���o �~ Agentic����j"
APP_SUB = "Opal�����o / Agent������iStop�݌v�j"
TAGLINE = "�����s�͎~�߂�B�l������ׂ��s�����c���B"

VALUE_STATEMENT = "AI�������s�ł͎��������~�߁A�o�����m�F���ׂ��s�����𕂂��яオ�点�܂��B"
VALUE_BULLETS = [
    "��������Y�v��^��p�����̎��̂������",
    "���f�����iflags�j���c���A�ォ�猟�؂ł���",
    "AI�ɐӔC�������t�����A�ӔC���E��݌v����",
]

STEP1 = "Step1�bOpal�Œ��o�i�h���JSON�j"
STEP2 = "Step2�bAdapter���K���i�����X�L�[�} v1.0�j"
STEP3 = "Step3�bClassifier����i3�l�E�f�肵�Ȃ��j"

STOP_NOTE = "�v�m�F�͐��x�s���ł͂Ȃ��A���f��~�iStop�݌v�j�ł��B"
STEP_LABELS = ["Step1 ���o", "Step2 ���K��", "Step3 ����"]

SAMPLE_DIR = ROOT_DIR / "data" / "opal_outputs"
POLICY_OPTIONS = {
    "None�i�f�t�H���g�j": None,
    "company_default�idemo�j": ROOT_DIR / "policies" / "company_default.json",
}


def _read_json_file(path: Path) -> Dict[str, Any]:
    txt = path.read_text(encoding="utf-8-sig")
    return json.loads(txt)


def _safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _truncate(s: str, n: int = 30) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + "�c"


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
        flags_str = f"flags: {flags_str_raw}" if flags_str_raw else ""
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
            prefix = "[�v�m�F] "
            if not label_ja.startswith(prefix):
                label_ja = prefix + label_ja
            if not desc.startswith(prefix):
                desc = prefix + desc

        rows.append(
            {
                "priority": "�v�m�F" if str(cls).upper() == "GUIDANCE" else "",
                "line_no": it.get("line_no"),
                "description": desc,
                "amount_display": amount_display,
                "label_ja": label_ja,
                "classification": cls,
                "rationale_ja": rationale_ja,
                "flags": flags_str,
                "evidence": evidence_short,
            }
        )
    return rows


def _render_dataframe(rows: List[Dict[str, Any]]) -> None:
    if rows:
        ordered_rows: List[Dict[str, Any]] = []
        preferred = ["description", "amount_display", "classification", "rationale_ja", "flags", "evidence"]
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
        "amount_display": st.column_config.TextColumn("���z", help="�\���p�iJPY�J���}��؂�j"),
    }
    try:
        st.dataframe(ordered_rows, hide_index=True, use_container_width=True, column_config=column_config)
    except TypeError:
        st.dataframe(ordered_rows, use_container_width=True, column_config=column_config)


def _sort_rows_for_review(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    order = {"GUIDANCE": 0, "CAPITAL_LIKE": 1, "EXPENSE_LIKE": 2}
    return sorted(rows, key=lambda r: order.get(str(r.get("classification", "")).upper(), 9))


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
            s = "��ƃ|���V�["
        elif s.startswith("mixed_keyword:"):
            s = "�L�[���[�h"
        elif s.startswith("regex:"):
            s = "���K�\��"
        humanized.append(s)
        if len(humanized) >= 3:
            break
    return "�^".join(humanized)


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
        "�X�e�b�v��I��",
        options=list(range(3)),
        format_func=lambda i: step_labels[i],
        index=current,
        horizontal=True,
    )
    if nav_step != current:
        _go(nav_step)
        current = nav_step

    st.progress(current / 2)
    st.caption(f"���݁F{STEP_LABELS[current]}�iStep1��Step2��Step3�j")

    if st.session_state.step == 0:
        st.success(VALUE_STATEMENT)
        st.markdown("### ���̃c�[���łł��邱��")
        for b in VALUE_BULLETS:
            st.write(f"�E{b}")

        with st.expander("�i�ߕ��i3�X�e�b�v�j", expanded=True):
            st.write(STEP1)
            st.write(STEP2)
            st.write(STEP3)

        st.markdown("## Step1�b���́iOpal���oJSON�j")
        st.caption("Opal��OCR�E���ڒ��o�܂ł�S�����܂��B�����ŃT���v���I���܂���JSON�\�t���s���܂��B")

        colA, colB = st.columns([1, 1], gap="large")

        with colA:
            st.markdown("### �T���v���I��")
            samples: List[str] = []
            if SAMPLE_DIR.exists():
                samples = sorted([p.name for p in SAMPLE_DIR.glob("*.json")])
            sample_name = st.selectbox("Select a sample", options=(["(none)"] + samples), index=1 if len(samples) else 0)

            sample_data = None
            if sample_name and sample_name != "(none)":
                try:
                    sample_data = _read_json_file(SAMPLE_DIR / sample_name)
                except Exception as e:
                    st.error(f"�T���v���ǂݍ��݂Ɏ��s���܂���: {e}")

        with colB:
            st.markdown("### �e�L�X�g�\�t")
            pasted = st.text_area(
                "Opal JSON ��\��t���i�T���v���I��������ꍇ�͕s�v�j",
                height=260,
                placeholder='��: {"vendor": null, "invoice_date": "...", "line_items": [...]}',
            )

        opal_dict: Optional[Dict[str, Any]] = None
        if sample_data is not None:
            opal_dict = sample_data
        elif pasted.strip():
            try:
                opal_dict = json.loads(pasted)
            except Exception as e:
                st.error(f"JSON�̃p�[�X�Ɏ��s���܂���: {e}")

        st.divider()

        left, right = st.columns([1, 1])
        with left:
            st.caption("��������s����Ǝ�����Step3�֐i�݂܂��BStep2�̓i�r�Ŋm�F�ł��܂��B")
        with right:
            run_disabled = opal_dict is None
            st.caption(f"Policy: {policy_display}")

            if st.button("��������s���Đi��", type="primary", use_container_width=True, disabled=run_disabled):
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
                    st.error(f"�����Ɏ��s���܂���: {e}")

        with st.expander("����JSON�v���r���[�i�C�Ӂj", expanded=False):
            if opal_dict is None:
                st.caption("�T���v���I���܂��͓\�t���s���ƃv���r���[�ł��܂��B")
            else:
                st.code(_safe_json_dumps(opal_dict), language="json")

        return

    if st.session_state.step == 1:
        st.markdown("## Step2�b���K���iAdapter���ʁj")
        st.caption("Opal���o���Œ�X�L�[�}�ɐ��K���������e���m�F���܂��B���֐i�ނƔ��茋�ʂ������܂��B")
        st.caption(f"Policy: {st.session_state.policy_display}")
        adapted = st.session_state.adapted_doc

        if adapted is None:
            st.warning("Step1�ŃT���v���I���܂��͓\�t���s���A����{�^���������Ă��������B")
        else:
            st.info("Adapter�o�́i��v�t�B�[���h�̂ݔ����j�B")
            st.code(_safe_json_dumps(adapted), language="json")

        st.divider()
        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("�߂�iStep1 ���́j", use_container_width=True):
                _go(0)
        with b2:
            if st.button("���ցiStep3 ����j", type="primary", use_container_width=True, disabled=st.session_state.final_doc is None):
                _go(2)

        return

    if st.session_state.step == 2:
        st.markdown("## Step3�b����iAgentic�j")
        opal_dict = st.session_state.opal_dict
        final_doc = st.session_state.final_doc
        st.caption(f"Policy: {st.session_state.applied_policy_display}")
        _render_warnings(final_doc.get("warnings") if isinstance(final_doc, dict) else None)

        if not opal_dict or not final_doc:
            st.warning("���ʂ�����܂���BStep1�œ��͂��A��������s���Ă��������B")
            if st.button("Step1�֖߂�", type="primary"):
                _go(0)
            return

        items = final_doc.get("line_items") or []
        counts = _count_by_class(items)
        guidance_items = [it for it in items if str(it.get("classification") or "").upper() == "GUIDANCE"]

        st.markdown("### ���ʃT�}���[")
        m1, m2, m3 = st.columns(3)
        m1.metric("�v�m�F�iGUIDANCE�j", counts["GUIDANCE"])
        m2.metric("���Y���iCAPITAL�j", counts["CAPITAL_LIKE"])
        m3.metric("��p���iEXPENSE�j", counts["EXPENSE_LIKE"])
        top_reason = None
        for it in guidance_items:
            summary = _summarize_flags(it.get("flags"))
            if summary:
                top_reason = summary
                break
        if top_reason:
            st.caption(f"��\�I�Ȓ�~���R: {top_reason}")
        st.info(STOP_NOTE)

        with st.container(border=True):
            st.markdown("**Stop�݌v�i�f�肵�Ȃ����l�j**")
            st.write("�E�P���^�ڐ݁^���݂ȂǁA���f������������m������ GUIDANCE �Ƃ��Ē�~���܂��B")
            st.write("�E��~���R�� flags �Ɏc���A�ォ�猟�؂ł���悤�ɂ��܂��B")
            st.write("�E������������i���Y�^��p�̌돈���j������A�����Ŏg����`�ɂ��܂��B")

        st.markdown("### ���茋�ʁi�v�m�F���ɕ\���j")
        if counts.get("GUIDANCE", 0) > 0:
            st.warning("�v�m�F�iGUIDANCE�j�͌딻��ł͂���܂���B���f�������\�������邽�ߒ�~���Ă��܂��B")
        rows = _to_table_rows(items)
        rows = _sort_rows_for_review(rows)
        _render_dataframe(rows)

        if guidance_items:
            with st.expander("�v�m�F�iGUIDANCE�j�̗��R�i�N���b�N�ŊJ���j", expanded=False):
                options = list(range(len(guidance_items)))
                fmt = lambda idx: f"{guidance_items[idx].get('line_no') or '-'}: { (guidance_items[idx].get('description') or '')[:40] }"
                selected_idx = st.selectbox("�v�m�F�s��I��", options=options, format_func=fmt, key="guidance_select")
                selected_item = guidance_items[selected_idx]
                ev = selected_item.get("evidence") or {}
                source_text = ev.get("source_text") if isinstance(ev, dict) else ""
                flags = selected_item.get("flags") or []
                flags_str = ", ".join(flags) if isinstance(flags, list) else str(flags or "")
                with st.container(border=True):
                    st.write(f"�s�ԍ�: {selected_item.get('line_no')}")
                    st.write(f"����: {selected_item.get('description') or ''}")
                    st.write(f"���ރ��x��: {selected_item.get('label_ja') or ''}")
                    st.write(f"���R: {selected_item.get('rationale_ja') or ''}")
                    if flags_str:
                        st.write(f"flags: {flags_str}")
                    if source_text:
                        st.write("evidence.source_text:")
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
                        "rationale_ja": it.get("rationale_ja") or "",
                        "flags": flags_str,
                    }
                    if source_text:
                        row["evidence.source_text"] = source_text
                    guidance_rows.append(row)
                st.dataframe(guidance_rows, hide_index=True, use_container_width=True)
        else:
            st.caption("�v�m�F�iGUIDANCE�j�͂���܂���B")

        st.markdown("### ���ɂ�邱��")
        st.write("1. �v�m�F�iGUIDANCE�j�̍s��D�悵�āA�l�����f���܂��B")
        st.write("2. flags/evidence �����āA�K�v�Ȃ猩�Ϗ������ɖ߂��Ċm�F���܂��B")
        st.write("3. ���f���ʂ�JSON�Ƃ��ĕۑ��E���L�ł��܂��B")

        with st.expander("Opal JSON�i���f�[�^�j", expanded=False):
            st.code(_safe_json_dumps(opal_dict), language="json")

        with st.expander("Final JSON�i�S�́j", expanded=False):
            st.code(_safe_json_dumps(final_doc), language="json")

        st.markdown("### �o�́i�ۑ��j")
        final_text = _safe_json_dumps(final_doc)
        final_bytes = final_text.encode("utf-8-sig")
        st.caption("�_�E�����[�h��UTF-8�iBOM�t���j�ŕۑ����܂��iWindows�݊��j�B")
        st.download_button(
            label="final.json ���_�E�����[�h",
            data=final_bytes,
            file_name="final.json",
            mime="application/json",
            use_container_width=True,
        )

        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("�߂�iStep2 ���K���j", use_container_width=True):
                _go(1)
        with b2:
            if st.button("Step1 ���͂�", use_container_width=True):
                _go(0)


def _render_pdf_flow(policy_display: str, policy_path: Optional[str]) -> None:
    st.markdown("## PDF Upload")
    st.caption(f"Policy: {policy_display}")
    uploaded_pdf = st.file_uploader("PDF���A�v���b�v", type=["pdf"], key="pdf_upload_input")
    st.caption("USE_DOCAI / USE_LOCAL_OCR / OCR_TEXT_THRESHOLD �̐ݒ�ɊY������B�g�p�f�[�^�����Ȃ��ĉU�镶���ł��܂�.")

    col_run, col_info = st.columns([1, 1])
    with col_run:
        disabled = uploaded_pdf is None
        if st.button("PDF��萔�l�֐i����/�~�j", type="primary", use_container_width=True, disabled=disabled):
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
                st.success("PDF��萔�l�֐i�萔�j���������܂���B")
            except Exception as e:
                st.error(f"PDF�o�͂Ɏ��s���܂���: {e}")
    with col_info:
        if st.session_state.pdf_upload_path:
            st.write(f"Uploads: {st.session_state.pdf_upload_path}")
        if st.session_state.pdf_extract_path and st.session_state.pdf_final_path:
            st.write(f"Results: {st.session_state.pdf_extract_path} / {st.session_state.pdf_final_path}")

    extraction = st.session_state.pdf_extraction
    final_doc = st.session_state.pdf_final_doc
    if not extraction or not final_doc:
        st.info("PDF��A�v���b�v���ăo�͂���Ă��������B�萔�ʂ� results ���\���܂�.")
        return

    _render_warnings(final_doc.get("warnings") if isinstance(final_doc, dict) else None)

    items = final_doc.get("line_items") or []
    counts = _count_by_class(items)

    st.markdown("### ���ʃT�}���[")
    m1, m2, m3 = st.columns(3)
    m1.metric("�v�m�F�iGUIDANCE�j", counts["GUIDANCE"])
    m2.metric("���Y���iCAPITAL�j", counts["CAPITAL_LIKE"])
    m3.metric("��p���iEXPENSE�j", counts["EXPENSE_LIKE"])
    st.info(STOP_NOTE)

    st.markdown("### ���茋�ʂƃG�b�W�F���X")
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
        st.markdown("### Evidence�i�萔�ł̎Q�Ɓj")
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
        with st.expander("Final �̃G�b�W�F���X�i�萔��->�萔�j", expanded=False):
            st.dataframe(final_snippets, hide_index=True, use_container_width=True)

    with st.expander("�萔�e�L�X�g�i�y�[�W�\���j", expanded=False):
        for p in extraction.get("pages") or []:
            st.write(f"Page {p.get('page')}: method={p.get('method')}")
            st.code(p.get("text") or "", language="text")

    with st.expander("extraction JSON / final JSON", expanded=False):
        st.caption("extraction")
        st.code(_safe_json_dumps(extraction), language="json")
        st.caption("final")
        st.code(_safe_json_dumps(final_doc), language="json")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    _init_state()

    st.title(APP_TITLE)
    st.caption(APP_SUB)
    st.caption(TAGLINE)
    st.info(
        "**�Ȃ��u�~�܂� Agent�v���K�v�Ȃ̂�**\n"
        "����ł́u�N�����m�F�����͂��v�Ƃ����O��ŏ���������܂��B\n"
        "�����E���Z���́AAI�̌��ʂ��l�̔��f���\���ɋ^���]�T������܂���B\n"
        "���̎d�g�݂́A�����s�������I��GUIDANCE�Œ�~���A\n"
        "�g�^���]�T���Ȃ��󋵁h�ł�������f�肪�ʉ߂��Ȃ��悤�ɂ��܂��B"
    )

    policy_choice = st.sidebar.radio("Policy�i��ƑO��j", options=list(POLICY_OPTIONS.keys()))
    selected_policy_path = POLICY_OPTIONS.get(policy_choice)
    policy_path: Optional[str] = None
    policy_display = "None"
    if selected_policy_path:
        p = Path(selected_policy_path)
        if p.exists():
            policy_path = str(p)
            policy_display = p.name
        else:
            st.sidebar.warning(f"Policy�t�@�C�� `{p}` ��������܂���BNone�Ƃ��Ĉ����܂��B")
    st.sidebar.caption(f"Policy: {policy_display}")
    st.session_state.policy_path = policy_path
    st.session_state.policy_display = policy_display

    tab_json, tab_pdf = st.tabs(["Opal / JSON", "PDF Upload"])
    with tab_json:
        _render_json_flow(policy_display, policy_path)
    with tab_pdf:
        _render_pdf_flow(policy_display, policy_path)


if __name__ == "__main__":
    main()
