# Cloud Run トラブルシューティング

## 実行環境について

**Cursor 統合ターミナルで gcloud が動かない場合**

- `gcloud` 実行時に `WinError 5`（`credentials.db` へのアクセス拒否）が出ることがある。
- 原因: Cursor 内のシェルやサンドボックスにより、`%APPDATA%\Roaming\gcloud\` への読み書きがブロックされる。
- **対処**: **外部ターミナル**（Windows ターミナル、PowerShell、cmd 等）で `gcloud auth login` を完了し、本ドキュメントのコマンドおよび `scripts/cloudrun_triage_and_fix.ps1` を実行する。

---

## ContainerImageImportFailed の典型原因と対処

### 典型原因: Artifact Registry の pull 権限不足

Cloud Build がイメージを Artifact Registry に push しても、Cloud Run のリビジョンが **ContainerImageImportFailed** になる場合、多い原因は以下です。

1. **ランタイム用サービスアカウント**に Artifact Registry の読取権限がない  
2. **Cloud Run サービスエージェント**（Serverless Robot）に Artifact Registry の読取権限がない  

その結果、Cloud Run がイメージを pull できず、リビジョンが失敗します。

### 対処の流れ

1. 失敗の詳細を確認（`services describe` / `revisions describe`）
2. ランタイム SA とサービスエージェントを特定
3. 両方に `roles/artifactregistry.reader` を付与
4. 既存イメージの **digest 指定**で再デプロイ（ビルドなし）
5. `Ready=True` と `scripts/smoke_cloudrun.ps1` で確認

---

## Runtime SA / Service Agent の特定

### ランタイム用サービスアカウント（Runtime SA）

```powershell
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="value(spec.template.spec.serviceAccountName)"
```

- **出力が空** → デフォルトの Compute エンジン用 SA を使用:  
  `{PROJECT_NUMBER}-compute@developer.gserviceaccount.com`
- **出力あり** → その値を Runtime SA として使用

### プロジェクト番号（PROJECT_NUMBER）

```powershell
gcloud projects describe fixedassets-project --format="value(projectNumber)"
```

### Cloud Run サービスエージェント

```
service-{PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com
```

`{PROJECT_NUMBER}` は上記で取得した値に置き換える。

---

## roles/artifactregistry.reader 付与

`<RUNTIME_SA>` と `<PROJECT_NUMBER>` を、上で特定した値に置き換えて実行。

```powershell
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:<RUNTIME_SA>" --role="roles/artifactregistry.reader" --project fixedassets-project
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:service-<PROJECT_NUMBER>@serverless-robot-prod.iam.gserviceaccount.com" --role="roles/artifactregistry.reader" --project fixedassets-project
```

---

## digest 指定での再デプロイ（ビルドなし）

### 1. イメージ digest の取得

```powershell
gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy --include-tags --project fixedassets-project
```

一覧から **fixed-asset-agentic-api** の **DIGEST**（`sha256:` の後ろ 64 文字の 16 進）をコピー → `<FULL_DIGEST>` に使う。

### 2. デプロイ

```powershell
gcloud run deploy fixed-asset-agentic-api --image asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy/fixed-asset-agentic-api@sha256:<FULL_DIGEST> --region asia-northeast1 --allow-unauthenticated --project fixedassets-project
```

`<FULL_DIGEST>` には `sha256:` を付けず、64 文字の 16 進のみを指定する。

---

## scripts/smoke_cloudrun.ps1 の実行と期待値

### 実行

```powershell
$env:CLOUD_RUN_URL = "https://fixed-asset-agentic-api-XXXXXXXX.asia-northeast1.run.app"
.\scripts\smoke_cloudrun.ps1
```

`status.url` を `gcloud run services describe ... --format="value(status.url)"` で取得し、`CLOUD_RUN_URL` に設定する。

### 期待値

| 項目 | 期待値 |
|------|--------|
| **/health** | HTTP 200、`{"ok": true}` |
| **/classify** | HTTP 200、`decision`, `is_valid_document`, `confidence`, `trace`, `missing_fields`, `why_missing_matters` を含む |
| **/classify_pdf**（feature flag 既定 OFF） | HTTP 400、`detail.error == "PDF_CLASSIFY_DISABLED"`、`detail.how_to_enable`、`detail.fallback` を含む |

全てパスすれば `=== All smoke tests passed ===` が表示される。

---

## 一括実行

`scripts/cloudrun_triage_and_fix.ps1` で、上記の確認・IAM・digest 入力・再デプロイ・スモーク手順の案内を対話形式で実行できる。  
**必ず gcloud が使える外部ターミナルで実行すること。**

```powershell
.\scripts\cloudrun_triage_and_fix.ps1
```
