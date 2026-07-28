<#
.SYNOPSIS
  Creates a Managed Private Endpoint (MPE) in a Microsoft Fabric workspace,
  pointing at a private Azure data source (Storage, SQL DB, Cosmos, Key Vault, ...).

.DESCRIPTION
  MPEs are *Fabric-managed* — they live inside the workspace, are visible only
  to Fabric workloads (Spark notebooks, lakehouses, eventstreams, Spark job
  defs), and require approval on the *target* resource. There is no Terraform
  AzureRM resource for them today; the public surface is a Fabric REST API.

  Reference: https://learn.microsoft.com/rest/api/fabric/core/managed-private-endpoints/create-workspace-managed-private-endpoint
  Overview:  https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-overview

.PARAMETER WorkspaceId
  GUID of the Fabric workspace (must be on a paid F SKU or Trial; assigned to
  the capacity created by this Terraform sample).

.PARAMETER Name
  Name of the MPE (max 64 chars, unique within the workspace).

.PARAMETER TargetResourceId
  ARM resource ID of the data source (e.g. /subscriptions/.../Microsoft.Sql/servers/mysql).

.PARAMETER TargetSubresource
  Sub-resource name. Common values:
    sqlServer    Azure SQL Database / Synapse SQL
    blob         Storage account (blob)
    dfs          Storage account (ADLS Gen2)
    Sql          Cosmos DB SQL API
    vault        Azure Key Vault
    namespace    Event Hubs / Service Bus

.PARAMETER RequestMessage
  Message shown to the target resource owner during approval (max 140 chars).

.PARAMETER WaitForActivated
  When set, poll the MPE until provisioningState = Succeeded AND
  connectionState = Approved. Without approval on the target side, the MPE
  stays in Pending — you must approve it in the Azure portal on the target
  resource (Networking -> Private endpoint connections).

.EXAMPLE
  Connect-AzAccount -Tenant $tenantId
  ./Create-FabricMpe.ps1 `
    -WorkspaceId 47482db6-4583-4672-86dd-999d0f8f4d7a `
    -Name "mpe-sql-shared" `
    -TargetResourceId "/subscriptions/.../resourceGroups/data/providers/Microsoft.Sql/servers/sqlsrv01" `
    -TargetSubresource sqlServer `
    -RequestMessage "Fabric workspace prod-analytics needs read access to sqlsrv01"
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $WorkspaceId,
  [Parameter(Mandatory)] [string] $Name,
  [Parameter(Mandatory)] [string] $TargetResourceId,
  [ValidateSet('sqlServer', 'blob', 'dfs', 'file', 'queue', 'table', 'Sql', 'vault', 'namespace')]
  [string] $TargetSubresource = 'sqlServer',
  [string] $RequestMessage    = 'Fabric MPE created via automation',
  [switch] $WaitForActivated
)

$ErrorActionPreference = 'Stop'

# ---- Acquire a Fabric API token from the cached az/Az session ----
try {
  $token = (Get-AzAccessToken -ResourceUrl 'https://api.fabric.microsoft.com').Token
} catch {
  throw "Could not acquire Fabric API token. Run 'Connect-AzAccount -Tenant <tenantId>' first. $($_.Exception.Message)"
}

$headers = @{
  Authorization = "Bearer $token"
  'Content-Type' = 'application/json'
}

$uri  = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/managedPrivateEndpoints"
$body = @{
  name                        = $Name
  targetPrivateLinkResourceId = $TargetResourceId
  targetSubresourceType       = $TargetSubresource
  requestMessage              = $RequestMessage
} | ConvertTo-Json -Depth 5

Write-Host "POST $uri" -ForegroundColor Cyan
Write-Host $body

$resp = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
$resp | ConvertTo-Json -Depth 8 | Write-Host

$mpeId = $resp.id
Write-Host "Created MPE id=$mpeId, provisioningState=$($resp.provisioningState)" -ForegroundColor Green
Write-Host ''
Write-Host "ACTION REQUIRED: approve the request on the target resource in the Azure portal:" -ForegroundColor Yellow
Write-Host "  $TargetResourceId" -ForegroundColor Yellow
Write-Host "  Networking -> Private endpoint connections -> Approve" -ForegroundColor Yellow

if (-not $WaitForActivated) { return }

# ---- Optional: poll until activated ----
$getUri = "$uri/$mpeId"
$deadline = (Get-Date).AddMinutes(20)

while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 30
  $cur = Invoke-RestMethod -Uri $getUri -Headers $headers -Method Get
  $ps  = $cur.provisioningState
  $cs  = $cur.connectionState.status
  Write-Host ("  provisioning={0} connection={1}" -f $ps, $cs)
  if ($ps -eq 'Succeeded' -and $cs -eq 'Approved') {
    Write-Host 'MPE active.' -ForegroundColor Green
    return
  }
  if ($ps -eq 'Failed') {
    throw "MPE provisioning failed."
  }
}

Write-Warning "Timed out waiting for activation. Approve on the target resource and re-check via GET $getUri."
