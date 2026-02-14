# -*- coding: utf-8 -*-
"""Unit tests for core/classifier.py – keyword matching, tax-law rules, and confidence."""
import pytest

from core import schema
from core.adapter import adapt_opal_to_v1
from core.classifier import (
    _find_keywords,
    _merge_keywords,
    _safe_policy,
    _append_flag,
    _apply_tax_rules,
    _calculate_confidence,
    classify_line_item,
    classify_document,
)


# ---------------------------------------------------------------------------
# Tax-law rule tests (10万/20万/30万/60万 thresholds)
# ---------------------------------------------------------------------------
class TestApplyTaxRules:
    def test_below_100k_expense_possible(self):
        """10万円未満: 少額固定資産として費用処理可能"""
        rules = _apply_tax_rules(50_000)
        assert len(rules) == 1
        assert rules[0]["rule_id"] == "R-AMOUNT-003"
        assert rules[0]["suggests_guidance"] is False

    def test_100k_to_200k_guidance(self):
        """10万円以上20万円未満: 3年一括償却の確認が必要 → GUIDANCE"""
        rules = _apply_tax_rules(150_000)
        assert any(r["rule_id"] == "R-AMOUNT-100k200k" for r in rules)
        assert all(r["suggests_guidance"] is True for r in rules)

    def test_200k_to_300k_two_rules(self):
        """20万円以上30万円未満: 一括償却資産 + 中小企業特例"""
        rules = _apply_tax_rules(250_000)
        rule_ids = [r["rule_id"] for r in rules]
        assert "R-AMOUNT-001" in rule_ids
        assert "R-AMOUNT-SME300k" in rule_ids

    def test_300k_to_600k(self):
        """30万円以上60万円未満: 一括償却資産の取扱い"""
        rules = _apply_tax_rules(400_000)
        assert rules[0]["rule_id"] == "R-AMOUNT-001"
        assert rules[0]["suggests_guidance"] is False

    def test_above_600k_guidance(self):
        """60万円以上: 修繕費vs資本的支出の判定には追加情報が必要"""
        rules = _apply_tax_rules(700_000)
        assert rules[0]["rule_id"] == "R-AMOUNT-600k"
        assert rules[0]["suggests_guidance"] is True

    def test_zero_amount_returns_empty(self):
        assert _apply_tax_rules(0) == []

    def test_negative_amount_returns_empty(self):
        assert _apply_tax_rules(-100) == []

    def test_none_amount_returns_empty(self):
        assert _apply_tax_rules(None) == []

    def test_string_amount_returns_empty(self):
        assert _apply_tax_rules("50000") == []


# ---------------------------------------------------------------------------
# Keyword classification logic
# ---------------------------------------------------------------------------
class TestClassifyLineItem:
    def test_capital_keyword_detected(self):
        """資産キーワード（設置）がある場合 → CAPITAL_LIKE"""
        item = {"description": "サーバー設置工事", "amount": 500_000}
        result = classify_line_item(item)
        assert result["classification"] == schema.CAPITAL_LIKE

    def test_expense_keyword_detected(self):
        """費用キーワード（保守）がある場合 → EXPENSE_LIKE"""
        item = {"description": "年間保守契約", "amount": 50_000}
        result = classify_line_item(item)
        assert result["classification"] == schema.EXPENSE_LIKE

    def test_mixed_keyword_forces_guidance(self):
        """混在キーワード（一式）がある場合 → GUIDANCE"""
        item = {"description": "機器一式", "amount": 100_000}
        result = classify_line_item(item)
        assert result["classification"] == schema.GUIDANCE
        assert any("mixed_keyword" in f for f in result["flags"])

    def test_conflicting_keywords_guidance(self):
        """資産+費用の両方のキーワードがある場合 → GUIDANCE"""
        item = {"description": "空調設置および保守", "amount": 300_000}
        result = classify_line_item(item)
        assert result["classification"] == schema.GUIDANCE
        assert "conflicting_keywords" in result["flags"]

    def test_no_keywords_guidance(self):
        """キーワードなし → GUIDANCE"""
        item = {"description": "その他", "amount": 50_000}
        result = classify_line_item(item)
        assert result["classification"] == schema.GUIDANCE
        assert "no_keywords" in result["flags"]

    def test_evidence_source_text_used_for_matching(self):
        """evidence.source_text からもキーワードが検出される"""
        item = {
            "description": "不明な項目",
            "amount": 50_000,
            "evidence": {"source_text": "新設工事費用"},
        }
        result = classify_line_item(item)
        assert result["classification"] == schema.CAPITAL_LIKE

    def test_tax_rule_does_not_override_keyword_match(self):
        """キーワード判定済みの場合、税ルールでGUIDANCEに上書きしない"""
        item = {"description": "サーバー購入", "amount": 150_000}
        result = classify_line_item(item)
        # 購入 → CAPITAL_LIKE keyword: 税ルール(10万-20万)はフラグのみ追加、上書きしない
        assert result["classification"] == schema.CAPITAL_LIKE
        assert any("tax_rule:" in f for f in result["flags"])

    def test_confidence_field_present(self):
        """確信度が結果に含まれる"""
        item = {"description": "サーバー設置", "amount": 50_000}
        result = classify_line_item(item)
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_label_ja_set(self):
        """日本語ラベルが設定される"""
        item = {"description": "保守点検", "amount": 30_000}
        result = classify_line_item(item)
        assert result["label_ja"] == "費用寄り"


