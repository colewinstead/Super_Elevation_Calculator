[CmdletBinding()]
param(
    [string]$PublisherName = "Cole Winstead",
    [int]$ValidYears = 3,
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $Root "dist"
}
if ($ValidYears -lt 1) {
    throw "ValidYears must be at least 1."
}

$RootSubject = "CN=$PublisherName Pilot Root CA"
$SigningSubject = "CN=$PublisherName"
$MinimumExpiration = (Get-Date).AddDays(30)

$RootCertificate = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object {
        $_.Subject -eq $RootSubject -and
        $_.HasPrivateKey -and
        $_.NotAfter -gt $MinimumExpiration
    } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $RootCertificate) {
    $RootCertificate = New-SelfSignedCertificate `
        -Subject $RootSubject `
        -FriendlyName "Superelevation Calculator Pilot Root CA" `
        -Type Custom `
        -CertStoreLocation Cert:\CurrentUser\My `
        -KeyAlgorithm RSA `
        -KeyLength 3072 `
        -HashAlgorithm SHA256 `
        -KeyExportPolicy Exportable `
        -KeyUsage CertSign, CRLSign, DigitalSignature `
        -TextExtension @("2.5.29.19={critical}{text}ca=1&pathlength=1") `
        -NotAfter (Get-Date).AddYears($ValidYears + 2)
    Write-Host "Created pilot root certificate $($RootCertificate.Thumbprint)."
} else {
    Write-Host "Reusing pilot root certificate $($RootCertificate.Thumbprint)."
}

$SigningCertificate = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object {
        $_.Subject -eq $SigningSubject -and
        $_.Issuer -eq $RootSubject -and
        $_.HasPrivateKey -and
        $_.NotAfter -gt $MinimumExpiration
    } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $SigningCertificate) {
    $SigningCertificate = New-SelfSignedCertificate `
        -Subject $SigningSubject `
        -FriendlyName "Superelevation Calculator Pilot Code Signing" `
        -Type CodeSigningCert `
        -Signer $RootCertificate `
        -CertStoreLocation Cert:\CurrentUser\My `
        -KeyAlgorithm RSA `
        -KeyLength 3072 `
        -HashAlgorithm SHA256 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears($ValidYears)
    Write-Host "Created pilot code-signing certificate $($SigningCertificate.Thumbprint)."
} else {
    Write-Host "Reusing pilot code-signing certificate $($SigningCertificate.Thumbprint)."
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$RootPublicPath = Join-Path $OutputDirectory "Cole-Winstead-Pilot-Root.cer"
$SigningPublicPath = Join-Path $OutputDirectory "Cole-Winstead-Pilot-Code-Signing.cer"
Export-Certificate -Cert $RootCertificate -FilePath $RootPublicPath -Force | Out-Null
Export-Certificate -Cert $SigningCertificate -FilePath $SigningPublicPath -Force | Out-Null

Write-Host "Public root certificate: $RootPublicPath"
Write-Host "Root thumbprint: $($RootCertificate.Thumbprint)"
Write-Host "Public signing certificate: $SigningPublicPath"
Write-Host "Signing subject: $($SigningCertificate.Subject)"
Write-Host "Signing expiration: $($SigningCertificate.NotAfter.ToString('yyyy-MM-dd'))"
Write-Host "Signing thumbprint: $($SigningCertificate.Thumbprint)"
Write-Warning "Both private keys remain in the current user's Windows certificate store. Never publish or send a PFX/private-key export."
