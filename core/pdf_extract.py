import datetime
import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _extract_all_tables_pdfplumber(path: Path) -> Dict[int, List[List[List[Optional[str]]]]]:
    """Extract tables from all pages when fitz was used for text (pdfplumber for tables only)."""
    try:
        import pdfplumber
    except ImportError:
        return {}
    out: Dict[int, List[List[List[Optional[str]]]]] = {}
    try:
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = _extract_tables_from_plumber_page(page)
                if tables:
                    out[i + 1] = tables
    except Exception:
        pass
    return out


def _extract_tables_from_plumber_page(plumber_page: Any) -> List[List[List[Optional[str]]]]:
    """Extract tables from a pdfplumber page. Returns list of tables, each table is list of rows (list of cells)."""
    if plumber_page is None:
        return []
    try:
        tables = plumber_page.extract_tables()
        if not tables:
            return []
        return [[[str(c).strip() if c is not None else "" for c in row] for row in t] for t in tables]
    except Exception:
        return []


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
            tables = _extract_tables_from_plumber_page(page)
            pages.append({"page": i + 1, "text": text, "tables": tables, "_plumber_page": page})
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


def _try_gemini_vision(path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract PDF using Gemini Vision API.
    Feature Flag: GEMINI_PDF_ENABLED=1

    PDFを画像化してGemini Visionに送信し、line_itemsを抽出する。
    人間が見るのと同じ精度で様々な様式のPDFを読み取れる。
    """
    if not _bool_env("GEMINI_PDF_ENABLED", False):
        return None

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        import fitz  # PyMuPDF for PDF to image
        import google.generativeai as genai
        from PIL import Image
        import io
        import json
    except ImportError:
        return None

    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Convert PDF to images
        doc = fitz.open(str(path))
        images = []
        for page_index in range(min(doc.page_count, 5)):  # Limit to 5 pages
            page = doc.load_page(page_index)
            # Higher resolution for better accuracy
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        doc.close()

        if not images:
            return None

        # Prompt for extraction
        prompt = """この見積書・請求書・納品書の画像から、明細行を抽出してください。

【出力形式】必ず以下のJSON形式で回答してください:
{
  "line_items": [
    {"description": "品名・作業内容（具体的な名称）", "amount": 金額（数値）},
    ...
  ],
  "vendor": "発行元会社名（わかれば）",
  "total": 合計金額（数値、わかれば）
}

【重要：descriptionの書き方】
- 品名・作業内容・サービス名を「具体的に」記載すること
- NG例: "明細", "品目1", "項目" （これらは不可）
- OK例: "Dell PowerEdge サーバー", "空調設備工事", "ノートPC HP ProBook"
- 商品名、型番、作業内容など具体的な名称を優先

【その他のルール】
- amountは数値のみ（カンマや円記号なし）
- 小計・合計行は line_items に含めない
- 税抜金額を優先
- 読み取れない場合は空配列 [] を返す"""

        # Send to Gemini Vision
        response = model.generate_content(
            [prompt] + images,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        # Parse response
        result = json.loads(response.text)
        line_items = result.get("line_items", [])

        if not line_items:
            return None

        # Convert to internal format
        formatted_items = []
        for item in line_items:
            desc = item.get("description", "")
            amt = item.get("amount")
            if desc or amt:
                formatted_item = {
                    "description": desc or "明細",
                    "evidence": {
                        "source_text": desc,
                        "position_hint": "gemini_vision",
                        "snippets": [{"page": 1, "method": "gemini_vision", "snippet": desc}],
                    },
                }
                if amt is not None:
                    try:
                        formatted_item["amount"] = int(float(amt))
                    except (ValueError, TypeError):
                        pass
                formatted_items.append(formatted_item)

        if not formatted_items:
            return None

        return {
            "meta": {
                "filename": path.name,
                "sha256": _compute_sha256(path),
                "num_pages": len(images),
                "extracted_at": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "gemini_vision",
                "warnings": [],
            },
            "pages": [{"page": 1, "text": "", "method": "gemini_vision", "tables": []}],
            "line_items": formatted_items,  # Pre-parsed line items
            "vendor": result.get("vendor"),
            "total": result.get("total"),
        }

    except Exception:
        return None


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


def extract_pdf(
    path: Path,
    *,
    use_docai: bool = False,
    use_ocr: bool = False,
    use_gemini_vision: bool = False,
) -> Dict[str, Any]:
    """
    Extract text and line items from PDF.

    Args:
        path: PDF file path
        use_docai: Force use Document AI
        use_ocr: Force use local OCR
        use_gemini_vision: Force use Gemini Vision API (requires GEMINI_PDF_ENABLED=1)
    """
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

    # Priority 1: Gemini Vision (highest accuracy, like human reading)
    # Enabled either by env flag or explicit parameter
    if use_gemini_vision or _bool_env("GEMINI_PDF_ENABLED", False):
        gemini_res = _try_gemini_vision(path)
        if gemini_res:
            return gemini_res

    # Priority 2: Document AI
    if use_docai or _bool_env("USE_DOCAI", False):
        docai_res = _try_docai(path)
        if docai_res:
            return docai_res

    pages = _extract_with_fitz(path) or _extract_with_pdfplumber(path) or []
    meta["num_pages"] = len(pages)

    tables_by_page: Dict[int, List[List[List[Optional[str]]]]] = {}
    if pages and "_plumber_page" not in (pages[0] or {}):
        tables_by_page = _extract_all_tables_pdfplumber(path)

    results: List[Dict[str, Any]] = []
    methods_used: List[str] = []
    for entry in pages:
        page_no = entry.get("page") or 0
        text = entry.get("text") or ""
        method = "text"
        evidence = []
        tables = entry.get("tables") or tables_by_page.get(page_no, [])

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
        results.append({"page": page_no, "method": method, "text": text, "tables": tables, "evidence": evidence})
        methods_used.append(method)

    meta["source"] = _mark_methods(methods_used)
    meta["warnings"] = warnings
    return {"meta": meta, "pages": results}


_HEADER_DESC = frozenset({"品名", "品目", "摘要", "項目", "内訳", "名称", "内容", "明細", "工事内容", "備考", "説明", "デスクリプション"})
_HEADER_QTY = frozenset({"数量", "個数", "式"})
_HEADER_UNIT = frozenset({"単位"})
_HEADER_PRICE = frozenset({"単価", "価格"})
_HEADER_AMOUNT = frozenset({"金額", "合計", "小計", "計", "税込", "税抜"})

# 合計行・小計行として除外すべきキーワード
_TOTAL_KEYWORDS = frozenset({
    "合計", "小計", "計", "税込", "税抜", "税込合計", "税抜合計",
    "総合計", "御請求金額", "請求金額", "お支払金額", "支払金額",
    "消費税", "消費税額", "税額", "値引", "値引き", "割引",
    "送料", "運賃", "配送料", "手数料", "振込手数料",
    "TOTAL", "Total", "total", "SUBTOTAL", "Subtotal", "subtotal",
    "TAX", "Tax", "tax", "合計金額", "ご請求金額", "お見積金額",
})


def _is_total_row(desc: str) -> bool:
    """
    Check if the description indicates a total/subtotal row that should be excluded.
    合計行・小計行・税込行などを除外するための判定。
    """
    if not desc:
        return False
    # 完全一致チェック
    normalized = desc.strip().replace(" ", "").replace("　", "")
    if normalized in _TOTAL_KEYWORDS:
        return True
    # 先頭一致チェック（「合計:」「小計　」など）
    for keyword in _TOTAL_KEYWORDS:
        if normalized.startswith(keyword):
            return True
    return False


def _normalize_header(cell: Any) -> str:
    s = (cell or "").strip().replace(" ", "").replace("\n", "")
    return s


def _detect_table_columns(header_row: List[Optional[str]]) -> Tuple[int, int, int, int]:
    """
    Detect column indices for description, quantity, unit_price, amount.
    Returns (desc_col, qty_col, unit_col, amount_col), -1 if not found.
    """
    desc_col = qty_col = unit_col = amount_col = -1
    for i, cell in enumerate(header_row):
        norm = _normalize_header(cell)
        if not norm:
            continue
        if norm in _HEADER_DESC and desc_col < 0:
            desc_col = i
        elif norm in _HEADER_QTY and qty_col < 0:
            qty_col = i
        elif norm in _HEADER_UNIT and unit_col < 0:
            unit_col = i
        elif norm in _HEADER_PRICE and unit_col < 0:
            unit_col = i
        elif norm in _HEADER_AMOUNT and amount_col < 0:
            amount_col = i
    if amount_col < 0 and unit_col >= 0 and len(header_row) > unit_col + 1:
        amount_col = unit_col + 1
    return (desc_col, qty_col, unit_col, amount_col)


def _parse_number(s: Any) -> Optional[float]:
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("，", "")
    t = re.sub(r"[^\d.\-]", "", t)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _parse_line_items_from_tables(
    pages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Parse line items from extracted tables. Returns list of {description, quantity, unit_price, amount, evidence}."""
    line_items: List[Dict[str, Any]] = []
    seen: set = set()

    for p in pages or []:
        page_no = p.get("page", 0)
        tables = p.get("tables") or []
        evidence_list = p.get("evidence") or []
        snippets = [e.get("snippet", "") for e in evidence_list if isinstance(e, dict)]
        source_text = " ".join(snippets) if snippets else (p.get("text") or "")[:500]

        for table in tables:
            if not table or len(table) < 2:
                continue
            header_row = table[0]
            if not isinstance(header_row, list):
                continue
            desc_col, qty_col, unit_col, amount_col = _detect_table_columns(header_row)
            if desc_col < 0 and amount_col < 0:
                desc_col = 0
                if len(header_row) >= 4:
                    qty_col, unit_col, amount_col = 1, 2, 3
                elif len(header_row) >= 3:
                    unit_col, amount_col = 1, 2
                elif len(header_row) >= 2:
                    amount_col = 1

            for row in table[1:]:
                if not isinstance(row, list):
                    continue
                cells = [str(c).strip() if c is not None else "" for c in row]
                desc = cells[desc_col] if 0 <= desc_col < len(cells) else ""

                # 合計行・小計行・税込行は除外
                if _is_total_row(desc):
                    continue

                qty_val = _parse_number(cells[qty_col]) if 0 <= qty_col < len(cells) else None
                unit_val = _parse_number(cells[unit_col]) if 0 <= unit_col < len(cells) else None
                amt_val = _parse_number(cells[amount_col]) if 0 <= amount_col < len(cells) else None
                if amt_val is None and unit_val is not None and qty_val is not None:
                    amt_val = unit_val * qty_val
                if amt_val is None:
                    amt_val = unit_val
                if not desc and amt_val is None:
                    continue
                amt_key = round(amt_val, 2) if isinstance(amt_val, float) else amt_val
                key = (page_no, (desc or "")[:80], amt_key)
                if key in seen:
                    continue
                seen.add(key)
                evidence_obj: Dict[str, Any] = {"source_text": desc or source_text, "position_hint": f"page{page_no}"}
                if evidence_list:
                    evidence_obj["snippets"] = [
                        {"page": e.get("page", page_no), "method": e.get("method", "text"), "snippet": _safe_snippet(e.get("snippet", desc))}
                        for e in evidence_list if isinstance(e, dict)
                    ]

                # descが空の場合のフォールバック処理（演算子優先順位を明確に）
                if desc:
                    item_description = desc
                elif amt_val:
                    item_description = f"明細({int(amt_val) if amt_val == int(amt_val) else amt_val}円)"
                else:
                    item_description = "品名なし"

                item: Dict[str, Any] = {
                    "description": item_description,
                    "evidence": evidence_obj,
                }
                if qty_val is not None:
                    item["quantity"] = int(qty_val) if qty_val == int(qty_val) else qty_val
                if unit_val is not None:
                    item["unit_price"] = unit_val
                if amt_val is not None:
                    item["amount"] = int(amt_val) if amt_val == int(amt_val) else amt_val
                line_items.append(item)

    return line_items


def _parse_line_items_from_text(text: str, page_no: int = 1) -> List[Dict[str, Any]]:
    """
    Fallback: parse line-like patterns from text.
    Matches: description followed by numbers (qty unit amount or amount only).
    """
    items: List[Dict[str, Any]] = []
    lines = text.split("\n")
    num_pat = re.compile(r"[\d,]+(?:\.[\d]+)?")
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
        nums = num_pat.findall(line)
        nums_clean = [_parse_number(n) for n in nums]
        nums_clean = [n for n in nums_clean if n is not None and n > 0]
        if not nums_clean:
            continue
        amt = nums_clean[-1]
        desc = num_pat.sub("", line).strip()
        desc = re.sub(r"\s+", " ", desc).strip()

        # 合計行・小計行・税込行は除外
        if _is_total_row(desc):
            continue

        if not desc:
            desc = f"明細({int(amt)}円)"
        if amt < 10 or amt > 10_000_000_000:
            continue
        evidence_obj: Dict[str, Any] = {
            "source_text": line[:300],
            "position_hint": f"page{page_no}",
            "snippets": [{"page": page_no, "method": "text", "snippet": _safe_snippet(line)}],
        }
        items.append({
            "description": desc,
            "amount": int(amt) if amt == int(amt) else amt,
            "evidence": evidence_obj,
        })
    return items


def extraction_to_opal(extraction: Dict[str, Any]) -> Dict[str, Any]:
    # If Gemini Vision already extracted line_items, use them directly
    if extraction.get("line_items"):
        return {
            "title": extraction.get("meta", {}).get("filename", ""),
            "invoice_date": "",
            "vendor": extraction.get("vendor"),
            "line_items": extraction.get("line_items"),
        }

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

    line_items = _parse_line_items_from_tables(pages or [])

    if not line_items:
        for p in pages or []:
            text = (p.get("text") or "").strip()
            page_no = p.get("page", 1)
            if text:
                parsed = _parse_line_items_from_text(text, page_no)
                if parsed:
                    line_items.extend(parsed)
                    break

    if not line_items:
        evidence_obj: Dict[str, Any] = {"source_text": combined_text, "position_hint": ""}
        if evidence_snippets:
            evidence_obj["snippets"] = evidence_snippets
        line_items = [
            {
                "description": combined_text,
                "evidence": evidence_obj,
            }
        ]

    return {
        "title": extraction.get("meta", {}).get("filename", ""),
        "invoice_date": "",
        "vendor": None,
        "line_items": line_items,
    }
