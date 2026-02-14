# 修正ログ: セキュリティ修正 C-01〜C-04

**担当**: 足軽4号 (subtask_067_04)
**日時**: 2026-02-10
**親コマンド**: cmd_067 ワークストリームB

---

## C-01: APIキー認証

**ファイル**: `api/main.py`
**修正箇所**: import行 + PROJECT_ROOT直後にヘルパー追加 + 3エンドポイント

### 変更内容
1. `Depends`, `Header` を fastapi importに追加
2. `verify_api_key` 非同期関数を追加
   - 環境変数 `FIXED_ASSET_API_KEY` からAPIキーを読み込み
   - `X-API-Key` ヘッダーで認証
   - キー未設定時はローカル開発モードで認証スキップ（`logger.warning`出力）
3. `/classify`, `/classify_pdf`, `/classify_batch` の3エンドポイントに `Depends(verify_api_key)` を適用

### 設計判断
- ヘルスチェック(`/healthz`, `/health`)とルート(`/`)は認証不要（Cloud Run等のLBヘルスチェック対応）
- 開発モード（キー未設定）では警告ログを出力し、認証をスキップ

---

## C-02: パストラバーサル対策

**ファイル**: `api/main.py`
**修正箇所**: `_validate_policy_path`関数追加 + 3箇所で適用

### 変更内容
1. `_validate_policy_path` ヘルパー関数を追加
   - `..`, `/`, `\` を含むパスは400エラー
   - `os.path.basename` でファイル名のみに正規化
   - `PROJECT_ROOT/policies/` 配下のみアクセス許可（resolve後にstartswithで検証）
2. `/classify` エンドポイントの `request.policy_path` に適用
3. `/classify_pdf` エンドポイントの `policy_path` パラメータに適用
4. `_process_single_pdf` 内部関数の `policy_path` に適用

### 設計判断
- 二重チェック（文字列チェック + resolve後のstartswith）で確実にディレクトリ外アクセスを遮断
- `None` 入力はそのまま返す（デフォルトポリシー使用のため）

---

## C-03: アップロードバリデーション

**ファイル**: `api/main.py`
**修正箇所**: `_validate_pdf_upload`関数追加 + 定数追加 + 3箇所で適用

### 変更内容
1. `_MAX_UPLOAD_SIZE = 50 * 1024 * 1024` (50MB) 定数
2. `_MAX_BATCH_FILES = 20` 定数
3. `_validate_pdf_upload` 非同期ヘルパー関数を追加
   - MIMEタイプチェック: `application/pdf` のみ許可
   - マジックバイト: 先頭4バイトが `%PDF` であることを確認
   - サイズ上限: 50MB
4. `/classify_pdf` のファイル読み込みを `_validate_pdf_upload` 経由に変更
5. `_process_single_pdf` のファイル読み込みを `_validate_pdf_upload` 経由に変更
6. `/classify_batch` にファイル数上限チェック（20ファイル）を追加

### 設計判断
- MIMEタイプとマジックバイトの二重チェックでPDF偽装を防止
- content_typeがNoneの場合（ブラウザが送信しない場合）はマジックバイトチェックで対応
- バッチ処理のファイル数制限はDDoS軽減のため

---

## C-04: プロンプトインジェクション対策

**ファイル**: `api/gemini_classifier.py`
**修正箇所**: `import re`追加 + `_sanitize_text`関数追加 + `_build_user_prompt`修正

### 変更内容
1. `import re` を追加
2. `_MAX_INPUT_LENGTH = 50000` 定数
3. `_sanitize_text` ヘルパー関数を追加
   - 入力テキストの長さ制限（50000文字）
   - 制御文字のサニタイズ（`\x00-\x08`, `\x0b`, `\x0c`, `\x0e-\x1f` 除去）
   - `\n`（改行）と `\t`（タブ）は保持
4. `_build_user_prompt` のユーザー入力部分を修正
   - 書類情報（title, vendor, date, notes）を `_sanitize_text` でサニタイズ
   - 明細のdescription, remarksを `_sanitize_text` でサニタイズ
   - 追加コンテキストを `_sanitize_text` でサニタイズ
   - 各ユーザー入力セクションを ` ``` ` デリミタで囲んで明示的に分離

### 設計判断
- デリミタで「システム指示」と「ユーザー入力」を明確に分離
- 金額（int型）はサニタイズ不要（数値のみ）
- 制御文字除去で不可視文字による指示挿入を防止
- 50000文字制限でトークン爆発攻撃を防止

---

## 品質確認

- [x] `python3 -m py_compile api/main.py` — パス
- [x] `python3 -m py_compile api/gemini_classifier.py` — パス
- [x] RACE-001警告準拠: 全修正にEditツール（old_string→new_string）を使用
- [x] 担当セクションのみ修正（認証・policy_path・アップロード・プロンプト構築）
