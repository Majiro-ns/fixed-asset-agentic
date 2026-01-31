# Cloud Run 環境変数チェックリスト

Cloud Run デプロイ時に設定する環境変数の一覧。未設定時は feature は OFF となり、フォールバック動作をする。

---

## DocAI（PDF 抽出）

| 変数 | 必須 | 既定 | 説明 |
|------|------|------|------|
| `USE_DOCAI` | - | 未設定＝OFF | `1` / `true` 等で有効。PDF 抽出に Document AI を使用。 |
| `GOOGLE_CLOUD_PROJECT` | USE_DOCAI 時 | - | GCP プロジェクト ID。 |
| `DOCAI_PROCESSOR_ID` | USE_DOCAI 時 | - | Document AI プロセッサ ID。 |
| `DOCAI_LOCATION` | - | `us` | Document AI のロケーション。 |

- **USE_DOCAI 未設定 or 0**: `core/pdf_extract._try_docai` は呼ばれず、PyMuPDF / pdfplumber にフォールバック。
- **USE_DOCAI=1 かつ GOOGLE_CLOUD_PROJECT / DOCAI_PROCESSOR_ID のいずれか未設定**: `_try_docai` は `None` を返し、同様にフォールバック。

---

## /classify_pdf（PDF 分類）

| 変数 | 必須 | 既定 | 説明 |
|------|------|------|------|
| `PDF_CLASSIFY_ENABLED` | - | 未設定＝OFF | `1` / `true` 等で有効。POST /classify_pdf を許可。 |

### /classify_pdf が OFF のときの期待値

- **HTTP**: `400`
- **body.detail**（JSON）:
  - `detail.error` == `"PDF_CLASSIFY_DISABLED"`
  - `detail.how_to_enable`: 有効化方法（例: `"Set PDF_CLASSIFY_ENABLED=1 on server"`）
  - `detail.fallback`: 代替手段（例: `"Use POST /classify with Opal JSON instead"`）

---

## Vertex AI Search（法令エビデンス）

| 変数 | 必須 | 既定 | 説明 |
|------|------|------|------|
| `VERTEX_SEARCH_ENABLED` | - | 未設定＝OFF | `1` / `true` 等で有効。GUIDANCE 時に Citation 検索。 |
| `GOOGLE_CLOUD_PROJECT` | 有効時 | - | GCP プロジェクト ID。 |
| `DISCOVERY_ENGINE_DATA_STORE_ID` | 有効時 | - | Discovery Engine データストア ID。 |

- 未設定 or 無効時: `get_citations_for_guidance` は空リストを返す。

---

## Gemini API（AI分類）

| 変数 | 必須 | 既定 | 説明 |
|------|------|------|------|
| `GEMINI_ENABLED` | - | 未設定＝OFF | `1` / `true` 等で有効。Gemini APIによる分類を使用。 |
| `GOOGLE_API_KEY` | GEMINI_ENABLED時 | - | Gemini API キー。Google AI Studio で取得。 |
| `GEMINI_MODEL` | - | `gemini-1.5-flash` | 使用するGeminiモデル名。 |

- **GEMINI_ENABLED=1 かつ GOOGLE_API_KEY 未設定**: フォールバックでルールベース分類を使用。
- **エラー発生時**: Stop-first原則に従い、GUIDANCE（要確認）を返す。

### APIキーの設定方法

**ローカル開発時**:
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**Cloud Run デプロイ時**:
```bash
# Secret Managerを使用（推奨）
gcloud run deploy SERVICE_NAME \
  --set-secrets "GOOGLE_API_KEY=gemini-api-key:latest"

# または環境変数で直接設定
gcloud run deploy SERVICE_NAME \
  --set-env-vars "GEMINI_ENABLED=1,GOOGLE_API_KEY=your-key"
```

---

## 耐用年数判定（Useful Life Estimator）

| 変数 | 必須 | 既定 | 説明 |
|------|------|------|------|
| `GOOGLE_API_KEY` | - | - | マスタ照合で該当なしの場合、Gemini APIで推定。 |
| `GEMINI_API_KEY` | - | - | `GOOGLE_API_KEY` の代替（どちらでも可）。 |

- マスタデータ（法定耐用年数）は常に利用可能。
- APIキー未設定時はマスタ照合のみ（Gemini推定なし）。

---

## その他（Cloud Run 共通）

- `PORT`: Cloud Run が自動設定。Dockerfile の `ENV PORT=8080` はデフォルト用。
