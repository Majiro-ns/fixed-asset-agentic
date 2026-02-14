# Deploy Streamlit UI to Cloud Run
# Usage: .\deploy_ui.ps1
# Override defaults via environment variables:
#   $env:PROJECT_ID = "my-project"; $env:REGION = "us-central1"; .\deploy_ui.ps1

$PROJECT_ID = if ($env:PROJECT_ID) { $env:PROJECT_ID } else { "because-and-or" }
$REGION = if ($env:REGION) { $env:REGION } else { "asia-northeast1" }
$SERVICE_NAME = "fixed-asset-agentic-ui"
$API_URL = if ($env:API_URL) { $env:API_URL } else { "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app" }

Write-Host "=== Deploying Streamlit UI to Cloud Run ===" -ForegroundColor Cyan
Write-Host "  PROJECT_ID: $PROJECT_ID" -ForegroundColor Gray
Write-Host "  REGION:     $REGION" -ForegroundColor Gray
Write-Host "  API_URL:    $API_URL" -ForegroundColor Gray

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
