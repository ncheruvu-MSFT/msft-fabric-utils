// ============================================================================
// Phase 2: Private DNS Zone + Private Endpoint for ACA Environment
// ============================================================================
// Run AFTER Phase 1 (main.bicep) completes, using its outputs as parameters.
//
// Supports cross-subscription / cross-VNet scenarios:
//   - The Private Endpoint subnet can reside in a DIFFERENT VNet, subscription,
//     and resource group from the ACA environment.
//   - If peVnetId differs from acaVnetId, the DNS zone is linked to BOTH VNets.
//   - Deploy this template into the resource group where the PE subnet lives
//     (or any group with cross-sub subnet access).
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters (populated from Phase 1 outputs + PE subnet details)
// ---------------------------------------------------------------------------
@description('Azure region for the private endpoint (should match PE subnet region)')
param location string = resourceGroup().location

@description('ACA environment default domain (e.g., kindocean-abc123.eastus2.azurecontainerapps.io)')
param acaDefaultDomain string

@description('ACA environment static IP')
param acaStaticIp string

@description('ACA environment resource ID (can be cross-subscription)')
param acaEnvironmentId string

@description('ACA environment name (used for PE naming)')
param acaEnvironmentName string

@description('Resource ID of the VNet where the ACA environment is deployed')
param acaVnetId string

@description('Name of the VNet where the ACA environment is deployed (for DNS link naming)')
param acaVnetName string

@description('Resource ID of the subnet for private endpoints. Can be in a different VNet/subscription/resource group.')
param peSubnetId string

@description('Resource ID of the VNet that contains the PE subnet. If same as acaVnetId, only one DNS link is created.')
param peVnetId string

@description('Name of the VNet that contains the PE subnet (for DNS link naming)')
param peVnetName string

@description('Tags')
param tags object = {
  environment: 'demo'
  purpose: 'aca-private-deployment'
}

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------
var isCrossVnet = acaVnetId != peVnetId

// ---------------------------------------------------------------------------
// 1. Private DNS Zone – matches the ACA environment's default domain
// ---------------------------------------------------------------------------
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: acaDefaultDomain
  location: 'global'
  tags: tags
}

// Link the DNS zone to the ACA VNet (always)
resource dnsAcaVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: privateDnsZone
  name: '${acaVnetName}-link'
  location: 'global'
  tags: tags
  properties: {
    virtualNetwork: {
      id: acaVnetId
    }
    registrationEnabled: false
  }
}

// Link the DNS zone to the PE VNet (only if different from ACA VNet)
resource dnsPeVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = if (isCrossVnet) {
  parent: privateDnsZone
  name: '${peVnetName}-link'
  location: 'global'
  tags: tags
  properties: {
    virtualNetwork: {
      id: peVnetId
    }
    registrationEnabled: false
  }
}

// Wildcard A record → ACA static IP
resource dnsWildcard 'Microsoft.Network/privateDnsZones/A@2024-06-01' = {
  parent: privateDnsZone
  name: '*'
  properties: {
    ttl: 300
    aRecords: [
      {
        ipv4Address: acaStaticIp
      }
    ]
  }
}

// Root A record → ACA static IP
resource dnsRoot 'Microsoft.Network/privateDnsZones/A@2024-06-01' = {
  parent: privateDnsZone
  name: '@'
  properties: {
    ttl: 300
    aRecords: [
      {
        ipv4Address: acaStaticIp
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// 2. Private Endpoint for the ACA Environment
// ---------------------------------------------------------------------------
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${acaEnvironmentName}-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${acaEnvironmentName}-plsc'
        properties: {
          privateLinkServiceId: acaEnvironmentId
          groupIds: [
            'managedEnvironments'
          ]
        }
      }
    ]
  }
}

// Register the PE NIC in the private DNS zone
resource peDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output privateDnsZoneName string = privateDnsZone.name
output privateEndpointId string = privateEndpoint.id
output isCrossVnet bool = isCrossVnet
