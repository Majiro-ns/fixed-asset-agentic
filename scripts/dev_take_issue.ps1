param(
    [Parameter(Mandatory = $true)][int]$IssueNumber,
    [string]$CommitMessage
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required"
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "gh CLI is required (https://cli.github.com/)"
}
try {
    gh auth status | Out-Null
} catch {
    throw "gh CLI is not authenticated. Run 'gh auth login' before scripts/dev_take_issue.ps1."
}

$branch = "ai/issue-$IssueNumber"
$CommitMessage = if ($CommitMessage) { $CommitMessage } else { "chore: close #$IssueNumber" }

$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
$dirty = git status --porcelain

Write-Host "[dev_take_issue] target branch:" $branch

git fetch origin main

if ($currentBranch -ne $branch) {
    if ($dirty) {
        throw "Working tree has uncommitted changes on $currentBranch. Commit/stash before switching."
    }
    Write-Host "[dev_take_issue] updating main then switching to $branch"
    git checkout main
    git pull --ff-only origin main
    git checkout -B $branch
} else {
    Write-Host "[dev_take_issue] already on $branch; continuing"
}

Write-Host "[dev_take_issue] running quality gate..."
& "$PSScriptRoot/dev_run_checks.ps1"

$pending = git status --porcelain
if (-not $pending) {
    throw "No changes to commit. Apply work for issue $IssueNumber, then rerun."
}

Write-Host "[dev_take_issue] staging and committing..."
git add .
git commit -m $CommitMessage

Write-Host "[dev_take_issue] pushing to origin..."
git push -u origin $branch

Write-Host "[dev_take_issue] creating PR..."
$prTitle = "Issue #$IssueNumber"
$prBody = "Closes #$IssueNumber"
$prUrl = (& gh pr create --head $branch --base main --title $prTitle --body $prBody).Trim()
Write-Host "[dev_take_issue] PR created: $prUrl"

Write-Host "[dev_take_issue] watching CI checks..."
& gh pr checks --watch $prUrl

Write-Host "[dev_take_issue] done"
