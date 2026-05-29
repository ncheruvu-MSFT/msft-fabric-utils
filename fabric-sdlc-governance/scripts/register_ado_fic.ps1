<#
.SYNOPSIS
Register an Azure DevOps Workload Identity Federation (WIF / FIC) trust on the
Entra app used by ADO service connections. Replaces SPN secret-based auth.

PREREQ
  * The Entra app (SPN) already exists.
  * You have an ADO service connection of type "Workload identity federation
    (manual)" that provides Issuer + Subject identifier values to be trusted.
  * Run as an account with Application.ReadWrite.OwnedBy or Application Admin.

USAGE
  pwsh ./register_ado_fic.ps1 `
    -SpnAppId           "00000000-0000-0000-0000-000000000000" `
    -AdoOrg             "ncheruvu0468" `
    -AdoProject         "NagaDevops" `
    -ServiceConnection  "azure-fabric-sso"

This adds a FederatedIdentityCredential matching:
  Issuer:   https://vstoken.dev.azure.com/<org-guid>
  Subject:  sc://<org>/<project>/<service-connection>
  Audience: api://AzureADTokenExchange
#>
param(
  [Parameter(Mandatory=$true)] [string] $SpnAppId,
  [Parameter(Mandatory=$true)] [string] $AdoOrg,
  [Parameter(Mandatory=$true)] [string] $AdoProject,
  [Parameter(Mandatory=$true)] [string] $ServiceConnection,
  [string] $CredentialName = "ado-wif",
  [string] $AdoOrgId       = $env:ADO_ORG_ID,
  [string] $AdoPat         = $env:ADO_PAT
)

# 1. Resolve issuer + subject from the actual ADO service connection (most
#    reliable — ADO chooses the format, e.g. /eid1/c/pub/t/.../sc/<org>/<sc>).
Write-Host "Fetching service connection '$ServiceConnection' from ADO ..."
if (-not $AdoPat) { throw "ADO_PAT (or -AdoPat) is required to query the service connection." }
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$AdoPat"))
$adoHdr = @{ Authorization = "Basic $b64" }

$endpoints = Invoke-RestMethod -Headers $adoHdr `
  -Uri "https://dev.azure.com/$AdoOrg/$AdoProject/_apis/serviceendpoint/endpoints?endpointNames=$ServiceConnection&api-version=7.1-preview.4"
$ep = $endpoints.value | Select-Object -First 1
if (-not $ep) { throw "Service connection '$ServiceConnection' not found in $AdoOrg/$AdoProject. Create it first (see scripts/create_ado_wif_connection.ps1)." }

$issuer  = $ep.authorization.parameters.workloadIdentityFederationIssuer
$subject = $ep.authorization.parameters.workloadIdentityFederationSubject
if (-not $issuer -or -not $subject) {
  throw "Connection '$ServiceConnection' is not Workload Identity Federation (no issuer/subject). Authorization scheme: $($ep.authorization.scheme)"
}
Write-Host "  Issuer:  $issuer"
Write-Host "  Subject: $subject"

# 2. Resolve app object id
$appObjId = (az ad app show --id $SpnAppId --query id -o tsv)
if (-not $appObjId) { throw "Entra app '$SpnAppId' not found." }
Write-Host "  App object id: $appObjId"

# 3. Add (or update) Federated Identity Credential
$existing = az ad app federated-credential list --id $SpnAppId --query "[?name=='$CredentialName'] | [0].id" -o tsv
$body = @{
  name      = $CredentialName
  issuer    = $issuer
  subject   = $subject
  audiences = @("api://AzureADTokenExchange")
  description = "ADO WIF for $AdoOrg/$AdoProject/$ServiceConnection"
} | ConvertTo-Json -Compress

$tmp = New-TemporaryFile
$body | Out-File -FilePath $tmp -Encoding utf8

if ($existing) {
  Write-Host "`nUpdating existing FIC '$CredentialName' ..."
  az ad app federated-credential update --id $SpnAppId --federated-credential-id $existing --parameters "@$tmp" | Out-Null
} else {
  Write-Host "`nCreating FIC '$CredentialName' ..."
  az ad app federated-credential create --id $SpnAppId --parameters "@$tmp" | Out-Null
}
Remove-Item $tmp -ErrorAction SilentlyContinue

Write-Host "`nDone. FIC trust registered."
Write-Host "Next steps:"
Write-Host "  1. In ADO project '$AdoProject', edit the service connection '$ServiceConnection'."
Write-Host "  2. Confirm Issuer = $issuer  and  Subject = $subject."
Write-Host "  3. Remove the variable group entry SPN_CLIENT_SECRET (no longer needed)."
Write-Host "  4. Re-run pipeline-de.yml — fabric-cicd will auth via federated token."
