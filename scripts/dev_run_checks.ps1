param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

Write-Host "[dev_run_checks] repo: $repoRoot"

if (-not $SkipInstall) {
    Write-Host "[dev_run_checks] upgrading pip and installing deps..."
    python -m pip install --upgrade pip
    if (Test-Path "$repoRoot/requirements.txt") {
        python -m pip install -r "$repoRoot/requirements.txt"
    } else {
        Write-Host "[dev_run_checks] requirements.txt not found; skipping install"
    }
} else {
    Write-Host "[dev_run_checks] SkipInstall requested; using existing venv"
}

# Lint placeholder: add ruff/black/mypy here when available. Keep gate parity with CI.

Write-Host "[dev_run_checks] running pytest..."
python -m pytest

Write-Host "✅ checks ok"
