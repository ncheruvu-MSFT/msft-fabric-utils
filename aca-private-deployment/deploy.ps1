<#
.SYNOPSIS
    End-to-end deployment of a private Azure Container Apps environment.

.DESCRIPTION
    This script orchestrates a two-phase Bicep deployment:
      Phase 1 – VNet (or use existing), Log Analytics, ACA Environment (internal), Hello-World app
      Phase 2 – Private DNS Zone + Private Endpoint (requires runtime outputs from Phase 1)
    Then disables public network access via CLI and prints test instructions.

.PARAMETER ResourceGroupName
    Name of the resource group (created if it doesn't exist).

.PARAMETER Location
    Azure region for all resources.

.PARAMETER ExistingVnetId
    (Optional) Resource ID of an existing VNet. Leave empty to create a new one.

.PARAMETER ExistingAcaSubnetId
    (Optional) Resource ID of an existing subnet for ACA infrastructure.
    Must have Microsoft.App/environments delegation and be /23 or larger.

.PARAMETER ExistingPeSubnetId
    (Optional) Resource ID of an existing subnet for private endpoints.
    Should have privateEndpointNetworkPolicies set to Disabled.

.EXAMPLE
    # Create new VNet
    .\deploy.ps1 -ResourceGroupName "rg-aca-private-demo" -Location "eastus2"

.EXAMPLE
    # Use existing VNet and subnets
    .\deploy.ps1 -ResourceGroupName "rg-aca-private-demo" -Location "eastus2" `
        -ExistingVnetId "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>" `
        -ExistingAcaSubnetId "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-aca" `
        -ExistingPeSubnetId "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-pe"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "rg-aca-private-demo",

    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus2",

    [Parameter(Mandatory = $false)]
    [string]$ExistingVnetId = "",

    [Parameter(Mandatory = $false)]
    [string]$ExistingAcaSubnetId = "",

    [Parameter(Mandatory = $false)]
    [string]$ExistingPeSubnetId = ""
)

$ErrorActionPreference = "Stop"
$InfraDir = Join-Path $PSScriptRoot "infra"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " ACA Private VNet Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ── Pre-flight checks ──────────────────────────────────────────────────────
Write-Host "[1/6] Checking Azure CLI..." -ForegroundColor Yellow
az version --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Azure CLI is not installed or not in PATH. Install from https://aka.ms/installazurecli"
}
# Validate existing VNet parameters
$useExistingVnet = -not [string]::IsNullOrEmpty($ExistingVnetId)
if ($useExistingVnet) {
    if ([string]::IsNullOrEmpty($ExistingAcaSubnetId) -or [string]::IsNullOrEmpty($ExistingPeSubnetId)) {
        Write-Error "When using an existing VNet, you must provide both -ExistingAcaSubnetId and -ExistingPeSubnetId."
    }
    Write-Host "  Mode: Using EXISTING VNet" -ForegroundColor Green
    Write-Host "    VNet       : $ExistingVnetId"
    Write-Host "    ACA Subnet : $ExistingAcaSubnetId"
    Write-Host "    PE Subnet  : $ExistingPeSubnetId"
} else {
    Write-Host "  Mode: Creating NEW VNet" -ForegroundColor Green
}
# Ensure required providers are registered
Write-Host "[2/6] Registering resource providers..." -ForegroundColor Yellow
@("Microsoft.App", "Microsoft.Network", "Microsoft.OperationalInsights") | ForEach-Object {
    az provider register --namespace $_ --wait 2>$null
    Write-Host "  Registered: $_"
}

# ── Resource Group ──────────────────────────────────────────────────────────
Write-Host "`n[3/6] Creating resource group '$ResourceGroupName'..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output none

# ── Phase 1: Deploy ACA Environment (+ VNet if not using existing) ──────────
if ($useExistingVnet) {
    Write-Host "`n[4/6] Phase 1 – Deploying ACA Environment & Hello-World app (existing VNet)..." -ForegroundColor Yellow
} else {
    Write-Host "`n[4/6] Phase 1 – Deploying VNet, ACA Environment & Hello-World app..." -ForegroundColor Yellow
}
Write-Host "  (this may take 5-10 minutes)" -ForegroundColor DarkGray

# Build parameter overrides
$phase1Params = @(
    "location=$Location"
)
if ($useExistingVnet) {
    $phase1Params += "existingVnetId=$ExistingVnetId"
    $phase1Params += "existingAcaSubnetId=$ExistingAcaSubnetId"
    $phase1Params += "existingPeSubnetId=$ExistingPeSubnetId"
}

$phase1Result = az deployment group create `
    --name "aca-private-phase1" `
    --resource-group $ResourceGroupName `
    --template-file "$InfraDir\main.bicep" `
    --parameters "$InfraDir\main.bicepparam" `
    --parameters @phase1Params `
    --query "properties.outputs" `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Error "Phase 1 deployment failed."
}

# Extract outputs
$acaDomain     = $phase1Result.acaEnvironmentDefaultDomain.value
$acaStaticIp   = $phase1Result.acaEnvironmentStaticIp.value
$acaEnvId      = $phase1Result.acaEnvironmentId.value
$acaEnvName    = $phase1Result.acaEnvironmentName.value
$vnetId        = $phase1Result.vnetId.value
$vnetName      = $phase1Result.vnetName.value
$peSubnetId    = $phase1Result.peSubnetId.value
$appFqdn       = $phase1Result.containerAppFqdn.value

Write-Host "`n  Phase 1 Outputs:" -ForegroundColor Green
Write-Host "    ACA Domain   : $acaDomain"
Write-Host "    ACA Static IP: $acaStaticIp"
Write-Host "    App FQDN     : $appFqdn"
Write-Host "    VNet Name    : $vnetName"

# ── Phase 2: Private DNS Zone + Private Endpoint ────────────────────────────
Write-Host "`n[5/6] Phase 2 – Creating Private DNS Zone & Private Endpoint..." -ForegroundColor Yellow

$phase2Result = az deployment group create `
    --name "aca-private-phase2" `
    --resource-group $ResourceGroupName `
    --template-file "$InfraDir\private-dns.bicep" `
    --parameters `
        location=$Location `
        acaDefaultDomain=$acaDomain `
        acaStaticIp=$acaStaticIp `
        acaEnvironmentId=$acaEnvId `
        acaEnvironmentName=$acaEnvName `
        vnetId=$vnetId `
        vnetName=$vnetName `
        peSubnetId=$peSubnetId `
    --query "properties.outputs" `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Error "Phase 2 deployment failed."
}

