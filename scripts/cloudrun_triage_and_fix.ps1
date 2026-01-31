# Cloud Run: ContainerImageImportFailed triage and fix
# Run in an EXTERNAL terminal where gcloud works (gcloud auth login; gcloud config set project fixedassets-project).
# Cursor integrated terminal may hit WinError 5 on credentials.db -> use external terminal.
# Usage: .\scripts\cloudrun_triage_and_fix.ps1

$ErrorActionPreference = "Stop"
$Project = "fixedassets-project"
$Region = "asia-northeast1"
$Service = "fixed-asset-agentic-api"
$ImageRepo = "asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy/fixed-asset-agentic-api"

# --- 1) Fetch full failure message ---
Write-Host "`n=== 1) Fetch full failure message ===" -ForegroundColor Cyan
Write-Host "Service status and latest revision:" -ForegroundColor Yellow
gcloud run services describe $Service --region $Region --project $Project --format="yaml(status.conditions,status.latestCreatedRevisionName)"

$Latest = gcloud run services describe $Service --region $Region --project $Project --format="value(status.latestCreatedRevisionName)"
if (-not $Latest) {
    Write-Host "Could not get latest revision name. Stop." -ForegroundColor Red
    exit 1
}

Write-Host "`nRevision status and containers (latest=$Latest):" -ForegroundColor Yellow
gcloud run revisions describe $Latest --region $Region --project $Project --format="yaml(status.conditions,spec.containers)"

# --- 2) Runtime SA and IAM ---
Write-Host "`n=== 2) Runtime SA and IAM ===" -ForegroundColor Cyan
$SvcAccount = gcloud run services describe $Service --region $Region --project $Project --format="value(spec.template.spec.serviceAccountName)"
$ProjectNumber = gcloud projects describe $Project --format="value(projectNumber)"

if (-not $ProjectNumber) {
    Write-Host "Could not get project number. Stop." -ForegroundColor Red
    exit 1
}

$RuntimeSA = $SvcAccount
if ([string]::IsNullOrWhiteSpace($RuntimeSA)) {
    $RuntimeSA = "${ProjectNumber}-compute@developer.gserviceaccount.com"
    Write-Host "serviceAccountName is empty; using default runtime SA: $RuntimeSA" -ForegroundColor Gray
} else {
    Write-Host "Runtime SA: $RuntimeSA" -ForegroundColor Gray
}

$SvcAgent = "service-${ProjectNumber}@serverless-robot-prod.iam.gserviceaccount.com"
Write-Host "Cloud Run service agent: $SvcAgent" -ForegroundColor Gray

Write-Host "`nIf the revision status shows image pull / permission errors, run these IAM bindings:" -ForegroundColor Yellow
Write-Host "  gcloud projects add-iam-policy-binding $Project --member=`"serviceAccount:$RuntimeSA`" --role=`"roles/artifactregistry.reader`"" -ForegroundColor White
Write-Host "  gcloud projects add-iam-policy-binding $Project --member=`"serviceAccount:$SvcAgent`" --role=`"roles/artifactregistry.reader`"" -ForegroundColor White
$doIam = Read-Host "Run these IAM bindings now? (y/N)"
$IamDone = $false
if ($doIam -eq 'y' -or $doIam -eq 'Y') {
    gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$RuntimeSA" --role="roles/artifactregistry.reader"
    gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$SvcAgent" --role="roles/artifactregistry.reader"
    Write-Host "IAM bindings applied." -ForegroundColor Green
    $IamDone = $true
}

# --- 3) List image digests and redeploy (no build) ---
Write-Host "`n=== 3) List image digests and redeploy (no build) ===" -ForegroundColor Cyan
Write-Host "Listing images in Artifact Registry (pick sha256 from latest row):" -ForegroundColor Yellow
gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy --include-tags --project $Project

$Digest = Read-Host "`nPaste the FULL sha256 digest (64 hex chars; with or without 'sha256:' prefix)"
if ([string]::IsNullOrWhiteSpace($Digest)) {
    Write-Host "No digest; skipping deploy." -ForegroundColor Yellow
} else {
    $Digest = $Digest.Trim() -replace '^sha256:',''
    # Validate: exactly 64 hex characters
    if (-not ($Digest -match '^[0-9a-fA-F]{64}$')) {
        Write-Host "Invalid digest: must be 64 hex chars (e.g. abc123...). Got length=$($Digest.Length). Skipping deploy." -ForegroundColor Red
    } else {
        Write-Host "Deploying $ImageRepo@sha256:$Digest ..." -ForegroundColor Yellow
        gcloud run deploy $Service --image "${ImageRepo}@sha256:${Digest}" --region $Region --allow-unauthenticated --project $Project
    }
}

# --- 4) Confirm Ready=True and CLOUD_RUN_URL ---
Write-Host "`n=== 4) Confirm Ready=True and CLOUD_RUN_URL ===" -ForegroundColor Cyan
gcloud run services describe $Service --region $Region --project $Project --format="yaml(status.conditions,status.url)"

$Url = gcloud run services describe $Service --region $Region --project $Project --format="value(status.url)"
Write-Host "`nRun smoke test:" -ForegroundColor Green
Write-Host "  `$env:CLOUD_RUN_URL = `"$Url`"" -ForegroundColor White
Write-Host "  .\scripts\smoke_cloudrun.ps1" -ForegroundColor White

# --- 報告時に貼るべき3点 ---
Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor Magenta
Write-Host " [REPORT] 報告時に貼るべき3点 " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "`n(1) services describe の完全出力" -ForegroundColor Yellow
Write-Host "    次のコマンドを実行し、出力全体をコピーして貼り付ける:" -ForegroundColor Gray
Write-Host "    gcloud run services describe $Service --region $Region --project $Project --format=`"yaml(status.conditions,status.latestCreatedRevisionName,status.url)`"" -ForegroundColor White
Write-Host "`n(2) revisions describe の完全出力" -ForegroundColor Yellow
Write-Host "    上記の status.latestCreatedRevisionName を <LATEST_REVISION> に代入し、出力全体を貼り付ける:" -ForegroundColor Gray
Write-Host "    gcloud run revisions describe <LATEST_REVISION> --region $Region --project $Project --format=`"yaml(status.conditions,spec.containers)`"" -ForegroundColor White
Write-Host "`n(3) IAM 実行の有無" -ForegroundColor Yellow
if ($IamDone) {
    Write-Host "    -> 本実行で IAM を適用済み (roles/artifactregistry.reader を Runtime SA と Service Agent に付与)" -ForegroundColor Green
} else {
    Write-Host "    -> 本実行では IAM は未実施。手動で付与した場合はその旨を記載すること。" -ForegroundColor Gray
}
Write-Host ""
