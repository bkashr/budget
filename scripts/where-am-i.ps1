param(
    [string]$ExpectedRepoName = "budget",
    [string]$ExpectedBranch = "main"
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "=== $Title ==="
}

Write-Section "Workspace"
$cwd = (Get-Location).Path
Write-Host "Current directory: $cwd"

try {
    $repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
} catch {
    Write-Host "Not inside a git repository."
    exit 1
}

Write-Host "Git root: $repoRoot"

$repoName = Split-Path $repoRoot -Leaf
$currentBranch = (git branch --show-current).Trim()
$headSha = (git rev-parse --short HEAD).Trim()
$remotes = git remote -v
$status = git status --short

Write-Section "Git Identity"
Write-Host "Repo name: $repoName"
Write-Host "Branch: $currentBranch"
Write-Host "HEAD: $headSha"
Write-Host ""
Write-Host "Remotes:"
$remotes | ForEach-Object { Write-Host "  $_" }

Write-Section "Sync Check"
Write-Host "Expected repo name: $ExpectedRepoName"
Write-Host "Expected branch: $ExpectedBranch"

$ok = $true

if ($repoName -ne $ExpectedRepoName) {
    Write-Host "WARNING: repo name mismatch."
    $ok = $false
}

if ($currentBranch -ne $ExpectedBranch) {
    Write-Host "WARNING: branch mismatch."
    $ok = $false
}

try {
    git fetch origin | Out-Null
    $line = (git rev-list --left-right --count "origin/$currentBranch...$currentBranch").Trim()
    $parts = ($line -split '\s+') | Where-Object { $_ -ne "" }

    if ($parts.Count -ge 2) {
        $behind = [int]$parts[0]
        $ahead = [int]$parts[1]
        Write-Host "Behind origin/${currentBranch}: $behind"
        Write-Host "Ahead of origin/${currentBranch}: $ahead"
    } else {
        Write-Host "Could not parse ahead/behind status. Raw: $line"
        $ok = $false
    }
} catch {
    Write-Host "WARNING: Unable to fetch or compute ahead/behind."
    $ok = $false
}

Write-Section "Working Tree"
if ($status) {
    Write-Host "Uncommitted changes:"
    $status | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "Clean working tree."
}

Write-Section "Result"
if ($ok) {
    Write-Host "Repository identity checks passed."
    exit 0
}

Write-Host "Repository identity checks found issues."
exit 2
