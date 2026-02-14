# -*- coding: utf-8 -*-
"""End-to-end pipeline tests for core/pipeline.py.

External API calls (Gemini / Document AI) are mocked so tests run offline.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.adapter import adapt_opal_to_v1
from core.classifier import classify_document
from core.policy import load_policy
from core import schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_opal(line_items, **kwargs):
    """Build a minimal OPAL-like dict for testing."""
    base = {
        "invoice_date": "2024-06-01",
        "vendor": "テスト商事",
        "subtotal_amount": None,
        "tax_amount": None,
        "total_amount": None,
        "line_items": line_items,
    }
    base.update(kwargs)
    return base


def _run_classify_pipeline(opal, policy_path=None):
    """Simulate the core pipeline: adapt → load_policy → classify."""
    normalized = adapt_opal_to_v1(opal)
    policy = load_policy(policy_path)
    classified = classify_document(normalized, policy)
    return classified


# ---------------------------------------------------------------------------
# E2E test 1: Full invoice with mixed line items
# ---------------------------------------------------------------------------
class TestE2EFullInvoice:
    def test_mixed_invoice_classification(self):
        """複数明細行の見積書をパイプラインに通し、各行が正しく分類される"""
        opal = _make_opal(
            line_items=[
                {"item_description": "空調設備新設工事", "amount": 800_000, "quantity": 1},
                {"item_description": "年間保守契約", "amount": 60_000, "quantity": 1},
                {"item_description": "消耗品費", "amount": 5_000, "quantity": 10},
                {"item_description": "設備一式", "amount": 300_000, "quantity": 1},
            ],
            total_amount=1_165_000,
        )

        result = _run_classify_pipeline(opal)

        assert result["version"] == schema.VERSION
        assert len(result["line_items"]) == 4

        items = result["line_items"]

        # Line 1: 新設 → CAPITAL keyword, 60万以上の税ルールはフラグのみ（キーワード判定を上書きしない）
        assert items[0]["classification"] == schema.CAPITAL_LIKE
        assert any("tax_rule:R-AMOUNT-600k" in f for f in items[0]["flags"])

        # Line 2: 保守+契約 → EXPENSE_LIKE, 10万未満 → no tax override
        assert items[1]["classification"] == schema.EXPENSE_LIKE

        # Line 3: 消耗品 → EXPENSE_LIKE, amount=5000 (per unit) → under 10万
        assert items[2]["classification"] == schema.EXPENSE_LIKE

        # Line 4: 一式 → mixed keyword → GUIDANCE
        assert items[3]["classification"] == schema.GUIDANCE
        assert any("mixed_keyword" in f for f in items[3]["flags"])

        # All items have required fields
        for item in items:
            assert "classification" in item
            assert "label_ja" in item
            assert "confidence" in item
            assert "flags" in item
            assert isinstance(item["flags"], list)


# ---------------------------------------------------------------------------
# E2E test 2: Policy override pipeline
# ---------------------------------------------------------------------------
class TestE2EPolicyOverride:
    def test_policy_forces_guidance_via_regex(self, tmp_path):
        """ポリシーJSONを使って regex.always_guidance でGUIDANCEに強制できる"""
        policy_data = {
            "keywords": {"asset_add": [], "expense_add": [], "guidance_add": []},
            "thresholds": {"guidance_amount_jpy": None},
            "regex": {"always_guidance": "リース"},
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy_data), encoding="utf-8")

        opal = _make_opal(
            line_items=[
                {"item_description": "サーバーリース更新", "amount": 50_000, "quantity": 1},
            ]
        )

        result = _run_classify_pipeline(opal, policy_path=str(policy_file))

        item = result["line_items"][0]
        assert item["classification"] == schema.GUIDANCE
        assert any("policy:always_guidance" in f for f in item["flags"])


# ---------------------------------------------------------------------------
# E2E test 3: Empty / edge-case inputs
# ---------------------------------------------------------------------------
class TestE2EEdgeCases:
    def test_empty_line_items(self):
        """明細行が空のOPALでもパイプラインがクラッシュしない"""
        opal = _make_opal(line_items=[])
        result = _run_classify_pipeline(opal)
        assert result["version"] == schema.VERSION
        assert result["line_items"] == []

    def test_none_opal(self):
        """None入力でもパイプラインがクラッシュしない"""
        result = _run_classify_pipeline(None)
        assert result["version"] == schema.VERSION
        assert result["line_items"] == []

    def test_item_with_none_description(self):
        """descriptionがNoneの明細行でもクラッシュしない"""
        opal = _make_opal(
            line_items=[{"description": None, "amount": 50_000}]
        )
        result = _run_classify_pipeline(opal)
        assert len(result["line_items"]) == 1
        assert result["line_items"][0]["classification"] == schema.GUIDANCE

    def test_item_with_none_amount(self):
        """amountがNoneの明細行でもクラッシュしない"""
        opal = _make_opal(
            line_items=[{"item_description": "サーバー設置", "amount": None}]
        )
        result = _run_classify_pipeline(opal)
        item = result["line_items"][0]
        # 設置キーワード → CAPITAL_LIKE, amount=None → no tax rule override
        assert item["classification"] == schema.CAPITAL_LIKE

    def test_non_dict_line_item_skipped(self):
        """明細がdictでない場合もクラッシュしない（adapterでデフォルト値が入る）"""
        opal = _make_opal(line_items=["string item", 12345])
        result = _run_classify_pipeline(opal)
        assert len(result["line_items"]) == 2
        # Both get default empty description → GUIDANCE (no_keywords)
        for item in result["line_items"]:
            assert item["classification"] == schema.GUIDANCE


# ---------------------------------------------------------------------------
# E2E test 4: PDF pipeline with mocked extract_pdf
# ---------------------------------------------------------------------------
class TestE2EPdfPipeline:
    @patch("core.pipeline.extract_pdf")
    @patch("core.pipeline.extraction_to_opal")
    def test_pdf_pipeline_mocked(self, mock_extraction_to_opal, mock_extract_pdf, tmp_path):
        """PDF パイプラインの統合テスト（extract_pdf をモックして外部API回避）"""
        from core.pipeline import run_pdf_pipeline

        # Mock extract_pdf to return a fake extraction result
        mock_extract_pdf.return_value = {
            "pages": [{"text": "テスト見積書\nサーバー設置工事 500,000円"}],
            "meta": {"warnings": ["test_warning"]},
        }

        # Mock extraction_to_opal to return OPAL format
        mock_extraction_to_opal.return_value = {
            "invoice_date": "2024-01-15",
            "vendor": "テスト設備株式会社",
            "line_items": [
                {"item_description": "サーバー設置工事", "amount": 500_000, "quantity": 1}
            ],
            "total_amount": 500_000,
        }

        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 dummy")

        results_dir = tmp_path / "results"
        results_dir.mkdir()

        result = run_pdf_pipeline(pdf_file, results_dir)

        assert "final_doc" in result
        final = result["final_doc"]
        assert final["version"] == schema.VERSION
        assert len(final["line_items"]) == 1
        assert final["line_items"][0]["classification"] in (
            schema.CAPITAL_LIKE,
            schema.EXPENSE_LIKE,
            schema.GUIDANCE,
        )
        assert "warnings" in final
        assert "test_warning" in final["warnings"]

        # Verify files were saved
        assert result["extraction_path"].exists()
        assert result["final_path"].exists()

        mock_extract_pdf.assert_called_once()
        mock_extraction_to_opal.assert_called_once()


# ---------------------------------------------------------------------------
# E2E test 5: Multi-item individual classification (cmd_040 / case11)
# ---------------------------------------------------------------------------
class TestE2EMultiItemClassification:
    def test_multi_item_individual_classification(self):
        """4明細入力 → classify_document() → 4件のline_items各々にclassificationがある。
        各明細は個別金額に基づいて判定される（合計金額ではない）。"""
        opal = _make_opal(
            line_items=[
                {"item_description": "サーバー機器新設工事", "amount": 400_000, "quantity": 1},
                {"item_description": "ネットワーク設備設置工事", "amount": 300_000, "quantity": 1},
                {"item_description": "セキュリティシステム導入", "amount": 200_000, "quantity": 1},
                {"item_description": "インフラ基盤構築作業", "amount": 100_000, "quantity": 1},
            ],
            total_amount=1_000_000,
        )

        result = _run_classify_pipeline(opal)

        assert result["version"] == schema.VERSION
        assert len(result["line_items"]) == 4

        items = result["line_items"]

        # All items must have classification and required fields
        for item in items:
            assert "classification" in item
            assert item["classification"] in (schema.CAPITAL_LIKE, schema.EXPENSE_LIKE, schema.GUIDANCE)
            assert "confidence" in item
            assert "flags" in item
            assert "label_ja" in item
            assert isinstance(item["flags"], list)

        # Key assertion: each item is classified based on INDIVIDUAL amount, NOT total (1M).
        # Items 1 & 2 (400K, 300K) have CAPITAL keywords and amount in 200K-600K range
        #   → tax rule R-AMOUNT-001 with suggests_guidance=False → stays CAPITAL_LIKE
        assert items[0]["classification"] == schema.CAPITAL_LIKE  # 新設 400K
        assert items[1]["classification"] == schema.CAPITAL_LIKE  # 設置 300K

        # If total (1M) were used, ALL items would get R-AMOUNT-600k (guidance override).
        # Items 1 & 2 being CAPITAL_LIKE proves individual-amount classification.
        # Items 3 & 4: キーワード判定(導入/構築=CAPITAL)は税ルールで上書きされない
        assert items[2]["classification"] == schema.CAPITAL_LIKE  # 導入 200K → keyword wins
        assert items[3]["classification"] == schema.CAPITAL_LIKE  # 構築 100K → keyword wins

        # Verify NO item was classified using total_amount (1M → R-AMOUNT-600k)
        for item in items:
            assert not any("R-AMOUNT-600k" in f for f in item["flags"]), \
                f"Item '{item['description']}' should not have R-AMOUNT-600k flag (total-based)"


# ---------------------------------------------------------------------------
# E2E test 6: Subtotal/Tax/Total rows excluded (cmd_040 / case12)
# ---------------------------------------------------------------------------
class TestE2ESubtotalExclusion:
    def test_subtotal_tax_total_excluded(self):
        """7行（4明細+小計+消費税+合計）入力 → adapter → 4明細のみ分類対象。
        小計・消費税・合計行はadapterでフィルタされる。"""
        opal = _make_opal(
            line_items=[
                {"item_description": "空調設備設置工事", "amount": 450_000, "quantity": 1},
                {"item_description": "電気配線工事", "amount": 250_000, "quantity": 1},
                {"item_description": "防火設備導入", "amount": 180_000, "quantity": 1},
                {"item_description": "現場管理費", "amount": 120_000, "quantity": 1},
                {"item_description": "小計", "amount": 1_000_000, "quantity": 1},
                {"item_description": "消費税", "amount": 100_000, "quantity": 1},
                {"item_description": "合計", "amount": 1_100_000, "quantity": 1},
            ],
            total_amount=1_100_000,
        )

        result = _run_classify_pipeline(opal)

        # Only 4 real line items should remain (summary rows filtered by adapter)
        assert len(result["line_items"]) == 4

        # Verify no summary row descriptions remain in classified items
        descriptions = [item["description"] for item in result["line_items"]]
        for summary_word in ["小計", "消費税", "合計"]:
            assert summary_word not in descriptions, \
                f"Summary row '{summary_word}' should be filtered out by adapter"

        # line_no should be sequential (1-4) after filtering
        line_nos = [item["line_no"] for item in result["line_items"]]
        assert line_nos == [1, 2, 3, 4]

        # All remaining items should have valid classifications
        for item in result["line_items"]:
            assert item["classification"] in (schema.CAPITAL_LIKE, schema.EXPENSE_LIKE, schema.GUIDANCE)


# ---------------------------------------------------------------------------
# E2E test 7: Mixed CAPITAL/EXPENSE classification (cmd_040 / case13)
# ---------------------------------------------------------------------------
class TestE2EMixedCapitalExpense:
    def test_mixed_capital_expense_decision(self):
        """CAPITAL+EXPENSE混在の見積書 → 各明細が個別に分類され、混在が検出される。"""
        opal = _make_opal(
            line_items=[
                {"item_description": "サーバー設置工事", "amount": 500_000, "quantity": 1},
                {"item_description": "年間保守契約", "amount": 50_000, "quantity": 1},
                {"item_description": "消耗品", "amount": 5_000, "quantity": 1},
            ],
            total_amount=555_000,
        )

        result = _run_classify_pipeline(opal)

        assert len(result["line_items"]) == 3

        items = result["line_items"]

        # Item 1: サーバー設置工事 500K → "設置" CAPITAL keyword
        #   500K in 200K-600K range → R-AMOUNT-001 (suggests_guidance=False) → CAPITAL_LIKE
        assert items[0]["classification"] == schema.CAPITAL_LIKE

        # Item 2: 年間保守契約 50K → "年間","保守" EXPENSE keywords
        #   50K < 100K → R-AMOUNT-003 (suggests_guidance=False) → EXPENSE_LIKE
        assert items[1]["classification"] == schema.EXPENSE_LIKE

        # Item 3: 消耗品 5K → "消耗品" EXPENSE keyword
        #   5K < 100K → R-AMOUNT-003 (suggests_guidance=False) → EXPENSE_LIKE
        assert items[2]["classification"] == schema.EXPENSE_LIKE

        # Mixed classifications exist in the same document
        classifications = {item["classification"] for item in items}
        assert schema.CAPITAL_LIKE in classifications
        assert schema.EXPENSE_LIKE in classifications
        assert len(classifications) >= 2, "Document should contain mixed classification types"
