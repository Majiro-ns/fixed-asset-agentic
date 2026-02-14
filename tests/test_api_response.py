"""Test API response schema includes WIN+1 additive fields and evidence.tax_rules."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import _format_classify_response
from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.policy import load_policy

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_response_includes_win1_fields():
    """Test that response includes all WIN+1 additive fields."""
    doc = {
        "version": "v1.0",
        "document_info": {"vendor": "Test"},
        "line_items": [
            {
                "line_no": 1,
                "description": "test item",
                "classification": "CAPITAL_LIKE",
                "rationale_ja": "Test rationale",
                "evidence": {
                    "source_text": "test",
                    "position_hint": "hint",
                },
            }
        ],
        "totals": {},
    }
    
    response = _format_classify_response(doc)
    
    # Original fields
    assert hasattr(response, "decision")
    assert hasattr(response, "reasons")
    assert hasattr(response, "evidence")
    assert hasattr(response, "questions")
    assert hasattr(response, "metadata")
    
    # WIN+1 additive fields
    assert hasattr(response, "is_valid_document")
    assert isinstance(response.is_valid_document, bool)
    
    assert hasattr(response, "confidence")
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0
    
    assert hasattr(response, "error_code")
    assert response.error_code is None or isinstance(response.error_code, str)
    
    assert hasattr(response, "trace")
    assert isinstance(response.trace, list)
    assert all(isinstance(t, str) for t in response.trace)
    
    assert hasattr(response, "missing_fields")
    assert isinstance(response.missing_fields, list)
    
    assert hasattr(response, "why_missing_matters")
    assert isinstance(response.why_missing_matters, list)
    
    # Evidence should have confidence
    if response.evidence:
        assert "confidence" in response.evidence[0]
        assert isinstance(response.evidence[0]["confidence"], float)


def test_guidance_populates_missing_fields():
    """Test that GUIDANCE decision populates missing_fields and why_missing_matters."""
    doc = {
        "version": "v1.0",
        "document_info": {"vendor": "Test"},
        "line_items": [
            {
                "line_no": 1,
                "description": "unknown item",
                "classification": "GUIDANCE",
                "flags": ["missing_info", "ambiguous"],
                "rationale_ja": "Need guidance",
                "evidence": {
                    "source_text": "test",
                    "position_hint": "hint",
                },
            }
        ],
        "totals": {},
    }
    
    response = _format_classify_response(doc)
    
    assert response.decision == "GUIDANCE"
    assert len(response.missing_fields) > 0
    assert len(response.why_missing_matters) > 0


def test_non_guidance_has_empty_missing_fields():
    """Test that non-GUIDANCE decisions have empty missing_fields."""
    doc = {
        "version": "v1.0",
        "document_info": {"vendor": "Test"},
        "line_items": [
            {
                "line_no": 1,
                "description": "test item",
                "classification": "CAPITAL_LIKE",
                "rationale_ja": "Test",
                "evidence": {
                    "source_text": "test",
                },
            }
        ],
        "totals": {},
    }
    
    response = _format_classify_response(doc)
    
    assert response.decision != "GUIDANCE"
    assert response.missing_fields == []
    assert response.why_missing_matters == []


def test_evidence_tax_rules_reflects_flags_200k():
    """evidence[].tax_rules に flags の tax_rule:* が反映される（200k: R-AMOUNT-001 等）."""
    policy_path = PROJECT_ROOT / "policies" / "company_default.json"
    policy = load_policy(str(policy_path) if policy_path.exists() else None)
    opal = {"line_items": [{"item_description": "test 200k", "amount": 200000}]}
    norm = adapt_opal_to_v1(opal)
    classified = classify_document(norm, policy)
    resp = _format_classify_response(classified)
    tax_rule_ev = [e for e in resp.evidence if isinstance(e.get("tax_rules"), list) and e["tax_rules"]]
    assert len(tax_rule_ev) >= 1
    all_tax = [f for e in tax_rule_ev for f in e["tax_rules"] if isinstance(f, str) and f.startswith("tax_rule:")]
    assert any("R-AMOUNT-001" in t or "R-AMOUNT-SME300k" in t for t in all_tax)


def test_evidence_tax_rules_reflects_flags_600k():
    """evidence[].tax_rules に flags の tax_rule:* が反映される（600k: R-AMOUNT-600k）."""
    policy_path = PROJECT_ROOT / "policies" / "company_default.json"
    policy = load_policy(str(policy_path) if policy_path.exists() else None)
    opal = {"line_items": [{"item_description": "test 600k", "amount": 600000}]}
    norm = adapt_opal_to_v1(opal)
    classified = classify_document(norm, policy)
    resp = _format_classify_response(classified)
    tax_rule_ev = [e for e in resp.evidence if isinstance(e.get("tax_rules"), list) and e["tax_rules"]]
    assert len(tax_rule_ev) >= 1
    all_tax = [f for e in tax_rule_ev for f in e["tax_rules"] if isinstance(f, str) and f.startswith("tax_rule:")]
    assert any("R-AMOUNT-600k" in t for t in all_tax)


# ---------------------------------------------------------------------------
# TC-040-05: Multi-item aggregation tests
# ---------------------------------------------------------------------------
def _make_doc_with_items(items):
    """Helper to build a minimal doc dict for _format_classify_response."""
    return {
        "version": "v1.0",
        "document_info": {"vendor": "Test"},
        "line_items": items,
        "totals": {},
    }


def test_multi_item_all_capital():
    """TC-040-05a: All CAPITAL_LIKE items → document decision CAPITAL_LIKE."""
    doc = _make_doc_with_items([
        {
            "line_no": 1,
            "description": "サーバー新設",
            "classification": "CAPITAL_LIKE",
            "confidence": 0.90,
            "rationale_ja": "新設工事",
            "flags": [],
            "evidence": {"source_text": "サーバー新設"},
        },
        {
            "line_no": 2,
            "description": "設置工事",
            "classification": "CAPITAL_LIKE",
            "confidence": 0.88,
            "rationale_ja": "設置",
            "flags": [],
            "evidence": {"source_text": "設置工事"},
        },
    ])
    resp = _format_classify_response(doc)
    assert resp.decision == "CAPITAL_LIKE"


def test_multi_item_all_expense():
    """TC-040-05b: All EXPENSE_LIKE items → document decision EXPENSE_LIKE."""
    doc = _make_doc_with_items([
        {
            "line_no": 1,
            "description": "保守点検",
            "classification": "EXPENSE_LIKE",
            "confidence": 0.90,
            "rationale_ja": "保守",
            "flags": [],
            "evidence": {"source_text": "保守点検"},
        },
        {
            "line_no": 2,
            "description": "消耗品交換",
            "classification": "EXPENSE_LIKE",
            "confidence": 0.85,
            "rationale_ja": "消耗品",
            "flags": [],
            "evidence": {"source_text": "消耗品交換"},
        },
    ])
    resp = _format_classify_response(doc)
    assert resp.decision == "EXPENSE_LIKE"


def test_multi_item_mixed():
    """TC-040-05c: CAPITAL + EXPENSE mixed → document decision GUIDANCE."""
    doc = _make_doc_with_items([
        {
            "line_no": 1,
            "description": "サーバー購入",
            "classification": "CAPITAL_LIKE",
            "confidence": 0.90,
            "rationale_ja": "購入",
            "flags": [],
            "evidence": {"source_text": "サーバー購入"},
        },
        {
            "line_no": 2,
            "description": "保守点検",
            "classification": "EXPENSE_LIKE",
            "confidence": 0.85,
            "rationale_ja": "保守",
            "flags": [],
            "evidence": {"source_text": "保守点検"},
        },
    ])
    resp = _format_classify_response(doc)
    assert resp.decision == "GUIDANCE"


def test_multi_item_with_guidance():
    """TC-040-05d: CAPITAL + GUIDANCE → majority vote (CAPITAL wins when more)."""
    doc = _make_doc_with_items([
        {
            "line_no": 1,
            "description": "サーバー新設",
            "classification": "CAPITAL_LIKE",
            "confidence": 0.90,
            "rationale_ja": "新設",
            "flags": [],
            "evidence": {"source_text": "サーバー新設"},
        },
        {
            "line_no": 2,
            "description": "設置工事",
            "classification": "CAPITAL_LIKE",
            "confidence": 0.88,
            "rationale_ja": "設置",
            "flags": [],
            "evidence": {"source_text": "設置工事"},
        },
        {
            "line_no": 3,
            "description": "撤去費",
            "classification": "GUIDANCE",
            "confidence": 0.55,
            "rationale_ja": "撤去",
            "flags": ["mixed_keyword:撤去"],
            "evidence": {"source_text": "撤去費"},
        },
    ])
    resp = _format_classify_response(doc)
    # 2 CAPITAL vs 0 EXPENSE vs 1 GUIDANCE → CAPITAL_LIKE wins by majority
    assert resp.decision == "CAPITAL_LIKE"
