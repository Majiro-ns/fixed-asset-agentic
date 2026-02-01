#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""複数書類を1つのPDFに結合するスクリプト"""
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDFが必要です: pip install PyMuPDF")
    sys.exit(1)


def merge_pdfs(input_paths: list, output_path: str) -> None:
    """複数のPDFを1つに結合"""
    merged = fitz.open()

    for path in input_paths:
        if not Path(path).exists():
            print(f"警告: {path} が見つかりません、スキップします")
            continue

        doc = fitz.open(path)
        merged.insert_pdf(doc)
        doc.close()
        print(f"追加: {path} ({merged.page_count}ページ)")

    merged.save(output_path)
    merged.close()
    print(f"\n結合完了: {output_path} (全{fitz.open(output_path).page_count}ページ)")


def main():
    # プロジェクトルート
    root = Path(__file__).resolve().parent.parent
    demo_dir = root / "data" / "demo_pdf"
    output_path = demo_dir / "demo_multi_documents.pdf"

    # 結合するPDF（見積書 + 請求書 + 経費）
    input_pdfs = [
        demo_dir / "demo_capital.pdf",    # 見積書（資産）
        demo_dir / "demo_expense.pdf",    # 見積書（経費）
        demo_dir / "demo_guidance.pdf",   # 見積書（要確認）
    ]

    print("=== 複数書類PDF作成 ===")
    print(f"入力: {len(input_pdfs)}ファイル")

    merge_pdfs([str(p) for p in input_pdfs], str(output_path))


if __name__ == "__main__":
    main()
