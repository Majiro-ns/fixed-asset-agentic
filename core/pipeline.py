import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.pdf_extract import extract_pdf, extraction_to_opal
from core.policy import load_policy

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_text_auto(path: str) -> str:
    """Hackathon patch: robust text decoding for Japanese invoices (UTF-8/CP932/Shift-JIS)."""
    data = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    # last resort: keep pipeline running while marking garbled chars
    return data.decode("cp932", errors="replace")


def load_json(path: Path) -> Any:
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return json.loads(data.decode(enc))
        except UnicodeDecodeError:
            continue
    # last resort: keep running (mojibake may remain, but no crash)
    return json.loads(data.decode("utf-8", errors="replace"))


def save_json(path: Path, obj: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8-sig") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def run_adapter(input_path: Path, output_path: Path) -> Path:
    opal = load_json(Path(input_path))
    normalized = adapt_opal_to_v1(opal)
    save_json(Path(output_path), normalized)
    return Path(output_path)


def run_pipeline(input_path: Path, output_path: Path, policy_path: Optional[str] = None) -> Path:
    opal = load_json(Path(input_path))
    normalized = adapt_opal_to_v1(opal)
    policy = load_policy(policy_path)
    classified = classify_document(normalized, policy)
    save_json(Path(output_path), classified)
    return Path(output_path)


def _persist_pdf_to_uploads(pdf_path: Path) -> Path:
    uploads_dir = PROJECT_ROOT / "data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.parent.resolve() == uploads_dir.resolve():
        return pdf_path

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = pdf_path.name.replace(" ", "_")
    target = uploads_dir / f"{timestamp}_{safe_name}"
    target.write_bytes(pdf_path.read_bytes())
    return target


def run_pdf_pipeline(pdf_path: Path, results_dir: Path, policy_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract PDF -> normalize -> classify.
    Saves artifacts under data/uploads and data/results and returns paths plus in-memory results.
    """
    stored_pdf = _persist_pdf_to_uploads(Path(pdf_path))

    results_root = Path(results_dir) if results_dir else PROJECT_ROOT / "data" / "results"
    results_root.mkdir(parents=True, exist_ok=True)
    stem = stored_pdf.stem

    extraction = extract_pdf(stored_pdf)
    extraction_path = results_root / f"{stem}_extract.json"
    save_json(extraction_path, extraction)

    opal_like = extraction_to_opal(extraction)
    normalized = adapt_opal_to_v1(opal_like)
    policy = load_policy(policy_path)
    final_doc = classify_document(normalized, policy)
    warnings = extraction.get("meta", {}).get("warnings", [])
    final_doc["warnings"] = warnings

    final_path = results_root / f"{stem}_final.json"
    save_json(final_path, final_doc)

    return {
        "upload_path": stored_pdf,
        "extraction_path": extraction_path,
        "final_path": final_path,
        "extraction": extraction,
        "final_doc": final_doc,
    }
