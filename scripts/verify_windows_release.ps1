[CmdletBinding()]
param(
    [string]$DistPath,
    [string]$PublisherName = "Cole Winstead"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $DistPath) {
    $DistPath = Join-Path $Root "dist"
}
$DistPath = (Resolve-Path -LiteralPath $DistPath).Path

$ChecksumPath = Join-Path $DistPath "SHA256SUMS.txt"
$RootCertificatePath = Join-Path $DistPath "Cole-Winstead-Pilot-Root.cer"
$SigningCertificatePath = Join-Path $DistPath "Cole-Winstead-Pilot-Code-Signing.cer"
$RootCertificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($RootCertificatePath)
$SigningCertificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($SigningCertificatePath)

if ($SigningCertificate.Subject -ne "CN=$PublisherName") {
    throw "Unexpected signing subject: $($SigningCertificate.Subject)"
}
if ($SigningCertificate.Issuer -ne $RootCertificate.Subject) {
    throw "The signing certificate was not issued by the supplied pilot root."
}

$ExpectedHashes = @{}
foreach ($Line in Get-Content -LiteralPath $ChecksumPath) {
    if ($Line -notmatch '^([0-9a-f]{64})  (.+)$') {
        throw "Invalid checksum line: $Line"
    }
    $ExpectedHashes[$Matches[2]] = $Matches[1]
}

$ReleaseFiles = Get-ChildItem -LiteralPath $DistPath -File |
    Where-Object { $_.Name -ne "SHA256SUMS.txt" }
foreach ($File in $ReleaseFiles) {
    if (-not $ExpectedHashes.ContainsKey($File.Name)) {
        throw "No checksum was published for $($File.Name)."
    }
    $ActualHash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHashes[$File.Name]) {
        throw "SHA-256 checksum mismatch for $($File.Name)."
    }
}
if ($ExpectedHashes.Count -ne $ReleaseFiles.Count) {
    throw "SHA256SUMS.txt references a file that is not present."
}

$SignedFiles = $ReleaseFiles | Where-Object { $_.Extension -eq ".exe" }
if (-not $SignedFiles) {
    throw "No signed Windows executable files were found."
}
foreach ($File in $SignedFiles) {
    $Signature = Get-AuthenticodeSignature -FilePath $File.FullName
    if (-not $Signature.SignerCertificate -or
        $Signature.SignerCertificate.Thumbprint -ne $SigningCertificate.Thumbprint -or
        $Signature.SignatureType -ne "Authenticode") {
        throw "Authenticode signature verification failed for $($File.Name)."
    }

    $Chain = [System.Security.Cryptography.X509Certificates.X509Chain]::new()
    $Chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck
    $Chain.ChainPolicy.VerificationFlags = [System.Security.Cryptography.X509Certificates.X509VerificationFlags]::AllowUnknownCertificateAuthority
    $Chain.ChainPolicy.ExtraStore.Add($RootCertificate) | Out-Null
    if (-not $Chain.Build($Signature.SignerCertificate)) {
        throw "Certificate-chain verification failed for $($File.Name)."
    }
    $ChainRoot = $Chain.ChainElements[$Chain.ChainElements.Count - 1].Certificate
    if ($ChainRoot.Thumbprint -ne $RootCertificate.Thumbprint) {
        throw "The signature on $($File.Name) does not chain to the supplied pilot root."
    }
}

Write-Host "Verified $($ReleaseFiles.Count) SHA-256 checksums and $($SignedFiles.Count) Authenticode signatures."
Write-Host "Publisher: $($SigningCertificate.Subject)"
Write-Host "Pilot root thumbprint: $($RootCertificate.Thumbprint)"
Write-Host "Signing thumbprint: $($SigningCertificate.Thumbprint)"
