#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デモPDFのEnd-to-Endテストスクリプト（デバッグ版）
APIレスポンスの詳細を表示して問題を特定する
"""

import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests がインストールされていません")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).parent.parent
DEMO_PDF_DIR = PROJECT_ROOT / "data" / "demo_pdf"

API_URL = "https://fixed-asset-agentic-api-vpq2oosrfq-an.a.run.app/classify_pdf"


def test_pdf(filename: str):
    """PDFをAPIに送信し、詳細レスポンスを表示"""
    pdf_path = DEMO_PDF_DIR / filename

    print(f"\n{'='*60}")
    print(f"Testing: {filename}")
    print(f"{'='*60}")

    if not pdf_path.exists():
        print(f"ERROR: ファイルが存在しません")
        return

    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(API_URL, files=files, timeout=60)

        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            print(response.text)
            return

        data = response.json()

        print(f"\n【判定結果】: {data.get('decision')}")
        print(f"【確信度】: {data.get('confidence')}")

        print(f"\n【判定理由 (reasons)】:")
        for i, reason in enumerate(data.get('reasons', [])[:5]):
            print(f"  {i+1}. {reason}")

        print(f"\n【フラグ】:")
        # evidenceからflagsを抽出
        for ev in data.get('evidence', [])[:3]:
            line_no = ev.get('line_no', '?')
            desc = ev.get('description', '')[:30]
            print(f"  Line {line_no}: {desc}")
            # flagsは通常line_items経由だが、evidenceにtax_rulesがある
            tax_rules = ev.get('tax_rules', [])
            if tax_rules:
                for tr in tax_rules:
                    print(f"    - {tr}")

        print(f"\n【missing_fields】:")
        for mf in data.get('missing_fields', []):
            print(f"  - {mf}")

        print(f"\n【trace】: {' → '.join(data.get('trace', []))}")

        # 問題特定: なぜGUIDANCEになったか
        reasons = data.get('reasons', [])
        if 'flag: no_keywords' in reasons:
            print("\n⚠️ 問題: キーワードが見つからなかった (no_keywords)")
        if any('mixed_keyword' in r for r in reasons):
            print("\n⚠️ 問題: 混合キーワード (一式, 撤去等) が検出された")
        if any('tax_rule' in str(r) for r in reasons):
            print("\n⚠️ 問題: 税ルールによりGUIDANCEに変更された")

    except Exception as e:
        print(f"ERROR: {e}")


def main():
    print("デモPDF APIレスポンス詳細分析")

    test_pdf("demo_capital.pdf")
    test_pdf("demo_expense.pdf")
    test_pdf("demo_guidance.pdf")
    test_pdf("demo_capital2.pdf")


if __name__ == "__main__":
    main()
