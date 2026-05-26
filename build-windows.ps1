# Build ScreenOffTimer.exe on Windows 10+
# Usage: powershell -ExecutionPolicy Bypass -File build-windows.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "==> Generate icons"
python scripts/generate_icon.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Install PyInstaller"
python -m pip install --upgrade pip pyinstaller pillow
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Build exe"
python -m PyInstaller --noconfirm ScreenOffTimer.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Exe = Join-Path $Root "dist\ScreenOffTimer.exe"
if (Test-Path $Exe) {
    Write-Host ""
    Write-Host "Built: $Exe"
    Get-Item $Exe | Format-List Name, Length, LastWriteTime
} else {
    Write-Error "dist\ScreenOffTimer.exe not found"
    exit 1
}
