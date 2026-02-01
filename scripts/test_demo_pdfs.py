#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デモPDFのEnd-to-Endテストスクリプト

使い方:
    cd C:/Users/owner/Desktop/fixed-asset-ashigaru
    python scripts/test_demo_pdfs.py

このスクリプトは以下を確認する:
1. PyMuPDFでテキスト抽出できるか
2. 抽出されたテキストに判定キーワードが含まれるか
3. Cloud Run APIで正しい判定結果が返るか
"""

import os
import sys
from pathlib import Path

# PyMuPDFのインポート
try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF がインストールされていません")
    print("pip install pymupdf を実行してください")
    sys.exit(1)

# requestsのインポート
try:
    import requests
except ImportError:
    print("ERROR: requests がインストールされていません")
    print("pip install requests を実行してください")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).parent.parent
DEMO_PDF_DIR = PROJECT_ROOT / "data" / "demo_pdf"

# Cloud Run API URL
API_URL = "https://fixed-asset-agentic-api-vpq2oosrfq-an.a.run.app/classify_pdf"

# 期待される判定結果とキーワード
EXPECTED_RESULTS = {
    "demo_capital.pdf": {
        "decision": "CAPITAL_LIKE",
        "keywords": ["新設", "設置", "導入", "構築"],
    },
    "demo_expense.pdf": {
        "decision": "EXPENSE_LIKE",
        "keywords": ["保守", "点検", "修理", "調整", "清掃"],
    },
    "demo_guidance.pdf": {
        "decision": "GUIDANCE",
        "keywords": ["既設", "撤去", "移設"],
    },
    "demo_capital2.pdf": {
        "decision": "CAPITAL_LIKE",
        "keywords": ["購入", "整備"],
    },
}


def test_pdf_text_extraction(pdf_path: Path) -> tuple[bool, str, list]:
    """PDFからテキスト抽出をテスト"""
    try:
        doc = fitz.open(str(pdf_path))
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        # テキストが空でないか
        if not full_text.strip():
            return False, "(empty)", []

        # 日本語が含まれているか（文字化けしていないか）
        has_japanese = any('\u3040' <= c <= '\u309f' or  # ひらがな
                          '\u30a0' <= c <= '\u30ff' or  # カタカナ
                          '\u4e00' <= c <= '\u9fff'     # 漢字
                          for c in full_text)

        return has_japanese, full_text[:300], []

    except Exception as e:
        return False, f"Error: {e}", []


def test_keywords_in_text(text: str, keywords: list) -> list:
    """テキストにキーワードが含まれているか確認"""
    found = []
    for kw in keywords:
        if kw in text:
            found.append(kw)
    return found


def test_api_classification(pdf_path: Path) -> tuple[str, float]:
    """Cloud Run APIで判定テスト"""
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(API_URL, files=files, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return data.get("decision", "UNKNOWN"), data.get("confidence", 0.0)
        else:
            return f"HTTP {response.status_code}", 0.0

    except Exception as e:
        return f"Error: {e}", 0.0


def main():
    print("=" * 60)
    print("デモPDF End-to-End テスト")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    for filename, expected in EXPECTED_RESULTS.items():
        pdf_path = DEMO_PDF_DIR / filename
        print(f"Testing: {filename}")
        print("-" * 40)

        if not pdf_path.exists():
            print(f"  ERROR: ファイルが存在しません")
            all_passed = False
            results.append((filename, "FILE_NOT_FOUND", False))
            print()
            continue

        # 1. テキスト抽出テスト
        has_japanese, text_preview, _ = test_pdf_text_extraction(pdf_path)
        print(f"  テキスト抽出: {'OK (日本語あり)' if has_japanese else 'NG (日本語なし/文字化け)'}")
        if not has_japanese:
            print(f"    抽出結果: {text_preview[:100]}...")

        # 2. キーワードテスト
        if has_japanese:
            doc = fitz.open(str(pdf_path))
            full_text = "".join(page.get_text() for page in doc)
            doc.close()
            found_keywords = test_keywords_in_text(full_text, expected["keywords"])
            print(f"  キーワード: {found_keywords if found_keywords else 'なし'}")
            print(f"    期待: {expected['keywords']}")

        # 3. API判定テスト
        print(f"  API判定中...")
        actual_decision, confidence = test_api_classification(pdf_path)
        expected_decision = expected["decision"]

        match = actual_decision == expected_decision
        status = "PASS" if match else "FAIL"

        print(f"  API結果: {actual_decision} (確信度: {confidence:.2f})")
        print(f"  期待値:  {expected_decision}")
        print(f"  判定:    {status}")

        if not match:
            all_passed = False

        results.append((filename, actual_decision, match))
        print()

    # サマリー
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for filename, decision, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {filename}: {decision} {status}")

    print()
    if all_passed:
        print("🎉 全テストPASS - デモPDFは正常に動作します")
    else:
        print("⚠️ テスト失敗あり - PDFの再生成または修正が必要です")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
