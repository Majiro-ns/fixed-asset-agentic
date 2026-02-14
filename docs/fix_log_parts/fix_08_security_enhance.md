# 修正ログ: セキュリティ強化+ログ（ashigaru8）

## 修正18: CORS設定の追加
- **対象**: `api/main.py`
- **変更内容**:
  - `from fastapi.middleware.cors import CORSMiddleware` を追加
  - `app.add_middleware(CORSMiddleware, ...)` を `app = FastAPI(...)` 直後に追加
  - `allow_origins`: 環境変数 `CORS_ORIGINS` から読み込み（デフォルト: `http://localhost:8501`）、カンマ区切りで複数指定可
  - `allow_methods`: `["GET", "POST"]`
  - `allow_headers`: `["X-API-Key", "Content-Type"]`
- **確認**: py_compile OK

## 修正19: レート制限の導入
- **対象**: `api/main.py`, `requirements.txt`
- **変更内容**:
  - slowapi を try/except import でオプショナルに導入
  - 制限: 10 req/min/IP（`default_limits=["10/minute"]`）
  - `requirements.txt` に `slowapi>=0.1.9` を追加
  - slowapi未インストール時は警告ログを出力し、レート制限なしで動作（既存動作を維持）
- **確認**: py_compile OK

## 修正20: Cloud Run URLのハードコード除去
- **対象**: `ui/batch_upload.py:291`
- **変更内容**:
  - 変更前: `DEFAULT_API_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"`
  - 変更後: `api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")`
  - GCPプロジェクト番号（986547623556）を含むURLをソースコードから除去
- **確認**: py_compile OK

## 修正21: 構造化ログの導入
- **対象**: `api/main.py`
- **変更内容**:
  - `import logging`, `import json`, `import uuid` を追加
  - `_JSONFormatter` クラスを定義（timestamp, level, message, module, request_id をJSON出力）
  - `logger = logging.getLogger("fixed_asset_api")` でロガーを取得
  - `/classify` エンドポイントにログ追加: start, done（decision付き）, ValueError, error
  - `/classify_pdf` エンドポイントにログ追加: start（filename付き）, done（decision+filename）, ValueError, error
  - 各リクエストにUUID（8桁短縮）のrequest_idを付与してトレーサビリティ確保
- **確認**: py_compile OK

## 修正22: 免責表示ルール実装
- **対象**: `api/main.py`
- **変更内容**:
  - `ClassifyResponse` モデルに `disclaimer: str` フィールドを追加（デフォルト: 基本免責文）
  - `_format_classify_response()` 内でconfidence > 0.9 の場合に追加免責文を連結
  - 基本: 「この判定結果はAIによる参考情報です。最終的な判断は税理士等の専門家にご確認ください。」
  - 高確信度時追加: 「高確信度の判定ですが、必ず専門家の確認を受けてください。」
- **確認**: py_compile OK
