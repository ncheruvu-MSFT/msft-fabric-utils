// Parameters file for Phase 1 (main.bicep)
using './main.bicep'

param baseName = 'acaprivate'
// location is passed via CLI --parameters location=<region>

// ── Existing VNet/Subnet (leave empty to create new) ────────────────────────
// To use an existing VNet, provide all three resource IDs:
//   param existingVnetId = '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>'
//   param existingAcaSubnetId = '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/<aca-subnet>'
//   param existingPeSubnetId = '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/<pe-subnet>'
param existingVnetId = ''
param existingAcaSubnetId = ''
param existingPeSubnetId = ''

// ── New VNet settings (used only when existingVnetId is empty) ───────────────
param vnetAddressPrefix = '10.100.0.0/16'
param acaSubnetPrefix = '10.100.0.0/23'
param peSubnetPrefix = '10.100.2.0/24'

param containerImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param containerAppName = 'helloworld'
param tags = {
  environment: 'demo'
  purpose: 'aca-private-deployment'
}
