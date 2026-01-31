# Cloud Run: ContainerImageImportFailed — 実行コマンド（コピー用）

**前提**: `gcloud auth login` と `gcloud config set project fixedassets-project` を済ませ、**認証済みのターミナル**で実行すること。

---

## 1) 失敗内容の確認

```powershell
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,status.latestCreatedRevisionName)"
```

`status.latestCreatedRevisionName` を控える（例: `fixed-asset-agentic-api-00042-xxx`）。

```powershell
gcloud run revisions describe <LATEST_REVISION> --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,spec.containers)"
```

`<LATEST_REVISION>` を上で控えた名前に置き換える。  
`status.conditions` の `message` に image pull / permission 系の文言があれば、以下 2) の IAM を実施。

---

## 2) イメージ pull 用 IAM（image pull エラー時）

```powershell
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="value(spec.template.spec.serviceAccountName)"
gcloud projects describe fixedassets-project --format="value(projectNumber)"
```

- `serviceAccountName` が空 → ランタイム SA: `{projectNumber}-compute@developer.gserviceaccount.com`
- 空でない → その値をランタイム SA として使う  
- サービスエージェント: `service-{projectNumber}@serverless-robot-prod.iam.gserviceaccount.com`

```powershell
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:<RUNTIME_SA>" --role="roles/artifactregistry.reader"
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:service-<PROJECT_NUMBER>@serverless-robot-prod.iam.gserviceaccount.com" --role="roles/artifactregistry.reader"
```

`<RUNTIME_SA>` と `<PROJECT_NUMBER>` を上で確認した値に置き換える。

---

## 3) イメージ digest の確認と再デプロイ（ビルドなし）

```powershell
gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy --include-tags
```

一覧から **fixed-asset-agentic-api** の行の **DIGEST**（`sha256:` の後ろ）をコピー → これを `<FULL_DIGEST>` に使う。

```powershell
gcloud run deploy fixed-asset-agentic-api --image asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy/fixed-asset-agentic-api@sha256:<FULL_DIGEST> --region asia-northeast1 --allow-unauthenticated --project fixedassets-project
```

`<FULL_DIGEST>` を上でコピーした digest（`sha256:` は付けない）に置き換える。

---

## 4) Ready 確認とスモーク

```powershell
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,status.url)"
```

`status.conditions` で `type: Ready` かつ `status: True` を確認。  
`status.url` を `CLOUD_RUN_URL` に設定してスモーク:

```powershell
$env:CLOUD_RUN_URL = "https://fixed-asset-agentic-api-XXXXXXXX.asia-northeast1.run.app"
.\scripts\smoke_cloudrun.ps1
```

`status.url` の値をそのまま `$env:CLOUD_RUN_URL` に入れる。

---

## 一括実行用スクリプト

対話形式で 1)〜4) を順に実行する場合:

```powershell
.\scripts\cloudrun_triage_and_fix.ps1
```
