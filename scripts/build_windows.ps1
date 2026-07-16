[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$BuildInstaller,
    [string]$PythonPath,
    [string]$InnoSetupCompiler
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Test-PythonExecutable {
    param([string]$Candidate)

    if (-not $Candidate -or -not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
        return $false
    }
    try {
        $VersionOutput = & $Candidate --version 2>&1
        return $LASTEXITCODE -eq 0 -and "$VersionOutput" -match '^Python 3\.'
    } catch {
        return $false
    }
}

function Resolve-PythonExecutable {
    $Candidates = @()
    if ($PythonPath) {
        $Candidates += $PythonPath
    }
    if ($env:LOCALAPPDATA) {
        $Candidates += Join-Path $env:LOCALAPPDATA "Python\bin\python.exe"
        $Candidates += Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA "Programs\Python\Python*\python.exe") `
            -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    }
    $Candidates += Get-Command python.exe -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source

    foreach ($Candidate in ($Candidates | Where-Object { $_ } | Select-Object -Unique)) {
        if (Test-PythonExecutable $Candidate) {
            return $Candidate
        }
    }
    throw "Python 3 was not found. Install Python 3.11 or newer, or pass -PythonPath C:\path\to\python.exe."
}

function Resolve-InnoSetupCompiler {
    $Candidates = @()
    if ($InnoSetupCompiler) {
        $Candidates += $InnoSetupCompiler
    }
    $Command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($Command) {
        $Candidates += $Command.Source
    }
    if ($env:LOCALAPPDATA) {
        $Candidates += Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
    }
    if (${env:ProgramFiles(x86)}) {
        $Candidates += Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
    }
    if ($env:ProgramFiles) {
        $Candidates += Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"
    }

    foreach ($Candidate in ($Candidates | Where-Object { $_ } | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return $Candidate
        }
    }
    throw "Inno Setup 6 was not found. Install it, or pass -InnoSetupCompiler C:\path\to\ISCC.exe."
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath failed with exit code $LASTEXITCODE."
    }
}

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "The Windows executable must be built on Windows."
}

$PythonExe = Resolve-PythonExecutable
Write-Host "Using Python: $PythonExe"

if (-not $SkipInstall) {
    Invoke-Checked $PythonExe @("-m", "pip", "install", "-r", "requirements.txt", "pyinstaller>=6.0,<7.0")
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Invoke-Checked $PythonExe @("scripts/generate_windows_version_info.py", "build/windows_version_info.txt")
Invoke-Checked $PythonExe @("-m", "PyInstaller", "--clean", "--noconfirm", "SuperElevation.spec")

$Hash = Get-FileHash dist/SuperElevation.exe -Algorithm SHA256
"$($Hash.Hash.ToLower())  SuperElevation.exe" | Set-Content -Encoding ascii dist/SHA256SUMS.txt

if ($BuildInstaller) {
    $Version = & $PythonExe -c "from app_info import APP_VERSION; print(APP_VERSION)"
    if ($LASTEXITCODE -ne 0) {
        throw "$PythonExe could not read the application version."
    }
    $Iscc = Resolve-InnoSetupCompiler
    Write-Host "Using Inno Setup: $Iscc"
    Invoke-Checked $Iscc @("/DMyAppVersion=$($Version.Trim())", "packaging/Superelevation.iss")
}

Write-Host "Built dist/SuperElevation.exe and dist/SHA256SUMS.txt"
