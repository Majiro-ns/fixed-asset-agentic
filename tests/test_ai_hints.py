"""Unit tests for the AI hint (heuristic) feature in _add_ai_hints_for_guidance."""

from unittest.mock import patch

import pytest

# We need to mock GEMINI_ENABLED and GEMINI_AVAILABLE *before* importing
# _add_ai_hints_for_guidance so the module-level flags are False.
with patch.dict("os.environ", {"GEMINI_ENABLED": "0"}):
    from api.main import _add_ai_hints_for_guidance, _format_classify_response

from core import schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(description: str, classification: str = "GUIDANCE", amount: int = 100000):
    """Return a minimal line-item dict used by the classifier pipeline."""
    return {
        "line_no": 1,
        "description": description,
        "amount": amount,
        "classification": classification,
        "confidence": 0.5,
        "flags": [],
        "rationale_ja": "",
        "evidence": {
            "source_text": description,
            "position_hint": "",
        },
    }


def _run_heuristic(items):
    """Run _add_ai_hints_for_guidance with Gemini disabled and return trace_steps."""
    classified = {"line_items": items}
    trace_steps = []
    with patch("api.main.GEMINI_ENABLED", False), \
         patch("api.main.GEMINI_AVAILABLE", False):
        _add_ai_hints_for_guidance(classified, trace_steps)
    return classified, trace_steps


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHeuristicHintExpenseKeyword:
    """When a GUIDANCE item description contains an expense keyword,
    the heuristic should add ai_hint with suggestion=EXPENSE_LIKE."""

    @pytest.mark.parametrize("keyword", ["撤去", "廃棄", "処分", "解体", "除却", "原状回復"])
    def test_each_expense_keyword(self, keyword):
        item = _make_item(f"空調設備{keyword}工事")
        classified, trace_steps = _run_heuristic([item])

        assert "ai_hint" in classified["line_items"][0]
        hint = classified["line_items"][0]["ai_hint"]
        assert hint["suggestion"] == schema.EXPENSE_LIKE
        assert hint["confidence"] == 0.6
        assert keyword in hint["reasoning"]
        assert "ai_hint_heuristic" in trace_steps

    def test_expense_keyword_撤去(self):
        """Explicit test: description containing '撤去'."""
        item = _make_item("既設空調撤去")
        classified, _ = _run_heuristic([item])

        hint = classified["line_items"][0]["ai_hint"]
        assert hint["suggestion"] == schema.EXPENSE_LIKE
        assert hint["suggestion_label"] == "費用寄り"


class TestHeuristicHintCapitalKeyword:
    """When a GUIDANCE item description contains a capital keyword,
    the heuristic should add ai_hint with suggestion=CAPITAL_LIKE."""

    @pytest.mark.parametrize("keyword", ["新設", "設置", "導入", "構築", "整備", "購入", "増設", "改修"])
    def test_each_capital_keyword(self, keyword):
        item = _make_item(f"サーバー{keyword}")
        classified, trace_steps = _run_heuristic([item])

        assert "ai_hint" in classified["line_items"][0]
        hint = classified["line_items"][0]["ai_hint"]
        assert hint["suggestion"] == schema.CAPITAL_LIKE
        assert hint["confidence"] == 0.6
        assert keyword in hint["reasoning"]
        assert "ai_hint_heuristic" in trace_steps

    def test_capital_keyword_新設(self):
        """Explicit test: description containing '新設'."""
        item = _make_item("空調新設工事")
        classified, _ = _run_heuristic([item])

        hint = classified["line_items"][0]["ai_hint"]
        assert hint["suggestion"] == schema.CAPITAL_LIKE
        assert hint["suggestion_label"] == "資産寄り"


class TestHeuristicHintMixedKeywords:
    """When a description contains both expense and capital keywords,
    should get GUIDANCE suggestion with low confidence."""

    def test_mixed_撤去_and_新設(self):
        item = _make_item("旧設備撤去及び新設備新設工事")
        classified, trace_steps = _run_heuristic([item])

        hint = classified["line_items"][0]["ai_hint"]
        assert hint["suggestion"] == "GUIDANCE"
        assert hint["suggestion_label"] == "判定困難"
        assert hint["confidence"] == 0.3
        assert "混在" in hint["reasoning"]
        assert "ai_hint_heuristic" in trace_steps

    def test_mixed_廃棄_and_導入(self):
        item = _make_item("旧機器廃棄・新機器導入一式")
        classified, _ = _run_heuristic([item])

        hint = classified["line_items"][0]["ai_hint"]
        assert hint["suggestion"] == "GUIDANCE"
        assert hint["confidence"] == 0.3


