# Cloud Run 障害報告テンプレ（貼り付け用）

**このテンプレを埋めて貼れば原因特定が早い。** ContainerImageImportFailed や Ready にならない事象の報告時に、以下 3 つを埋めて共有する。

---

## 1. services describe の出力

**実行するコマンド:**

```powershell
gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,status.latestCreatedRevisionName,status.url)"
```

**貼り付け枠（出力をそのままコピペ）:**

```
（ここに上記コマンドの出力全体を貼る）
```

---

## 2. revisions describe の出力

(1) の `status.latestCreatedRevisionName` の値を `<LATEST_REVISION>` に代入する。

**実行するコマンド:**

```powershell
gcloud run revisions describe <LATEST_REVISION> --region asia-northeast1 --project fixedassets-project --format="yaml(status.conditions,spec.containers)"
```

**貼り付け枠（出力をそのままコピペ）:**

```
（ここに上記コマンドの出力全体を貼る）
```

---

## 3. IAM を実行したか

次のいずれかを選んで記載する。

- **未実施**  
  「未実施」または「本件では IAM の付与は行っていない」

- **実施した**  
  実行したコマンドをそのまま貼る。例:

```powershell
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:XXXXXXXX-compute@developer.gserviceaccount.com" --role="roles/artifactregistry.reader" --project fixedassets-project
gcloud projects add-iam-policy-binding fixedassets-project --member="serviceAccount:service-XXXXXXXX@serverless-robot-prod.iam.gserviceaccount.com" --role="roles/artifactregistry.reader" --project fixedassets-project
```

---

## 参照

- 対話式の確認・IAM・再デプロイ: `scripts/cloudrun_triage_and_fix.ps1`
- 原因と対処の流れ: [CLOUDRUN_TROUBLESHOOTING.md](CLOUDRUN_TROUBLESHOOTING.md)
