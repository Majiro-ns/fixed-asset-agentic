#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提出前自動検証スクリプト (Preflight Check)

使い方:
    python scripts/preflight_check.py

このスクリプトは以下を自動検証する:
1. 必須ファイルの存在
2. Cloud Run API の稼働確認
3. 機密情報の混入チェック
4. デモPDFの存在
5. コードの基本的な整合性

殿（人間）が確認すべき項目は別途リストアップされる。
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# 結果格納
results: List[Tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = ""):
    """チェック結果を記録"""
    results.append((name, passed, detail))
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {name}")
    if detail and not passed:
        print(f"         → {detail}")


def section(title: str):
    """セクション見出し"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_required_files():
    """必須ファイルの存在確認"""
    section("1. 必須ファイル存在確認")

    required_files = [
        ("README.md", "審査員向け概要"),
        ("LICENSE", "ライセンスファイル"),
        ("requirements.txt", "依存関係"),
        ("Dockerfile", "コンテナ定義"),
        ("api/main.py", "APIエントリポイント"),
        ("core/classifier.py", "分類ロジック"),
        ("core/adapter.py", "データアダプター"),
        ("ui/app_minimal.py", "Streamlit UI"),
        ("docs/LORD_ACTION_PLAN.md", "殿の手順書"),
        ("docs/DEMO_RUNBOOK.md", "デモ手順"),
        ("docs/COMPLIANCE_CHECKLIST.md", "規約準拠"),
        ("policies/company_default.json", "デフォルトポリシー"),
    ]

    for filepath, desc in required_files:
        full_path = PROJECT_ROOT / filepath
        exists = full_path.exists()
        check(f"{filepath} ({desc})", exists,
              f"ファイルが見つかりません" if not exists else "")


def check_demo_pdfs():
    """デモPDFの存在確認"""
    section("2. デモPDF存在確認")

    demo_pdf_dir = PROJECT_ROOT / "data" / "demo_pdf"
    expected_pdfs = [
        "demo_capital.pdf",
        "demo_capital2.pdf",
        "demo_expense.pdf",
        "demo_guidance.pdf",
    ]

    for pdf in expected_pdfs:
        pdf_path = demo_pdf_dir / pdf
        exists = pdf_path.exists()
        size = pdf_path.stat().st_size if exists else 0
        check(f"{pdf}", exists and size > 1000,
              f"ファイルなし or サイズ異常 ({size} bytes)" if not (exists and size > 1000) else "")


def check_no_secrets():
    """機密情報の混入チェック"""
    section("3. 機密情報チェック")

    # 危険なファイルパターン
    dangerous_patterns = [
        r"\.env$",
        r"\.env\.local$",
        r"credentials\.json$",
        r"service[-_]?account.*\.json$",
        r".*[-_]key\.json$",
        r"secret.*\.txt$",
        r"\.gcloud_config$",
    ]

    # 機密情報パターン（ファイル内容）
    secret_patterns = [
        (r"GOOGLE_API_KEY\s*=\s*['\"][^'\"]+['\"]", "Google APIキーがハードコード"),
        (r"AIza[A-Za-z0-9_-]{35}", "Google APIキーパターン検出"),
        (r"sk-[A-Za-z0-9]{48}", "OpenAI APIキーパターン検出"),
        (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token検出"),
    ]

    # .gitignore確認
    gitignore_path = PROJECT_ROOT / ".gitignore"
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        has_env = ".env" in gitignore_content
        check(".gitignore に .env が含まれる", has_env)
    else:
        check(".gitignore存在", False, ".gitignoreファイルがありません")

    # 危険なファイルの存在チェック
    dangerous_found = []
    for pattern in dangerous_patterns:
        for f in PROJECT_ROOT.rglob("*"):
            if f.is_file() and re.search(pattern, f.name, re.IGNORECASE):
                # .gitで無視されるファイルは除外
                rel_path = f.relative_to(PROJECT_ROOT)
                if ".git" not in str(rel_path):
                    dangerous_found.append(str(rel_path))

    check("危険なファイルパターンなし", len(dangerous_found) == 0,
          f"検出: {dangerous_found[:3]}" if dangerous_found else "")

    # Pythonファイル内の機密情報チェック
    secrets_in_code = []
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if ".git" in str(py_file) or "venv" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in secret_patterns:
                if re.search(pattern, content):
                    secrets_in_code.append(f"{py_file.name}: {desc}")
        except Exception:
            pass

    check("コード内に機密情報なし", len(secrets_in_code) == 0,
          f"検出: {secrets_in_code[:3]}" if secrets_in_code else "")


def check_api_health():
    """Cloud Run API稼働確認"""
    section("4. Cloud Run API稼働確認")

    try:
        import requests

        api_url = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

        # /health
        try:
            resp = requests.get(f"{api_url}/health", timeout=10)
            health_ok = resp.status_code == 200 and resp.json().get("ok") == True
            check("/health エンドポイント", health_ok,
                  f"status={resp.status_code}" if not health_ok else "")
        except Exception as e:
            check("/health エンドポイント", False, str(e))

        # /classify
        try:
            test_payload = {
                "opal_json": {
                    "invoice_date": "2024-01-01",
                    "vendor": "テスト株式会社",
                    "line_items": [
                        {"item_description": "サーバー新設工事", "amount": 500000, "quantity": 1}
                    ]
                }
            }
            resp = requests.post(f"{api_url}/classify", json=test_payload, timeout=15)
            classify_ok = resp.status_code == 200 and "decision" in resp.json()
            decision = resp.json().get("decision", "N/A") if classify_ok else "N/A"
            check(f"/classify エンドポイント (結果: {decision})", classify_ok,
                  f"status={resp.status_code}" if not classify_ok else "")
        except Exception as e:
            check("/classify エンドポイント", False, str(e))

    except ImportError:
        check("requests ライブラリ", False, "pip install requests が必要")


def check_code_quality():
    """コード品質の基本チェック"""
    section("5. コード品質チェック")

    # DEBUG printの残存確認
    debug_found = []
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if ".git" in str(py_file) or "venv" in str(py_file) or "test" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'print\s*\(\s*["\']?\[?DEBUG', content, re.IGNORECASE):
                debug_found.append(py_file.name)
        except Exception:
            pass

    check("DEBUG printなし", len(debug_found) == 0,
          f"検出: {debug_found}" if debug_found else "")

    # TODO/FIXMEの確認（警告のみ）
    todo_count = 0
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if ".git" in str(py_file) or "venv" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            todo_count += len(re.findall(r'#\s*(TODO|FIXME|XXX)', content, re.IGNORECASE))
        except Exception:
            pass

    check(f"TODO/FIXME ({todo_count}件)", todo_count < 10,
          f"{todo_count}件のTODO/FIXMEがあります（確認推奨）" if todo_count >= 10 else "")


def check_golden_set():
    """Golden Set評価"""
    section("6. Golden Set確認")

    golden_dir = PROJECT_ROOT / "data" / "golden"
    if golden_dir.exists():
        golden_files = list(golden_dir.glob("*.json"))
        check(f"Golden Setファイル数 ({len(golden_files)}件)", len(golden_files) >= 10,
              f"{len(golden_files)}件 (10件以上推奨)" if len(golden_files) < 10 else "")
    else:
        check("Golden Setディレクトリ", False, "data/golden/ が見つかりません")


def generate_human_checklist():
    """殿（人間）が確認すべき項目を出力"""
    section("7. 殿（人間）確認項目")

    print("""
  以下は自動検証できません。殿が手動で確認してください:

  □ GitHubリポジトリが Public である
    → https://github.com/Majiro-ns/fixed-asset-agentic

  □ 参加登録が完了している（締切: 2/13）
    → https://lu.ma/agentic-ai-hackathon-4

  □ Zenn記事が公開されている
    → カテゴリ: Idea
    → トピック: gch4 （必須）
    → デモ動画（3分）埋め込み済み

  □ デモ動画がアクセス可能（YouTube/Vimeo）

  □ Cloud Run に最新コードがデプロイされている
    → PDF_CLASSIFY_ENABLED=1
    → GEMINI_PDF_ENABLED=1 (任意)
""")


def main():
    print("\n" + "="*60)
    print("  提出前自動検証 (Preflight Check)")
    print("  Fixed Asset Classifier - Hackathon Submission")
    print("="*60)

    check_required_files()
    check_demo_pdfs()
    check_no_secrets()
    check_api_health()
    check_code_quality()
    check_golden_set()
    generate_human_checklist()

    # サマリ
    section("サマリ")
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"\n  合計: {len(results)} 項目")
    print(f"  ✅ PASS: {passed} 項目")
    print(f"  ❌ FAIL: {failed} 項目")

    if failed > 0:
        print("\n  ⚠️ 失敗項目を修正してから提出してください")
        print("\n  失敗項目一覧:")
        for name, ok, detail in results:
            if not ok:
                print(f"    - {name}")
                if detail:
                    print(f"      → {detail}")
        sys.exit(1)
    else:
        print("\n  ✅ 自動検証項目は全てパスしました")
        print("  → 「殿確認項目」を手動で確認してください")
        sys.exit(0)


if __name__ == "__main__":
    main()
