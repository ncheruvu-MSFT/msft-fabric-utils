// ============================================================================
// Phase 1: Azure Container Apps – VNet, Environment & Hello-World App
// ============================================================================
// Deploys:
//   1. Virtual Network with subnets (or uses existing ones)
//   2. Log Analytics workspace (required by ACA environment)
//   3. Azure Container Apps Environment (internal-only, VNet-injected)
//   4. Hello-World container app
//
// Supports two modes:
//   - Create new VNet/subnets: leave existingVnet* params empty (default)
//   - Use existing VNet/subnets: provide resource IDs via existingVnet* params
//
// Phase 2 (private-dns.bicep) creates the Private DNS Zone & Private Endpoint
// using the runtime-generated default domain from this deployment's outputs.
//
// Public network access is disabled via CLI after deployment (see deploy.ps1).
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------
@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base name used to derive resource names')
@minLength(3)
@maxLength(20)
param baseName string = 'acaprivate'

// ── Existing VNet/Subnet parameters (leave empty to create new ones) ──────
@description('Resource ID of an existing VNet. Leave empty to create a new VNet.')
param existingVnetId string = ''

@description('Resource ID of an existing subnet for ACA infrastructure (must have Microsoft.App/environments delegation, /23 minimum). Required when existingVnetId is provided.')
param existingAcaSubnetId string = ''

@description('Resource ID of an existing subnet for private endpoints (privateEndpointNetworkPolicies should be Disabled). Required when existingVnetId is provided.')
param existingPeSubnetId string = ''

// ── New VNet parameters (used only when existingVnetId is empty) ───────────
@description('Address space for the new VNet (ignored if using existing VNet)')
param vnetAddressPrefix string = '10.100.0.0/16'

@description('Subnet CIDR for ACA infrastructure (ignored if using existing VNet)')
param acaSubnetPrefix string = '10.100.0.0/23'

@description('Subnet CIDR for private endpoints (ignored if using existing VNet)')
param peSubnetPrefix string = '10.100.2.0/24'

@description('Container image to deploy (hello-world)')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container app name')
param containerAppName string = 'helloworld'

@description('Tags applied to every resource')
param tags object = {
  environment: 'demo'
  purpose: 'aca-private-deployment'
}

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------
var useExistingVnet = !empty(existingVnetId)
var uniqueSuffix = uniqueString(resourceGroup().id, baseName)
var newVnetName = '${baseName}-vnet-${uniqueSuffix}'
var logAnalyticsName = '${baseName}-la-${uniqueSuffix}'
var acaEnvName = '${baseName}-env-${uniqueSuffix}'
var acaSubnetName = 'snet-aca-infra'
var peSubnetName = 'snet-private-endpoints'

// ---------------------------------------------------------------------------
// 1. Virtual Network (created only when not using an existing one)
// ---------------------------------------------------------------------------
resource newVnet 'Microsoft.Network/virtualNetworks@2024-05-01' = if (!useExistingVnet) {
  name: newVnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: acaSubnetName
        properties: {
          addressPrefix: acaSubnetPrefix
          // ACA requires delegation to Microsoft.App/environments
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: peSubnetName
        properties: {
          addressPrefix: peSubnetPrefix
          // Private endpoints do not require delegation
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// 2. Log Analytics Workspace (required by ACA)
// ---------------------------------------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// ---------------------------------------------------------------------------
// 3. Azure Container Apps Environment – Internal Only
// ---------------------------------------------------------------------------
resource acaEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: acaEnvName
  location: location
  tags: tags
  properties: {
    // Attach to the VNet infrastructure subnet (existing or newly created)
    vnetConfiguration: {
      infrastructureSubnetId: useExistingVnet ? existingAcaSubnetId : newVnet!.properties.subnets[0].id
      internal: true // ← makes the environment internal-only (no public IP)
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// 4. Hello-World Container App
// ---------------------------------------------------------------------------
resource helloApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: acaEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true // "external" within the internal environment → reachable on VNet
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'helloworld'
          image: containerImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs – consumed by Phase 2 (private-dns.bicep) and deploy.ps1
// ---------------------------------------------------------------------------
output vnetName string = useExistingVnet ? last(split(existingVnetId, '/'))! : newVnet!.name
output vnetId string = useExistingVnet ? existingVnetId : newVnet!.id
output peSubnetId string = useExistingVnet ? existingPeSubnetId : newVnet!.properties.subnets[1].id
output usingExistingVnet bool = useExistingVnet
output acaEnvironmentId string = acaEnv.id
output acaEnvironmentName string = acaEnv.name
output acaEnvironmentDefaultDomain string = acaEnv.properties.defaultDomain
output acaEnvironmentStaticIp string = acaEnv.properties.staticIp
output containerAppFqdn string = helloApp.properties.configuration.ingress.fqdn
