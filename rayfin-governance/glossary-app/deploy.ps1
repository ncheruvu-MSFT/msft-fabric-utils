<#
.SYNOPSIS
  Deploy this Rayfin app into an EXISTING Microsoft Fabric workspace.

.DESCRIPTION
  A Rayfin app is a Fabric item, so it is deployed into a workspace you already
  own rather than creating its own. This script:
    1. Resolves the target workspace (from -WorkspaceId or $env:FABRIC_WORKSPACE_ID).
    2. Verifies the Rayfin CLI is installed and you are signed in.
    3. Builds the Fluent UI frontend (dist/).
    4. Runs `rayfin up` targeting that workspace.

  Nothing about the workspace is committed to source — it comes from the
  environment / parameters at deploy time.

.PARAMETER WorkspaceId
  Existing Fabric workspace GUID. Defaults to $env:FABRIC_WORKSPACE_ID.

.PARAMETER CapacityId
  Optional capacity GUID backing the workspace. Defaults to $env:FABRIC_CAPACITY_ID.

.PARAMETER SkipBuild
  Skip `npm run build` (use the existing dist/).

.PARAMETER WhatIf
  Print the resolved deploy command without executing it.

.EXAMPLE
  ./deploy.ps1 -WorkspaceId 00000000-0000-0000-0000-000000000000

.EXAMPLE
  $env:FABRIC_WORKSPACE_ID = '...'; ./deploy.ps1
#>
[CmdletBinding()]
param(
    [string]$TenantId = $env:FABRIC_TENANT_ID,
    [string]$WorkspaceId = $env:FABRIC_WORKSPACE_ID,
    [string]$CapacityId = $env:FABRIC_CAPACITY_ID,
    [switch]$SkipBuild,
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# 1. Resolve target workspace ----------------------------------------------
if ([string]::IsNullOrWhiteSpace($WorkspaceId)) {
    throw "No workspace specified. Pass -WorkspaceId or set FABRIC_WORKSPACE_ID (see rayfin/.env.example)."
}
$guidPattern = '^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$'
if ($WorkspaceId -notmatch $guidPattern) {
    throw "WorkspaceId '$WorkspaceId' is not a valid GUID."
}
if ($TenantId -and $TenantId -notmatch $guidPattern) {
    throw "TenantId '$TenantId' is not a valid GUID."
}
if ($TenantId) { Write-Step "Target tenant (external): $TenantId" }
Write-Step "Target Fabric workspace: $WorkspaceId"
if ($CapacityId) { Write-Step "Capacity: $CapacityId" }

# 2. Verify Rayfin CLI ------------------------------------------------------
$rayfin = Get-Command rayfin -ErrorAction SilentlyContinue
if (-not $rayfin) {
    throw "Rayfin CLI not found on PATH. Install the Fabric Apps (Rayfin) preview CLI, then sign in with 'rayfin login'."
}
Write-Step "Rayfin CLI: $($rayfin.Source)"

# 2b. Sign in to the target tenant -----------------------------------------
# For an external tenant you must authenticate against THAT tenant before
# deploying, otherwise rayfin uses your home tenant context.
if ($TenantId) {
    Write-Step "Signing in to tenant $TenantId (rayfin login --tenant)"
    if (-not $WhatIf) {
        & rayfin login --tenant $TenantId
        if ($LASTEXITCODE -ne 0) { throw "rayfin login to tenant $TenantId failed (exit $LASTEXITCODE)." }
    }
}

# 3. Build frontend ---------------------------------------------------------
if (-not $SkipBuild) {
    Write-Step "Building frontend (npm run build)"
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed (exit $LASTEXITCODE)." }
}
else {
    Write-Step "Skipping build (-SkipBuild)"
}

# 4. Deploy -----------------------------------------------------------------
$deployArgs = @('up', '--config', 'rayfin/rayfin.yml', '--workspace', $WorkspaceId)
if ($TenantId) { $deployArgs += @('--tenant', $TenantId) }
if ($CapacityId) { $deployArgs += @('--capacity', $CapacityId) }

Write-Step ("rayfin " + ($deployArgs -join ' '))
if ($WhatIf) {
    Write-Host "[WhatIf] Not executing. Re-run without -WhatIf to deploy." -ForegroundColor Yellow
    return
}

& rayfin @deployArgs
if ($LASTEXITCODE -ne 0) { throw "rayfin up failed (exit $LASTEXITCODE)." }
Write-Step "Deployment complete. The App item now lives in workspace $WorkspaceId."
