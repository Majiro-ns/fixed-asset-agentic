# 実装サマリ（What changed / Why / How to test）

**日付**: 2026-01-24

---

## What changed

### STEP A: Cloud Run（ContainerImageImportFailed）対処

- **変更**: なし（gcloud は認証済み環境で手動実行が必要）
- **実施した手順**: 下記「使用したコマンド」を参照。Artifact Registry の pull 権限付与と、Cloud Build のイメージ digest を使った `gcloud run deploy` で対応。

### STEP C: 税務閾値（10/20/30/60万）stop-first

| ファイル | 変更内容 |
|---------|---------|
| `core/classifier.py` | ・`_apply_tax_rules(amount, total_amount)` を追加（R-AMOUNT-003, 100k200k, R-AMOUNT-001, R-AMOUNT-SME300k, R-AMOUNT-600k）<br>・`classify_line_item` に `doc` を追加し、`_apply_tax_rules` の結果を `flags` に `tax_rule:{id}:{reason}` で付与。`suggests_guidance=True` のとき `GUIDANCE` に統一<br>・`classify_document` から `classify_line_item` に `doc` を渡すよう変更 |
| `api/main.py` | ・`_format_classify_response` の `evidence` に、`flags` の `tax_rule:*` を `tax_rules` として付与 |
| `data/golden/case05_expected.json` | ・`reasons_contains`: `["設置"]` → `["R-AMOUNT-001"]`（200k で `suggests_guidance` により GUIDANCE になるため） |
| `data/golden/case08_expected.json` | ・`decision`: `CAPITAL_LIKE` → `GUIDANCE`<br>・`reasons_contains`: `["増設"]` → `["R-AMOUNT-600k"]`（600k 以上で修繕費 vs 資本的支出のため stop-first で GUIDANCE） |

### STEP D: Google Cloud DocAI（USE_DOCAI）

| ファイル | 変更内容 |
|---------|---------|
| `core/pdf_extract.py` | ・`_try_docai(path)` を実装（`USE_DOCAI=1` かつ `GOOGLE_CLOUD_PROJECT`, `DOCAI_PROCESSOR_ID` があるときのみ DocAI 呼び出し。`DOCAI_LOCATION` は任意、既定 `us`）<br>・失敗・ImportError 時は `None` を返し、従来の PyMuPDF/pdfplumber にフォールバック |
| `requirements.txt` | ・`google-cloud-documentai>=2.20.0` を追加 |

- **Gemini**: 未実装（オプションのまま。GUIDANCE 時の説明・質問生成に使う想定で `USE_GEMINI` をフラグとして想定）。

---

## Why

- **Cloud Run**: `ContainerImageImportFailed` は、Cloud Run 用サービスアカウント／Serverless Robot に Artifact Registry の `roles/artifactregistry.reader` がなく、イメージを pull できないことが原因になり得る。権限付与と digest 指定の再デプロイで解消を想定。
- **税務閾値**: 10万（少額）、20万・30万（一括償却・中小企業特例）、60万（修繕費 vs 資本的支出）の stop-first 判定を入れ、不足情報がある場合は GUIDANCE + `missing_fields` / `why_missing_matters` とする。
- **DocAI**: ハッカソン要件の「Google Cloud AI を主要技術として使用」に対応。`USE_DOCAI` で有効化し、未設定時は既存の PDF 抽出にフォールバック。

---

## How to test

### ゲート（ローカル）

```powershell
cd c:\Users\owner\Desktop\fixed-asset-agentic-repo
python -m pytest -q
python scripts\eval_golden.py
```

- 期待: `pytest` 10 passed、`eval_golden` 10/10（100%）。

### Cloud Run スモーク（Cloud Run が Ready のとき）

```powershell
$env:CLOUD_RUN_URL = "https://fixed-asset-agentic-api-XXXX.asia-northeast1.run.app"
.\scripts\smoke_cloudrun.ps1
```

- 期待: `/health` 200、`/classify` 200、`/classify_pdf` が 400 かつ `detail.error=PDF_CLASSIFY_DISABLED`、`detail.how_to_enable`、`detail.fallback` を含む。

### DocAI（USE_DOCAI=1 時）

- 要: `GOOGLE_CLOUD_PROJECT`、`DOCAI_PROCESSOR_ID`、必要なら `DOCAI_LOCATION`。
- `USE_DOCAI=1` で `extract_pdf` を実行し、`meta.source == "docai"` と `pages[].method == "docai"` を確認。未設定・失敗時は `source` が `local` などにフォールバック。

---

## 使用したコマンド（gcloud / デプロイ）

※ `gcloud auth login` および `gcloud config set project fixedassets-project` を事前に実施のこと。

### 状態確認

```powershell
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,status.latestCreatedRevisionName)"
gcloud run revisions list --service fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --limit 5
gcloud run revisions describe <LATEST_REVISION> --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,spec.containers)"
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="value(spec.template.spec.serviceAccountName)"
gcloud projects describe fixedassets-project --format="value(projectNumber)"
```

- `serviceAccountName` が空のとき、ランタイム SA は `{PROJECT_NUMBER}-compute@developer.gserviceaccount.com`。
- Cloud Run 用サービスエージェント: `service-{PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com`。

### Artifact Registry の pull 権限

```powershell
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:<RUNTIME_SA>" --role="roles/artifactregistry.reader"
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:service-<PROJECT_NUMBER>@serverless-robot-prod.iam.gserviceaccount.com" --role="roles/artifactregistry.reader"
```

- `<RUNTIME_SA>`: 上記ランタイム SA。
- `<PROJECT_NUMBER>`: `gcloud projects describe` の `projectNumber`。

### イメージ digest 指定での再デプロイ（ビルドなし）

```powershell
gcloud run deploy fixed-asset-agentic-api --image asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy/fixed-asset-agentic-api@sha256:<FULL_DIGEST> --region asia-northeast1 --allow-unauthenticated --project fixedassets-project
```

- `<FULL_DIGEST>`: Cloud Build の「pushed」イメージの完全な SHA256。

### ゲート（プロジェクトルート）

```powershell
cd c:\Users\owner\Desktop\fixed-asset-agentic-repo
python -m pytest -q
python scripts\eval_golden.py
```
