#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APIレスポンスをJSONファイルとして保存するスクリプト
"""

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests を実行してください")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
DEMO_PDF_DIR = PROJECT_ROOT / "data" / "demo_pdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "debug"

API_URL = "https://fixed-asset-agentic-api-vpq2oosrfq-an.a.run.app/classify_pdf"

FILES = [
    "demo_capital.pdf",
    "demo_expense.pdf",
    "demo_guidance.pdf",
    "demo_capital2.pdf",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename in FILES:
        pdf_path = DEMO_PDF_DIR / filename
        if not pdf_path.exists():
            print(f"SKIP: {filename} not found")
            continue

        print(f"Processing: {filename}")

        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                response = requests.post(API_URL, files=files, timeout=60)

            if response.status_code == 200:
                data = response.json()
                output_file = OUTPUT_DIR / f"{filename.replace('.pdf', '_response.json')}"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  Saved: {output_file}")
            else:
                print(f"  ERROR: HTTP {response.status_code}")

        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n出力先: {OUTPUT_DIR}")
    print("JSONファイルをテキストエディタで開いて詳細を確認できます")


if __name__ == "__main__":
    main()
