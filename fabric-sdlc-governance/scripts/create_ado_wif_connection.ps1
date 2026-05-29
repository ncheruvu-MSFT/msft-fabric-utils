<#
.SYNOPSIS
Create an ADO ARM service connection of type WorkloadIdentityFederation
directly via REST (when the portal "manual" option is missing).

PREREQ
  * $env:ADO_PAT set (or pass -AdoPat). Scope: Service Connections (Read, query,
    manage).
  * The Entra app (SPN) already exists in the target tenant.

USAGE
  pwsh ./create_ado_wif_connection.ps1 `
    -AdoOrg          ncheruvu0468 `
    -AdoProject      NagaDevops `
    -ConnectionName  azure-fabric-wif `
    -SubscriptionId  31613fe0-1e9b-4a97-b771-dc48fbaa0fbb `
    -SubscriptionName "Visual Studio Enterprise" `
    -TenantId        62c0cb46-1fcc-4c79-ba1b-d7d9fdfbaa68 `
    -SpnAppId        47a48c18-47f4-4f90-a5e7-f5add3cb2ee3

After it returns, run scripts/register_ado_fic.ps1 with the same connection
name to add the federated trust on the Entra app.
#>
param(
  [Parameter(Mandatory=$true)] [string] $AdoOrg,
  [Parameter(Mandatory=$true)] [string] $AdoProject,
  [Parameter(Mandatory=$true)] [string] $ConnectionName,
  [Parameter(Mandatory=$true)] [string] $SubscriptionId,
  [Parameter(Mandatory=$true)] [string] $SubscriptionName,
  [Parameter(Mandatory=$true)] [string] $TenantId,
  [Parameter(Mandatory=$true)] [string] $SpnAppId,
  [string] $AdoPat = $env:ADO_PAT
)

if (-not $AdoPat) { throw "Set ADO_PAT or pass -AdoPat." }
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$AdoPat"))
$hdr = @{ Authorization = "Basic $b64"; "Content-Type" = "application/json" }

# Resolve project id
$proj = Invoke-RestMethod -Headers $hdr `
  -Uri "https://dev.azure.com/$AdoOrg/_apis/projects/$AdoProject?api-version=7.1-preview.4"
$projId = $proj.id
Write-Host "Project id: $projId"

$body = @{
  name        = $ConnectionName
  type        = "azurerm"
  url         = "https://management.azure.com/"
  description = "WIF service connection for $ConnectionName"
  authorization = @{
    scheme     = "WorkloadIdentityFederation"
    parameters = @{
      tenantid    = $TenantId
      serviceprincipalid = $SpnAppId
    }
  }
  data = @{
    subscriptionId   = $SubscriptionId
    subscriptionName = $SubscriptionName
    environment      = "AzureCloud"
    scopeLevel       = "Subscription"
    creationMode     = "Manual"
  }
  isShared       = $false
  isReady        = $true
  serviceEndpointProjectReferences = @(
    @{
      projectReference = @{ id = $projId; name = $AdoProject }
      name = $ConnectionName
      description = "WIF service connection"
    }
  )
} | ConvertTo-Json -Depth 6

$uri = "https://dev.azure.com/$AdoOrg/_apis/serviceendpoint/endpoints?api-version=7.1-preview.4"
Write-Host "POST $uri"
$resp = Invoke-RestMethod -Method Post -Uri $uri -Headers $hdr -Body $body
Write-Host ""
Write-Host "Created service connection:"
Write-Host "  id     : $($resp.id)"
Write-Host "  name   : $($resp.name)"
Write-Host "  issuer : $($resp.authorization.parameters.workloadIdentityFederationIssuer)"
Write-Host "  subject: $($resp.authorization.parameters.workloadIdentityFederationSubject)"
Write-Host ""
Write-Host "Now run register_ado_fic.ps1 -ServiceConnection '$ConnectionName' to wire the FIC."
