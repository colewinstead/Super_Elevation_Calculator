[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ReleaseCommit,

    [Parameter(Mandatory = $true)]
    [string]$SiteRemoteUrl,

    [string]$SiteBranch = 'main',

    [Parameter(Mandatory = $true)]
    [string]$ArchivePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-CheckedGit {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [switch]$Authenticated
    )

    $gitArguments = @('-C', $script:ResolvedRepositoryRoot)
    if ($Authenticated) {
        $authorizationHeader = [Environment]::GetEnvironmentVariable('SHIP_MAIN_SITE_AUTH_HEADER')
        if ([string]::IsNullOrWhiteSpace($authorizationHeader)) {
            throw 'SHIP_MAIN_SITE_AUTH_HEADER is required for the Sites source operation.'
        }
        $gitArguments += @('-c', "http.extraHeader=$authorizationHeader")
    }
    $gitArguments += $Arguments

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & git @gitArguments 2>&1
        $gitExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($gitExitCode -ne 0) {
        throw "Git command failed: $($output -join [Environment]::NewLine)"
    }
    return @($output)
}

$script:ResolvedRepositoryRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$authenticatedRemote = $SiteRemoteUrl -match '^https?://'
if ($authenticatedRemote) {
    $authorizationHeader = [Environment]::GetEnvironmentVariable('SHIP_MAIN_SITE_AUTH_HEADER')
    if ([string]::IsNullOrWhiteSpace($authorizationHeader)) {
        throw 'SHIP_MAIN_SITE_AUTH_HEADER is required for an HTTPS Sites source remote.'
    }
}
$resolvedWebRoot = Join-Path $script:ResolvedRepositoryRoot 'web'
$resolvedDistRoot = Join-Path $resolvedWebRoot 'dist'
$serverEntry = Join-Path $resolvedDistRoot 'server\index.js'
$hostingMetadata = Join-Path $resolvedDistRoot '.openai\hosting.json'

if (-not (Test-Path -LiteralPath $serverEntry -PathType Leaf)) {
    throw "Missing production server entry: $serverEntry"
}
if (-not (Test-Path -LiteralPath $hostingMetadata -PathType Leaf)) {
    throw "Missing Sites hosting metadata: $hostingMetadata"
}

$resolvedReleaseCommit = ([string](Invoke-CheckedGit -Arguments @('rev-parse', "$ReleaseCommit^{commit}"))).Trim()
$headCommit = ([string](Invoke-CheckedGit -Arguments @('rev-parse', 'HEAD'))).Trim()
if ($headCommit -ne $resolvedReleaseCommit) {
    throw "Worktree HEAD $headCommit does not match release commit $resolvedReleaseCommit."
}

$trackedStatus = @(Invoke-CheckedGit -Arguments @('status', '--porcelain', '--untracked-files=no'))
if ($trackedStatus.Count -gt 0) {
    throw 'The release worktree contains tracked changes. Use a clean temporary worktree.'
}

$resolvedArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)
if (Test-Path -LiteralPath $resolvedArchivePath) {
    throw "Archive already exists: $resolvedArchivePath"
}
$archiveParent = Split-Path -Parent $resolvedArchivePath
if (-not (Test-Path -LiteralPath $archiveParent -PathType Container)) {
    [void](New-Item -ItemType Directory -Path $archiveParent)
}

& tar -C $resolvedWebRoot -czf $resolvedArchivePath dist
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to create the Sites deployment archive.'
}
$archiveEntries = @(& tar -tzf $resolvedArchivePath)
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to inspect the Sites deployment archive.'
}
foreach ($requiredEntry in @('dist/server/index.js', 'dist/.openai/hosting.json')) {
    if ($archiveEntries -notcontains $requiredEntry) {
        throw "Deployment archive is missing $requiredEntry."
    }
}

$siteTrackingRef = "refs/remotes/ship-main-site/$SiteBranch"
$fetchArguments = @('fetch', $SiteRemoteUrl, "+refs/heads/$SiteBranch`:$siteTrackingRef")
[void](Invoke-CheckedGit -Arguments $fetchArguments -Authenticated:$authenticatedRemote)

$releaseTree = ([string](Invoke-CheckedGit -Arguments @('rev-parse', "$resolvedReleaseCommit^{tree}"))).Trim()
$siteParent = ([string](Invoke-CheckedGit -Arguments @('rev-parse', $siteTrackingRef))).Trim()
$sourceCommit = ([string](Invoke-CheckedGit -Arguments @(
            '-c', 'user.name=Superelevation Calculator Release',
            '-c', 'user.email=release@vericivil.com',
            'commit-tree', $releaseTree,
            '-p', $siteParent,
            '-m', "Deploy released main $resolvedReleaseCommit"
        ))).Trim()

$pushArguments = @('push', $SiteRemoteUrl, "$sourceCommit`:refs/heads/$SiteBranch")
[void](Invoke-CheckedGit -Arguments $pushArguments -Authenticated:$authenticatedRemote)

$remoteHeadOutput = @(Invoke-CheckedGit -Arguments @('ls-remote', $SiteRemoteUrl, "refs/heads/$SiteBranch") -Authenticated:$authenticatedRemote)
if ($remoteHeadOutput.Count -ne 1) {
    throw 'Could not verify the Sites source branch after pushing.'
}
$remoteHead = ($remoteHeadOutput[0] -split '\s+')[0]
if ($remoteHead -ne $sourceCommit) {
    throw "Sites source verification failed. Expected $sourceCommit but found $remoteHead."
}

$archiveHash = (Get-FileHash -LiteralPath $resolvedArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
[pscustomobject]@{
    release_commit = $resolvedReleaseCommit
    release_tree   = $releaseTree
    site_parent    = $siteParent
    source_commit  = $sourceCommit
    archive        = $resolvedArchivePath
    archive_sha256 = $archiveHash
} | ConvertTo-Json
