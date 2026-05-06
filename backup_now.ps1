Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Resolve paths from the script's own location -- avoids encoding issues
# with accented folder names (Area de Trabalho).
$PROJETO  = $PSScriptRoot                        # the folder this script lives in
$GIT_DIR  = Join-Path $PROJETO 'ps-deobfuscator'
$DESKTOP  = [Environment]::GetFolderPath('Desktop')
$TS       = Get-Date -Format 'yyyyMMdd_HHmm'
$ZIP_DST  = Join-Path $DESKTOP "PROJETO_backup_$TS.zip"
$SRC_DST  = Join-Path $DESKTOP "ps-deobfuscator_src_$TS"

$SEP = '=' * 60

function Info($msg) { Write-Host "  $msg" -ForegroundColor DarkGray }
function OK($msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function WARN($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function FAIL($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Head($n,$msg) { Write-Host "`n$SEP`nSTEP $n -- $msg`n$SEP" -ForegroundColor Cyan }

# Sanity check before doing anything
if (-not (Test-Path $GIT_DIR)) {
    Write-Host "ERROR: Could not find $GIT_DIR" -ForegroundColor Red
    Write-Host "Script location: $PSScriptRoot" -ForegroundColor Red
    Write-Host 'Press Enter to close...' -NoNewline
    $null = Read-Host
    exit 1
}
Info "PROJETO  : $PROJETO"
Info "GIT_DIR  : $GIT_DIR"
Info "ZIP dest : $ZIP_DST"
Info "SRC dest : $SRC_DST"

# ---------------------------------------------------------------------------
Head 'A' 'git add + commit + push'
# ---------------------------------------------------------------------------
Push-Location $GIT_DIR
try {
    $dirty = & git status --porcelain 2>&1
    if ($dirty) {
        Info 'Uncommitted changes found -- staging all...'
        & git add -A
        & git commit -m "chore: pre-cleanup snapshot $TS"
        OK 'Changes committed.'
    } else {
        OK 'Working tree is clean -- nothing to commit.'
    }

    Info 'Pushing to remote...'
    & git push 2>&1 | ForEach-Object { Info $_ }
    if ($LASTEXITCODE -eq 0) {
        OK 'git push succeeded.'
    } else {
        WARN 'git push returned a non-zero exit code.'
        WARN 'Local backups (B + C) will still run.'
    }
} catch {
    WARN "git step error: $_"
    WARN 'Continuing with local backups.'
} finally {
    Pop-Location
}

# ---------------------------------------------------------------------------
Head 'B' "Full PROJETO ZIP -> $ZIP_DST"
# ---------------------------------------------------------------------------
Info 'Compressing -- may take 1-3 minutes (includes binaries)...'
try {
    Compress-Archive -Path $PROJETO -DestinationPath $ZIP_DST -CompressionLevel Fastest
    $zip_mb = [math]::Round((Get-Item $ZIP_DST).Length / 1MB, 0)
    OK "ZIP created ($zip_mb MB) : $ZIP_DST"

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip_obj   = [System.IO.Compression.ZipFile]::OpenRead($ZIP_DST)
    $zip_count = $zip_obj.Entries.Count
    $zip_obj.Dispose()
    OK "Archive integrity OK -- $zip_count entries."
} catch {
    FAIL "ZIP creation failed: $_"
}

# ---------------------------------------------------------------------------
Head 'C' "Source-only copy -> $SRC_DST"
# ---------------------------------------------------------------------------
Info 'Copying source (excluding build/, dist/, __pycache__, *.pyc)...'
try {
    robocopy $GIT_DIR $SRC_DST `
        /E /DCOPY:T /R:1 /W:1 /NP /NFL /NDL `
        /XD 'build' 'dist' '__pycache__' '.mypy_cache' '.ruff_cache' '.pytest_cache' `
        /XF '*.pyc' | Out-Null

    if ($LASTEXITCODE -le 7) {
        $src_files = (Get-ChildItem $SRC_DST -Recurse -File).Count
        $src_kb    = [math]::Round(
            (Get-ChildItem $SRC_DST -Recurse -File |
             Measure-Object -Property Length -Sum).Sum / 1KB, 0)
        OK "Copied $src_files files, $src_kb KB"
        OK "Location: $SRC_DST"
    } else {
        FAIL "robocopy exited with code $LASTEXITCODE"
    }
} catch {
    FAIL "Source copy failed: $_"
}

# ---------------------------------------------------------------------------
Head 'D' 'Verification report'
# ---------------------------------------------------------------------------
$results = @()

Push-Location $GIT_DIR
try {
    $remote = & git ls-remote origin HEAD 2>&1
    if ($LASTEXITCODE -eq 0) {
        $sha = ($remote -split '\s+')[0].Substring(0, [math]::Min(12, ($remote -split '\s+')[0].Length))
        $results += [PSCustomObject]@{ Check = 'GitHub remote HEAD'; Status = 'OK'; Detail = $sha }
    } else {
        $results += [PSCustomObject]@{ Check = 'GitHub remote HEAD'; Status = 'WARN'; Detail = 'Could not verify' }
    }
} catch {
    $results += [PSCustomObject]@{ Check = 'GitHub remote HEAD'; Status = 'WARN'; Detail = 'Network error' }
} finally {
    Pop-Location
}

if (Test-Path $ZIP_DST) {
    $sz = [math]::Round((Get-Item $ZIP_DST).Length / 1MB, 0)
    $results += [PSCustomObject]@{ Check = 'Full ZIP archive'; Status = 'OK'; Detail = "$sz MB at Desktop" }
} else {
    $results += [PSCustomObject]@{ Check = 'Full ZIP archive'; Status = 'FAIL'; Detail = 'File not found' }
}

if (Test-Path $SRC_DST) {
    $fc = (Get-ChildItem $SRC_DST -Recurse -File).Count
    $results += [PSCustomObject]@{ Check = 'Source-only copy'; Status = 'OK'; Detail = "$fc files at Desktop" }
} else {
    $results += [PSCustomObject]@{ Check = 'Source-only copy'; Status = 'FAIL'; Detail = 'Folder not found' }
}

Write-Host ''
$results | Format-Table -AutoSize

$failures = $results | Where-Object { $_.Status -eq 'FAIL' }
if ($failures) {
    Write-Host 'BACKUP INCOMPLETE -- review FAIL items before deleting anything.' -ForegroundColor Red
} else {
    Write-Host 'BACKUP COMPLETE -- safe to proceed with cleanup.' -ForegroundColor Green
    Write-Host ''
    Write-Host 'Rollback reference:' -ForegroundColor DarkGray
    Write-Host "  Any file  : Expand-Archive '$ZIP_DST' -DestinationPath <path>" -ForegroundColor DarkGray
    Write-Host "  Source    : copy from $SRC_DST" -ForegroundColor DarkGray
    Write-Host '  GitHub    : git clone https://github.com/Fabio-H/Veritas.git' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host 'Press Enter to close...' -NoNewline
$null = Read-Host