class TestHeuristicHintNoKeywords:
    """When description has no matching keywords, ai_hint should NOT be added."""

    def test_generic_description(self):
        item = _make_item("電気工事一式")
        classified, trace_steps = _run_heuristic([item])

        assert "ai_hint" not in classified["line_items"][0]
        # No hint added means no trace entry
        assert "ai_hint_heuristic" not in trace_steps

    def test_plain_工事(self):
        item = _make_item("工事")
        classified, trace_steps = _run_heuristic([item])

        assert "ai_hint" not in classified["line_items"][0]
        assert "ai_hint_heuristic" not in trace_steps

    def test_empty_description(self):
        item = _make_item("")
        classified, _ = _run_heuristic([item])

        assert "ai_hint" not in classified["line_items"][0]


class TestAiHintOnlyForGuidance:
    """When items are CAPITAL_LIKE or EXPENSE_LIKE, no ai_hint should be added."""

    def test_capital_like_item_no_hint(self):
        item = _make_item("サーバー新設", classification="CAPITAL_LIKE")
        classified, trace_steps = _run_heuristic([item])

        # CAPITAL_LIKE items should be skipped entirely
        assert "ai_hint" not in classified["line_items"][0]
        assert "ai_hint_heuristic" not in trace_steps

    def test_expense_like_item_no_hint(self):
        item = _make_item("設備撤去", classification="EXPENSE_LIKE")
        classified, trace_steps = _run_heuristic([item])

        assert "ai_hint" not in classified["line_items"][0]
        assert "ai_hint_heuristic" not in trace_steps

    def test_mixed_classifications_only_guidance_gets_hint(self):
        """In a list with multiple classifications, only GUIDANCE items get hints."""
        items = [
            _make_item("サーバー新設", classification="CAPITAL_LIKE"),
            _make_item("古い設備撤去作業", classification="GUIDANCE"),
            _make_item("配線工事", classification="EXPENSE_LIKE"),
        ]
        classified, trace_steps = _run_heuristic(items)

        # CAPITAL_LIKE item: no hint
        assert "ai_hint" not in classified["line_items"][0]
        # GUIDANCE item: gets expense hint (contains 撤去)
        assert "ai_hint" in classified["line_items"][1]
        assert classified["line_items"][1]["ai_hint"]["suggestion"] == schema.EXPENSE_LIKE
        # EXPENSE_LIKE item: no hint
        assert "ai_hint" not in classified["line_items"][2]
        assert "ai_hint_heuristic" in trace_steps


class TestAiHintInFormattedResponse:
    """Verify that ai_hint passes through _format_classify_response correctly."""

    def test_ai_hint_preserved_in_line_items(self):
        """ai_hint on a line_item should appear in the formatted response."""
        item = _make_item("空調設備撤去工事", classification="GUIDANCE")
        # Manually add an ai_hint to simulate what _add_ai_hints_for_guidance does
        item["ai_hint"] = {
            "suggestion": schema.EXPENSE_LIKE,
            "suggestion_label": "費用寄り",
            "confidence": 0.6,
            "reasoning": "「撤去」を含むため費用の可能性",
        }
        doc = {
            "version": schema.VERSION,
            "document_info": {"title": "テスト見積書"},
            "line_items": [item],
            "totals": {"total": 100000},
        }

        response = _format_classify_response(doc, trace_steps=["ai_hint_heuristic"])

        # Check that the response line_items contain ai_hint
        assert len(response.line_items) == 1
        resp_item = response.line_items[0]
        assert "ai_hint" in resp_item
        assert resp_item["ai_hint"]["suggestion"] == schema.EXPENSE_LIKE
        assert resp_item["ai_hint"]["suggestion_label"] == "費用寄り"
        assert resp_item["ai_hint"]["confidence"] == 0.6

    def test_no_ai_hint_not_present_in_response(self):
        """When ai_hint is absent, it should not appear in formatted response."""
        item = _make_item("電気工事一式", classification="GUIDANCE")
        doc = {
            "version": schema.VERSION,
            "document_info": {"title": "テスト見積書"},
            "line_items": [item],
            "totals": {"total": 100000},
        }

        response = _format_classify_response(doc, trace_steps=[])

        assert len(response.line_items) == 1
        resp_item = response.line_items[0]
        assert "ai_hint" not in resp_item

    def test_full_roundtrip_heuristic_to_format(self):
        """End-to-end: heuristic adds hint, then _format_classify_response preserves it."""
        item = _make_item("新設サーバー機器", classification="GUIDANCE")
        classified = {
            "version": schema.VERSION,
            "document_info": {"title": "テスト見積書"},
            "line_items": [item],
            "totals": {"total": 100000},
        }
        trace_steps = []

        with patch("api.main.GEMINI_ENABLED", False), \
             patch("api.main.GEMINI_AVAILABLE", False):
            _add_ai_hints_for_guidance(classified, trace_steps)

        # Verify hint was added by heuristic
        assert item["ai_hint"]["suggestion"] == schema.CAPITAL_LIKE

        # Now format
        response = _format_classify_response(classified, trace_steps=trace_steps)

        resp_item = response.line_items[0]
        assert resp_item["ai_hint"]["suggestion"] == schema.CAPITAL_LIKE
        assert resp_item["ai_hint"]["suggestion_label"] == "資産寄り"
        assert "ai_hint_heuristic" in response.trace
