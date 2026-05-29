<#
.SYNOPSIS
    End-to-end deployment of a private Azure Container Apps environment.

.DESCRIPTION
    This script orchestrates a two-phase Bicep deployment:
      Phase 1 – Log Analytics, ACA Environment (internal), Hello-World app
      Phase 2 – Private DNS Zone + Private Endpoint (requires runtime outputs from Phase 1)
    Then disables public network access via CLI and prints test instructions.

    The VNet and subnets must already exist before running this script.
    The Private Endpoint subnet can be in a DIFFERENT VNet, subscription, and
    resource group from the ACA environment.

.PARAMETER ResourceGroupName
    Resource group for the ACA environment (created if it doesn't exist).

.PARAMETER Location
    Azure region for ACA resources.

.PARAMETER AcaSubnetId
    (Required) Resource ID of the ACA infrastructure subnet.
    Must have Microsoft.App/environments delegation and be at least /23.

.PARAMETER PeSubnetId
    (Required) Resource ID of the private endpoint subnet. Can be in a different
    VNet/subscription/resource group from the ACA subnet.

.PARAMETER PeResourceGroupName
    (Optional) Resource group where the PE subnet lives. Derived from PeSubnetId
    if not specified. Phase 2 is deployed here.

.PARAMETER PeLocation
    (Optional) Region for the private endpoint. Defaults to Location.

.EXAMPLE
    # PE subnet in the same VNet as ACA
    .\deploy.ps1 -ResourceGroupName "rg-aca-private-demo" -Location "eastus2" `
        -AcaSubnetId "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-aca-infra" `
        -PeSubnetId  "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-pe"

.EXAMPLE
    # PE subnet in a different VNet / subscription / resource group
    .\deploy.ps1 -ResourceGroupName "rg-aca-demo" -Location "eastus2" `
        -AcaSubnetId "/subscriptions/<aca-sub>/resourceGroups/<aca-rg>/providers/Microsoft.Network/virtualNetworks/<aca-vnet>/subnets/snet-aca" `
        -PeSubnetId  "/subscriptions/<pe-sub>/resourceGroups/<pe-rg>/providers/Microsoft.Network/virtualNetworks/<pe-vnet>/subnets/snet-pe"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "rg-aca-private-demo",

    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus2",

    [Parameter(Mandatory = $true)]
    [string]$AcaSubnetId,

    [Parameter(Mandatory = $true)]
    [string]$PeSubnetId,

    [Parameter(Mandatory = $false)]
    [string]$PeResourceGroupName = "",

    [Parameter(Mandatory = $false)]
    [string]$PeLocation = ""
)

$ErrorActionPreference = "Stop"
$InfraDir = Join-Path $PSScriptRoot "infra"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " ACA Private VNet Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ── Derive VNet info from subnet resource IDs ──────────────────────────────
# Subnet ID format: /subscriptions/.../providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/<subnet>
function Get-VnetInfoFromSubnetId([string]$SubnetId) {
    $parts = $SubnetId -split '/'
    $vnetName = $parts[8]
    $vnetId   = ($SubnetId -split '/subnets/')[0]
    $rg       = $parts[4]
    return @{ VnetName = $vnetName; VnetId = $vnetId; ResourceGroup = $rg }
}

$acaInfo = Get-VnetInfoFromSubnetId -SubnetId $AcaSubnetId
$peInfo  = Get-VnetInfoFromSubnetId -SubnetId $PeSubnetId

$AcaVnetId   = $acaInfo.VnetId
$AcaVnetName = $acaInfo.VnetName
$PeVnetId    = $peInfo.VnetId
$PeVnetName  = $peInfo.VnetName

if ([string]::IsNullOrEmpty($PeResourceGroupName)) {
    $PeResourceGroupName = $peInfo.ResourceGroup
}
if ([string]::IsNullOrEmpty($PeLocation)) {
    $PeLocation = $Location
}

$isCrossVnet = $AcaVnetId -ne $PeVnetId

# ── Pre-flight checks ──────────────────────────────────────────────────────
Write-Host "[1/6] Checking Azure CLI..." -ForegroundColor Yellow
az version --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Azure CLI is not installed or not in PATH. Install from https://aka.ms/installazurecli"
}

Write-Host "  ACA Subnet : $AcaSubnetId" -ForegroundColor Green
Write-Host "  ACA VNet   : $AcaVnetName ($AcaVnetId)"
Write-Host "  PE Subnet  : $PeSubnetId" -ForegroundColor Green
Write-Host "  PE VNet    : $PeVnetName ($PeVnetId)"
if ($isCrossVnet) {
    Write-Host "  (Cross-VNet) PE is in a different VNet – DNS zone will be linked to both VNets" -ForegroundColor Magenta
    Write-Host "  PE Resource Group: $PeResourceGroupName" -ForegroundColor Magenta
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

# ── Phase 1: Deploy ACA Environment ─────────────────────────────────────────
Write-Host "`n[4/6] Phase 1 – Deploying ACA Environment & Hello-World app..." -ForegroundColor Yellow
Write-Host "  (this may take 5-10 minutes)" -ForegroundColor DarkGray

$phase1Result = az deployment group create `
    --name "aca-private-phase1" `
    --resource-group $ResourceGroupName `
    --template-file "$InfraDir\main.bicep" `
    --parameters "$InfraDir\main.bicepparam" `
    --parameters location=$Location acaSubnetId=$AcaSubnetId `
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
$appFqdn       = $phase1Result.containerAppFqdn.value

Write-Host "`n  Phase 1 Outputs:" -ForegroundColor Green
Write-Host "    ACA Domain   : $acaDomain"
Write-Host "    ACA Static IP: $acaStaticIp"
Write-Host "    App FQDN     : $appFqdn"
Write-Host "    ACA VNet     : $AcaVnetName"
Write-Host "    PE Subnet    : $PeSubnetId"
if ($isCrossVnet) {
    Write-Host "    (Cross-VNet) PE VNet: $PeVnetName in RG: $PeResourceGroupName" -ForegroundColor Magenta
}

# ── Phase 2: Private DNS Zone + Private Endpoint ────────────────────────────
Write-Host "`n[5/6] Phase 2 – Creating Private DNS Zone & Private Endpoint..." -ForegroundColor Yellow
if ($PeResourceGroupName -ne $ResourceGroupName) {
    Write-Host "  Deploying into PE resource group: $PeResourceGroupName" -ForegroundColor Magenta
}

$phase2Result = az deployment group create `
    --name "aca-private-phase2" `
    --resource-group $PeResourceGroupName `
    --template-file "$InfraDir\private-dns.bicep" `
    --parameters `
        location=$PeLocation `
        acaDefaultDomain=$acaDomain `
        acaStaticIp=$acaStaticIp `
        acaEnvironmentId=$acaEnvId `
        acaEnvironmentName=$acaEnvName `
        acaVnetId=$AcaVnetId `
        acaVnetName=$AcaVnetName `
        peSubnetId=$PeSubnetId `
        peVnetId=$PeVnetId `
        peVnetName=$PeVnetName `
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
