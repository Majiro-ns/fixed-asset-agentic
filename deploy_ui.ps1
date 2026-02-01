# Deploy Streamlit UI to Cloud Run
# Usage: .\deploy_ui.ps1

$PROJECT_ID = "because-and-or"  # 必要に応じて変更
$REGION = "asia-northeast1"
$SERVICE_NAME = "fixed-asset-agentic-ui"
$API_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

Write-Host "=== Deploying Streamlit UI to Cloud Run ===" -ForegroundColor Cyan

# Build and deploy using Dockerfile.ui
gcloud run deploy $SERVICE_NAME `
    --source . `
    --dockerfile Dockerfile.ui `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars "API_URL=$API_URL" `
    --memory 512Mi `
    --cpu 1 `
    --timeout 60

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "UI URL: https://$SERVICE_NAME-*.run.app" -ForegroundColor Yellow
