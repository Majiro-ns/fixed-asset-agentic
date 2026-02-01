# Deploy Streamlit UI to Cloud Run via Artifact Registry
# Usage: .\scripts\deploy_ui.ps1
# Run from project root: cd /path/to/fixed-asset-ashigaru && .\scripts\deploy_ui.ps1

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "because-and-or"
$REGION = "asia-northeast1"
$SERVICE_NAME = "fixed-asset-ui"
$REPOSITORY = "fixed-asset-repo"
$IMAGE_NAME = "fixed-asset-ui"
$API_BASE_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

# Artifact Registry full image path
$AR_HOST = "${REGION}-docker.pkg.dev"
$IMAGE_TAG = "${AR_HOST}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"

Write-Host "`n=== Deploying Streamlit UI to Cloud Run ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION" -ForegroundColor Gray
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Gray
Write-Host "Image: $IMAGE_TAG" -ForegroundColor Gray
Write-Host "API URL: $API_BASE_URL" -ForegroundColor Gray

# Step 1: Configure Docker for Artifact Registry
Write-Host "`n[1/4] Configuring Docker authentication..." -ForegroundColor Yellow
gcloud auth configure-docker $AR_HOST --quiet

# Step 2: Build Docker image using ui/Dockerfile
Write-Host "`n[2/4] Building Docker image..." -ForegroundColor Yellow
Write-Host "Using: ui/Dockerfile" -ForegroundColor Gray

# Ensure we're in project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

docker build -f ui/Dockerfile -t $IMAGE_TAG .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

# Step 3: Push to Artifact Registry
Write-Host "`n[3/4] Pushing to Artifact Registry..." -ForegroundColor Yellow
docker push $IMAGE_TAG
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker push failed!" -ForegroundColor Red
    exit 1
}

# Step 4: Deploy to Cloud Run
Write-Host "`n[4/4] Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_TAG `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --set-env-vars "API_BASE_URL=$API_BASE_URL" `
    --memory 512Mi `
    --cpu 1 `
    --port 8501 `
    --timeout 60

if ($LASTEXITCODE -ne 0) {
    Write-Host "Cloud Run deploy failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Yellow

# Get and display the service URL
$serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)"
Write-Host "UI URL: $serviceUrl" -ForegroundColor Cyan