# ---------------------------------------------------------------------------
# Policy overrides
# ---------------------------------------------------------------------------
class TestPolicyOverrides:
    def test_policy_guidance_keyword(self):
        """ポリシーのguidance_addキーワードで強制GUIDANCE"""
        policy = {"keywords": {"guidance_add": ["特注"]}, "thresholds": {}, "regex": {}}
        item = {"description": "特注サーバー設置", "amount": 50_000}
        result = classify_line_item(item, policy=policy)
        assert result["classification"] == schema.GUIDANCE

    def test_policy_regex_always_guidance(self):
        """ポリシーのregex.always_guidanceでGUIDANCEに強制"""
        policy = {"keywords": {}, "thresholds": {}, "regex": {"always_guidance": "リース"}}
        item = {"description": "リース契約更新", "amount": 50_000}
        result = classify_line_item(item, policy=policy)
        assert result["classification"] == schema.GUIDANCE
        assert any("policy:always_guidance" in f for f in result["flags"])

    def test_policy_amount_threshold_flag(self):
        """ポリシーの金額閾値を超えるGUIDANCEアイテムにフラグ付与"""
        policy = {"keywords": {}, "thresholds": {"guidance_amount_jpy": 500_000}, "regex": {}}
        item = {"description": "不明品", "amount": 1_000_000}
        result = classify_line_item(item, policy=policy)
        assert "policy:amount_threshold" in result["flags"]


# ---------------------------------------------------------------------------
# classify_document
# ---------------------------------------------------------------------------
class TestClassifyDocument:
    def test_classifies_all_line_items(self):
        doc = adapt_opal_to_v1({
            "line_items": [
                {"item_description": "サーバー設置", "amount": 50_000},
                {"item_description": "年間保守", "amount": 30_000},
            ]
        })
        result = classify_document(doc)
        assert len(result["line_items"]) == 2
        assert all("classification" in item for item in result["line_items"])

    def test_non_dict_doc_returned_as_is(self):
        assert classify_document("not a dict") == "not a dict"

    def test_missing_line_items_returns_doc(self):
        doc = {"version": "v1.0"}
        result = classify_document(doc)
        assert result == doc


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
class TestHelpers:
    def test_find_keywords(self):
        assert _find_keywords("サーバー新設工事", ["新設", "保守"]) == ["新設"]

    def test_find_keywords_no_match(self):
        assert _find_keywords("テスト", ["新設"]) == []

    def test_merge_keywords_dedup(self):
        result = _merge_keywords(["a", "b"], ["b", "c"])
        assert result == ["a", "b", "c"]

    def test_safe_policy_none(self):
        result = _safe_policy(None)
        assert "keywords" in result

    def test_append_flag_dedup(self):
        flags = ["a"]
        _append_flag(flags, "a")
        assert flags == ["a"]
        _append_flag(flags, "b")
        assert flags == ["a", "b"]


# ---------------------------------------------------------------------------
# Confidence calculation
# ---------------------------------------------------------------------------
class TestCalculateConfidence:
    def test_capital_base_confidence(self):
        conf = _calculate_confidence(schema.CAPITAL_LIKE, ["設置"], [], [], [], [])
        assert conf == pytest.approx(0.85)

    def test_capital_bonus(self):
        conf = _calculate_confidence(schema.CAPITAL_LIKE, ["設置", "新設", "購入"], [], [], [], [])
        assert conf == pytest.approx(0.91)

    def test_expense_base_confidence(self):
        conf = _calculate_confidence(schema.EXPENSE_LIKE, [], ["保守"], [], [], [])
        assert conf == pytest.approx(0.85)

    def test_guidance_conflicting(self):
        conf = _calculate_confidence(schema.GUIDANCE, [], [], [], [], ["conflicting_keywords"])
        assert conf == pytest.approx(0.55)

    def test_guidance_no_keywords(self):
        conf = _calculate_confidence(schema.GUIDANCE, [], [], [], [], ["no_keywords"])
        assert conf == pytest.approx(0.40)
