<#
.SYNOPSIS
  Configure a Storage account so that a Microsoft Fabric workspace can reach it
  via Trusted Workspace Access while keeping public network access disabled.

.DESCRIPTION
  This is the identity-perimeter equivalent of an MPE for the OneLake-shortcut /
  lakehouse-load case. Requires:
    - Storage account with publicNetworkAccess = Disabled
    - Storage account "Allow Azure services on the trusted services list" enabled
    - The Fabric workspace identity granted Storage Blob Data Reader/Contributor
      on the account or container

  Reference:
    https://learn.microsoft.com/fabric/security/security-trusted-workspace-access

.PARAMETER StorageAccountResourceId
  ARM resource ID of the target Storage account.

.PARAMETER WorkspaceIdentityObjectId
  Object (principal) ID of the Fabric workspace identity service principal.
  Visible in the Fabric workspace settings -> Workspace identity blade.

.PARAMETER RoleDefinitionName
  Default Storage Blob Data Reader. Pass Contributor if writes are required.

.EXAMPLE
  Connect-AzAccount -Tenant $tenantId
  ./Enable-TrustedWorkspaceAccess.ps1 `
    -StorageAccountResourceId '/subscriptions/.../resourceGroups/data/providers/Microsoft.Storage/storageAccounts/datalake01' `
    -WorkspaceIdentityObjectId 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $StorageAccountResourceId,
  [Parameter(Mandatory)] [string] $WorkspaceIdentityObjectId,
  [ValidateSet('Storage Blob Data Reader', 'Storage Blob Data Contributor', 'Storage Blob Data Owner')]
  [string] $RoleDefinitionName = 'Storage Blob Data Reader'
)

$ErrorActionPreference = 'Stop'

# Parse the resource ID
if ($StorageAccountResourceId -notmatch '^/subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft\.Storage/storageAccounts/([^/]+)$') {
  throw "StorageAccountResourceId is not a valid Storage account resource ID."
}
$subId   = $matches[1]
$rgName  = $matches[2]
$saName  = $matches[3]

Set-AzContext -SubscriptionId $subId | Out-Null

Write-Host "Hardening storage account $saName ..." -ForegroundColor Cyan

# 1. Disable public network access, allow trusted Azure services bypass.
Set-AzStorageAccount `
  -ResourceGroupName     $rgName `
  -Name                  $saName `
  -PublicNetworkAccess   Disabled `
  -NetworkRuleSet @{
      bypass        = 'AzureServices,Logging,Metrics'
      defaultAction = 'Deny'
  } | Out-Null

Write-Host "  publicNetworkAccess=Disabled, bypass=AzureServices" -ForegroundColor Green

# 2. Grant the workspace identity data-plane access (RBAC).
$existing = Get-AzRoleAssignment `
  -ObjectId         $WorkspaceIdentityObjectId `
  -Scope            $StorageAccountResourceId `
  -RoleDefinitionName $RoleDefinitionName `
  -ErrorAction      SilentlyContinue

if ($null -eq $existing) {
  New-AzRoleAssignment `
    -ObjectId           $WorkspaceIdentityObjectId `
    -RoleDefinitionName $RoleDefinitionName `
    -Scope              $StorageAccountResourceId | Out-Null
  Write-Host "  Granted '$RoleDefinitionName' to workspace identity $WorkspaceIdentityObjectId" -ForegroundColor Green
} else {
  Write-Host "  Workspace identity already has '$RoleDefinitionName'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "NEXT: in the Fabric portal -> workspace -> Settings -> Trusted workspace access," -ForegroundColor Cyan
Write-Host "      register this storage account so OneLake shortcuts can use it." -ForegroundColor Cyan
