# -*- coding: utf-8 -*-
"""Unit tests for core/adapter.py"""
import pytest

from core.adapter import (
    _get_first,
    _normalize_vendor,
    _to_quantity_str,
    _safe_number,
    _normalize_evidence,
    _is_summary_row,
    _build_line_items,
    adapt_opal_to_v1,
)
from core import schema


# ---------------------------------------------------------------------------
# _get_first
# ---------------------------------------------------------------------------
class TestGetFirst:
    def test_returns_first_matching_key(self):
        data = {"a": None, "b": "hello", "c": "world"}
        assert _get_first(data, ["a", "b", "c"]) == "hello"

    def test_returns_default_when_no_match(self):
        data = {"a": None, "b": ""}
        assert _get_first(data, ["a", "b"], default="fallback") == "fallback"

    def test_returns_default_for_empty_dict(self):
        assert _get_first({}, ["x"], default=42) == 42

    def test_returns_none_default_when_keys_missing(self):
        assert _get_first({"a": 1}, ["z"]) is None


# ---------------------------------------------------------------------------
# _normalize_vendor
# ---------------------------------------------------------------------------
class TestNormalizeVendor:
    def test_none_returns_none(self):
        assert _normalize_vendor(None) is None

    def test_blank_string_returns_none(self):
        assert _normalize_vendor("   ") is None

    def test_empty_string_returns_none(self):
        assert _normalize_vendor("") is None

    def test_valid_vendor_passes_through(self):
        assert _normalize_vendor("ACME Corp") == "ACME Corp"

    def test_numeric_vendor_passes_through(self):
        assert _normalize_vendor(123) == 123


# ---------------------------------------------------------------------------
# _to_quantity_str
# ---------------------------------------------------------------------------
class TestToQuantityStr:
    def test_none_returns_empty(self):
        assert _to_quantity_str(None) == ""

    def test_integer(self):
        assert _to_quantity_str(5) == "5"

    def test_whole_float(self):
        assert _to_quantity_str(3.0) == "3"

    def test_fractional_float(self):
        assert _to_quantity_str(2.5) == "2.5"

    def test_string_stripped(self):
        assert _to_quantity_str("  10  ") == "10"


# ---------------------------------------------------------------------------
# _safe_number
# ---------------------------------------------------------------------------
class TestSafeNumber:
    def test_int_passes(self):
        assert _safe_number(100) == 100

    def test_float_passes(self):
        assert _safe_number(99.9) == 99.9

    def test_string_returns_none(self):
        assert _safe_number("100") is None

    def test_none_returns_none(self):
        assert _safe_number(None) is None

    def test_bool_passes_as_int_subclass(self):
        # bool is subclass of int in Python; _safe_number does not reject it
        assert _safe_number(True) is True


# ---------------------------------------------------------------------------
# _normalize_evidence
# ---------------------------------------------------------------------------
class TestNormalizeEvidence:
    def test_none_raw_uses_description(self):
        result = _normalize_evidence(None, "desc text")
        assert result["source_text"] == "desc text"
        assert result["position_hint"] == ""

    def test_dict_preserves_existing(self):
        raw = {"source_text": "original", "position_hint": "p1"}
        result = _normalize_evidence(raw, "fallback")
        assert result["source_text"] == "original"
        assert result["position_hint"] == "p1"

    def test_dict_fills_missing_source_text(self):
        raw = {"position_hint": "top"}
        result = _normalize_evidence(raw, "desc")
        assert result["source_text"] == "desc"
        assert result["position_hint"] == "top"

    def test_empty_source_text_replaced(self):
        raw = {"source_text": ""}
        result = _normalize_evidence(raw, "fallback")
        assert result["source_text"] == "fallback"


# ---------------------------------------------------------------------------
# _build_line_items
# ---------------------------------------------------------------------------
class TestBuildLineItems:
    def test_non_list_returns_empty(self):
        assert _build_line_items("not a list") == []
        assert _build_line_items(None) == []

    def test_basic_item(self):
        items = [{"item_description": "server", "amount": 5000, "quantity": 2}]
        result = _build_line_items(items)
        assert len(result) == 1
        assert result[0]["line_no"] == 1
        assert result[0]["description"] == "server"
        assert result[0]["quantity"] == "2"
        assert result[0]["amount"] == 5000
        assert result[0]["classification"] is None

    def test_multiple_items_sequential_line_no(self):
        items = [{"description": "a"}, {"description": "b"}, {"description": "c"}]
        result = _build_line_items(items)
        assert [r["line_no"] for r in result] == [1, 2, 3]

    def test_non_dict_item_produces_defaults(self):
        items = ["just a string"]
        result = _build_line_items(items)
        assert len(result) == 1
        assert result[0]["description"] == ""
        assert result[0]["amount"] is None

    def test_empty_list(self):
        assert _build_line_items([]) == []


