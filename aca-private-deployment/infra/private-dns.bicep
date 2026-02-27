// ============================================================================
// Phase 2: Private DNS Zone + Private Endpoint for ACA Environment
// ============================================================================
// Run AFTER Phase 1 (main.bicep) completes, using its outputs as parameters.
// The ACA environment's default domain is only known at runtime, so this
// phase accepts it as a parameter.
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters (populated from Phase 1 outputs)
// ---------------------------------------------------------------------------
@description('Azure region')
param location string = resourceGroup().location

@description('ACA environment default domain (e.g., kindocean-abc123.eastus2.azurecontainerapps.io)')
param acaDefaultDomain string

@description('ACA environment static IP')
param acaStaticIp string

@description('ACA environment resource ID')
param acaEnvironmentId string

@description('VNet resource ID')
param vnetId string

@description('VNet name')
param vnetName string

@description('Subnet resource ID for private endpoints')
param peSubnetId string

@description('ACA environment name (used for PE naming)')
param acaEnvironmentName string

@description('Tags')
param tags object = {
  environment: 'demo'
  purpose: 'aca-private-deployment'
}

// ---------------------------------------------------------------------------
// 1. Private DNS Zone – matches the ACA environment's default domain
// ---------------------------------------------------------------------------
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: acaDefaultDomain
  location: 'global'
  tags: tags
}

// Link the private DNS zone to the VNet
resource dnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: privateDnsZone
  name: '${vnetName}-link'
  location: 'global'
  tags: tags
  properties: {
    virtualNetwork: {
      id: vnetId
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
