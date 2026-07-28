<#
.SYNOPSIS
  Lists Managed Private Endpoints in a Fabric workspace.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $WorkspaceId
)
$ErrorActionPreference = 'Stop'
$token = (Get-AzAccessToken -ResourceUrl 'https://api.fabric.microsoft.com').Token
$headers = @{ Authorization = "Bearer $token" }
$uri = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/managedPrivateEndpoints"
(Invoke-RestMethod -Uri $uri -Headers $headers -Method Get).value |
  Select-Object name, id, provisioningState, targetSubresourceType,
                @{n='connectionStatus'; e={ $_.connectionState.status }},
                targetPrivateLinkResourceId |
  Format-Table -AutoSize