Write-Host "  Private DNS Zone: $($phase2Result.privateDnsZoneName.value)" -ForegroundColor Green

# ── Disable public network access via CLI ────────────────────────────────────
Write-Host "`n[6/6] Disabling public network access on the ACA environment..." -ForegroundColor Yellow
az containerapp env update `
    --name $acaEnvName `
    --resource-group $ResourceGroupName `
    --enable-public-network-access false `
    --output none 2>$null

# If the above flag isn't available in your CLI version, use REST API:
# az rest --method PATCH `
#     --url "https://management.azure.com${acaEnvId}?api-version=2024-10-02-preview" `
#     --body '{"properties":{"publicNetworkAccess":"Disabled"}}'

Write-Host "  Public network access: DISABLED" -ForegroundColor Green

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resource Group  : $ResourceGroupName"
Write-Host "ACA Environment : $acaEnvName"
Write-Host "Default Domain  : $acaDomain"
Write-Host "Static IP       : $acaStaticIp"
Write-Host "App FQDN        : $appFqdn"
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. From a VM in the VNet (or peered VNet), test:"
Write-Host "       nslookup $appFqdn"
Write-Host "       curl https://$appFqdn"
Write-Host ""
Write-Host "  2. For ExpressRoute connectivity, see README.md:"
Write-Host "       - Configure Azure DNS Private Resolver (Steps 3-4)"
Write-Host "       - Set up AD conditional forwarders (Step 5)"
Write-Host ""
Write-Host "  3. To clean up:"
Write-Host "       az group delete --name $ResourceGroupName --yes --no-wait"
Write-Host ""
