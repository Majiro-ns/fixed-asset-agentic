# Docker local smoke: /health, /classify, /classify_pdf OFF (no gcloud)
# Run after: docker build -t fixed-asset-api . && docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api
# Usage: .\scripts\docker_smoke.ps1
# Env: DOCKER_SMOKE_URL (default http://localhost:8080). Exit 1 on failure.

$ErrorActionPreference = "Stop"
$BaseUrl = $env:DOCKER_SMOKE_URL
if (-not $BaseUrl) { $BaseUrl = "http://localhost:8080" }

Write-Host "`n=== Docker Local Smoke ===" -ForegroundColor Cyan
Write-Host "URL: $BaseUrl`n" -ForegroundColor Gray

# 1) /health
Write-Host "1. /health..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    if ($r.ok -ne $true) { Write-Host "   FAIL: ok != true" -ForegroundColor Red; exit 1 }
    Write-Host "   OK" -ForegroundColor Green
} catch { Write-Host "   FAIL: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }

# 2) /classify
Write-Host "`n2. /classify..." -ForegroundColor Yellow
$body = '{"opal_json":{"invoice_date":"2024-01-01","vendor":"ACME","line_items":[{"item_description":"server install","amount":5000,"quantity":1}]}}'
try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/classify" -Method Post -Body $body -ContentType "application/json"
    $need = @("decision","is_valid_document","confidence","trace","missing_fields","why_missing_matters")
    foreach ($k in $need) {
        if (-not (Get-Member -InputObject $r -Name $k -ErrorAction SilentlyContinue)) {
            Write-Host "   FAIL: missing $k" -ForegroundColor Red; exit 1
        }
    }
    Write-Host "   OK" -ForegroundColor Green
} catch { Write-Host "   FAIL: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }

# 3) /classify_pdf OFF -> 400 + detail.error=PDF_CLASSIFY_DISABLED, how_to_enable, fallback
Write-Host "`n3. /classify_pdf (expect 400, PDF_CLASSIFY_DISABLED)..." -ForegroundColor Yellow
$pdf = Join-Path (Split-Path $PSScriptRoot -Parent) "tests\fixtures\sample_text.pdf"
if (-not (Test-Path $pdf)) { Write-Host "   SKIP: $pdf not found" -ForegroundColor Yellow } else {
    try {
        $form = @{ file = Get-Item -LiteralPath $pdf }
        Invoke-WebRequest -Uri "$BaseUrl/classify_pdf" -Method Post -Form $form -UseBasicParsing | Out-Null
        Write-Host "   FAIL: expected 400, got 200" -ForegroundColor Red; exit 1
    } catch {
        $resp = $_.Exception.Response
        if (-not $resp) { Write-Host "   FAIL: no response - $($_.Exception.Message)" -ForegroundColor Red; exit 1 }
        if ([int]$resp.StatusCode -ne 400) { Write-Host "   FAIL: expected 400, got $([int]$resp.StatusCode)" -ForegroundColor Red; exit 1 }
        $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $json = $sr.ReadToEnd() | ConvertFrom-Json; $sr.Close()
        $d = $json.detail
        if (-not $d) { Write-Host "   FAIL: detail missing" -ForegroundColor Red; exit 1 }
        if ($d.error -ne "PDF_CLASSIFY_DISABLED") { Write-Host "   FAIL: detail.error != PDF_CLASSIFY_DISABLED (got: $($d.error))" -ForegroundColor Red; exit 1 }
        if (-not $d.how_to_enable) { Write-Host "   FAIL: detail.how_to_enable missing" -ForegroundColor Red; exit 1 }
        if (-not $d.fallback) { Write-Host "   FAIL: detail.fallback missing" -ForegroundColor Red; exit 1 }
        Write-Host "   OK" -ForegroundColor Green
    }
}

Write-Host "`n=== All docker smoke tests passed ===" -ForegroundColor Green
