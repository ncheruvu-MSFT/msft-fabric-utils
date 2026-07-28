# Deploy Cost Guard: infra + function code.
# Usage:
#   .\deploy.ps1                # deploy infra, then publish code (uses Azure Functions Core Tools if available)
#   .\deploy.ps1 -InfraOnly     # only the Bicep deploy
#   .\deploy.ps1 -CodeOnly      # only push the code to an already-deployed function app
#   .\deploy.ps1 -Run           # trigger the function once after deploy (smoke test)
[CmdletBinding()]
param(
  [string]$Location = 'eastus2',
  [string]$ParamFile = "$PSScriptRoot\infra\main.bicepparam",
  [switch]$InfraOnly,
  [switch]$CodeOnly,
  [switch]$Run
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$infraDir = Join-Path $root 'infra'
$appDir = Join-Path $root 'app'

Write-Host "=== Cost Guard deploy ==="
$account = az account show --query "{sub:id, tenant:tenantId, user:user.name}" -o json | ConvertFrom-Json
Write-Host "Subscription: $($account.sub)"
Write-Host "Tenant:       $($account.tenant)"
Write-Host "User:         $($account.user)"
Write-Host ""

$deployName = "cost-guard-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

if (-not $CodeOnly) {
  Write-Host "=== Deploying Bicep (sub scope) ==="
  $out = az deployment sub create `
    --name $deployName `
    --location $Location `
    --template-file (Join-Path $infraDir 'main.bicep') `
    --parameters $ParamFile `
    --query 'properties.outputs' -o json
  if ($LASTEXITCODE -ne 0) { throw "Bicep deploy failed" }
  $outputs = $out | ConvertFrom-Json
  $functionAppName = $outputs.functionAppName.value
  $rgName = $outputs.resourceGroupName.value
  Write-Host "Function App:   $functionAppName"
  Write-Host "Resource group: $rgName"
} else {
  # discover the most recent successful deploy's outputs
  Write-Host "=== Discovering existing function app ==="
  $deployments = az deployment sub list --query "[?contains(name, 'cost-guard')] | [0]" -o json | ConvertFrom-Json
  if (-not $deployments) { throw "No cost-guard deployment found in this subscription. Run without -CodeOnly first." }
  $outputs = az deployment sub show --name $deployments.name --query 'properties.outputs' -o json | ConvertFrom-Json
  $functionAppName = $outputs.functionAppName.value
  $rgName = $outputs.resourceGroupName.value
}

if ($InfraOnly) {
  Write-Host "InfraOnly: skipping code push."
  Write-Host "Next: .\deploy.ps1 -CodeOnly"
  exit 0
}

Write-Host ""
Write-Host "=== Publishing function code ==="

# Prefer Azure Functions Core Tools (handles remote build + indexing properly)
$func = Get-Command func -ErrorAction SilentlyContinue
if ($func) {
  Push-Location $appDir
  try {
    func azure functionapp publish $functionAppName --python --build remote
    if ($LASTEXITCODE -ne 0) { throw "func publish failed" }
  } finally {
    Pop-Location
  }
} else {
  Write-Warning "Azure Functions Core Tools ('func') not found. Falling back to az zip deploy."
  Write-Warning "Install: https://learn.microsoft.com/azure/azure-functions/functions-run-local"
  $zip = Join-Path $env:TEMP "cost-guard-$(Get-Date -Format yyyyMMddHHmmss).zip"
  if (Test-Path $zip) { Remove-Item $zip -Force }
  Compress-Archive -Path "$appDir\*" -DestinationPath $zip -Force
  az functionapp deployment source config-zip -g $rgName -n $functionAppName --src $zip --build-remote true
  if ($LASTEXITCODE -ne 0) { throw "zip deploy failed" }
  Remove-Item $zip -Force
}

if ($Run) {
  Write-Host ""
  Write-Host "=== Triggering one manual run (admin endpoint) ==="
  $masterKey = az functionapp keys list -g $rgName -n $functionAppName --query masterKey -o tsv
  $invokeUrl = "https://$functionAppName.azurewebsites.net/admin/functions/nightly_cost_guard"
  Invoke-RestMethod -Method Post -Uri $invokeUrl `
    -Headers @{ 'x-functions-key' = $masterKey; 'Content-Type' = 'application/json' } `
    -Body '{"input":""}'
  Write-Host "Triggered. Check logs:"
  Write-Host "  az webapp log tail -g $rgName -n $functionAppName"
}

Write-Host ""
Write-Host "=== Done ==="
Write-Host "Stream logs:   az webapp log tail -g $rgName -n $functionAppName"
Write-Host "App settings:  az functionapp config appsettings list -g $rgName -n $functionAppName -o table"
Write-Host "Switch DRY_RUN off when ready:"
Write-Host "  az functionapp config appsettings set -g $rgName -n $functionAppName --settings DRY_RUN=false"
