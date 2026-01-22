# Fixed Asset Classification Demo UI Launcher
# Launches Streamlit UI from repo root with guardrails.

$ErrorActionPreference = "Stop"

# Ensure we're in the repo root
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Host "ERROR: Not in a git repository. Please run from repo root." -ForegroundColor Red
    exit 1
}

Set-Location $repoRoot

# Check if ui/app_minimal.py exists
$uiPath = Join-Path $repoRoot "ui\app_minimal.py"
if (-not (Test-Path $uiPath)) {
    Write-Host "ERROR: ui/app_minimal.py not found at $uiPath" -ForegroundColor Red
    exit 1
}

# Check if streamlit is installed
try {
    $null = python -c "import streamlit" 2>$null
} catch {
    Write-Host "ERROR: streamlit not installed. Run: pip install streamlit" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Streamlit UI from repo root: $repoRoot" -ForegroundColor Green
Write-Host "UI file: $uiPath" -ForegroundColor Green
Write-Host ""

# Launch Streamlit
python -m streamlit run $uiPath
