[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$BuildInstaller,
    [switch]$Sign,
    [string]$PythonPath,
    [string]$InnoSetupCompiler,
    [string]$CertificateThumbprint,
    [string]$PublisherName = "Cole Winstead",
    [string]$TimestampServer
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

function Resolve-CodeSigningCertificate {
    $Certificates = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
        Where-Object { $_.HasPrivateKey -and $_.NotAfter -gt (Get-Date) }

    if ($CertificateThumbprint) {
        $NormalizedThumbprint = $CertificateThumbprint.Replace(" ", "").ToUpperInvariant()
        $Certificate = $Certificates |
            Where-Object { $_.Thumbprint -eq $NormalizedThumbprint } |
            Select-Object -First 1
    } else {
        $Certificate = $Certificates |
            Where-Object {
                $_.Subject -eq "CN=$PublisherName" -and
                $_.Issuer -eq "CN=$PublisherName Pilot Root CA"
            } |
            Sort-Object NotAfter -Descending |
            Select-Object -First 1
    }

    if (-not $Certificate) {
        throw "No usable code-signing certificate was found for '$PublisherName'. Run scripts\new_pilot_signing_certificate.ps1 first, or pass -CertificateThumbprint."
    }
    return $Certificate
}

function Set-ReleaseSignature {
    param(
        [string]$Path,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate
    )

    $Parameters = @{
        FilePath = $Path
        Certificate = $Certificate
        HashAlgorithm = "SHA256"
    }
    if ($TimestampServer) {
        $Parameters.TimestampServer = $TimestampServer
    }

    Set-AuthenticodeSignature @Parameters | Out-Null
    $Signature = Get-AuthenticodeSignature -FilePath $Path
    if (-not $Signature.SignerCertificate -or
        $Signature.SignerCertificate.Thumbprint -ne $Certificate.Thumbprint -or
        $Signature.SignatureType -ne "Authenticode") {
        throw "Authenticode signing verification failed for $Path. Status: $($Signature.StatusMessage)"
    }
    Write-Host "Signed $Path with $($Certificate.Subject) ($($Certificate.Thumbprint))."
}

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "The Windows executable must be built on Windows."
}

$PythonExe = Resolve-PythonExecutable
Write-Host "Using Python: $PythonExe"

if (-not $SkipInstall) {
    Invoke-Checked $PythonExe @("-m", "pip", "install", "-r", "requirements-lock.txt", "pyinstaller>=6.0,<7.0")
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Invoke-Checked $PythonExe @("scripts/generate_windows_version_info.py", "build/windows_version_info.txt")
Invoke-Checked $PythonExe @("-m", "PyInstaller", "--clean", "--noconfirm", "SuperElevation.spec")

$SigningCertificate = $null
if ($Sign) {
    $SigningCertificate = Resolve-CodeSigningCertificate
    Set-ReleaseSignature -Path "dist/SuperElevation.exe" -Certificate $SigningCertificate
}

if ($BuildInstaller) {
    $Version = & $PythonExe -c "from app_info import APP_VERSION; print(APP_VERSION)"
    if ($LASTEXITCODE -ne 0) {
        throw "$PythonExe could not read the application version."
    }
    $Iscc = Resolve-InnoSetupCompiler
    Write-Host "Using Inno Setup: $Iscc"
    Invoke-Checked $Iscc @("/DMyAppVersion=$($Version.Trim())", "packaging/Superelevation.iss")

    if ($Sign) {
        $InstallerPath = "dist/SuperelevationCalculator-$($Version.Trim())-Setup.exe"
        Set-ReleaseSignature -Path $InstallerPath -Certificate $SigningCertificate
    }
}

if ($Sign) {
    $RootCertificate = Get-ChildItem Cert:\CurrentUser\My |
        Where-Object { $_.Subject -eq "CN=$PublisherName Pilot Root CA" } |
        Sort-Object NotAfter -Descending |
        Select-Object -First 1
    if (-not $RootCertificate) {
        throw "The pilot root certificate for '$PublisherName' was not found. Run scripts\new_pilot_signing_certificate.ps1 first."
    }
    Export-Certificate `
        -Cert $SigningCertificate `
        -FilePath "dist/Cole-Winstead-Pilot-Code-Signing.cer" `
        -Force | Out-Null
    Export-Certificate `
        -Cert $RootCertificate `
        -FilePath "dist/Cole-Winstead-Pilot-Root.cer" `
        -Force | Out-Null
}

$ReleaseFiles = Get-ChildItem -Path dist -File |
    Where-Object { $_.Name -ne "SHA256SUMS.txt" } |
    Sort-Object Name
$ChecksumLines = foreach ($ReleaseFile in $ReleaseFiles) {
    $Hash = Get-FileHash -LiteralPath $ReleaseFile.FullName -Algorithm SHA256
    "$($Hash.Hash.ToLower())  $($ReleaseFile.Name)"
}
$ChecksumLines | Set-Content -Encoding ascii dist/SHA256SUMS.txt

Write-Host "Built release files and dist/SHA256SUMS.txt"
