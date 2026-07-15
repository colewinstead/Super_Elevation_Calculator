[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$BuildInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "The Windows executable must be built on Windows."
}

if (-not $SkipInstall) {
    python -m pip install -r requirements.txt "pyinstaller>=6.0,<7.0"
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
python scripts/generate_windows_version_info.py build/windows_version_info.txt
python -m PyInstaller --clean --noconfirm SuperElevation.spec

$Hash = Get-FileHash dist/SuperElevation.exe -Algorithm SHA256
"$($Hash.Hash.ToLower())  SuperElevation.exe" | Set-Content -Encoding ascii dist/SHA256SUMS.txt

if ($BuildInstaller) {
    $Version = python -c "from app_info import APP_VERSION; print(APP_VERSION)"
    $Iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if (-not $Iscc) {
        throw "Inno Setup 6 (iscc.exe) is required when -BuildInstaller is selected."
    }
    & $Iscc.Source "/DMyAppVersion=$Version" packaging/Superelevation.iss
}

Write-Host "Built dist/SuperElevation.exe and dist/SHA256SUMS.txt"
