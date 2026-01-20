"""Test API response schema includes WIN+1 additive fields."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import _format_classify_response


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
