# Smoke test script for Cloud Run deployment
# Tests /health, /classify, and /classify_pdf OFF (feature-flag default)

$ErrorActionPreference = "Stop"

# Get Cloud Run URL from environment or use default
$CloudRunUrl = $env:CLOUD_RUN_URL
if (-not $CloudRunUrl) {
    $CloudRunUrl = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"
    Write-Host "Using default URL: $CloudRunUrl" -ForegroundColor Yellow
}

Write-Host "`n=== Cloud Run Smoke Test ===" -ForegroundColor Cyan
Write-Host "URL: $CloudRunUrl`n" -ForegroundColor Gray

# Test /health
Write-Host "1. Testing /health..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$CloudRunUrl/health" -Method Get
    if ($healthResponse.ok -eq $true) {
        Write-Host "   ✓ /health: OK" -ForegroundColor Green
    } else {
        Write-Host "   ✗ /health: Unexpected response" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ✗ /health: Failed - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test /classify
Write-Host "`n2. Testing /classify..." -ForegroundColor Yellow
$classifyPayload = @{
    opal_json = @{
        invoice_date = "2024-01-01"
        vendor = "ACME Corp"
        line_items = @(
            @{
                item_description = "server install"
                amount = 5000
                quantity = 1
            }
        )
    }
} | ConvertTo-Json -Depth 10

try {
    $classifyResponse = Invoke-RestMethod -Uri "$CloudRunUrl/classify" -Method Post -Body $classifyPayload -ContentType "application/json"
    
    # Check required fields
    $requiredFields = @("decision", "is_valid_document", "confidence", "trace", "missing_fields", "why_missing_matters")
    $allPresent = $true
    foreach ($field in $requiredFields) {
        if (-not (Get-Member -InputObject $classifyResponse -Name $field -ErrorAction SilentlyContinue)) {
            Write-Host "   ✗ Missing field: $field" -ForegroundColor Red
            $allPresent = $false
        }
    }
    
    if ($allPresent) {
        Write-Host "   ✓ /classify: OK" -ForegroundColor Green
        Write-Host "   Decision: $($classifyResponse.decision)" -ForegroundColor Gray
        Write-Host "   Valid Document: $($classifyResponse.is_valid_document)" -ForegroundColor Gray
        Write-Host "   Confidence: $($classifyResponse.confidence)" -ForegroundColor Gray
        Write-Host "   Trace: $($classifyResponse.trace -join ', ')" -ForegroundColor Gray
    } else {
        Write-Host "   ✗ /classify: Missing required fields" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ✗ /classify: Failed - $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Gray
    }
    exit 1
}

# Test /classify_pdf OFF (feature flag default; expect 400 + detail.error=PDF_CLASSIFY_DISABLED)
Write-Host "`n3. Testing /classify_pdf (expect OFF, 400)..." -ForegroundColor Yellow
$pdfPath = Join-Path $PSScriptRoot "..\tests\fixtures\sample_text.pdf"
if (-not (Test-Path $pdfPath)) {
    Write-Host "   Skip: $pdfPath not found" -ForegroundColor Yellow
} else {
    try {
        $form = @{ file = Get-Item -LiteralPath $pdfPath }
        Invoke-WebRequest -Uri "$CloudRunUrl/classify_pdf" -Method Post -Form $form -UseBasicParsing | Out-Null
        Write-Host "   ✗ /classify_pdf: Expected 400 (OFF), got 200" -ForegroundColor Red
        exit 1
    } catch {
        $resp = $_.Exception.Response
        if (-not $resp) {
            Write-Host "   ✗ /classify_pdf: No response (e.g. connection failed) - $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
        $status = [int]$resp.StatusCode
        if ($status -eq 400) {
            $stream = $resp.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $body = $reader.ReadToEnd() | ConvertFrom-Json
            $reader.Close(); $stream.Close()
            $err = $body.detail
            if ($err -and $err.error -eq "PDF_CLASSIFY_DISABLED") {
                Write-Host "   ✓ /classify_pdf OFF: 400 + detail.error=PDF_CLASSIFY_DISABLED" -ForegroundColor Green
            } else {
                Write-Host "   ✗ /classify_pdf: 400 but detail.error mismatch (got: $($err.error))" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "   ✗ /classify_pdf: Expected 400, got $status - $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "`n=== All smoke tests passed ===" -ForegroundColor Green
