---
title: "cmd_067 修正ログ"
date: 2026-02-10
---

# 修正ログ（cmd_067）

## サマリ

cmd_067では、08_Skill_Based_Review.md で指摘されたCritical/Major項目のうち、即時対応が必要な22件の修正を5名の足軽が並列で実施した。API認証・パストラバーサル対策・アップロードバリデーション・プロンプトインジェクション対策のセキュリティ4件（Critical）、プライバシー3件、プロダクト整理4件、UX改善5件、セキュリティ強化+ログ5件を完了。全修正ファイルは `python3 -m py_compile` で構文検証済み。api/main.py への並列修正はRACE-001警告に従い全員がEditツール（差分編集）を使用し、競合なく完了。

| ワークストリーム | 担当 | 修正件数 | 対象ファイル数 |
|----------------|------|---------|-------------|
| B: セキュリティ Critical | ashigaru4 | 4件（C-01〜C-04） | api/main.py, api/gemini_classifier.py |
| A: プライバシー + confidence | ashigaru5 | 4件（C-05〜C-07 + Bug修正） | core/pipeline.py, api/main.py, ui/app_minimal.py |
| D: プロダクト整理 | ashigaru6 | 4件（C-08〜C-11） | ui/app.py→app_classic.py, .gitignore |
| C: UX改善 | ashigaru7 | 5件（修正13〜17） | ui/components/*, ui/styles.py, ui/app_minimal.py |
| C: セキュリティ強化+ログ | ashigaru8 | 5件（修正18〜22） | api/main.py, ui/batch_upload.py, requirements.txt |

---

## 修正一覧

| # | 分類 | 対象ファイル | 修正内容 | 担当 | 状態 |
|---|------|-------------|---------|------|------|
| 1 | Critical/セキュリティ | api/main.py | APIキー認証（X-API-Key, Depends）導入。3エンドポイントに適用 | ashigaru4 | 完了 |
| 2 | Critical/セキュリティ | api/main.py | policy_pathパストラバーサル対策（`_validate_policy_path`関数） | ashigaru4 | 完了 |
| 3 | Critical/セキュリティ | api/main.py | PDFアップロードバリデーション（MIME・マジックバイト・サイズ50MB・バッチ20件） | ashigaru4 | 完了 |
| 4 | Critical/セキュリティ | api/gemini_classifier.py | プロンプトインジェクション対策（`_sanitize_text`+デリミタ分離+50000文字制限） | ashigaru4 | 完了 |
| 5 | Critical/プライバシー | core/pipeline.py | PDF保持期間ポリシー（24時間自動削除 `cleanup_old_files`関数） | ashigaru5 | 完了 |
| 6 | Critical/プライバシー | core/pipeline.py | 抽出結果JSON保持期間（data/results/にも24時間クリーンアップ適用） | ashigaru5 | 完了 |
| 7 | Critical/プライバシー | ui/app_minimal.py | LLMデータ送信の情報開示（Google Gemini APIへの送信に関するst.info追加） | ashigaru5 | 完了 |
| 8 | Major/既知バグ | api/main.py | confidenceデフォルト値修正（0.8→0.0、3箇所） | ashigaru5 | 完了 |
| 9 | Critical/プロダクト | ui/app.py → app_classic.py | UI二重実装の解消（app.pyをapp_classic.pyにリネーム） | ashigaru6 | 完了 |
| 10 | Critical/プロダクト | .gitignore | data/results/ と data/uploads/ を.gitignoreに追加 | ashigaru6 | 完了 |
| 11 | Critical/UI | ui/app_classic.py | 技術用語の平易化（Opal/Agentic/Stop設計等→ユーザー向け日本語に全面書換） | ashigaru6 | 完了 |
| 12 | Critical/UI | ui/app_classic.py | テーブルカラム名を日本語化（classification→分類結果、flags→注意事項等） | ashigaru6 | 完了 |
| 13 | Major/UX | diff_display.py, app_minimal.py | GUIDANCE用語統一（「要確認」「GUIDANCE」→「確認が必要です」） | ashigaru7 | 完了 |
| 14 | Major/UX | diff_display.py | 英語ラベル日本語化（Before:/After:→変更前:/変更後:） | ashigaru7 | 完了 |
| 15 | Major/UX | styles.py | 免責事項コントラスト比改善（#9CA3AF→#4B5563、WCAG AA準拠） | ashigaru7 | 完了 |
| 16 | Minor/UX | result_card.py | 確信度表現改善（「たぶん大丈夫」→「概ね確実（念のため確認推奨）」） | ashigaru7 | 完了 |
| 17 | Major/UX | input_area.py | Empty Stateガイダンス充実（1行→3行、対応形式・サンプル導線を追加） | ashigaru7 | 完了 |
| 18 | Major/セキュリティ | api/main.py | CORS設定追加（CORSMiddleware、環境変数CORS_ORIGINSから読込） | ashigaru8 | 完了 |
| 19 | Major/セキュリティ | api/main.py, requirements.txt | レート制限導入（slowapi、10 req/min/IP） | ashigaru8 | 完了 |
| 20 | Major/プライバシー | ui/batch_upload.py | Cloud Run URLハードコード除去（環境変数API_BASE_URL化） | ashigaru8 | 完了 |
| 21 | Major/運用 | api/main.py | 構造化ログ導入（JSON形式、request_id付き、/classify, /classify_pdf） | ashigaru8 | 完了 |
| 22 | Major/セキュリティ | api/main.py | 免責表示ルール実装（disclaimerフィールド、高確信度時追加免責） | ashigaru8 | 完了 |

---

## 詳細（各修正のdiff要約）

### 修正1: APIキー認証（ashigaru4）
```
+ async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
+     if not _API_KEY: return  # dev mode
+     if x_api_key != _API_KEY: raise HTTPException(401)
  @app.post("/classify", ...)
- async def classify(request):
+ async def classify(request, _auth=Depends(verify_api_key)):
```

### 修正2: パストラバーサル対策（ashigaru4）
```
+ def _validate_policy_path(policy_path):
+     if ".." in policy_path or "/" in policy_path: raise HTTPException(400)
+     resolved = (PROJECT_ROOT / "policies" / basename).resolve()
+     if not str(resolved).startswith(str(policies_dir)): raise HTTPException(400)
```

### 修正3: アップロードバリデーション（ashigaru4）
```
+ _MAX_UPLOAD_SIZE = 50 * 1024 * 1024
+ _MAX_BATCH_FILES = 20
+ async def _validate_pdf_upload(file):
+     if file.content_type != "application/pdf": raise HTTPException(400)
+     if len(content) > _MAX_UPLOAD_SIZE: raise HTTPException(400)
+     if not content[:4] == b"%PDF": raise HTTPException(400)
```

### 修正4: プロンプトインジェクション対策（ashigaru4）
```
+ _MAX_INPUT_LENGTH = 50000
+ def _sanitize_text(text):
+     text = text[:_MAX_INPUT_LENGTH]
+     text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
+     return text
  # _build_user_prompt内: ユーザー入力を```デリミタで囲み、_sanitize_text適用
```

### 修正5-6: PDF/JSON保持期間ポリシー（ashigaru5）
```
+ def cleanup_old_files(directory, max_age_hours=24):
+     # 24時間以上経過したファイルを削除
+ def _cleanup_data_directories():
+     cleanup_old_files("data/uploads")
+     cleanup_old_files("data/results")
  # モジュールロード時に自動実行
```

### 修正7: LLMデータ送信の情報開示（ashigaru5）
```
+ st.info("アップロードされたPDFの内容は、判定のためにGoogle Gemini APIに送信されます。")
```

### 修正8: confidence デフォルト値修正（ashigaru5）
```
- item.get("confidence", 0.8)  # 3箇所
+ item.get("confidence", 0.0)  # 3箇所
```

### 修正9: app.py リネーム（ashigaru6）
```
$ mv ui/app.py ui/app_classic.py
```

### 修正10: .gitignore追加（ashigaru6）
```
+ data/results/
+ data/uploads/
```

### 修正11-12: 技術用語平易化 + テーブルカラム日本語化（ashigaru6）
```
- APP_TITLE = "Opal抽出 × Agentic判定"
+ APP_TITLE = "自動抽出 × 自動判定"
- "classification", "flags", "evidence"
+ "分類結果", "注意事項", "根拠"
```

### 修正13: GUIDANCE用語統一（ashigaru7）
```
- "⚠️ 要確認（自動判定不可）"
+ "⚠️ 確認が必要です"
```

### 修正14: diff_display日本語化（ashigaru7）
```
- "Before:" / "After:"
+ "変更前:" / "変更後:"
```

### 修正15: 免責コントラスト比改善（ashigaru7）
```
- color: #9CA3AF  (contrast 2.9:1)
+ color: #4B5563  (contrast 7.5:1, WCAG AA準拠)
```

### 修正16: 確信度表現改善（ashigaru7）
```
- "たぶん大丈夫"
+ "概ね確実（念のため確認推奨）"
```

### 修正17: Empty Stateガイダンス充実（ashigaru7）
```
- st.caption("👆 PDFをアップロードして判定を実行")
+ st.caption("請求書・見積書・領収書のPDFをアップロードしてください。")
+ st.caption("対応形式: PDF（テキスト埋め込み型推奨）")
+ st.caption("サンプルで試す場合は下の「デモで試す」ボタンをどうぞ。")
```

### 修正18: CORS設定（ashigaru8）
```
+ from fastapi.middleware.cors import CORSMiddleware
+ _cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:8501").split(",")
+ app.add_middleware(CORSMiddleware, allow_origins=_cors_origins, ...)
```

### 修正19: レート制限（ashigaru8）
```
+ from slowapi import Limiter, _rate_limit_exceeded_handler  # try/except
+ limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])
+ requirements.txt: + slowapi>=0.1.9
```

### 修正20: Cloud Run URLハードコード除去（ashigaru8）
```
- DEFAULT_API_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"
+ api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
```

### 修正21: 構造化ログ（ashigaru8）
```
+ class _JSONFormatter(logging.Formatter): ...
+ logger = logging.getLogger("fixed_asset_api")
+ logger.info("POST /classify start", extra={"request_id": req_id})
+ logger.info("POST /classify done decision=%s", ..., extra={"request_id": req_id})
+ logger.error("POST /classify error: %s", e, extra={"request_id": req_id})
```

### 修正22: 免責表示ルール（ashigaru8）
```
+ class ClassifyResponse:
+     disclaimer: str = "この判定結果はAIによる参考情報です。..."
+ def _format_classify_response():
+     if confidence > 0.9:
+         disclaimer += " 高確信度の判定ですが、必ず専門家の確認を受けてください。"
```
