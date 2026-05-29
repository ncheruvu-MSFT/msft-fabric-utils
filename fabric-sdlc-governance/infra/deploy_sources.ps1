# Multi-source provisioning + Fabric mirroring + Purview governance
# Run order:
#   1. ./deploy_sources.ps1         # creates Databricks/SQL/Postgres/Cosmos (CAF + AVM)
#   2. python ../scripts/sources/load_all.py   # loads sample retail data
#   3. python ../scripts/fabric_create_mirrored.py    # creates mirrored DBs
#   4. python ../scripts/fabric_create_items.py       # lakehouse + warehouse + agent
#   5. python ../scripts/purview_setup_domains.py     # governance domains
#   6. python ../scripts/purview_register_sources.py  # register + scan
#   7. python ../scripts/purview_setup_workflows.py   # self-service access
#   8. python ../scripts/lineage_demo.py              # end-to-end lineage
[CmdletBinding()]
param(
  [string]$Subscription  = "00000000-0000-0000-0000-000000000000",
  [string]$ResourceGroup = "ng-fabric-sources-cc",
  [string]$Location      = "canadacentral",
  [string]$Workload      = "fbrcdemo",
  [ValidateSet('dev','tst','prd')][string]$Env = "dev",
  [ValidateSet('cac','eus','eus2','wus2','wus3')][string]$RegionCode = "cac",
  [string]$Instance      = "001",
  [Parameter(Mandatory=$true)][SecureString]$PgPassword
)

az account set --subscription $Subscription | Out-Null
az group create -n $ResourceGroup -l $Location | Out-Null

$pgPwd = [System.Net.NetworkCredential]::new("", $PgPassword).Password

Write-Host "Deploying sources via AVM (CAF naming)..."
$out = az deployment group create `
  -g $ResourceGroup `
  -n "sources-avm-$Env" `
  -f "$PSScriptRoot/sources.bicep" `
  -p workload=$Workload env=$Env regionCode=$RegionCode instance=$Instance pgPassword=$pgPwd `
  --query properties.outputs -o json | ConvertFrom-Json

$envFile = "$PSScriptRoot/../.sources.env"
@"
SOURCE_DBX_NAME=$($out.databricksWorkspaceName.value)
SOURCE_DBX_ID=$($out.databricksResourceId.value)
SOURCE_SQL_FQDN=$($out.sqlServerFqdn.value)
SOURCE_SQL_NAME=$($out.sqlServerName.value)
SOURCE_SQL_DB=$($out.sqlDatabase.value)
SOURCE_PG_FQDN=$($out.postgresFqdn.value)
SOURCE_PG_NAME=$($out.postgresName.value)
SOURCE_PG_DB=$($out.postgresDatabase.value)
SOURCE_COSMOS_EP=$($out.cosmosEndpoint.value)
SOURCE_COSMOS_ACCT=$($out.cosmosName.value)
SOURCE_COSMOS_DB=$($out.cosmosDatabase.value)
SOURCE_ADMIN_LOGIN=ncheruvu@MngEnvMCAP219373.onmicrosoft.com
SOURCE_PG_LOGIN=pgadmin
SOURCE_PG_PASSWORD=$pgPwd
"@ | Out-File -FilePath $envFile -Encoding utf8

Write-Host "`nSources provisioned. Endpoints written to $envFile"
$out | ConvertTo-Json -Depth 5