# ---------------------------------------------------------------------------
# adapt_opal_to_v1
# ---------------------------------------------------------------------------
class TestAdaptOpalToV1:
    def test_full_opal(self):
        opal = {
            "invoice_date": "2024-01-15",
            "vendor": "テスト株式会社",
            "subtotal_amount": 10000,
            "tax_amount": 1000,
            "total_amount": 11000,
            "line_items": [
                {"item_description": "サーバー設置", "amount": 10000, "quantity": 1}
            ],
        }
        result = adapt_opal_to_v1(opal)
        assert result["version"] == schema.VERSION
        assert result["document_info"]["date"] == "2024-01-15"
        assert result["document_info"]["vendor"] == "テスト株式会社"
        assert result["totals"]["subtotal"] == 10000
        assert result["totals"]["tax"] == 1000
        assert result["totals"]["total"] == 11000
        assert len(result["line_items"]) == 1

    def test_none_input(self):
        result = adapt_opal_to_v1(None)
        assert result["version"] == schema.VERSION
        assert result["document_info"]["vendor"] is None
        assert result["line_items"] == []

    def test_empty_dict(self):
        result = adapt_opal_to_v1({})
        assert result["version"] == schema.VERSION
        assert result["document_info"]["title"] == "見積書"
        assert result["line_items"] == []

    def test_vendor_blank_normalized(self):
        opal = {"vendor": "  "}
        result = adapt_opal_to_v1(opal)
        assert result["document_info"]["vendor"] is None

    def test_line_items_none_treated_as_empty(self):
        opal = {"line_items": None}
        result = adapt_opal_to_v1(opal)
        assert result["line_items"] == []


# ---------------------------------------------------------------------------
# _is_summary_row
# ---------------------------------------------------------------------------
class TestIsSummaryRow:
    def test_subtotal(self):
        assert _is_summary_row("小計") is True

    def test_tax(self):
        assert _is_summary_row("消費税") is True

    def test_total(self):
        assert _is_summary_row("合計") is True

    def test_tax_included_total(self):
        assert _is_summary_row("税込合計") is True

    def test_tax_excluded_total(self):
        assert _is_summary_row("税抜合計") is True

    def test_discount(self):
        assert _is_summary_row("値引") is True

    def test_discount2(self):
        assert _is_summary_row("割引") is True

    def test_special_discount(self):
        assert _is_summary_row("出精値引") is True

    def test_normal_item(self):
        assert _is_summary_row("サーバー設置工事") is False

    def test_item_containing_keyword(self):
        # "合計" at start triggers filter, but "小計" in the middle does not
        assert _is_summary_row("小計額の確認") is True
        assert _is_summary_row("工事の合計") is False

    def test_whitespace_stripped(self):
        assert _is_summary_row("  小計  ") is True


# ---------------------------------------------------------------------------
# _build_line_items — Summary row filtering
# ---------------------------------------------------------------------------
class TestBuildLineItemsFilter:
    def test_filter_subtotal_rows(self):
        items = [
            {"item_description": "サーバー設置", "amount": 100000},
            {"item_description": "小計", "amount": 100000},
        ]
        result = _build_line_items(items)
        assert len(result) == 1
        assert result[0]["description"] == "サーバー設置"

    def test_filter_tax_rows(self):
        items = [
            {"item_description": "空調設備", "amount": 500000},
            {"item_description": "消費税", "amount": 50000},
        ]
        result = _build_line_items(items)
        assert len(result) == 1
        assert result[0]["description"] == "空調設備"

    def test_filter_total_rows(self):
        items = [
            {"item_description": "配管工事", "amount": 300000},
            {"item_description": "合計", "amount": 330000},
        ]
        result = _build_line_items(items)
        assert len(result) == 1
        assert result[0]["description"] == "配管工事"

    def test_keep_normal_items(self):
        items = [
            {"item_description": "サーバー新設", "amount": 800000},
            {"item_description": "設置工事", "amount": 200000},
            {"item_description": "保守契約", "amount": 50000},
        ]
        result = _build_line_items(items)
        assert len(result) == 3
        assert [r["description"] for r in result] == [
            "サーバー新設", "設置工事", "保守契約"
        ]

    def test_mixed_filter(self):
        """4 normal items + subtotal + tax + total → only 4 items remain."""
        items = [
            {"item_description": "サーバー本体", "amount": 500000},
            {"item_description": "設置工事費", "amount": 200000},
            {"item_description": "撤去費", "amount": 50000},
            {"item_description": "運搬費", "amount": 30000},
            {"item_description": "小計", "amount": 780000},
            {"item_description": "消費税", "amount": 78000},
            {"item_description": "合計", "amount": 858000},
        ]
        result = _build_line_items(items)
        assert len(result) == 4
        assert [r["description"] for r in result] == [
            "サーバー本体", "設置工事費", "撤去費", "運搬費"
        ]
        # Verify sequential line_no after filtering
        assert [r["line_no"] for r in result] == [1, 2, 3, 4]
