# デプロイ手順書

## 前提

- Google Cloud SDK インストール済み
- `gcloud auth login` 完了済み
- プロジェクト: `fixedassets-project`
- リージョン: `asia-northeast1`

---

## 1. Git Push（コード変更後は必ず実行）

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
git add .
git commit -m "変更内容を記述"
git push origin main
```

---

## 2. APIのみ更新

```powershell
gcloud run deploy fixed-asset-agentic-api --source . --region asia-northeast1 --allow-unauthenticated --memory 1Gi --set-env-vars "PDF_CLASSIFY_ENABLED=1,GEMINI_PDF_ENABLED=1,GOOGLE_API_KEY=YOUR_API_KEY"
```

---

## 3. UIのみ更新

### 手順（Dockerfileを一時的に差し替える）

```powershell
# 1. バックアップ & 差し替え
Copy-Item Dockerfile Dockerfile.api.bak
Copy-Item Dockerfile.ui Dockerfile
Copy-Item .dockerignore .dockerignore.api.bak
Copy-Item .dockerignore.ui .dockerignore

# 2. デプロイ
gcloud run deploy fixed-asset-agentic-ui --source . --region asia-northeast1 --set-env-vars "API_URL=https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

# 3. 元に戻す
Copy-Item Dockerfile.api.bak Dockerfile
Copy-Item .dockerignore.api.bak .dockerignore
Remove-Item Dockerfile.api.bak
Remove-Item .dockerignore.api.bak
```

### 一括実行版（コピペ用）

```powershell
Copy-Item Dockerfile Dockerfile.api.bak; Copy-Item Dockerfile.ui Dockerfile; Copy-Item .dockerignore .dockerignore.api.bak; Copy-Item .dockerignore.ui .dockerignore; gcloud run deploy fixed-asset-agentic-ui --source . --region asia-northeast1 --set-env-vars "API_URL=https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"; Copy-Item Dockerfile.api.bak Dockerfile; Copy-Item .dockerignore.api.bak .dockerignore; Remove-Item Dockerfile.api.bak; Remove-Item .dockerignore.api.bak
```

---

## 4. API + UI 両方更新

```powershell
# API
gcloud run deploy fixed-asset-agentic-api --source . --region asia-northeast1 --allow-unauthenticated --memory 1Gi --set-env-vars "PDF_CLASSIFY_ENABLED=1,GEMINI_PDF_ENABLED=1,GOOGLE_API_KEY=YOUR_API_KEY"

# UI（Dockerfile差し替え）
Copy-Item Dockerfile Dockerfile.api.bak; Copy-Item Dockerfile.ui Dockerfile; Copy-Item .dockerignore .dockerignore.api.bak; Copy-Item .dockerignore.ui .dockerignore; gcloud run deploy fixed-asset-agentic-ui --source . --region asia-northeast1 --set-env-vars "API_URL=https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"; Copy-Item Dockerfile.api.bak Dockerfile; Copy-Item .dockerignore.api.bak .dockerignore; Remove-Item Dockerfile.api.bak; Remove-Item .dockerignore.api.bak
```

---

## 5. 動作確認

```powershell
# API ヘルスチェック
curl https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health

# UI 確認（ブラウザで開く）
start https://fixed-asset-agentic-ui-986547623556.asia-northeast1.run.app
```

---

## サービスURL

| サービス | URL |
|---------|-----|
| API | https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app |
| UI | https://fixed-asset-agentic-ui-986547623556.asia-northeast1.run.app |

---

## トラブルシューティング

### ビルドログ確認

```powershell
gcloud builds list --region asia-northeast1 --limit 5
gcloud builds log BUILD_ID --region asia-northeast1
```

### 環境変数のみ更新

```powershell
# API
gcloud run services update fixed-asset-agentic-api --region asia-northeast1 --set-env-vars "KEY=VALUE"

# UI
gcloud run services update fixed-asset-agentic-ui --region asia-northeast1 --set-env-vars "API_URL=https://..."
```

### 認証設定（未認証アクセス許可）

```powershell
gcloud run services add-iam-policy-binding SERVICE_NAME --region asia-northeast1 --member="allUsers" --role="roles/run.invoker"
```
