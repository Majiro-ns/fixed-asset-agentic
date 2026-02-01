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

# gh は「あるなら使う」。無ければPR作成/チェック監視をスキップして成功終了できるようにする
$hasGh = [bool](Get-Command gh -ErrorAction SilentlyContinue)
$ghAuthed = $false
if ($hasGh) {
    try {
        gh auth status | Out-Null
        $ghAuthed = $true
    } catch {
        # CI等で未認証でも「実装・コミット・push」までは行えるため、PR関連のみスキップ可能にする
        $ghAuthed = $false
    }
}

$branch = "ai/issue-$IssueNumber"
$CommitMessage = if ($CommitMessage) { $CommitMessage } else { "chore: close #$IssueNumber" }

$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
$dirty = git status --porcelain

Write-Host "[dev_take_issue] target branch: $branch"

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
    Write-Host "[dev_take_issue] NO_CHANGES: nothing to commit for issue $IssueNumber. Exiting 0."
    exit 0
}

Write-Host "[dev_take_issue] staging and committing..."
git add .
git commit -m $CommitMessage

Write-Host "[dev_take_issue] pushing to origin..."
git push -u origin $branch

# PR作成は gh が使える場合のみ（CI/ローカル差分に耐える）
if (-not $hasGh) {
    Write-Host "[dev_take_issue] GH_MISSING: gh CLI not found. Skipping PR creation. Exiting 0."
    exit 0
}
if (-not $ghAuthed) {
    Write-Host "[dev_take_issue] GH_NOT_AUTHED: gh CLI not authenticated. Skipping PR creation. Exiting 0."
    exit 0
}

Write-Host "[dev_take_issue] creating PR..."
$prTitle = "Issue #$IssueNumber"
$prBody = "Closes #$IssueNumber"
$prUrl = (& gh pr create --head $branch --base main --title $prTitle --body $prBody).Trim()
Write-Host "[dev_take_issue] PR created: $prUrl"

Write-Host "[dev_take_issue] watching CI checks..."
& gh pr checks --watch $prUrl

Write-Host "[dev_take_issue] done"
