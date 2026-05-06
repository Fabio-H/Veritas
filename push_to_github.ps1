Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$REPO = $PSScriptRoot
$SEP  = '=' * 60

function Info($m) { Write-Host "  $m" -ForegroundColor DarkGray }
function OK($m)   { Write-Host "  [OK]   $m" -ForegroundColor Green }
function WARN($m) { Write-Host "  [WARN] $m" -ForegroundColor Yellow }
function FAIL($m) { Write-Host "  [FAIL] $m" -ForegroundColor Red; exit 1 }
function Head($m) { Write-Host "`n$SEP`n$m`n$SEP" -ForegroundColor Cyan }

if (-not (Test-Path (Join-Path $REPO '.git'))) {
    FAIL "No .git found at $REPO -- run from PROJETO folder."
}

Set-Location $REPO
Info "Repository: $REPO"

# ── 1. Show current status ──────────────────────────────────────────────────
Head '1 / 4 -- git status'
$status = & git status --short 2>&1
if ($status) {
    Write-Host $status
    Info 'Uncommitted changes found above.'
} else {
    OK 'Working tree is clean.'
}

# ── 2. Stage + commit if there is anything new ─────────────────────────────
Head '2 / 4 -- stage and commit'
$dirty = & git status --porcelain 2>&1
if ($dirty) {
    Info 'Staging all changes...'
    & git add -A

    $TS  = Get-Date -Format 'yyyy-MM-dd HH:mm'
    $MSG = "feat: Veritas v0.1.0 -- PySide6 GUI, IOC table redesign, English labels, layout fixes ($TS)"
    & git commit -m $MSG
    if ($LASTEXITCODE -ne 0) { FAIL 'git commit failed.' }
    OK "Committed: $MSG"
} else {
    OK 'Nothing to commit -- will push existing HEAD.'
}

# ── 3. Show what will be pushed ─────────────────────────────────────────────
Head '3 / 4 -- commits to push'
$log = & git log --oneline 2>&1
Write-Host $log
Info 'These commits will be sent to origin/main.'

# ── 4. Push ─────────────────────────────────────────────────────────────────
Head '4 / 4 -- git push'
Info 'Pushing to origin main...'
& git push -u origin main 2>&1 | ForEach-Object { Info $_ }

if ($LASTEXITCODE -eq 0) {
    OK 'Push succeeded.'
    Write-Host ''
    Write-Host 'Repository updated:' -ForegroundColor Green
    Write-Host '  https://github.com/Fabio-H/Veritas' -ForegroundColor Cyan
} else {
    Write-Host ''
    WARN 'git push returned a non-zero exit code.'
    Write-Host ''
    Write-Host 'Common fixes:' -ForegroundColor Yellow
    Write-Host '  Auth error  : run  git push -u origin main  in a terminal and log in.' -ForegroundColor DarkGray
    Write-Host '  No remote   : run  git remote add origin https://github.com/Fabio-H/Veritas.git' -ForegroundColor DarkGray
    Write-Host '  Diverged    : run  git pull --rebase origin main  then push again.' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host 'Press Enter to close...' -NoNewline
$null = Read-Host
