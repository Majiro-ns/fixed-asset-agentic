import datetime
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

OCR_TEXT_THRESHOLD_DEFAULT = 50
TEXT_TOO_SHORT_CODE = "TEXT_TOO_SHORT"


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_snippet(text: str, limit: int = 200) -> str:
    if not text:
        return ""
    t = text.replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "..."


def _extract_with_fitz(path: Path) -> Optional[List[Dict[str, Any]]]:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    doc = fitz.open(str(path))
    pages: List[Dict[str, Any]] = []
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        text = page.get_text("text") or ""
        pages.append({"page": page_index + 1, "text": text, "_page_obj": page})
    return pages


def _extract_with_pdfplumber(path: Path) -> Optional[List[Dict[str, Any]]]:
    try:
        import pdfplumber
    except ImportError:
        return None

    pages: List[Dict[str, Any]] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            pages.append({"page": i + 1, "text": text, "_plumber_page": page})
    return pages


def _ocr_page_via_fitz(page_obj: Any) -> Optional[str]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return None

    try:
        pix = page_obj.get_pixmap()
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        return pytesseract.image_to_string(img)
    except Exception:
        return None


def _mark_methods(methods: List[str]) -> str:
    uniq = set(methods)
    if not uniq:
        return "local"
    if len(uniq) == 1:
        m = uniq.pop()
        return "docai" if m == "docai" else ("ocr" if m == "ocr" else "local")
    return "mixed"


def _try_docai(path: Path) -> Optional[Dict[str, Any]]:
    """Extract PDF using Google Cloud Document AI. Only used when USE_DOCAI=1."""
    if not _bool_env("USE_DOCAI", False):
        return None
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    processor_id = os.getenv("DOCAI_PROCESSOR_ID")
    if not project_id or not processor_id:
        return None
    location = os.getenv("DOCAI_LOCATION", "us")
    try:
        from google.cloud.documentai_v1 import DocumentProcessorServiceClient
        from google.cloud.documentai_v1.types import ProcessRequest, RawDocument
    except ImportError:
        return None
    try:
        client = DocumentProcessorServiceClient()
        name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        raw_doc = RawDocument(content=path.read_bytes(), mime_type="application/pdf")
        req = ProcessRequest(name=name, raw_document=raw_doc)
        result = client.process_document(request=req)
        doc = result.document
        text = (doc.text or "") if (doc and hasattr(doc, "text")) else ""
        num_pages = len(doc.pages) if (doc and hasattr(doc, "pages") and doc.pages) else 1
        return {
            "meta": {
                "filename": path.name,
                "sha256": _compute_sha256(path),
                "num_pages": num_pages,
                "extracted_at": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "docai",
                "warnings": [],
            },
            "pages": [{"page": 1, "text": text, "method": "docai"}],
        }
    except Exception:
        return None


def extract_pdf(path: Path, *, use_docai: bool = False, use_ocr: bool = False) -> Dict[str, Any]:
    path = Path(path)
    threshold = _int_env("OCR_TEXT_THRESHOLD", OCR_TEXT_THRESHOLD_DEFAULT)
    ocr_enabled = use_ocr or _bool_env("USE_LOCAL_OCR", False)
    meta: Dict[str, Any] = {
        "filename": path.name,
        "sha256": _compute_sha256(path),
        "num_pages": 0,
        "extracted_at": datetime.datetime.utcnow().isoformat() + "Z",
        "source": "local",
        "warnings": [],
    }
    warnings: List[Dict[str, Any]] = []

    if use_docai or _bool_env("USE_DOCAI", False):
        docai_res = _try_docai(path)
        if docai_res:
            return docai_res

    pages = _extract_with_fitz(path) or _extract_with_pdfplumber(path) or []
    meta["num_pages"] = len(pages)

    results: List[Dict[str, Any]] = []
    methods_used: List[str] = []
    for entry in pages:
        page_no = entry.get("page") or 0
        text = entry.get("text") or ""
        method = "text"
        evidence = []

        if len(text) < threshold and ocr_enabled:
            ocr_text = _ocr_page_via_fitz(entry.get("_page_obj"))
            if ocr_text:
                text = ocr_text
                method = "ocr"
            else:
                evidence.append({"method": "ocr", "page": page_no, "snippet": "ocr_unavailable_or_failed"})

        if len(text) < threshold:
            msg_suffix = "OCR is enabled." if ocr_enabled else "OCR is disabled (USE_LOCAL_OCR=false)."
            warnings.append(
                {
                    "code": TEXT_TOO_SHORT_CODE,
                    "message": "Text extraction is too short; scanned PDF suspected. " + msg_suffix,
                    "page": page_no,
                }
            )

        evidence.append({"method": method, "page": page_no, "snippet": _safe_snippet(text)})
        results.append({"page": page_no, "method": method, "text": text, "tables": [], "evidence": evidence})
        methods_used.append(method)

    meta["source"] = _mark_methods(methods_used)
    meta["warnings"] = warnings
    return {"meta": meta, "pages": results}


def extraction_to_opal(extraction: Dict[str, Any]) -> Dict[str, Any]:
    pages = extraction.get("pages") if isinstance(extraction, dict) else []
    texts: List[str] = []
    evidence_snippets: List[Dict[str, Any]] = []

    for p in pages or []:
        text = (p.get("text") or "").strip()
        if text:
            texts.append(text)

        ev_list = p.get("evidence") if isinstance(p, dict) else []
        if isinstance(ev_list, list):
            for ev in ev_list:
                if not isinstance(ev, dict):
                    continue
                snippet = ev.get("snippet") or text
                evidence_snippets.append(
                    {
                        "page": ev.get("page") or p.get("page"),
                        "method": ev.get("method"),
                        "snippet": _safe_snippet(snippet),
                    }
                )

    combined_text = "\n\n".join(texts).strip()
    if not combined_text:
        combined_text = extraction.get("meta", {}).get("filename", "")

    evidence_obj: Dict[str, Any] = {"source_text": combined_text, "position_hint": ""}
    if evidence_snippets:
        evidence_obj["snippets"] = evidence_snippets

    return {
        "title": extraction.get("meta", {}).get("filename", ""),
        "invoice_date": "",
        "vendor": None,
        "line_items": [
            {
                "description": combined_text,
                "evidence": evidence_obj,
            }
        ],
    }
