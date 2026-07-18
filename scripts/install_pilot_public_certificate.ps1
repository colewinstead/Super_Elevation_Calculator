[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RootCertificatePath,
    [Parameter(Mandatory = $true)]
    [string]$SigningCertificatePath,
    [switch]$AcknowledgePilotTrust
)

$ErrorActionPreference = "Stop"

if (-not $AcknowledgePilotTrust) {
    throw "Review both certificate thumbprints with Cole Winstead, then rerun with -AcknowledgePilotTrust. Trusting the pilot root means this Windows user trusts software issued by its private key."
}

$RootCertificatePath = (Resolve-Path -LiteralPath $RootCertificatePath).Path
$SigningCertificatePath = (Resolve-Path -LiteralPath $SigningCertificatePath).Path
$RootCertificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($RootCertificatePath)
$SigningCertificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($SigningCertificatePath)

if ($RootCertificate.Subject -ne $SigningCertificate.Issuer) {
    throw "The signing certificate was not issued by the supplied pilot root certificate."
}

Write-Host "Root subject: $($RootCertificate.Subject)"
Write-Host "Root thumbprint: $($RootCertificate.Thumbprint)"
Write-Host "Signing subject: $($SigningCertificate.Subject)"
Write-Host "Signing thumbprint: $($SigningCertificate.Thumbprint)"
Write-Host "Signing expiration: $($SigningCertificate.NotAfter.ToString('yyyy-MM-dd'))"

Write-Host "Windows may ask you to confirm trust for the private pilot root."
Import-Certificate -FilePath $RootCertificatePath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
Import-Certificate -FilePath $SigningCertificatePath -CertStoreLocation Cert:\CurrentUser\TrustedPublisher | Out-Null

Write-Host "Trusted for the current Windows user. Verify the downloaded installer hash before running it."
