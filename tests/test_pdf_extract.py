from pathlib import Path

from core.pdf_extract import TEXT_TOO_SHORT_CODE, extract_pdf, extraction_to_opal
from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.pipeline import run_pdf_pipeline
from core.policy import load_policy


FIXTURE = Path(__file__).parent / "fixtures" / "sample_text.pdf"


def test_extract_pdf_text_only():
    data = extract_pdf(FIXTURE, use_docai=False, use_ocr=False)
    assert data["meta"]["filename"] == FIXTURE.name
    assert data["meta"]["num_pages"] == 1
    assert data["meta"]["source"] == "local"
    pages = data["pages"]
    assert len(pages) == 1
    p0 = pages[0]
    assert p0["method"] == "text"
    assert p0["evidence"]
    assert isinstance(p0["evidence"], list)
    assert p0["evidence"][0].get("snippet")


def test_extract_to_classify_without_ocr_or_docai(monkeypatch):
    # Explicitly disable env-driven toggles
    monkeypatch.setenv("USE_DOCAI", "false")
    monkeypatch.setenv("USE_LOCAL_OCR", "false")
    monkeypatch.setenv("OCR_TEXT_THRESHOLD", "20")

    extraction = extract_pdf(FIXTURE, use_docai=False, use_ocr=False)
    opal_like = extraction_to_opal(extraction)
    doc = adapt_opal_to_v1(opal_like)
    policy = load_policy(None)
    classified = classify_document(doc, policy)
    item = classified["line_items"][0]
    assert item["classification"] in {"GUIDANCE", "CAPITAL_LIKE", "EXPENSE_LIKE"}
    assert item.get("evidence")


def test_run_pdf_pipeline_creates_outputs(monkeypatch):
    monkeypatch.setenv("USE_DOCAI", "false")
    monkeypatch.setenv("USE_LOCAL_OCR", "false")

    results = run_pdf_pipeline(FIXTURE, Path("data/results"), None)
    assert results["extraction_path"].exists()
    assert results["final_path"].exists()

    final_doc = results["final_doc"]
    assert final_doc.get("line_items")
    evidence = final_doc["line_items"][0].get("evidence")
    assert evidence
    assert evidence.get("source_text")
    assert evidence.get("snippets")
    assert final_doc.get("warnings") == results["extraction"]["meta"].get("warnings")


def test_extraction_to_opal_parses_tables():
    """Line items are parsed from extracted tables when available."""
    extraction = {
        "meta": {"filename": "test.pdf"},
        "pages": [
            {
                "page": 1,
                "text": "見積書",
                "tables": [
                    [
                        ["品名", "数量", "単価", "金額"],
                        ["業務用プリンター", "1", "50000", "50000"],
                        ["据付工事", "1", "10000", "10000"],
                    ]
                ],
                "evidence": [{"page": 1, "method": "text", "snippet": "test"}],
            }
        ],
    }
    opal = extraction_to_opal(extraction)
    items = opal["line_items"]
    assert len(items) >= 2
    descs = [it.get("description", "") for it in items]
    assert "業務用プリンター" in descs
    assert "据付工事" in descs
    amounts = [it.get("amount") for it in items if it.get("amount") is not None]
    assert 50000 in amounts
    assert 10000 in amounts


def test_extraction_to_opal_parses_text_fallback():
    """Line items are parsed from text when no tables."""
    extraction = {
        "meta": {"filename": "test.pdf"},
        "pages": [
            {
                "page": 1,
                "text": "工事代金 1 式 300000 円\n諸経費 1 式 50000 円",
                "tables": [],
                "evidence": [{"page": 1, "method": "text", "snippet": "test"}],
            }
        ],
    }
    opal = extraction_to_opal(extraction)
    items = opal["line_items"]
    assert len(items) >= 1
    assert any(it.get("amount") == 300000 or it.get("amount") == 50000 for it in items)


def test_extract_pdf_emits_warning_for_short_text(monkeypatch, tmp_path):
    monkeypatch.setenv("USE_LOCAL_OCR", "false")
    dummy_pdf = tmp_path / "blank.pdf"
    dummy_pdf.write_bytes(b"")

    monkeypatch.setattr("core.pdf_extract._extract_with_fitz", lambda path: [{"page": 1, "text": ""}])
    monkeypatch.setattr("core.pdf_extract._extract_with_pdfplumber", lambda path: [])

    extraction = extract_pdf(dummy_pdf, use_docai=False, use_ocr=False)
    warnings = extraction["meta"].get("warnings")
    assert warnings
    assert warnings[0]["code"] == TEXT_TOO_SHORT_CODE
