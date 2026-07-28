<#
.SYNOPSIS
  Deploy the Azure Databricks workspace for the lineage demo and append its
  host URL to .env.cloud.

.EXAMPLE
  ./deploy_databricks.ps1 -ResourceGroup rg-fbrlin-dev-cac -Location canadacentral
#>
param(
  [Parameter(Mandatory)] [string] $ResourceGroup,
  [string] $Location = 'canadacentral'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$bicep = Join-Path $PSScriptRoot 'databricks.bicep'
$param = Join-Path $PSScriptRoot 'databricks.bicepparam'

Write-Host "Deploying Databricks workspace..." -ForegroundColor Cyan
$deployment = az deployment group create `
  --resource-group $ResourceGroup `
  --template-file  $bicep `
  --parameters     $param `
  --output json | ConvertFrom-Json

if (-not $deployment) { throw "Databricks deployment failed" }

$host_url = $deployment.properties.outputs.workspaceHost.value
$envFile  = Join-Path $PSScriptRoot '..' '..' '..' '.env.cloud'
$envFile  = (Resolve-Path -LiteralPath $envFile -ErrorAction SilentlyContinue) ?? $envFile

# Idempotent upsert: drop any existing DATABRICKS_HOST line then append fresh.
$lines = @()
if (Test-Path $envFile) {
  $lines = (Get-Content -LiteralPath $envFile) | Where-Object {
    $_ -notmatch '^\s*DATABRICKS_HOST\s*='
  }
}
$lines += "DATABRICKS_HOST=$host_url"
$lines | Set-Content -Path $envFile -Encoding utf8

Write-Host "Databricks host: $host_url" -ForegroundColor Green
Write-Host "Next: python samples/cloud/seed/seed_databricks.py" -ForegroundColor Yellow
