# Smoke test script for Cloud Run deployment
# Tests /health and /classify endpoints

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

Write-Host "`n=== All tests passed ===" -ForegroundColor Green
