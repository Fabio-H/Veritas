# Build Windows bundle and copy to ../release/ (see scripts/build_exe.py).
# Prerequisite: pip install ".[gui,dev,build]"
# Run from ps-deobfuscator:  .\scripts\pyinstaller_gui.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Running scripts/build_exe.py ..."
python scripts/build_exe.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$release = Join-Path (Split-Path -Parent $ProjectRoot) "release\ps-deobfuscator-gui\ps-deobfuscator-gui.exe"
if (Test-Path $release) {
    Write-Host "Executable: $release"
    Write-Host "Versioned zip is written to the root release folder."
} else {
    Write-Warning "Release copy not found at expected path."
}
